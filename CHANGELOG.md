# Changelog

## v6.24.4 - 2026-08-23

### Fixed
- **Native Prompt Gate Priority**: Standardized approval and choice gates to use native Agent/IDE `ask_question` first, with `aiwf prompt select` limited to a fallback bridge.
- **Headless Prompt Safety**: Strategic approval prompts now report `PROMPT_UNAVAILABLE` when no real prompt or stdin answer is available, preventing unavailable prompts from being interpreted as `Cancel`.
- **Blueprint Quality Gates**: Hardened quick-fix, quick-feature, and standard Blueprint review gates so source-changing Blueprints require `CODE_BLOCK_GATE: PASS`, 500-line file budgets, family-folder split evidence, aggregate entry points, and language-specific build/lint/typecheck/test plans before approval.

### Validation
- `python -m py_compile` on modified workflow runtime modules and prompt gate tests -> pass.
- `python -m pytest skills\workflow-runtime\tests\unit\test_prompt_bridge_priority.py -q` -> 3 passed.
- `python -m pytest public_export\skills\workflow-runtime\tests\unit\test_prompt_bridge_priority.py -q` -> 3 passed.
- `python -m pytest skills\workflow-runtime\tests\unit\test_runtime_daemon_guardrails.py -q` -> 6 passed.
- `python -m pytest public_export\skills\workflow-runtime\tests\unit\test_runtime_daemon_guardrails.py -q` -> 6 passed.
- Scoped `git diff --check` for release files -> pass.

## v6.24.3 - 2026-08-22

### Fixed
- **Personal Information Scrub**: Removed hardcoded personal names, domains, email addresses, local user paths, hostnames, and credential examples from source, skills, docs, generated artifacts, and release metadata.
- **Environment-Driven Repository Source**: Updated the Agent OS AIWF installer to read the framework repository URL from `AIWF_REPOSITORY_URL`, with a neutral default repository fallback.
- **Neutral Release Metadata**: Replaced personal publisher, website, registry, ingress, msgbus, and documentation examples with neutral placeholder values.

### Validation
- Case-insensitive personal-domain/name/local-path scan -> no matches.
- URL/email/repository/hostname sensitive-string scan -> no matches.
- `python -m py_compile AgentOS\agent_os_runtime\aiwf_installer.py` -> pass.
- JSON parse check for root/editor/package/msgbus configuration files -> pass.

## v6.24.2 - 2026-08-17

### Fixed
- **Session Init RecursionError**: Fixed infinite recursive call to `do_init(args)` in `session_init.py` when initializing a workspace where `project.config.json` does not exist.

## v6.24.1 - 2026-08-17

### Fixed
- **Runtime Summary Functions Signature Mismatch**: Fixed `get_workflow_summary`, `get_project_summary`, and `save_usage_to_dbs` in `metadata_insight_records.py` and `usage_report.py` to accept arguments `(conversation_id, provider, model)` correctly and query SQLite usage records.
- **Session Init NameError**: Fixed `session_dict` variable reference to `session` in `session_init.py`.
- **Memory Bootstrap & Update `files_read` List**: Added `files_read` to result payload in `bootstrap.py` and `update.py`, and added `populate_indexed_files` to record scanned files into SQLite `indexed_files` table.

## v6.24.0 - 2026-08-17

### Features
- **Agent OS Restructure**: Moved all Agent OS code from `skills/` to dedicated `AgentOS/` directory to separate runtime application from AIWF skills
- **AIWF SkillLoader**: Created `skill_loader.py` — discovers and loads 58 AIWF skills from project, maps to 15 agent roles via `AGENT_SKILL_MAP`
- **Skill-Aware Agent Prompts**: `LeaderOrchestrator._build_subtask_prompt()` now injects full AIWF skill instructions into each agent's execution context
- **Skills API**: Added `GET /api/skills` (list all skills + agent mappings) and `GET /api/skills/agent/{name}` (per-agent skill lookup with context preview)

### Fixed
- **Token Burn Prevention**: Changed Leader `auto_pilot` default to `False` and increased poll interval from 4s to 30s. Leader no longer auto-burns tokens on startup
- **Zombie Task Detection**: Added stuck/zombie task detection in `LeaderOrchestrator` — auto-fixes tasks with `completed_at` but `status=running`, and tasks stuck > 10 min with no subtasks

### Changed
- `start_agent_os.py` updated to load from `AgentOS/` path
- `container.py` references updated from `skills/` to `AgentOS/`
- `builder.py` base_dir updated to `AgentOS/agent_os_kernel`

## v6.23.0 - 2026-08-14

### Features
- add msgbus-ws LAN realtime message+file bus skill (QUICK-043) (b390e01b)


All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.22.1] - 2026-08-12

### Fixed

- **Runtime Daemon Reliability (FIX-413)**:
  - Added singleton state handling so repeated runtime starts report the existing daemon instead of spawning duplicate PIDs.
  - Hardened Windows runtime autostart policy to avoid visible Startup Folder `.cmd` fallback behavior.
  - Added runtime heartbeat/status metadata and `workflow submit --prompt` command parity.
- **Prompt Gate UX & JSON Hygiene**:
  - Updated AIWF prompt gate policy to prefer native `ask_question` first and fall back to `aiwf prompt select`.
  - Added regression coverage for ask-question-first prompt bridge output and malformed raw JSON fallback wording.
- **Session Mailbox Safety**:
  - Renamed the cross-project session bus skill to `session-mailbox`.
  - Added a safe JSONL mailbox utility with JSON serialization, file locking, validation, and repair quarantine for corrupted lines.
- **Release Skill Encoding**:
  - Removed UTF-8 BOM from `implementation-to-release/SKILL.md` so skill frontmatter validation passes.
- **Release Publication Runbook**:
  - Documented that `make export` only prepares a release locally; GitHub receives a version only after `public_export` is committed, tagged, and pushed.
  - Added the required post-publish local install step: `aiwf update -Force` on Windows and `aiwf update --force` on Unix shells.

### Validation

- `python -m pytest skills\session-mailbox\tests\test_session_mailbox.py -q` -> 3 passed.
- `python -m pytest skills\workflow-runtime\tests\unit\test_runtime_daemon_guardrails.py skills\workflow-runtime\tests\unit\test_prompt_bridge_priority.py skills\session-mailbox\tests\test_session_mailbox.py -q` -> 9 passed.
- `powershell.exe -ExecutionPolicy Bypass -File tools\validate-skills.ps1` -> all 56 skills valid.
- `python -m workflow_runtime workflow submit --prompt "fix runtime daemon singleton"` -> routed successfully.
- `python -m workflow_runtime runtime status` -> runtime daemon active.

### Known Test Harness Drift

- The broad legacy `skills/workflow-runtime/tests/unit` collection still contains stale imports for modules that were moved out of `skills/workflow-runtime/scripts`; release validation used the affected targeted suites and live CLI smoke checks instead of treating that existing harness drift as a product regression.

## [6.22.0] - 2026-08-10

### Fixed

- **SKILL.md UTF-8 BOM & Frontmatter Restoration**:
  - Removed UTF-8 BOM (`EF BB BF`) from 9 skill files (`skills/workflow-coordinator`, `skills/workflow-command-audit`, `skills/csharp-dotnet-pro`, `skills/document-compliance-assessment`, `skills/go-development`, `skills/golang-pro`, `skills/notify-telegram`, `skills/python-development`, `skills/web-design-guidelines`).
  - Added mandatory `description:` frontmatter field to `skills/aiwf`, `skills/workflow-coordinator`, and `skills/workflow-command-audit`.
  - Added export-time BOM stripping and YAML frontmatter validation in `tools/export.js`.
  - Added CI validation tools `tools/validate-skills.sh` and `tools/validate-skills.ps1`.
- **Installer & Updater Safety Guards**:
  - Hardened `install.sh`, `install.ps1`, `update.sh`, and `update.ps1` to validate `SKILL.md` frontmatter before copying. Invalid source skills are skipped to preserve existing working mirrors and trigger exit code `1`.
- **PowerShell/.NET CWD Path Resolution**:
  - Resolved CWD path resolution mismatch in `update.ps1` using `$ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath()`.

## [6.21.4] - 2026-08-06

### Fixed

- **Hotfix: `aiwf update --all` ParameterBindingException** (`update.ps1`):
  - PowerShell `param()` chỉ nhận `-Flag` (single dash), không nhận `--flag` (double-dash Linux style).
  - Thêm post-`param()` normalization loop để map `--all` → `$All`, `--force` → `$Force`, `--current` → `$Current`.
  - Bây giờ cả `aiwf update -All` và `aiwf update --all` đều hoạt động đúng.

## [6.21.3] - 2026-08-06

### Fixed

- **Hotfix: Import errors in `workflow_runtime` package** (`skills/workflow-runtime` v2.12.1):
  - `bootstrap.py`: Fixed bare `from analyzer import ProjectAnalyzer` → `from .analyzer import ProjectAnalyzer` (relative import).
  - `bootstrap.py`: Fixed bare `from git_diff import get_latest_commit_hash` → `from .git_diff import get_latest_commit_hash` (relative import).
  - `shared_helpers.py`: Fixed `NameError: name 'runtime_bus_autostart_target' is not defined` — added lazy import from `provider_data` inside `is_runtime_bus_autostart_enabled()`.
  - Root cause: bare module imports work in development (sys.path includes package root) but break when called as `python -m workflow_runtime` from an installed location.

## [6.21.2] - 2026-08-04

### Fixed

- Hardened document-authoring skills so low-reasoning agents reject rubber-stamp reviews, mojibake, local-file links, completion claims without live runtime evidence, and no-test-files coverage claims.
- Added a hard installed-mirror write ban for `.agents/skills/**`; AGY command-bus runs now roll back and fail unauthorized mirror edits.
- Fixed fresh-project full-flow CLI issues for `install --help`, non-interactive init config loading, init workspace validation, release dry-run output, and post-release lifecycle commands.

### Validation

- `python -m pytest -q skills\workflow-runtime\tests\test_agy_command_bus_enforcer.py` -> 23 passed.
- Fresh scratch one-line flow from `git init` through `aiwf post-release status` -> PASS.

## [6.21.1] - 2026-08-04

### Fixed

- Hardened AIWF runtime command-bus enforcement for low-reasoning AGY model runs:
  - Guarded `agy.run` now runs in plan mode before Blueprint approval.
  - Runtime request JSON accepts Windows UTF-8 BOM files.
  - Windows path separators are normalized before documentation diff checks.
  - Runtime output and generated artifacts are sanitized for local path leaks.
- Strengthened workflow-document quality gates:
  - Workflow/model tests must follow the standard roadmap -> architecture review -> brainstorming -> architecture review -> plan -> architecture review -> blueprint -> architecture review sequence.
  - Brainstorming, plan, and blueprint stages must include both master and phase artifacts.
  - Every Blueprint file must independently include change matrix, API signatures, schemas, targeted tests, risks, binary acceptance criteria, and detailed code or pseudocode blocks.
  - Placeholder markers are rejected across all Markdown workflow artifacts.
- Fixed installer and CLI compatibility issues:
  - Root `AGENTS.md` and `AI_RULES.md` are installed into new projects.
  - `aiwf config --check-only` is accepted by the modular CLI parser.
  - Installed projects no longer receive transient scratch, cache, or browser-profile directories.
- Added release evidence report for AGY medium workflow validation under `docs/reports/`.

## [6.21.0] - 2026-08-03

### Added

- **QUICK-039: Command Registry Refactoring** (`skills/workflow-runtime` v2.11.0 → v2.12.0):
  - Refactored `workflow_runtime` package CLI command layer to use a modular Command Registry pattern.
  - Split monolith command execution (`workflow_runtime.py`) into 21 independent command modules under `commands/`.
  - Enforced 500-line limit across all `workflow_runtime` source files, splitting large files into `_ext` and `_p2` modules.
  - Command `help()` is now automatically generated and synchronized with the registry.

## [6.20.44] - 2026-07-31

### Fixed

- **FIX-426: `initialize-workflow` Missing Rules & Context Load** (`skills/initialize-workflow` v3.2.0 → v3.3.0):
  - Thêm **Rules & Policy Loading** (item 3 mới trong Section 2): agent bắt buộc đọc `AI_RULES.md` và `AGENTS.md` **trước tiên** trước bất kỳ hành động nào, ngăn vi phạm Blueprint Mandatory Policy (§13), Approval Gate Policy (§1), và Workflow First Enforcement (§27) ngay từ đầu session.
  - Thêm **Memory Context Loading** (item 4 mới): agent đọc `memory/walkthrough.md`, `state/walkthrough.md`, `inbox/inbox.json`, và `project-profile.json` để biết rõ việc đang làm dở dang từ session trước.
  - Renumber các items cũ 3→5, 4→6, 5→7, 6→8, 7→9.
  - Thêm Section 4 **Mandatory Bootstrap Execution Checklist** với 13 bước ordered rõ ràng.
  - Cập nhật `BOOTSTRAP_BLOCKED` để cũng block khi `AI_RULES.md` không tồn tại.

- **FIX-427: `initialize-workflow` Session Cache Behavior** (`skills/initialize-workflow` v3.3.0 → v3.4.0):
  - Phân loại 13 bước bootstrap thành `[CACHED]` (đọc 1 lần/session) và `[REFRESH]` (luôn reload): tiết kiệm ~110KB token mỗi lần gọi lại `/aiwf` trong cùng session.
  - Cập nhật YAML `runtime_requirements`: `rules: session_cached`, `memory: session_cached`.
  - Thêm Section 5 **Session Cache Behavior** với bảng phân loại 13 file theo Mode A (first call) và Mode B (subsequent call).

### Removed

- Xóa scratch/temp files không cần thiết: `refactor_phase*.py`, `gen_parallel.ps1`, `generate_python_blueprints.ps1`, `fake_cookies.json`, `fake_secrets.json`, `screenshot.png`, `run_frontend_and_review.ps1`, `run_full_workflow.ps1`, `public_export_*_result.txt`.

## [6.20.41] - 2026-07-31

### Added
- **Ollama & Docker detection**: Implemented `detect_infrastructure()` in `analyzer.py` to identify local models and containerization runtimes on the host machine. These are now correctly populated into the `Local Infrastructure & Models` section of `project-summary.md` and `architecture/overview.md` during memory generation.

### Fixed
- **Empty files_written output**: Patched `bootstrap.py` and `update.py` in the workflow-runtime to properly track and return `files_written: [...]` to the CLI instead of returning an empty array when executing `aiwf memory update` and `bootstrap` commands.
- **Type Hint Warnings**: Cleared `list[dict]` generic typing warnings in `analyzer.py` and `markdown_writer.py` to comply with `basedpyright` strict analysis.

## [6.20.40] - 2026-07-31

### Fixed

- **Apply all 4 governance fixes to `plan-to-blueprint/SKILL.md`**:
  Corrected a prior omission: `plan-to-blueprint` generates the Technical Blueprint artifact and therefore
  requires the same governance standards as `quick-feature` and `quick-fix`.

  1. *CODE_BLOCK_GATE* (Section 8 — Blueprint Quality Gates): Hard `[!CAUTION]` gate added.
     Every code block in the generated Blueprint must be verified against actual source files
     (`view_file`/`grep_search`), cited with `// verified from: <path:line>`, and never copied from
     memory without re-reading source in the current session.
  2. *Expanded Internal Review Evidence table* (Section 8): Blueprint template now mandates 6
     checklist rows + mandatory CODE_BLOCK_GATE row. CODE_BLOCK_GATE must be explicitly `PASS`
     before submission for Architecture Approval.
  3. *Approval gate anti-bypass* (Section 10 — Gate Hooks): Closed the `aiwf prompt select`
     bridge-unavailability loophole. Chat approval is NEVER valid; agent must stop unconditionally
     and wait for runtime `Continue` or user typing `APPROVE BLUEPRINT` in a new turn.
  4. *Live checklist ticking* (Section 10, item 5): Implementation checklist items must be ticked
     `[x]` one-by-one immediately after each code write. Batching all writes then ticking at end
     is FORBIDDEN. Blocked items use `[!]` marker with inline note.

- **CHANGELOG.md corruption repaired**: User message text accidentally inserted into v6.20.39
  CHANGELOG entry (lines 21-22) has been removed and correct entry restored.

## [6.20.39] - 2026-07-31

### Fixed

- **Apply governance fixes to all implementation-path skills** (`quick-fix`, `blueprint-to-implementation`):
  Extended the three governance patches previously released for `quick-feature` (v6.20.37-38) to the full skill pipeline:

  **`quick-fix/SKILL.md`** — all 3 fixes applied:
  1. *CODE_BLOCK_GATE* (Section 4): Hard `[!CAUTION]` gate — every code block must cite `// verified from: <path:line>`, no guessed identifiers, banned code blocks for hallucinated method names/imports/fields.
  2. *Approval gate hardening* (Step 8): Chat approval NEVER valid; only `Continue` from runtime prompt OR user typing `APPROVE BLUEPRINT` in new turn. Self-declaring bridge unavailability = CRITICAL VIOLATION.
  3. *Live checklist ticking* (Step 10): Each checklist item ticked `[x]` immediately after its code write, one-by-one. Batching at end FORBIDDEN. Blocked items use `[!]` marker.
  4. *Internal Review Evidence table expanded*: 6 checklist rows + mandatory CODE_BLOCK_GATE row (replaces vague single "Checklist Result" row).

  **`blueprint-to-implementation/SKILL.md`** — live checklist ticking added to Section 10:
  - New "Live Checklist Ticking" policy in the Task Evidence section applies to all blueprints with `## Implementation Checklist` sections regardless of skill path (quick-feature, quick-fix, or full plan→blueprint→implementation).
  - Hash-mismatch / scope-blocked items use `[!]` marker instead of silent skip.

  **Skills NOT patched** (no blueprint/code block output):
  - `brainstorming` — produces brainstorming artifact only, no code blocks, no approval gate.
  - `brainstorming-to-plan` — produces plan artifact only, no code blocks, no implementation step.
  - `plan-to-blueprint` — **PATCHED in v6.20.40** (produces Technical Blueprint, requires all 4 governance fixes).

## [6.20.38] - 2026-07-31


### Fixed

- **Blueprint checklist not ticked during implementation** (`quick-feature/SKILL.md`):
  Step 10 previously said only "Implement code changes exactly as described in the blueprint", giving no instruction about the checklist. Agents would implement all code and never update the `- [ ]` items. New policy enforces a strict per-item loop:
  1. Read one checklist item.
  2. Implement code for that item only.
  3. Immediately write `- [x]` to the Blueprint file via `multi_replace_file_content`.
  4. Proceed to the next item.
  Batching code first then ticking all at the end is now explicitly **FORBIDDEN**.
  Blocked items must be marked `- [!]` with inline blocker notes instead of being skipped silently.

## [6.20.37] - 2026-07-31


### Security / Governance

- **Blueprint Approval Gate — close "prompt bridge unavailable" bypass loophole** (`quick-feature/SKILL.md`):
  The old policy allowed agents to self-declare the `aiwf prompt select` runtime bridge as unavailable and treat plain chat text as a valid fallback approval. This was a critical bypass vector. New policy:
  - **CHAT APPROVAL IS NEVER VALID** regardless of bridge availability.
  - The ONLY valid approval is: runtime prompt returning `Continue` OR the user explicitly typing the exact phrase `APPROVE BLUEPRINT` in a **new user turn**.
  - An agent claiming bridge unavailability in the same turn as Blueprint presentation and then continuing to implement is now classified as a **CRITICAL VIOLATION**.

- **Blueprint CODE_BLOCK_GATE — enforce source-verified code blocks** (`quick-feature/SKILL.md`):
  Section 4 "Algorithms & Key Logic" now has a hard `[!CAUTION]` gate. Every non-trivial code block must be verified against actual source files (`view_file`/`grep_search`) within the current session. Code blocks must carry `// verified from: <path:line>` annotations. Invented method names, guessed import paths, and hallucinated struct fields are explicitly **banned**. `NOTE` or `PENDING` in the Internal Review Evidence row is treated as automatic FAIL.

- **Internal Review Evidence table expanded** with 6 explicit checklist rows (No Placeholders, File-by-File Change Matrix, API & Interface Signatures, Data Schemas & Models, Test Strategy, Risk & Mitigation) plus a mandatory `CODE_BLOCK_GATE` row. Vague single-row "Checklist Result" removed.

- **IDE Planning Mode Anti-Bypass Policy added** (`AGENTS.md`): The IDE "Proceed" button DOES NOT constitute Blueprint Approval Gate. Documented and enforced in both primary and `.agents/` copies of `AGENTS.md`.

- **UTF-8 encoding fix** (`AGENTS.md`, `.agents/AGENTS.md`, `temp.ps1`): Repaired mojibake characters introduced by Windows-1252/Latin-1 misreads (`â€"` → `—`).

## [6.20.36] - 2026-07-31


### Fixed
- **`aiwf coordinator --tick` ValueError on legacy PhaseStatus**: Fixed `ValueError: 'FEATURE_IMPLEMENTATION_COMPLETED' is not a valid PhaseStatus` crash when reading `workflow.json` or `checkpoints.json` files written by older framework versions or custom skill authors. Added `_coerce_phase_status()` helper in `state_store.py` that maps known legacy status strings (e.g. `FEATURE_IMPLEMENTATION_COMPLETED`, `IMPLEMENTATION_COMPLETED`, `DONE`, `RUNNING`, `ERROR`) to their canonical `PhaseStatus` equivalents and falls back to `IN_PROGRESS` for fully unknown values, preventing hard crashes.

### Verified
- `aiwf coordinator --tick` no longer crashes when state file contains legacy status values.
- All canonical `PhaseStatus` values continue to parse correctly.

## [6.20.35] - 2026-07-31

### Fixed
- **`aiwf memory update` ModuleNotFoundError**: Fixed `from memory.update import run_update` failing with `No module named 'memory'` when running via `python -m workflow_runtime`. The `infrastructure/memory/` sub-package uses implicit relative imports (`from common import ...`) and was originally designed to run with its directory on `sys.path`. The caller was adding a wrong path (`presentation/cli/memory/` which does not exist). Fixed by computing the correct path (`presentation/cli/../../infrastructure/memory`) and inserting it into `sys.path` before importing in all three affected locations (`do_memory_action` bootstrap/update/search, `do_update`, and `release_manager`).

### Verified
- `python -m workflow_runtime memory update` returns `{"status": "success"}`.
- All 8 registry unit tests pass.

## [6.20.34] - 2026-07-30

### Fixed
- **Windows Doctor Python Probe Quoting**: Replaced the PowerShell `python -c` inline dependency probe with a here-string piped to `python -`, preventing quote stripping that produced `SyntaxError` on Windows.
- **Windows Doctor Null Output Handling**: Prevented `.Trim()` from being called on null probe output when Python exits with an error.

### Verified
- PowerShell doctor dependency probe is no longer quote-sensitive.
- Existing Bash doctor and registry tests remain unchanged.

## [6.20.33] - 2026-07-30

### Added
- **One-Command Doctor Repair**: `aiwf doctor` now enables safe auto-repair by default, with `--check-only` / `--no-fix` available for read-only diagnostics.
- **Doctor Dependency Repair**: Doctor now checks and installs missing user-level Python runtime packages (`pyyaml`, `psutil`, `pytest`) and verifies runtime CLI dependency readiness with a smoke test.
- **Project Auto-Install**: Doctor installs AIWF into the active Git project from the current package when core `.agents/` files are missing.
- **Project File Self-Heal**: Doctor restores missing project rules or manifest files from the current package.
- **One-Command User Guide**: Added `docs/guides/aiwf_one_command_user_guide.md` for the normal user install/update/runtime flow.

### Fixed
- **Registry Legacy Schema Crash**: Fixed `aiwf registry doctor` crashing with `KeyError: 'aiwf_version'` when older registry records do not contain the newer metadata fields.
- **Registry Backfill**: Registry list/doctor/register/unregister paths now backfill missing legacy fields instead of failing.

### Verified
- Legacy registry record without `aiwf_version` is backfilled and does not crash doctor.
- Registry unit tests: `8 passed`.

## [6.20.32] - 2026-07-30

### Fixed
- **Updater Strict Shell Compatibility**: Fixed `update.sh --all` failing with `PYTHONPATH: unbound variable` when `PYTHONPATH` is unset under `set -u`.

### Verified
- `update.sh --all` with `PYTHONPATH` unset using a mocked `python3` executor.
- `public_export/update.sh --all` with `PYTHONPATH` unset using a mocked `python3` executor.
- `update.sh --all` preserves an existing `PYTHONPATH` suffix.

## [6.20.31] - 2026-07-30

### Added
- **Natural Prompt AIWF Entry**: Added fail-closed AGY normalization so raw prompts without `/aiwf` are treated as `/aiwf <raw_request>` before AGY can plan or act.
- **Natural Prompt Regression Coverage**: Added source and mirror tests for command-bus prompt normalization, gateway routing, and agent dispatch prompt contracts.
- **User Guide**: Added a user-facing guide for AGY install/update/runtime restart, memory bootstrap/update, natural prompt usage, documentation gates, verification, and release.

### Changed
- **AGY Command Bus Guard**: Hardened `agy.run` so guarded pre-approval runs require workflow documentation changes by default and fail when AGY only responds or implements without persisting docs.
- **Workflow Gateway Intake**: Changed natural language gateway behavior from chat bypass to workflow routing by default, including Vietnamese engineering intent keywords and runtime state/event initialization.
- **CLI Entrypoint Alignment**: Unified `python -m workflow_runtime` with the installed `aiwf` wrapper command surface and repaired compatibility for `verify`, `state`, `memory`, `knowledge`, `migration`, and related CLI groups.

### Fixed
- **Missing Coordinator Script Dependency**: Replaced the gateway dependency on the absent `workflow-coordinator/scripts/coordinator.py` path with the runtime coordinator service.
- **Runtime State Compatibility**: Fixed workflow gateway state persistence to write enum-compatible `IN_PROGRESS` status and set workflow environment context for managed tool execution.
- **Global Wrapper Drift**: Updated bootstrap/update wrappers to invoke `python -m workflow_runtime` consistently.

### Verified
- Source and mirror targeted runtime tests: `21 passed` each.
- Source and mirror CLI help matrix: `134` checks, `0` failures.
- Source and mirror CLI handler matrix: `32` checks, `0` failures.
- Source and mirror skill verification: `55/55` skills, average score `100/100`.
- Command-bus smoke: raw prompt without `/aiwf` normalized to `/aiwf`, guard applied, documentation gate enforced.

## [6.20.30] - 2026-07-30

### Added
- **AGY Release Artifact Gate**: Added `require_release_artifacts` enforcement for `agy.run` so release dry-runs must update release metadata (`CHANGELOG.md`, manifest/package metadata) and create or update a workflow report under `docs/`.
- **AGY Release Regression Coverage**: Added source and mirror tests covering release metadata change detection and semantic report path detection.

### Changed
- **AGY Workflow Enforcement**: Hardened command-bus AGY runs with persisted documentation/report gates, blueprint quality checks, sanitized runtime output, same-context stress validation, and fail-closed `/aiwf` pre-approval source protection.
- **Telegram Supervision**: Updated workflow rules and initialization so Telegram is runtime-supervised only; initialize no longer starts a standalone Telegram daemon.

### Fixed
- **AGY Command Builder**: Fixed AGY command ordering, `--effort high`, resolved working directory handling, and prompt text handling so AGY prompts containing test terminology do not trigger false test-command blocks.
- **Skill Verification**: Fixed false positive absolute-path and placeholder detections while preserving real local-path leak enforcement.

### Verified
- Source and mirror AGY command-bus tests: `11 passed` each.
- Source and mirror skill verification: `55/55` skills, average score `100/100`.
- Same-context AGY workflow stress fixture: `35 passed`.
- AGY release dry-run fixture: created release report, `CHANGELOG.md`, and `MANIFEST.json`; source files unchanged; path-leak scan clean.

## [6.20.29] - 2026-07-30

### Added
- **Transactional Documentation–Source Synchronization**: Registered `documentation-synchronization-governance` support skill (`skills/documentation-synchronization-governance/SKILL.md`) enforcing `NO REQUIRED DOCUMENT = NO CODE`, `NO BLUEPRINT = NO CODE`, and `NO DOCUMENT UPDATE = NO SOURCE CHANGE COMPLETION`.
- **DOCUMENTATION_SYNC_GATE**: Established `DOCUMENTATION_SYNC_GATE` verifying `all_required_documents_exist`, `zero_stale_documents`, `zero_missing_documents`, and `all_sha256_verify` before phase completion or `@aiwf next` command execution.
- **Workflow Document Reconciliation**: Reconciled workflow documentation files with `documentation-dependency-graph.json` and `documentation-sync-state.json` across active workflow runs under `docs/aiwf-runs/`.

## [6.20.28] - 2026-07-29

### Added
- **No Blueprint No Code Policy**: Enforced mandatory pre-implementation document lifecycle (`00-intake/` -> `05-blueprint/`) before any business source code file modification.
- **CODE_BLOCK_GATE & SOURCE_WRITE_GUARD**: Established `CODE_BLOCK_GATE` requiring `readiness_score >= 95/100`, zero Critical/High blockers, and design code blocks, enforced via `SOURCE_WRITE_GUARD` and `implementation-entry-receipt.json`.
- **Pre-Implementation Document Backfill**: Backfilled 24 pre-implementation documentation files across executed workflow runs under `docs/aiwf-runs/`.

## [6.20.27] - 2026-07-29

### Added
- **Mandatory AIWF Bootstrap Contract**: Enforced `aiwf → initialize-workflow → bootstrap receipt → workflow-coordinator` route with fail-closed coordinator guard.
- **Command Receipt Persistence**: Registered `workflow-command-audit` skill (`skills/workflow-command-audit/SKILL.md`) to persist tamper-evident command receipts under `.agents/state/audit/commands/YYYY/MM/DD/` and update `.agents/state/audit/latest-command.json`.
- **Zero Path Leakage Policy**: Enforced POSIX repository-relative path representation and sanitized all historical evidence report files.

## [6.20.26] - 2026-07-29

### Added
- **AIWF Command Suite Expansion**: Enhanced `@aiwf` wrapper skill (`skills/aiwf/SKILL.md`) with full command grammar supporting `help`, `status`, `next`, `continue`, `resume`, `debug`, `verify`, `cancel`, `recover`, and `new-request`.

## [6.20.25] - 2026-07-29

### Added
- **AIWF User Entry Wrapper**: Added `@aiwf` wrapper skill (`skills/aiwf/SKILL.md`) for quick user entry.
- **Redesign Skills Integration**: Registered all 53 skills in `MANIFEST.json` and synchronized `public_export`.

### Fixed
- **Updater Fail-Safe**: Added `Log-Warn` / `log_warn` in `update.ps1` and `update.sh` when a source skill path is missing from the framework root.

## [6.20.24] - 2026-07-27

### Changed
- **Workflow Initialization**: Finalized Output Format block in SKILL.md to render Markdown tables seamlessly.
- **CLI Native Wrapper**: Added support for headless AgY runner via daemon command bus.

### Removed
- **VIR Runtime**: Cleaned up obsolete Python scripts inside `.agents/skills/vir-runtime/scripts/`.

## [6.20.23] - 2026-07-27

### Fixed
- **Qdrant Vector Retrieval**: Fixed syntax bug in `rag_store_adapter.py` that caused RAG search to fail by incorrectly filtering on `{value: kw}` instead of `{text: kw}` during vector REST API calls.
- **Workflow Initialization**: Restored the mandatory `.agents/memory/lessons/` loading rules that were inadvertently removed during a remote branch merge conflict resolution.
- **Public Export Alignment**: Fast-forwarded and committed the `public_export` submodule pointer to align with the latest published commits.

## [6.20.22] - 2026-07-27

### Changed
- **CLI Native Wrapper**: Upgraded the `aiwf` command wrapper to natively delegate to the Python `workflow_runtime` engine, improving startup performance and decoupling from bash-only scripts.

## [6.20.21] - 2026-07-27

### Fixed
- **Rule Loading Redundancy**: Fixed `initialize-workflow` where `AI_RULES.md` was redundantly loaded instead of relying on `AGENTS.md` as the single source of truth. Removed obsolete "Removed Operations" section from `initialize-workflow/SKILL.md`.
- **Workflow Runtime Policies**: Fixed `workflow_runtime.py` to also parse `.agents/AGENTS.md` when gathering rules for `aiwf rules`, ensuring project-specific rules are correctly detected.
- **Walkthrough Privacy Leaks**: Cleaned up absolute local paths in `.agents/memory/walkthrough.md` to prevent local environment path leakage in project memory.

## [6.20.20] - 2026-07-27

### Changed
- **Blueprint Quality Control**: Added a mandatory requirement to `plan-to-blueprint`, `quick-feature`, and `quick-fix` skills. Agents MUST pre-verify code blocks using the Scratch Environment (`.agents/scratch/`) and import the actual project codebase to prove feasibility before writing code into a Blueprint. This strictly prevents hallucinated code in technical designs.

## [6.20.19] - 2026-07-27

### Added
- **Runtime Command Bus `agy.run`**: Added `agy.run` command to the Runtime Daemon Command Bus to orchestrate Sub-Agents headlessly. This provides an architectural solution to securely invoke the Anthropic Claude Code CLI (`agy`) with `--dangerously-skip-permissions` without being intercepted and blocked by the Sandbox Permission Classifier.

### Changed
- **System Coordinator Agent**: Updated `SKILL.md` to formally transition all `agy` sub-agent invocations away from Terminal `run_command` over to the Runtime Command Bus. Also added a requirement for the Coordinator to explicitly feed previous failed review reasons into subsequent AGY retry prompts for a continuous learning loop.

## [6.20.18] - 2026-07-27

### Changed
- **Source Code File Size Limit Exemption Rule**: Generalized the 500-line limit rule in `AGENTS.md` and `.agents/AGENTS.md` to explicitly exempt non-SDK `.csproj` files, `package-lock.json`, `MANIFEST.json`, `CHANGELOG.md`, and other structural manifest/configuration files. Agents are now instructed not to falsely flag these as violations or attempt to split them regardless of their length.

## [6.20.17] - 2026-07-27

### Added
- **Global Payload Rule**: Enforced mandatory content payload generation via global rule across `.agents/AI_RULES.md`, `AGENTS.md`, and `implementation-to-release/SKILL.md`. Agents must explicitly compute and pass content payload (e.g. commit messages) into `args` when calling the Runtime Daemon Command Bus, as the daemon does not auto-generate content.

## [6.20.16] - 2026-07-27

### Fixed
- **Qdrant Adapter Vector Bug**: Fixed an issue in `workflow-runtime` where `aiwf search` returned 0 results because the Qdrant adapter was sending a dummy vector (`[0.0]*128`). Refactored to use Qdrant's `/points/scroll` API with a `should` text filter to correctly retrieve results without an embedding model.
- **Project Memory Gap**: Modified `initialize-workflow` (`SKILL.md`) to explicitly mandate reading critical files inside `.agents/memory/lessons/` (like `known-problems.md`, `coordinator-operating-rules.md`, and `architectural-decisions.md`) upon every startup to ensure the agent does not repeat historical mistakes.

## [6.20.15] - 2026-07-27

### Added
- **Skill Dispatch Enforcement**: Added `Explicit Skill Enforcement Rule` to `workflow-coordinator` to guarantee that assigned agents load and strictly follow their target SKILL.md.
- **Deep Thinking Prompt Injection**: Added `Mandatory Prompt Injection` directive to `system-coordinator-agent` to force AGY into deep-thinking mode and ground its outputs in real code rather than assumptions.
- **Micro-Tasking & Granular Blueprinting**: Added rules to `system-coordinator-agent` to overcome AGY superficial outputs by chunking tasks and mandating code-block-level blueprinting precision.

### Changed
- **System Coordinator Guides Migration**: Migrated `system-coordinator-agent-guide.en.md` and `agy_headless_intergration.md` directly into the `skills/system-coordinator-agent/` folder for better locality. Removed redundant legacy `.vi.md` documentation.
- **Global Rules Cleanup**: Cleaned up legacy `Guide Documentation Protection Rule` and obsolete `System Coordinator Agent Skill Rule` paths from `AGENTS.md` and `.agents/AGENTS.md`.

## [6.20.14] - 2026-07-27

### Fixed
- **CLI Subparser Conflict**: Fixed a critical argument parsing bug where commands like `aiwf start` that accept a `--command` flag conflicted with the root parser's `dest="command"`, causing the CLI to incorrectly fail and print the root help menu instead of executing the command.
- **Workflow Initialization Logic**: Removed the legacy daemon activity check from Step 8 in `initialize-workflow` that inadvertently suppressed the arming of the unified Session Mail & Telegram Inbox monitor. The monitor is now unconditionally armed at Step 10 via the `schedule` tool.

### Changed
- **Initialization Formatting & Structure**: Enhanced `initialize-workflow` report formatting with clean Markdown tables and restructured initialization sequence (Steps 8-10) to clearly separate project inbox monitoring, Session Mail registration, and combined inbox scheduling with adaptive backoff intervals.


## [6.20.8] - 2026-07-25

### Fixed
- Fixed Telegram daemon (`daemon.py`) where 5 send methods in `TelegramDaemonManager` raised `NotImplementedError` and the outbox dispatcher (`validate_outbox_payload`) hard-rejected every outbox type except `TELEGRAM_REPLY`. Only plain-text replies could be sent. All 6 outbox types are now fully operational.

### Added
- **`send_telegram_document`** — Upload any file to Telegram via `sendDocument` (multipart/form-data, 60s timeout).
- **`send_telegram_photo`** — Upload images (`.jpg`, `.png`, `.gif`, `.webp`) via `sendPhoto` with automatic MIME detection.
- **`send_telegram_url`** — Send a clickable URL with Telegram link preview via `sendMessage`.
- **`send_telegram_buttons`** — Send interactive `InlineKeyboardMarkup` button rows via `sendMessage`.
- **`send_telegram_commands`** — Register/update bot menu commands via `setMyCommands`.
- **`_dispatch_outbox`** — Multi-type outbox router supporting 6 outbox types: `TELEGRAM_REPLY`, `TELEGRAM_SEND_DOCUMENT`, `TELEGRAM_SEND_PHOTO`, `TELEGRAM_SEND_URL`, `TELEGRAM_SEND_BUTTONS`, `TELEGRAM_SEND_COMMANDS`.
- **`_build_multipart_body`** — RFC2388 multipart/form-data builder for binary file uploads.

## [6.20.7] - 2026-07-25


### Fixed
- Fixed critical bug in `aiwf update -All` (`update_all_projects()`) where `--force` (double-dash) was passed to `update.ps1` instead of `-Force` (single-dash). PowerShell named switch parameters require single-dash syntax. The double-dash caused `$Force` to always be `$false`, so when the installed version already matched the source version, the update script exited early without copying any files — meaning deleted or missing skills were never restored.

## [6.20.6] - 2026-07-25

### Fixed
- Fixed `do_init()` writing null bytes to `.agents/state/daemon.json`: after checking `~/.aiwf/telegram-daemon.pid`, the real daemon status (PID + running flag) is now written to the JSON cache file so Agent reads always reflect the true state.
- Fixed `monitor_listener.py` reference in `do_init()`: this standalone script was removed during DDD refactoring. The init flow now uses the `python -m workflow_runtime telegram monitor-inbox` CLI module instead.

### Added
- `do_init()` now loads `project-summary.md` and `memory-state.json` from `.agents/memory/` into the session context after startup, so downstream skills have immediate access to project memory without a separate memory-load step.
- `do_init()` now prints a structured **Initialization Report** at the end of every `aiwf init` run, showing: project name/version, conversation ID, git branch, permission mode, runtime mode, memory load status with last-updated timestamp, Telegram daemon PID, and any warnings.

## [6.20.4] - 2026-07-25

### Fixed
- Fixed a critical syntax bug in PowerShell installation scripts (`install.ps1`, `update.ps1`) caused by UTF-8 em-dashes `—` being misinterpreted as smart quotes in Windows-1252 parsing.
- Fixed an issue where `aiwf doctor` would crash because it was still trying to call the deleted legacy `workflow_runtime.py`. It now correctly invokes `workspace_doctor.main()`.
- Added 11 missing skills back to `MANIFEST.json` so they are correctly copied during `aiwf update` or installation:
  - `architecture-review`
  - `csharp-dotnet-pro`
  - `document-compliance-assessment`
  - `go-development`
  - `golang-pro`
  - `notify-telegram`
  - `post-release-lifecycle`
  - `python-development`
  - `python-patterns`
  - `web-design-guidelines`
  - `workflow-coordinator`
- Removed hardcoded references to `docs/release-guide.md` in install and update scripts since this file was migrated during semantic cleanup.

## [6.20.3] - 2026-07-25

### Removed
- **Telegram Legacy Scripts Cleanup**:
  - Permanently deleted obsolete legacy shell and python scripts (`poll_reply.sh`, `send_file.sh`, `monitor_listener.py`, etc.) from the `notify-telegram` skill. These were accidentally left in the source tree during the `6.20.1` upgrade, causing them to leak into the `public_export`.

## [6.20.2] - 2026-07-25

### Fixed
- **Global CLI Module Resolution**:
  - Fixed a critical `ModuleNotFoundError: No module named workflow_runtime` bug in the global `aiwf` CLI wrappers (`bootstrap.ps1` and `bootstrap.sh`).
  - Corrected the `PackageRoot` path resolution logic, ensuring `PYTHONPATH` correctly targets the `skills/workflow-runtime` directory when executing `python -m workflow_runtime` commands.

## [6.20.1] - 2026-07-25

### Changed
- **Telegram Notification System Upgrade**:
  - Deprecated and removed legacy shell scripts (`poll_reply.sh`, `send_file.sh`, etc.) for Telegram notifications.
  - Unified the Telegram interaction model into a file-based JSON Inbox/Outbox mechanism powered by a robust Python daemon (`python -m workflow_runtime telegram daemon`).
  - Simplified proxy and daemon management; the daemon is now strictly run externally by the user, isolating network complexity from agent skills.
- **Release & Export Pipeline (`Makefile`)**:
  - Removed legacy Golang binary compilation (`aiwf exe`) and injection from the export pipeline. The `make export` process now cleanly exports only essential IDE resources, significantly improving build speeds and reducing noise.

## [6.20.0] - 2026-07-23

### Added
- **Python VAR Agent Hexagonal Architecture (FEAT-505)**:
  - Completely ported the Visual Agentic Runtime (VAR) to a strict Hexagonal Architecture (`vir_runtime/varbc`).
  - Added new domain entities (Pydantic v2) for zero-dependency modeling.
  - Implemented `VARAgentLoop`, `VARInvestigator`, and `VARVerifier` with separated infrastructure ports.
  - Added `AsyncCDPClient`, `DrissionPageAdapter`, and `PlaywrightAdapter` through a dynamic `AdapterFactory`.
  - Introduced `var_dispatch.py` as a centralized CLI bridge, while replacing legacy agent scripts with thin wrappers.

## [6.19.7] - 2026-07-23
- **`aiwf doctor` check**:
  - Added a new `workflow_runtime_daemon` check to detect if the agent-safe runtime daemon is running, missing, or stale.

## [6.19.6] - 2026-07-23

### Added
- **`aiwf doctor` command**:
  - Added new CLI command to check workspace health (git status, python/node versions, `.agents/state`, project memory).
  - Included JSON reporting mode (`--json`) and markdown table output.

### Changed
- **AIWF Framework Rules Update**:
  - Updated 6 global policies in `AGENTS.md` covering workflow routing, 5-agent coordination, strict code-build-test loops, and zero-placeholder blueprints.
  - Enforced `workflow-coordinator` first policy for all requests.

### Fixed
- **`aiwf doctor` workspace root resolution**:
  - Fixed false-negative path resolution errors by detecting project root via `git rev-parse` instead of using the raw working directory.
- **`make export` binary injection**:
  - Fixed race condition where `tools/export.js` cleaned `public_export/` after binaries were injected, deleting them. Rewrote Makefile ordering to fix this.

## [6.19.5] - 2026-07-21

### Changed
- **Lightweight Runtime Initialization**:
  - Updated `initialize-workflow` context tracking and ISO timestamp updates.
- **Visualizer Extension v1.0.49**:
  - Recompiled webview resources (`webviewHtml.ts`) from `webview.html` source.

## [6.19.4] - 2026-07-21

### Changed
- **Telegram inbox workflow continuity**:
  - Updated `initialize-workflow` so agents must arm the project inbox monitor with a 10-second schedule timer only when the shared Telegram daemon is active.
  - Clarified `notify-telegram` project inbox guidance so the scheduled monitor continuously checks `.agents/inbox/inbox.json` without noisy idle replies.

### Fixed
- **Telegram group routing**:
  - Added a fallback for unmapped Telegram groups so the daemon can route a group message to the active project and persist that chat binding for later messages.

## [6.19.3] - 2026-07-21

### Added
- **AIWF Framework desktop app release pipeline**:
  - Added desktop packaging targets for macOS installers and GitHub release artifacts.
  - Added a GitHub Actions desktop release workflow that builds downloadable packages on tag pushes.

### Fixed
- **AIWF Framework macOS tray behavior**:
  - Kept the desktop app running in the macOS menu bar when the main window is closed.
  - Enforced singleton launch behavior so opening the app again focuses the existing instance.
  - Fixed the tray icon rendering by using a dedicated macOS template tray glyph instead of the full app icon.
- **AIWF Framework desktop runtime execution**:
  - Resolved Python runtime launch failures on machines where `python` is not available by detecting `python3`, `python`, `py -3`, or an explicit `AIWF_PYTHON` override.
  - Added macOS signing and notarization hooks for trusted public `.pkg` and `.dmg` releases.

## [6.19.2] - 2026-07-21

### Fixed
- **Blueprint Approval scope enforcement**:
  - Blocked implementation when a Blueprint approval belongs to a different work item than the current workflow.
  - Prevented full-access and autonomous delivery modes from auto-approving final Blueprint Approval gates.
  - Added runtime and coordinator validation so Blueprint approval records must match the active work item, Blueprint path, and Blueprint frontmatter.
  - Added regression coverage for the cross-work-item approval case that previously allowed `FIX-*` state to unlock a `FEAT-*` Blueprint.

## [6.19.1] - 2026-07-21

### Added
- **Semantic documentation cleanup skill**:
  - Added `semantic-docs-cleanup` with `/semantic-docs-cleanup`, `/docs-cleanup`, `/semantic-docs`, and `/cleanup-docs` entry points.
  - Added deterministic dry-run, apply, and validate-only cleanup flows for migrating legacy `docs/` artifacts into `docs/features/<feature-family>/<stage>/`.
  - Added backup, WIP protection, forbidden ID-folder validation, and report/review generation under `_to_delete/semantic-docs-cleanup/`.

### Changed
- **Documentation governance and artifact layout**:
  - Migrated clean tracked legacy documentation into semantic feature family folders under `docs/features/`.
  - Updated workflow rules and skills to require new FEAT/FIX/QUICK artifacts to use semantic feature family paths instead of flat legacy stage folders.
  - Added manifest registration for `semantic-docs-cleanup` in the documentation category.

### Fixed
- **Runtime and daemon management polish**:
  - Added the `runtime reload` action to restart both the runtime bus and shared Telegram daemon.
  - Restored orchestrator status and health subcommands while keeping deprecated resident daemon actions blocked.
  - Updated targeted runtime and Telegram routing tests for the current command behavior.

## [6.19.0] - 2026-07-21

### Added
- **AIWF runtime configuration and project status workflow (QUICK-035 / QUICK-036)**:
  - Added project-aware runtime status reporting for registered projects, workflow state, dependency cache, daemon health, Telegram inbox/outbox, and Git status.
  - Added an interactive AIWF usage guide and interactive docs surface so users can review common setup, status, runtime, and workflow commands from a single place.
  - Added runtime daemon management guidance for start, stop, enable, disable, and restart flows.

- **Visualizer Extension v1.0.47**:
  - Added an Active Project Status panel to show registry, Telegram, Git, workflow, lease, dependency cache, and daemon status for the current project.
  - Added refresh/config controls and parser tests for project status rendering.

### Changed
- **Continuous pre-approval workflow gates**:
  - Updated quick-feature, quick-fix, brainstorming, planning, blueprint, and coordinator skills so agents self-review each pre-approval artifact and continue until the Blueprint review passes.
  - Moved the mandatory user approval stop to the post-Blueprint review gate before implementation.
  - Added strict failure reporting rules so agents must state failed review points and revise only those points before continuing.

- **AIWF global agent rules**:
  - Moved Git staging, targeted pytest logging, environment discovery, frontend-design binding, and continuous pre-approval review rules into the reusable AIWF rules block.
  - Required `frontend-design` whenever a task or artifact touches frontend design, UI/UX, layout, color, typography, animation, icons, or visual hierarchy.

### Fixed
- **Telegram inbox JSON routing**:
  - Updated Telegram message routing to write valid JSON objects into `.agents/inbox/inbox.json` using atomic replacement.
  - Updated the Telegram monitor, routing tests, and notify-telegram documentation to read the JSON inbox format.
  - Ignored local Telegram inbox runtime data while keeping the project inbox folder available.

## [6.18.4] - 2026-07-21

### Added
- **Telegram CLI Interactive Configuration (QUICK-034)**:
  - Added `telegram config` to the workflow runtime so users can configure the Telegram bot token and optional proxy through a guided CLI prompt.
  - Mirrored the command into `.agents/workflow_runtime.__main__` so Antigravity and project-local agents use the same runtime behavior as the canonical `skills/` tree.
  - Updated Unix and PowerShell bootstrap help text to show the Telegram command group.

### Fixed
- **Configuration save robustness**:
  - Empty token input now exits with code 1 when no previous token exists.
  - Telegram configuration writes now use a temporary file plus atomic replacement and sanitized error output.
- **Project-local Telegram inbox routing**:
  - Routed Telegram messages into `.agents/inbox/inbox.json` inside the registered project instead of `~/.aiwf/<project>/inbox.json`.
  - Updated the Telegram monitor and workflow rules so agents may read project-local inbox messages without an extra workflow confirmation prompt.
  - Kept received Telegram files and photos under `.agents/inbox/` so agents with project-only filesystem access can process them.

## [6.18.3] - 2026-07-20

### Fixed
- **Sửa lỗi Telegram Listener Daemon & Thêm Quy tắc Phản hồi (FIX-410)**:
  - Tách tiến trình `listen.sh` thành daemon độc lập bằng cách truyền Parent PID rỗng.
  - Khắc phục lỗi mã hóa Unicode trên hệ điều hành Windows (loại bỏ ký tự emoji `✨`).
  - Gửi thông báo khởi tạo thành công kèm `Conversation ID` hiện hành qua Telegram API.
  - Tự động đăng ký các câu lệnh chính thức của Telegram qua api `setMyCommands`.
  - Khắc phục các xung đột liên quan đến Windows PID trên Git Bash/MSYS và bắt lỗi crash `curl`.
- **Cập nhật chính sách đường dẫn tương đối (Relative Path Policy)**:
  - Yêu cầu bắt buộc mọi tài liệu Markdown (`docs/`) và quy tắc chung (`AI_RULES.md`) phải sử dụng định dạng đường dẫn tương đối thay vì dùng file URL tuyệt đối.

### Added (Visualizer Extension v1.0.46)
- **Tăng cường Extension API & Sidebar controller (QUICK-033 / FEAT-409)**:
  - Đăng ký các lệnh VS Code chính thức `visualizer.getSessionData` và `ai-skill-workflow-visualizer.getSessionData` để xuất trạng thái session hiện tại.
  - Sửa lỗi null check an toàn cho tab stats của Test Coordinator.
  - Bổ sung bộ điều khiển Sidebar Toggle lưu trạng thái mở rộng/thu gọn vào LocalStorage.

## [6.18.2] - 2026-07-19

### Fixed
- **Tự động khởi chạy Telegram Inbox Monitor (FIX-411)**:
  - Tự động chạy tiến trình nền `monitor_listener.py` khi chạy lệnh `init` khởi động workflow, giải quyết vấn đề nhận lệnh Telegram trên các cuộc hội thoại mới.
  - Tương thích tốt với môi trường Windows (`CREATE_NO_WINDOW`) và Unix (`start_new_session=True`), chạy không chặn (non-blocking) và ẩn log.
  - Cập nhật tài liệu kỹ năng `initialize-workflow` để loại bỏ hướng dẫn chạy script `listen.sh` cũ.
- **Quy tắc Kiểm thử Giới hạn Phạm vi (Targeted Testing)**:
  - Bổ sung quy định kiểm thử mới vào `AGENTS.md`, yêu cầu Agent chỉ chạy các test case liên quan trực tiếp đến thành phần chỉnh sửa để tiết kiệm tài nguyên.

## [6.16.0] - 2026-07-13

### Added
- **Antigravity Gateway Adapter (FEAT-315)**:
  - Tích hợp Antigravity IDE với AIWF Workflow Runtime để submit, status và follow các workflows.
  - Cung cấp cơ chế chuyển tiếp cuộc gọi an toàn thông qua các Adapter Gateway.
- **AIWF MCP Auto Provisioning CLI (FEAT-316)**:
  - Triển khai lệnh CLI `aiwf mcp` (hỗ trợ các subactions `install`, `uninstall`, `status`, `doctor`).
  - Hỗ trợ cấu hình mcp.json/settings.json an toàn cho Windows, macOS, Linux trên các IDE Antigravity, VS Code, và Cursor.
  - Tích hợp MCP auto-provision check tự động cài đặt MCP wrapper khi chạy `initialize-workspace`.

## [6.15.4] - 2026-07-13

### Added
- **Session Auto-Initialization & Bootstrap Guard (FEAT-314)**:
  - Triển khai `SessionBootstrapGuard` tự động khởi tạo workspace khi bắt đầu phiên làm việc mới mà không làm mất prompt gốc.
  - Cập nhật CLI lệnh `aiwf session` với status, initialize và reset.
  - Ghi nhận nhật ký sự kiện và cách ly session.

## [6.15.3] - 2026-07-13

### Added
- **Mandatory Entry Gateway Enforcement (FEAT-313)**:
  - Triển khai `WorkflowEntryGateway` bắt buộc toàn bộ các yêu cầu kỹ thuật tự nhiên phải đi qua `workflow_runtime.py workflow submit`.
  - Cập nhật quy tắc toàn cục `Workflow First Enforcement Policy` chặn đứng việc Agent tự viết code ngoài workflow context.
  - Ghi nhận nhật ký sự kiện đồng bộ vào `.agents/state/events.jsonl` tại root của state.

## [6.15.1] - 2026-07-13

### Fixed
- **Verification Gate (FEAT-401)**:
  - Khởi tạo thành công và lập báo cáo kiểm định chất lượng đạt trạng thái PASS cho Work Item FEAT-401 tại docs/verification/FEAT-401_verify.md.

## [6.15.0] - 2026-07-13

### Added
- **Workflow Supervisor & Skill Governance (FEAT-302 / FEAT-304)**:
  - Tái cấu trúc Orchestrator từ Resident Daemon sang mô hình Workflow Supervisor chạy theo phiên (session-based) an toàn.
  - Tích hợp ghi nhận nhật ký sự kiện Observability chi tiết vào `.agents/state/events.jsonl` (gồm workflow.started, phase.started, agent.started, agent.completed, phase.completed, workflow.completed).
  - Cập nhật CLI lệnh `aiwf orchestrator` hỗ trợ các subcommands: start, stop, status, follow, và agents.
  - Triển khai Skill Governance Engine kiểm duyệt vật lý sự tồn tại của tệp tin tài liệu (`docs/brainstorming/`, `docs/planning/`, `docs/blueprints/`) trước khi cho phép vượt qua các cổng kiểm soát trong chế độ autonomous.

## [6.14.2] - 2026-07-13

### Added
- **Session Runtime Redesign (FEAT-211)**:
  - Tái thiết kế Session Runtime Core chuyển đổi từ mô hình đa tiến trình daemon sang in-process async engine siêu nhẹ.
  - Tích hợp SQLite WAL Event Store lưu trữ dòng sự kiện lịch sử phục vụ event replay/recovery và audit trail.
  - Xây dựng Shared Session Context Engine bất biến kết hợp Copy-on-Write và Optimistic Concurrency Control (OCC) loại bỏ xung đột dữ liệu đa tác nhân.
  - Triển khai Scheduler & Bounded Worker Pool quản lý xếp hàng tác vụ và chống quá tải tài nguyên thông qua CPU throttling.
  - Triển khai Tool Executor cô lập tiến trình kết hợp validator toàn cục chặn cuộc gọi subprocess lậu ngoài luồng kiểm duyệt.
  - Thiết lập ranh giới phân quyền phân cấp Permission Boundary đa lớp (Global -> Session -> Agent -> Tool) chống privilege/scope escalation.
  - Xây dựng máy chủ Runtime API v3 JSON-RPC cùng Runtime SDK v3 Client và Adapter tương thích ngược v1/v2 phát cảnh báo di trú.

## [6.14.0] - 2026-07-13

### Added
- **Dynamic Agent Registry**:
  - Triển khai Dynamic Agent discovery và validation sử dụng JSON Schema (`agent.schema.json`).
  - Tự động biên dịch 41 file markdown agent sang tệp registry duy nhất `registry.json`.
  - Cập nhật quyền ghi `scoped-write` hợp lý cho Frontend, Backend, Database và Test Developer Agents.
- **TESTER Agent Ownership Enforcement**:
  - Monkey patch toàn cục `subprocess.run` và `subprocess.Popen` nhằm ngăn chặn mọi hoạt động thực thi test command trái phép (không có active test task hoặc được gán sai owner).
- **Autonomous Workflow & Adaptive Capacity Planning (v1)**:
  - Tích hợp Confidence Gates (yêu cầu >= 95% cho brainstorm/planning/blueprint).
  - Triển khai Adaptive Team Planner và Capacity Controller giúp điều phối tối ưu concurrency dựa trên CPU/RAM và tự động tuyển dụng (dynamic recruitment) specialists.

## [6.13.2] - 2026-07-13

### Fixed
- **OS File Locking & Process Resiliency (FEAT-051 / Multi-Agent Safety)**:
  - Khôi phục công cụ an toàn ghi đa tác nhân [safe_multi_agent_writes.py](skills/workflow-runtime/scripts/safe_multi_agent_writes.py) và các tệp kiểm thử đi kèm.
  - Sửa đổi cơ chế khóa `OSFileLock` trong [session.py](skills/workflow-runtime/scripts/session.py) để cô lập cờ bypass lock chỉ kích hoạt trong môi trường kiểm thử pytest (`PYTEST_CURRENT_TEST`), đảm bảo lock vật lý luôn hoạt động trên production.
  - Bổ sung cơ chế khóa tiến trình `OSFileLock` cho `LeaseManager` trong `safe_multi_agent_writes.py` nhằm loại bỏ rủi ro tranh chấp ghi file đĩa đồng thời trên Windows.
  - Bổ sung cơ chế thử lại (atomic replace retry loop) tối đa 5 lần cho `write_json_atomic` tăng cường khả năng phục hồi lỗi khóa tệp Windows.
  - Dọn dẹp triệt để các tiến trình mồ côi (zombie python tasks) giúp tái tạo môi trường làm việc sạch.
  - Khắc phục 18 bài kiểm thử bị lỗi liên quan đến đường dẫn import chéo và mock liveness PID sai lệch.

## [6.13.1] - 2026-07-13

### Fixed
- **Incident Recovery & Hardening (FEAT-118)**:
  - Khắc phục sự cố tràn tiến trình Python gây OOM bằng cách tối ưu hóa kết nối SQLite trong [db.py](skills/workflow-runtime/scripts/db.py) (tránh truy vấn khóa độc quyền ghi khi đọc dữ liệu).
  - Tích hợp kiểm tra PID kết hợp `process_create_time` qua `psutil` trong [workflow_runtime.py](workflow_runtime.__main__) nhằm loại bỏ lỗi nhận diện sai tiến trình trùng lặp PID trên Windows.
  - Áp dụng cơ chế nhóm Windows Job Object để tự động dọn dẹp các tiến trình con khi tiến trình cha daemon bị kết thúc.
  - Tự động bỏ qua (bypass) các cổng phê duyệt trung gian (`blueprint_approval`) khi kích hoạt chế độ tự động `autonomous_delivery`, ngoại trừ cổng kiểm soát phát hành (`release_approval`).
  - Hoàn thiện lập lịch thông minh Adaptive Team Planner và giới hạn tài nguyên tính toán cho `RuntimeScheduler`.

## [6.13.0] - 2026-07-12

### Added
- **Autonomous Delivery Mode (FEAT-116)**:
  - Triển khai cờ khởi chạy CLI `--autonomous` cho phép tự động bypass các cổng phê duyệt thủ công trung gian đối với các hành động thông thường (normal writes/compiles/tests).
  - Tích hợp tính năng tự động ghi nhận thuộc tính `autonomous_delivery` và tính toán động `progress_percentage` trong pha lưu trữ phân tách Pure Split State.
  - Tích hợp nhãn trạng thái `⚡ AUTONOMOUS DELIVERY` động và thanh tiến độ thực thi trực quan trên Visualizer Sidebar.
  - Bổ sung quy tắc theo dõi và thông báo tiến độ kiểm thử chạy ngầm (background tests) mỗi 5% tiến trình vào chính sách kiểm thử [AI_RULES.md](AI_RULES.md).

## [6.12.0] - 2026-07-12

### Added
- **Quality & Quality Governance Upgrade (DDD, Clean Architecture & Code Size Governance)**:
  - Triển khai **Code Size Policy Governance** phân tích AST Python và bracket-balancing Go, tự động cảnh báo hoặc báo lỗi cứng khi kích thước file/class/function vượt ngưỡng quy định.
  - Tích hợp đề xuất SRP Refactoring khuyến cáo cách trích xuất hàm và phân rã tệp tin vi phạm.
  - Triển khai **DDD & Clean Architecture Validator** quét dependency imports tự động cho Go và Python, tính toán điểm số tuân thủ kiến trúc (yêu cầu tối thiểu 95/100).
  - Tích hợp cổng kiểm soát chất lượng kiến trúc và Code Size vào pha Debug & Verification của `validation_runner.py`.
  - Nâng cấp Visualizer Dashboard Webview bổ sung tab **Code Size** thể hiện Neon status (PASSED/FAILED), top 5 vi phạm lớn nhất và các đề xuất SRP refactor trực quan.
  - Tái cấu trúc thành công Golang Wails App tại thư mục `desktop/` chuyển sang kiến trúc DDD chuẩn (`domain`, `application`, `infrastructure`, `delivery`), loại bỏ hoàn toàn các cấu trúc file phẳng cũ.

## [6.11.0] - 2026-07-12

### Added
- **FEAT-112: Resident Orchestrator Service & Dynamic Subagent Runtime**:
  - Triển khai tiến trình ngầm (daemon/service) trú đóng dài hạn luôn luôn hoạt động.
  - Tích hợp tính năng tự động khởi chạy service qua sự kiện khởi tạo workspace.
  - Xếp hàng và nhận chỉ thị phi đồng bộ ngoài luồng Command Inbox phản hồi < 100ms.
  - Phân tích đồ thị DAG tác vụ để sinh động và thu hồi Subagents nhàn rỗi (ephemeral workers).
  - Tích hợp WebSocket trực tiếp vào Visualizer Dashboard để cập nhật trạng thái động của daemon.

## [6.10.0] - 2026-07-12

### Added
- **FEAT-111: Hierarchical Multi-Agent Runtime Platform Foundation**:
  - Triển khai bộ điều phối phân cấp đa tác nhân chạy nền phi block với hàng đợi Command Inbox.
  - Hỗ trợ lập lịch song song thực sự (Real Parallel Scheduler) tối đa 6 tác vụ chạy đồng thời.
  - Triển khai cơ chế cách ly tiến trình (Worker Process Isolation) cùng dấu hiệu sống Heartbeats.
  - Quản lý vòng đời uỷ quyền thời gian thực (`authorization.json` tự động hết hạn).
  - Tích hợp sâu vào bảng quản trị giao diện Visualizer và loại bỏ hoàn toàn `.session.json` cũ.

## [6.9.0] - 2026-07-12

### Added
- **AIWF OS v2 Core Upgrade**:
  - Triển khai động cơ thực thi liên tục và 4 chế độ chạy (Step, Sprint, Program, Objective).
  - Tích hợp hàng đợi thực thi bền vững và phục hồi điểm kiểm soát SQLite.
  - Tích hợp lớp giám sát tự trị và tự chữa lành (Self-Healing) cho AIWF OS v2.
  - Thiết kế và phân rã lộ trình đám mây AIWF Cloud (FEAT-201 đến FEAT-210) cùng báo cáo đánh giá chiến lược, khung quản trị và kiến trúc North Star cho 5 chương trình Cloud chính.

## [6.8.0] - 2026-07-12

### Added
- **Visual Intelligence Runtime (VIR) Integration & Relocation**:
  - Di chuyển mã nguồn và tệp tests của VIR Runtime vào mô hình Skill đóng gói (Publishable Skill Package) tại `skills/vir-runtime/`.
  - Tạo tệp entry-point chính thức `skills/vir-runtime/scripts/vir.py` hỗ trợ chạy CLI đa nền tảng và phân giải import tương đối an toàn.
  - Tích hợp điều phối pha VIR Visual QA vào workflow orchestrator trung tâm `skills/software-development-workflow/SKILL.md`.
  - Đăng ký và đồng bộ các Skill mới (`vir-runtime`, `vir-investigate`, `vir-verify`, `vir-memory-update`) trong manifest và catalogs (`MANIFEST.json`, `SKILLS.md`).
  - Triển khai quy trình tự động hóa xuất bản thông qua lệnh **`make publish-github`** để đồng bộ hóa mã nguồn sang GitLab/GitHub và cập nhật liên kết submodule **`public_export`** của dự án cha.

## [6.7.0] - 2026-07-11

### Added
- **FEAT-054: Build update-source and Interactive Project Initialization**:
  - Triển khai lệnh CLI `aiwf update-source` hỗ trợ kiểm tra và cập nhật an toàn mã nguồn framework trung tâm qua Git fast-forward-only.
  - Triển khai lệnh CLI `aiwf init` hỗ trợ bộ câu hỏi tương tác wizard 18 phần, sinh tệp tin cấu hình dự án `.agents/project.config.json` và tệp profile `.agents/PROJECT_PROFILE.md` tự động.
  - Tích hợp bộ khuyến nghị stack thông minh RecommendationEngine và ScaffoldPlanner thực thi tạo cấu trúc thư mục chuẩn.

## [6.6.2] - 2026-07-11

### Fixed
- **FIX-026: Add bootstrap, init, and test Commands to AIWF CLI Wrapper**:
  - Bổ sung các lệnh con `bootstrap`, `init`, và `test` vào PowerShell wrapper CLI toàn cục (`bootstrap.ps1`).
  - Hỗ trợ gọi trực tiếp trình cài đặt môi trường (`aiwf bootstrap`), khởi tạo phiên làm việc mới (`aiwf init`) và chạy bộ kiểm thử/xác thực tĩnh (`aiwf test [args...]`).
  - Cập nhật tài liệu hướng dẫn nhanh Show-Help trong wrapper CLI.

## [6.6.1] - 2026-07-11

### Added
- **QUICK-029: Permanent Testing Architecture Rules & CI Validation**:
  - Ban hành Quy định cấu trúc thư mục kiểm thử vĩnh viễn (`smoke/`, `unit/`, `integration/`, `concurrency/`).
  - Di chuyển toàn bộ 35 tệp tin test và gắn thẻ marker pytest tương ứng khớp 100% với tên thư mục chứa.
  - Bổ sung lệnh CLI `aiwf test validate` để tự động kiểm tra tĩnh cấu trúc thư mục, marker pytest, tính đầy đủ của impact mapping, trùng lặp file và obsolete mappings.
  - Định cấu hình `pythonpath` trong `pytest.ini` giải quyết triệt để vấn đề phân giải import đường dẫn tương đối trong các thư mục kiểm thử lồng nhau.

## [6.6.0] - 2026-07-11

### Added
- **FEAT-050: Lightweight Runtime Initialization and Runtime Dependency Resolver**:
  - Tái cấu trúc kỹ năng `initialize-workflow` thành bộ khởi tạo siêu nhẹ (<800ms, loại bỏ hoàn toàn các lệnh kiểm tra công cụ CLI, quét workspace, nạp full bộ nhớ và kết nối RAG).
  - Bổ sung bộ giải quyết phụ thuộc thời gian chạy **Runtime Dependency Resolver** (`dependency_resolver.py`) hỗ trợ quét và xác thực khai báo `runtime_requirements` của các kỹ năng.
  - Bổ sung bộ quản lý đồ thị công cụ và máy trạng thái công việc **Task Dependency Graph & State Machine** (`task_orchestrator.py`) kiểm soát chặt chẽ 19 trạng thái công việc và ngăn chặn các phím tắt chuyển trạng thái bất hợp lệ.
  - Cấu hình cổng kiểm soát hoàn thành pha **Phase Completion Gate** yêu cầu 100% độ bao phủ công việc và các tiêu chí chất lượng nghiêm ngặt trước khi chuyển pha.
  - Bổ sung các lệnh CLI hữu ích `deps inspect/validate/resolve/doctor/fix` và `task graph/state/next` vào `workflow_runtime.py`.
  - Đồng bộ cập nhật khai báo `runtime_requirements` cho toàn bộ 52 kỹ năng trong hệ thống.
  - Biên soạn tài liệu hướng dẫn phát triển tích hợp [Runtime Dependency Resolver Guide](docs/guides/runtime-dependency-resolver.md).

## [6.5.2] - 2026-07-09

### Added
- **QUICK-028: Add Provider and Sync Commands to Wrapper CLI**:
  - Bổ sung lệnh con `provider` và `sync` trực tiếp vào wrapper `aiwf` (Bash & PowerShell) để gọi nhanh các tác vụ quản lý tri thức.
  - Hỗ trợ lệnh viết tắt tiện lợi `aiwf sync <provider_name>` để đồng bộ hóa nhanh sang Obsidian.

## [6.5.1] - 2026-07-09

### Added
- **QUICK-028: Upgrade Quick Feature & Quick Fix into Blueprint-Ready Mini Plans**:
  - Làm giàu các mẫu tài liệu đặc tả ở Phase 1 của `quick-feature` và `quick-fix` thành các bản **Mini Plan** hoàn chỉnh chứa đầy đủ 19 mục thông tin hoạt động, ràng buộc kiến trúc, kiểm tra phụ thuộc và ma trận xử lý lỗi.
- **FIX-024: Missing Obsidian Folder Mappings**:
  - Bổ sung cấu hình mặc định trong `provider_manager.py` và `.agents/memory.config.json` để đồng bộ hóa đầy đủ 11 thư mục tri thức dưới `docs/` sang Obsidian.
  - Phân loại tri thức chính xác theo bản chất: QUICK specs ➔ `Brainstorming`, FIX specs ➔ `Plans`, các tài liệu chuyên biệt khác ➔ `Prompts`, `Verification`, `Debug`, `Archive`.

## [6.5.0] - 2026-07-09

### Added
- **QUICK-023: Ensure New Skills Always Generate a Complete AIWF Skill Skeleton**:
  - Thêm chính sách bắt buộc `Mandatory Skill Skeleton Policy` vào tệp quy tắc trung tâm `AI_RULES.md`.
  - Cấu hình kỹ năng Thiết kế (`skills/plan-to-blueprint/SKILL.md`) để từ chối và báo lỗi xác thực nếu bản thiết kế tạo kỹ năng mới mà không định nghĩa đầy đủ tệp `SKILL.md`.

## [6.4.2] - 2026-07-09

### Added
- **QUICK-022: Upgrade plan-to-blueprint Skill to v3.2 (Complete Implementation Contract)**:
  - Đồng bộ hóa 100% dữ liệu thiết kế giữa hai định dạng Markdown và JSON (`FEAT-XXX_blueprint.json`).
  - Bổ sung cấu trúc gói thực thi lập trình `implementation_packages` vào tệp JSON thiết kế để hỗ trợ hạ nguồn lập trình tự động hóa.
  - Mở rộng chi tiết thiết kế lớp (Class Contracts), thiết kế lưu trữ (Storage Design), CLI và tích hợp.

## [6.4.1] - 2026-07-09

### Added
- **QUICK-021: Upgrade plan-to-blueprint Skill into an Implementation Contract Generator**:
  - Nâng cấp kỹ năng Thiết kế (`skills/plan-to-blueprint/SKILL.md`) hỗ trợ tạo Technical Design Blueprint v3.2 với 13 phần phân tích mới.
  - Hỗ trợ xuất đồng bộ tệp thiết kế có cấu trúc JSON (`FEAT-XXX_blueprint.json`) giúp hạ nguồn triển khai nhanh chóng.
  - Cấu hình `skills/blueprint-to-implementation/SKILL.md` để ưu tiên đọc tệp JSON thiết kế trước khi bắt đầu lập trình.

## [6.4.0] - 2026-07-09

### Added
- **QUICK-020: Upgrade quick-feature Skill Based on QUICK-018 Review**:
  - Nâng cấp kỹ năng Phát triển nhanh (`skills/quick-feature/SKILL.md`) hỗ trợ tạo đặc tả Mini Spec v3.2 với 7 phần bắt buộc nâng cao chất lượng.
  - Phân định scope rõ ràng (In/Out/Not Modified/Future Work) và cấm tuyệt đối sinh đường dẫn tuyệt đối trong tài liệu spec.

## [6.3.9] - 2026-07-09

### Added
- **QUICK-019: Upgrade brainstorming-to-plan Skill into an Execution Planning Engine**:
  - Nâng cấp kỹ năng Lập kế hoạch (`skills/brainstorming-to-plan/SKILL.md`) hỗ trợ tạo Execution Plan v3.2 với 11 phần phân tích mới.
  - Hỗ trợ xuất đồng bộ tệp kế hoạch có cấu trúc JSON (`FEAT-XXX_plan.json`) giúp các pha hạ nguồn nạp dữ liệu nhanh chóng.
  - Cấu hình `skills/plan-to-blueprint/SKILL.md` để ưu tiên đọc tệp JSON kế hoạch trước.
  - Sửa lỗi đường dẫn tương đối trong tất cả các tệp kỹ năng.

## [6.3.8] - 2026-07-09

### Added
- **FEAT-046: Upgrade Brainstorming Skill to v3 (Master Requirement Discovery)**:
  - Nâng cấp mẫu tài liệu Động não (`skills/brainstorming/SKILL.md`) hỗ trợ 14 phần phân tích tri thức mới phục vụ hạ nguồn.
  - Tinh giản tệp hướng dẫn `skills/brainstorming-to-plan/SKILL.md` và `skills/plan-to-blueprint/SKILL.md` để Planner và Architect không phải phân tích lại.

## [6.3.7] - 2026-07-09

### Fixed
- **Gemini Cache Discount Cost Calculation**: Fixed token accounting in `parse_transcript` and `sync_request_history` of `context.py` to calculate accurate accumulated Gemini cost by applying a 75% prompt caching hit discount.
- **Memory & RAG Telemetry Sync**: Updated `get_workflow_summary` in `db.py` to fetch, aggregate, and return `memory_hit_ratio` and `rag_hit_ratio` to the UI provider.

---

## [6.3.6] - 2026-07-08

### Added
- **FEAT-029: Project/Global Usage Scope Aggregation & Normalization Fix**:
  - Hỗ trợ lọc thống kê sử dụng token và chi phí API chính xác theo từng mã dự án riêng biệt (`project_id`).
  - Hỗ trợ câu lệnh `usage normalize` để tự động dọn dẹp, chuẩn hóa và sửa đổi các số liệu token rác/khổng lồ của các phiên cũ về mức thực tế.
- **FEAT-030: Config-driven Telemetry & Cost Warning Thresholds**:
  - Nạp động cấu hình các ngưỡng tỷ lệ phần trăm đầy Context và cảnh báo chi phí tích lũy từ tệp cấu hình dự án.
- **FEAT-031: Redesigned AIWF Context Status Visualizer UX**:
  - Phân tách giao diện Footer hiển thị thông số sử dụng thành 3 thẻ card riêng biệt: **Context Analytics**, **Accumulated API Usage**, và **Efficiency & Optimization**.
  - Trực quan hóa trạng thái `🟢 Healthy` trung tính, không sử dụng hộp cảnh báo hay biểu tượng khẩn cấp gây hiểu lầm.
  - Căn lề dọc hoàn hảo cho các biểu tượng cảnh báo bên trong Alert Boxes.


## [6.3.5] - 2026-07-08

### Added
- **FEAT-027: Investigate and Fix AIWF Runtime Token Accounting**:
  - Khắc phục các giá trị token không nhất quán và không hợp lý trên bảng điều khiển bằng cách sửa đổi logic phân tích cú pháp transcript.
  - Tách biệt dữ liệu Active Context (chỉ đại diện cho kích thước context hoạt động) và các số liệu tích lũy (Input/Output/Cost/Request).
- **FEAT-028: Pure Split State Management**:
  - Loại bỏ hoàn toàn tệp tin trạng thái lớn `.agents/.session.json` để chuyển hẳn sang sử dụng cơ chế lưu trữ phân tách (Pure Split State) trong thư mục `.agents/state/`.
  - Giảm thiểu I/O đĩa thừa, tránh lỗi tranh chấp ghi khóa tệp và tối ưu hóa tốc độ khởi tạo.

## [6.3.4] - 2026-07-08

### Fixed
- **FIX-018: Standardize generic workflow templates and auto-generate actual configuration files**:
  - Chuyển đổi các tệp mẫu cấu hình `release.config.json` và `workflow.config.json.template` thành dạng tổng quát (`single` project_type).
  - Tích hợp logic tự động sinh tệp cấu hình thực tế cho dự án đích khi chạy lệnh `discover`.
  - Loại bỏ trường dư thừa `feature_prefix` trong tất cả cấu hình mẫu và script runtime.
  - Thêm quy tắc an toàn bảo mật `Absolute Path Prohibition Policy` vào `AI_RULES.md` ngăn chặn rò rỉ username và đường dẫn tuyệt đối khi push Git.

## [6.3.3] - 2026-07-08

### Added
- **FEAT-025: Project-specific Workflow Templates & Release Configuration**:
  - Hỗ trợ cơ chế cấu hình quy trình Git Flow (development_branch, release_branch, feature_prefix, sync_method) tùy biến riêng cho từng dự án thông qua `.agents/workflow.config.json`.
  - Hỗ trợ Release Pipeline tùy biến thông qua custom commands cho từng module bị ảnh hưởng và custom commands global.
  - Tự động hóa các tác vụ Git Flow (merge/rebase) và release pipeline shell commands trong `release_manager.py`.

## [6.3.0] - 2026-07-08

### Added
- **QUICK-015: Upgrade skill-self-verification into a Behavioral Acceptance Testing (BAT) Skill**:
  - Nâng cấp bộ xác thực Skill sang kiểm thử hành vi thực tế (Behavioral Acceptance Testing - BAT).
  - Tích hợp giả lập User Personas đa nhân vật, sinh Simulated Conversation Transcript tương tác với các Cổng kiểm soát (Gates) và Prompts.
  - Tự động so sánh git diff Trước vs Sau (**Before vs After**) cho các Skill được chỉnh sửa.
  - Đo lường đánh giá UX Review, Productivity Impact và Token/API Cost.
  - Xuất báo cáo BAT nghiệm thu đầy đủ 12 chương mục chất lượng cao dưới `docs/verification/`.
- **FIX-017: Fix Orchestrator Routing & Blueprint Enforcement**:
  - Khắc phục lỗi Orchestrator tự ý code bỏ qua blueprint. Tự động dispatch sang `quick-fix`/`quick-feature`/`brainstorming` nếu phát hiện và tuân thủ rule/guide từng Phase.
  - Chặn cứng Phase 6 (Implementation) từ CLI nếu tệp Design Blueprint tương ứng chưa được phê duyệt (`blueprint.approved == True`).

## [6.2.0] - 2026-07-08

### Added
- **QUICK-013: Stricter Blueprint Generation**:
  - Nâng cấp `plan-to-blueprint` Skill để Technical Design Blueprint đóng vai trò là hợp đồng triển khai (Implementation Contract) chặt chẽ.
  - Áp dụng các quy tắc tự kiểm tra nghiêm ngặt: cấm link `file://` và đường dẫn tuyệt đối, yêu cầu tương thích ngược, enum an toàn cho `permission_mode`, xác thực đường dẫn pseudo-code, và mô tả đầy đủ acceptance criteria & extension changes.
- **FIX-016: Fix aiwf Git Repository Detection for Worktrees/Submodules**:
  - Khắc phục sự cố cài đặt, cập nhật, và chẩn đoán framework (`install`, `update`, `doctor`) không hoạt động trên Git worktrees, submodules (nơi `.git` là một tệp văn bản) và khi chạy từ thư mục con lồng nhau.
  - Sử dụng `git rev-parse --is-inside-work-tree` và `git rev-parse --show-toplevel` làm nguồn dữ liệu tin cậy nhất để tự động phát hiện project root và di chuyển vị trí thực thi.

## [6.1.0] - 2026-07-08

### Added
- **FEAT-022: Split Runtime State, Optimize Initialize Workflow, and Update Extension**:
  - Tái cấu trúc cơ chế lưu trữ trạng thái: Tách tệp tin `.session.json` monolit thành 8 file trạng thái con chuyên biệt trong `.agents/state/` (`context.json`, `workflow.json`, v.v.).
  - Triển khai lớp đồng bộ hai chiều (Aggregate & Deconstruct) bảo đảm tương thích ngược với các Agent đời cũ.
  - Tối ưu hóa tốc độ khởi động `initialize-workflow` bằng cơ chế kiểm tra cache vân tay dự án (Project Fingerprint SHA-256), giảm thời gian tải xuống dưới 50ms.
  - Cập nhật VS Code Extension watch thư mục `state/` để ghép ViewModel in-memory và live update giao diện mượt mà không nhấp nháy.
  - Bổ sung 5 lệnh CLI quản trị trạng thái mới: `context`, `rules status`, `state status/recover/validate`.

## [6.0.0] - 2026-07-08

### Added
- **FEAT-021: Convert Deterministic Skills to Script-First Execution**:
  - Tách toàn bộ logic kiểm tra/thẩm định mang tính chất thủ tục (init, resume, project stack discovery, project memory bootstrap/sync/search, env health, test runner, verify checklist, release gates) thành các script Python chạy tập trung.
  * Bổ sung các lệnh CLI JSON-returning mới: `discover`, `classify`, `memory bootstrap/update/search`, `env health`, `validate artifact/blueprint/session`, `debug run`, `verify run`, `release plan/execute`.
  * Viết bộ kiểm thử tự động `test_script_first.py` bao quát toàn bộ 17 kịch bản nghiệp vụ đặc thù.
  * Cập nhật đặc tả phân nhóm Group A (Script-First), Group B (Hybrid), Group C (LLM-driven) trong `SKILLS.md` và `AI_RULES.md`.

## [5.2.1] - 2026-07-07

### Added
- **FIX-014: Orchestrator Scope Correction (Parallel Only During Implementation)**:
  - Giới hạn lựa chọn chạy song song (Parallel execution) chỉ kích hoạt khi bắt đầu pha Triển khai (Implementation) sau khi đã duyệt Blueprint (checkpoint >= 5).
  - Các pha trước đó (discovery, brainstorming, planning, blueprint) và pha release phía sau bắt buộc chạy tuần tự (Sequential).
  - Nâng cấp CLI `workflow_runtime.py` từ chối kích hoạt song song và trả về mã lỗi `1` nếu checkpoint < 5.
  - Bổ sung 3 trường trạng thái mới (`implementation_execution_mode`, `parallel_allowed_phase`, `parallel_allowed`) vào tệp cấu hình và đồng bộ hóa qua nhịp tim hệ thống.
  - Cập nhật tài liệu tương tác `interactive-docs` bổ sung quy trình điều phối Orchestrator, đồng thời sửa lỗi gập vỡ giao diện tab trên mobile bằng bố cục lưới 2x2.

## [5.2.0] - 2026-07-07

### Added
- **FEAT-016: Interactive CLI & Workflow Prompts via IDE Dialogs**:
  - Tích hợp hàm `prompt_select` tại `utils.py` hiển thị thẻ XML tương tác `<interactive_prompt>` giúp Agent nhận diện và mở giao diện bảng đối thoại `ask_question` trên IDE thay vì nhập tay trong CLI.
  - Tự động phát hiện môi trường kiểm thử (bằng `TESTING=1` và `select.select` trên `stdin`) để tránh bị treo trong các tiến trình con unit tests.
  - Thay thế toàn bộ cổng gõ tay tương tác (chọn chế độ phân quyền và cảnh báo unrestricted) trong `workflow_runtime.py` bằng bảng đối thoại trực quan.
  - Bổ sung Section 16 (Interactive CLI Prompts Bridge Policy) và cập nhật Section 1, 14 trong `AI_RULES.md` để Agent bắt buộc sử dụng `ask_question`.

## [5.1.3] - 2026-07-07

### Added
- **QUICK-007: Interactive Docs & Workflow Simulator Website & Extension Tweak**:
  - Xây dựng một trang web tài liệu tĩnh (HTML/CSS/JS) chạy Client-side, tích hợp thông tin của 19 skills và hướng dẫn chi tiết theo 3 quy trình chính (Standard, Quick Feature, Quick Fix).
  - Tích hợp **Interactive Workflow Simulator** mô phỏng chạy CLI và gác duyệt của 3 quy trình.
  - Thiết kế Responsive (hỗ trợ Tablet và Mobile với Menu hamburger và sticky header).
  - Thiết kế thanh cuộn Neon scrollbar giống hệt extension và cố định chiều cao Terminal di động là 400px với tính năng tự động cuộn xuống cuối (scroll to bottom).
  - Thêm 2 nút liên kết kèm biểu tượng chính thức của VS Code ribbon và Puzzle piece dẫn tới 2 extension: **Visualizer (VS Code)** trên Marketplace và **Visualizer (Open VSX)** trên Open VSX Registry.
  - Di chuyển website sang thư mục riêng `interactive-docs/` ngoài thư mục `docs/`.
  - Tích hợp `interactive-docs/` vào quy trình xuất bản `make export` sang `public_export`.
  - Loại trừ thư mục `screenshots` kiểm thử ra khỏi Git thông qua `.gitignore`.
  - **VS Code Extension (v1.0.30)**: Tích hợp nút **Docs** (mở trang tài liệu tĩnh) kèm biểu tượng quyển sách mở vào header webview của extension.


## [5.1.2] - 2026-07-07

### Fixed
- **FIX-012: Auto-Sync Conversation ID on Rollover**:
  - Tự động trích xuất `conversationId` từ biến môi trường `ANTIGRAVITY_SOURCE_METADATA` trong hàm `update_context_health` của `workflow_runtime.py`.
  - Đồng bộ kịp thời và ghi đè trực tiếp `conversation_id` mới vào `.agents/.session.json` bất cứ khi nào bất kỳ thao tác nào của CLI Runtime được gọi.
  - Khắc phục triệt để lỗi tính toán Fallback Token Estimation bị giữ ở mức 85% của thread cũ khi chuyển sang hội thoại mới.
  - Khôi phục subcommand `compact` và `permission` trong `workflow_runtime.py` bị mất do thao tác checkout.

### Added
- **Global Rule 6: Mandatory SDLC Skill Binding**:
  - Bổ sung quy tắc bắt buộc mọi hoạt động thay đổi mã nguồn phải diễn ra trong phạm vi của một SDLC Skill tương ứng (`quick-fix`, `quick-feature`), cấm tự ý sửa đổi file trực tiếp trong `AI_RULES.md`.

## [5.1.1] - 2026-07-07

### Fixed
- **FIX-011: Prevent Session Drift on Memory Sync**:
  - Modified session helpers in `runtime/scripts/project_memory/common.py` to check the active skill before modifying workflow routing fields.
  - Prevents the visualizer from jumping back and forth to step 2 when memory updates are executed ngầm as side effects (background/unrelated steps).
  - Preserves RAG and memory health syncing in the session metadata on completion.

## [5.1.0] - 2026-07-07

### Added
- **Unrestricted Mode (AI_RULES.md Section 15)**:
  - Added a 3rd permission level "Unrestricted Mode" which bypasses all approval gates.
  - Implemented a Two-Factor Confirmation Gate requiring CLI input `CONFIRM_UNRESTRICTED` to unlock.
- **Session Durability (Recovery & Backup Strategy)**:
  - Added automatic backup `.session.json.bak` before saving.
  - Implemented Self-Healing in `load_session()` to automatically restore from `.bak` if the main session file is corrupted, empty, or fails JSON parsing.
- **CLI Permission Inspection Subcommand**:
  - Added `permission` command to `workflow_runtime.py` to print a structured layout mapping common actions to status (`ALLOWED` or `REQUIRED_APPROVAL`).

### Changed
- **Unit Tests Isolation**:
  - Isolated test backups to `.testbackup` to avoid conflict with runtime `.bak` file recovery.

## [5.0.0] - 2026-07-07

### Added
- **Workspace Permission Modes Policy (AI_RULES.md Section 15)**:
  - Enforced Workspace Permission Modes: Sandbox Mode (default, prompts for every change) and Full Access Mode (bypasses confirmation gates for normal, non-destructive workflow tasks).
- **CLI Permission Helpers & Arguments**:
  - Added `get_permission_mode()` and `requires_approval(action_type)` to `workflow_runtime.py`.
  - Added `--permission` parameter to `init` command.
- **Permission Session Schema**:
  - Integrated `permission_mode` fields in session schema.

### Changed
- **Workflow Skills Integration**:
  - Updated all core workflow skills (`initialize-workflow`, `software-development-workflow`, `quick-fix`, `quick-feature`, `brainstorming`, `blueprint-to-implementation`) to query `requires_approval()` and adapt prompts dynamically.

## [4.0.0] - 2026-07-06

### Added
- **Skill Suggestion Gate Policy (AI_RULES.md Section 14)**:
  - Enforced a pre-workflow Suggestion Gate for all unclassified natural language user requests. The AI must stop, classify the request using a Classification Matrix, suggest a workflow Skill or present options, and wait for confirmation.
- **CLI Suggestion Subcommand**:
  - Integrated `suggest` subcommand in `workflow_runtime.py` to register and verify raw user requests, options, and status.

### Changed
- **SDLC Orchestrator Suggestion Routing**:
  - Upgraded `software-development-workflow` to handle unclassified requests and enforce suggestion gate logic.
- **Workflow Skills Enforcement**:
  - Updated all core workflow skills (`quick-fix`, `quick-feature`, `brainstorming`, `blueprint-to-implementation`, `implementation-to-release`, `resume-workflow`) to reference the Suggestion Gate Policy.

## [3.0.0] - 2026-07-06

### Added
- **Blueprint Mandatory Execution Policy (AI_RULES.md Section 13)**:
  - Enforced Design Blueprint as the sole legal input for code generation or modification. Implementation from specifications, brainstorms, planning documents, or conversation text is strictly forbidden.
- **Explicit Release Policy (AI_RULES.md Section 9)**:
  - Enforced manual user-driven releases. The AI Agent is strictly prohibited from running version updates, committing, tagging, or pushing automatically unless explicitly requested by the user.

### Changed
- **Three-Stage Quick-Fix Workflow**:
  - Redesigned `quick-fix` skill to separate work into three strictly gated phases: Spec Generation -> Design Blueprint -> Code Implementation.
- **Three-Stage Quick-Feature Workflow**:
  - Redesigned `quick-feature` skill identically to follow a three-stage gated flow.
- **SDLC Orchestrator Upgrade**:
  - Upgraded `software-development-workflow` to track blueprint approval status (`blueprint.approved` inside session) and enforce manual release stops.
- **CLI Runtime Upgrades**:
  - Upgraded CLI parser in `workflow_runtime.py` to add `blueprint` subcommand for registering and approving design blueprints on session files.

## [2.13.2] - 2026-07-06

### Fixed
- **Visualizer Extension Dashboard Version Display (v1.0.28)**:
  - Fixed a dashboard display bug where the session version fell back to `v0.0.0` by forcing the visualizer backend to read the version directly from `.agents/MANIFEST.json` instead of relying solely on the session file.

## [2.13.1] - 2026-07-06

### Fixed
- **Visualizer Extension & CLI Session Sync (v1.0.27)**:
  - Resolved an issue where running `workflow_runtime.py validate` calculated token values in memory but failed to persist the updated session variables back to `.session.json` on disk.
  - Fixed a display inconsistency in the visualizer's fallback logic where the progress bar token count and details (Input/Output/Cache/Thinking) were out of sync.

## [2.13.0] - 2026-07-06

### Added
- **Visualizer Extension (v1.0.27)**:
  - Integrated asynchronous skills update notifications by polling the raw GitHub stable channel.
  - Implemented client-side version skipping features backed by VS Code `globalState` and browser `localStorage`.
  - Added a dismissable close button (`&times;`) to temporarily hide update alerts.
  - Added a glassmorphism Custom HTML Confirm Modal to prevent accidental version skipping.
- **Script-First Project Memory CLI Engine**:
  - Implemented `runtime/scripts/project_memory/` Python package featuring modules for filesystem scanning (`filesystem.py`), git diff parsing (`git_diff.py`), language/framework detection (`scanner.py`), abstract syntax tree parsing (`parser.py`), architecture/database analysis (`analyzer.py`), index builders (`markdown_writer.py`, `json_writer.py`, `sqlite_writer.py`), and RAG search logic (`search.py`).
  - Added centralized CLI controller `cli.py` exposing `bootstrap`, `update` (incremental sync), and `search` subcommands.
  - Registered the new CLI engine as `aiwf memory` command inside the global bootstrappers `bootstrap.sh` and `bootstrap.ps1`.
  - Added automated tests for all memory subcommands under `skills/workflow-runtime/tests/test_project_memory.py`.


### Changed
- **Refactored Prompt-Driven Skills to Script-First**:
  - Reduced `SKILL.md` token footprints by over 95% for `project-memory-bootstrap`, `project-memory-update`, and `project-rag-search` skills.
  - Migrated complex scanning, indexing, chunking, and search logic from prompt instructions into the Python execution layer.

### Fixed
- **Version Detection Fallback**:
  - Resolved an issue where the Workflow Session dashboard displayed version `v0.0.0` inside user projects by extending `get_version_info` in `validator.py` to search for `MANIFEST.json` inside `.agents/` directory and automatically fallback to parsing the nearest Git tag (`git describe --tags`) if no manifest exists.

## [2.12.5] - 2026-07-06



### Fixed
- **Visualizer Extension (v1.0.26)**:
  - Implemented client-side fallback estimations for token categories (`input_tokens`, `output_tokens`, `cache_tokens`, `thinking_tokens`), cost estimation, `provider`, and `model` in the webview to prevent displays of `0` or `N/A` when the session file contains a total token count but is missing breakdown details.
  - Upgraded extension parse validation to trigger active estimation if the loaded session's summary is missing essential properties like `provider` or `input_tokens`.

---

## [2.12.4] - 2026-07-06

### Fixed
- **Token Estimation & Database Overwriting**:
  - Implemented `get_fallback_usage` on Python side to dynamically estimate tokens based on checkpoint when active logs are missing.
  - Added a protection check in database handler `save_usage_to_dbs` to prevent overwriting correct token/cost history metrics with smaller or zero fallback estimates during initialization.
  - Resolved `OperationalError` when initializing databases on a fresh workspace without a pre-existing `.agents` directory.
- **Visualizer Extension (v1.0.25)**:
  - Updated `README.md` to show the correct new JSON structure and include all missing session fields (`logs`, `suggested_next_skill`, etc.).
  - Upgraded the extension's default/fallback values nạp logic so that `workflow_usage_summary`, `project_usage_summary`, and `global_usage_summary` are always initialized correctly from session data.

---

## [2.12.3] - 2026-07-06

### Fixed
- **Workflow Runtime & Token Estimation Path**:
  - Fixed a critical cross-platform compatibility issue where `BRAIN_ROOT` was hardcoded to a Windows directory, causing token estimation and context percentage calculations to fail on macOS and Linux systems.
  - Dynamically resolved the IDE `brain` directory path using `os.path.expanduser` to support macOS, Linux, and Windows seamlessly.
- **Visualizer Extension (v1.0.24)**:
  - Updated the Workflow Usage token count label to show `active_tokens` (current context window size) instead of `total_tokens` (accumulated tokens), resolving the mathematical mismatch with the percentage bar.
  - Eliminated the blank loading state box when token usage is zero at initialization, ensuring the full layout card remains visible with default zero values.

## [2.12.2] - 2026-07-06

### Fixed
- **Installer & SQLite/UI Synchronization**:
  - Fixed a critical installer packaging issue where the `docs/` folder (specifically `release-guide.md`) was missing from the `public_export` directory, causing installation crashes.
  - Corrected the Python CLI runtime executable path in bash (`install.sh`) and PowerShell (`install.ps1`) installers, changing it to use `$INSTALL_TARGET/$SKILL_DIR/workflow-runtime/workflow_runtime.__main__`.
  - Added automatic SQLite initialization sync to `install.sh` and `install.ps1` to populate initial session metrics immediately upon framework setup.
  - Updated `migrate_session_to_db.py` to push calculated project and global usage summaries back into `.session.json` after running SQLite migration, ensuring Visualizer extension displays correct metrics.
  - Adjusted VS Code Visualizer webview CSS (`webview.html` & `webviewHtml.ts`) to change `.step-row` `scroll-margin-top` from `190px` to `250px`, resolving UI overlay issues under the sticky header.
  - Excluded `temp_extract` from visualizer extension `tsconfig.json` to prevent compilation failures.

## [2.12.1] - 2026-07-06

### Fixed
- **Safe & Idempotent AGENTS.md Integration**:
  - Refactored `install.ps1`, `install.sh`, `update.ps1`, and `update.sh` to safely merge rules block inside the project root `AGENTS.md` instead of creating/overwriting `.agents/AGENTS.md`.
  - Added new E2E test suite `test_agents_merge.py` covering all 7 scenarios of the test matrix (fresh install, existing user rules, old block replacement, multiple installs, corrupted block repair, and user customization preservation).

## [2.12.0] - 2026-07-06

### Added
- **Script-First Runtime Engine**:
  - Refactored the token and cost calculation into a fully deterministic Python pipeline.
  - Implemented SQLite database storage local to the project (`.agents/project_runtime.db`) and globally in OS AppData directory (`global_runtime.db`) to track three independent scopes: Workflow, Project, and Global usage.
  - Added new CLI subcommands: `usage sync`, `usage report`, `usage diagnose`, `usage export`.
  - Updated the Visualizer Sidebar webview to show three distinct scope cards, with Workflow context limit comparing current active window tokens instead of accumulated totals.

## [2.11.1] - 2026-07-06

### Added
- **Visualizer Extension Session Usage**:
  - Integrated a new visual "Session Usage" metadata card into the visualizer sidebar extension template (`webview.html`).
  - Added token and cost visualization including total tokens, input/output/cache/thinking counts, context limit, usage percentage, cost USD, provider name, active model, accuracy, and last updated time.
  - Implemented color-changing progress bar indicating token capacity warning states (Green < 60%, Yellow 60%-85%, Red > 85%).
  - Added a toggleable empty state fallback container to gracefully handle missing session metrics.

## [2.11.0] - 2026-07-06

### Added
- **Centralized CLI Runtime Engine**:
  - Implemented a modular, executable Python CLI Runtime Engine under `skills/workflow-runtime/scripts/`.
  - Exposed Runtime CLI API: `init`, `validate`, `start`, `step`, `complete`, `fail`, `heartbeat`.
  - Moved session schema validation, atomic file writing, token estimation, drift check, and heartbeat formatting into the Runtime Engine.
  - Refactored all 26 skills to call this CLI instead of natural language prompt edits, resulting in major token savings and robust execution.
  - Added comprehensive automated unit tests under `skills/workflow-runtime/tests/`.

## [2.10.1] - 2026-07-06

### Optimized
- **Token Usage Optimization**: Refactored all 26 workflow skills to centralize repeated policy descriptions (approval gates, git workflow, memory strategy, RAG retrieval) inside `AI_RULES.md`, reducing prompt sizes by ~3,000 tokens per agent context load while preserving 100% behavior.

## [2.10.0] - 2026-07-06

### Added
- **Dynamic Project-Aware Checkpoints**:
  - Introduced the `project-discovery` skill (`/discover`) to scan codebase structure (configuration files, package managers, frameworks, and databases) and generate `.agents/project-profile.json`.
  - Refactored the orchestrator (`software-development-workflow`) and other SDLC skills to dynamically skip checkpoints (e.g., skip `frontend-visual-debug` for backend-only/CLI projects) according to the project profile.
  - Upgraded the VS Code Visualizer extension to support dynamic project-aware checkpoint rendering.

### Fixed
- **Framework Installer Export Bug**:
  - Fixed a packaging bug in `tools/export.js` that missed copying the `templates`, `agents`, and `runtime` folders to the public export directory, resolving installer failures during `aiwf install`.

---

## [2.9.0] - 2026-07-04

### Added
- **Claude (Anthropic) Support Integration**: Added environment, prompt, and discovery support for Anthropic Claude.
  - Upgraded `skills/environment-bootstrap/SKILL.md` to prompt and configure `ANTHROPIC_API_KEY`.
  - Added key verification diagnostics for Gemini and Anthropic in `doctor.ps1` and `doctor.sh`.
  - Defined XML tagging guidelines in `AI_RULES.md` to wrap boundaries for optimal instruction-following on Claude.
  - Added step-by-step Claude Desktop and Claude Code integration guides in `INSTALL.md`.
  - Upgraded VS Code Extension (`extensions/visualizer`) to version `1.0.10` with custom installation instructions in its README, compiled and packaged to `.vsix` packages.

---

## [2.8.3] - 2026-07-04

### Added
- **Visualizer Extension Webview Separation & Branding**: Upgraded the VS Code Extension (`extensions/visualizer`) to version `1.0.5` to separate inline webview HTML/CSS/JS code into resources file, implement build-time code-gen, and attach the missing Marketplace branding Icon.
  - Linked official logo image to extension manifest.
  - Staged, compiled and packaged the extension to `extensions/visualizer/ai-workflow-visualizer-1.0.5.vsix`.

---

## [2.8.2] - 2026-07-03

### Added
- **Visualizer Extension Author Profile**: Upgraded the VS Code Extension (`extensions/visualizer`) to version `1.0.4` to display the Framework Author profile card containing name, email, and website at the bottom of the sidebar explorer webview.
  - Staged, compiled and packaged the extension to `extensions/visualizer/ai-workflow-visualizer-1.0.4.vsix`.

---

## [2.8.1] - 2026-07-03

### Added
- **Visualizer Extension Upgrade**: Upgraded the VS Code Extension (`extensions/visualizer`) to version `1.0.3` to render checkpoint execution status badges:
  - Rendered pulsing orange `"Running"` badge when checkpoint is `"in_progress"`.
  - Rendered red `"Failed"` badge when checkpoint is `"failed"`.
  - Rendered green `"Complete"` badge when checkpoint is `"completed"`.
  - Staged, compiled and packaged the extension to `extensions/visualizer/ai-workflow-visualizer-1.0.3.vsix`.

---

## [2.8.0] - 2026-07-03

### Added
- **Checkpoint Status Tracking**: Introduced checkpoint execution status (`status: "in_progress" | "completed" | "failed"`) to the session state `.session.json` to allow the Visualizer UI Extension to accurately reflect current running and completed steps.
  - Updated `skills/workflow-runtime/SKILL.md` schema to include the `"status"` field and define update rules.
  - Integrated status checks into `skills/resume-workflow/SKILL.md` and `skills/software-development-workflow/SKILL.md` to recommend retrying/running the exact interrupted skill when a checkpoint has status `"in_progress"` or `"failed"`.
  - Added status update instructions to all checkpoint-changing skills (`brainstorming`, `brainstorming-to-plan`, `plan-to-blueprint`, `blueprint-to-implementation`, `implementation-to-release`, `quick-fix`, `quick-feature`, `project-memory-bootstrap`, `project-memory-update`).

---

## [2.7.0] - 2026-07-03

### Added
- **Standardized Author Metadata**: Integrated professional author metadata across the framework.
  - Added structured author details (Maintainer, email, website), license (MIT), repository URL, creation date (`created_at: 2026-07-03`), and last update (`updated_at: 2026-07-03`) to the frontmatter of all 22 `SKILL.md` files.
  - Declared the `"author"` block at the root level of `MANIFEST.json` as the single source of truth, and bumped framework version to `2.7.0`.
  - Added an **Author** bio section to the end of `README.md`.
  - Enforced a strict no-signature constraint in Section 7 of `AI_RULES.md` to prevent agents from appending personal signatures to generated engineering plans, blueprints, or implementations.

---

## [2.6.0] - 2026-07-03

### Added
- **Command-Based Architecture**: Redesigned metadata system to support concise command interactions (`/command` style) instead of verbose skill folder name invocations, while preserving folder paths and skill names for 100% backward compatibility.
  - Added `command`, `aliases`, `category`, and `tags` to the frontmatter of all 22 `SKILL.md` files.
  - Re-structured `MANIFEST.json` list of skills from a string array to an array of objects detailing command properties, and added a `"categories"` configuration grouping the skills.
  - Updated all user-facing documentation (`USAGE.md`, `README.md`, `SKILLS.md`) to use short command invocation examples (e.g. `/workflow`, `/plan`, `/blueprint`, `/implement`).
  - Replaced legacy commands inside skill instruction files (e.g. `/plan-to-blueprint` -> `/blueprint`).

---

## [2.5.0] - 2026-07-03

### Changed
- **Workflow Phase Separation & Project Planning Refactor**: Refactored the Planning phase into Project Planning, separating project scope and technical details.
  - Slashed code implementation details, folder layout, databases, APIs, classes, SQL, and pseudo-code from the Planning phase (`planning-prompt-to-plan` and `brainstorming-to-plan`).
  - Strengthened `plan-to-blueprint` to read both brainstorming and plan files, consolidating all technical design specifications (database schemas, public APIs, sequence diagrams, migration/rollback strategy, folder structure) into a single technical design document.
  - Added "Workflow Phase Separation Policy" as Section 10 to `AI_RULES.md` and updated `AGENTS.md` to define these boundaries.
  - Updated `README.md`, `SKILLS.md`, and `INSTALL.md` to document the new boundaries.

---

## [2.4.6] - 2026-07-03

### Fixed
- **SDLC Checkpoint Alignment**: Fixed target checkpoint transitions in `brainstorming` and `brainstorming-to-plan` skills to write Checkpoint `3` (Architecture Analysis Complete) to `.session.json` upon successful execution (fixing legacy specs that erroneously set it to 1 or 2).

---

## [2.4.5] - 2026-07-03

### Changed
- **Active Runtime Context Tracking**: Mandated executing agents inside `initialize-workflow` and `workflow-runtime` skills to dynamically calculate and save active conversation token usage (calculated from local transcript JSONL logs) to the `"context_usage"` field in `.agents/.session.json` during state updates.

---

## [2.4.4] - 2026-07-03

### Added
- **Default Session Initialization**: Configured installation (`install.sh` / `install.ps1`) and update (`update.sh` / `update.ps1`) scripts to automatically create or upgrade `.agents/.session.json` to the new nested format with elegant initial values to prevent Webview loading issues on empty workspaces.

---

## [2.4.3] - 2026-07-03

### Changed
- **Unified Session State Schema**: Aligned the `.agents/.session.json` schema inside `workflow-runtime` skill with the rich, nested format expected by the VS Code UI Visualizer Extension (including `git`, `work_item`, `version`, `memory`, `rag`, and `context_usage` objects).

---

## [2.4.2] - 2026-07-03

### Changed
- **Strict Relative Path Guards**: Strengthened behavioral rules in `initialize-workflow` and `workflow-runtime` skills to explicitly force runtime agents to save workspace directory paths as `"."` under `.agents/.session.json` to eliminate absolute path outputs completely.

---

## [2.4.1] - 2026-07-03

### Changed
- **Relative Path Optimization**: Configured workspace session state and initialization scripts to report project paths using relative representations (e.g. `.`) rather than absolute paths to prevent local file path leakage.

---

## [2.4.0] - 2026-07-03

### Added
- **Configuration-Driven Releases (`release.config.json`)**: Refactored the release subsystem to read layout metadata from a centralized project configuration. Supports single projects, multi-module (backend/frontend), mobile, desktop, and monorepos.
- **Affected Module Detection**: Added Git diff scanning to identify modified modules and bump versions/changelogs only for affected components.
- **Shared Module Detection**: Added dependency propagation so that modifications to common folders (like `shared/`, `common/`, `libs/`) prompt the user to decide on dependent module updates.
- **Release Guide Document (`release-guide.md`)**: Created detailed documentation explaining release modes, schemas, and safety gates.
- **Auto-Detection Fallback**: Implemented automatic language/framework detection to suggest configuration structures to the user if `release.config.json` is missing.

---

## [2.3.0] - 2026-07-03

### Added
- **Multi-Agent Role Contracts (`agents/`)**: Added role specifications, artifact ownership rules, and execution constraints for `planner`, `architect`, `coder`, `reviewer`, and `release-manager` agents.
- **Handoff Runtime Schemas & State Files (`runtime/`)**: Created JSON schema specifications and tracking files for handoffs (`handoffs.json`), checkpoints (`checkpoints.json`), and system state (`state.schema.json`) to track role transitions and prevent illegal workspace alterations.
- **Script Support & Installers**: Updated `install.*`, `update.*`, and `uninstall.*` utility scripts to support deploying, upgrading, and removing the new multi-agent `agents/` and `runtime/` directories.

---

## [2.2.0] - 2026-07-03

### Added
- **Workflow Runtime Controller (`workflow-runtime`)**: Introduced a new core Skill that acts as the runtime controller for execution state management, session handling (`.agents/.session.json`), validation checkpoints, and resume-workflow recovery capabilities.
- **Unified Checkpoints and Heartbeats**: Added checkpoint transitions (1 to 7) and plain text heartbeat logging to all SDLC Feature and Fast-track/Quick skills to detect context drift (unexpected branch/work item/version changes) and ensure resumable, robust execution.

---

## [2.1.0] - 2026-07-03

### Added
- **Workflow Initialization Skill (`initialize-workflow`)**: Introduced a new core Skill acting as the mandatory entry point of the entire AI Engineering Workflow. It aggregates workspace validation, policy loading, project memory status, Git checking, active work item discovery, version detection, and tool inspection into a single runtime context.
- **Reference-Driven Initialization Check**: Updated all 12 core Skills to assume `initialize-workflow` has executed and to verify context before running, eliminating redundant environment and configuration parsing checks in individual Skills.

---

## [2.0.1] - 2026-07-03

### Changed
- **Plain Text Orchestrator Report**: Refactored the `software-development-workflow` output layout from Markdown tables to a clean, structured plain text block format to align with other Skill Completion Contracts and prevent UI line-wrap issues.

---

## [2.0.0] - 2026-07-03

### Added
- **Centralized Policy Architecture (`AI_RULES.md`)**: Created a centralized global policies file in the repository root as the single source of truth for all shared behaviors, constraints, and SDLC gates.
- **Reference-Driven Skills**: Refactored all core Skills (`software-development-workflow`, `brainstorming`, `brainstorming-to-plan`, `plan-to-blueprint`, `blueprint-to-implementation`, `quick-fix`, `quick-feature`, `implementation-to-release`, `project-memory-bootstrap`, `project-memory-update`, `project-rag-search`, `environment-bootstrap`, `environment-health`) to reference `AI_RULES.md` instead of duplicating rules, satisfying DRY principles and enabling policy-driven architecture.

---

## [1.9.1] - 2026-07-03

### Changed
- **Unicode Box Art Migration**: Replaced Unicode box art boundary boxes with native Markdown tables and plain text headers in all skill definitions (`brainstorming`, `quick-fix`, `quick-feature`, `software-development-workflow`, `environment-health`, `environment-bootstrap`) to guarantee stable font rendering across all IDEs and chat clients while preserving the behavioral anchor constraints.

---

## [1.9.0] - 2026-07-03

### Changed
- **Unified Global Approval Gate Policy**: Implemented strict approval gates before any state-changing action in the workspace (modifying source code, creating/deleting files, branch checkouts, merging, version bumps, commits, tags, pushing). Agents must display changes, list affected files, current branch, and stop to await `Y`/`Yes`/`Proceed`/`Continue`.
- **Pre-Implementation Git Gate**: Refactored `blueprint-to-implementation`, `quick-fix` (Phase 2), and `quick-feature` (Phase 2) to display the active branch and status, prompt the user with branch options (continue on branch, create new branch with suggested names `feature/FEAT-XXX-slug`, `fix/FIX-XXX-slug`, `quick/QUICK-XXX-slug`, or stop), and wait for approval before any coding.
- **Merge Gate & Release Workflow Order**: Refactored `implementation-to-release` to follow the strict sequential release workflow (Build/Test, Detect version, Update version, Update CHANGELOG, Approval, Commit, Create Tag `vX.Y.Z`, Push Branch, Push Tag). If not on main/master, the agent must explicitly ask for merge permission. Skipped Git steps automatically for Non-Git projects.
- **Workflow Orchestration Reminders**: Upgraded `software-development-workflow` to remind executing agents about branch and merge gates during Implementation and Release cases.

---

## [1.8.0] - 2026-07-03

### Changed
- **New Documentation Folders Alignment**: Refactored `quick-fix` and `quick-feature` Skills to conform to the new project directory architecture:
  - **`quick-fix`**: Generates Fix files under `docs/issues/FIX-XXX_issue_name.md` instead of `docs/brainstorming/`. Updates Phase 2 execution to read from `docs/issues/`.
  - **`quick-feature`**: Generates Spec files under `docs/quick/QUICK-XXX_feature_name.md` instead of `docs/brainstorming/`. Calculates IDs by scanning `docs/quick/`. Updates Phase 2 execution to read from `docs/quick/`.
- **Project Memory & RAG Upgrades**: Updated `project-memory-bootstrap`, `project-memory-update`, and `project-rag-search` Skills to index and search files inside `docs/issues/` and `docs/quick/` alongside standard SDLC folders.
- Preserved the existing standard workflow.

---

## [1.7.1] - 2026-07-03

### Changed
- **Rename fast-fix to quick-fix**: Renamed the `fast-fix` Skill directory to `skills/quick-fix/` and all internal/external CLI references to `/quick-fix`.
- **Mandatory Mode Active Blocks**: Added `🔒 QUICK-FEATURE MODE ACTIVE` and `🔒 QUICK-FIX MODE ACTIVE` behavioral anchor blocks to establish immediate approval gate boundaries.
- **Mandatory Specification Creation**: Enforced that `docs/brainstorming/FEAT-XXX_feature_name.md` (for `quick-feature`) and `docs/brainstorming/FIX-XXX_issue_name.md` (for `quick-fix`) must be generated during Phase 1. Source code modifications are strictly blocked until the user confirms with `Y` or `Yes`.

---

## [1.7.0] - 2026-07-03

### Added
- **New `quick-feature` Skill**: Introduced a lightweight parallel workflow designed specifically for low-risk, small feature requests (e.g. adding one API endpoint, button, dialog, filter, validation, search field, export function, configuration option). Eligible features bypass standard planning/blueprint overhead. Includes:
  - Scope/Eligibility Matrix (low impact, single module context).
  - Mini Feature Specification template generated at `docs/brainstorming/FEAT-XXX_feature_name.md`.
  - User Approval Gate blocking code modifications until explicit Y/N confirmation.
  - Automatic compilation/test verification and Quick Feature Summary output formatting.
  - Self-Validation checklist for compliance.

### Changed
- **Workflow Orchestration Integration**: Upgraded the `software-development-workflow` Skill to support the parallel **Option 3: Quick-Feature Workflow** track. The orchestrator now automatically classifies incoming tasks and recommends `quick-feature` based on scope, risk, and impact analysis of the `task_description`.
- Registered `quick-feature` in `MANIFEST.json` and cataloged it in `SKILLS.md`.

---

## [1.6.2] - 2026-07-03

### Changed
- **Two-Phase Quick-Fix Workflow**: Refactored the `quick-fix` Skill from an immediate implementation skill into a two-phase workflow with an explicit User Approval Gate:
  - **Phase 1 (Analysis)**: Generates a formal Fix document at `docs/brainstorming/FIX-XXX_issue_name.md` containing metadata, symptoms, root cause, proposed fix, acceptance criteria, and a test plan. Bypasses source code modifications.
  - **User Approval Gate**: Automatically stops after writing the Fix document and prompts the user `Continue? [Y/N]`.
  - **Phase 2 (Implementation)**: Executes minimal source code changes only after receiving explicit Y/yes confirmation from the user.
- Updated `skills/quick-fix/SKILL.md` to establish the `QUICK-FIX MODE ACTIVE` behavioral anchor and wrong behavior check patterns.

---

## [1.6.1] - 2026-07-03

### Fixed
- **CLI Updater macOS/BSD Compatibility**: Fixed a bug where `aiwf update` and `aiwf uninstall` failed to sync or remove skills on macOS because of the non-portable `\s` regex pattern in `sed`. Replaced it with a POSIX-compliant `[[:space:]]` pattern and added a grep filter to exclude target prefixes.
- Deployed identical fixes to both `update.sh` and `uninstall.sh`.

---

## [1.6.0] - 2026-07-03

### Added
- **New `quick-fix` Skill**: Introduced a lightweight parallel workflow designed specifically for low-risk, small bug fixes (e.g. routing errors, null pointers, typos, configuration changes, simple validations). Eligible fixes bypass the full SDLC (No Brainstorming, Planning, Blueprint, or ADR). Includes:
  - Scope/Eligibility Matrix (low impact, single module context).
  - Decision Matrix for auto-classification (Quick-Fix vs Standard Workflow).
  - Automatic compilation checks and test suite verification.
  - Comprehensive Quick-Fix Implementation Summary output formatting.
  - Verification checklist for compliance.

### Changed
- **Workflow Orchestration Integration**: Upgraded the `software-development-workflow` Skill to accept `task_description` input. The orchestrator now automatically classifies incoming tasks and recommends either the `quick-fix` track or the `brainstorming` standard workflow based on scope and risk analysis.
- Registered the `quick-fix` skill in `MANIFEST.json` and cataloged it in `SKILLS.md`.

---

## [1.5.5] - 2026-07-03

### Changed
- **Completion Report Layout Refactoring**: Refactored the `Self-Validation Checklist` and `Completion Report` text blocks in the `brainstorming` skill into beautiful, native Markdown tables and callout alert boxes to prevent ugly line wraps and layout breaks in chat interfaces.

---

## [1.5.4] - 2026-07-03

### Changed
- **Skill Renamed**: `idea-to-planning-prompt` → `brainstorming` — invocation is now `/brainstorming`. Directory renamed to `skills/brainstorming/`.
- **Skill Renamed**: `planning-prompt-to-plan` → `brainstorming-to-plan` — invocation is now `/brainstorming-to-plan`. Directory renamed to `skills/brainstorming-to-plan/`.
- Updated all cross-references in: `MANIFEST.json`, `SKILLS.md`, `README.md`, `INSTALL.md`, `USAGE.md`, `CHANGELOG.md`, and Skills: `software-development-workflow`, `environment-bootstrap`, `environment-health`, `project-rag-search`, `project-memory-update`.

---

## [1.5.3] - 2026-07-03

### Changed
- **Behavior Anchoring: brainstorming**: Root cause identified — previous guardrails were passive warnings that LLM helpfulness bias could override. Fixed with: (1) Mandatory First Output declaration block — AI must print "DISCOVERY MODE ACTIVE" verbatim before any other action, creating a behavioral commitment anchor; (2) Wrong Behavior Detection pattern — explicit checklist of prohibited tool calls with a right vs wrong examples table; (3) Restructured workflow with `[MANDATORY]` step before Step 1; (4) Identical SKILL.md deployed to both framework source and installed project `.agents/`.
- **Repository Metadata Sync**: Bumped framework version to `1.5.3` in `MANIFEST.json`.

---

## [1.5.2] - 2026-07-03

### Changed
- **Production Hardening: brainstorming**: Performed root cause analysis identifying 8 critical/high/medium defects. Refactored the Skill with: (1) Requirement Readiness Score gate (0–100, threshold 85), (2) explicit Y/N user confirmation before document generation, (3) free-text invocation replacing YAML input parsing, (4) corrected Feature labels during decomposition to prevent ID naming conflicts, (5) added Impact Analysis and Risk Analysis to discovery checklist, (6) top-level STOP RULE block preventing auto-transition to downstream phases, (7) expanded 14-section Brainstorming document template per production spec, (8) resolved Capability Boundary vs Completion Report conflict.
- **Repository Metadata Sync**: Bumped framework version to `1.5.2` in `MANIFEST.json`.

---

## [1.5.1] - 2026-07-03

### Changed
- **Strict Requirement Discovery & Feature Decomposition**: Refactored `brainstorming` skill to focus purely on read-only requirement discovery and solution discovery, preventing direct implementation or auto-execution of downstream tasks. Added multi-feature decomposition support.
- **Repository Metadata Sync**: Bumped framework version to `1.5.1` in `MANIFEST.json`.

---

## [1.5.0] - 2026-07-03

### Changed
- **Solution Architect Workshop Upgrade**: Refactored `brainstorming` (now Interactive Solution Discovery) to conduct in-depth architectural design reviews. It maps context, generates 2-3 significantly different solution options, provides trade-offs and complexity ratings, recommends the best choice, and requires user selection (`user_selection`) before writing `docs/brainstorming/` files.
- **Repository Metadata Sync**: Bumped framework version to `1.5.0` in `MANIFEST.json` and synchronized descriptions/inputs in `SKILLS.md`.

---

## [1.4.0] - 2026-07-03

### Added
- **Global Bootstrap Installers**: Added `bootstrap.sh` (macOS/Linux), `bootstrap.ps1` (Windows PowerShell), and `bootstrap.bat` (Windows CMD) to easily configure a global PATH environment variable one-time setup.
- **Global `aiwf` CLI Wrapper**: Added light-weight binary and script command-line wrappers redirecting project-level actions (`install`, `update`, `uninstall`, `doctor`, `version`) back to the framework repository location.
- **Diagnostics and Doctor Scripts**: Added `doctor.sh` and `doctor.ps1` to test the validity of PATH setups and project structure integrity.
- **Version Reporting CLI**: Added `version.sh` and `version.ps1` to display framework core metadata.
- **Windows CLI Complete parity**: Added `update.ps1` and `uninstall.ps1` to provide native CLI powershell support under Windows.

---

## [1.3.0] - 2026-07-03

### Added
- **Framework Installer**: Added `install.sh` (Linux/macOS) and `install.ps1` (Windows/PowerShell Core) to deploy framework files (`AI_RULES.md`, `MANIFEST.json`, `skills/`, `templates/`) into target projects under the `.agents/` folder.
- **Idempotency and Safeguards**: Both installers are fully idempotent, enforce Git repository detection, and prevent overwriting existing custom configs unless explicitly requested.
- **Framework Synchronizer**: Added `update.sh` to compare target versions and update changed skills/files without deleting user-created content.
- **Framework Uninstaller**: Added `uninstall.sh` to perform clean removals of only framework-managed files.
- **Package Manifest**: Updated `MANIFEST.json` to schema `1.3.0` containing repository URLs, supported OS list, and file structure rules.
- **New Folders**: Added placeholder `templates/` and `examples/` folders.

---

## [1.2.0] - 2026-07-03

### Added
- **New Skill: `create-adr`**: Added a dedicated skill under `skills/create-adr/SKILL.md` to generate Architecture Decision Records (ADRs) under `docs/adr/ADR-XXX_*.md`.
- **FEAT-XXX Padded Feature IDs**: Pinned Feature IDs to the unified `FEAT-001`, `FEAT-002`, `FEAT-003` prefix standard.
- **ADR Assessment & Validation Gates**:
  - `plan-to-blueprint` now assesses and recommends ADR requirements (it does not write ADR files).
  - `blueprint-to-implementation` now blocks execution and requests `/create-adr` if a blueprint requires an ADR that does not exist or is not Accepted.
  - `software-development-workflow` now detects pending ADR creation steps.

### Changed
- **Release Tracking**: Refactored `implementation-to-release` to document releases directly into `CHANGELOG.md` instead of creating release files.
- **Clean Documentation Folders**: Kept only the 4 core folders (`docs/brainstorming/`, `docs/plans/`, `docs/designs/`, and `docs/adr/`).
- **All Skills Refactored**: Refactored all 13 existing skills and framework files (README, SKILLS, INSTALL, AGENTS, MANIFEST) to conform to the `FEAT-XXX` format and simplified folders.

### Removed
- Removed legacy folders `docs/releases/` and `docs/archive/`.

---

## [1.1.0] - 2026-07-03

### Added
- **Feature-Centric Documentation Structure**: Added `docs/brainstorming/` (for discovery requirements), `docs/designs/` (for blueprints), `docs/releases/` (for release notes), `docs/adr/` (for Architectural Decision Records), and `docs/archive/` (for deprecated features).
- **Feature ID Traceability**: Introduced unified Feature IDs (e.g. `001`, `002`) to link all artifacts generated during a feature's lifecycle (Discovery -> Plan -> Blueprint -> Release).
- **ID Allocation Algorithm**: Standardized the Feature ID calculation to read only from `docs/brainstorming/`.

### Changed
- **Orchestrator Refactoring**: Updated `software-development-workflow` to track status based on Feature IDs and detect active phase files using the new directory structure.
- **Requirement Discovery Upgrade**: Updated `brainstorming` to write master requirements files under `docs/brainstorming/` formatted as `NNN_<feature_name>.md`. Tweak to include Traceability headers.
- **Planning Prompt to Plan Refactoring**: Updated `brainstorming-to-plan` to read from `docs/brainstorming/` and output plans to `docs/plans/` using Feature IDs.
- **Plan to Blueprint Refactoring**: Updated `plan-to-blueprint` to read plans from `docs/plans/` and output blueprints to `docs/designs/` using Feature IDs.
- **Blueprint Execution Refactoring**: Updated `blueprint-to-implementation` to use technical designs in `docs/designs/`.
- **Git Release Refactoring**: Updated `implementation-to-release` to output release logs to `docs/releases/` using Feature IDs.
- **Repository Metadata Sync**: Updated `MANIFEST.json` (bumped to 1.1.0), `README.md`, `SKILLS.md`, `INSTALL.md`, and `AGENTS.md` to document the new feature-centric layout and rules.

---

## [1.0.0] - 2026-07-03

### Added
- **AI Skill Library**: Initial collection of 13 modular AI Agent skills for managing the Software Development Life Cycle (SDLC).
- **Environment Bootstrapping & Diagnostics**: Added `environment-bootstrap` and `environment-health` skills for automated workspace provisioning and health checks.
- **Project Memory Management**: Added `project-memory-bootstrap` and `project-memory-update` for maintaining a persistent, memory-first workspace metadata layer.
- **RAG & Search capabilities**: Added `project-rag-search` for lightning-fast semantic context retrieval.
- **Planning & Design Engine**: Added `brainstorming-to-plan` and `plan-to-blueprint` to build implementation plans and blueprints from structured requirements.
- **Code implementation**: Added `blueprint-to-implementation` and `implementation-to-release` to generate code and release software in a standardized, controlled fashion.
- **Frontend Design Thinking**: Added `frontend-design` containing core styling guidelines and accessibility rules.
- **OKR Reporting**: Added `okr-report-generator` for processing objective matrices.
- **Workflow Orchestration**: Added `software-development-workflow` to supervise the current phase of development.
- **Package Manifest**: Added `MANIFEST.json` containing machine-readable definitions for the skill library.
- **Documentation**: Added `README.md`, `INSTALL.md`, `SKILLS.md`, `LICENSE`, and this `CHANGELOG.md`.

### Changed
- **Interactive Requirement Discovery**: Refactored the `brainstorming` skill to use a 10-phase interactive workshop model. Calculates a Readiness Score and prompts clarifications when below 85 before producing a planning prompt.
