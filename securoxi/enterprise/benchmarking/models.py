"""
SECUROXI AI Intelligence 2.0 — Cross-Organization Benchmarking Models (Phase 9 Stage 58)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time
import uuid
from securoxi.enterprise.benchmarking.types import (
    ParticipationState,
    BenchmarkDomain,
    ConfidenceLevel,
    CohortDimension,
)


@dataclass
class BenchmarkDefinition:
    """Canonical benchmark definition."""
    benchmark_id: str = field(default_factory=lambda: f"BM-{uuid.uuid4().hex[:8].upper()}")
    domain: BenchmarkDomain = BenchmarkDomain.HIRING
    metric_name: str = "screening_p95_latency_seconds"
    cohort_dimension: CohortDimension = CohortDimension.WORKFLOW_VOLUME
    min_sample_size: int = 5  # k-anonymity minimum threshold
    time_window_days: int = 30
    created_at: float = field(default_factory=time.time)


@dataclass
class BenchmarkDataset:
    """Aggregated, anonymized benchmark distribution."""
    dataset_id: str = field(default_factory=lambda: f"DS-{uuid.uuid4().hex[:8].upper()}")
    benchmark_id: str = "BM-DEFAULT"
    sample_count: int = 0
    median_value: float = 0.0
    p25_value: float = 0.0
    p75_value: float = 0.0
    p95_value: float = 0.0
    is_suppressed: bool = False  # Suppressed if sample_count < min_sample_size
    generated_at: float = field(default_factory=time.time)


@dataclass
class BenchmarkResult:
    """Tenant comparison result against anonymized cohort benchmarks."""
    result_id: str = field(default_factory=lambda: f"BMR-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    benchmark_id: str = "BM-DEFAULT"
    metric_name: str = "screening_p95_latency_seconds"
    organization_value: float = 0.0
    cohort_median: float = 0.0
    cohort_p75: float = 0.0
    percentile_bucket: str = "TOP_QUARTILE"  # e.g., TOP_QUARTILE, ABOVE_MEDIAN, BELOW_MEDIAN
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    status: str = "SUCCESS"  # SUCCESS, BENCHMARK_UNAVAILABLE, OPTED_OUT
    generated_at: float = field(default_factory=time.time)


@dataclass
class OptimizationRecommendation:
    """Actionable optimization suggestion derived from verified performance gaps."""
    recommendation_id: str = field(default_factory=lambda: f"OPT-{uuid.uuid4().hex[:8].upper()}")
    organization_id: str = "ORG-DEFAULT"
    metric_name: str = "screening_p95_latency_seconds"
    observed_gap: float = 0.0
    recommendation_text: str = "Enable index pre-warming to reduce screening latency"
    expected_impact: str = "Estimated 25% reduction in P95 latency"
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    created_at: float = field(default_factory=time.time)
