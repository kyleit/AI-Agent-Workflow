---
name: blueprint-to-implementation
command: implement
aliases:
  - code
  - build
category: workflow
tags:
  - implementation
  - code
  - generation
version: 3.2.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-09
description: Enforces Blueprint validation as the sole inputs for implementation, upgraded to support v3.2 JSON blueprints.
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
  usage: cached---

# Skill: Blueprint to Implementation (Blueprint-Driven Guardrails)

## Purpose

Enforces Blueprint validation as the sole inputs for implementation, upgraded to support v3.2 JSON blueprints.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 4"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "blueprint-to-implementation" --command "implement" --checkpoint 5 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 5 --step "Step Complete" --next-skill "implementation-to-debug" --next-command "debug"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.
- **Blueprint Mandatory Execution Policy** (Section 13) - Enforces Blueprint as the sole legal input.
- **Skill Suggestion Gate Policy** (Section 14) - Raw requests require suggestion first; selected Skill requires confirmation.
- **Workspace Permission Mode Policy** (Section 15) - Sandbox mode is default; ask user to choose sandbox or full_access at init.

---

## 🔒 MANDATORY INPUT VALIDATION GATES

Prior to generating any source code, modifying existing files, or conducting any implementation steps, the AI must strictly execute the following validations:

1. **Verify Blueprint Path**: Identify the Technical Design Blueprint file(s). The path must reside under the `docs/blueprints/` directory, in one of two shapes (see `plan-to-blueprint`):
   - **Single-file shape**: `docs/blueprints/FEAT-XXX_feature_slug_blueprint.md` (+ `.json`).
   - **Multi-phase folder shape**: `docs/blueprints/<feature-slug>/phase-NN-<phase-slug>/phase-blueprint.md` (+ `.json`), plus `docs/blueprints/<feature-slug>/master/FEAT-XXX_..._master_blueprint.md` for feature-wide context. Implement one phase per `/implement` invocation unless the user explicitly asks for more.
2. **Verify Blueprint File Existence**: Confirm the target blueprint file(s) exist on disk.
3. **Discover and read every companion file**: A `phase-blueprint.md` (or single-file blueprint) may be an index pointing to companion files split out by layer/module (e.g. `phase-blueprint-domain-layer.md`, `phase-blueprint-implementation-detail.md`) per the blueprint's own file-splitting rule. Read the index first, then read **every** companion it links before writing any code — a companion holds the exact struct fields, method signatures, and step-by-step logic; implementing from the index alone produces incomplete code.
4. **Verify Blueprint Status Check**: Verify that the blueprint is marked as `"approved": true` in the active workflow session data or that explicit approval (`Y`, `Yes`, `Proceed`, `Continue`) was given in the chat log.
5. **Reject Unapproved Inputs**: Reject any brainstorm documents, planning documents, feature specifications, or quick specifications as source code generation inputs.
6. **Load Structured JSON Blueprint**: Coder/Developer MUST search for and read the structured JSON representation of the blueprint (`...blueprint.json`, same shape/location as the `.md`) first. If it exists, load it to extract class structures, methods, dependencies, database schema, test matrices, and implementation contracts with minimal token usage. If the JSON blueprint does not exist, fall back to reading the `.md` file(s) from step 3.
7. **Re-verify against real, current source**: For every file the blueprint's File-by-File Analysis table marks `MODIFY`, open that real file now and confirm it still matches what the blueprint assumed (the blueprint may have been written before other changes landed). If it has drifted, STOP and report the concrete delta (file:line) instead of silently reconciling or guessing — this is the same discipline the blueprint itself was written under.

**If any check fails:**
- **STOP immediately**.
- Print the warning: `❌ Implementation aborted: No approved Technical Design Blueprint found. Please generate and get user approval for the blueprint file(s) under docs/blueprints/ before proceeding.`
- Halt all file generation and modifications.

---

## 🔒 BLUEPRINT-DRIVEN CODE TRANSCRIPTION MANDATE

The blueprint this Skill consumes is not a high-level sketch — per `plan-to-blueprint`'s depth requirement, it already specifies, for every class/module: its DDD/Clean-Architecture layer, every struct/class field (name + type + purpose), every method's complete signature (every parameter typed, every return/error type), and a numbered, step-by-step pseudocode description of each non-trivial method body. This Skill's job is to **transcribe** that specification into real, compilable code in the target language — not to redesign it.

Concretely:
- **File placement**: create each file in the exact directory the blueprint's "Target Folder Structure" section specifies (the DDD layer — domain/application/infrastructure/interface — is not optional or renameable mid-implementation).
- **Signatures & fields**: struct/class fields and method signatures in the generated code must match the blueprint's names and types exactly, translated into the target language's real syntax.
- **Method bodies**: turn each numbered pseudocode step into the equivalent real statement(s) in the target language — branches become `if`/`switch`, the stated error path becomes the stated error return/throw, the stated call to another module becomes a real call to that module's real (blueprint-specified) signature. Do not invent a different algorithm even if you believe it's better — if the blueprint's approach looks wrong, STOP and flag it rather than silently substituting your own design.
- **Dependency direction**: before marking a phase's implementation done, verify the generated code's imports actually respect the inward-only dependency rule (domain imports nothing from application/infrastructure/interface; application imports domain + its own declared ports only; infrastructure/interface implement/call inward). A domain file importing an HTTP or DB package is a defect, not a style nit.
- **Genuine gaps**: if the blueprint is ambiguous or silent on something code-generation needs (e.g. an exact error message string), make the smallest reasonable choice, note it explicitly in the Final Summary's "Remaining Issues" — do not block on it, but do not hide it either.

## 🔒 LANGUAGE SKILL ROUTING MATRIX

When implementing, implementation agents must check the project language and load the corresponding helper skills:
- **Python**: For `*.py`, FastAPI, Django, Flask, pytest -> load `python-development`; use `python-patterns` for framework/architecture decisions.
- **Go**: For `*.go`, `go.mod`, Go services -> load `go-development`; use `golang-pro` for goroutines, channels, gRPC, generics, performance, microservices.
- **C#**: For `*.cs`, `*.csproj`, `*.sln`, ASP.NET Core, EF Core, LINQ, Unity C# -> load `csharp-dotnet-pro`.
- **Any other stack** (JS/TS, Rust, Java, etc.): if no dedicated language skill exists under `.agents/skills/` for it, proceed using the target language's own idiomatic conventions and the blueprint's explicit guidance — do not force-fit a Python/Go/C# skill's conventions onto a different language. Note in the Final Summary that no dedicated language skill was available.

---

## Final Summary Format

Upon completion of the implementation and validation phase, print this exact final summary format to the console and update `.session.json`:

```markdown
## Implementation Status

[PASS | FAILED]

## Implemented

- [Bullet points of implemented features/modules]

## Files Created

- [List of created files or "None"]

## Files Modified

- [List of modified files or "None"]

## Validation

### Build
Command: [detected command or "None"]
Result: [PASS | FAILED | Not Configured]

### Tests
Command: [detected command or "None"]
Result: [PASS | FAILED | Not Configured]

### Lint
Command: [detected command or "None"]
Result: [PASS | FAILED | Not Configured]

### Typecheck
Command: [detected command or "None"]
Result: [PASS | FAILED | Not Configured]

### Real Integration QA
Surface: [the real integration surface exercised — e.g. real IPC pipe call, real DB, real HTTP call to a running server, real browser session — NOT a mock/stub of it]
Result: [PASS | FAILED | Not Applicable + why]
Note: A phase is not "done" on unit tests alone if the blueprint's design involves any real I/O boundary (pipe, DB, network, external process) — that boundary must be exercised for real at least once before this reads PASS.

### Layer Placement & Dependency Direction
Result: [PASS | FAILED]
Note: Every new file is in the directory its blueprint layer (Domain/Application/Infrastructure/Interface) specifies, and a dependency-direction check (domain imports nothing outward) was actually performed, not assumed.

### Self Review
Result: [PASS | FAILED]

## Issues Fixed During Validation
- [Bullet points of fixes applied during validation or "None"]

## Remaining Issues
- [Bullet points of remaining/unresolved issues or "None"]

## Recommended Next Skill
- If PASS: /debug or /verify
- If FAILED: /debug

Workflow Paused.
```

---

## 🔒 GIT BRANCH GATE
Before initiating code generation, query the user's branch intention using:
```bash
python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Choose Git branch action:" --options "Continue on current branch|Create new branch|Stop" --default "Stop"
```
