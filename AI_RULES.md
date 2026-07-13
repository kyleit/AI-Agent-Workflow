# AI Rules & Global Policies

This document is the single source of truth for all shared behaviors, constraints, and policies across all AI Engineering Workflow Skills. All Skills must refer to these policies to prevent duplication and ensure consistency.

---

### 1. Approval Gate Policy

The framework is strictly **approval-driven**, but allows dual execution modes depending on project configurations:

- **Legacy Mode (`workflow_mode=legacy`)**: Every state-changing action (modifying files, commits, tags, branches) requires explicit human confirmation via the `ask_question` tool.
- **Autonomous Mode (`workflow_mode=autonomous`)**: Workflow execution is managed by the **Workflow Supervisor**. State-changing actions during intermediate compilation, test runs, and static linting are automated. The supervisor strictly halts only at the following **3 Strategic Human Approval Gates**:
  1. **Gate 1 — Planning Approval**: Human validates scope and priority.
  2. **Gate 2 — Blueprint Approval**: Human validates technical architecture and contracts.
  3. **Gate 3 — Release Approval**: Human validates production release risk.

*   **No Double Confirmation Policy**: Mọi hành động mà người dùng đã phê duyệt hoặc lựa chọn thông qua giao diện tương tác (như `ask_question` hoặc CLI `prompt select` / `choice`) thì Agent **không được phép hỏi lại hoặc yêu cầu xác nhận lại** trong đoạn chat. Agent phải trực tiếp thực hiện hành động đó ngay sau khi có kết quả lựa chọn của người dùng, ngoại trừ việc chọn chế độ nguy hiểm `unrestricted` thì bắt buộc phải cảnh báo và xác nhận lại.

---

## 1A. Workflow Supervisor Execution Policy

- **Lifecycle Ownership**: The Workflow Supervisor owns the thread execution loop, event routing, and checkpoint resume. Worker agents execute assigned micro-tasks only and cannot spawn other workers or edit workflow states directly.
- **Retry & Fail-safe**: Failed agent compilations automatically trigger retries up to 3 times. If failures persist, the supervisor halts execution, escalates to the Debug Agent, and notifies the user.
- **Suggestion Gate Bypass**: When tasks are triggered autonomously by the Supervisor loop, typical suggestion confirmation alerts are bypassed.

---

## 1B. Permission Model Separation

- **Workflow Permission**: Grants the supervisor authorization to read/write state checkpoints and run local verification test scripts.
- **Release Permission**: Controls packaging, version tagging, and git pushes. Release permission is NEVER automated and strictly requires user confirmation.

---

## 2. Git Workflow Policy

All Git actions must be performed with explicit visibility and approval.

*   **Branch Strategy**:
    *   All work should occur on a dedicated feature/fix/quick branch.
    *   **Feature Branches**: Named `feature/FEAT-XXX-slug` (from `docs/brainstorming/`).
    *   **Fix Branches**: Named `fix/FIX-XXX-slug` (from `docs/issues/`).
    *   **Quick Feature Branches**: Named `quick/QUICK-XXX-slug` (from `docs/quick/`).
*   **Branch Management**:
    *   Never create, switch, check out, or delete branches automatically.
    *   Before coding, run `git branch --show-current` and `git status --short`. Recommend branch names and wait for explicit choice.
*   **Dirty Tree Handling**:
    *   If the working tree is dirty or has uncommitted changes, warn the user.
*   **Commit, Tag, and Push**:
    *   Never perform `git commit`, `git tag`, or `git push` automatically. Always prompt the user for approval first.
    *   Tags must use the format `vX.Y.Z`.
*   **Non-Git Projects**:
    *   If no `.git` directory is detected, skip Git branch/merge/commit/push steps entirely, but still execute build, test, and summary actions.

---

## 3. Memory First Policy

To prevent context overload and improve accuracy, all operations must prioritize the Project Memory over directory scans.

*   **Sequence**:
    1.  **Project Memory**: Consult `<memory_root>/project-summary.md` and module configuration first to identify structure, API patterns, and code boundaries.
    2.  **RAG Search**: Query the RAG vector store or memory indexes for specific files or APIs.
    3.  **Targeted Source Inspection**: Inspect ONLY the files directly relevant to the feature or issue.
    4.  **User Questions**: Ask the user clarifying questions only when memory and targeted inspection do not resolve ambiguity.
*   **Constraints**:
    *   Never scan the entire repository (e.g., wild recursive greps) as a first step.
    *   Always consult Project Memory before asking the user for design guidance.

---

## 4. RAG Policy

Retrieval-Augmented Generation searches must follow a strict priority ordering.

*   **Retrieval Hierarchy**:
    *   **Level 1**: Project Memory (`project-summary.md`, area and module documents under `memory_root`).
    *   **Level 2**: Discovery & Specifications (`docs/brainstorming/`, `docs/issues/`, `docs/quick/`).
    *   **Level 3**: Implementation Plans (`docs/plans/`).
    *   **Level 4**: Technical Blueprints (`docs/designs/`).
    *   **Level 5**: Architectural Decision Records (`docs/adr/`).
    *   **Level 6**: Targeted source code inspection (only for files identified in Levels 1–5).
*   **Chunk Selection & Fallback**:
    *   Rank results by similarity score.
    *   Fallback to adjacent modules or documentation if direct matches are not found.
    *   Never run full repository scans or generic searches if RAG results are available.

---

## 5. Artifact Policy

The documentation architecture enforces strict separation of concerns.

*   **Directory Structure**:
    | Directory | Purpose | Naming Format |
    | :--- | :--- | :--- |
    | `docs/brainstorming/` | Requirements Discovery (Standard Features) | `FEAT-XXX_slug.md` |
    | `docs/plans/` | Implementation Plans | `FEAT-XXX_slug_plan.md` |
    | `docs/designs/` | Technical Blueprints | `FEAT-XXX_slug_blueprint.md` |
    | `docs/issues/` | Bug Fix Specifications (Quick-Fix) | `FIX-XXX_slug.md` |
    | `docs/quick/` | Quick Feature Specifications | `QUICK-XXX_slug.md` |
    | `docs/adr/` | Architectural Decision Records | `ADR-XXX_slug.md` |
    | `docs/debug/` | Debug and Build Diagnostics | `FEAT-XXX_debug.md` |
    | `docs/verification/` | Final Quality Gate Reports | `FEAT-XXX_verify.md` |
    | `docs/releases/` | Release Notes & Change Logs | `RELEASE-XXX_slug.md` |
    | `docs/archive/` | Historical/Retired Artifacts | As needed |
*   **Relative Paths**: All links inside documents must use relative file paths/links. Absolute paths (e.g., `file:///Users/...`) are strictly prohibited in project artifacts.
*   **Metadata**: Every document must begin with YAML frontmatter specifying its `artifact_type`, `feature_id`/`issue_id`, `workflow`, `status`, and tracking links.
*   **Plan Synchronization**: Mọi kế hoạch thực thi (`implementation_plan.md`) được tạo ở tầng IDE để người dùng duyệt, sau khi được phê duyệt (Approved), **bắt buộc phải được Agent sao chép và lưu trữ chính thức vào đúng thư mục tương ứng của dự án** (ví dụ: `docs/plans/FEAT-XXX_slug_plan.md` cho feature, hoặc `docs/issues/` / `docs/quick/` cho fix/quick feature) trước khi tiến hành viết Blueprint hoặc triển khai code. Việc chỉ lưu plan ở thư mục brain tạm thời của IDE mà không đồng bộ vào dự án là vi phạm nghiêm trọng quy trình.

---

## 6. Versioning Policy

We strictly adhere to Semantic Versioning (SemVer).

*   **Format**: `vX.Y.Z` (e.g., `v1.9.0`)
*   **Bumping Rules**:
    *   **Patch (`Z`)**: Bug fixes and backward-compatible security updates.
    *   **Minor (`Y`)**: Backward-compatible new features, specs, or skills.
    *   **Major (`X`)**: Backward-incompatible architectural changes.
*   **Tagging**: Git tags must match the exact version prefix: `vX.Y.Z`.

---

## 7. Documentation Policy

Documentation must remain clean, professional, and easy to parse.

*   **Markdown Standards**:
    *   Use GitHub Flavored Markdown (GFM).
    *   Always use Markdown tables instead of Unicode box art drawings for reports, metrics, and logs to avoid rendering issues.
    *   Include clear, clean headers and checklists.
*   **Metadata**:
    *   Keep YAML blocks simple, clean, and placed at the absolute start of files.
    *   **Strict Constraint**: Never place author information inside prompt bodies. Never append signatures, names, emails, or personal comments to generated planning, blueprint, or implementation documents. Author metadata must belong only to `SKILL.md` frontmatter, `MANIFEST.json`, and `README.md`.
*   **Prompt Boundary XML Tagging (Claude Optimization)**:
    *   To prevent context leakage and confusion when mixing instructions and codebase files, use standard XML tags (e.g. `<instructions>`, `<context>`, `<file_content>`) to encapsulate structural payload boundaries.
    *   Example: Wrap codebase contents in `<file_content filepath="path/to/file">...</file_content>` tags to help Claude distinguish instruction sets from project code.

---

## 8. Testing Policy

Reliability is enforced through automated builds, testing, and runtime validation.

*   **Verification Gates**:
    *   Before any code change is finalized, you must verify compilation, run the test suite, execute the Runtime Validation Pipeline, and perform DDD/Clean Architecture Validation.
    *   **Runtime Validation Requirement**: A feature is considered complete ONLY when all the following runtime validation steps pass successfully:
        1. **Build/Compile**: PASS (Command used: `go build` / `npm run build` / etc.)
        2. **Static Analysis & Lint**: PASS (Command used: `go vet` / `ruff` / etc.)
        3. **Unit Tests**: PASS (Command used: `go test` / `pytest` / etc.)
        4. **Runtime Startup**: PASS (Process starts without immediate crashes, panic, traceback, or exit errors)
        5. **Readiness Detection**: PASS (Process binds to TCP ports or passes HTTP /health /ready HTTP status 200 checks within 15 seconds)
        6. **Runtime Smoke Tests**: PASS (Simulated request/response loop, WebSocket, worker task, or database read/write executes successfully)
        7. **Health Checks**: PASS (Resources and telemetry data reporting are healthy)
        8. **Graceful Shutdown**: PASS (Process terminates cleanly via SIGTERM / exit code = 0, releasing all bound ports and resources without leaks)
        9. **DDD / Clean Architecture Validation**: PASS (Architecture Compliance Score >= 95/100, no Critical Architecture Violations)
    *   **Strict Rule**: Passing unit tests alone MUST NEVER mark a feature as completed.
    *   **Debug & Verify Quality Gates**: All standard feature cycles must pass through `implementation-to-debug` (compilation, linter, tests, and runtime pipeline validation) followed by `debug-to-verify` (blueprint compliance, runtime checks, architecture verification, and Go/No-Go decision).
*   **Failure Behavior**:
    *   If building or compiling fails, or if any test fails, or if runtime validation fails: print stdout/stderr/crash logs.
    *   **STOP** immediately. Set status to `Failed verification` and do not proceed with commit, verify, or release activities. Apply self-healing rules (up to 3 retries) within task scope if applicable.
*   **Background Test Progress Notification**:
    *   Các tiến trình test chạy ngầm (background tests) bắt buộc phải theo dõi tiến trình và cứ mỗi 5% tiến độ hoàn thành phải gửi thông báo cập nhật lên giao diện/hệ thống hoặc logs một lần để Ba dễ dàng theo dõi trực quan.
    *   For any background or asynchronous test execution processes, the agent or test coordinator must track execution progress and output a progress notification or log update exactly every 5% of completed tests.

---

## 9. Explicit Release Policy

Release is NEVER automatic. Completion of implementation, compilation, or verification (passing all tests and quality gates) does NOT grant permission to perform release activities.

The AI must NEVER update version numbers, modify `CHANGELOG.md`, create git commits, tags, merges, pushes, or invoke the `implementation-to-release` skill unless the user has explicitly requested a Release (e.g. via keywords like `/release`, `release`, `create release`, `publish release`, `bump version`, `commit and push`, or `tag this version`). 

If no explicit release request is given by the user, the workflow MUST STOP after the Verification phase, recommend running Release, and wait for input.

*   **Release Sequence**:
    1.  **Verify Status Check**: Check `docs/verification/FEAT-XXX_verify.md` and ensure the verification status is `PASS`. If `FAIL` or missing, STOP the workflow and return to the debug phase.
    2.  **Build & Test**: Compile the codebase and run test suites to ensure 100% pass rate.
    3.  **Detect Version**: Determine the current project version.
    4.  **Update Version**: Update the version strings across project config files (requires approval).
    5.  **Update CHANGELOG**: Write release notes into `CHANGELOG.md` under a new version heading (requires approval).
    6.  **Merge (if applicable)**: Run the Release Gate; if on a non-main branch, ask whether to merge and await approval.
    7.  **Approval Gate**: Explain the final Git commit, tag, and push actions, listing all modified files and branch, then request final release approval.
    8.  **Commit**: Commit version files and `CHANGELOG.md`.
    9.  **Git Tag**: Tag the release commit as `vX.Y.Z`.
    10. **Push Branch**: Push the release branch to the remote repository.
    11. **Push Tag**: Push the tag to the remote repository.

---

## 10. Workflow Phase Separation Policy

To eliminate duplicated information, reduce token usage, and maintain clear separation of concerns, the **Planning** and **Blueprint** phases have distinct, non-overlapping responsibilities:

*   **Project Planning Phase (`docs/plans/`)**:
    *   Focusses entirely on project management, scope, deliverables, and risk mitigation.
    *   **Strict Constraints**: Planning documents must **NEVER** describe code implementations, define classes, define functions or interfaces, define database tables/schemas/SQL, define directory or folder layouts, or generate pseudo-code.
    *   The document must remain understandable by both technical and non-technical stakeholders.
*   **Technical Design Blueprint Phase (`docs/designs/`)**:
    *   Acts as the **single source of technical truth** and the **Implementation Contract** for code changes.
    *   **Strict Quality Constraints**: The Design Blueprint must contain complete technical decisions and specs. It is strictly forbidden to use placeholders (`...`, `etc.`, `TBD`, `to be decided`, `future work`) or generic instructions (`modify related files`, `update existing logic`). Every single affected file, API contract, and algorithm must be explicitly defined and documented.
    *   Owns all technical specifications, including: architecture layouts, sequence and interaction flows (e.g., Mermaid diagrams), class and method signatures (with types), database schemas and migration scripts, folder structures, error handling, security validations, and test strategies.
    *   It references the Project Plan for high-level guidance but does not duplicate its sections.

---

## 11. Shared Validation Engine Policy

All code-generating workflows (`blueprint-to-implementation`, `quick-fix`, `quick-feature`) must run an automated validation pipeline before reporting status.

*   **Command Auto-Detection**:
    *   Automatically scan the workspace for files indicating the project technology stack:
        *   `package.json`: `npm run build`, `npm run lint`, `npm test` or `npm run test`, `npm run typecheck`.
        *   `Makefile`: `make`, `make build`, `make test`.
        *   `go.mod`: `go build ./...`, `go test ./...`.
        *   `pyproject.toml` / `pytest.ini` / `requirements.txt` / `setup.py`: `pytest`, `python -m pytest`, `pylint`, `black --check`.
        *   `Cargo.toml`: `cargo build`, `cargo test`.
        *   `tsconfig.json`: `tsc --noEmit`.
    *   If a category has no config file, mark it as `Not Configured`.
*   **Execution & Self-Fix Loop**:
    1.  Run the validation command.
    2.  If the command fails:
        *   Analyze the log files to locate errors (compilation, linter, tests).
        *   **Scope Protection Rule**: Automatically fix issues ONLY if they are inside the scope of files modified by the current active task. Never refactor or edit unrelated modules/code.
        *   Re-run validation.
        *   Allow up to a maximum of **3 retries**.
    3.  If validation still fails after retries, or if the fix is unsafe/out of scope:
        *   **STOP** immediately. Set status to `FAILED`.
        *   Never claim implementation complete.
        *   Do not perform git commit, tag, or push.
        *   Recommend running `/debug`.
*   **Completion Criteria**:
    *   Status is `PASS` only when:
        *   Build: `PASS` or `Not Configured`
        *   Lint: `PASS` or `Not Configured`
        *   Typecheck: `PASS` or `Not Configured`
        *   Tests: `PASS` or `Not Configured`
        *   Self Review: `PASS` (code is clean, well-logged, free of dead code)

---

## 12. Session State Tracking Policy

To keep the VS Code Visualizer Dashboard synchronized in real-time with minimum I/O overhead, the active workflow state, step logging, and token count must be updated progressively during execution using a split-state engine under `.agents/state/`.

*   **Split State Files**:
    *   State is split into 8 specialized JSON files inside `.agents/state/`: `context.json`, `workflow.json`, `runtime.json`, `approvals.json`, `usage.json`, `agents.json`, `rules.json`, `recovery.json`.
    *   The monolithic `.agents/.session.json` is a derivative compatibility view generated by aggregate sync.
*   **Atomic Writing**:
    *   To prevent file corruption and partial reads, all updates to individual state files inside `.agents/state/` and `.agents/.session.json` MUST be performed atomically.
    *   First, write the complete JSON content to a temporary file: `<filename>.tmp`.
    *   Then, rename/replace the temporary file to the final destination.
*   **Bi-directional Synchronization**:
    *   Any writes to sub-state files automatically rebuild `.session.json` (Aggregate).
    *   Any external writes to `.session.json` are automatically parsed back to sub-state files (Deconstruct) upon CLI invocation to prevent drift.
*   **Progressive Updates**:
    *   Every Skill must update the session state files progressively during execution, specifically at:
        1. **Skill start**: Immediately set status to `in_progress`, current_skill, current_command, and start logging in `runtime.json`.
        2. **Each major step/checkpoint transition**: Update current_step and append log lines to current_logs in `runtime.json`.
        3. **Before running long-running/async commands**: Set step/logs indicating the command is launching.
        4. **After command results**: Append output highlights, status, or errors to the logs.
        5. **On failure**: Set status to `failed` and append error logs.
        6. **On completion**: Set status to `completed` and update suggested next skill/command in `workflow.json` / `runtime.json`.
*   **Preserving & Detecting Conversation ID**:
    *   On every initialize/resume workflow entry, the runtime MUST detect the active conversation ID first. If the active conversation ID differs from `context.json` (or `.agents/.session.json`), update it before calculating context usage. Preserve workflow state, but refresh active context usage using the new transcript.
*   **Required Session Fields**:
    *   Every update must preserve existing fields and update only changed fields.
    *   The following live tracking fields MUST be updated:
        ```json
        {
          "conversation_id": "string (GUID)",
          "checkpoint": "integer (1-10)",
          "status": "in_progress | completed | failed",
          "current_skill": "string",
          "current_command": "string",
          "current_step": "string (current active subtask description)",
          "current_logs": ["array of string log lines showing progressive progress"],
          "suggested_next_skill": "string | null",
          "suggested_next_command": "string | null",
          "updated_at": "string (ISO-8601 Timestamp)"
        }
        ```
*   **Context Usage Token Estimation**:
    *   Locate the main `transcript.jsonl` using the preserved `"conversation_id"` at `<appDataDir>/brain/<conversation_id>/.system_generated/logs/transcript.jsonl`.
    *   Estimate `total_tokens` as `fileSize / 3`.
    *   Update the `"context_usage"` object in `.agents/.session.json`.

---

## 13. Blueprint Mandatory Execution Policy

This is a mandatory global policy. The following rules are absolute and cannot be bypassed:

*   **Rule 1: No Code Modification Without Blueprint**: No Skill may create, delete, or modify source code unless there is a Technical Design Blueprint document. Triaging or implementing changes directly from brainstorming, planning, feature specifications, fix specifications, quick specifications, or user conversation text is strictly forbidden. The Technical Design Blueprint is the ONLY legal input for code generation and modification.
*   **Rule 2: Valid Blueprint Path**: A Blueprint must exist under the `docs/designs/` directory. Valid file paths must match:
    - `docs/designs/FEAT-XXX_slug_blueprint.md`
    - `docs/designs/FIX-XXX_slug_blueprint.md`
    - `docs/designs/QUICK-XXX_slug_blueprint.md`
*   **Rule 3: Explicit User Approval**: The Blueprint must be explicitly approved by the user. Accepted approval keywords are: `Y`, `Yes`, `Proceed`, `Continue` (case-insensitive). The AI must never assume blueprint approval.
*   **Rule 4: Stop Condition**: If no approved Blueprint exists, the AI must IMMEDIATELY STOP, explain the requirement, recommend generating or approving the Blueprint, and wait for input.
*   **Rule 5: Override Priority**: This policy overrides all implementation-capable Skills. No exceptions.
*   **Rule 6: Mandatory SDLC Skill Binding**: Mọi hoạt động chỉnh sửa, thêm, xóa tệp mã nguồn dự án bắt buộc phải được thực hiện trong phạm vi hoạt động của một SDLC Skill tương ứng (như `quick-fix` cho sửa lỗi nhanh, `quick-feature` cho tính năng nhanh). Nghiêm cấm AI Agent tự ý thay đổi file mã nguồn trực tiếp bên ngoài ranh giới của các Skill này, ngay cả khi tài liệu lập kế hoạch `implementation_plan.md` ở tầng IDE đã được duyệt.
*   **Rule 7: Blueprint Quality Gate**: Before a Blueprint is approved, it must be verified that it contains a complete file-by-file analysis table (mapping absolute/relative paths, operations, and responsibilities) and a verifiable implementation checklist. Any Blueprint containing placeholders or generic instructions must be rejected and returned to the draft phase.

---

## 14. Skill Suggestion Gate Policy

When the user provides a natural language request without explicitly invoking a Skill (such as `/workflow`, `/brainstorm`, `/quick-fix`, `/quick-feature`, `/blueprint`, `/implement`, or `/release`), the AI must NOT start work immediately.

The AI must classify the request first using the following classification rules:
- **Bug, error, regression, wrong output, broken behavior**: Recommend `quick-fix` (if localized/low-risk) or `brainstorming` (if complex/broad).
- **Small feature, simple UI block, validation, filter, button, config option**: Recommend `quick-feature`.
- **Large feature, new module, architecture change, multi-component work**: Recommend `brainstorming`.
- **Existing approved blueprint**: Recommend `blueprint-to-implementation`.
- **Debug/build/test failure after implementation**: Recommend `implementation-to-debug`.
- **Verification / Final Quality Gate check**: Recommend `debug-to-verify`.
- **Release, tagging, push, version bump, changelog update**: Recommend `implementation-to-release` ONLY if the user explicitly requested release.

### Suggestion Format:

When classification is clear, output this format and STOP:
```text
I detected this as: [classification]

Recommended Skill:
[skill-name] / [command]

Reason:
[short reason]

This workflow will:
- [step 1]
- [step 2]
- [step 3]

Confirm to continue?
Y / N
```

When multiple options are possible, output this format and STOP:
```text
I found multiple possible workflows:

Option 1:
Skill: quick-fix
Use when: this is a localized bug or small issue.
Result: creates FIX spec, then Blueprint, then waits for approval.

Option 2:
Skill: quick-feature
Use when: this is a small new feature.
Result: creates QUICK spec, then Blueprint, then waits for approval.

Option 3:
Skill: brainstorming
Use when: this may affect architecture, modules, or multiple components.
Result: starts full discovery workflow.

Please choose:
1, 2, or 3
```

The AI must use the `ask_question` tool to present the options (Yes/No or option list) as an interactive menu. If the tool is not supported by the client/IDE, fall back to the text format. The AI must NEVER execute the recommended Skill or modify files until the user explicitly confirms (either by clicking the option in the UI or by typing `Y`, `Yes`, `Proceed`, `Continue`, or the option number).

---

## 15. Workspace Permission Mode Policy

The framework supports three workspace permission modes:
- **sandbox** (Default): Under sandbox mode, the AI must explicitly prompt for approval before any state-changing action, including writing or modifying files, modifying source code, running build/test/lint commands, updating project memory/RAG, and publishing releases.
- **full_access**: Under full_access mode, the AI is granted permission to perform normal workflow actions automatically without repeated prompts. This includes writing/updating specs, design blueprints, source code files, local database files, running builds/tests, and updating project memory/RAG.
- **unrestricted**: Under unrestricted mode, the AI is granted permission to perform ALL actions automatically (including git push, tags, release, and credentials/secrets modifications) without any prompts. 

**Two-Factor Confirmation Gate**: When selecting `unrestricted` mode during workspace initialization, the CLI must output a high-impact warning and require the user to explicitly type `CONFIRM_UNRESTRICTED` to proceed. If the confirmation fails, it must fallback to `sandbox` mode.

**Hard-Gated Operations**: Even in `full_access` mode, the AI MUST explicitly prompt for approval before executing any of the following actions (they are bypassable ONLY in `unrestricted` mode):
1. Version bump and editing CHANGELOG release sections.
2. Git commits, tags, and pushing/merging branches.
3. Destructive deletion of large files/directories.
4. Shell commands targeting directories outside the workspace.
5. Editing credential, config, or security secret settings.
6. Changing the permission mode itself.

If the permission mode is missing, invalid, or corrupted, the system must automatically fallback to `sandbox` mode.

---

## 16. Interactive CLI Prompts Bridge Policy

To streamline runtime interactions and eliminate manual keyboard input in the chat interface:
1. **XML Output Interception**: Whenever a CLI subprocess outputs a `<interactive_prompt type="select">...</interactive_prompt>` XML block, the AI Agent must intercept the command output and parse the JSON payload inside the tags.
2. **Tool Invocation**: The Agent must call the `ask_question` tool using the question and options parsed from the XML payload.
3. **Piped Response**: Upon receiving the user's selection, the Agent must use the `manage_task` tool with `send_input` action to pipe the selected option string (or option index) directly back into the subprocess's stdin.
4. **Graceful Fallback**: If the `ask_question` tool is unavailable or unsupported in the current client, the Agent must print the question as text in the chat, wait for the user to type the selection, and then pipe that input back to the subprocess stdin.

---

## 17. Environment Tools Checking and Caching Policy

To optimize execution speed, minimize token utilization, and prevent redundant shell executions, the following rules apply when verifying tools in the environment during initialization:
1. **Caching Requirement**: The AI Agent must store verified environment tool states in `.agents/runtime/env_cache.json` along with a `cached_at` ISO-8601 timestamp and the list of checked tools and their status.
2. **Cache Validation**: When verifying tools during workspace initialization (`initialize-workflow`), the AI Agent must check if `.agents/runtime/env_cache.json` exists. If it exists and the `cached_at` timestamp is within the last 24 hours, the Agent MUST skip executing shell verification commands (such as `which`, `git --version`, `docker ps`, etc.) and load the tool status directly from the cache.
3. **Cache Invalidation & Recheck**: The cache is bypassed and tools are rechecked ONLY when:
   - The cache file does not exist or is corrupted.
   - The cache age exceeds 24 hours.
   - A force recheck is requested.
   - A tool marked as "available" in the cache fails to execute during workflow stages.

---

## 18. Option Selection and Decision Making Policy

To ensure structured interactions and prevent open-ended or ambiguous confirmations when presenting choices to the user:
1. **Mandatory Interactive Prompting**: Whenever the AI Agent presents multiple options, choices, or alternative paths to the user (including brainstorming directions, design alternatives, architecture options, or resolving ambiguous requirements), the Agent **MUST** use the `ask_question` tool to render the options as a structured, interactive list.
2. **Constraint on Text List**: The Agent must not simply list options in the chat text and wait for the user to type their choice. An interactive selection menu via the `ask_question` tool is mandatory.
3. **Graceful Fallback**: If the `ask_question` tool is not supported or fails in the IDE/client, the Agent may fall back to presenting the options as a numbered list in the chat text.

---

## 19. Multi-Agent Orchestration Policy

To ensure centralized decision making, task isolation, and secure parallel execution across the workspace:
1. **Orchestrator Command Primacy**: The Orchestrator is the single entry point. Every workflow execution must begin inside the Orchestrator via the `/orchestrate` command.
2. **Worker Skill Constraints**: Other workflow Skills (such as brainstorming, planning, blueprinting, implementing, etc.) act strictly as workers. Workers cannot invoke other workers, schedule parallel tasks, merge files, or own the global workflow session state.
3. **Execution Scope Isolation**: Every task scheduled by the Orchestrator must define a distinct `read_set` and a non-overlapping `write_set` in `execution-plan.json`. Workers are strictly prohibited from modifying files outside of their assigned `write_set`.
4. **File Locking Registry**: Before modifying any file, the Agent must acquire a file lock in `.agents/runtime/file-locks.json` using the `lock acquire` command. Workers must respect locks held by other tasks.
5. **No Self-Dispatch**: Agents executing worker tasks must never spawn or dispatch other agents. Only the Orchestrator owns multi-agent planning and coordination.
6. **Task Execution State**: All changes to the runtime session and parallel task statuses must be synchronized through the `workflow-runtime` CLI commands.
7. **Implementation-Only Parallel Execution**: Parallel execution is allowed ONLY during the implementation/execution phase (after an approved blueprint exists, or spec approved, and entering implementation/execution). All other workflow phases (discovery, brainstorming, planning, blueprint generation, ADR creation, memory bootstrap, memory update, RAG search, project discovery, workflow initialization, approval gates, and release) MUST remain strictly sequential.
8. **User Execution Mode Choice Timing**: The Orchestrator may never automatically choose parallel mode. The user is prompted to choose the execution mode ONLY when implementation is ready to begin. No prompts for Parallel or Sequential choice are allowed during discovery, brainstorming, planning, or blueprinting.
9. **Allowed Execution Modes**: Supported implementation modes are Parallel and Sequential. If Parallel is chosen, the Orchestrator runs concurrent workers for task groups with non-overlapping write sets. If Sequential is chosen, tasks are run one-by-one according to topological order.
10. **Choice Gate Stop**: If the user does not select a mode when prompted at the implementation start (1. Parallel, 2. Sequential, 3. Re-split, 4. Cancel), execution must stop immediately without modifying any workspace files.

---

## 20. Multi-Agent Analysis Policy

To support deep engineering research, architecture reviews, and validation while keeping workspace mutations safe:
1. **Multi-Agent Analysis Availability**: Every workflow phase (discovery, brainstorming, planning, blueprint generation, design, verification, and release) may dispatch temporary analysis agents or sub-agents for research, validation, auditing, and review purposes.
2. **Analysis-Only Scope (Read-Only)**: Analysis agents are strictly read-only. They are permitted to inspect project memory, vector RAG database, blueprints, plans, source files, configuration, logs, and git status.
3. **No Code Modification**: Analysis agents must never modify any source code files, update session or runtime state, create git commits/tags, perform releases, or edit final canonical workflow documents.
4. **Structured Recommendations**: Analysis agents return only structured recommendations and summaries. Only the owning phase agent (e.g., the planner during planning, the architect during blueprinting) is authorized to compile and output the final canonical workflow artifact (e.g., the plan, the design blueprint, the verification report).
5. **Lifespan Boundaries**: All analysis agents are temporary. Their metadata, status, and recommendations are tracked in `analysis-agents.json` and synchronized with the visualizer, and they must be automatically cleaned up upon phase completion.

---

## 21. Script-First Execution Policy

To minimize token consumption, eliminate LLM logic errors, and ensure repeatable, verifiable execution of procedural tasks:
1. **Deterministic Tasks**: All deterministic, repeatable, file-based, validation-based, and state-management actions MUST be executed by Python CLI scripts instead of natural language prompt instructions.
2. **Hybrid Tasks Separation**: For hybrid tasks (brainstorming, quick-fix, quick-feature, brainstorming-to-plan, plan-to-blueprint, ADR creation, blueprint-to-implementation), the LLM is restricted to reasoning, design, code generation, and rationale writing. The CLI script commands must handle ID allocation, path generation, YAML/markdown validation, checkpoint/session state persistence, and command execution.
3. **Structured JSON Output**: Every script-first CLI command must return structured JSON formatting on standard output.

---

## 22. Absolute Path Prohibition Policy

To prevent the leakage of user directory structures, usernames, and system details when project files and changes are pushed to remote Git repositories:
1. **No Absolute Paths**: All AI agents and CLI scripts are strictly prohibited from generating, writing, or placing absolute file paths (e.g., `/Users/username/...`, `C:\Users\username\...`, or `file:///path/to/user/...`) in any project files, documents, configuration files, prompt responses, source code, or tests.
2. **Mandatory Relative Paths**: All references to files, folders, and resources must use project-relative paths (e.g., `./skills/...`, `docs/plans/...`, or `.agents/workflow.config.json`).
3. **Markdown Links**: Fenced markdown links and file pointers must use relative URLs/paths instead of absolute URLs/schemes pointing to the local filesystem (unless using relative links like `[link](file://./relative_path)` or generic references).
4. **Scope of Application**: This rule applies universally to all Skills, docs, issues, plans, designs, code comments, tests, and CLI outputs.

---

## 23. Mandatory Skill Skeleton Policy

Whenever a Blueprint introduces a new AIWF Skill, it MUST generate the complete Skill skeleton including SKILL.md and all required supporting artifacts.

*   **Structure**:
    The generated Skill folder `skills/<skill-name>/` must contain at least:
    *   `SKILL.md` (containing Purpose, Public APIs, Workflow Integration, Configuration, Runtime Commands, Provider Strategy, Backward Compatibility, Usage Examples, Extension Points, Limitations).
    *   `scripts/` (containing Python CLI script or helpers).
    *   `tests/` (containing unit/integration tests for the CLI script).
*   **Validation Gate**:
    Any Blueprint that adds a new skill path under `skills/` but does not define `SKILL.md` or required directories in its write set is invalid and must fail validation.

---

## 24. Unified Knowledge Layer Policy

No AIWF Skill may access knowledge providers (such as Markdown files, SQLite databases, Qdrant vector databases, or Obsidian local REST APIs) directly. All knowledge operations (including search, read, write, and index updates) must go through the Knowledge Runtime API unless explicitly approved as a compatibility adapter.

*   **Machine-Level Global Provider Manager**:
    *   Cấu hình thông số kết nối và mã khóa bí mật (`api_key`) toàn cục được lưu trữ tại `~/.aiwf/providers.json` (macOS/Linux) hoặc `%USERPROFILE%\.aiwf\providers.json` (Windows).
    *   Cấm tuyệt đối lưu trữ hoặc commit mã khóa bảo mật (`api_key`) vào tệp cục bộ của dự án. Cấu hình dự án chỉ chứa các thuộc tính override cục bộ (ví dụ: tắt/bật provider hoặc thay đổi vault_path).
    *   Giao tiếp dòng lệnh CLI của `provider` được tích hợp qua lệnh `aiwf provider` (`list`, `add`, `enable`, `disable`, `test`, `doctor`).

---

## 25. Backend Architectural & Code Quality Policy

Để đảm bảo dự án phát triển bền vững và chất lượng QA/QC được kiểm soát chặt chẽ ở mức sản phẩm thật (production-ready):

1. **Domain-Driven Design (DDD) & Clean Architecture**:
   * Tất cả mã nguồn backend phải tuân thủ nghiêm ngặt mô hình Clean Architecture và DDD.
   * **Domain Layer**: Chứa Entities, Value Objects, Domain Events và Interface. Lớp này không được phụ thuộc vào bất kỳ thư viện hay framework bên ngoài nào (như HTTP, Web frameworks, ORMs, Database drivers, Message brokers, Cloud SDKs).
   * **Application Layer**: Chứa Use Cases và Ports. Logic nghiệp vụ ở đây chỉ phối hợp luồng hoạt động của Domain và chỉ phụ thuộc vào Domain abstractions.
   * **Infrastructure Layer**: Chứa Database adapters, HTTP/gRPC handlers, Wails bindings, file storage adapters.
   * Logic nghiệp vụ cốt lõi không được phép viết trực tiếp trong tệp giao tiếp (Wails controller hoặc FastAPI routes).
   * **Dependency Direction Enforcement**: Chiều phụ thuộc bắt buộc là Delivery -> Application -> Domain, Infrastructure -> Application/Domain Interfaces.

2. **Automated Architecture Fitness Validation**:
   * Hệ thống tự động quét AST (Abstract Syntax Tree) để phân tích các imports của Go và Python.
   * **Architecture Compliance Score**: Mỗi Work Item phải có điểm số kiến trúc tối thiểu đạt **95/100**.
   * **Cấm tuyệt đối Critical Architecture Violations** (bất kể tổng điểm):
     * Domain phụ thuộc vào Infrastructure hoặc Delivery.
     * Application phụ thuộc trực tiếp vào concrete Infrastructure adapters.
     * Lớp Delivery bỏ qua (bypass) Use Cases để thao tác trực tiếp với Database/Repository.
     * Có liên kết phụ thuộc vòng (circular dependency) giữa các lớp lõi.
   * Kết quả phân tích chất lượng kiến trúc bắt buộc phải được ghi nhận tại `docs/verification/<WORK_ITEM>_architecture_verify.md`.

3. **Code Lines Limit**:
   * **Giới hạn số dòng tối đa trên mỗi tệp**: Mỗi tệp tin mã nguồn backend (Go `.go`, Python `.py`) **KHÔNG ĐƯỢC VƯỢT QUÁ 500 dòng code**.
   * Nếu tệp tin vượt quá 500 dòng, bắt buộc phải thực hiện tái cấu trúc (refactoring), tách nhỏ thành các module hoặc tệp tin con riêng biệt có trách nhiệm đơn nhất (Single Responsibility Principle).

4. **QA/QC Embedded Asset Guard**:
   * **Cấm tuyệt đối Dummy Assets khi Build**: Cấm sử dụng các tệp tin giả lập (dummy), tệp tin rỗng (như index.html trống) hoặc tài nguyên thiếu (missing JS/CSS) để vượt qua bước biên dịch.
   * **Xác thực tự động**: Validation pipeline phải thực hiện quét phân tích các thư mục tài nguyên nhúng (như `frontend/dist`). Nếu phát hiện chứa tệp dummy hoặc kích thước quá nhỏ (< 1KB), pipeline phải đánh dấu thất bại ngay lập tức (FAIL) và yêu cầu build đầy đủ frontend.
   * **Graceful Runtime Check**: Đảm bảo ứng dụng sau khi khởi chạy phải load được tài nguyên giao diện thật thông qua smoke tests kiểm tra nội dung trả về, thay vì chỉ kiểm tra cổng port mở.

---

## 26. Workspace Session Runtime Policy

*   **Session Runtime as Default**: Session Runtime is the default execution model for all workspace operations. It uses lightweight in-memory and file-based state checks via the Workflow Supervisor, without requiring long-running daemons.
*   **Resident Daemon is Optional**: The Resident Daemon (Resident Orchestrator / Runtime Manager) is optional and must never be started automatically during project initialization (`aiwf init`). It can only be started explicitly via command line (e.g., `aiwf orchestrator start --mode resident`).
*   **Forbid Manual Environment Checks**: AI agents MUST NOT manually run verification commands such as `python --version`, `go version`, `node --version`, `git --version`, `docker --version`, or similar tool validation commands.
*   **Mandatory Doctor Consumption**: All environment, capability, and stack checking operations must strictly consume the structured JSON payload returned by executing `workspace_doctor.py`.

---

## 27. Workflow First Enforcement Policy

To enforce standard software engineering processes and prevent bypasses, all operations must adhere to the Workflow First Enforcement rules:

1. **Mandatory Workflow Entry Gate**:
   Every engineering request (including new features, bug fixes, refactoring, architecture changes, migrations, and code modifications) MUST enter through the Workflow Supervisor. AI must perform Intent Detection and routing first. Direct implementation is strictly prohibited.
   *Flow:* User Request -> Workflow Entry Gateway -> Intent Detection -> Workflow Supervisor -> Skill Router -> Skill Execution -> Agent Execution -> Artifacts + Evidence.

2. **Prevention of Direct Coding**:
   The AI MUST NOT directly edit source code, create implementation files, modify configurations, run build commands, or run tests before the required workflow phases are completed. Code modifications are only allowed after the design phase is approved.

3. **Mandatory Skill Lifecycle Mapping**:
   Every workflow phase must map to a registered skill:
   - Discovery -> `brainstorming`
   - Planning -> `brainstorming-to-plan`
   - Architecture -> `architecture-review`
   - Design -> `plan-to-blueprint` / `quick-feature` / `quick-fix`
   - Implementation -> `blueprint-to-implementation`
   - Debug -> `implementation-to-debug`
   - Verification -> `debug-to-verify`
   - Certification -> `vir-verify`
   - Final Review -> `final-review`
   - Release Preparation -> `release-preparation`
   - Release -> `implementation-to-release`

4. **Artifact Enforcement**:
   Every skill must generate its required artifacts under the approved docs/ directories:
   - Discovery/Brainstorming: `docs/brainstorming/FEAT-xxx.md` (or `docs/brainstorming/FIX-xxx.md`)
   - Planning: `docs/planning/FEAT-xxx_plan.md`
   - Design/Blueprint: `docs/blueprints/FEAT-xxx_blueprint.md`
   - Technical Reports: `docs/reports/FEAT-xxx_report.md`
   Creating workflow artifacts in project root is strictly forbidden. If a required artifact is missing or stored in an invalid location, the workflow status is set to `BLOCKED`.

5. **State Separation (Workspace vs. Workflow)**:
   Workspace state is decoupled from feature workflow state. Workspace state being `READY` does not mean the feature workflow is completed or released. Release decisions must depend on verified evidence.

6. **Human Approval Gates**:
   Human approval is strictly required at three strategic gates:
   - Gate 1: Planning Approval
   - Gate 2: Blueprint Approval
   - Gate 3: Release Approval
   All intermediate phases (Implementation, Debug, Verification, Certification, Final Review, Release Preparation, Post Release Validation, Monitoring, Governance) must execute autonomously when evidence passes.

7. **AI Response Behavior**:
   When receiving an engineering request, the AI must first output a detection summary and STOP:
   ```text
   AIWF Workflow Detection
   Intent: [Feature Request | Bug Fix | Refactoring | Migration]
   Workflow: [feature-development | bug-fix | refactoring | migration]
   Starting Skill: [skill-name]
   ```
   Do not modify code immediately.

8. **Workflow Trace Requirement**:
   Every engineering request must create trace events:
   - `workflow.request.received`
   - `workflow.started`
   - `skill.selected`
   - `skill.started`
   - `artifact.created`
   - `phase.completed`
   - `workflow.completed`
   These events must be appended to `.agents/state/events/events.jsonl` (or `.agents/state/events.jsonl`).

9. **Legacy Resident Orchestrator Migration**:
   The Resident Orchestrator is deprecated. The default model is Session Runtime + Workflow Supervisor. Resident daemon mode only runs when explicitly commanded by the user.


---

## Section 28: Artifact Governance & Documentation Structure Policy

1. **Approved Documentation Storage**:
   All AIWF generated artifacts MUST be stored under approved documentation directories. Creating workflow artifacts in project root is forbidden.
   
   Approved mappings:
   - **Brainstorming**: `docs/brainstorming/`
   - **Planning**: `docs/planning/`
   - **Architecture**: `docs/architecture/`
   - **Blueprints**: `docs/blueprints/`
   - **Implementation**: `docs/implementation/`
   - **Verification**: `docs/verification/`
   - **Release**: `docs/release/`
   - **Reports**: `docs/reports/`
   - **Operations**: `docs/operations/`

2. **Creation Lifecycle**:
   Before creating any artifact:
   - Identify artifact type.
   - Select approved directory.
   - Validate path.
   - Create document.

3. **Supervisor Blocking**:
   Workflow Supervisor must verify artifact paths and naming before phase transitions. Any violation will set status to `BLOCKED` with reason `Artifact governance violation`.
