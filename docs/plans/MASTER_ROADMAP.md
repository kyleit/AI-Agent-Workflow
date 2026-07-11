# AIWF OS Executive Runtime Master Roadmap

This document outlines the implementation schedule, dependencies, and sprints for the upgraded AIWF Operating System Platform (Architecture Baseline v1, FEAT-086 to FEAT-108).

## 1. Implementation Phasing Strategy

To minimize risk and accelerate testing, the implementation is decomposed into four sequential phases, establishing a **Minimum Viable Runtime (MVR)** first before layering advanced services, daemons, and plugins.

```
       Phase 1: Core Kernel (MVR)  ──>  Phase 2: Core Services  ──>  Phase 3: Daemons  ──>  Phase 4: Platform/SDKs
```

---

## 2. Sprint Schedule

### Sprint 1: Minimum Viable Runtime (Core Kernel)
- **FEAT-086**: Executive Loop Controller (Target: Loop state machine, context snapshots)
- **FEAT-087**: Task Graph Engine (Target: DAG compiler, priority queue scheduler)
- **FEAT-101**: Virtual Process Manager (Target: Virtual process table, signal handler)
- **FEAT-089**: Event Journal & Observability (Target: Async SQLite journal, JSONL fallback)
- **Milestone 1**: A local, single-user CLI executing non-dependent or simple linear task chains with automatic crash recovery.

### Sprint 2: Hardening & Isolation (Core Services)
- **FEAT-091**: Policy Enforcement Engine (Target: Command static analyzer, path boundary checker)
- **FEAT-092**: Context Isolation Manager (Target: Isolated temp workspace session directories)
- **FEAT-098**: Virtual Filesystem (VFS) Overlay (Target: Memory-mapped VFS overlay)
- **FEAT-102**: Transaction Rollback & State Reversion (Target: 3-tier atomic undo/rollback engine)
- **FEAT-090**: Validation Engine (Target: AC mapper, test run compiler)
- **Milestone 2**: Secure, isolated agent executions where failures automatically rollback changes.

### Sprint 3: Background Daemons (Observability & Speed)
- **FEAT-099**: IPC WebSockets Sidecar Daemon (Target: Persistent `aiwf-sidecar` service, WebSocket protocol)
- **FEAT-097**: AST Incremental Parser Engine (Target: Dynamic code indexing, Tree-sitter query API)
- **FEAT-100**: Interactive Terminal & Process Monitor (Target: Multi-process watcher, shell wrapper)
- **Milestone 3**: Zero-latency CLI launches (<20ms) and real-time state streaming to the visualizer webview.

### Sprint 4: Platforms, Federation & SDKs
- **FEAT-088**: Multi-Agent Registry SDK (Target: Agent specifications, handoff protocol)
- **FEAT-094**: Sandbox Container Execution Provider (Target: Docker environment isolator)
- **FEAT-093**: Compatibility Migration Adapter (Target: Legacy visualizer state translator)
- **FEAT-103**: Token Scheduler & Context Compressor (Target: Context-limit manager)
- **FEAT-104**: Secure Cryptographic Token Authorization (Target: User approval digital signs)
- **FEAT-105**: Remote Execution & Federation Platform (Target: Distributed gRPC node clusters)
- **FEAT-106**: Global Knowledge Graph (Target: Cross-project semantic graph db)
- **FEAT-107**: Plugin & Marketplace Engine (Target: Skill marketplace, signature verification)
- **FEAT-108**: Cost Optimizer & Model Router (Target: Cost tracking, dynamic router)
- **Milestone 4**: Fully-featured Enterprise AI Operating System supporting multi-user clusters and visual debugger.

---

## 3. Critical Path Analysis

The critical path focuses entirely on **Execution Flow Integrity**:
1. **FEAT-086 (Kernel Loop)** must be established first to define the session lifecycle.
2. **FEAT-087 (DAG Compiler)** integrates with the loop to schedule tasks.
3. **FEAT-101 (Process Table)** launches the scheduled tasks.
4. **FEAT-098 (VFS Overlay)** wraps process filesystem writes to prevent workspace pollution.
5. **FEAT-090 (Validation)** checks outcomes before completing the loop.
6. **FEAT-099 (IPC Sidecar)** streams outcomes to the user interface.
