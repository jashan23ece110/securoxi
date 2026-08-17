"""
SECUROXI AI Continuous Monitoring & Distributed Event Pipeline Engine
Implements dual-mode asynchronous event bus (InMemoryEventBus & RedisEventBus),
idempotency deduplication, dead-letter queue (DLQ), recurring threat pattern detection,
and Security Brain integration.
"""

import time
import uuid
import queue
import json
import os
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from securoxi.brain.core import SecurityBrainCore
from securoxi.brain.models import EventSource, SignalSeverity
from securoxi.config import SecuroxiConfig
from securoxi.logger import get_logger

REDIS_URL = os.environ.get("REDIS_URL") or os.environ.get("SECUROXI_REDIS_URL")
EVENT_BUS_PROVIDER = os.environ.get("EVENT_BUS_PROVIDER", "memory").lower()


class EventProcessingState(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


class EnterpriseEventType(str, Enum):
    NEW_DOCUMENT = "NEW_DOCUMENT"
    MODIFIED_DOCUMENT = "MODIFIED_DOCUMENT"
    NEW_ATS_CANDIDATE = "NEW_ATS_CANDIDATE"
    SCREENING_EVENT = "SCREENING_EVENT"
    MODEL_INTERACTION = "MODEL_INTERACTION"
    TOOL_CALL = "TOOL_CALL"
    SUSPICIOUS_CONTENT = "SUSPICIOUS_CONTENT"
    SECURITY_POLICY_VIOLATION = "SECURITY_POLICY_VIOLATION"
    REPEATED_ATTACK = "REPEATED_ATTACK"


@dataclass
class EnterpriseSecurityEvent:
    """Normalized Enterprise Security Event."""
    event_id: str = field(default_factory=lambda: f"EVT-ENT-{uuid.uuid4().hex[:8]}")
    event_type: EnterpriseEventType = EnterpriseEventType.NEW_DOCUMENT
    source: str = "CONTINUOUS_MONITOR"
    file_path: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    state: EventProcessingState = EventProcessingState.QUEUED
    retry_count: int = 0
    max_retries: int = 3
    processing_latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if isinstance(self.event_type, EnterpriseEventType) else str(self.event_type),
            "source": self.source,
            "file_path": self.file_path,
            "payload": self.payload,
            "state": self.state.value if isinstance(self.state, EventProcessingState) else str(self.state),
            "retry_count": self.retry_count,
            "processing_latency_ms": round(self.processing_latency_ms, 2),
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnterpriseSecurityEvent":
        evt_type = data.get("event_type", EnterpriseEventType.NEW_DOCUMENT.value)
        try:
            enum_type = EnterpriseEventType(evt_type)
        except ValueError:
            enum_type = EnterpriseEventType.NEW_DOCUMENT

        evt_state = data.get("state", EventProcessingState.QUEUED.value)
        try:
            enum_state = EventProcessingState(evt_state)
        except ValueError:
            enum_state = EventProcessingState.QUEUED

        return cls(
            event_id=data.get("event_id", f"EVT-ENT-{uuid.uuid4().hex[:8]}"),
            event_type=enum_type,
            source=data.get("source", "CONTINUOUS_MONITOR"),
            file_path=data.get("file_path"),
            payload=data.get("payload", {}),
            state=enum_state,
            retry_count=data.get("retry_count", 0),
            processing_latency_ms=data.get("processing_latency_ms", 0.0),
            timestamp=data.get("timestamp", time.time())
        )


class ContinuousEventBus:
    """Asynchronous Queue & Event Bus Abstraction with DLQ, Deduplication, and Redis/InMemory Provider Selection."""

    def __init__(self, provider: Optional[str] = None, redis_url: Optional[str] = None, config: Optional[Any] = None):
        self.logger = get_logger("securoxi.monitoring.bus")
        self.config = config
        self.provider = (provider or EVENT_BUS_PROVIDER).lower()
        self.redis_url = redis_url or REDIS_URL

        self.event_queue: queue.Queue = queue.Queue()
        self.dlq: List[EnterpriseSecurityEvent] = []
        self.processed_event_ids: set = set()
        self.event_history: Dict[str, EnterpriseSecurityEvent] = {}

        self.metrics = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "retry_count": 0,
            "broker_health": "HEALTHY"
        }

        # Attempt Redis client setup if provider is redis or REDIS_URL is provided
        self.redis_client = None
        if self.provider == "redis" or self.redis_url:
            try:
                import redis
                self.redis_client = redis.Redis.from_url(self.redis_url or "redis://localhost:6379/0", decode_responses=True)
                self.redis_client.ping()
                self.provider = "redis"
                self.logger.info("Connected to Redis Event Bus Broker.")
            except Exception as err:
                self.logger.warning(f"Could not connect to Redis broker ({err}). Falling back to InMemoryEventBus.")
                self.provider = "memory"
                self.redis_client = None

    def publish_event(self, event: EnterpriseSecurityEvent) -> bool:
        """Publishes event to queue/stream. Deduplicates if event_id already exists."""
        if event.event_id in self.processed_event_ids:
            self.logger.info(f"Event '{event.event_id}' already processed. Deduplicating.")
            return False

        self.processed_event_ids.add(event.event_id)
        self.event_history[event.event_id] = event
        self.metrics["events_published"] += 1

        if self.provider == "redis" and self.redis_client:
            try:
                self.redis_client.rpush("securoxi:event_stream", json.dumps(event.to_dict()))
                self.logger.info(f"Published event [{event.event_id}] to Redis Event Stream.")
                return True
            except Exception as err:
                self.logger.error(f"Redis publish failed ({err}). Falling back to memory queue.")
                self.metrics["broker_health"] = "DEGRADED"

        self.event_queue.put(event)
        self.logger.info(f"Published event [{event.event_id}] ({event.event_type.value}) to Event Bus.")
        return True

    def get_next_event(self, timeout_sec: float = 0.1) -> Optional[EnterpriseSecurityEvent]:
        """Fetches next available event from Redis stream or memory queue."""
        if self.provider == "redis" and self.redis_client:
            try:
                raw_event = self.redis_client.lpop("securoxi:event_stream")
                if raw_event:
                    data = json.loads(raw_event)
                    return EnterpriseSecurityEvent.from_dict(data)
            except Exception as err:
                self.logger.error(f"Redis consume error: {err}")
                self.metrics["broker_health"] = "DEGRADED"

        try:
            return self.event_queue.get(timeout=timeout_sec)
        except queue.Empty:
            return None

    def send_to_dlq(self, event: EnterpriseSecurityEvent):
        event.state = EventProcessingState.DEAD_LETTER
        self.dlq.append(event)
        self.metrics["events_failed"] += 1
        self.logger.error(f"Event [{event.event_id}] sent to Dead-Letter Queue (DLQ) after {event.retry_count} retries.")

        if self.provider == "redis" and self.redis_client:
            try:
                self.redis_client.rpush("securoxi:dlq", json.dumps(event.to_dict()))
            except Exception as err:
                self.logger.error(f"Redis DLQ push failed: {err}")

    def get_metrics(self) -> Dict[str, Any]:
        """Returns observability metrics for continuous monitoring dashboard."""
        q_len = self.event_queue.qsize()
        if self.provider == "redis" and self.redis_client:
            try:
                q_len = self.redis_client.llen("securoxi:event_stream")
            except Exception:
                pass

        return {
            "provider": self.provider,
            "queue_depth": q_len,
            "events_published": self.metrics["events_published"],
            "events_processed": self.metrics["events_processed"],
            "events_failed": self.metrics["events_failed"],
            "retry_count": self.metrics["retry_count"],
            "dlq_count": len(self.dlq),
            "broker_health": self.metrics["broker_health"]
        }


class ContinuousMonitoringEngine:
    """
    Continuous Enterprise Security Monitoring Engine.
    Consumes events from ContinuousEventBus, executes Security Brain reasoning,
    detects recurring attack patterns across multiple documents, and emits real-time alerts.
    """

    def __init__(self, config: Optional[SecuroxiConfig] = None):
        self.config = config or SecuroxiConfig()
        self.logger = get_logger("securoxi.monitoring.engine")
        self.event_bus = ContinuousEventBus()
        self.brain = SecurityBrainCore(config=self.config)
        self.threat_pattern_frequency: Dict[str, int] = {}  # Tracks recurring attack patterns
        self.incidents: List[Dict[str, Any]] = []

    def ingest_event(
        self,
        event_type: EnterpriseEventType,
        source: str,
        file_path: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None
    ) -> EnterpriseSecurityEvent:
        payload_data = payload or {}
        evt = EnterpriseSecurityEvent(
            event_id=event_id or f"EVT-ENT-{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            source=source,
            file_path=file_path,
            payload=payload_data
        )
        self.event_bus.publish_event(evt)
        return evt

    def process_queue_batch(self, max_batch_size: int = 10) -> List[Dict[str, Any]]:
        """Processes up to max_batch_size queued events synchronously."""
        results = []
        processed_count = 0

        while processed_count < max_batch_size:
            evt = self.event_bus.get_next_event()
            if not evt:
                break

            start_t = time.perf_counter()
            evt.state = EventProcessingState.PROCESSING

            try:
                # Security Brain event processing
                brain_res = self.brain.process_event(
                    source=EventSource.CONTINUOUS_MONITOR,
                    signal_type=evt.event_type.value if isinstance(evt.event_type, EnterpriseEventType) else str(evt.event_type),
                    severity=SignalSeverity.HIGH if "ATTACK" in str(evt.event_type) else SignalSeverity.INFO,
                    payload=evt.payload,
                    provenance=evt.file_path or evt.source
                )

                # Recurring Threat Correlation Check
                for thr in brain_res.get("threats", []):
                    ttype = thr.get("threat_type", "UNKNOWN")
                    self.threat_pattern_frequency[ttype] = self.threat_pattern_frequency.get(ttype, 0) + 1

                    # Trigger REPEATED_ATTACK incident if pattern repeats >= 3 times!
                    if self.threat_pattern_frequency[ttype] >= 3:
                        self.logger.warning(f"RECURRING ATTACK PATTERN DETECTED: '{ttype}' seen {self.threat_pattern_frequency[ttype]} times!")
                        brain_res["recurring_attack_alert"] = {
                            "threat_type": ttype,
                            "frequency": self.threat_pattern_frequency[ttype],
                            "alert": "REPEATED_ATTACK_PATTERN_CORRELATED"
                        }

                evt.state = EventProcessingState.COMPLETED
                evt.processing_latency_ms = (time.perf_counter() - start_t) * 1000.0
                self.event_bus.metrics["events_processed"] += 1

                results.append({
                    "event_id": evt.event_id,
                    "state": evt.state.value if isinstance(evt.state, EventProcessingState) else str(evt.state),
                    "latency_ms": evt.processing_latency_ms,
                    "brain_result": brain_res
                })
                processed_count += 1

            except Exception as err:
                self.logger.error(f"Error processing event '{evt.event_id}': {err}")
                evt.retry_count += 1
                self.event_bus.metrics["retry_count"] += 1
                if evt.retry_count >= evt.max_retries:
                    self.event_bus.send_to_dlq(evt)
                else:
                    evt.state = EventProcessingState.QUEUED
                    self.event_bus.event_queue.put(evt)

        return results
