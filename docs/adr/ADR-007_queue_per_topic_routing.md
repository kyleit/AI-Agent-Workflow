<!-- File path: docs/adr/ADR-007_queue_per_topic_routing.md -->

# ADR-007: Event Routing using Queue-Per-Topic Pattern

## Status
Accepted

## Related Feature
[FEAT-056: Visual Intelligence Runtime — Runtime Core & Event Bus Architecture](file:///e:/AgentsProject/docs/brainstorming/FEAT-056_vir_runtime_core_and_event_bus.md)

## Context
In the VIR event-driven architecture, agents subscribe to specific topic namespaces (e.g. `vir.evidence.hearing.*`). Some agents (like the VLM Vision agent) process messages very slowly, whereas other agents (like the DOM Inspector) publish logs and telemetry extremely quickly.
If we use a single shared queue for all topics, a slow consumer will cause events to back up, creating latency spikes across all agents or memory overflow. We need an event routing mechanism that guarantees isolation, handles backpressure, and supports message prioritization.

## Decision
We will implement the **Queue-Per-Topic** routing pattern:
- The `EventBus` will maintain a registry of topics, where each topic maps to a dedicated `asyncio.Queue` per subscriber.
- Publishing to a topic copies the event payload to the queue of each active subscriber for that specific topic.
- Bounded queue limits are enforced per subscriber queue (default max size: 1000 events).
- If a queue fills up, a backpressure signal is triggered to throttle the publisher, or the event is redirected to a dead-letter queue (DLQ) if it is low priority.

## Alternatives Considered
- **Option A: Single Shared Queue with Consumer-Side Filtering:** All events go into one queue; consumers pop and discard unrelated messages. Rejected because it wastes CPU processing unrelated envelopes and lacks backpressure isolation for slow agents.
- **Option B: Event Emitter Callback Pattern:** Simple list of listener callbacks executed sequentially. Rejected because it runs synchronously on the publisher's task, meaning a slow subscriber blocks the publisher directly.

## Trade-offs
### Pros:
- **Consumer Isolation:** A stuck or slow agent (VLM) only blocks its own topic queue; other agents (DOM/Console) continue running at maximum speed.
- **Granular Backpressure:** We can enforce queue bounds and backpressure parameters individually per topic.
- **Simple Priority Routing:** High-priority queues can be evaluated first during loop checks.

### Cons:
- **Memory Footprint:** Memory scales linearly with the number of topic subscribers due to duplicate event reference buffers in memory.
- **Latency overhead:** Event routing multiplexing adds minor CPU overhead (< 1ms).

## Consequences
- Subscriber agents must handle backpressure events (e.g., slow down publishing or log warnings).
- Naming conventions for topics must be strict and hierarchical to prevent queue routing map conflicts.

## Risks
- **Memory bloat on long runs:** Bounded queues must be strictly enforced.
- **Queue starvation:** If high-priority topics flood the system, standard evidence processing could starve. *Mitigation:* Bounded limits on priority queues.

## References
- [VIR Index](file:///e:/AgentsProject/docs/brainstorming/VIR_ARCHITECTURE_BIBLE_INDEX.md)
- [FEAT-056](file:///e:/AgentsProject/docs/brainstorming/FEAT-056_vir_runtime_core_and_event_bus.md)
