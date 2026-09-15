# pgbouncer 镜像 —— 基于 edoburu/pgbouncer 1.22.1（Debian slim）
FROM edoburu/pgbouncer:1.22.1

# 自定义配置 / 用户清单拷进镜像
COPY pgbouncer.ini /etc/pgbouncer/pgbouncer.ini
# COPY userlist.txt /etc/pgbouncer/userlist.txt  # 由 docker-compose 用 secret 挂载更安全

EXPOSE 6432

# 默认 CMD 由 edoburu 镜像提供（/usr/bin/pgbouncer /etc/pgbouncer/pgbouncer.ini）
# 这里只显式声明便于 override
CMD ["/usr/bin/pgbouncer", "/etc/pgbouncer/pgbouncer.ini"]