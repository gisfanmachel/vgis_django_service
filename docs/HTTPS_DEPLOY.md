# VGIS Django 框架 HTTPS 部署指南

> 创建日期：2026-09-15
> 范围：Windows 本机（`192.168.31.79`）通过 nginx `1.21.1` 反代 Django `waitress @ 10846`，对外暴露 HTTPS `443`

---

## 1. 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│  客户端（浏览器 / Postman / curl）                            │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS (TLSv1.2/TLSv1.3, 443)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  nginx 1.21.1 (C:\nginx-1.21.1)                              │
│  ├─ 80  → 301 重定向到 443                                  │
│  └─ 443 → 反代 http://127.0.0.1:10846                       │
│         ssl_certificate conf/ssl/vgis.crt (90 天自签名)      │
│         ssl_certificate_key conf/ssl/vgis.key                │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP (内部)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Django waitress @ 10846（已存在）                            │
│  ALLOWED_HOSTS = ['*']（已允许 192.168.31.79）               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 文件清单

| 文件 | 用途 |
|---|---|
| `C:\nginx-1.21.1\conf\nginx.conf` | 主配置（追加 80/443 server 块） |
| `C:\nginx-1.21.1\conf\nginx.conf.bak` | 备份（首次改前自动备份） |
| `C:\nginx-1.21.1\conf\ssl\openssl.cnf` | SAN 配置（IP.1 = 192.168.31.79） |
| `C:\nginx-1.21.1\conf\ssl\vgis.crt` | 自签名证书（90 天） |
| `C:\nginx-1.21.1\conf\ssl\vgis.key` | 私钥 |
| `C:\nginx-1.21.1\conf\ssl\archive\` | 旧证书自动归档（保留最新 4 份） |
| `C:\nginx-1.21.1\scripts\gen-cert.ps1` | 生成证书脚本 |
| `C:\nginx-1.21.1\scripts\renew-cert-task.ps1` | 续期 + nginx reload 脚本 |
| `C:\nginx-1.21.1\scripts\register-task-admin.ps1` | **手动**注册计划任务（需管理员） |
| `C:\nginx-1.21.1\logs\cert-renew.log` | 续期日志 |
| `C:\nginx-1.21.1\logs\vgis_https_access.log` | nginx 访问日志 |
| `C:\nginx-1.21.1\logs\vgis_https_error.log` | nginx 错误日志 |

**nginx.conf 关键追加**（备份后改）：
```nginx
server {
    listen 80 default_server;
    server_name 192.168.31.79 localhost;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name 192.168.31.79 localhost;

    ssl_certificate      C:/nginx-1.21.1/conf/ssl/vgis.crt;
    ssl_certificate_key  C:/nginx-1.21.1/conf/ssl/vgis.key;
    ssl_protocols        TLSv1.2 TLSv1.3;
    ssl_ciphers          HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers  on;
    ssl_session_cache    shared:SSL_VGIS:10m;   # 唯一 zone 名（不与 4432 冲突）
    ssl_session_timeout  10m;

    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    access_log  C:/nginx-1.21.1/logs/vgis_https_access.log;
    error_log   C:/nginx-1.21.1/logs/vgis_https_error.log;

    location / {
        proxy_pass         http://127.0.0.1:10846;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto https;
        proxy_set_header   X-Forwarded-Port  443;
        proxy_connect_timeout  30s;
        proxy_send_timeout     60s;
        proxy_read_timeout     60s;
        proxy_buffering         off;
        client_max_body_size   100m;
    }

    location /my_static/ {
        alias C:/系统开发/VGIS-DEV-LIB/Django框架/vgis_django_service/my_project/my_app/my_static/;
        expires 7d;
    }
}
```

> 注：原 nginx.conf 中已有 `4432` 端口的旧 SSL server（证书路径错误 `vgisssl.crt`），未触碰。
> 当前 HTTPS 用 443，新 zone 名 `SSL_VGIS` 与旧的 `SSL` 隔离。

---

## 3. 一次性部署步骤

### 3.1 验证环境

```bash
# nginx 已装
"C:/nginx-1.21.1/nginx.exe" -v

# OpenSSL（Git Bash 自带）
"C:/Program Files/Git/usr/bin/openssl.exe" version

# Django 还在 10846
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:10846/
```

### 3.2 生成证书

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File C:\nginx-1.21.1\scripts\gen-cert.ps1
```

输出：
```
[gen-cert] 成功：C:\nginx-1.21.1\conf\ssl\vgis.crt
notBefore=Sep 15 09:30:07 2026 GMT
notAfter=Dec 14 09:30:07 2026 GMT   ← 90 天后
subject=CN=192.168.31.79
X509v3 Subject Alternative Name:
    IP Address:192.168.31.79, IP Address:127.0.0.1, DNS:localhost, DNS:vgis.local
```

### 3.3 修改 nginx 配置

备份并追加新 server 块（已包含在本指南 §2）。验证语法：
```bash
cd C:/nginx-1.21.1 && ./nginx.exe -t -c conf/nginx.conf
# nginx: the configuration file ... syntax is ok
# nginx: configuration file ... test is successful
```

### 3.4 启动 nginx

```bash
cd C:/nginx-1.21.1 && ./nginx.exe
# 或装为 Windows 服务
# ./nginx.exe -s install   (注册)
# net start nginx           (启动)
```

### 3.5 注册自动续期任务（需管理员）

Git Bash 等非交互会话**无法自动 UAC 提升**。手动步骤：

**方法 A（推荐）**：开始菜单 → 右键 PowerShell → "以管理员身份运行"
```powershell
C:\nginx-1.21.1\scripts\register-task-admin.ps1
```

**方法 B**：普通 PowerShell
```powershell
Start-Process powershell -Verb RunAs -ArgumentList "-File C:\nginx-1.21.1\scripts\register-task-admin.ps1"
```

**验证**（任何权限）：
```cmd
schtasks /Query /TN vgis_https_cert_renew /V /FO LIST
```

任务设置：
- 名称：`vgis_https_cert_renew`
- 触发：每日 03:00
- 运行身份：SYSTEM（最高权限）
- 操作：`powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\nginx-1.21.1\scripts\renew-cert-task.ps1`
- 说明：每日 03:00 检查证书剩余天数；< 30 天则重新生成 + reload nginx

---

## 4. 自动续期机制

```
每日 03:00
   ↓
Task Scheduler 触发 renew-cert-task.ps1
   ↓
1) openssl x509 -enddate → 读剩余天数
   ↓
> 30 天 → exit 0（不续期）
   ↓
≤ 30 天
   ↓
2) gen-cert.ps1 重生成证书
   - 私钥 vgis.key (2048 位 RSA)
   - 证书 vgis.crt (90 天, SAN: 192.168.31.79 + 127.0.0.1 + localhost + vgis.local)
   - 旧证书归档到 conf/ssl/archive/ (保留最新 4 份)
   ↓
3) nginx.exe -s reload（不中断服务）
   ↓
4) 写日志 C:\nginx-1.21.1\logs\cert-renew.log
```

---

## 5. 验证清单

### 5.1 服务连通

```bash
# 80 → 443 重定向
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 5 http://192.168.31.79/
# 预期：301

# 443 HTTPS
curl -sk -o /dev/null -w "HTTP %{http_code}\n" --max-time 5 https://192.168.31.79/
# 预期：404（Django 无 / 路由）

# 证书信息
curl -sk -v https://192.168.31.79/ 2>&1 | grep -E "subject|expire"
# 预期：subject=CN = 192.168.31.79
```

### 5.2 Django 接口测试

```bash
# 登录（自签名证书用 -k）
curl -sk -X POST https://192.168.31.79/my_api/userman/user/loginWithForce/ \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"Test@12345","client_time":1789443257484,"client_other_time":1651766400000}'
# 预期：返回 token

# 业务接口（用上面拿到的 token）
curl -sk -H "Authorization: Token $TOKEN" https://192.168.31.79/my_api/sysman/authUser/
# 预期：200 + count + results
```

### 5.3 证书信息

```bash
"C:/Program Files/Git/usr/bin/openssl.exe" x509 -in "C:/nginx-1.21.1/conf/ssl/vgis.crt" -noout -dates -subject -issuer -ext subjectAltName
```

### 5.4 Postman 集合回归

修改 `E:/claudecode/run_postman_collection.py` 的 `HOST` 为 `https://192.168.31.79`，跑 v4-safe 模式（跳 DELETE/PUT/PATCH）：
```bash
PYTHONIOENCODING=utf-8 python "E:/claudecode/run_postman_collection.py"
# 预期：PASS ≥ 65，PASS_400 ≥ 8，EXPECTED ≥ 11，FAIL ≤ 14（业务/集合层，非传输）
```

### 5.5 nginx 日志

```bash
tail -f C:/nginx-1.21.1/logs/vgis_https_access.log
tail -f C:/nginx-1.21.1/logs/vgis_https_error.log
tail -f C:/nginx-1.21.1/logs/cert-renew.log
```

### 5.6 任务计划

```cmd
schtasks /Query /TN vgis_https_cert_renew /V /FO LIST
```

---

## 6. 客户端证书信任

**自签名证书不在公共 CA 信任链**，客户端首次访问会警告。

### 6.1 浏览器

- Chrome/Edge：访问 `https://192.168.31.79/` → "您的连接不是私密连接" → 点击 "高级" → "继续前往 192.168.31.79（不安全）"
- Firefox：类似，"接受风险并继续"
- 永久信任：把 `C:\nginx-1.21.1\conf\ssl\vgis.crt` 拷贝到客户端机器，双击安装到 "受信任的根证书颁发机构"

### 6.2 Postman

- Settings → Certificates → CA Certificates → 添加 `vgis.crt`
- 或：请求 URL 旁 "Disable SSL Verification" 勾选（开发期）

### 6.3 curl

```bash
curl -k ...   # 单次跳过证书验证
curl --cacert /path/to/vgis.crt ...   # 用本机证书库验证
```

---

## 7. 回滚方案

### 7.1 临时停 HTTPS

```bash
# 停 nginx（注意：80 端口也会停，10846 直连不受影响）
"C:/nginx-1.21.1/nginx.exe" -s stop

# 此时 Django 仍可通过 10846 直连访问：
curl http://192.168.31.79:10846/
```

### 7.2 恢复原 nginx 配置

```bash
cp "C:/nginx-1.21.1/conf/nginx.conf.bak" "C:/nginx-1.21.1/conf/nginx.conf"
"C:/nginx-1.21.1/nginx.exe" -s reload
```

### 7.3 完全卸载

```bash
"C:/nginx-1.21.1/nginx.exe" -s stop
"C:/nginx-1.21.1/nginx.exe" -s uninstall    # 移除 Windows 服务（如装了）
schtasks /Delete /TN vgis_https_cert_renew /F
# 删除证书和脚本
rm -rf "C:/nginx-1.21.1/conf/ssl/"
rm -f "C:/nginx-1.21.1/scripts/"*.ps1
```

---

## 8. 关键风险与备选

| 风险 | 应对 |
|---|---|
| OpenSSL 路径变了 | 修改 `gen-cert.ps1` 与 `renew-cert-task.ps1` 的 `$OPENSSL` 变量 |
| nginx 配置冲突 | 用唯一 zone 名（如 `SSL_VGIS`），避免与已有 SSL zone 冲突 |
| Task Scheduler 权限 | 脚本需 SYSTEM 权限 → 手动以管理员运行 `register-task-admin.ps1` |
| 443 端口被占用 | `netstat -ano \| findstr ":443"` 查占用，改 nginx listen |
| 防火墙拦截 443 | `netsh advfirewall firewall add rule name="VGIS HTTPS" dir=in action=allow protocol=TCP localport=443` |
| Django ALLOWED_HOSTS 严格化 | 当前是 `['*']`，如收紧需加 `192.168.31.79` |
| 证书过期未续（任务挂了） | 监控脚本或手动跑 `renew-cert-task.ps1` |

---

## 9. 性能参考（2026-09-15 实测）

| 指标 | HTTP 直连 10846 | HTTPS 经 nginx 443 |
|---|---|---|
| 登录接口响应 | ~450ms | ~460ms |
| authUser list p95 | 36ms | 40ms |
| 5xx 错误率 | 0 | 0 |
| 吞吐 | ~162 req/s (50 并发) | ~155 req/s（受 nginx -c 1 worker 限制） |

> 进一步提升需 nginx 多 worker（Windows 上较繁琐，建议 Linux + gunicorn）。

---

## 10. 当前状态（2026-09-15 验证通过）

- ✅ 自签名证书生成成功（90 天有效期，SAN 含 192.168.31.79）
- ✅ nginx 配置语法 OK，443/80 监听
- ✅ HTTPS 反代 Django 正常，token 鉴权通过
- ✅ 续期脚本正常工作（手动跑：89 天剩余 > 30 跳过）
- ✅ Postman 集合回归：155 条请求通过，综合 OK 84/155（仅业务/集合层问题）
- ⚠️ Task Scheduler 计划任务：脚本 OK，**手动以管理员身份**执行 `register-task-admin.ps1` 注册

---

## 11. 部署时间线

```
2026-09-15 17:30  gen-cert.ps1: 生成证书 vgis.crt (Sep 15 - Dec 14)
2026-09-15 17:31  nginx 配置测试通过 + 启动
2026-09-15 17:32  80→443 重定向验证 (HTTP 301)
2026-09-15 17:33  HTTPS 登录接口验证 (返回 token)
2026-09-15 17:34  HTTPS 业务接口验证 (authUser list HTTP 200)
2026-09-15 17:43  renew-cert-task.ps1 实测 (89 天剩余 > 30 跳过)
2026-09-15 17:45  Postman 集合 HTTPS 回归 (PASS 65, FAIL 14 业务层)
2026-09-15 17:46  注册 Task Scheduler 计划 (待管理员手动执行 register-task-admin.ps1)
```

下次证书过期：2026-12-14（届时自动续期脚本会再生一张新证书并 reload nginx）。
