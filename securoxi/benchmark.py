"""
SECUROXI AI Performance & Latency Benchmark Framework
Measures parsing latency, visual analyzer latency, prompt analyzer latency, AI reasoning latency,
total scan latency, throughput (spans/sec), and peak memory usage across Small, Medium, and Large PDFs.
"""

import os
import sys
import time
import tracemalloc
import pymupdf as fitz
from typing import Dict, Any, List
from securoxi.scanner import SecuroxiScanner
from securoxi.config import SecuroxiConfig


BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "benchmarks"))


def generate_benchmark_pdf(filename: str, pages: int, text_per_page: int) -> str:
    """Generates synthetic benchmark PDFs of specified page and span count."""
    os.makedirs(BENCHMARK_DIR, exist_ok=True)
    filepath = os.path.join(BENCHMARK_DIR, filename)
    doc = fitz.open()

    sample_lines = [
        "Jane Doe - Senior Software Engineer & Cloud Architect.",
        "10+ years experience building distributed microservices in Go and Python.",
        "Managed Kubernetes clusters handling 50,000 requests per second.",
        "Implemented zero-trust security architecture across cloud environments.",
        "Published research on static analysis and automated vulnerability detection."
    ]

    for p in range(pages):
        page = doc.new_page(width=595, height=842)
        y = 50
        for i in range(text_per_page):
            line = sample_lines[i % len(sample_lines)]
            page.insert_text(fitz.Point(50, y), line, fontsize=10)
            y += 15
            if y > 800:
                y = 50

    doc.save(filepath)
    doc.close()
    return filepath


def run_benchmarks() -> List[Dict[str, Any]]:
    """Runs performance benchmark suite across Small, Medium, and Large PDF workloads."""
    config = SecuroxiConfig(ai_reasoning_enabled=True)
    scanner = SecuroxiScanner(config=config)

    test_specs = [
        {"name": "Small PDF", "filename": "benchmark_small.pdf", "pages": 1, "lines_per_page": 10},
        {"name": "Medium PDF", "filename": "benchmark_medium.pdf", "pages": 10, "lines_per_page": 50},
        {"name": "Large PDF", "filename": "benchmark_large.pdf", "pages": 50, "lines_per_page": 100}
    ]

    results = []

    print("\n======================================================================")
    print("  SECUROXI AI PERFORMANCE & RESOURCE LATENCY BENCHMARK")
    print("======================================================================")

    for spec in test_specs:
        pdf_path = generate_benchmark_pdf(spec["filename"], spec["pages"], spec["lines_per_page"])
        file_size_kb = os.path.getsize(pdf_path) / 1024.0

        tracemalloc.start()
        t0 = time.time()
        report = scanner.scan(pdf_path)
        total_time_ms = (time.time() - t0) * 1000
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        timing = report.metadata.get("timing_ms", {})
        total_spans = report.total_spans_analyzed
        throughput = (total_spans / (total_time_ms / 1000.0)) if total_time_ms > 0 else 0

        res = {
            "name": spec["name"],
            "filename": spec["filename"],
            "pages": spec["pages"],
            "file_size_kb": round(file_size_kb, 1),
            "total_spans": total_spans,
            "parsing_latency_ms": timing.get("parsing_latency_ms", 0.0),
            "visual_latency_ms": timing.get("visual_analyzer_latency_ms", 0.0),
            "prompt_latency_ms": timing.get("prompt_analyzer_latency_ms", 0.0),
            "ai_latency_ms": timing.get("ai_reasoning_latency_ms", 0.0),
            "total_latency_ms": round(total_time_ms, 2),
            "throughput_spans_per_sec": round(throughput, 0),
            "peak_memory_mb": round(peak_mem / (1024 * 1024), 2)
        }
        results.append(res)

        print(f"[{res['name']}] Size: {res['file_size_kb']} KB | Pages: {res['pages']} | Spans: {res['total_spans']}")
        print(f"   • Parse Latency : {res['parsing_latency_ms']} ms")
        print(f"   • Visual Latency: {res['visual_latency_ms']} ms")
        print(f"   • Prompt Latency: {res['prompt_latency_ms']} ms")
        print(f"   • AI Latency    : {res['ai_latency_ms']} ms")
        print(f"   • Total Latency : {res['total_latency_ms']} ms")
        print(f"   • Throughput    : {res['throughput_spans_per_sec']} spans/sec")
        print(f"   • Peak Memory   : {res['peak_memory_mb']} MB\n")

    return results


if __name__ == "__main__":
    run_benchmarks()
