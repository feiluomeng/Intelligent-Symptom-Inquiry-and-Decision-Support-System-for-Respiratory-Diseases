# test_performance.py
# -*- coding: utf-8 -*-
"""
性能测试脚本：比较“首次请求（预计未命中缓存）”与“重复请求（命中缓存）”的响应时间。
使用方法：
1) 先启动你的 Flask 后端（确保 /api/search 可访问）
2) 在另一个终端运行：python test_performance.py
"""

import time
import json
import statistics as stats
from dataclasses import dataclass
from typing import Dict, List, Tuple
import requests

# ============ 可配置区域 ============
BASE_URL = "http://127.0.0.1:5000"
API_PATH = "/api/search"
URL = BASE_URL + API_PATH

TIMEOUT = 20   # 单次请求超时时间（秒）
REPEATS = 20   # 重复请求次数（用于统计缓存命中性能）

# 分别测试关键词模式与自由文本模式
PAYLOADS = [
    {"name": "keyword_Cough", "body": {"symptom": "Cough", "searchType": "1"}},
    {"name": "text_SoreThroat", "body": {"symptom": "I have a sore throat.", "searchType": "2"}},
]

HEADERS = {"Content-Type": "application/json"}
# ===================================

@dataclass
class RunStats:
    label: str
    n: int
    times: List[float]
    ok_cnt: int
    err_cnt: int
    sample_result_len: int

    def summary(self) -> Dict[str, float]:
        """统计平均值、中位数、极值和标准差"""
        if not self.times:
            return {}
        return {
            "mean": sum(self.times) / len(self.times),
            "median": stats.median(self.times),
            "min": min(self.times),
            "max": max(self.times),
            "stdev": stats.pstdev(self.times) if len(self.times) > 1 else 0.0,
        }


def call_once(payload: Dict) -> Tuple[float, bool, int, str]:
    """发起一次请求，返回：(耗时, 是否success, 结果条数, 错误信息)"""
    start = time.perf_counter()
    err = ""
    result_len = -1
    ok = False
    try:
        r = requests.post(URL, headers=HEADERS, json=payload, timeout=TIMEOUT)
        elapsed = time.perf_counter() - start
        try:
            data = r.json()
        except Exception as e:
            return elapsed, False, -1, f"JSON parse error: {e}"

        if isinstance(data, dict) and data.get("success") is True and isinstance(data.get("results"), list):
            ok = True
            result_len = len(data["results"])
        else:
            ok = False
            err = str(data.get("error", f"unexpected response: {data}"))
        return elapsed, ok, result_len, err
    except requests.exceptions.RequestException as e:
        elapsed = time.perf_counter() - start
        return elapsed, False, -1, f"HTTP error: {e}"


def run_case(name: str, payload: Dict, repeats: int) -> None:
    """运行单个测试用例"""
    print("=" * 70)
    print(f"[CASE] {name}")
    print(f"POST {URL}")
    print("Payload:", json.dumps(payload, ensure_ascii=False))
    print("-" * 70)

    # 首次请求（预计未命中缓存）
    t_first, ok_first, len_first, err_first = call_once(payload)
    print(f"First request : {t_first:.4f}s | success={ok_first} | results={len_first} | err={err_first}")

    # 重复请求（命中缓存）
    times_hit: List[float] = []
    ok_cnt = 0
    err_cnt = 0
    sample_len = -1

    for _ in range(repeats - 1):  # 已经请求了1次，再请求 (repeats-1) 次
        t, ok, result_len, err = call_once(payload)
        times_hit.append(t)
        ok_cnt += 1 if ok else 0
        err_cnt += 0 if ok else 1
        if sample_len < 0 and result_len >= 0:
            sample_len = result_len

    # 汇总
    if times_hit:
        s = RunStats(
            label=f"{name}_cached_hits",
            n=len(times_hit),
            times=times_hit,
            ok_cnt=ok_cnt,
            err_cnt=err_cnt,
            sample_result_len=sample_len if sample_len >= 0 else len_first,
        )
        smry = s.summary()
        print("-" * 70)
        print(f"Repeated requests ({s.n} times):")
        print(f"  Avg : {smry.get('mean', 0):.4f}s")
        print(f"  Median : {smry.get('median', 0):.4f}s")
        print(f"  Min : {smry.get('min', 0):.4f}s")
        print(f"  Max : {smry.get('max', 0):.4f}s")
        print(f"  Std dev : {smry.get('stdev', 0):.4f}s")
        print(f"  Success : {s.ok_cnt} / {s.n}")
        print(f"  Sample result length : {s.sample_result_len}")
    print("=" * 70 + "\n")


def main():
    print("\n=== Respiratory Symptom DSS - Performance Test ===\n")
    print(f"Target: {URL}\n")
    for p in PAYLOADS:
        run_case(p["name"], p["body"], REPEATS)

    print("Hint: To force 'first request (cache miss)', you can either:")
    print("1) Restart the backend (clear in-memory cache), or")
    print("2) Change the symptom text to generate a new cache key.\n")


if __name__ == "__main__":
    main()
