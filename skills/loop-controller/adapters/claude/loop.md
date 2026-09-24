---
description: Drive one AIWF loop-controller cycle (load → decide → persist)
argument-hint: <workflow-id> <phase> <PASS|BLOCK|FAIL|ERROR>
---

<!-- SOURCE of the Claude /loop adapter. Install to `.claude/commands/loop.md`
     (repo) and/or `~/.claude/commands/loop.md` (user-global). Thin adapter:
     it maps "call skill / run one engine step / read-write state" only and
     carries NO business logic. All rules live in the engine + PROTOCOL.md. -->

You are running ONE loop-controller cycle for workflow **$1** at phase **$2**
with verdict **$3** in this repository. Do this now:

1. **DECIDE** — run one deterministic engine step (canonical form first):

   ```bash
   aiwf loop decide --workflow $1 --phase $2 --verdict $3 [--finding "..."] \
     [--backtrack-target brainstorming] [--next-phase <p>] [--terminal] \
     [--requires-approval] [--approval-present] [--gate <name>] > .agents/tmp/loop-decide.json
   ```

   If the `aiwf` CLI is unavailable, use the launcher
   `skills/loop-controller/scripts/loop_engine.sh decide ...`. If no Python
   interpreter exists, follow `skills/loop-controller/PROTOCOL.md` §3 by hand.

2. **PERSIST** — write state + append the ledger:

   ```bash
   aiwf loop persist --input .agents/tmp/loop-decide.json
   ```

3. From the decision: dispatch per `transition`
   (`ADVANCE`/`REPEAT`/`BACKTRACK`/`HALT`). On `HALT` with `escalate=true`,
   present the recorded `escalation_options` to the user and stop.
