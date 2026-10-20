#!/usr/bin/env python3
"""
LingCast High-Concurrency Stress Testing Script
Simulates live streaming peak load: concurrent barrage ingestion, DFA sensitive word filtering,
LLM orchestration pipeline and TTS prefetching queue under stress.
"""

import sys
import os
import time
import asyncio
import argparse
import random
from typing import List, Dict, Any

# Ensure project root and server root are in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "server"))

from server.core.compliance import DFASensitiveFilter, audit_text_compliance
from server.services.live_orchestrator import LiveOrchestrator

# Test sample data
SAMPLE_BARRAGES = [
    "主播这件衣服怎么卖？有没有优惠券？",
    "请问发货时间是多久？顺丰包邮吗？",
    "支持七天无理由退换货吗？质量怎么样？",
    "衣服版型偏大还是偏小？身高170体重120穿什么尺码？",
    "全网首发顶级工艺！独家首创史无前例！",  # Trigger advertising violations
    "主播声音好听，能再唱首歌吗？",
    "这个价格太划算了，已经下单3件了！",
    "有没有其他颜色可以选择？喜欢黑色款",
    "透视外挂赌博洗钱代开发票测试词",      # Trigger fraud/illegal violations
    "客服态度真好，数字人直播好逼真啊！",
]


async def benchmark_compliance(total_requests: int, concurrency: int) -> Dict[str, Any]:
    """Benchmark DFA Sensitive Filter and PII masking throughput."""
    filter_instance = DFASensitiveFilter()
    semaphore = asyncio.Semaphore(concurrency)
    latencies: List[float] = []
    blocked_count = 0

    async def worker(text: str):
        nonlocal blocked_count
        async with semaphore:
            start = time.perf_counter()
            res = audit_text_compliance(text)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            latencies.append(elapsed_ms)
            if not res["is_compliant"]:
                blocked_count += 1

    tasks = [
        worker(random.choice(SAMPLE_BARRAGES))
        for _ in range(total_requests)
    ]

    start_total = time.perf_counter()
    await asyncio.gather(*tasks)
    total_duration = time.perf_counter() - start_total

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p90 = latencies[int(len(latencies) * 0.90)]
    p99 = latencies[int(len(latencies) * 0.99)]
    qps = total_requests / total_duration if total_duration > 0 else 0

    return {
        "module": "DFA Compliance & PII Masking",
        "total_requests": total_requests,
        "concurrency": concurrency,
        "total_duration_sec": round(total_duration, 4),
        "qps": round(qps, 2),
        "p50_ms": round(p50, 4),
        "p90_ms": round(p90, 4),
        "p99_ms": round(p99, 4),
        "blocked_count": blocked_count,
    }


async def benchmark_orchestrator(total_requests: int, concurrency: int) -> Dict[str, Any]:
    """Benchmark LiveOrchestrator pipeline (Danmaku Ingestion + Queue Scheduling)."""
    orchestrator = LiveOrchestrator(
        session_id=999,
        room_id="benchmark_room",
        avatar_id=1,
        stream_key="benchmark_stream"
    )
    semaphore = asyncio.Semaphore(concurrency)
    latencies: List[float] = []

    async def worker(user: str, msg: str):
        async with semaphore:
            start = time.perf_counter()
            await orchestrator.enqueue_danmaku(sender=user, content=msg)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            latencies.append(elapsed_ms)

    tasks = []
    for i in range(total_requests):
        tasks.append(
            worker(
                user=f"user_{random.randint(1000, 9999)}",
                msg=random.choice(SAMPLE_BARRAGES)
            )
        )

    start_total = time.perf_counter()
    await asyncio.gather(*tasks)
    total_duration = time.perf_counter() - start_total

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p90 = latencies[int(len(latencies) * 0.90)]
    p99 = latencies[int(len(latencies) * 0.99)]
    qps = total_requests / total_duration if total_duration > 0 else 0

    return {
        "module": "Live Orchestrator Pipeline",
        "total_requests": total_requests,
        "concurrency": concurrency,
        "total_duration_sec": round(total_duration, 4),
        "qps": round(qps, 2),
        "p50_ms": round(p50, 4),
        "p90_ms": round(p90, 4),
        "p99_ms": round(p99, 4),
    }


def print_report(res: Dict[str, Any]):
    print("=" * 60)
    print(f"BENCHMARK REPORT: {res['module']}")
    print("=" * 60)
    print(f"Total Requests:      {res['total_requests']}")
    print(f"Concurrency Level:   {res['concurrency']}")
    print(f"Total Time Taken:    {res['total_duration_sec']}s")
    print(f"Throughput (QPS):    {res['qps']} req/sec")
    print(f"Latency P50:         {res['p50_ms']} ms")
    print(f"Latency P90:         {res['p90_ms']} ms")
    print(f"Latency P99:         {res['p99_ms']} ms")
    if "blocked_count" in res:
        print(f"Violations Blocked:  {res['blocked_count']}")
    print("=" * 60 + "\n")


async def main():
    parser = argparse.ArgumentParser(description="LingCast High-Concurrency Stress Test")
    parser.add_argument("--total", type=int, default=500, help="Total number of requests (default: 500)")
    parser.add_argument("--concurrency", type=int, default=50, help="Concurrency level (default: 50)")
    args = parser.parse_args()

    print(f"\n🚀 Starting LingCast Load Benchmark (Total: {args.total}, Concurrency: {args.concurrency})...\n")

    # 1. Benchmark DFA Compliance
    dfa_res = await benchmark_compliance(args.total, args.concurrency)
    print_report(dfa_res)

    # 2. Benchmark Live Orchestrator
    orch_res = await benchmark_orchestrator(args.total, args.concurrency)
    print_report(orch_res)

    print("✅ All stress benchmarks executed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
