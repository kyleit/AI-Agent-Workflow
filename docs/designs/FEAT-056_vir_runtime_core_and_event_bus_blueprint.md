<!-- File path: docs/designs/FEAT-056_vir_runtime_core_and_event_bus_blueprint.md -->

---
feature_id: FEAT-056
feature_name: Visual Intelligence Runtime — Runtime Core & Event Bus
status: reviewed
stage: blueprint
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../plans/FEAT-056_vir_runtime_core_and_event_bus_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Runtime Core & Event Bus

## 0. Baseline Context & References
- **Memory Baseline**: Memory of async IO patterns inside Visualizer and event processing bounds.
- **RAG Query Summaries**: `ADR-006` details localized asyncio queue configurations to protect against circular blocking locks.
- **Inspected Source Files**:
  - [FEAT-056 Plan](file:///e:/AgentsProject/docs/plans/FEAT-056_vir_runtime_core_and_event_bus_plan.md)
  - [ADR-006 asyncio message bus](file:///e:/AgentsProject/docs/adr/ADR-006_asyncio_local_message_bus.md)

---

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `vir_runtime/core/bus.py` | Create | Core AsyncIO event bus publisher and listeners router | None | High. Backbone of inter-agent messaging. |
| `vir_runtime/core/events.py` | Create | Event object dataclass shapes and topic identifiers | None | Medium. Event schema constraints. |
| `vir_runtime/core/loop_protector.py` | Create | Intercept cyclic event patterns and halt propagation | `events.py` | Low. Enhances event safety. |

---

## 2. Target Folder Structure
```text
vir_runtime/
└── core/
    ├── bus.py
    ├── events.py
    └── loop_protector.py
```

---

## 3. Complete Class & Module Design

### 3.1 AsyncEventBus
- **Class / Module Name**: `vir_runtime.core.bus.AsyncEventBus`
  - **Responsibilities**: Route event payloads to subscribed handlers asynchronously without blocking publishing threads.
  - **Constructor Parameters**:
    - `loop_limit: int` - Maximum events processed per investigation session.
  - **Public Methods**:
    - `async def publish(event: Event) -> None` - Put event into queue.
    - `def subscribe(topic: str, handler: Callable[[Event], Coroutine]) -> None` - Registers handler.
    - `async def start() -> None` - Starts the asyncio queue processing worker loop.
    - `async def stop() -> None` - Joins queue and shuts down workers.
  - **Internal Methods**:
    - `async def _worker() -> None` - Processes event queues.
  - **Dependencies**: `asyncio`, `vir_runtime.core.events`, `vir_runtime.core.loop_protector`

### 3.2 LoopProtector
- **Class / Module Name**: `vir_runtime.core.loop_protector.LoopProtector`
  - **Responsibilities**: Keep history of processed event hashes to spot recursive loop patterns.
  - **Constructor Parameters**:
    - `max_history: int` - Maximum signatures cached.
  - **Public Methods**:
    - `def inspect_event(event: Event) -> bool` - Returns True if loop pattern detected.
  - **Internal Methods**:
    - `def _compute_hash(event: Event) -> str` - Computes MD5 signature of event details.

---

## 4. Detailed Interface Contracts

- **API Signature**: `def subscribe(topic: str, handler: Callable[[Event], Coroutine]) -> None`
  - **Parameters**:
    - `topic` (string pattern mapping event topics e.g. `evidence.new`)
    - `handler` (awaitable asynchronous callback receiver function)
  - **Return Types**: None.
  - **Exceptions**:
    - `InvalidTopicError` - Topic name format doesn't match standard regex constraints.

---

## 5. Configuration Schema

- **Target Schema**:
```yaml
vir:
  event_bus:
    queue_max_size: 1000
    worker_count: 2
    loop_detection_limit: 10
```

---

## 6. Database & Storage Design
- The Event Bus runs strictly in RAM (volatile asyncio queues). No database storage is configured.

---

## 7. Cache Architecture
- **Loop Signature Cache**:
  - Memory array: `collections.deque` containing past 100 event hashes.
  - TTL: Invalidated at the start of a new investigation session run.

---

## 8. Error Model

- **Exception Class**: `CyclicEventLoopError`
  - **Trigger Condition**: An agent publishes an event that matches recursive hash sequences.
  - **Recovery Strategy**: Drop the offending event, post warning, shut down bus.
  - **Logging Requirements**: WARNING level log highlighting topic loop traces.

---

## 9. Skill Integration Contracts
- None. (Event Bus stays private within VIR core).

---

## 10. CLI & Runtime Contracts
- None. (Bus does not expose external CLI arguments).

---

## 11. Sequence Flows

- **Event Propagation Flow**:
  1. Observer posts `Event(topic="evidence.new", payload=...)` to `AsyncEventBus`.
  2. `AsyncEventBus` queue pushes event payload.
  3. `LoopProtector` inspects payload signature.
  4. Worker thread picks up event and schedules subscribers asyncio Tasks.

---

## 12. Security & Safety
- **Handler Isolation**: Handler failures are caught using `try-except` inside the worker loop to prevent one faulty agent handler from crashing the main bus thread.

---

## 13. Complete Test Matrix

| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| `FR-06` | Unit Test | `tests/unit/test_bus_pubsub.py` | `bus.py` | `self.assertEqual(received_payload, sent_payload)` |
| `FR-08` | Unit Test | `tests/unit/test_loop_protection.py` | `loop_protector.py` | `self.assertTrue(loop_detected)` |

---

## 14. Requirement Traceability Matrix
- `FR-06` -> Task 1.2 -> Class `AsyncEventBus` -> `bus.py` -> `test_bus_pubsub.py` -> Verified.
- `FR-08` -> Task 1.8 -> Class `LoopProtector` -> `loop_protector.py` -> `test_loop_protection.py` -> Verified.

---

## 15. File-Level Implementation Contracts
- **File**: `vir_runtime/core/bus.py`
  - **Purpose**: Low-latency AsyncIO local message pipeline router.
  - **Owner**: Coder
  - **Inputs / Outputs / Dependencies**: Depends on queue sizes configurations.
