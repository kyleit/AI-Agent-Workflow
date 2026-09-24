# Antigravity workflow: AIWF loop-controller cycle

Antigravity (`agy`) reads repo `AGENTS.md` and `.agents/` rules. This workflow
gives it one-touch execution of a single loop-controller cycle. This is a **thin
adapter** — it maps "run one engine step / read-write state" only and carries NO
business logic; all rules live in the engine and `skills/loop-controller/PROTOCOL.md`.

> **Degrade path.** Antigravity headless is the hardest surface to verify
> automatically, so this workflow always keeps the PROTOCOL.md hand-execution
> path available: if neither `aiwf` nor a Python interpreter is present, follow
> `skills/loop-controller/PROTOCOL.md` §3 and write the files in §5 directly.

## Steps

1. **DECIDE** — one deterministic engine step:

   ```bash
   aiwf loop decide --workflow <id> --phase <phase> --verdict <PASS|BLOCK|FAIL|ERROR> [flags] > .agents/tmp/loop-decide.json
   # fallback launcher: skills/loop-controller/scripts/loop_engine.sh decide ...
   ```

2. **PERSIST** — write state + append the append-only ledger:

   ```bash
   aiwf loop persist --input .agents/tmp/loop-decide.json
   ```

3. Dispatch per the returned `transition`
   (`ADVANCE` → next phase, `REPEAT` → same phase, `BACKTRACK` → named upstream
   phase, `HALT` → stop). On `HALT` with `escalate=true`, present the recorded
   `escalation_options` to the user and stop.
