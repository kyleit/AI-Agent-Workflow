---
name: project-discovery
command: discover
aliases:
  - tech-stack
  - project-profile
category: environment
tags:
  - project
  - tech-stack
  - workflow
  - profile
  - discovery
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-05
updated_at: 2026-07-05
description: Discover target project's tech stack (languages, frameworks, tools, platforms, databases, infrastructure) and generate project-profile.json to configure dynamic workflow checkpoints.
---

# Skill: Project Discovery

## Purpose

Discover target project's technologies (languages, frameworks, compilers, test frameworks, lint tools, database systems, runtime environments, and infrastructure) and generate `.agents/project-profile.json`.

This profile is loaded by the workflow orchestrator, runtime engine, quality debug/verify skills, and the VS Code Webview dashboard to adjust quality gates and checkpoints dynamically according to the actual tech stack of the project.

This Skill must run before planning or implementation begins. If `.agents/project-profile.json` is missing or stale, the orchestrator will mandate running this Skill.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "at least 1"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "project-discovery" --command "discover" --checkpoint 1 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 1 --step "Step Complete" --next-skill "project-memory-bootstrap" --next-command "memory-init"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.

## Detection Targets and Sources

The Skill scans configuration files in the workspace root or key directories (without doing a full recursive scan of `node_modules`, `vendor`, or `.git` folders):

### Key Scan Sources
```text
package.json
pnpm-lock.yaml
yarn.lock
bun.lockb
vite.config.*
next.config.*
svelte.config.*
angular.json
wails.json
go.mod
pyproject.toml
requirements.txt
pytest.ini
Cargo.toml
pom.xml
build.gradle
pubspec.yaml
docker-compose.yml
Dockerfile
.github/workflows/
```

### Stack Detection Categories

1. **Languages**:
   - `Go`: `go.mod`
   - `Python`: `pyproject.toml`, `requirements.txt`, `setup.py`
   - `TypeScript`/`JavaScript`: `package.json`, `tsconfig.json`
   - `Rust`: `Cargo.toml`
   - `Java`: `pom.xml`, `build.gradle`
   - `PHP`: `composer.json`
   - `Dart`: `pubspec.yaml`
   - `C#`: `*.csproj`
   - `C/C++`: `CMakeLists.txt`, `Makefile`

2. **Frameworks**:
   - `React`: `react` in package dependencies.
   - `Vue`: `vue` in package dependencies.
   - `Svelte` / `SvelteKit`: `svelte`, `@sveltejs/kit` in package dependencies.
   - `Next.js`: `next` in package dependencies.
   - `Nuxt`: `nuxt` in package dependencies.
   - `Angular`: `@angular/core` or `angular.json`
   - `Vite`: `vite` in package dependencies or `vite.config.*`
   - `Wails`: `wails.json` or `wails` references in code.
   - `Electron`: `electron` in package dependencies.
   - `Flutter`: `flutter` in `pubspec.yaml`
   - `React Native`: `react-native` in package dependencies.
   - `Gin` / `Echo`: `github.com/gin-gonic/gin` or `github.com/labstack/echo` in `go.mod`
   - `FastAPI` / `Django` / `Flask`: package list in python dependency files.
   - `Laravel`: `laravel/framework` in `composer.json`
   - `Spring Boot`: `spring-boot-starter` in maven/gradle dependencies.

3. **Tooling**:
   - Package managers: `npm`, `pnpm`, `yarn`, `bun`
   - Testing: `go test`, `pytest`, `cargo test`, `gradle test`, `maven test`, `vitest`, `jest`
   - Linting: `eslint`, `ruff`, `cargo clippy`
   - Formatting: `prettier`, `black`, `ruff`
   - Typechecking: `typescript` (`tsc`), `mypy`
   - End-to-End: `playwright`, `cypress`

4. **Runtime/Platform**:
   - `Desktop`: Wails, Electron, Tauri, PyQt.
   - `Mobile`: Flutter, React Native, Android, iOS.
   - `Browser Extension`: `manifest.json` under root or src directories.
   - `CLI`: python entrypoints, rust main, or custom CLI flags.
   - `Dockerized App`: `Dockerfile` or `docker-compose.yml`
   - `Web` / `Backend API`: web frameworks, index.html.

5. **Database / Infra**:
   - `PostgreSQL` / `MySQL` / `SQLite` / `Redis` / `MongoDB` / `Qdrant` / `Docker` / `Docker Compose` / `Kubernetes`

---

## Dynamic Workflow Checkpoint Generation Rules

The Skill constructs the `recommended_workflow` array in `.agents/project-profile.json` using these rules:

### 1. Always Included Checkpoints (Base Core)
- **Workspace Initialization** (skill: `initialize-workflow`, command: `init`, agent: `architect`)
- **Memory & Environment Load** (skill: `project-memory-update`, command: `memory-sync`, agent: `architect`)
- **Architecture Analysis** (skill: `brainstorming`, command: `brainstorm`, agent: `planner`)
- **Implementation Plan** (skill: `planning-prompt-to-plan`, command: `plan`, agent: `planner`)
- **Technical Blueprint** (skill: `plan-to-blueprint`, command: `blueprint`, agent: `architect`)
- **Code Generation** (skill: `blueprint-to-implementation`, command: `implement`, agent: `coder`)
- **Quality Debugging** (skill: `implementation-to-debug`, command: `debug`, agent: `coder`)
- **Feature Verification** (skill: `debug-to-verify`, command: `verify`, agent: `reviewer`)
- **Release & Documentation** (skill: `implementation-to-release`, command: `release`, agent: `release-manager`)

### 2. Conditionally Inserted Checkpoints
- **Frontend Visual Debug** (skill: `frontend-visual-debug`, command: `visual-debug`, agent: `frontend-qa`):
  - Insert between **Quality Debugging** and **Feature Verification**.
  - Required if: React, Vue, Svelte, SvelteKit, Next.js, Nuxt, Angular, Vite, Wails frontend, Electron, or Browser Extension are detected.
  - Profile marks `"visual_debug": { "required": true, "type": "frontend", "reason": "Detected Svelte/React/Vite" }`.
- **Desktop UI Debug** (skill: `desktop-ui-debug`, command: `desktop-debug`, agent: `desktop-qa`):
  - Insert between **Quality Debugging** and **Feature Verification**.
  - Required if: Wails, Electron, Tauri, or PyQt detected.
  - Profile marks `"visual_debug": { "required": true, "type": "desktop", "reason": "Detected Wails/Tauri" }`.
- **Mobile Visual Debug** (skill: `mobile-visual-debug`, command: `mobile-debug`, agent: `mobile-qa`):
  - Insert between **Quality Debugging** and **Feature Verification**.
  - Required if: Flutter, React Native, Android, or iOS detected.
  - Profile marks `"visual_debug": { "required": true, "type": "mobile", "reason": "Detected Flutter/ReactNative" }`.
- **Database Migration Check** (skill: `db-migration-check`, command: `db-verify`, agent: `db-engineer`):
  - Insert between **Quality Debugging** and **Feature Verification**.
  - Required if: `migrations/` folder, Prisma, Goose, SQLC, Alembic, Flyway, or Liquibase detected.

---

## Output Profile Template: `.agents/project-profile.json`

Generate `.agents/project-profile.json` in this format:

```json
{
  "project_id": "[feature-identifier-or-directory-name]",
  "detected_at": "[ISO-8601-Timestamp]",
  "languages": ["typescript", "go"],
  "frameworks": ["svelte", "vite", "wails"],
  "platforms": ["desktop", "web"],
  "package_managers": ["npm"],
  "build_tools": ["vite", "go compiler"],
  "test_tools": ["vitest", "go test"],
  "lint_tools": ["eslint"],
  "format_tools": ["prettier"],
  "typecheck_tools": ["typescript"],
  "databases": ["sqlite"],
  "infra": ["docker-compose"],
  "quality_gates": ["build", "lint", "test", "typecheck", "visual_debug"],
  "visual_debug": {
    "required": true,
    "type": "desktop",
    "reason": "Detected Go + Wails Desktop Application"
  },
  "recommended_workflow": [
    { "name": "Workspace Initialization", "skill": "initialize-workflow", "command": "init", "agent": "architect", "logs": ["> Scanning workspace structure...", "> Loading project rules & policies", "> Checking Git environment status"] },
    { "name": "Memory & Environment Load", "skill": "project-memory-update", "command": "memory-sync", "agent": "architect", "logs": ["> Scanning file system modifications...", "> Syncing RAG search vectors", "> Memory index updated successfully"] },
    { "name": "Architecture Analysis", "skill": "brainstorming", "command": "brainstorm", "agent": "planner", "logs": ["> Discovering system requirements...", "> Checking constraint validation", "> Readiness score: 85/100"] },
    { "name": "Implementation Plan", "skill": "planning-prompt-to-plan", "command": "plan", "agent": "planner", "logs": ["> Generating project implementation plan...", "> Estimating complexity & risks", "> Defining verification checklists"] },
    { "name": "Technical Blueprint", "skill": "plan-to-blueprint", "command": "blueprint", "agent": "architect", "logs": ["> Generating technical design specifications...", "> Writing module dependencies and schemas", "> Designing class signatures and APIs"] },
    { "name": "Code Generation", "skill": "blueprint-to-implementation", "command": "implement", "agent": "coder", "logs": ["> Generating logic modifications...", "> Editing source code files", "> Applying incremental code diffs"] },
    { "name": "Quality Debugging", "skill": "implementation-to-debug", "command": "debug", "agent": "coder", "logs": ["> Compiling the codebase...", "> Running linters and formatting code", "> Fixing failing test cases and improving logs"] },
    { "name": "Frontend Visual Debug", "skill": "frontend-visual-debug", "command": "visual-debug", "agent": "frontend-qa", "logs": ["> Opening browser...", "> Inspecting DOM...", "> Checking console...", "> Comparing layout...", "> Testing interactions...", "> Generating visual report..."], "conditional": "frontend" },
    { "name": "Feature Verification", "skill": "debug-to-verify", "command": "verify", "agent": "reviewer", "logs": ["> Reviewing blueprint compliance...", "> Testing acceptance criteria and performance", "> Performing final code audits and security checks"] },
    { "name": "Release & Documentation", "skill": "implementation-to-release", "command": "release", "agent": "release-manager", "logs": ["> Bumping package version...", "> Generating change logs", "> Committing & pushing to git repository"] }
  ]
}
```

---

## Completion Contract

Upon execution:
- Print the list of detected technologies.
- Print the generated list of checkpoints.
- Verify that `.agents/project-profile.json` was successfully created.
- Set `.session.json` checkpoint to `2` and status to `completed`.
- Output workflow runtime heartbeat.
