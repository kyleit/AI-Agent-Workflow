---
name: loop
description: Run one AIWF loop-controller cycle (load → decide → persist) to advance/repeat/backtrack/halt a workflow. Use when coordinating a self-correcting AIWF run or when a gate verdict must decide the next phase.
---

# Codex skill: loop (loop-controller adapter)

Install location: `~/.codex/skills/loop/SKILL.md`. Codex also reads the repo
`AGENTS.md`, which points at `skills/loop-controller/PROTOCOL.md`, so even
without this skill the protocol is reachable. This is a **thin adapter**: it maps
"run one engine step / read-write state" only and carries NO business logic.

## When invoked with `<workflow-id> <phase> <verdict>`

1. **DECIDE** — prefer the canonical CLI; fall back to the launcher, then to
   hand-execution:

   ```bash
   aiwf loop decide --workflow <id> --phase <phase> --verdict <PASS|BLOCK|FAIL|ERROR> [flags] > .agents/tmp/loop-decide.json
   # fallback: skills/loop-controller/scripts/loop_engine.sh decide ...
   # last resort: follow skills/loop-controller/PROTOCOL.md §3 by hand
   ```

2. **PERSIST**:

   ```bash
   aiwf loop persist --input .agents/tmp/loop-decide.json
   ```

3. Dispatch per the returned `transition`. On `HALT` with `escalate=true`,
   surface `escalation_options` and stop. `load`/`decide` never write; only
   `persist` mutates state.
