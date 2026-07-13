<!-- File path: docs/adr/ADR-005_runtime_event_bus_and_streaming_protocol.md -->

# ADR-005: Runtime Event Bus & Streaming Protocol for Provider-Centric Architecture

## Status
Accepted

## Related Feature
FEAT-048: Provider-Centric Runtime & Usage Engine

## Context

The FEAT-048 blueprint introduces a **Runtime Event Bus** (FR-08) to capture and replay workflow events across the AI Engineering Workflow. As part of this redesign, the system must decide:

1. **Event storage mechanism**: Where and how `RuntimeEvents` are persisted for replay
2. **Streaming transport protocol**: How events flow from the Python backend to the VS Code Extension webview in real-time (required for FEAT-049)
3. **Event schema versioning strategy**: How to evolve the event schema without breaking existing consumers

### Drivers of This Decision

- **Current architecture**: Extension communicates with Python via `child_process.exec()` (spawn CLI). This is a pull-based, request-response pattern with ~100–200ms latency per call. It is not suitable for real-time event streaming.
- **FEAT-048 scope boundary**: WebSocket daemon is **design-only** in FEAT-048. However, the decision on protocol must be made now to avoid locking into a non-extensible design.
- **FEAT-049 scope**: Will implement the actual streaming daemon. The protocol chosen here constrains FEAT-049 architecture.
- **Multi-IDE compatibility**: Future connectors (Claude Code, Cursor) operate in their own processes. The streaming design must be IDE-agnostic enough to receive events from external processes.
- **VS Code Extension constraints**: The Extension host cannot expose raw OS sockets easily. VS Code provides built-in `vscode.postMessage` (webview IPC) and `vscode.ExtensionContext.secrets`. However, these are internal to the Extension process — they cannot receive events from external Python processes directly.
- **Developer experience**: Framework maintainers adding new providers must not be required to understand the streaming protocol in depth.

### Options Evaluated

Three options were evaluated before this decision:

1. **Option A: VS Code IPC only** (`vscode.postMessage` + `child_process.exec` polling)
2. **Option B: RFC 6455 WebSocket daemon** (standalone Python `asyncio` WebSocket server)
3. **Option C: Hybrid — SQLite Event Journal + WebSocket opt-in** (selected)

---

## Decision

**Selected: Option C — Hybrid SQLite Event Journal + WebSocket Opt-In**

### Design

#### Phase 1 (FEAT-048): SQLite Event Journal

- All `RuntimeEvents` are **written to the `runtime_events` SQLite table** by `event_bus.py`.
- The Extension **polls** the `runtime_events` table via `provider_engine.py diagnose` on a 5-second interval (using `child_process.exec` — existing spawn pattern).
- New events since last poll are returned in the `DiagnosticsReport` JSON.
- No WebSocket daemon is started. Zero new processes.

#### Phase 2 (FEAT-049): WebSocket Opt-In

- `provider_engine.py` gains a `--daemon` flag that starts a lightweight `asyncio` WebSocket server on `localhost:PORT` (user-configurable).
- The Extension detects whether the daemon is running via a `health_check.txt` sentinel file in `project_runtime.db` directory.
- If daemon detected: Extension upgrades to WebSocket push (sub-100ms latency).
- If daemon not running: Extension falls back to polling (unchanged from Phase 1).
- **Protocol**: RFC 6455 WebSocket (standard, IDE-agnostic, testable with `websocat` and standard browser tools).

#### Event Schema Versioning

- Each `RuntimeEvent` carries a `schema_version` field (semver string, e.g., `"1.0"`).
- Consumers check `schema_version` and gracefully ignore unknown fields.
- Breaking changes (field removal, type change) require `schema_version` major bump.
- The `event_data_json` TEXT column in SQLite is schema-less by design — consumers parse it with `schema_version`-aware deserializers.

---

## Alternatives Considered

### Option A: VS Code IPC Only (vscode.postMessage + polling)

**Description**: Keep the existing `child_process.exec()` pattern permanently. The Extension polls `workflow_runtime.py` CLI every 5 seconds for new events. All event data flows through CLI JSON output. No daemon or WebSocket.

**Why rejected**:
- **Latency ceiling**: Minimum ~200ms per poll cycle due to Python process spawn overhead. Unacceptable for real-time skill progress visualization.
- **No push capability**: Cannot support future streaming requirements (FEAT-049 cannot be built on this).
- **Scalability limit**: Each poll spawns a new Python process — at high event rates (build, test, shell events), this creates process churn.
- **Dead-end architecture**: Adding cross-IDE event collection would require even more spawn calls.

**What it gets right**: Zero new infrastructure; works on all OS with no port conflicts; simplest implementation.

---

### Option B: RFC 6455 WebSocket Daemon (mandatory)

**Description**: A mandatory `asyncio` Python WebSocket server runs as a long-lived daemon process. The Extension connects at startup. All events are pushed over the WebSocket. No SQLite polling.

**Why rejected**:
- **Port conflict risk**: A fixed or even configurable port can conflict with other local services. This creates a fragile dependency on OS port availability.
- **Daemon lifecycle complexity**: Extension must manage the daemon's start/stop lifecycle. If the daemon crashes, the Extension must detect this and restart it. This is significant engineering complexity.
- **Distribution friction**: Users must explicitly allow the daemon process (Windows Firewall, macOS socket permissions). This creates a poor first-run experience.
- **Mandatory dependency**: If the daemon fails to start (e.g., port blocked, Python asyncio not available), the entire Extension fails to show any data — a hard regression from current behavior.
- **Out of scope for FEAT-048**: Blueprint explicitly states "no daemon by default" (TC-02).

**What it gets right**: True real-time push, sub-10ms event latency, clean architecture, no polling overhead.

---

### Option C: Hybrid SQLite Event Journal + WebSocket Opt-In (Selected)

**Description**: Phase 1 uses SQLite as a durable event journal. Phase 2 adds an opt-in WebSocket daemon that the Extension automatically detects and upgrades to if available.

**Why selected**: See Trade-offs section below.

---

## Trade-offs

| Criterion | Option A (IPC Only) | Option B (WS Mandatory) | Option C (Hybrid — Selected) |
| :--- | :---: | :---: | :---: |
| Implementation complexity | Very Low | High | Medium |
| Real-time event latency | ~200ms (spawn) | <10ms | Phase 1: ~5s poll / Phase 2: <10ms |
| Port conflict risk | None | High | None (Phase 1) / Low (Phase 2, opt-in) |
| Daemon lifecycle risk | None | High | None (Phase 1) / Contained (Phase 2) |
| Regression risk | None | Very High | None |
| Distribution friction | None | High | None |
| Future extensibility | None | Very High | High |
| Cross-IDE compatibility | Low | High | High (RFC 6455) |
| TC-02 compliance (no daemon) | Yes | No | Phase 1: Yes / Phase 2: opt-in |
| FEAT-049 enablement | Blocks | Enables | Enables |
| Phase 1 development cost | Low | High | Low |
| Phase 2 development cost | N/A | Already done | Medium |

**Key reasoning**:
1. **Option C decouples phases**: Phase 1 (FEAT-048) ships without any daemon, maintains zero regression, and establishes the event journal pattern. Phase 2 (FEAT-049) adds the WebSocket layer as a transparent upgrade.
2. **SQLite event journal is durable**: Events persist across Extension restarts, IDE crashes, and daemon failures. This is a significant reliability advantage over pure in-memory WebSocket streaming.
3. **Opt-in daemon removes mandatory infrastructure risk**: Users who need real-time streaming start the daemon. Users who don't need it get polling with zero overhead.
4. **RFC 6455 is IDE-agnostic**: Future Claude Code or Cursor integrations can send events to the WebSocket server without VS Code involvement.
5. **Graceful degradation**: Extension always works — WebSocket is an upgrade, not a requirement.

---

## Consequences

### On FEAT-048 Implementation
- `event_bus.py` implements SQLite write-only in Phase 1. `subscribe()` handlers are in-process only (no WebSocket emit).
- `provider_engine.py` does NOT gain a `--daemon` flag in FEAT-048. This is deferred to FEAT-049.
- `DiagnosticsReport` includes a `has_new_events: bool` field so the Extension can poll efficiently (skip heavy refresh if no new events).
- Extension polls `provider_engine.py diagnose` every 5 seconds via existing `child_process.exec` pattern.

### On FEAT-049 Design
- FEAT-049 must implement: `provider_engine.py --daemon --port PORT`, a sentinel file writer, and a WebSocket event emitter inside `event_bus.emit()`.
- Extension must implement: sentinel file watcher (`vscode.createFileSystemWatcher`), WebSocket client upgrade logic (`ws` npm package or native `WebSocket` if Node.js >= 21), and graceful fallback to polling.
- The WebSocket message schema is defined in this ADR and must be followed:
  ```json
  {
    "schema_version": "1.0",
    "event_id": "uuid-v4",
    "timestamp": "ISO8601",
    "conversation_id": "string",
    "provider": "string",
    "event_type": "skill_start | skill_complete | skill_fail | checkpoint_advance | tool_call | build | test | shell",
    "event_data": {}
  }
  ```

### On Extension Architecture
- `updateDiagnosticsData()` is the unified entry point for both polling (Phase 1) and WebSocket push (Phase 2). The polling timer is **cancelled** when WebSocket connection is established; **restarted** if WebSocket disconnects.
- WebSocket client reconnects with exponential backoff (1s, 2s, 4s, max 30s).

### On Future Provider Connectors
- New providers wishing to emit runtime events call `EventBus.emit()` from Python. The event is written to SQLite and optionally pushed via WebSocket — the connector author does not need to know the transport layer.
- This satisfies NFR-04 (new connector = one Python class only).

### On Memory & Knowledge
- `architecture` memory must be updated to document the Event Bus pattern and two-phase streaming design.
- `patterns` memory must record: **SQLite Event Journal Pattern** — use SQLite as durable event store before investing in streaming infrastructure.

---

## Risks

| Risk | Severity | Probability | Mitigation |
| :--- | :---: | :---: | :--- |
| Poll interval (5s) too coarse for some event types | Medium | Medium | Phase 2 WebSocket solves this. Phase 1 acceptable for non-real-time use cases (checkpoint, skill, diagnostics). |
| WebSocket port conflict in Phase 2 (FEAT-049) | Medium | Low | User-configurable port in settings.json; default 0 (OS-assigned ephemeral port); sentinel file records actual port. |
| SQLite `runtime_events` table grows unbounded | Low | Medium | Pruning strategy: delete events older than 30 days on `event_bus.emit()` init; configurable retention period. |
| Schema version drift between Extension (TS) and daemon (Python) | Medium | Low | Both read `schema_version` from event JSON; Extension ignores unknown fields; daemon bumps major version for breaking changes. |
| FEAT-049 not implemented — Extension stays on polling indefinitely | Low | Low | Polling is fully functional for all current requirements. WebSocket is additive only. |

---

## References

- **Brainstorming**: [FEAT-048 Brainstorming Doc](../brainstorming/FEAT-048_provider_centric_runtime_and_usage_engine.md) — Sections 17 (Risk Matrix), 20 (ADR Detection), 35 (Final Planning Prompt)
- **Blueprint**: [FEAT-048 Technical Blueprint](../designs/FEAT-048_provider_centric_runtime_and_usage_engine_blueprint.md) — Section 9 (Skill Integration), Section 11 (Sequence Flows: DiagnosticsPanel Refresh)
- **Implementation Plan**: [FEAT-048 Plan](../plans/FEAT-048_provider_centric_runtime_and_usage_engine_plan.md) — Task 4.1 (Runtime Event Bus)
- **Related ADRs**: ADR-004 (Pure Split State Management) — establishes the SQLite dual-DB pattern this ADR extends
- **External References**:
  - RFC 6455 — The WebSocket Protocol: https://tools.ietf.org/html/rfc6455
  - Python `asyncio` WebSocket server: https://websockets.readthedocs.io/
  - VS Code Extension API — `createFileSystemWatcher`: https://code.visualstudio.com/api/references/vscode-api#FileSystemWatcher
