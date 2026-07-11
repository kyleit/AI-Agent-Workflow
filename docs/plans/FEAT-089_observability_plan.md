# Implementation Plan – FEAT-089: Event Journal & Observability

## 1. Goal & Objectives
Implement a queryable **Event Journal** using SQLite and an append-only JSONL log fallback to track all runtime actions, states, and telemetry.

## 2. Sprint & Milestones
- **Sprint**: Sprint 1 (Minimum Viable Runtime)
- **Milestone**: M1 (Core Kernel Execution)
- **Target Date**: Week 1

## 3. Deliverables
- `journal.py`: Handles structured event formats.
- `db.py` updates: Write-Ahead Logging (WAL) setup for SQLite, background async writer thread.
- `.agents/runtime/event_stream.ndjson` format output.

## 4. Dependencies
- None.

## 5. Risks & Mitigations
- **Risk**: SQLite lock contentions during multi-task logging.
- **Mitigation**: Use WAL mode and queue all writes through an in-memory queue processed by a single background thread.

## 6. Definition of Done (DoD)
- Log and retrieve events via CLI under 10ms.
- Recover corrupted database tables from raw JSONL fallbacks.

## 7. Test Strategy
- Concurrency test: trigger 100 concurrent log writes and verify no `database is locked` errors occur.

## 8. Release Gate
- Database migration script runs without errors; WAL mode successfully verified.
