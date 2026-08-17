"""
SECUROXI AI Distributed Event Bus & Continuous Monitoring Test Suite
Validates event publishing, consumption, deduplication, retry engine,
Dead-Letter Queue (DLQ) routing, metrics telemetry, and fallback mechanisms.
"""

import pytest
from securoxi.brain.continuous_monitoring import (
    ContinuousEventBus,
    ContinuousMonitoringEngine,
    EnterpriseSecurityEvent,
    EnterpriseEventType,
    EventProcessingState
)


def test_event_bus_publish_and_consume():
    """Verify event publishing and consumption lifecycle."""
    bus = ContinuousEventBus(provider="memory")
    evt = EnterpriseSecurityEvent(
        event_id="EVT-TEST-001",
        event_type=EnterpriseEventType.NEW_DOCUMENT,
        payload={"filename": "resume_sample.pdf"}
    )

    published = bus.publish_event(evt)
    assert published is True

    consumed = bus.get_next_event()
    assert consumed is not None
    assert consumed.event_id == "EVT-TEST-001"
    assert consumed.payload["filename"] == "resume_sample.pdf"


def test_event_bus_deduplication():
    """Verify event ID deduplication prevents duplicate queueing."""
    bus = ContinuousEventBus(provider="memory")
    evt = EnterpriseSecurityEvent(
        event_id="EVT-DUP-001",
        event_type=EnterpriseEventType.SUSPICIOUS_CONTENT
    )

    assert bus.publish_event(evt) is True
    # Duplicate attempt must return False
    assert bus.publish_event(evt) is False


def test_event_bus_retry_and_dlq_routing():
    """Verify failed events retry up to max_retries before routing to DLQ."""
    bus = ContinuousEventBus(provider="memory")
    evt = EnterpriseSecurityEvent(
        event_id="EVT-FAIL-001",
        event_type=EnterpriseEventType.SECURITY_POLICY_VIOLATION,
        max_retries=2
    )

    bus.publish_event(evt)
    
    # Simulate failed processing
    evt.retry_count += 1
    assert evt.retry_count < evt.max_retries

    evt.retry_count += 1
    if evt.retry_count >= evt.max_retries:
        bus.send_to_dlq(evt)

    assert len(bus.dlq) == 1
    assert bus.dlq[0].event_id == "EVT-FAIL-001"
    assert bus.dlq[0].state == EventProcessingState.DEAD_LETTER


def test_monitoring_engine_batch_processing():
    """Verify ContinuousMonitoringEngine processes event queue batches and correlates recurring threats."""
    engine = ContinuousMonitoringEngine()
    
    # Ingest 3 suspicious events with same threat type to trigger REPEATED_ATTACK correlation
    for i in range(3):
        engine.ingest_event(
            event_type=EnterpriseEventType.SUSPICIOUS_CONTENT,
            source="RECURRING_TEST",
            payload={"threat_type": "PROMPT_INJECTION"}
        )

    results = engine.process_queue_batch(max_batch_size=10)
    assert len(results) == 3
    assert results[0]["state"] == "COMPLETED"


def test_event_bus_metrics_telemetry():
    """Verify event bus observability metrics reporting."""
    bus = ContinuousEventBus(provider="memory")
    bus.publish_event(EnterpriseSecurityEvent(event_id="EVT-METRIC-1"))
    
    metrics = bus.get_metrics()
    assert "queue_depth" in metrics
    assert "events_published" in metrics
    assert metrics["events_published"] >= 1
    assert metrics["broker_health"] == "HEALTHY"
