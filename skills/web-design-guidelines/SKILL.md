---
name: web-design-guidelines
command: web-audit
aliases:
  - web-design-review
  - ui-audit
  - ux-audit
  - accessibility-audit
category: quality
tags:
  - web
  - ui
  - ux
  - accessibility
  - audit
  - frontend
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-15
updated_at: 2026-07-15
description: Review UI code for Web Interface Guidelines compliance. Use when asked to review UI, check accessibility, audit design, review UX, or check site against best practices.
runtime_requirements:
  rules: required
  state: required
  approvals: required
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: none
  version: cached
  provider: optional
  usage: cached
---

# Skill: web-design-guidelines

## Purpose
Review web user interfaces (UI) and code for compliance with Web Interface Guidelines. Use when asked to review UI, check accessibility, audit design, review UX, or check a site against best practices.

## Workflow Runtime & Initialization Check
This skill must interface with the workflow runtime engine. Validate the workflow session and checkpoints before starting a verification audit.

## Global Policy References
Adheres strictly to global policies in `AI_RULES.md`:
- **Approval Gate Policy**: All corrective changes based on audit must be approved.
- **Memory First Policy**: Memory-first retrieval for guidelines application.

## Public APIs / Trigger Contract
- **Trigger Phrases**: review UI, check accessibility, audit design, review UX, check site against best practices, Web Interface Guidelines
- **Command**: `web-audit`
- **Aliases**: `web-design-review`, `ui-audit`, `ux-audit`, `accessibility-audit`
- **Input**: Target UI files, directories, or patterns.

## Workflow Integration
- **Owner Agent**: `reviewer`
- **Specialist Agents**: `accessibility-reviewer`, `frontend-developer`, `qa-reviewer`
- **Phase**: `verification`
- **Execution Mode**: `sequential`

## Guidelines Source
Fetches the latest guidelines before each review:
```
https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
```

## Review Procedure
1. Fetch latest guidelines from the source URL above.
2. Read the specified target files or prompt user for files/patterns.
3. Audit the specified files against the fetched guidelines.
4. Highlight gaps in design, accessibility, and UX.

## Output Format
Output findings in the terse `file:line` format according to fetched guidelines. Example:
```
src/components/Button.js:15: Button does not have an explicit aria-label.
```

## Related Skills
- **frontend-design** (`../frontend-design/SKILL.md`): Applied during design phase.
- **frontend-visual-debug** (`../frontend-visual-debug/SKILL.md`): Applied during implementation/debugging.

## Provider Strategy
Operates in a provider-agnostic manner, using default model provider settings.

## Backward Compatibility
Maintains compatibility with all Vercel Web Interface Guidelines.

## Usage Examples
Run an audit on all source components:
```bash
web-audit src/components/*.jsx
```

## Extension Points
Custom local rules can be added to complement the fetched remote guidelines.

## Limitations
- Static review only. Visual-only checks should be verified via frontend-visual-debug.
- Requires network access to fetch guidelines.
