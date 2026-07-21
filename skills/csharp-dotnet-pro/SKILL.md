---
name: csharp-dotnet-pro
command: csharp-dotnet
aliases:
  - csharp
  - dotnet
  - cs
category: implementation
tags:
  - csharp
  - dotnet
  - aspnet-core
  - ef-core
  - linq
  - unity
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-15
updated_at: 2026-07-15
description: Guides advanced C# and .NET development including C#, CSharp, dotnet, .NET 8, .NET 9, ASP.NET Core, EF Core, LINQ, async/await, xUnit, NUnit, Clean Architecture, and Unity C#.
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

# Skill: csharp-dotnet-pro (C# & .NET Enterprise & Unity Guidelines)

## 1. Purpose
Governs enterprise-grade application development using C# and .NET platforms, ensuring adherence to clean architecture principles and performance best practices.

## 2. Workflow Runtime & Initialization Check
This Skill is invoked dynamically by `blueprint-to-implementation` routing based on target solution detection. It does not directly manage workflow checkpoints or session state updates.

## 3. Global Policy References
Adheres strictly to the policies defined in `AI_RULES.md`:
- **Approval Gate Policy** (Section 1) - Seek confirmation before modifying code.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits with approval.
- **Memory First Policy** (Section 3) - Search codebase/memory first.
- **RAG Policy** (Section 4) - Level-based query sequences.
- **Testing Policy** (Section 8) - Run test validation suites.

## 4. Public APIs / Trigger Contract
- **Commands**: `csharp-dotnet`
- **Aliases**: `csharp`, `dotnet`, `cs`
- **File Patterns**: `*.cs`, `*.csproj`, `*.sln`

## 5. Workflow Integration
When `blueprint-to-implementation` executes, it detects solution/csproj files within the scope of changes and routes specific code modifications and validation commands to this skill.

## 6. Language-Specific Guidance
- **Project Detection**: Scan solutions (`*.sln`) or C# projects (`*.csproj`). Identify target frameworks (`net8.0`, `net9.0`).
- **API Design**: Minimal APIs for microservices. Controllers for complex monoliths. Standard responses (Problem Details RFC 7807).
- **EF Core**: Use migrations (`dotnet ef migrations add`). Scoped `DbContext`. AsNoTracking for reads. Eager loading (Include/ThenInclude). Transactions for mutation.
- **LINQ Correctness**: Deferred execution materialization (`.ToList()`, `.ToArray()`). `IQueryable` for SQL filtering vs `IEnumerable` for memory. Use `.Any()` instead of `.Count() > 0`.
- **Async & Cancellation**: Propagate `CancellationToken`. Use `ValueTask` on hot paths. Avoid Sync-over-Async (`.Result`, `.GetAwaiter().GetResult()`).
- **Architecture & DDD**: Domain (pure), Application (Mediator), Infrastructure layers. Domain events.
- **Unity Constraints**: Avoid GC allocations inside hot loops (`Update`). Cache components (`GetComponent`) in Awake/Start. Optimize structs by reference (`in`, `out`, `ref`).
- **Anti-patterns to Avoid**: N+1 queries, Sync-over-async, multiple query materializations.

## 7. Validation Commands
Before completion, ensure all tests and checkers pass:
- **Build**: `dotnet build`
- **Formatting**: `dotnet format --verify-no-changes`
- **Testing**: `dotnet test` (xUnit or NUnit)

## 8. Provider Strategy
Provider agnostic. Emphasizes MSBuild warning levels and project RAG analysis before LLM generation.

## 9. Backward Compatibility
Fully compatible with .NET Standard, .NET 8, .NET 9, and Unity Mono/IL2CPP runtimes.

## 10. Usage Examples
- Run local code build and test checks:
  ```bash
  dotnet build && dotnet test
  ```

## 11. Extension Points
Roslyn analyzers can be added to custom project packages.

## 12. Limitations
Requires .NET SDK / Unity editor installed locally to validate.
