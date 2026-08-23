# Antigravity workflow: DevTeam seat

Antigravity (`agy`) reads repo `AGENTS.md` and `.agents/` rules. This workflow
gives it one-touch seat entry; if the `devteam` MCP server is registered in the
Antigravity IDE MCP settings, prefer the `seat_enter` tool.

> **Delivery note (R3).** Antigravity headless (`agy --print`, with
> `--dangerously-skip-permissions` blocked) is the hardest surface to verify
> automatically. This workflow therefore always keeps the PROTOCOL.md degrade
> path available and is validated by the manual runbook in
> `docs/features/agent-orchestration/reports/`.

## Steps

1. Enter the seat:
   - MCP available → call tool `seat_enter` with `{ "slug": "<slug>" }`.
   - Else shell → `python -m devteam seat enter <slug>`.
   - Else → follow `docs/features/agent-orchestration/PROTOCOL.md` §3 by hand.
2. Read the charter and **NEXT STEP NOW**; resume exactly there.
3. Poll mail: `python -m devteam mailbox poll <slug>`.
4. Work only inside the seat's write-set. To edit a shared path, first
   `python -m devteam lock acquire <path> --seat <slug> --ttl 1800` and stop on
   `LOCK_CONFLICT`.
5. At every checkpoint, update the living state:
   `python -m devteam seat leave <slug> --field next_step_now="..."`.

## Manual verification runbook (headless)

```bash
agy --print "Run: python -m devteam seat enter <slug>. Then print NEXT STEP NOW and resume." < /dev/null
```
Confirm the printed `next_step_now` matches `.agents/devteam/state/seat-<slug>.md`.
