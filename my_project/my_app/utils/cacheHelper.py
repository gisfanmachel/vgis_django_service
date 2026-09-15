# -*- coding: utf-8 -*-
"""
Stage C：表级缓存工具。

设计要点：
  - key 格式 "table:<table_name>:<scope>:<suffix>"，统一前缀便于按表失效。
  - loader 抛错时本次失败返回 None（不污染缓存）；下次请求重新计算。
  - serialize/deserialize：值若不可 JSON 序列化（datetime 等），直接 fallback 到原值。
  - invalidate_pattern 仅在 cache backend 支持 delete_pattern 时生效（django_redis 支持）；
    否则降级为删 known key，避免误删。

参见 plan: SpringBoot 对齐方案 / Stage C。
"""
from __future__ import unicode_literals

import json
import logging

from django.core.cache import cache

logger = logging.getLogger("django")


class TableCacheHelper:
    """表级缓存 helper：get_or_load / invalidate / invalidate_pattern"""

    PREFIX = "table"
    DEFAULT_TTL = 1800  # 30 分钟默认

    @classmethod
    def key(cls, table_name, scope="all", suffix=None):
        parts = [cls.PREFIX, table_name, scope]
        if suffix is not None:
            parts.append(str(suffix))
        return ":".join(parts)

    @classmethod
    def get_or_load(cls, table_name, loader, ttl=DEFAULT_TTL, scope="all", suffix=None):
        """
        优先从 cache 读；miss 时调 loader() 加载并写入。
        loader 应返回 list[dict] 或 dict 等可序列化的结构。
        """
        cache_key = cls.key(table_name, scope, suffix)
        try:
            cached = cache.get(cache_key)
        except Exception as exp:
            logger.warning("cache.get(%s) 失败: %s", cache_key, exp)
            cached = None

        if cached is not None:
            # 之前以 JSON 字符串存的，deserialize 回来
            if isinstance(cached, (str, bytes)):
                try:
                    return json.loads(cached)
                except (TypeError, ValueError):
                    return cached
            return cached

        try:
            value = loader()
        except Exception as exp:
            logger.warning("cache loader(%s) 失败: %s", table_name, exp)
            return None

        if value is None:
            return None

        # 大多数 loader 返回 list/dict，JSON 可序列化；其它类型直接缓存原值。
        try:
            payload = json.dumps(value, default=str)
            cache.set(cache_key, payload, ttl)
        except (TypeError, ValueError):
            cache.set(cache_key, value, ttl)
        return value

    @classmethod
    def invalidate(cls, table_name, scope="all", suffix=None):
        """删单条 cache key。失败静默（运维配置变更不该阻塞业务请求）"""
        try:
            cache.delete(cls.key(table_name, scope, suffix))
        except Exception as exp:
            logger.warning("cache.delete(%s) 失败: %s", table_name, exp)

    @classmethod
    def invalidate_pattern(cls, table_name):
        """
        按表名失效所有 scope / suffix。
        - django_redis 支持 cache.delete_pattern
        - 其它 backend（locmem / db）会 AttributeError，降级到 invalidate("all")
        """
        pattern = "{}:{}:*".format(cls.PREFIX, table_name)
        try:
            cache.delete_pattern(pattern)
            return
        except AttributeError:
            pass
        except Exception as exp:
            logger.warning("cache.delete_pattern(%s) 失败: %s", pattern, exp)
        # 降级
        cls.invalidate(table_name, "all")