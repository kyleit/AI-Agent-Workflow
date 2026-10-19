<!-- AIWF:RULES:BEGIN -->
# AI Engineering Workflow Agents

Follow `AI_RULES.md`, the shared policy authority. Its current execution policy
takes precedence over historical gate requirements in older skills or artifacts.

## Global resources

Use the globally installed AIWF skills, runtime, templates and policies directly.
Do not copy or recreate `.agents/skills` in a project when global assets exist.
Project `.agents/` holds project state, config, memory and owned extensions.
Preserve existing custom skills and unrelated work.

## Execution

Use the matching AIWF skill to organize the owner's requested work. AIWF
blocking gates are disabled by default. Do not stop for Blueprint approval,
implementation-entry receipts, source capabilities, readiness scores,
documentation-sync gates or mandatory spikes. `aiwf gate status` reports
disabled checks as SKIPPED. Never invent an approval or claim a skipped test ran.
Historical enforcement is opt-in only through `AIWF_GATE_MODE=enforce`.

Every new Blueprint uses `blueprint_depth: CONTRACT` at every level: master,
family, small feature, phase, standard feature, quick feature and fix. Spikes
are optional investigations. Complete runnable code belongs in implementation.
Preserve frozen historical artifacts, typed contracts and acceptance criteria.

Continue requested work autonomously. Report real compilation, lint, test and
execution failures accurately. Preserve project identity, scoped state and
other sessions' changes. Disabling AIWF gates does not itself request a commit,
push, release or deployment.
<!-- AIWF:RULES:END -->

<!-- AIWF:DEVTEAM:BEGIN (hand-maintained) -->
## DevTeam multi-session seats

When taking a seat, use `/seat <slug>`, the `seat` skill, or
`docs/features/agent-orchestration/PROTOCOL.md`.
Engine: `python -m devteam init|seat|mailbox|board`.
Data lives in `.agents/devteam/` and `.agents/session-mail/`.
Never edit another seat's write-set.
<!-- AIWF:DEVTEAM:END -->

<!-- AIWF:LOOP-CONTROLLER:BEGIN (hand-maintained) -->
## Self-correcting loop controller

Use `aiwf loop load|decide|persist` for LOAD -> EXECUTE -> EVALUATE -> DECIDE ->
PERSIST. Keep user-halt, execution-error and bounded-loop termination behavior.
Approval checkpoints do not stop the default gate-free workflow. Spikes are
optional. State lives in `.agents/state/loop/<workflow-id>.json` and its ledger.
<!-- AIWF:LOOP-CONTROLLER:END -->

<!-- AIWF:MULTI-AGENT-LOOP:BEGIN (hand-maintained) -->
## Multi-agent loop orchestration

When explicitly using multi-agent orchestration, use
`aiwf malo run --workflow <id> --phases plan,blueprint,implement,verify`.
Assignment uses `.agents/config/agent-registry.json`. Approval checkpoints are
skipped by default without creating fake approval records. Run evidence lives
in `.agents/state/loop/<workflow-id>.runs.jsonl`.
<!-- AIWF:MULTI-AGENT-LOOP:END -->
