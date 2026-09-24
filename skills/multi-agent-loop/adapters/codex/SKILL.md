---
name: orchestrate
description: Drive the AIWF multi-agent loop yourself, one step per turn (tick), until HALT. You are worker AND driver on one shared workspace across Claude/Codex/Antigravity.
---

# Codex skill: orchestrate (multi-agent-loop adapter)

Install location: `~/.codex/skills/orchestrate/SKILL.md`. Thin adapter: maps "run one
engine command" only; all rules live in the engine and PROTOCOL.md.

## Drive loop — agent-driven (default), one step per turn
You are the **worker AND the driver**: do each phase yourself, then tick to get the next step.

```bash
aiwf malo tick --workflow <id> --phase <phase-just-done> --verdict PASS|BLOCK|FAIL|ERROR --phases <p1,p2,...>
# fallback: skills/multi-agent-loop/scripts/malo.sh tick ...
# last resort: skills/multi-agent-loop/PROTOCOL.md by hand
```
Obey `next_action`: `EXECUTE_PHASE` (do `resulting_phase`, tick again) · `RUN_CODE_BLOCK_GATE`
(blueprint/impl gate needs real full-file blocks first — materialize + run the strict code-block
gate, then tick with `--gate-evidence <code-block-gate.json>`; never approve a code-less blueprint)
· `AUTO_APPROVE` (run `approval_command` yourself, then tick with `--verdict PASS`) ·
`AWAIT_APPROVAL` (STOP, surface the human gate) · `COMPLETED`/`HALTED`/`HALT_ESCALATE` (report,
present `escalation_options`). `git`/`release`/`deploy` never auto-approve. The loop-controller owns transitions.

## Autonomous alternative (CI / unattended)
`aiwf malo run --workflow <id> --phases <p1,p2,...>` spawns agents headless per phase until HALT.
