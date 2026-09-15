# -*- coding: utf-8 -*-
"""
Stage F：数据库健康指标管理命令。

用法：
  python manage.py db_health                # 跑所有 alias
  python manage.py db_health --alias default  # 只跑 default
  python manage.py db_health --alias replica   # 只跑 replica（开启 DB_REPLICA_ENABLED 才存在）

输出：
  - PG version（截 60 字符）
  - active / idle 连接数（来自 pg_stat_activity）
  - SELECT 1 探活结果
  - 当前别名 + 后端进程清单（用于排查 dangling connection）
"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = "数据库连接健康指标（PG version + SELECT 1 + 连接数）"

    def add_arguments(self, parser):
        parser.add_argument('--alias', default='all',
                            help='只跑某个 alias（默认 all）')

    def handle(self, *args, **options):
        target = options['alias']
        for alias in connections:
            if target != 'all' and alias != target:
                continue
            self._probe(alias)

    def _probe(self, alias):
        try:
            conn = connections[alias]
            # ensure_connection 强制建连（不依赖缓存的连接池）
            conn.ensure_connection()
            with conn.cursor() as cur:
                cur.execute('SELECT version()')
                ver = cur.fetchone()[0][:60]
                self.stdout.write('[{}] PG {}'.format(alias, ver))

                cur.execute(
                    "SELECT count(*) FILTER (WHERE state='active'), "
                    "       count(*) FILTER (WHERE state='idle') "
                    "FROM pg_stat_activity "
                    "WHERE backend_type='client backend'"
                )
                active, idle = cur.fetchone()
                self.stdout.write('[{}] connections: active={} idle={}'.format(alias, active, idle))

                cur.execute('SELECT 1')
                cur.fetchone()
                self.stdout.write('[{}] SELECT 1 OK'.format(alias))
        except Exception as e:
            self.stdout.write(self.style.ERROR('[{}] FAIL: {}'.format(alias, e)))