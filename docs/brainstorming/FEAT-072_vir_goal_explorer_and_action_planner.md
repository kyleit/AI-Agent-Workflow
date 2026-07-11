<!-- docs/brainstorming/FEAT-072_vir_goal_explorer_and_action_planner.md -->

---
feature_id: FEAT-072
feature_name: Visual Intelligence Runtime — Goal Explorer & Action Planner
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: FEAT-071_vir_visual_to_source_code_mapper.md
next_artifact: ../plans/FEAT-072_vir_goal_planner_plan.md
---

# Master Requirement Document – VIR Goal Explorer & Action Planner

## 1. Feature ID & Name
- **Feature ID**: FEAT-072
- **Feature Name**: Visual Intelligence Runtime — Goal Explorer & Action Planner

## 2. Original Idea
Design the Goal Explorer & Action Planner system for VIR. It extracts verification objectives from blueprints, plans, and specifications, translates them into goal structures, compiles dynamic interaction path graphs, and directs the Touch Engine to explore application states safely.

## 3. Business Problem
- **Problem**: Scripted E2E tests break when layout structures modify, rendering procedural automation fragile. Procedural scripts cannot discover edge-case bugs, explore alternative paths, or handle popups dynamically.
- **Why it matters**: Goal-directed exploration translates specifications to visual outcomes. By focusing on *what* to verify rather than *how* to click, VIR remains resilient against minor frontend changes.
- **Who is affected**: Touch Engine, Digital Twin, Cognitive Engines, Quality Gate, CI/CD runners.
- **Expected outcome**: An action planner that dynamically maps out state transitions, calculates paths, detects loops, checks safety, and guides the Touch Engine to satisfy verification goals.

## 4. Requirement Discovery

### Functional Requirements
- **FR-01: Goal Extraction:** Parse specifications, blueprints, and test briefs into structured verification objectives containing preconditions, postconditions, and target states.
- **FR-02: User-Journey Discovery:** Automatically map out user journeys based on the targets extracted (e.g. `Login -> Shop -> Cart -> Checkout`).
- **FR-03: State-Aware Action Planning:** Maintain a State Transition Graph where nodes represent page routes/layouts (using DOM fingerprints) and edges represent interaction selectors (buttons, inputs).
- **FR-04: Dynamic Path Exploration:** Calculate optimal interaction sequences using path-finding algorithms (e.g., A*, Dijkstra) to navigate from the current state to the target verification state.
- **FR-05: Route & Form Discovery:** Discover input forms and routes dynamically; auto-fill inputs with seeded dummy data.
- **FR-06: Action Safety Classification:** Classify every action as SAFE (idempotent click/navigation) or UNSAFE (mutates data, submits charge, deletes records).
- **FR-07: Idempotency & Destructive-Action Blocking:** Intercept and block destructive actions unless explicitly authorized by the security policy.
- **FR-08: Credential & Permission Boundaries:** Enforce execution limits based on user role permissions (e.g., verify that user A cannot click admin links).
- **FR-09: Recovery, Rollback & Backtracking:** If an action leads to a dead-end or error page, backtrack to the last stable graph state, refresh the page, or restore database baselines (via FEAT-070).
- **FR-10: Exploration Budgets:** Enforce session limits (max duration, max clicks, max steps) to prevent resource exhaustion.
- **FR-11: Loop & Dead-End Detection:** Stop and alert when cyclic loops occur (e.g. clicking back and forth between two pages) or when no outbound edges exist.
- **FR-12: Alternative-Path Generation:** If a primary path is blocked, generate alternate routes to verify the same target.
- **FR-13: Human-Behavior Simulation (Mode B integration):** Supply seeded, randomized movements and timings to simulated actions when exploring paths.
- **FR-14: Deterministic Replay:** Re-run identical path sequences using the recorded action seed for debugging.
- **FR-15: Coverage Scoring:** Calculate overall exploration coverage (percentage of spec targets visited, DOM tree coverage).
- **FR-16: Unreachable-State Reporting:** Publish `goal.unreachable` when target state cannot be reached after exhausting all routes.
- **FR-17: Hand-off to Touch Engine:** Expose planned action sequences as step arrays consumed by the Touch Engine.
- **FR-18: Human Approval Requirements:** Request confirmation before taking actions flagged as destructive or outside the safety policy.

### Non-functional Requirements
- **NFR-01: Path-finding Overhead:** Path calculations completed in under 100ms per action step.
- **NFR-02: Graph Scalability:** Support state transition graphs with up to 100 distinct layout nodes.
- **NFR-03: Replay Consistency:** 100% path reproducibility when using the same seed and starting state.

### Technical Constraints
- TC-01: State signature hashes derived from page route + clean DOM layout fingerprint.
- TC-02: Exploration graphs persisted in memory during execution and stored in SQLite `vir_exploration_graphs` table.
- TC-03: Security policies defined in `.agents/visual-runtime/config/safety.yaml`.

## 5. Requirement Traceability Matrix

| Req ID | Priority | Description | Related Blueprint | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Goal extraction | BP-VIR-020 | Parse user login spec | Produces login precondition object |
| FR-03 | Must | State Transition Graph | BP-VIR-020 | Navigate 3 page routes | Graph records 3 nodes and transition edges |
| FR-04 | Must | Dynamic path-finding | BP-VIR-020 | Path request: Home to Cart | Returns click sequence to reach Cart |
| FR-06 | Must | Action safety | BP-VIR-020 | Check delete button action | Classifies action as UNSAFE |
| FR-07 | Must | Destructive action block | BP-VIR-020 | Attempt delete click without auth | Action blocked; approval requested |
| FR-09 | Must | Recovery / Backtracking | BP-VIR-020 | Click button resulting in 404 | Backtracks to previous healthy state |
| FR-11 | Must | Loop detection | BP-VIR-020 | Repeat click loop 4 times | Halts and emits loop warning |
| FR-14 | Must | Deterministic replay | BP-VIR-020 | Replay seed 123 | Executes identical action sequence |

## 6. Stakeholder Analysis

| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Touch Engine | Internal | Critical | Critical | Receives goal-directed actions instead of brittle scripts |
| Digital Twin | Internal | High | High | Visualizes current user location on navigation graph |
| Business Intelligence | Internal | High | High | Automated validation of multi-step business journeys |
| Security Review Agent | External | Medium | High | Enforces safety policy bounds |

## 7. Scope Boundary

### In Scope
- Goal extraction parser.
- State Transition Graph and A* pathfinder.
- Detour planning, backtracking, loop detection.
- Action safety checks, policy enforcement.
- Seeded path generation and deterministic replay logs.

### Out of Scope
- Direct browser click driver (Touch Engine handles driver commands).
- Natural language blueprint translation in MVP (YAML/JSON specs only).

### Deferred Scope
- AI-driven state exploration (Phase 12+).

## 8. Dependency Graph Preview
- FEAT-072: Goal Explorer & Action Planner
  - FEAT-056: Event Bus (prerequisite)
  - FEAT-059: Touch Engine (executes planner output)
  - FEAT-060: Digital Twin (inputs navigation/interaction state)
  - FEAT-064: Memory Engine (uses page layout fingerprints)

## 9. Data Flow Preview
- Specification loaded: "Check cart checkout flow"
  └── GoalPlanner compiles 3 ActionGoals: [Go to shop, Add item, Complete checkout]
      └── State graph detects current page = Home
          └── Path finder maps path: [Home -> ShopPage -> CartPage]
              └── Directs Touch: `click('#shop-link')`
                  └── Pop-up modal intercepts: "Newsletter signup"
                      └── Detour planner triggers: `click('#close-newsletter')` -> modal disappears
                          └── Resumes original path: `click('#shop-link')`

## 10. Existing Asset Analysis
- Reuses base process wrapping checks from `workflow_runtime.py`.
- Integrates stack detection using `project-profile.json` configuration structures.

## 11-13. Implementation Details
- **Contracts:** `GoalPlanner(Protocol)` interface.
- **Privacy:** Rejects resolution of files outside the git repository directory tree.
- **Failures:** Fallback locator searches for unique DOM IDs or class groupings if metadata is stripped.

## 14-16. Metrics & Business Value
- **Token savings**: Up to 40% reduction in debug discussion logs.
- **Efficacy**: 100% of visual bugs have corresponding code location references.

## 17. Risk Matrix
- *Risk:* Infinite loops in complex SPAs. *Mitigation:* Cyclic detection rules; hard exploration limits.
- *Risk:* Detour planner gets stuck on sticky modals. *Mitigation:* Visual detection backup; escalates to human.
- *Risk:* Dynamic route hashes pollute state graph. *Mitigation:* Strip random query params/hashes in state identifiers.

## 34. Acceptance Criteria
- [ ] AC-01: Generates 3-step action path graph from specification schema.
- [ ] AC-02: Dismisses unexpected alert modal and resumes target exploration path.
- [ ] AC-03: Warns and stops execution after 3 repeating cycle state actions.
- [ ] AC-04: Recovers navigation when dynamic elements changes their coordinate positions.

## 35. Final Planning Prompt
Provide design blueprints for GoalPlanner interface, A* path compilation, unexpected modal handling, and SQLite graph storage schemas.
