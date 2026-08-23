---
name: devteam
command: devteam
category: orchestration
version: 0.1.0
license: MIT
created_at: 2026-08-13
updated_at: 2026-08-13
feature_id: FEAT-420
feature_family: agent-orchestration
role: multi_session_orchestration
description: Split a repo across a leader + N dev-seats, coordinate via file mailboxes, and hand off between AI sessions with zero knowledge loss. Agent-agnostic (Claude Code, Codex CLI, Antigravity). Deterministic Python engine + MCP + thin adapters, with a PROTOCOL.md fallback.
---

# Skill: devteam (Multi-Session Agent Orchestration)

## Purpose
DevTeam lets several AI sessions work one repository in parallel without context
bloat. A **leader** coordinates; each **dev-seat** owns one non-overlapping slice
of the repo. Sessions coordinate through append-only file mailboxes and hand a
seat off via a living `seat-state` whose key field is **NEXT STEP NOW**, so a
fresh session resumes with zero knowledge loss. It is agent-agnostic: Claude
Code, Codex CLI, and Antigravity all interoperate on the same plain files.

## Architecture (Clean Architecture + DI)
```
domain/         entities, value objects, ports (pure; stdlib only)
application/    use cases (Init, EnterSeat, LeaveSeat, SendMail, PollMail, RenderBoard)
infrastructure/ adapters implementing ports (fs, repositories, scanning, system, install)
interface/      delivery: composition root (DI) + CLI ; plus mcp/ server
```
Dependency rule: `interface → application → domain`; `infrastructure → domain`.
Domain imports nothing outside domain. Concrete adapters are wired only in
`interface/composition.py` (constructor injection). Every file ≤500 lines, split
by feature/topic/category.

## Public APIs (CLI — JSON on stdout)
| Command | Purpose |
|---|---|
| `python -m devteam init [--apply]` | Detect top-level dirs, propose roster; `--apply` scaffolds files. |
| `python -m devteam seat enter <slug> [--session ID]` | Resume-aware seat entry (charter + NEXT STEP NOW + new mail + git status). |
| `python -m devteam seat leave <slug> [--field k=v ...]` | Write the living seat-state (handoff). |
| `python -m devteam mailbox send --to <slug> --type <t> --json '{...}'` | Append a validated envelope (cross-process-locked). |
| `python -m devteam mailbox poll <slug> [--no-advance]` | Read unread mail; advance cursor exactly-once. |
| `python -m devteam board` | Render the seat status board + active locks. |
| `python -m devteam lock acquire <path> --seat <slug> [--ttl s] [--note ..] [--force]` | Take an exclusive cross-seat lock on a shared path (atomic; refuses on conflict). |
| `python -m devteam lock release <path> --seat <slug> [--force]` | Release a held lock. |
| `python -m devteam lock list` / `lock check <path>` | List active locks / check a path's holder. |
| `python -m devteam setup [--write-configs] [--mcp]` | One-shot install: engine + adapters (+ mcp, + MCP configs). |
| `python -m devteam doctor` | Health-check the install + wiring (JSON). |

Error results are `{"ok":false,"error":{code,message,details}}` with exit code 2
(domain error) or 1 (unexpected).

## Runtime Commands (per-repo data)
- Roster/charters/state/board: `.agents/devteam/`
- Mailboxes (git-ignored): `.agents/session-mail/seat-<slug>.inbox.jsonl` + `.cursor`

## MCP tools
`init`, `seat_enter`, `seat_leave`, `mailbox_send`, `mailbox_poll`, `board`,
`lock_acquire`, `lock_release`, `lock_list`, `lock_check` — see `mcp/README.md`.
Requires `pip install mcp` (optional; the engine itself has no third-party dependency).

## Enforced shared-path locks
Seats own non-overlapping write-sets. To edit a **shared** path (outside your
write-set), acquire a lock first (`lock acquire`); a second seat's acquire is
refused atomically (`LOCK_CONFLICT`). `--ttl` auto-expires stale locks so a dead
session never deadlocks a file. Adapters/PROTOCOL instruct sessions to
check-before-write. See `docs/features/agent-orchestration/PROTOCOL.md` §5B.

## Adapters (one-touch entry; degrade to PROTOCOL.md)
- Claude Code: `/seat <slug>` (`.claude/commands/seat.md`; source `adapters/claude/`)
- Codex CLI: `~/.codex/skills/seat/SKILL.md` (source `adapters/codex/`)
- Antigravity: `adapters/antigravity/seat.workflow.md` + `AGENTS.md` pointer
- Fallback: `docs/features/agent-orchestration/PROTOCOL.md`

## Provider Strategy
Filesystem-only; no network, no database. Global engine installed at
`~/.aiwf/devteam/` (co-located with `~/.aiwf/session-bus/`), shared by every
project and tool. Per-repo holds only data.

## Configuration
- `AIWF_HOME` (default `~/.aiwf`) — global engine home base.
- `AIWF_DEVTEAM_ENGINE` — explicit engine path override for the MCP server.

## Installation — one command
```bash
python -m devteam setup --write-configs --mcp
```
Does everything: installs the global engine + MCP server to `~/.aiwf/devteam/`,
copies the three tool adapters user-global, `pip install mcp` (`--mcp`), and
registers the MCP server in Claude/Codex/Antigravity configs (`--write-configs`).

Registering configs is **hard-gated** (§15): it happens ONLY with the explicit
`--write-configs` flag (the owner's approval), non-destructive merge + `.bak`
backup. Without the flag, setup installs engine+adapters and dry-run-plans the
configs. Verify anytime:
```bash
python -m devteam doctor
```
Doctor checks engine, MCP server, `mcp` package, the three adapters, the three
configs, and per-repo init — returns JSON with an overall `ok` + `failed` list.

## Backward Compatibility
Additive skill; touches no existing skill. Introduces `.agents/devteam/` and
`.agents/session-mail/`; appends a marker block to `AGENTS.md` and a `.gitignore`
rule. Does not alter the machine-global `session-bus`.

## Usage Examples
```bash
python -m devteam init --apply
python -m devteam mailbox send --to ipc --type task --json '{"title":"wire mailbox","task_id":"T-001","state":"queued"}'
python -m devteam mailbox poll ipc
python -m devteam seat leave ipc --field next_step_now="add cursor test"
python -m devteam seat enter ipc            # prints NEXT STEP NOW, resumes
python -m devteam board
```

## Extension Points
- New message `type`/`state`: extend `domain/mailbox/message_type.py`.
- New seat metadata: extend `domain/seats/seat.py` + `seatsjson` mapping.
- New delivery surface: add under `interface/` consuming the same composition root.

## Limitations
- Single-writer per seat write-set (no automatic merge of overlapping areas).
- MCP tools require the optional `mcp` package.
- Antigravity headless verification is a documented manual runbook (R3).

## Tests
`python -m pytest skills/devteam/tests -q` — domain/application/infrastructure/
interface layers incl. a real-concurrency append test (AC3) and exactly-once poll.
