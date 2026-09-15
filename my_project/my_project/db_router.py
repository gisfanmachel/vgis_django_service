"""
主从路由（Stage B）

行为：
  - 读：DB_REPLICA_ENABLED=true 时把读流量切到 replica alias；
        其它 alias（pgstac 等）继续按 Django 默认走 original_alias
  - 写：永远走 default（replica 只读，写过去会报错）
  - migrate：只在 default 上跑（避免副本库被结构变更污染）

为什么这样写：
  - Django 的 router 只在 query 时返回 alias，写/migrate 必须显式拦，
    否则 ORM 会按 default 跑；与 Django 官方推荐写法一致。
  - 默认 DB_REPLICA_ENABLED=False 时一切走 default，零回归。
"""
from django.conf import settings


def _replica_enabled():
    """延迟读 settings：避免 settings.py 加载阶段就耦合"""
    return getattr(settings, "DATABASES", {}).get("replica") is not None


class PrimaryReplicaRouter:
    """主从路由：读 replica，写 default"""

    def db_for_read(self, model, **hints):
        if _replica_enabled():
            return "replica"
        return None  # 走 original_alias（即 default）

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """
        跨 alias 关联查询时是否允许拼接返回。
        这里全部 True —— Django 会按 hint 决定要不要跨 alias 拼。
        """
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        migrate 只在 default 上跑；replica 只是只读副本。
        """
        if db == "default":
            return True
        return False