<!-- File path: docs/adr/ADR-006_asyncio_local_message_bus.md -->

# ADR-006: Local Event-Driven Message Bus using Python Asyncio

## Status
Accepted

## Related Feature
[FEAT-056: Visual Intelligence Runtime — Runtime Core & Event Bus Architecture](file:///e:/AgentsProject/docs/brainstorming/FEAT-056_vir_runtime_core_and_event_bus.md)

## Context
The Visual Intelligence Runtime (VIR) is structured as a multi-agent system where independent agents (Vision, Hearing, Touch, Cognitive, Consensus) cooperate to evaluate frontend quality. These agents need to share raw data, structured evidence, hypotheses, and veto declarations. A monolithic orchestration wrapper creates tight coupling and compromises failure isolation.
However, using a heavy, external distributed message broker (such as Redis, RabbitMQ, or Kafka) would introduce external dependencies, require setup overhead during environment bootstrap, increase local test latency, and conflict with VIR's "script-first" and lightweight local CLI/IDE execution modes. We need a zero-dependency, in-memory, highly performant message bus execution model.

## Decision
We will implement an in-process, asynchronous local event bus using Python's native `asyncio` framework.
- The Event Bus will run on a single shared `asyncio` event loop.
- It will support pub/sub message propagation with topic-based hierarchical routing (e.g. `vir.evidence.vision.*`).
- Agents will register as async coroutines consuming from async queues.
- The Event Bus interface will be abstracted behind an `EventBus` Protocol interface, allowing future alternative transport implementations.

## Alternatives Considered
- **Option A: Monolithic direct invocation (Monolith):** Direct function calls and shared memory references. Rejected because it breaks agent boundary isolation, makes dynamic agent registration difficult, and complicates the implementation of the Self-Doubt and Contradiction Engines.
- **Option B: Redis Pub/Sub:** Rejected because it requires a running Redis server locally, complicating the CLI/CI environment bootstrap sequence.
- **Option C: Node.js style EventEmitter:** Rejected because it does not naturally support async backpressure, thread safety, or prioritization out of the box in Python.

## Trade-offs
### Pros:
- **Zero Dependencies:** Runs natively in standard Python library without external services.
- **High Performance:** In-memory queue transfers take < 5ms per message.
- **Async Safety:** Plays natively with Python's coroutine loop model.
- **Clean Abstraction:** Swapping to Redis or gRPC in the future is easy since the core only interacts with the `EventBus` interface.

### Cons:
- **Single Process Limit:** Limited to a single OS process memory space in the default implementation.
- **Debugging Complexity:** Asynchronous event streams are harder to trace than standard linear stack traces.

## Consequences
- Agents must never call each other directly; they must publish to the bus and subscribe to topics.
- All event payloads must be JSON serializable for diagnostic logging and potential multi-process transport.
- The event bus becomes the primary interface for system-wide telemetry.

## Risks
- **Event loop blocking:** A CPU-bound task in an agent blocks event processing. *Mitigation:* Heavy computation (like image comparison or local VLM parsing) must run in thread pools using `loop.run_in_executor()`.
- **Memory leaks:** Lingering references in queues can bloat RAM. *Mitigation:* Bounded queues with strict retention limits.

## References
- [VIR Index](file:///e:/AgentsProject/docs/brainstorming/VIR_ARCHITECTURE_BIBLE_INDEX.md)
- [FEAT-056](file:///e:/AgentsProject/docs/brainstorming/FEAT-056_vir_runtime_core_and_event_bus.md)
