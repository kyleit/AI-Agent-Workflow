---
description: Take a DevTeam seat (resume-aware) — load charter, NEXT STEP NOW, new mail
argument-hint: <seat-slug>
---

<!-- SOURCE of the Claude /seat adapter. Install to `.claude/commands/seat.md`
     (repo) and/or `~/.claude/commands/seat.md` (user-global). Kept in sync here
     as the tracked source of truth. -->

You are taking DevTeam seat **$1** in this repository. Do this now:

1. Enter the seat (prefer the `devteam` MCP `seat_enter` tool; else shell out):

   ```bash
   python -m devteam seat enter $1 --session "$CLAUDE_SESSION_ID"
   ```

   If the engine is not on PATH, read
   `docs/features/agent-orchestration/PROTOCOL.md` §3 and enter by hand.

2. From the JSON: print the charter, print **NEXT STEP NOW** verbatim and resume
   there, summarize new_mail, note git_status.

3. Load the charter's skills, then continue.

**Hard rules:** stay inside your write-set; to edit a shared path first
`devteam lock acquire <path> --seat $1 --ttl 1800` (stop on `LOCK_CONFLICT`);
update living state each checkpoint
(`devteam seat leave $1 --field next_step_now="..."`); coordinate via
`devteam mailbox send/poll`.
