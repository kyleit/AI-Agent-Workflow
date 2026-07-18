---
name: golang-pro
command: golang-pro
aliases:
  - go-pro
  - go-advanced
category: implementation
tags:
  - go
  - golang
  - concurrency
  - grpc
  - performance
  - microservices
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-15
updated_at: 2026-07-15
description: Guides advanced Go programming including concurrency (goroutines, channels), performance profiling, gRPC, generics, and microservices architecture.
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

# Skill: golang-pro (Advanced Go Programming)

## 1. Purpose
Governs high-performance, concurrent, and scalable application development in Go, targeting system-level optimization and advanced patterns.

## 2. Workflow Runtime & Initialization Check
This Skill is invoked dynamically by `blueprint-to-implementation` routing based on target service design. It does not directly manage workflow checkpoints or session state updates.

## 3. Global Policy References
Adheres strictly to the policies defined in `AI_RULES.md`:
- **Approval Gate Policy** (Section 1) - Seek confirmation before introducing complex patterns.
- **Memory First Policy** (Section 3) - Align with existing microservices frameworks.
- **Testing Policy** (Section 8) - Run race detector and fuzz checks.

## 4. Public APIs / Trigger Contract
- **Commands**: `golang-pro`
- **Aliases**: `go-pro`, `go-advanced`
- **File Patterns**: `*.go`, `*.proto`, `go.mod`

## 5. Workflow Integration
Executed when building critical backends, streaming APIs, or performance-sensitive systems.

## 6. Language-Specific Guidance
- **Concurrency & Channels**: Managing goroutine lifecycles. Prefer unbuffered channels. Avoid closing from receiver. Use `select` with timeouts.
- **Worker Pools & Graceful Shutdown**: Implement signal handling (Interrupt, SIGTERM) and WaitGroup. Throttle resource usage.
- **High-Performance gRPC**: Define APIs in protobuf. Middleware interceptors. Bidirectional streaming APIs.
- **Microservices**: Decouple via brokers. OpenTelemetry tracing and Prometheus metrics.
- **Clean Interface Design**: SOLID interfaces (consumer-owned). Keep them small, return structs and accept interfaces.
- **Go Generics**: Type-safe structures ([T any]). Avoid over-engineering.
- **Diagnostics & Profiling**: Integrate `net/http/pprof`. Analyze CPU/Heap profiles.
- **Benchmarks & Memory**: Use `testing.B` with `-benchmem`. sync.Pool recycling. Avoid string/[]byte conversions.
- **Race Condition Detection**: Always use `-race` during testing and building. Use atomic/Mutex.
- **Native Fuzz Testing**: Write fuzz tests using `testing.F` to catch edge cases.

## 7. Validation Commands
Before completion, ensure advanced checkers pass:
- **Race Detection**: `go test -race ./...`
- **Benchmarks**: `go test -bench=. -benchmem ./...`
- **Fuzzing**: `go test -fuzz=FuzzParser -fuzztime=10s`

## 8. Provider Strategy
Provider agnostic. Focuses on profiling outputs and compiler/linter diagnostics.

## 9. Backward Compatibility
Requires Go 1.18+ (for generics and fuzzing support).

## 10. Usage Examples
- Profiling setup check:
  ```bash
  go tool pprof http://localhost:6060/debug/pprof/profile
  ```

## 11. Extension Points
Observability hooks and trace exporters.

## 12. Limitations
Fuzzing and generics require modern Go SDK support.
