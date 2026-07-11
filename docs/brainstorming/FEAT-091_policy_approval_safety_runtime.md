---
feature_id: FEAT-091
feature_name: Policy & Safe Autonomy Runtime
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-091_policy_approval_safety_runtime_plan.md
---

# Master Brainstorming Document – Policy & Safe Autonomy Runtime (FEAT-091)

## 1. Executive Summary
This document designs the **Policy & Safe Autonomy Runtime**. It enforces system safety boundaries, manages dynamic approval scopes, and validates runtime operations against policies defined in `AI_RULES.md`. It regulates write permissions, git modifications, and release operations to prevent unsafe autonomous actions.

## 2. Background
Currently, safety policies (like the Approval Gate Policy and Permission Mode) are defined as text rules in `AI_RULES.md` and checked manually or via basic CLI prompts. An agent executing autonomously needs a runtime engine to dynamically enforce permission models, check path boundaries, and prompt the user for approvals.

## 3. Current Architecture Analysis
The current codebase has `approval_gate.py` and `permission_mode.py` under `skills/workflow-runtime/scripts`.
- It loads project permissions from `permissions.json`.
- It supports basic sandbox, full_access, and unrestricted modes.

## 4. Current Limitations
- **Static Checkpoints**: Lacks dynamic runtime hooks to intercept unsafe operations (e.g. executing unapproved terminal commands).
- **Loose Boundaries**: Path validations are manual; no centralized checker to catch absolute path violations.
- **Inflexible Approvals**: Prompt checks are all-or-nothing, which interrupts execution for trivial actions.

## 5. Objectives
- Establish a **Policy Enforcement Engine** to validate operations at runtime.
- Implement **Dynamic Approval Scopes** to balance user control and automation.
- Enforce strict **Git and Release Boundaries** during autonomous cycles.

## 6. Functional Requirements
- **FR-01: Operation Interception**: Intercept write, command-run, and git actions before execution.
- **FR-02: Policy Engine**: Match proposed operations against active rule profiles (`sandbox`, `full_access`).
- **FR-03: Scope Management**: Classify actions into approval categories (`implicit`, `ask_user`, `blocked`).
- **FR-04: Git Safeguards**: Block unapproved branching, commits, tag creations, or remote pushes.
- **FR-05: Release Verification**: Prevent release operations unless all verification criteria are met.

## 7. Non-Functional Requirements
- **NFR-01: Interception Overhead**: Operations validation must execute in `< 10ms`.
- **NFR-02: Safety-First Default**: Fail-secure behavior; block operations if evaluation errors occur.

## 8. Scope
- Policy Enforcement module (`policy_engine.py`).
- Approval scope manager and rules schema.
- System call interceptor hooks.
- Safety reporting tools.

## 9. Out of Scope
- OS-level user permission groups.
- Network-level sandbox enforcement (handled at Docker/sandbox layer).

## 10. Runtime Responsibilities
The Policy Runtime evaluates incoming operation requests, reads permission settings, prompts the user when required, and logs all safety verification outcomes.

## 11. Components
- `PolicyEnforcementEngine`: Validates operations against system rules.
- `ApprovalScopeManager`: Tracks user approval logs and current delegation states.
- `SafetyInterceptor`: Injected check hook running before tool execution.

## 12. Data Model
```json
{
  "permission_mode": "sandbox",
  "allowed_paths": ["."],
  "blocked_commands": ["rm -rf", "curl", "wget"],
  "rules": {
    "git_push": "require_approval",
    "file_write": "implicit"
  }
}
```

## 13. Runtime State
```
[Unverified] ──(evaluate rules)──> [Evaluating] ──(match)──> [Allowed]
                                           │
                                     (needs user)
                                           ▼
                                    [AwaitingUser] ──(Y)──> [Allowed]
                                                   ──(N)──> [Denied]
```

## 14. Event Flow
1. Coder agent requests to execute a git commit.
2. The runtime intercepts the git command.
3. The command is matched against the Git Safeguards policy.
4. The system detects that the commit target includes `memory-state.json`.
5. The transaction is flagged as `implicit` (approved automatically by rule) or `ask_user` depending on configuration.
6. If allowed, command executes; otherwise, execution blocks.

## 15. Sequence Flow
- Intercept action -> evaluate policies -> determine scope -> prompt user if needed -> execute or raise permission exception.

## 16. Dependencies
- State manager and process locking (from FEAT-051).

## 17. Integration Points
- CLI: `python workflow_runtime.py permission check`
- Configuration: `.agents/config/permissions.json`

## 18. Interaction with Executive Runtime
- The Executive loop routes all tool executions through the Policy & Safe Autonomy Runtime before dispatching.

## 19. Interaction with other features
- Restricts and audit-logs task executions managed by **Task Graph Engine (FEAT-087)**.

## 20. Security Considerations
- Prevent path-traversal attacks; block paths containing `..` or absolute prefixes outside the workspace.
- Scrub command arguments to prevent execution shell injection.

## 21. Performance Considerations
- Cache policy results to avoid repeating evaluation checks on identical tasks.

## 22. Scalability Considerations
- Design supports reading customized security policies from project configuration files.

## 23. Failure Scenarios
- **Policy Config Corrupted**: Fall back to strict sandbox mode (lock all operations except read).
- **User Rejects Action**: Cancel task execution, roll back changes, and notify the agent.

## 24. Recovery Strategy
On permission violations, log the event to the Event Journal, freeze the active execution thread, and prompt the user to choose between terminating the session or expanding privileges.

## 25. Migration Strategy
Parse and migrate existing values from `permissions.json` into the new policy configuration schema during initialization.

## 26. Backward Compatibility
Fall back to standard manual command confirmations if no custom security policies are defined.

## 27. Risks
- Privilege escalation via command injection. Mitigated by strict arguments tokenization.

## 28. Alternative Designs
- **Option A**: Hardcoded rules. (Rejected: prevents project-specific safety adjustments).
- **Option B**: Dynamic prompt-based safety agent. (Rejected: slow and vulnerable to jailbreaks).

## 29. Trade-offs
- Intercepting every tool call adds minor latency but guarantees security compliance.

## 30. Acceptance Criteria
- [ ] AC-01: Block command executions that violate the path boundary rules.
- [ ] AC-02: Successfully trigger prompt dialogs for actions in the `require_approval` scope.

## 31. Estimated Complexity
- Medium.

## 32. Blueprint Estimation
- 1 design blueprint (`docs/designs/FEAT-091_policy_approval_safety_runtime.md`).

## 33. Recommended Implementation Order
Implement sixth, following the Validation Runtime.
