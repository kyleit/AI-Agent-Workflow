---
name: seat
description: Take a DevTeam seat in this repo — resume-aware seat entry, mailbox, handoff. Use when the user says "take seat X", "seat <slug>", "join the dev team", or wants multi-session repo coordination.
---

# Codex skill: seat (DevTeam adapter)

Install location: `~/.codex/skills/seat/SKILL.md`. Codex also reads the repo
`AGENTS.md`, which points at `docs/features/agent-orchestration/PROTOCOL.md`, so
even without this skill the protocol is reachable.

## When invoked with a seat slug

1. Enter the seat via the `devteam` MCP tool `seat_enter` if configured in
   `~/.codex/config.toml` under `[mcp_servers.devteam]`. Otherwise run:

   ```bash
   python -m devteam seat enter <slug>
   ```

   If the engine is unavailable, follow `PROTOCOL.md` §3 by hand.

2. From the JSON result: show the charter, show **NEXT STEP NOW**
   (`next_step_now`) verbatim and resume there, list new mail, note git status.

3. Load the charter's skills. Work strictly inside the seat's write-set.

## Coordination

- Send: `python -m devteam mailbox send --to <slug> --type task --json '{"title":"..."}'`
- Poll: `python -m devteam mailbox poll <slug>`
- Handoff (every checkpoint): `python -m devteam seat leave <slug> --field next_step_now="..."`

To edit a SHARED path (outside your write-set), first
`python -m devteam lock acquire <path> --seat <slug> --ttl 1800`; stop on
`LOCK_CONFLICT` and coordinate via mailbox. Never edit another seat's directories.
All mailbox/state/lock files are plain files, so seats interoperate across Claude
Code, Codex, and Antigravity.
