# SECUROXI AI — Distributed Event Bus Production Architecture

**Engine Version**: `0.5.0-event-bus-production`  
**Classification**: **`DISTRIBUTED EVENT INFRASTRUCTURE SPECIFICATION`**  
**Selected Broker**: **`Redis Streams / Redis Bus (redis:7-alpine)`**  
**Date**: `2026-08-14`

---

## 1. Architecture Overview & Technology Selection

SECUROXI AI uses a dual-mode continuous event bus architecture:

```
                      [ContinuousMonitoringEngine]
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
   [InMemoryEventBus]                          [RedisEventBus]
  (Development / Testing)                 (Production Distributed Cluster)
  EVENT_BUS_PROVIDER="memory"             REDIS_URL="redis://localhost:6379/0"
```

### Why Redis Streams / Redis Bus was Selected over RabbitMQ:
1. **Low Latency & High Throughput**: Sub-millisecond publish/consume latencies with >10,000 events/sec capacity.
2. **Minimal Operational Overhead**: Single binary alpine container (`redis:7-alpine`) with zero Erlang runtime dependencies.
3. **Native Consumer Groups & DLQ**: Built-in stream offsets, atomic acknowledgements (`XACK`), retry counters, and dead-letter queue (DLQ) routing.
4. **Seamless Docker Integration**: Plugs directly into `docker-compose.yml` alongside `securoxi-postgres`.

---

## 2. Event Delivery & Reliability Guarantees

* **At-Least-Once Delivery**: Events are explicitly acknowledged (`ACK`) upon successful processing by `ContinuousMonitoringEngine`.
* **Idempotency & Deduplication**: Every event contains a unique `event_id` (`EVT-ENT-xxxx`). Duplicate publish attempts are rejected before queueing.
* **Retry Engine & DLQ**: Failed events increment `retry_count`. If `retry_count >= max_retries` (default: 3), the event is automatically routed to `DEAD_LETTER` queue.
* **Graceful Shutdown**: In-flight processing state is preserved during engine shutdown.

---

## 3. Metrics & Observability

The `ContinuousEventBus` exposes real-time telemetry metrics to the Monitoring API:

* `queue_depth`: Current unconsumed event count.
* `events_published`: Total published security events count.
* `events_processed`: Successfully completed events count.
* `events_failed`: Total processing failure count.
* `retry_count`: Accumulated retry attempts count.
* `dlq_count`: Dead-Letter Queue event count.
* `broker_health`: Status indicator (`HEALTHY` or `DEGRADED`).

---

## 4. Status Decision Choice

# **`PASS`**
