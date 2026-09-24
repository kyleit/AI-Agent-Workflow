# Antigravity workflow: AIWF multi-agent loop

Antigravity (`agy`) reads repo `AGENTS.md` and `.agents/` rules. This workflow drives the
multi-agent loop. Thin adapter — maps "run one engine command" only; rules live in the
engine and `skills/multi-agent-loop/PROTOCOL.md`.

> **Degrade path.** If neither `aiwf` nor a Python interpreter is present, follow
> `skills/multi-agent-loop/PROTOCOL.md` by hand — identical results.

## Drive loop — agent-driven (default), one step per turn
You are the **worker AND the driver**: do each phase yourself in this session, then tick to
get the next step (no subprocess spawn).

```bash
aiwf malo tick --workflow <id> --phase <phase-just-done> --verdict PASS|BLOCK|FAIL|ERROR --phases <p1,p2,...>
# fallback launcher: skills/multi-agent-loop/scripts/malo.sh tick ...
```
Obey `next_action`: `EXECUTE_PHASE` (do `resulting_phase`, tick again) · `RUN_CODE_BLOCK_GATE`
(blueprint/impl gate needs real full-file blocks first — materialize + run the strict code-block
gate, then tick with `--gate-evidence <code-block-gate.json>`; never approve a code-less blueprint)
· `AUTO_APPROVE` (run `approval_command` yourself, then tick with `--verdict PASS`) ·
`AWAIT_APPROVAL` (STOP, surface the human gate) · `COMPLETED`/`HALTED`/`HALT_ESCALATE` (report,
present `escalation_options`). `git`/`release`/`deploy` never auto-approve — you stop and ask.

## Autonomous alternative (CI / unattended)
```bash
aiwf malo run --workflow <id> --phases <p1,p2,...>
```
Spawns agents headless per phase and drives to HALT.
