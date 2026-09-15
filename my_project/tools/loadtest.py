#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
loadtest.py
50 并发 × 20 轮压测 8 个核心接口。
输出 p50/p95/p99 + 5xx 计数。

调用方式（venv_6.06）：
    python tools/loadtest.py --users 50 --rounds 20 --port 10846

注意：不读 count/next/previous 字段（API 契约里没有），只看 latency 与 HTTP 状态码。
"""
import argparse
import asyncio
import json
import statistics
import sys
import time
import urllib.error
import urllib.request

# 强制无 proxy（避免本地 aiohttp 误读环境变量走代理）
import os
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

try:
    import aiohttp
except ImportError:
    print("# aiohttp not installed; run: pip install aiohttp")
    sys.exit(1)


async def _post(session, url, payload, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Token ' + token
    t0 = time.perf_counter()
    try:
        async with session.post(url, json=payload, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=30)) as resp:
            await resp.read()
            elapsed = time.perf_counter() - t0
            return elapsed, resp.status, await resp.text()
    except Exception as e:
        return time.perf_counter() - t0, -1, str(e)


async def _get(session, url, token=None):
    headers = {}
    if token:
        headers['Authorization'] = 'Token ' + token
    t0 = time.perf_counter()
    try:
        async with session.get(url, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=30)) as resp:
            await resp.read()
            elapsed = time.perf_counter() - t0
            return elapsed, resp.status, await resp.text()
    except Exception as e:
        return time.perf_counter() - t0, -1, str(e)


def _quantiles(elapsed_list):
    if not elapsed_list:
        return (0, 0, 0, 0)
    s = sorted(elapsed_list)
    n = len(s)
    p50 = s[int(n * 0.5)]
    p95 = s[min(int(n * 0.95), n - 1)]
    p99 = s[min(int(n * 0.99), n - 1)]
    return p50, p95, p99, max(s)


async def worker_loop(uid, rounds, base, endpoints, token, results):
    """
    每个 worker 跑 rounds 轮，每轮 8 个 GET（共享 token）。
    关键：loginWithForce 在并发下会互踢（删旧 token 建新 token），
    这里改为：测试开始前只登录一次，所有 worker 复用同一 token。
    """
    async with aiohttp.ClientSession() as session:
        for r in range(rounds):
            for label, path in endpoints:
                elapsed, status, _ = await _get(
                    session, f"{base}{path}", token)
                results[label].append((elapsed, status))


async def main_async(args):
    base = f"http://127.0.0.1:{args.port}"
    endpoints = [
        ('authUser_list',     '/my_api/sysman/authUser/'),
        ('authUser_sqlsearch', '/my_api/sysman/authUser/sqlsearch/'),
        ('sysDept_sqlsearch', '/my_api/sysman/sysDepartment/sqlsearch/'),
        ('sysRole_sqlsearch',  '/my_api/sysman/sysRole/sqlsearch/'),
        ('sysMenu_list',       '/my_api/sysman/sysMenu/'),
        ('sysParam_list',      '/my_api/sysman/sysParam/'),
        ('sysLog_sqlsearch',   '/my_api/sysman/sysLog/sqlsearch/'),
    ]
    login_payload = {
        'username': args.user,
        'password': args.password,
        'client_time': int(args.client_time),
    }
    results = {}
    for label, _ in endpoints:
        results[label] = []

    # 1) 测试开始前登录一次：拿到一个稳定的 token 给所有 worker 复用。
    #    注意：必须等前一个 login 完全结束才能再 login，否则 loginWithForce 会互踢。
    async with aiohttp.ClientSession() as session:
        elapsed, status, body = await _post(
            session, f"{base}/my_api/userman/user/loginWithForce/", login_payload)
        print(f"# Pre-login: status={status}  elapsed={elapsed*1000:.1f}ms")
        if status != 200:
            print("# !! login failed, abort loadtest.")
            print(body[:300])
            return
        try:
            token = json.loads(body).get('token')
        except Exception:
            token = None
        if not token:
            print("# !! no token in response, abort.")
            return
        print(f"# token={token[:8]}...  (shared by all {args.users} workers)")

    print(f"# Loadtest @ {base}  users={args.users}  rounds={args.rounds}  "
          f"{time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 启动 N 个 worker，每个 worker 自己跑 rounds 轮
    tasks = [
        asyncio.create_task(
            worker_loop(uid, args.rounds, base, endpoints, token, results)
        )
        for uid in range(args.users)
    ]
    t0 = time.perf_counter()
    await asyncio.gather(*tasks)
    total_time = time.perf_counter() - t0
    total_reqs = sum(len(v) for v in results.values())
    print(f"\n# Done in {total_time:.1f}s, total {total_reqs} requests, "
          f"throughput {total_reqs / total_time:.0f} req/s\n")
    print("# ====================== LOADTEST RESULT ======================")
    for label, _ in endpoints:
        print(_fmt(label, results[label]))


def _fmt(label, samples):
    if not samples:
        return f"{label}: no samples"
    elapsed = [s[0] for s in samples]
    statuses = [s[1] for s in samples]
    n_ok = sum(1 for s in statuses if 200 <= s < 300)
    n_4xx = sum(1 for s in statuses if 400 <= s < 500)
    n_5xx = sum(1 for s in statuses if s >= 500 or s < 0)
    p50, p95, p99, mx = _quantiles(elapsed)
    # 状态码分布（top 5）
    from collections import Counter
    top = Counter(statuses).most_common(5)
    top_str = " ".join(f"{c}={n}" for c, n in top)
    return (f"{label:<40} n={len(samples):<5} 2xx={n_ok:<5} 4xx={n_4xx:<5} 5xx={n_5xx:<3} "
            f"p50={p50*1000:7.2f}ms p95={p95*1000:7.2f}ms "
            f"p99={p99*1000:7.2f}ms max={mx*1000:7.2f}ms [{top_str}]")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', default='10846')
    p.add_argument('--users', type=int, default=50)
    p.add_argument('--rounds', type=int, default=20)
    p.add_argument('--user', default='admin')
    p.add_argument('--password', default='Test@12345')
    p.add_argument('--client-time', default='1789000000000')
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == '__main__':
    main()
