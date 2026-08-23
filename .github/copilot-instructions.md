# AIWF — MANDATORY workflow for this project (GitHub Copilot)

Any request that modifies SOURCE CODE (add/fix/change a feature) MUST be routed
through the AIWF workflow BEFORE editing code — even if the user did not type
`/aiwf`:

1. `/aiwf <request>` -> initialize-workflow -> workflow-coordinator
2. Spec -> Technical Blueprint under `docs/features/...`
3. Blueprint approval (Blueprint Approval Gate)
4. Only then edit source.

This is enforced deterministically by git hooks (`core.hooksPath=tools/githooks`)
and, in Claude Code, a PreToolUse hook. Commits/pushes of source changes are
BLOCKED unless `.agents/state/source-write-authorization.json` authorizes the
active work item. You cannot bypass this by editing directly.

Never edit the mirrors `.agents/` or `public_export/` — they are generated
(`aiwf update --force` / `make export`). Edit source under repo root
(`skills/`, `tools/`, ...). See `AGENTS.md` for full rules.
