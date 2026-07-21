---
name: semantic-docs-cleanup
description: Use when cleaning or migrating the project docs directory into semantic feature-family folders. Safely inventories legacy docs, classifies feature families, backs up files, migrates clean tracked artifacts into docs/features/<feature-family>/<stage>/, skips WIP, removes empty obsolete folders, and writes audit reports.
command: /semantic-docs-cleanup
aliases:
  - docs-cleanup
  - semantic-docs
  - cleanup-docs
category: documentation
tags:
  - docs
  - migration
  - cleanup
  - governance
runtime_requirements:
  rules: required
  state: optional
  approvals: optional
  git: required
  memory: none
  rag: optional
  workspace_scan: required
  environment: cached
  version: none
  provider: optional
  usage: none
---

# Skill: semantic-docs-cleanup

## Purpose
Clean the `docs/` tree by migrating legacy workflow artifacts into the canonical semantic layout:

`docs/features/<feature-family>/<stage>/<original-file-name>`

Use this skill when the user asks to clean, migrate, regroup, reorganize, audit, or validate `docs/` by real feature/domain family.

## Hard Rules
- Work only inside `docs/` and `_to_delete/semantic-docs-cleanup/` unless the user explicitly asks for rule updates.
- Never create feature folders from work item IDs such as `FEAT-*`, `FIX-*`, or `QUICK-*`.
- Never move, delete, or rewrite modified or untracked WIP files.
- Always backup every moved/deleted file before applying changes.
- Delete only junk placeholders (`.DS_Store`, legacy `.gitkeep`) and empty obsolete directories.
- Do not write local absolute paths, `file:///` links, or machine-specific paths in reports.
- Reports must use neutral technical language.

## Workflow
1. Read `AI_RULES.md` and `AGENTS.md` documentation governance rules.
2. Run a dry-run inventory:
   ```bash
   python skills/semantic-docs-cleanup/scripts/semantic_docs_cleanup.py --dry-run
   ```
3. Review the generated dry-run report under `_to_delete/semantic-docs-cleanup/reports/`.
4. If classification looks wrong, rerun with explicit overrides:
   ```bash
   python skills/semantic-docs-cleanup/scripts/semantic_docs_cleanup.py --dry-run --override docs/path/file.md=workflow-runtime:reports
   ```
5. Apply only after the dry-run has no blocking failures and the user asked for cleanup:
   ```bash
   python skills/semantic-docs-cleanup/scripts/semantic_docs_cleanup.py --apply
   ```
6. Independently validate the result:
   ```bash
   python skills/semantic-docs-cleanup/scripts/semantic_docs_cleanup.py --validate-only
   ```
7. Report PASS only when:
   - no clean tracked legacy files remain outside `docs/features/`;
   - remaining legacy files are modified/untracked WIP only;
   - no forbidden ID-derived directory exists under `docs/features/`;
   - every moved/deleted file has a backup;
   - reports contain no local absolute paths or family-role wording.

## Stage Mapping
- `docs/brainstorming/*` -> `brainstorming`
- `docs/plans/*`, `docs/planning/*` -> `plans`
- `docs/blueprints/*`, `docs/designs/*`, `docs/architecture/*` -> `blueprints`, unless content is clearly a report/review/plan
- `docs/issues/*` -> `issues`
- `docs/quick/*` -> `quick`
- `docs/debug/*` -> `debug`
- `docs/verification/*` -> `verification`
- `docs/reports/*`, `docs/audit/*` -> `reports`
- `docs/reviews/*` -> `reviews`
- `docs/architecture-reviews/*` -> `architecture-reviews`
- `docs/adr/*` -> `adr`
- `docs/release/*`, `docs/releases/*` -> `releases`
- root roadmap files -> `roadmaps`
- governance standards -> `governance`
- general guides/reference docs -> `docs`

## Family Classification Guidance
Classify from content, not IDs. Read filename, title/headings, summary/problem statement, and linked artifacts.

Common families:
- `visualizer`: VS Code Visualizer extension, webview, sidebar, drawer, layout, screenshots, visual debug.
- `telegram`: Telegram bot, daemon, inbox/outbox, notification routing.
- `workflow-runtime`: runtime engine, session, token accounting, checkpoints, providers, state, locks, CLI runtime.
- `workflow-coordinator`: orchestration, agents, approval gates, choice protocol, workflow routing, multi-agent coordination.
- `project-memory`: memory, RAG, Obsidian, knowledge runtime, context summaries.
- `release-public-export`: release, changelog, versioning, packaging, `public_export`, install/upgrade/rollback.
- `documentation-governance`: docs standards, blueprint governance, templates, compliance, style guides.
- `framework-architecture`: ADRs and framework-wide architecture/policy.
- `cloud-local-hybrid`: cloud-local hybrid, fleet, scheduler, cloud control plane, disaster recovery.
- `vir`: VIR visual intelligence runtime and related architecture.

If confidence is below `0.90`, skip the file and record `NEEDS_REVIEW` in the report.

## Output
The script writes:
- `_to_delete/semantic-docs-cleanup/reports/<timestamp>_inventory.json`
- `_to_delete/semantic-docs-cleanup/reports/<timestamp>_plan.json`
- `_to_delete/semantic-docs-cleanup/reports/<timestamp>_report.md`
- `_to_delete/semantic-docs-cleanup/reports/<timestamp>_review.md`

Final answer should summarize counts, remaining WIP files, and any NO-GO points.
