---
feature_id: FEAT-089
feature_name: Runtime Infrastructure & Observability
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-089_runtime_infrastructure_observability_plan.md
---

# Master Brainstorming Document – Runtime Infrastructure & Observability (FEAT-089)

## 1. Executive Summary
This document designs the **Runtime Infrastructure & Observability** subsystem. It introduces a structured **Event Journal** (using SQLite and structured JSONL logs) to track every state change, agent dispatch, and tool execution, providing a detailed metrics timeline and real-time integration with the Visualizer dashboard.

## 2. Background
Currently, AIWF logs execution states to basic text logs and stores raw statistics in `workflow_usage.db`. While useful, this is insufficient for tracking complex agent graphs or diagnosing performance bottlenecks. To enable advanced debugging and optimization, we need a queryable Event Journal that tracks execution history, latency, token costs, and tool parameters in real-time.

## 3. Current Architecture Analysis
The current logging relies on text outputs and basic statistics stored in `db.py`.
- Statistics database: `workflow_usage.db`.
- UI updates are sent to `webview.html` via telemetry files.

## 4. Current Limitations
- **No Event Stream**: Cannot replay state changes or inspect historical decision sequences.
- **High Disk I/O**: Frequent updates to SQLite tables can lock execution loops.
- **Unstructured Logs**: Raw console logs are difficult to parse programmatically.

## 5. Objectives
- Establish an **Event Journal** that logs structured execution events.
- Implement **SQLite + JSONL Storage** to balance write speed and query support.
- Develop a **Telemetry API** to stream events to the Visualizer in real-time.

## 6. Functional Requirements
- **FR-01: Event Logging**: Capture events with standard parameters (`timestamp`, `source`, `event_type`, `payload`, `iteration`).
- **FR-02: Query Interface**: Support filtering events by conversation ID, agent ID, and time range.
- **FR-03: Visualizer Stream**: Output event streams in NDJSON format to update the VS Code webview.
- **FR-04: Token & Cost Accounting**: Log detailed token usage and costs per model call.
- **FR-05: Timeline Generation**: Generate a queryable timeline of execution events.

## 7. Non-Functional Requirements
- **NFR-01: Logging Overhead**: Writing an event to the journal must take `< 5ms`.
- **NFR-02: DB Stability**: Database writes must not block the main execution thread.

## 8. Scope
- Event Journal module (`journal.py`).
- SQLite storage schemas and migrations.
- Log rotation and archival policies.
- CLI subcommands for log querying (`history`, `export`, `trace`).

## 9. Out of Scope
- Code performance profiling (e.g. cProfile integrations).
- External cloud log exporting (restricted to local workspace).

## 10. Runtime Responsibilities
The Infrastructure layer logs events, manages the database connections, aggregates telemetry statistics, and maintains the Visualizer IPC connection.

## 11. Components
- `EventJournal`: Captures and formats incoming event logs.
- `SQLiteStorage`: Fast local storage for queryable traces.
- `JSONLWriter`: Append-only raw fallback file writer.
- `TelemetryServer`: Exposes the local socket or file-based updates to the Visualizer.

## 12. Data Model
```sql
CREATE TABLE event_journal (
    event_id TEXT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT,
    event_type TEXT,
    payload TEXT,
    iteration INTEGER
);
```

## 13. Runtime State
```
[Closed] ──(open)──> [Active] ──(log event)──> [Active] ──(close)──> [Closed]
```

## 14. Event Flow
1. Coder agent calls `replace_file_content`.
2. The execution runtime intercepts the tool call.
3. Event journal logs a `tool_call_start` event.
4. Tool finishes execution.
5. Event journal logs a `tool_call_end` event.
6. The event is formatted as NDJSON and appended to `.agents/runtime/event_stream.ndjson`.

## 15. Sequence Flow
- Intercept -> format payload -> write to JSONL -> write asynchronously to SQLite -> notify Visualizer.

## 16. Dependencies
- State synchronization module (from FEAT-051).

## 17. Integration Points
- Database: `.agents/project_runtime.db`
- Webview: `webview.html` via `event_stream.ndjson`

## 18. Interaction with Executive Runtime
- The Executive loop uses the Event Journal to record all state transitions, loop iterations, and error statuses.

## 19. Interaction with other features
- Logs task dispatches from **Task Graph Engine (FEAT-087)**.
- Tracks agent transitions from **Multi-Agent Runtime (FEAT-088)**.

## 20. Security Considerations
- Sanitize payload values to prevent SQL injection in SQLite.
- Scrub sensitive credentials (e.g., API keys, passwords) from the logs.

## 21. Performance Considerations
- Use asynchronous SQLite writes via a background worker thread.
- Limit database files sizes; archive logs older than 30 days.

## 22. Scalability Considerations
- The journal can store over 100,000 events without performance degradation.

## 23. Failure Scenarios
- **SQLite Database Locked**: Fall back to append-only JSONL files; retry DB write later.
- **Disk Full**: Log warning to stderr, disable non-critical telemetry, and continue execution.

## 24. Recovery Strategy
On startup, verify the integrity of the SQLite database. If corrupted, reconstruct it using the append-only JSONL files.

## 25. Migration Strategy
Migrate existing tables in `workflow_usage.db` into the new structured schema during the first initialization run.

## 26. Backward Compatibility
Support the legacy logging format to ensure existing visualizer tabs remain functional.

## 27. Risks
- Database lock contentions. Mitigated by using WAL mode in SQLite.

## 28. Alternative Designs
- **Option A**: Pure JSONL files. (Rejected: querying history is too slow).
- **Option B**: External logging services. (Rejected: violates offline/sandbox policy).

## 29. Trade-offs
- Async SQLite logging adds minor architectural complexity but prevents write lock delays in the main loop.

## 30. Acceptance Criteria
- [ ] AC-01: Successfully write event logs and query them via CLI within 10ms.
- [ ] AC-02: Recover database tables successfully from raw JSONL fallbacks.

## 31. Estimated Complexity
- Medium.

## 32. Blueprint Estimation
- 1 design blueprint (`docs/designs/FEAT-089_runtime_infrastructure_observability.md`).

## 33. Recommended Implementation Order
Implement fourth, following the Multi-Agent Runtime.
