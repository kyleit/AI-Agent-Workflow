---
name: go-development
command: go-dev
aliases:
  - golang
  - go
category: implementation
tags:
  - go
  - golang
  - backend
  - testing
  - linting
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-15
updated_at: 2026-07-15
description: Guides Go development tasks including modules, building, testing, linting, and basic service structure.
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

# Skill: go-development (Go Implementation Guidelines)

## 1. Purpose
Provides comprehensive guidelines for building idiomatic, robust, and clean applications in Go, targeting compiling, building, testing, and linting.

## 2. Workflow Runtime & Initialization Check
This Skill is invoked dynamically by `blueprint-to-implementation` routing based on the target project tech stack. It does not directly manage workflow checkpoints or session state updates.

## 3. Global Policy References
Adheres strictly to the policies defined in `AI_RULES.md`:
- **Approval Gate Policy** (Section 1) - Seek confirmation before modifying code.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits with approval.
- **Memory First Policy** (Section 3) - Search codebase/memory first.
- **RAG Policy** (Section 4) - Level-based query sequences.
- **Testing Policy** (Section 8) - Run test validation suites.

## 4. Public APIs / Trigger Contract
- **Commands**: `go-dev`
- **Aliases**: `golang`, `go`
- **File Patterns**: `*.go`, `go.mod`, `go.sum`

## 5. Workflow Integration
When `blueprint-to-implementation` executes, it detects Go files within the scope of changes and routes specific code modifications and validation commands to this skill.

## 6. Language-Specific Guidance
- **Codebase-First & RAG-First**: Check `go.mod` for dependencies. Use RAG queries or `grep` before writing.
- **Idiomatic Go Practices**: PascalCase for exported symbols, camelCase for unexported. Package names lowercase single-word. Composition over inheritance. Always format with `go fmt` or `goimports`.
- **Explicit Error Handling**: Do not ignore errors. Wrap errors with `%w`. Do not use `panic` for normal control flow.
- **Correct Context Usage**: Pass `ctx context.Context` as first parameter for I/O functions. Check `ctx.Done()` for deadlines. Never store contexts in structs.
- **Table-Driven Testing**: Use struct arrays with inputs, expected outputs, and `t.Run` execution.
- **Debugging**: Analyze stack traces. Use structured logging (`log/slog` or `zap`). Use Delve (`dlv debug`).
- **Database & Architecture**: Standard database/sql or sqlx, explicit transactions. Clean package layout (`cmd/`, `internal/`, `pkg/`).

## 7. Validation Commands
Before completion, ensure all tests and checkers pass:
- **Build Compilation**: `go build ./...`
- **Lint Verification**: `golangci-lint run`
- **Test Runner**: `go test -v -race ./...`

## 8. Provider Strategy
Provider agnostic. Emphasizes Go compiler warnings and project RAG analysis before LLM generation.

## 9. Backward Compatibility
Fully compatible with Go 1.18+ environments.

## 10. Usage Examples
- Formatted testing run:
  ```bash
  go fmt ./... && go test -v -race ./...
  ```

## 11. Extension Points
Custom linters can be integrated in `.golangci.yml` configurations.

## 12. Limitations
Requires Go SDK installed and correctly configured on the developer path.
