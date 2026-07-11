---
feature_id: FEAT-052
feature_name: Project-Level Permission Initialization and Manual Permission Mode Management
status: draft
stage: brainstorming
created_at: 2026-07-11
updated_at: 2026-07-11
previous_artifact: None
next_artifact: ../plans/FEAT-052_project_permissions_management_plan.md
---

# Master Requirement Document – Project-Level Permission Initialization and Manual Permission Mode Management

## 1. Feature ID & Name
- **Feature ID**: FEAT-052
- **Feature Name**: Project-Level Permission Initialization and Manual Permission Mode Management

## 2. Original Idea
```text
Add Project-Level Permission Initialization and Manual Permission Mode Management
The current behavior checks or requests permission repeatedly during workflow initialization. This is not desired.
The target behavior is:
1. Project permission mode is initialized exactly once by a manually executed CLI command.
2. The selected permission mode is persisted in a project JSON configuration file.
3. Skills and runtime commands only read and enforce the saved mode.
4. Skills must not ask for permission mode again on every run.
5. Permission mode changes must only happen through an explicit manually executed CLI command.
6. AI agents must never select, confirm, or change permission mode on behalf of the user.
7. Existing per-action approval gates must remain intact where required by policy.
```

## 3. Business Problem
- **Problem**: In the existing implementation, the AI Skill Framework checks or requests the project's permission mode (`sandbox` or `full_access`) repeatedly during workflow initialization (`initialize-workflow`). This repeated prompting disrupts flow, decreases developer experience, and introduces risk of AI agents self-selecting or escalating permission modes.
- **Why it matters**: Repeated prompting violates the security principle of explicit human authorization and creates friction during local development. AI agents should never have the power to elevate or modify their own permission boundaries.
- **Who is affected**: Developers (like Ba) using the local AI engineering workflow, and the AI agents executing task steps.
- **Expected outcome**: Permission mode is configured exactly once per project using a manual CLI subcommand, saved in a dedicated JSON file, and read statically on every run without further prompt.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Config file located at `.agents/config/permissions.json` representing project-level permission boundary.
  - FR-02: Support permission modes `sandbox` and `full-access`.
  - FR-03: Implement CLI subcommands under `aiwf permissions` (or equivalent):
    - `init`: Exactly once per project root, atomic creation, non-interactive fails if `--mode` is missing, default is `sandbox`.
    - `show`: Read-only print of initialized permissions configuration.
    - `change`: Escalation check, old vs new values, explicit confirmation `[y/N]` (default No), atomic overwrite, optimistic concurrency revision increment.
    - `validate`: JSON linter, schema correctness, legacy value overlap detection.
  - FR-04: Refactor `initialize-workflow` to load and validate permission mode, halting safely with setup command advice if missing.
  - FR-05: Refactor skills to treat the permission configuration as read-only.
- **Non-functional Requirements**:
  - NFR-01: The Visualizer can show the permission mode but must not perform write updates.
  - NFR-02: Test suites must use isolated configuration environments and not modify the project's real permissions file.
  - NFR-03: Backward compatibility with legacy session-embedded keys must be safely migrated during `init` or validate.

## 5. Requirement Traceability Matrix
| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Save permissions at `.agents/config/permissions.json` | Cấu hình permissions.json | Kiểm tra ghi tệp tin | Tệp tin được sinh ra đúng cấu trúc |
| FR-02 | Must | Support `sandbox` and `full-access` modes | Hỗ trợ các chế độ | Kiểm tra độ hợp lệ của giá trị | Chấp nhận sandbox, full-access |
| FR-03 | Must | Implement CLI subcommands under `workflow_runtime` | CLI subcommands | test_init_command, test_change_command | CLI hoạt động đầy đủ |
| FR-04 | Must | Refactor workflow init to block on missing config | Khởi tạo workflow | test_workflow_init_blocks | Dừng an toàn khi thiếu file |
| FR-05 | Must | Ensure skills treat mode as read-only | Chặn ghi từ skills | test_skills_read_only | Không ghi đè từ skill |

## 6. Stakeholder Analysis
| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Developer (Ba) | Primary | High | Critical | Improved UX, no annoying prompts, safe boundary definition |
| AI Coding Agents | Internal | Medium | High | Predictable execution context, read-only permissions mapping |

## 7. Scope Boundary
- **In Scope**:
  - Creating manual CLI commands for permissions administration.
  - Setting up atomic file write/replace logic.
  - Refactoring `initialize-workflow` and skills to consume the config.
  - Migrating legacy project session values.
- **Out of Scope**:
  - Overriding or weakening existing approval gates (such as Planning, Code modifications, Git, or Release approval gates).
  - Automatically escalating permissions on behalf of the user.

## 8. Dependency Graph Preview
- FEAT-052 Implementation Setup
  ├── Refactor state_store and session modules (to support read-only mode)
  ├── Implement permissions manager helper scripts
  ├── Implement CLI subcommands namespace (permissions namespace)
  ├── Refactor initialize-workflow skill
  └── Add test suite isolation validation

## 9. Data Flow Preview
- User CLI (manual command)
  └── writes atomic update ──> `.agents/config/permissions.json`
- Workflow Initialize CLI
  └── reads permissions.json ──> populates runtime context ──> feeds into Skills (Read-Only)

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Runtime Engine CLI | [workflow_runtime.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) | Refactor | Add `permissions` subcommand parser |
| Session module | [session.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/session.py) | Refactor | Clean up legacy permission mode prompts |
| Initialize Workflow | [initialize_workflow.py](file:///E:/AgentsProject/skills/initialize-workflow/scripts/initialize_workflow.py) | Refactor | Read permission mode and exit if uninitialized |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: `initialize-workflow`, `workflow-runtime`.
- **Affected Modules/Components**: CLI arguments parser, session store initialization, testing fixtures.
- **Impact Level**: Medium (affects security boundary initialization).

## 12. Migration Strategy
- During `aiwf permissions init`, detect legacy values from session/state store.
- Prompt the user with the legacy value and offer to migrate it to the config.
- Reject silent promotions of full-access.

## 13. Architecture Principles
- **Script First**: Enforced.
- **API First**: Expose helper methods for checking mode.
- **Memory First**: Resolved state read statically.

## 14. Non Goals
- Automating permissions changes.
- Eliminating manual verification steps.

## 15. ROI Analysis
- **Estimated Cost**: Low (minor Python script changes).
- **Runtime Savings**: Eliminates redundant questions, saving approximately 10-15 seconds per workflow start.

## 16. Success Metrics
- **Verification target**: 100% of permissions tests pass.
- **Prompt reduction**: 0 prompts on permissions during normal workflow initialization.

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Silent escalation of privileges | High | Low | Enforce strict confirmation gates and restrict write APIs | Developer |
| Concurrent CLI commands overwrite | Medium | Low | Integrate revision check and write-lock | Developer |

## 18. Technical Questions
- Should the config file have a validation hash or just json schema validation? JSON schema validation with optimistic concurrency revision is sufficient.

## 19. Open Decision Register
| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Subcommand namespace name | Resolved | Use `permissions` as the subcommand namespace |

## 20. ADR Detection
- **ADR Required**: No. Standard design is sufficient.

## 21. Knowledge Update Impact
- **project-summary**: Yes. Document permissions.json.
- **lessons**: Yes. Document test isolation override.

## 22. Test Strategy Preview
- Unit tests verifying initialization, validation, and change logic.
- Integration tests ensuring `initialize-workflow` aborts on missing configuration.

## 23. Extension Impact
- Visualizer UI shows the read-only permission mode correctly from runtime telemetry.

## 24. Complexity Estimation
- **Implementation Complexity**: Medium.
- **Estimated Refactoring Percentage**: 5%.

## 25. Roadmap Alignment
- **Milestones**: Deliver permissions CLI -> Refactor initialize-workflow -> Add tests -> Verify.

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Where should the config reside if not `.agents/config/`? | `.agents/config/permissions.json` is appropriate. |

## 27. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 28. Existing Project Context
- Refenced from [AI_RULES.md](file:///E:/AgentsProject/AI_RULES.md) (Section 15: Workspace Permission Mode Policy).

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| workflow_runtime.py | [workflow_runtime.py](file:///E:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) | Coder | CLI runner | 95% | 5% | Low | Parse permissions subcommands |

## 30. Solution Options Evaluated
- **Option A**: File-Based Single Config with CLI Operations (Selected).
- **Option B**: Database-embedded settings.

## 31. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Low | Medium |
| Risk | Low | Medium |
| Maintainability | High | Medium |
| Scalability | High | Low |

## 32. Selected Solution
- **Choice**: Option A.
- **Why Selected**: Fits exactly the constraints and provides the cleanest static mapping.

## 33. Risks & Assumptions
- Assumes the environment is local Windows or bash compatible.

## 34. Acceptance Criteria
- [ ] Permission mode configured exactly once per project.
- [ ] `initialize-workflow` stops safely on missing config.
- [ ] manual CLI commands successfully view and change permission mode.

## 35. Final Planning Prompt
Provide a complete, self-contained prompt to convert this Master Requirement Document into an Execution Plan under `docs/plans/FEAT-052_project_permissions_management_plan.md`.
- Objective: Map all functional requirements (FR-01 to FR-05) and verification test cases to concrete tasks.
- Target path: `docs/plans/FEAT-052_project_permissions_management_plan.md` and `docs/plans/FEAT-052_project_permissions_management_plan.json`.
