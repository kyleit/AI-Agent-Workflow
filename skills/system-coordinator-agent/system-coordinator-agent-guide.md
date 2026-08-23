# System Coordinator Agent Guide

## 1. Coordinator Role

The coordinator owns the full module rollout lifecycle by phase. The rules in this guide apply to every project module, workflow, and artifact. Do not move to the next phase until there is real test evidence and the minimum quality score has been met.

The coordinator must:

1. Receive Ba's request and identify the current phase correctly.
2. Break the work into independent lanes or agents when parallel execution is safe.
3. Assign each lane a clear edit scope, read-only scope, test scope, and boundary against other lanes.
4. Track lane progress, stop incorrect lanes, and redirect work when needed.
5. Consolidate results and re-check them through direct review and real commands.
6. Score readiness and readability on a 100-point scale.
7. Allow phase promotion only when the result scores at least 95/100 and does not violate the path policy.

## 2. Agent Lane Splitting Rules

When using multiple agents or Antigravity lanes, the coordinator must split work so lanes do not overwrite each other.

Example lane split:

1. **Implementation lane**: edits source code inside the assigned module scope.
2. **Audit lane**: read-only review of command surface, security risks, path policy, and missing cases.
3. **Test harness lane**: creates test scripts and cases, without source edits.
4. **Real runtime QA lane**: runs real cases against the open app, service, API, UI, CLI, or integration surface depending on the module type.
5. **Next phase preparation lane**: read-only preparation for the next phase, without early implementation.

Each lane must receive:

- **Goal**: what output the lane must produce.
- **Edit scope**: which files or folders the lane may modify.
- **Read-only scope**: which areas the lane may inspect only.
- **Forbidden actions**: do not revert others' code, do not delete artifacts outside the lane, and do not promote the phase.
- **Required output**: changed files, tests run, remaining errors, and final report.

## 2.1 Mandatory Prompt Injection (Deep Thinking & Code Grounding)

When assigning tasks to sub-agents via the AGY CLI (using `--print "<prompt>"`), the coordinator **MUST ALWAYS** insert the following strict directive into the prompt payload. This enforces deep thinking, practical problem solving, and prevents the agent from hallucinating or answering based on memory instead of real code:

> "ACTIVATE DEEP THINKING MODE: You MUST think carefully step-by-step before taking any action or answering. Your responses and output artifacts MUST be highly practical, direct, and not beat around the bush. All documentation, analysis, and code modifications MUST be strictly grounded in the actual codebase (you must read the real code using tools) and NEVER based on your training memory or assumptions."

## 2.2 Mandatory Prompt Injection (Skill Enforcement & Document Generation)

To guarantee that AGY strictly generates documents using the correct skills as defined by `workflow-coordinator`, the coordinator **MUST** also inject the following directive into the prompt payload:

> "MANDATORY WORKFLOW ENFORCEMENT: You MUST execute the exact workflow skill assigned to this phase. 
> 1. Before doing anything else, you MUST use the `view_file` tool to read `.agents/skills/<target_skill>/SKILL.md`.
> 2. You MUST strictly generate the documents and artifacts according to the format, templates, and rules inside that skill. 
> 3. You MUST comply with all global framework rules listed in `.agents/AI_RULES.md` and `.agents/AGENTS.md`.
> 4. DO NOT skip phases, do not invent document formats, and ALWAYS include the required `Internal Review Evidence` section before considering the document complete."

## 2.3 Micro-Tasking & Granular Blueprinting Rule (Overcoming AGY Laziness)

The Coordinator must recognize that AGY operates as a fast, context-limited worker and often outputs superficial, generic, or high-level English summaries if the assigned task is too broad. To overcome this and guarantee absolute implementation precision:

1. **Chunking / Micro-Tasking**: DO NOT assign the generation of a massive multi-component Blueprint or Spec in a single AGY dispatch. Break the work down and assign it piece-by-piece, file-by-file, or component-by-component.
2. **Zero-Guesswork Code-Block Level Standard**: Instruct AGY in the prompt that the Blueprint MUST be written at the code-block level of detail. Vague English descriptions are FORBIDDEN. The blueprint must contain precise data structures, exact function/API signatures, and step-by-step algorithmic logic inside code blocks, so that the implementation phase requires absolutely zero guesswork.
3. **Aggressive Rejection**: When reviewing AGY's output, if the document lacks block-code level detail or relies on lazy instructions (e.g., "update the logic here to do X"), the Coordinator MUST aggressively reject the artifact, fail the review, and dispatch a highly targeted prompt forcing AGY to rewrite that exact section with precise code-level details.

## 3. Project Rule and Skill Usage Rules

The coordinator and every assigned agent must use project-owned rules and skills before inventing a separate workflow.

Before starting a phase or work lane, the coordinator must:

1. Read and apply the rules in `PROJECT_RULES.md`, `./.agents/AGENTS.md`, and `./.agents/AI_RULES.md`.
2. Treat `./.agents/AI_RULES.md` as the primary workflow framework policy source when rule documents conflict.
3. Prioritize Memory First: read relevant Project Memory before scanning source code or asking Ba for design guidance.
4. Prioritize RAG First: when more context is needed, use `./.agents/skills/project-rag-search` first; inspect source files directly only when Memory/RAG is insufficient.
5. Do not scan the whole repository when Memory/RAG already returns sufficient sources; inspect only the files identified by Memory/RAG or project rules.
6. Scan or read the available skills under `./.agents/skills`.
7. Select the skills that directly match the work type, such as planning, blueprinting, implementation, debugging, verification, frontend review, or workflow runtime.
8. State which project rules, Memory/RAG requirement, and skills must be used in each agent assignment prompt.
9. Require the agent to read the relevant rules and the selected skill's `SKILL.md` completely before editing code, creating documentation, or running tests.
10. If no relevant skill exists, record why no skill was used; project rules and Memory First/RAG First still always apply.
11. Do not copy or create duplicate skills, rules, prompts, or workflows in another folder when the matching item already exists in the project.
12. When reviewing agent output, verify that the report names the rules and skills used, shows evidence that the instructions were read, shows Memory/RAG evidence when context was needed, and confirms compliance with those rules and skills.

Example skill assignment:

| Work type | Preferred skills |
|---|---|
| Memory context retrieval | `./.agents/skills/project-rag-search` |
| Project memory update after phase completion | `./.agents/skills/project-memory-update`, `./.agents/skills/vir-memory-update` |
| Workflow initialization or resume | `./.agents/skills/initialize-workflow`, `./.agents/skills/resume-workflow`, `./.agents/skills/workflow-runtime` |
| Brainstorming and planning | `./.agents/skills/brainstorming`, `./.agents/skills/brainstorming-to-plan`, `./.agents/skills/plan-to-blueprint` |
| Blueprint implementation | `./.agents/skills/blueprint-to-implementation`, `./.agents/skills/implementation-to-debug` |
| Debugging and verification | `./.agents/skills/debug-to-verify`, `./.agents/skills/vir-verify`, `./.agents/skills/vir-investigate` |
| Frontend or UI work | `./.agents/skills/frontend-design`, `./.agents/skills/frontend-visual-debug`, `./.agents/skills/web-design-guidelines` |

## 4. Language Rules

The coordinator and all agents must follow these language rules:

1. **Communicate with Ba in Vietnamese**: progress updates, questions, errors, final results, and coordination decisions must be written in Vietnamese.
2. **Write analysis and design documents in English**: documents such as brainstorming, plans, blueprints, ADRs, specifications, architecture notes, technical checklists, and design artifacts must be written entirely in English.
3. **Write report and result documents in Vietnamese**: documents such as implementation reports, debug reports, QA reports, verification reports, phase reports, test results, review results, readiness results, and final results must be written in Vietnamese so Ba can review them and make decisions quickly.
4. **Agent task prompts may use English**: when assigning work to Antigravity or another agent, prefer English for consistency with analysis and design documentation.
5. **Do not mix languages against the document type**: analysis/design documents use English; report/result documents use Vietnamese. If a document needs to quote logs, command output, or JSON results, keep the technical excerpt unchanged and explain it in the document's primary language.
6. **Do not translate technical identifiers**: keep command names, paths, classes, and files unchanged, such as `settings.get`, `qa_results.json`, and `SettingsCommandHandler`.
7. **After creating or updating documentation, summarize it in Vietnamese in chat**: the response to Ba must briefly state what document was created or updated, its purpose, the key points, related files, and verification status so Ba can quickly understand the content.

## 5. Real Runtime Validation Rules

Unit tests, reflection tests, or direct class calls inside a test process count only as supporting checks.

A phase is considered real-QA-ready only when all steps that match the module type are satisfied. The real surface may be an API endpoint, UI route, CLI command, background service, SDK call, database integration, message bus, job queue, plugin host, or workflow runtime.

1. Rebuild the app.
2. Launch the real app, service, UI, CLI, or worker runtime involved in the phase.
3. Let the runtime create or expose the real integration surface, such as an HTTP endpoint, UI route, CLI command, SDK entrypoint, message bus, plugin host, or job queue.
4. Connect to the real surface from an external client or driver process.
5. Send real commands, requests, or actions to the running runtime.
6. Verify real responses.
7. Snapshot and restore any data modified by tests.
8. Stop the app after all test cases complete.
9. Write sanitized artifacts.

If multiple runtime cases must run in parallel, **the main coordinator must own the app/runtime lifecycle**:

- The main coordinator launches the app, service, or runtime once.
- Client cases only connect to the already-running runtime.
- Client cases must not launch the runtime.
- Client cases must not stop the runtime.
- The main coordinator stops the runtime only after all cases finish.

This prevents one test case from shutting down the runtime while another case is still running. For API, UI, CLI, service, SDK, message bus, or plugin-host work, the same rule applies to the server, browser session, command runner, worker process, or runtime host.

## 6. Path Policy

New or edited source, scripts, artifacts, and documentation must use relative paths only.

Allowed examples:

```text
./docs/guides/example.md
src/bin/Release/MyApp.exe
dist/phase-02/results/qa_results.json
```

Forbidden examples:

```text
<absolute-drive-path>
<absolute-file-url>
<macos-absolute-path>
<linux-absolute-path>
```

If the app or a tool returns an absolute path, the artifact must sanitize it before saving, for example:

```json
{
  "path": "<abs-path>"
}
```

If a real absolute path is found in phase source, artifacts, or documentation, the phase fails even if all tests pass.

## 7. Readiness and Readability Score

Score on a 100-point scale. A phase may pass the gate only when the total score is at least 95 and the path policy is not violated.

| # | Criterion | Points | Full-score requirement |
|---|---|---:|---|
| 1 | Path compatibility | 30 | All source, scripts, artifacts, and docs use relative paths or sanitized placeholders. No absolute file URL, drive path, macOS absolute path, Linux absolute path, token leak, or log path leak. |
| 2 | Build and real runtime launch | 20 | The app, service, UI, CLI, or worker rebuilds successfully, the real runtime starts, the real integration surface is ready, and no process remains after testing. |
| 3 | Real runtime QA | 20 | Tests call the running runtime through the appropriate real surface, such as API, UI, CLI, SDK, message bus, job queue, plugin host, or service, not only unit or reflection tests. Main success paths, valid error paths, regression paths, and cleanup all pass. |
| 4 | Functional completeness | 15 | The phase implements every required command or API, has no unfinished placeholders, and does not miss important legacy behavior. |
| 5 | Readability and maintainability | 5 | Source, scripts, and artifacts are clear, structured, well named, minimally duplicated, and scoped to the phase. |
| 6 | Project rule, Memory/RAG, and skill compliance | 5 | The coordinator and agents read the project rules, used Memory First/RAG First through `./.agents/skills/project-rag-search` when context was needed, selected relevant skills from `./.agents/skills`, read skill instructions before work, recorded rules/skills in prompts/reports, and did not create duplicate rules or skills elsewhere. |
| 7 | Data safety and cleanup | 5 | Tests snapshot and restore settings, create no desktop or runtime junk, leak no token or secret, and leave no app or test process behind. |

## 8. Additional Scoring Methods

In addition to the readiness and readability score, each phase should use the following 100-point quality scores. Each main score must be at least 95/100 for the phase to pass. If a hard blocker exists inside a score category, that category must fail even when the component total appears high enough.

### 8.0. Phase Applicability

Not every phase is allowed to build, launch the app, or run real runtime tests. The coordinator must choose the scoring mode for the phase before assigning work to an agent.

| Phase type | Main goal | Run real runtime? | How to score Real Runtime Validation Score |
|---|---|---|---|
| Brainstorming | Discover requirements, legacy context, risks, scope, and open questions. | No, unless Ba explicitly requests it. | Score the **runtime validation strategy**: future surface to test, data to snapshot, expected success/error/regression cases, runtime risks. |
| Planning | Define scope, rollout order, dependencies, acceptance criteria, and test plan. | No, unless Ba explicitly requests it. | Score the **runtime validation strategy**: build/test plan, runtime type to launch later, artifacts to produce, pass/fail criteria. |
| Blueprint | Define technical contracts, API/command/UI/SDK surface, data model, and test design. | No, unless Ba explicitly requests it. | Score the **runtime validation strategy**: test matrix, input/output contract, error cases, cleanup plan, security/privacy checks. |
| Implementation | Edit source code and integrate the feature. | Yes, when the change has a runtime surface. | Score with **runtime evidence**: real build, real runtime launch, real surface call, snapshot/restore, sanitized logs/results, cleanup. |
| Debug | Fix defects after implementation. | Yes, when the defect involves runtime or integration behavior. | Score with **runtime evidence** after the fix. |
| Verification | Final phase validation. | Yes, unless the phase only produces documentation and changes no runtime. | Score with **runtime evidence**, or strategy-only evidence when the phase is documentation-only. |
| Release-readiness | Check release readiness without releasing unless Ba approved it. | Yes, when the release artifact has runtime behavior. | Score with **runtime evidence**, plus artifact manifest and known risks. |

Mandatory rule: agents **must not build, launch the app, start servers, open browsers, or run real runtime tests** during brainstorming, planning, or blueprint phases unless Ba explicitly asks for it. In these documentation phases, agents only design the runtime validation strategy for later phases.

| # | Score type | 100-point method | Hard fail condition |
|---|---|---|---|
| 1 | Architecture Compliance Score | 25 points for correct boundaries; 20 points for correct workflow runtime, DDD, or Clean Architecture; 20 points for dependency direction and ownership; 20 points for module contract consistency; 15 points for no critical architecture violations. | The frontend calls storage, a system bridge, or an internal runtime directly when rules require a facade; a module breaks ownership boundaries; any critical architecture violation exists. |
| 2 | Functional Coverage Score | 30 points for required use cases; 25 points for required command/API/UI surface; 20 points for valid error paths, edge cases, and validation; 15 points for required data states; 10 points for no release-blocking placeholders or TODOs. | A core requested feature is missing; a required API or command is not implemented; a main path still contains a placeholder. |
| 3 | Real Runtime Validation Score | For brainstorming/planning/blueprint: score 100 points for the runtime validation strategy, without running the real runtime. For implementation/debug/verification/release-readiness: 20 points for real build and startup; 20 points for calling the real surface such as API, UI, CLI, SDK, service, message bus, plugin host, or job queue; 20 points for success, valid error, and regression paths; 15 points for data snapshot/restore; 15 points for sanitized logs/results; 10 points for cleanup with no hanging process. | In documentation phases: concrete runtime validation strategy is missing. In runtime-required phases: only unit tests exist, no real runtime is launched, no real surface is called, a process remains, or test data is not restored. |
| 4 | Security & Privacy Score | 20 points for correct auth boundaries; 20 points for masking secrets, tokens, cookies, licenses, proxies, and captcha keys; 20 points for dangerous-operation guardrails; 15 points for input validation and abuse resistance; 15 points for safe audit/log behavior; 10 points for no PII or machine-info leak. | A real secret leaks; `security_token` is treated as an authentication boundary; auth/session validation is bypassed; logs contain unsanitized PII or tokens. |
| 5 | Legacy Parity Score | 30 points for legacy inventory; 25 points for primary behavior parity; 20 points for old data/config compatibility; 15 points for migration or backward compatibility; 10 points for documented gaps. | A critical legacy feature is missing; old behavior changes without a design decision; data compatibility is broken. |
| 6 | Integration Compatibility Score | 25 points for upstream/downstream contracts; 20 points for correct shared config consumption; 20 points for concurrency and lifecycle handling; 15 points for consistent error taxonomy; 10 points for SDK/version compatibility; 10 points for real integration tests. | A module consumes the wrong contract; dependent modules break; a required UI/backend/server/runtime bridge is missing. |
| 7 | Operational Safety Score | 20 points for coordinator-owned runtime lifecycle; 20 points for safe idempotency/retry; 20 points for cleanup/rollback; 15 points for resource limits; 15 points for failure containment; 10 points for monitoring or health evidence. | A lane stops another lane's runtime; tests damage data; risky changes have no rollback path. |
| 8 | Documentation Traceability Score | 20 points for requirement-to-plan/blueprint trace; 20 points for blueprint-to-implementation trace; 20 points for implementation-to-test evidence trace; 20 points for clear report/result evidence; 10 points for known risks; 10 points for relative artifact links. | The source requirement cannot be traced; test evidence is missing; an artifact uses an absolute path. |

Detailed scoring rule: a sub-item earns points only when concrete evidence exists in source code, documentation, report/result artifacts, or test output. Do not award points by intuition. Do not use points from one score category to compensate for a blocker in another category.

### 8.1. Architecture Compliance Score

| Sub-item | Points | Full-score method |
|---|---:|---|
| Correct boundary | 25 | UI does not call storage, a system bridge, or an internal runtime directly when rules require a facade; each module edits and exposes only its owned area. |
| Correct workflow runtime and architecture | 20 | The task uses the matching workflow runtime and skill; backend follows DDD/Clean Architecture when applicable; project rules are not bypassed. |
| Correct dependency direction | 20 | Higher layers depend through contracts, interfaces, or facades; no circular dependency or reverse-layer import is introduced. |
| Correct module contracts | 20 | Requests, responses, error codes, config, events, and lifecycle behavior match the approved design or legacy contract. |
| No critical violation | 15 | No severe architecture issue exists, such as auth bypass, facade bypass, direct storage writes outside ownership, or dependent-module breakage. |

### 8.2. Functional Coverage Score

| Sub-item | Points | Full-score method |
|---|---:|---|
| Required use cases | 30 | Every use case from the original request, plan, or blueprint has implementation and evidence. |
| Command/API/UI surface | 25 | Every required command, endpoint, UI action, SDK method, or workflow entrypoint exists and has a clear contract. |
| Error paths and edge cases | 20 | Invalid input, empty state, provider failure, timeout, permission failure, and invalid data are validated. |
| Data states | 15 | Create/read/update/delete, intermediate states, retry, rollback, or persistence are handled according to the module. |
| No release-blocking placeholder | 10 | No TODO, stub, mock, or hardcode remains in the main path unless the blueprint explicitly allows it and the report records the risk. |

### 8.3. Real Runtime Validation Score

| Sub-item | Points | Full-score method |
|---|---:|---|
| Correct runtime mode | 10 | Brainstorming/planning/blueprint records `strategy-only`; implementation/debug/verification/release-readiness records `runtime-evidence` when a runtime surface exists. |
| Clear runtime surface or strategy | 20 | Documentation phases describe the future surface to test; runtime phases call a real API, UI, CLI, SDK, service, message bus, plugin host, or job queue. |
| Build/startup or build/startup plan | 15 | Documentation phases define how build/startup will run later; runtime phases perform a real successful build and startup. |
| Main, error, and regression paths | 20 | Documentation phases design success/error/regression cases; runtime phases provide evidence that those cases ran. |
| Data snapshot/restore | 15 | Documentation phases define data to snapshot/restore; runtime phases snapshot before execution and restore afterward. |
| Sanitized logs/results | 10 | Documentation phases define artifact scrubbing rules; runtime phases produce artifacts with no token, secret, PII, machine info, or absolute path. |
| Process cleanup | 10 | Documentation phases define cleanup/lifecycle ownership; runtime phases leave no app, worker, browser, server, test client, or file lock behind. |

### 8.4. Security & Privacy Score

| Sub-item | Points | Full-score method |
|---|---:|---|
| Correct auth boundary | 20 | Session token, Bearer token, ACL, permission, and confirmation factor are clearly separated; `security_token` is not treated as an auth boundary. |
| Secret masking | 20 | Cookies, passwords, licenses, proxy credentials, captcha keys, API tokens, and session tokens are masked in UI/report/log output. |
| Dangerous-operation guardrails | 20 | Dangerous commands use confirmation, dry-run when needed, audit, rate limit, or permission checks according to module rules. |
| Input validation and abuse resistance | 15 | Schema validation, size limits, path traversal guards, timeouts, retry limits, and dangerous-data rejection are present. |
| Safe audit/log behavior | 15 | Logs are sufficient for tracing but do not leak secrets; security errors explain safe reasons without exposing sensitive data. |
| No PII or machine-info leak | 10 | Artifacts do not store usernames, emails, hostnames, internal IPs, machine paths, or personal domains. |

### 8.5. Legacy Parity Score

| Sub-item | Points | Full-score method |
|---|---:|---|
| Legacy inventory | 30 | Related legacy features, old forms, old commands, old config, old data, and old behavior are inventoried. |
| Primary behavior parity | 25 | New behavior produces equivalent results to the legacy flow for primary use cases. |
| Data/config compatibility | 20 | Old data can be read, written, or migrated correctly; profiles, accounts, proxies, captcha, licenses, and settings are not broken. |
| Migration/backward compatibility | 15 | A migration step, adapter, fallback, or shim exists when old and new contracts differ. |
| Documented gaps | 10 | Every remaining parity gap has a risk level, reason, and next action. |

### 8.6. Integration Compatibility Score

| Sub-item | Points | Full-score method |
|---|---:|---|
| Upstream/downstream contracts | 25 | The module uses the correct input, output, and error contracts from foundation and dependent modules. |
| Correct shared config consumption | 20 | The module consumes shared settings, license, captcha, proxy, or i18n config from the correct owner and does not hardcode it. |
| Concurrency and lifecycle | 20 | There is no race, double-start, double-stop, or unauthorized shutdown of shared runtime; locks or queues exist when needed. |
| Consistent error taxonomy | 15 | Errors use the shared code, message key, severity, and response format. |
| SDK/version compatibility | 10 | SDK, API facade, command surface, and client samples are compatible with the current version. |
| Real integration tests | 10 | At least one real test crosses two modules or layers, such as UI-to-backend, backend-to-service, SDK-to-server, or client-to-runtime. |

### 8.7. Operational Safety Score

| Sub-item | Points | Full-score method |
|---|---:|---|
| Coordinator-owned lifecycle | 20 | The main lane starts and stops the runtime; helper lanes do not manage shared lifecycle directly. |
| Safe idempotency/retry | 20 | Re-running tests or commands does not duplicate data or corrupt state; retries are bounded. |
| Cleanup/rollback | 20 | Artifacts, processes, file locks, config, and mid-run failures have cleanup or rollback handling. |
| Resource limits | 15 | Timeouts, parallelism limits, file/log size limits, and phase-folder isolation are enforced. |
| Failure containment | 15 | Failure in one lane does not damage another lane; provider failure does not crash the whole runtime. |
| Health/monitoring evidence | 10 | Health checks, status reports, progress logs, or evidence show the runtime remains healthy after testing. |

### 8.8. Documentation Traceability Score

| Sub-item | Points | Full-score method |
|---|---:|---|
| Requirement to plan/blueprint trace | 20 | Every main requirement maps to a plan, blueprint, or decision. |
| Blueprint to implementation trace | 20 | Every changed file, command, or API maps back to a design section or decision. |
| Implementation to test trace | 20 | Every main behavior has test evidence or a clear reason why it was not tested. |
| Report/result evidence | 20 | Vietnamese report/result artifacts state score, PASS/FAIL, commands run, artifacts, and remaining risks. |
| Known risks | 10 | Remaining risks include severity, impact, and next action. |
| Relative artifact links | 10 | All artifact links use relative paths, with no absolute path or file URL. |

The phase decision must not use averaging to hide a failed category. The pass rule is:

```text
phase_pass =
  readiness_score >= 95
  AND architecture_score >= 95
  AND functional_score >= 95
  AND runtime_validation_score >= 95
  AND security_privacy_score >= 95
  AND legacy_parity_score >= 95
  AND integration_compatibility_score >= 95
  AND operational_safety_score >= 95
  AND documentation_traceability_score >= 95
  AND no_mandatory_failure
```

The meaning of `runtime_validation_score` depends on the phase: in brainstorming/planning/blueprint it scores the runtime validation strategy; in implementation/debug/verification/release-readiness it scores real runtime evidence. If a score does not apply to the phase, the coordinator must mark it `NOT APPLICABLE` and record why. `NOT APPLICABLE` must not be used for runtime validation, security/privacy, path policy, rule/skill compliance, or documentation traceability.

## 9. Mandatory Failure Conditions

A phase must fail or stop if any of the following occurs:

1. A real absolute path exists in phase source, scripts, artifacts, or documentation.
2. Build fails.
3. The app cannot launch.
4. The real runtime integration surface is not ready, such as API endpoint, UI route, CLI command, SDK entrypoint, message bus, plugin host, or service health.
5. A required runtime case fails.
6. Testing is only unit or reflection based and has not called the real runtime.
7. An app or test process remains after QA completes.
8. Artifacts contain tokens, secrets, or unsanitized data.
9. A lane stops the app, service, or runtime without permission from the main coordinator.
10. An agent reports success without enough evidence.
11. An agent skips a relevant skill under `./.agents/skills` without a coordinator-approved reason.
12. An agent creates a duplicate skill, prompt, or workflow elsewhere when the project already has the matching skill.
13. An agent skips project rules or cannot prove that required rules were read before work.
14. An agent creates parallel rules that drift from `PROJECT_RULES.md`, `./.agents/AGENTS.md`, or `./.agents/AI_RULES.md`.
15. An agent scans source code or asks for design guidance before using Project Memory and `./.agents/skills/project-rag-search` when the task needs context.

## 10. Phase Report Template

```markdown
## Phase Status

- Phase: <module>/<phase-name>
- Status: PASS | FAIL | BLOCKED
- Score: <score>/100
- Architecture Compliance Score: <score>/100 | NOT APPLICABLE
- Functional Coverage Score: <score>/100 | NOT APPLICABLE
- Real Runtime Validation Score: <score>/100 (strategy-only | runtime-evidence)
- Security & Privacy Score: <score>/100
- Legacy Parity Score: <score>/100 | NOT APPLICABLE
- Integration Compatibility Score: <score>/100 | NOT APPLICABLE
- Operational Safety Score: <score>/100
- Documentation Traceability Score: <score>/100
- Build if phase requires it: PASS | FAIL | NOT APPLICABLE
- Real Runtime Launch if phase requires it: PASS | FAIL | NOT APPLICABLE
- Real Runtime QA if phase requires it: PASS | FAIL | NOT APPLICABLE
- Path Policy: PASS | FAIL
- Project Rules and Skills: PASS | FAIL
- Memory/RAG First: PASS | FAIL | NOT APPLICABLE
- Cleanup: PASS | FAIL

## Evidence

- QA case: `dist/<phase>/results/qa_case.json`
- QA result: `dist/<phase>/results/qa_results.json`
- Runner: `dist/<phase>/run-main-coordinator-real-validation.ps1`
- Rules used: `PROJECT_RULES.md`, `./.agents/AGENTS.md`, `./.agents/AI_RULES.md`
- Memory/RAG used: `./.agents/skills/project-rag-search/SKILL.md`
- Skills used: `./.agents/skills/<skill-name>/SKILL.md`

## Notes

- What passed:
- What failed:
- What was fixed:
- Remaining risks:
- Coordinator decision:
```

After creating a report or technical document, the coordinator must reply to Ba in Vietnamese. The English guide records the required message shape as follows:

```markdown
Created or updated:

- `<document-path>`: main purpose.

Quick summary:

- Key point 1.
- Key point 2.
- Key point 3.

Verification:

- Path policy: PASS | FAIL
- Build/test if applicable: PASS | FAIL | NOT APPLICABLE
- Project rules and skills: PASS | FAIL
- Memory/RAG First: PASS | FAIL | NOT APPLICABLE
```

## 11. Phase Promotion Decision

The coordinator may move to the next phase only when:

1. Readiness score and every required quality score are at least 95/100.
2. Path policy passes.
3. Build passes.
4. Real runtime QA against the running app, service, API, UI, CLI, SDK, message bus, job queue, plugin host, or runtime surface passes.
5. Cleanup passes.
6. Required project rules were read, applied, and recorded as evidence.
7. Memory First/RAG First was used when context was needed, or a reason for not applying it was recorded.
8. Relevant project skills were used or an approved reason for skipping them was recorded.
9. There are no blockers or severe risks.
10. Ba has approved continuing, or the current workflow explicitly allows automatic continuation.

If Ba asks to stop at the current phase, the coordinator must stop immediately and must not run the next phase.

## 12. Mandatory 5-Agent Coordination & Zero-Trust Review Policy

- **Minimum 5-Role Topology**: Every coordinated task MUST involve a minimum of 5 distinct operational roles:
  1. **Planner**: Defines specifications, user requirements, project scope, and phase planning.
  2. **Architect**: Designs system architecture, Technical Blueprints, API contracts, and data schemas.
  3. **Coder**: Executes source code modifications, refactoring, and bug fixes strictly within Blueprint scope.
  4. **Auditor**: Conducts independent code standard, architectural boundary, and compliance audits.
  5. **Manager**: Controls workflow execution gates, release risk, final quality validation, and delivery approval.
- **Zero-Trust Independent Review Rules**:
  - The Auditor and Manager MUST conduct reviews independently and asynchronously.
  - Rubber-stamping or trusting another agent's self-assessment is strictly prohibited.
  - The Auditor MUST independently verify code quality, linting, unit tests, and blueprint adherence.
  - The Manager MUST independently verify functional completion, integration readiness, risk factors, and compliance scores.
  - Neither Auditor nor Manager may approve a phase based on the Coder's or Planner's self-certification. Both Auditor PASS and Manager PASS approvals are required before proceeding to user approval gates.
