"""
SECUROXI AI Phase 2 Stage 10 — Performance & Throughput Benchmarking Framework
Measures screening latency, multi-candidate ranking throughput, and peak memory consumption.
"""

import time
import os
import resource
from typing import Dict, Any
from securoxi.config import SecuroxiConfig
from securoxi.screening.eval_dataset import generate_phase2_evaluation_dataset, EVAL_FIXTURES_DIR
from securoxi.screening.pipeline import SecuroxiScreeningPipeline


def get_peak_memory_mb() -> float:
    """Returns peak memory usage in Megabytes."""
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # On macOS ru_maxrss is in bytes
    return usage / (1024.0 * 1024.0)


def run_screening_benchmarks() -> Dict[str, Any]:
    """
    Executes Performance & Ranking Throughput Benchmarks.
    """
    config = SecuroxiConfig()
    pipeline = SecuroxiScreeningPipeline(config=config)
    dataset = generate_phase2_evaluation_dataset()

    jd_path = os.path.join(EVAL_FIXTURES_DIR, "..", "phase2", "sample_jd.txt")

    # 1. Single Resume Screening Latency
    single_pdf = dataset[0]["filepath"]
    start_time = time.perf_counter()
    res = pipeline.screen_resume(single_pdf, jd_path)
    single_latency_ms = (time.perf_counter() - start_time) * 1000.0

    # 2. Batch Multi-Candidate Ranking (5 Candidates)
    batch_5_paths = [d["filepath"] for d in dataset[:5]]
    start_batch_5 = time.perf_counter()
    rank_res_5 = pipeline.rank_resumes(batch_5_paths, jd_source=jd_path)
    batch_5_latency_ms = (time.perf_counter() - start_batch_5) * 1000.0

    # 3. Full Batch Multi-Candidate Ranking (20 Candidates)
    batch_20_paths = [d["filepath"] for d in dataset]
    start_batch_20 = time.perf_counter()
    rank_res_20 = pipeline.rank_resumes(batch_20_paths, jd_source=jd_path)
    batch_20_latency_ms = (time.perf_counter() - start_batch_20) * 1000.0

    throughput_resumes_per_sec = (len(dataset) / (batch_20_latency_ms / 1000.0)) if batch_20_latency_ms > 0 else 0.0

    return {
        "single_resume_latency_ms": round(single_latency_ms, 2),
        "batch_5_ranking_latency_ms": round(batch_5_latency_ms, 2),
        "batch_20_ranking_latency_ms": round(batch_20_latency_ms, 2),
        "throughput_resumes_per_sec": round(throughput_resumes_per_sec, 2),
        "peak_memory_mb": round(get_peak_memory_mb(), 2)
    }


if __name__ == "__main__":
    bench = run_screening_benchmarks()
    print("=" * 60)
    print("SECUROXI AI Phase 2 Screening Performance Benchmarks")
    print("=" * 60)
    print(f"Single Resume Latency: {bench['single_resume_latency_ms']} ms")
    print(f"5-Candidate Ranking Latency: {bench['batch_5_ranking_latency_ms']} ms")
    print(f"20-Candidate Ranking Latency: {bench['batch_20_ranking_latency_ms']} ms")
    print(f"Throughput: {bench['throughput_resumes_per_sec']} resumes / sec")
    print(f"Peak Memory: {bench['peak_memory_mb']} MB")
    print("=" * 60)
