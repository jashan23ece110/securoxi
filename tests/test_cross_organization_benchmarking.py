"""
SECUROXI AI Intelligence 2.0 — Cross-Organization Benchmarking Test Suite (Phase 9 Stage 58)
Validates privacy-preserving benchmark aggregation, k-anonymity suppression,
comparative insights, opt-out governance, and optimization recommendations.
"""

import pytest
from securoxi.enterprise.benchmarking import (
    CrossOrgBenchmarkingEngine,
    ParticipationState,
    BenchmarkDomain,
    ConfidenceLevel,
)


# =========================================================================
# 1. REGISTRATION, SUBMISSION & SMALL-SAMPLE SUPPRESSION
# =========================================================================

def test_small_sample_suppression():
    """Verifies that benchmarks with fewer than min_sample_size (k-anonymity) are suppressed."""
    engine = CrossOrgBenchmarkingEngine()

    bm = engine.register_benchmark(
        domain=BenchmarkDomain.HIRING,
        metric_name="screening_latency",
        min_sample_size=5,
    )

    # Opt in and submit metrics for only 3 organizations (< 5)
    for i in range(3):
        org = f"ORG-{i}"
        engine.set_participation(org, ParticipationState.PARTICIPATING)
        engine.submit_metric(org, "screening_latency", 4.0 + i)

    # Compute benchmark -> Must be suppressed
    dataset = engine.compute_benchmark(bm.benchmark_id)
    assert dataset.is_suppressed is True
    assert dataset.sample_count == 3

    # Query comparison -> Must return BENCHMARK_UNAVAILABLE
    comp = engine.get_benchmark_comparison("ORG-0", "screening_latency")
    assert comp.status == "BENCHMARK_UNAVAILABLE"
    assert comp.confidence == ConfidenceLevel.INSUFFICIENT_DATA


# =========================================================================
# 2. VALID AGGREGATION & ANONYMIZED PEER COMPARISON
# =========================================================================

def test_valid_benchmark_aggregation_and_comparison():
    """Verifies statistical distribution calculation and anonymized percentiles."""
    engine = CrossOrgBenchmarkingEngine()

    bm = engine.register_benchmark(
        domain=BenchmarkDomain.HIRING,
        metric_name="screening_latency",
        min_sample_size=5,
    )

    # Submit metrics for 6 organizations
    latencies = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    for i, lat in enumerate(latencies):
        org = f"ORG-{i}"
        engine.set_participation(org, ParticipationState.PARTICIPATING)
        engine.submit_metric(org, "screening_latency", lat)

    dataset = engine.compute_benchmark(bm.benchmark_id)
    assert dataset.is_suppressed is False
    assert dataset.sample_count == 6
    assert dataset.median_value == 4.5

    # Org-0 (latency 2.0) -> TOP_QUARTILE
    comp_fast = engine.get_benchmark_comparison("ORG-0", "screening_latency")
    assert comp_fast.status == "SUCCESS"
    assert comp_fast.percentile_bucket == "TOP_QUARTILE"
    assert comp_fast.organization_value == 2.0
    assert comp_fast.cohort_median == 4.5

    # Org-5 (latency 7.0) -> BELOW_MEDIAN
    comp_slow = engine.get_benchmark_comparison("ORG-5", "screening_latency")
    assert comp_slow.status == "SUCCESS"
    assert comp_slow.percentile_bucket == "BELOW_MEDIAN"


# =========================================================================
# 3. OPT-OUT GOVERNANCE & OPTIMIZATION RECOMMENDATIONS
# =========================================================================

def test_opt_out_governance_and_recommendations():
    """Verifies opt-out exclusion and automated optimization recommendations."""
    engine = CrossOrgBenchmarkingEngine()

    bm = engine.register_benchmark(
        domain=BenchmarkDomain.HIRING,
        metric_name="screening_latency",
        min_sample_size=5,
    )

    for i in range(6):
        org = f"ORG-{i}"
        engine.set_participation(org, ParticipationState.PARTICIPATING)
        engine.submit_metric(org, "screening_latency", float(i + 1))

    engine.compute_benchmark(bm.benchmark_id)

    # 1. Opt out Org-0 -> Query returns OPTED_OUT
    engine.set_participation("ORG-0", ParticipationState.OPTED_OUT)
    comp_opted_out = engine.get_benchmark_comparison("ORG-0", "screening_latency")
    assert comp_opted_out.status == "OPTED_OUT"

    # 2. Recommendations for slow tenant (ORG-5 with latency 6.0 > median 3.5)
    recs = engine.generate_optimization_recommendations("ORG-5")
    assert len(recs) == 1
    assert recs[0].metric_name == "screening_latency"
    assert recs[0].observed_gap > 0
    assert "screening_latency" in recs[0].recommendation_text
