#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
perf_baseline.py
对 VGIS Django 框架的 8 个核心接口做 N 轮调用，记录 min/avg/max/p95 耗时。
输出到指定文件（默认 stdout），便于阶段间 diff。

调用方式（venv_6.06）：
    python tools/perf_baseline.py --rounds 5 --host 127.0.0.1 --port 10846 > baseline_v0.txt
"""
import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request

# 避免被 settings 误加载
sys.path.insert(0, '.')


def _http_post(url, payload, token=None):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    if token:
        req.add_header('Authorization', 'Token ' + token)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8', errors='replace')
            return time.perf_counter() - t0, resp.status, body
    except urllib.error.HTTPError as e:
        return time.perf_counter() - t0, e.code, e.read().decode('utf-8', errors='replace')
    except Exception as e:
        return time.perf_counter() - t0, -1, str(e)


def _http_get(url, token=None):
    req = urllib.request.Request(url, method='GET')
    if token:
        req.add_header('Authorization', 'Token ' + token)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8', errors='replace')
            return time.perf_counter() - t0, resp.status, body
    except urllib.error.HTTPError as e:
        return time.perf_counter() - t0, e.code, e.read().decode('utf-8', errors='replace')
    except Exception as e:
        return time.perf_counter() - t0, -1, str(e)


def _summary(elapsed_list):
    if not elapsed_list:
        return (0, 0, 0, 0, 0)
    # p95
    p95 = statistics.quantiles(elapsed_list, n=20, method='inclusive')[18] \
        if len(elapsed_list) >= 5 else max(elapsed_list)
    return (
        min(elapsed_list),
        statistics.mean(elapsed_list),
        max(elapsed_list),
        p95,
        len(elapsed_list),
    )


def _fmt(label, samples):
    """samples is list of (elapsed_ms, status)"""
    if not samples:
        return f"{label}: no samples"
    elapsed = [s[0] for s in samples]
    statuses = [s[1] for s in samples]
    n_ok = sum(1 for s in statuses if 200 <= s < 300)
    n_err = sum(1 for s in statuses if s >= 400 or s < 0)
    mn, avg, mx, p95, n = _summary(elapsed)
    return (f"{label:<55} n={n:<3} 200={n_ok:<3} err={n_err:<3} "
            f"min={mn*1000:7.2f}ms avg={avg*1000:7.2f}ms "
            f"max={mx*1000:7.2f}ms p95={p95*1000:7.2f}ms")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', default='10846')
    p.add_argument('--rounds', type=int, default=5)
    p.add_argument('--user', default='admin')
    p.add_argument('--password', default='Test@12345')
    p.add_argument('--client-time', default='1789000000000')
    args = p.parse_args()

    base = f"http://{args.host}:{args.port}"
    print(f"# Baseline @ {base}  rounds={args.rounds}  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 第 1 步：登录拿 token（不在测速内）
    login_url = f"{base}/my_api/userman/user/loginWithForce/"
    login_payload = {
        "username": args.user,
        "password": args.password,
        # 注意：license_authorize 内部会做 license_time >= client_time 比较，
        # 若 client_time 是 str 会抛 TypeError；必须传 int
        "client_time": int(args.client_time),
    }
    _, status, body = _http_post(login_url, login_payload)
    print(f"# login init: status={status}")
    if status != 200:
        print("# !! login failed, baseline abort.")
        print(body[:300])
        sys.exit(1)
    try:
        token = json.loads(body).get("token") or json.loads(body).get("info", {}).get("token")
    except Exception:
        token = None
    print(f"# token={token[:8] if token else 'None'}...")
    print()

    # 第 2 步：定义 8 个接口 + 自定义 method
    # 实际 URL 前缀是 /my_api/（见 my_project/urls.py + 各模块的 urls.py）
    # 注意：用户列表的 sqlsearch 实际挂在 authUser 上（SysUserViewSet 没有 sqlsearch action）
    endpoints = [
        ("login (re-login)",
         lambda: _http_post(login_url, login_payload)),
        ("authUser list (12 users)",
         lambda: _http_get(f"{base}/my_api/sysman/authUser/", token)),
        ("authUser sqlsearch",
         lambda: _http_get(f"{base}/my_api/sysman/authUser/sqlsearch/", token)),
        ("sysDepartment sqlsearch",
         lambda: _http_get(f"{base}/my_api/sysman/sysDepartment/sqlsearch/", token)),
        ("sysRole sqlsearch",
         lambda: _http_get(f"{base}/my_api/sysman/sysRole/sqlsearch/", token)),
        ("sysMenu list",
         lambda: _http_get(f"{base}/my_api/sysman/sysMenu/", token)),
        ("sysParam list",
         lambda: _http_get(f"{base}/my_api/sysman/sysParam/", token)),
        ("sysLog sqlsearch",
         lambda: _http_get(f"{base}/my_api/sysman/sysLog/sqlsearch/", token)),
    ]

    # 每轮顺序跑，缓存每接口耗时
    summary = {label: [] for label, _ in endpoints}
    for round_idx in range(1, args.rounds + 1):
        print(f"--- round {round_idx} ---")
        # 每轮重登录一次：loginWithForce 会把上一轮 token 顶掉，缓存里的 token 会失效，
        # 这里必须刷新变量，否则后续 GET 全 401。
        for label, fn in endpoints:
            elapsed, status, body = fn()
            # 如果当前调用是 re-login，则从响应里抓新的 token 刷新变量
            if label.startswith("login"):
                try:
                    new_token = json.loads(body).get("token")
                    if new_token:
                        token = new_token
                except Exception:
                    pass
            summary[label].append((elapsed, status))
            print(f"  {label:<55} status={status:<4} {elapsed*1000:7.2f}ms")

    print()
    print("# ====================== SUMMARY ======================")
    for label, _ in endpoints:
        print(_fmt(label, summary[label]))


if __name__ == "__main__":
    main()
