---
name: brainstorming
command: brainstorm
aliases:
  - idea
  - discover
category: workflow
tags:
  - requirements
  - discovery
  - brainstorming
version: 3.1.0
license: MIT
created_at: 2026-07-03
updated_at: 2026-07-09
description: Skill definition.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: lazy
  workspace_scan: none
  environment: none
  version: none
  provider: optional
  usage: cached---

# Skill: brainstorming

---

## ⚠ MANDATORY FIRST ACTION — DO THIS BEFORE ANYTHING ELSE

**When this Skill is invoked, the VERY FIRST thing you must do is output this table:**

| 🔒 DISCOVERY MODE ACTIVE |
| :--- |
| This Skill is running in **READ-ONLY / DISCOVERY ONLY** mode. |
| I will **NOT** modify any source code. |
| I will **NOT** edit any project files. |
| I will **NOT** implement anything. |
| I will **ONLY** perform Requirement Discovery. |
| The ONLY files I may write are under `docs/features/<feature-family>/brainstorming/`; for large or multi-phase features I may also write the required Roadmap under `docs/features/<feature-family>/roadmaps/`; I may update `docs/features/<feature-family>/README.md` as the feature index. |
| I will self-review discovery outputs before writing and will not ask for user approval unless information is missing or ambiguous. |

> This output is mandatory. Do not skip it. Do not abbreviate it.
> Output it BEFORE reading the user's requirement. Output it BEFORE any analysis.
> This is your behavioral commitment for this entire execution.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the aiwf Go Native CLI Engine (`aiwf`):
- **Validate Checkpoint**: Run `aiwf validate --checkpoint "exactly 2"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `aiwf start --skill "brainstorming" --command "brainstorm" --checkpoint 3 --step "Starting execution..."`
  - *Step Updates*: Run `aiwf step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `aiwf complete --checkpoint 3 --step "Step Complete" --next-skill "brainstorming-to-plan" --next-command "plan"` when execution finishes successfully.
  - *Failure*: Run `aiwf fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## Wrong Behavior Detection

**Before taking any action, check yourself:**

```
IF you are about to:
  ✗ Use write_file() on any path except `docs/features/<feature-family>/brainstorming/`, the matching `docs/features/<feature-family>/roadmaps/` for large/multi-phase features, or `docs/features/<feature-family>/README.md`
  ✗ Use edit_file(), replace_file(), or multi_replace_file()
  ✗ Run any shell command that modifies files
  ✗ Read source code files to find bugs to fix
  ✗ Generate a plan (docs/plans/) or blueprint (docs/blueprints/)
  ✗ Invoke or call another Skill
  ✗ Modify memory, changelog, or git history

THEN: STOP immediately.
You are about to violate DISCOVERY ONLY mode.
Return to the workflow sequence and ask the user for clarification instead.
```

**Correct behavior examples:**

| User says | WRONG response | CORRECT response |
|---|---|---|
| "Fix login bug" | Read login code, find bug, write fix | Treat as requirement, start discovery |
| "Optimize cache" | Edit cache implementation | Ask clarification questions, readiness score |
| "Add Redis" | Install Redis, write integration code | Analyze requirement, present 2-3 options |
| "The DB saves wrong" | Open repository.go, fix insert | Discover root cause as requirement, document options |

---

## Execution Mode

> [!CAUTION]
> **EXECUTION MODE: DISCOVERY ONLY — NON-NEGOTIABLE**
>
> Everything written after `/brainstorm` is a **REQUIREMENT INPUT**.
> This includes phrases like:
> - "Fix X" → a requirement to document, not a command to implement
> - "Implement Y" → a requirement to analyze, not code to write
> - "The bug is..." → a problem statement to discover, not a ticket to close
> - "DB saves wrong data" → a requirement scenario, not a bug to patch directly

---

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.
- **Skill Suggestion Gate Policy** (Section 14) - Raw requests require suggestion first; selected Skill requires confirmation.
- **Workspace Permission Mode Policy** (Section 15) - Sandbox mode is default; ask user to choose sandbox or full_access at init.

## Multi-Agent Contract

Runs under the Multi-Agent Workflow. Respect agent ownership and handoff rules defined in [agents/](../../agents/) and [runtime/](../../runtime/).

---

## Invocation

User invokes this Skill with requirements in free text. No YAML parameters.

```text
/brainstorm <requirements as free text>

Examples:
/brainstorm Add local cache for playwright static files.
/brainstorm Fix login bug.
/brainstorm Bulk insert support. CSV validation. Issue generation.
/brainstorm The DB saves multiline proxy input as a single row.
```

All text after the slash command is raw requirement input.
Do not parse it as YAML. Do not treat it as implementation commands.

---

## Feature ID Allocation Rule

Feature IDs are determined **ONLY** by scanning `docs/brainstorming/`:

1. Scan `docs/brainstorming/` for both shapes: flat files matching `FEAT-XXX_*.md` (3-digit number) AND feature-folders `docs/brainstorming/<feature-slug>/master/FEAT-XXX_*_master_brainstorming.md`.
2. Ignore: `docs/plans/`, `docs/blueprints/`, `docs/adr/`, memory, git history, `CHANGELOG.md`.
3. Empty directory (or only `.gitkeep`) → start at `FEAT-001`.
4. Files exist (either shape) → next ID = highest existing ID + 1.
5. Resume/Selection mode → reuse the Feature ID under discussion.

## Semantic Feature Folder Rule

Before writing any document, classify `<feature-family>` as a semantic product/domain capability by reading the user request, feature name, filename candidates, title, headings, summary/problem statement, and linked artifacts. Do not use `FEAT-*`, `FIX-*`, or `QUICK-*` IDs as folder names. If classification confidence is below 0.85, stop and report the candidate feature families with evidence.

## Document Shape Rule (single file vs. multi-phase folder)

This Skill produces one document under the semantic feature folder (`docs/features/<feature-family>/brainstorming/FEAT-XXX_feature_name.md`) by default — this covers the large majority of features. Use the **multi-phase folder shape** instead —
`docs/features/<feature-family>/brainstorming/master/FEAT-XXX_..._master_brainstorming.md` + one `docs/features/<feature-family>/brainstorming/phase-NN-<phase-slug>/phase-brainstorming.md` per phase — ONLY when, during Step 3–7 discovery, the feature genuinely decomposes into multiple, largely independent implementation phases (each with its own FR/NFR/AC set that could plausibly ship on its own), typically 4+ phases for a large system-level feature. Ask the user before switching shape if it's ambiguous — this is a real judgment call, not an automatic threshold.

If the multi-phase shape is chosen, Step 14 writes and reviews the Roadmap first under `docs/features/<feature-family>/roadmaps/FEAT-XXX_feature_slug_roadmap.md`, then Step 16 writes the master doc (feature-wide problem statement, stakeholder analysis, architecture principles, risk matrix, and an index of every phase with a one-paragraph summary + link), then one phase-brainstorming.md per phase (using the same template below, scoped to that phase's FR/NFR/AC only).

## Roadmap-First Rule for Large or Multi-Phase Features

For any large, multi-phase, system-level, cross-module, or high-risk feature, a reviewed Roadmap artifact is mandatory before Planning or Blueprint.

- Roadmap path: `docs/features/<feature-family>/roadmaps/FEAT-XXX_feature_slug_roadmap.md`.
- The Roadmap must be created before `docs/plans/` or `docs/blueprints/` artifacts.
- The Roadmap must include a complete feature inventory, phase breakdown, requirement-to-phase coverage matrix, dependencies, release slices, risks, and explicit "not missed" checks.
- The Roadmap must contain `Internal Review Evidence`.
- If the Roadmap review FAILS, fix only the failed points and re-review until PASS.
- If a later phase discovers a missing feature or phase, return to Roadmap first instead of patching the Plan/Blueprint directly.

> [!WARNING]
> Never pre-assign FEAT-XXX IDs during Feature Decomposition.
> Use temporary labels **Feature 1, Feature 2, Feature 3** until user confirms strategy.
> Assign FEAT-XXX IDs only in Step 15 when writing the final document.

---

## Workflow Sequence

Execute this sequence strictly. STOP only for real blockers: multiple independent features, readiness below threshold, missing information, or final workflow completion.

```
[ MANDATORY ] Output DISCOVERY MODE ACTIVE declaration block
              ↓
Step 1:  Receive User Input
              ↓
Step 2:  Feature Detection & Decomposition
         [→ STOP if multiple features detected, wait for user choice]
              ↓
Step 3:  Requirement Discovery
              ↓
Step 4:  Requirement Analysis
              ↓
Step 5:  Gap Analysis
              ↓
Step 6:  Impact Analysis
              ↓
Step 7:  Risk Analysis
              ↓
Step 8:  Project Context Analysis
         [memory-first; do NOT scan full repository]
              ↓
Step 9:  Project Memory Lookup
              ↓
Step 10: RAG Search
              ↓
Step 11: Calculate Requirement Readiness Score (0–100)
         [→ STOP if score < 85, ask clarification questions, wait for answers]
              ↓
Step 12: Generate 2–3 Solution Options + Comparison Table
              ↓
Step 13: Recommend One Option (with architectural reasoning)
              ↓
Step 14: Roadmap Gate (large/multi-phase only)
         [generate and review docs/features/<feature-family>/roadmaps/FEAT-XXX_feature_slug_roadmap.md; if FAIL, revise only failed points until PASS]
              ↓
Step 15: Internal Discovery Review Gate
         [review all discovery outputs; if FAIL, state failed points and revise only those points until PASS]
              ↓
Step 16: Generate Brainstorming Document(s)
              ↓
         STOP — Skill responsibility complete.
```

---

## Detailed Phase Instructions

---

### [ MANDATORY ] Discovery Mode Declaration

Output the following table verbatim as your very first response.
Do not modify it. Do not skip it. Do not summarize it.

| 🔒 DISCOVERY MODE ACTIVE |
| :--- |
| This Skill is running in **READ-ONLY / DISCOVERY ONLY** mode. |
| I will **NOT** modify any source code. |
| I will **NOT** edit any project files. |
| I will **NOT** implement anything. |
| I will **ONLY** perform Requirement Discovery. |
| The ONLY files I may write are under `docs/features/<feature-family>/brainstorming/`; for large or multi-phase features I may also write `docs/features/<feature-family>/roadmaps/<WORK_ITEM_ID>_<slug>_roadmap.md`; I may update `docs/features/<feature-family>/README.md` |
| I will self-review discovery outputs before writing and will not ask for user approval unless information is missing or ambiguous. |

Reading requirement input...

---

### Step 2: Feature Detection & Decomposition

Analyze the user input for one or multiple independent features.

**If multiple independent features are detected**, display:

```text
I detected the following independent features in your input:

  Feature 1: [Brief description]
  Feature 2: [Brief description]
  Feature 3: [Brief description]

These appear to be independent features.

How would you like to proceed?

  1. Generate one Brainstorming document for each feature (Recommended)
  2. Merge all into one single Brainstorming document
  3. Select specific features to continue with
```

**→ STOP. Wait for user response. Do not proceed until user selects an option.**

Rules:
- Never merge unrelated features automatically
- Never assign FEAT-XXX IDs here — use Feature 1, 2, 3 as temporary labels
- Proceed only after the user selects an option

---

### Steps 3–7: Requirement Discovery, Analysis, Gap, Impact, Risk

For each active feature, perform all five analyses:

- **Requirement Discovery**: Core problem, business value, target users, expected outcomes, success criteria, known constraints.
- **Requirement Analysis**: Functional requirements (FR-XX), non-functional requirements (NFR-XX), technical constraints (TC-XX).
- **Gap Analysis**: Missing information, ambiguous scope, unresolved assumptions.
- **Impact Analysis**: Affected systems, modules, services, databases, APIs.
- **Risk Analysis**: Technical, business, and operational risks.

Group by: *Functional · Business Rules · Technical · Performance · Security · UX*

> [!NOTE]
> Do NOT scan the full repository.
> Use Project Memory and RAG as the primary context sources.
> Read specific modules only when directly referenced by the requirement.
> Do NOT open source files looking for bugs to fix.

---

### Steps 8–10: Project Context, Memory & RAG

#### Memory & RAG Retrieval
Follow Memory First Policy (Section 3) and RAG Policy (Section 4) in [AI_RULES.md](../../AI_RULES.md). Consult `.agents/memory.config.json` and use project-summary/RAG lookup before scanning source files.

### Step 11: Requirement Readiness Score

Calculate the Requirement Readiness Score (0–100):

| Component | Max Score |
|---|---|
| Core problem defined | 20 |
| Target users identified | 10 |
| Functional requirements clear | 20 |
| Non-functional requirements clear | 15 |
| Technical constraints identified | 15 |
| Risks identified | 10 |
| Acceptance criteria defined | 10 |

**Display the score:**

```text
Requirement Readiness Score: [XX/100]
```

**If score < 85 — STOP:**

```text
Requirement Readiness Score: [XX/100] — Below threshold (85 required)

I need the following clarifications before proceeding:

[Functional]
  Q1. [Question]

[Technical]
  Q2. [Question]

[Non-functional]
  Q3. [Question]

No files will be generated until the readiness score reaches 85.
Please provide answers to continue.
```

→ **STOP. Wait for user answers. Do not proceed to Step 12.**

**If score ≥ 85:** Continue to Step 12.

---

### Step 12: Generate 2–3 Solution Options

Generate 2–3 **significantly different** architectural solutions.
Not minor variations — each option must represent a meaningfully different approach.

For each option:

```text
Option [A/B/C]: [Descriptive Name]

Overview:
  [High-level design — 2–4 sentences]

Architecture:
  [Affected layers, components, data flows, interfaces]

Advantages:
  - [Pro 1]
  - [Pro 2]

Disadvantages:
  - [Con 1]
  - [Con 2]

Complexity:          [Low | Medium | High]
Risk:                [Low | Medium | High] — [Key risk]
Performance:         [Latency, resource usage]
Maintainability:     [Long-term maintenance cost]
Compatibility:       [Integration with existing system]
Future Scalability:  [Growth capacity]
```

Follow with a comparison table:

| Criteria | Option A | Option B | Option C |
|---|---|---|---|
| Complexity | | | |
| Risk | | | |
| Performance | | | |
| Maintainability | | | |
| Compatibility | | | |
| Future Scalability | | | |
| Development Cost | | | |

---

### Step 13: Recommend One Option

Select one option with detailed reasoning. Not superficial ("it's simpler").

```text
Recommended Solution: Option [A/B/C] — [Name]

Architectural Reasoning:
  [Detailed justification — minimum 3 specific reasons]

Trade-offs:
  [What is gained, what is sacrificed]

Long-term Impact:
  [Effect on code maintainability and system evolution]

Technical Debt:
  [What debt this option introduces, if any]

Risk Mitigation:
  [How the key risks will be mitigated]
```

---

### Step 14: Roadmap Gate (Large or Multi-Phase Features Only)

When the feature is large or multi-phase, generate and review the Roadmap before the Brainstorming document is finalized.

Roadmap template:

```markdown
<!-- File path: docs/features/<feature-family>/roadmaps/FEAT-XXX_feature_slug_roadmap.md -->
---
artifact_type: roadmap
feature_id: FEAT-XXX
workflow: standard
status: reviewed
---

# Roadmap – [Feature Name]

## 1. Feature Inventory
| Feature / Capability | Priority | Included? | Phase | Notes |
|---|---|:---:|---|---|
| [Capability] | Must/Should/Could | Yes/No | Phase N | [Notes] |

## 2. Phase Roadmap
| Phase | Goal | In Scope | Out of Scope | Exit Criteria |
|---|---|---|---|---|
| Phase 1 | [Goal] | [Scope] | [Out] | [Criteria] |

## 3. Requirement-To-Phase Coverage Matrix
| Req ID | Requirement | Phase | Acceptance Criteria | Test Evidence Target |
|---|---|---|---|---|
| FR-01 | [Requirement] | Phase 1 | [AC] | [Expected test/report] |

## 4. Dependency Order
- Phase 1 -> Phase 2 -> Phase 3

## 5. Release Slices
| Slice | Included Phases | User Value | Release Risk |
|---|---|---|---|
| Slice 1 | Phase 1 | [Value] | [Risk] |

## 6. Not Missed Checklist
- [ ] Every user-requested capability is listed in Feature Inventory.
- [ ] Every FR/NFR/TC maps to exactly one primary phase.
- [ ] Every phase has exit criteria.
- [ ] Dependencies are ordered.
- [ ] Deferred items are explicitly listed.

## 7. Internal Review Evidence
| Field | Evidence |
|---|---|
| Reviewer Roles | Product Analyst / Planner / Architect / Reviewer / QC |
| Source Artifacts Reviewed | User request, active Skill, `AI_RULES.md`, memory/RAG/source references |
| Checklist Result | PASS/FAIL rows with concrete evidence |
| Failed Points | `None` or exact failed-point list |
| Revision Scope | `None` or exact sections revised |
| Re-review Count | `0` for first-pass PASS, otherwise number of repeated reviews |
| Document Compliance Score | `NN/100` |
| Relative Path Scan | PASS only when no local absolute paths exist |
| Final Result | `PASS` or `FAIL` |
```

Rules:
- Do not continue to Planning unless the Roadmap exists and review result is PASS.
- Missing roadmap for a large/multi-phase feature is a workflow BLOCKER.
- Missing Feature Inventory coverage, missing phase mapping, or missing Not Missed Checklist is review FAIL.

---

### Step 15: Internal Discovery Review Gate

Self-review the discovery output before writing the Brainstorming document.

Review checklist:
- User request and original intent are preserved.
- Requirement readiness is at least 85/100.
- Scope, non-goals, risks, assumptions, acceptance criteria, roadmap alignment, and final planning prompt are internally consistent.
- Traceability exists from user request to FR/NFR/TC, solution option, selected solution, and acceptance criteria.
- All artifact links and planned paths are project-relative.
- `document-compliance-assessment` no-go conditions are not present.
- If the work touches UI/UX, frontend components, layout, spacing, typography, color, animation, icons, visual hierarchy, aesthetic styling, or design-system decisions, `frontend-design` has been used and its relevant findings are reflected.

Rules:
- Do not stop for user approval at this gate.
- The generated Brainstorming document must contain `Internal Review Evidence`; missing evidence is review FAIL.
- The review must include a document-compliance score and a relative-path scan result.
- If review FAILS, state the exact failed points and revise only those points.
- Repeat review/revision until PASS.
- Continue to Step 16 only after review passes.

---

### Step 16: Generate Brainstorming Document(s)

After Internal Discovery Review PASS:

1. Scan `docs/brainstorming/` to calculate the next Feature ID.
2. Per the Document Shape Rule above, write either:
   - `docs/features/<feature-family>/brainstorming/FEAT-XXX_feature_name.md` (single-file shape — default), one per independent feature if decomposition was chosen, OR
   - `docs/features/<feature-family>/brainstorming/master/FEAT-XXX_..._master_brainstorming.md` + `docs/features/<feature-family>/brainstorming/phase-NN-<phase-slug>/phase-brainstorming.md` per phase (multi-phase shape).
3. For large/multi-phase features, ensure `docs/features/<feature-family>/roadmaps/FEAT-XXX_feature_name_roadmap.md` already exists and has review result PASS.
4. Create or update `docs/features/<feature-family>/README.md` with relative links to every artifact created for this feature family.
4. Use **relative paths only** for all artifact links.
5. Include an `Internal Review Evidence` section recording the discovery review result.

---

## Brainstorming Document Template

```markdown
<!-- Single-file shape:   docs/features/<feature-family>/brainstorming/FEAT-XXX_feature_name.md -->
<!-- Multi-phase master:  docs/features/<feature-family>/brainstorming/master/FEAT-XXX_..._master_brainstorming.md -->
<!-- Multi-phase phase:   docs/features/<feature-family>/brainstorming/phase-NN-<phase-slug>/phase-brainstorming.md (same template, scoped to that phase) -->

---
feature_id: FEAT-XXX
feature_name: Human Readable Name
status: draft
stage: brainstorming
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
previous_artifact: None
next_artifact: [relative path to the matching plan file/folder once created — see brainstorming-to-plan]
---

# Master Requirement Document – [Human Readable Name]

## 1. Feature ID & Name
- **Feature ID**: FEAT-XXX
- **Feature Name**: [Human Readable Name]

## 2. Original Idea
[Exact user input, unmodified]

## 3. Business Problem
- **Problem**: [What is broken, missing, or inefficient]
- **Why it matters**: [Business impact if unsolved]
- **Who is affected**: [Target users or systems]
- **Expected outcome**: [What success looks like]

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: [...]
  - FR-02: [...]
- **Non-functional Requirements**:
  - NFR-01: [Performance: ...]
  - NFR-02: [Security: ...]
  - NFR-03: [Availability: ...]
- **Technical Constraints**:
  - TC-01: [...]

## 5. Requirement Traceability Matrix
| Req ID | Priority (Must/Should/Could/Won't) | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | [...] | [...] | [...] | [...] |
| FR-02 | Should | [...] | [...] | [...] | [...] |

## 6. Stakeholder Analysis
| Stakeholder | Category (Primary/Secondary/Internal/External) | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| [...] | [...] | [...] | [...] | [...] |

## 7. Scope Boundary
- **In Scope**:
  - [...]
- **Out of Scope**:
  - [...]
- **Deferred Scope**:
  - [...]
- **Future Scope**:
  - [...]

## 8. Dependency Graph Preview
Provide a textual dependency tree of implementation order. (Do NOT generate Mermaid, use structured Markdown):
- Requirement/Module A (Must)
  └── Requirement/Module B (Should)
      └── Requirement/Module C (Could)

## 9. Data Flow Preview
Provide a textual logical data flow diagram. (Do NOT generate Mermaid, use structured Markdown):
- Component A
  └── passes data to ──> Component B
      └── updates ──> Component C

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation (Reuse/Extend/Refactor/Replace/Remove) | Rationale |
| :--- | :--- | :--- | :--- |
| [...] | [...] | [...] | [...] |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: [...]
- **Affected Modules/Components**: [...]
- **Affected Runtime**: [...]
- **Affected Extension**: [...]
- **Affected Scripts**: [...]
- **Affected Database**: [...]
- **Affected Documentation**: [...]
- **Impact Level**: [Low | Medium | High]

## 12. Migration Strategy
- **Backward Compatibility**: [...]
- **Adapter Strategy**: [...]
- **Coexistence Period**: [...]
- **Deprecation Plan**: [...]
- **Migration Phases**: [...]

## 13. Architecture Principles
- **API First**: [...]
- **Provider First**: [...]
- **Script First**: [...]
- **Memory First**: [...]
- **Incremental Updates**: [...]
- **Backward Compatibility**: [...]
- **Replaceable Providers**: [...]

## 14. Non Goals
- [...]

## 15. ROI Analysis
- **Estimated Implementation Cost**: [...]
- **Runtime Savings**: [...]
- **Token Reduction Target**: [...]
- **API Call Reduction Target**: [...]
- **Maintenance Impact**: [...]
- **Expected Break-Even**: [...]
- **Long-Term ROI**: [...]

## 16. Success Metrics
- **Latency Target**: [...]
- **Memory Usage Limit**: [...]
- **Startup Time Target**: [...]
- **Cache Hit Ratio Target**: [...]
- **Accuracy Target**: [...]
- **Token Reduction Target**: [...]
- **Expected ROI**: [...]

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| [...] | [...] | [...] | [...] | [...] |

## 18. Technical Questions
- [...]

## 19. Open Decision Register
| Topic / Decision | Current Status (Resolved/Pending/Requires ADR/Requires Prototype/Requires Research) | Rationale & Next Steps |
| :--- | :--- | :--- |
| [...] | [...] | [...] |

## 20. ADR Detection
- **ADR Required**: [Yes | No]
- **Rationale & Focus**: [...]

## 21. Knowledge Update Impact
Identify which Project Memory layers will change:
- **project-summary**: [Yes/No + Description]
- **architecture**: [Yes/No + Description]
- **modules**: [Yes/No + Description]
- **lessons**: [Yes/No + Description]
- **patterns**: [Yes/No + Description]
- **ADR**: [Yes/No + Description]
- **SQLite**: [Yes/No + Description]
- **indexes**: [Yes/No + Description]
- **vector metadata**: [Yes/No + Description]

## 22. Test Strategy Preview
- **Unit Tests**: [...]
- **Integration Tests**: [...]
- **Regression Tests**: [...]
- **Performance Tests**: [...]
- **Migration Tests**: [...]
- **Compatibility Tests**: [...]

## 23. Extension Impact
- **Extension UI Changes**: [...]
- **Affected ViewModels / Watchers**: [...]

## 24. Complexity Estimation
- **Implementation Complexity**: [Low | Medium | High]
- **Estimated Refactoring Percentage**: [...]

## 25. Roadmap Alignment
- **Roadmap Phase**: [...]
- **Milestones**: [...]
- **Prerequisites & Dependencies**: [...]

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| [Q1] | [A1 or "Pending"] |
| [Q2] | [A2 or "Pending"] |

## 27. Requirement Readiness Score
- **Score**: [XX/100]
- **Status**: [Ready ≥ 85 | Below Threshold < 85]

## 28. Existing Project Context
- **Memory Source**: [project-summary.md and RAG results referenced]
- **Existing Architecture Summary**: [Relevant patterns and decisions]

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk (Low/Med/High) | Relevance |
|---|---|---|---|---|---|---|---|
| [Module] | [Relative path] | [...] | [...] | [...] | [...] | [...] | [How it relates] |

## 30. Solution Options Evaluated

### Option A: [Name]
- **Overview**: [...]
- **Architecture**: [...]
- **Advantages**: [...]
- **Disadvantages**: [...]
- **Complexity**: [Low/Med/High]
- **Risk**: [Low/Med/High]
- **Performance**: [...]
- **Maintainability**: [...]
- **Compatibility**: [...]
- **Future Scalability**: [...]

### Option B: [Name]
[Same structure]

### Option C: [Name] (if applicable)
[Same structure]

## 31. Solution Comparison Table
| Criteria | Option A | Option B | Option C |
|---|---|---|---|
| Complexity | | | |
| Risk | | | |
| Performance | | | |
| Maintainability | | | |
| Compatibility | | | |
| Future Scalability | | | |
| Development Cost | | | |

## 32. Selected Solution
- **Choice**: Option [A/B/C] — [Name]
- **Why Selected**: [Detailed architectural reasoning]
- **Trade-offs Accepted**: [...]
- **Technical Debt**: [...]
- **Risk Mitigation**: [...]

## 33. Risks & Assumptions
- **Risks**:
  - R-01: [Risk] → [Mitigation]
  - R-02: [Risk] → [Mitigation]
- **Assumptions**:
  - A-01: [...]

## 34. Acceptance Criteria
- [ ] AC-01 (maps to [FR-XX]): [Description] (Expected Test: [...])
- [ ] AC-02 (maps to [NFR-XX]): [Description] (Expected Test: [...])

## 35. Final Planning Prompt

### Purpose
Complete, self-contained prompt for the `brainstorming-to-plan` Skill.
The Planning Agent must require no further clarification from this section.

### Problem Statement
[Detailed, precise problem description]

### Objectives & Selected Solution
[Core goals + chosen architectural option and its design]

### Functional Requirements
[Complete FR list with acceptance criteria]

### Non-functional Requirements & Constraints
[Performance targets, security requirements, scalability limits]

### Architectural Details
[Affected layers, data schemas, API contracts, interface definitions]

### Risks & Assumptions
[All identified risks and mitigations]

### Verification Checklist
- [ ] Implementation Plan generated and internally reviewed (docs/plans/, single-file or multi-phase shape)
- [ ] Technical Blueprint generated, internally reviewed, and ready for final Blueprint Approval (docs/blueprints/, single-file or multi-phase shape)
- [ ] All Acceptance Criteria mapped to implementation tasks

### Internal Review Evidence
| Field | Evidence |
|---|---|
| Reviewer Roles | Product Analyst / Requirement Analyst / Reviewer / QC / relevant Specialist roles |
| Source Artifacts Reviewed | User request, active Skill, `AI_RULES.md`, memory/RAG/source references |
| Checklist Result | PASS/FAIL rows with concrete section evidence |
| Failed Points | `None` or exact failed-point list |
| Revision Scope | `None` or exact sections revised |
| Re-review Count | `0` for first-pass PASS, otherwise number of repeated reviews |
| Document Compliance Score | `NN/100` |
| Relative Path Scan | PASS only when no `file:///`, `/Users/`, `/Volumes/`, drive-letter paths, or local absolute links exist |
| Final Result | `PASS` or `FAIL` |

---

> Next Skill: `brainstorming-to-plan`.
> In an orchestrated continuous workflow, return control to `workflow-coordinator` so it can dispatch the next phase without asking the user for approval.

---

## Self-Validation Checklist

Before exiting, verify each item. Report any FAIL explicitly.

### 📋 Self-Validation Checklist

| Validation Item | Status |
| :--- | :---: |
| Outputted the `DISCOVERY MODE ACTIVE` declaration as the first action | [ ] PASS |
| Did NOT modify any source code files | [ ] PASS |
| Did NOT edit any project files outside the allowed work item artifact folders | [ ] PASS |
| Treated all user input as requirements (not implementation commands) | [ ] PASS |
| Calculated the Requirement Readiness Score | [ ] PASS |
| Asked clarification questions when score < 85 and stopped | [ ] PASS |
| Generated 2–3 significantly different solution options | [ ] PASS |
| Recommended one option with detailed architectural reasoning | [ ] PASS |
| Completed internal discovery review and fixed every failed point before writing | [ ] PASS |
| Returned control to workflow-coordinator for the next phase | [ ] PASS |
| Did NOT ask the user for approval after Brainstorming generation | [ ] PASS |

**Result:** `[ALL PASS | FAILED: list failed items]`

---

## Completion Report

Output at end of execution:

### 📊 Requirement Discovery Report

> [!NOTE]
> **Status:** `[Paused – Awaiting feature selection | Paused – Awaiting clarification | Completed]`

| Metric / Field | Details |
| :--- | :---: |
| **Active Feature(s)** | `[FEAT-XXX: Name | Feature 1, 2, 3 — pending user selection]` |
| **Readiness Score** | `[XX/100]` |
| **Requirement Gaps** | `[List or "None"]` |
| **Solutions Generated** | `[Option A: Name, Option B: Name, Option C: Name (if applicable)]` |
| **Recommended Solution** | `Option [A/B/C] — [Name]` |
| **Internal Review** | `[PASS | FAILED: item list]` |
| **Brainstorming File(s)** | `[docs/features/<feature-family>/brainstorming/FEAT-XXX_feature_name.md, or the master+phase-NN file set | None]` |
| **Self-Validation** | `[ALL PASS | FAILED: item list]` |

---
**Workflow Handed Off.** Skill responsibility is complete.
In an orchestrated continuous workflow, `workflow-coordinator` must dispatch `brainstorming-to-plan` without a user approval stop.

## Evaluation Criteria & Readiness Score (Scale 100)
Giai đoạn chỉ được qua cổng kiểm duyệt khi tổng điểm từ 95 trở lên và không vi phạm tiêu chí đường dẫn (đánh fail lập tức nếu vi phạm chính sách đường dẫn tuyệt đối).

| # | Tiêu chí đánh giá | Điểm tối đa | Điểm đạt | Điều kiện đạt đủ điểm & Ghi chú |
|---|---|---:|:---:|---|
| 1 | Tương thích đường dẫn | 30 | /30 | 100% đường dẫn trong mã nguồn, script, kết quả và tài liệu là đường dẫn tương đối hoặc đã được làm sạch. Không có URL tệp tuyệt đối, đường dẫn ổ đĩa, đường dẫn tuyệt đối của macOS hoặc Linux, mã xác thực hoặc log chứa đường dẫn tuyệt đối. |
| 2 | Build và chạy runtime thật | 20 | /20 | App, service, UI, CLI hoặc worker build lại thành công, runtime thật mở được, surface tích hợp thật sẵn sàng, và không còn tiến trình treo sau kiểm thử. |
| 3 | Kiểm thử runtime thật | 20 | /20 | Kiểm thử gọi vào runtime đang chạy qua surface thật phù hợp như IPC, API, UI, CLI, SDK, job queue hoặc service, không chỉ kiểm thử đơn vị hoặc phản chiếu. Luồng thành công chính, luồng lỗi hợp lệ, luồng hồi quy và dọn dẹp đều đạt. |
| 4 | Đầy đủ chức năng | 15 | /15 | Giai đoạn triển khai đủ lệnh hoặc API bắt buộc, không có phần giữ chỗ chưa hoàn thiện, không bỏ sót hành vi cũ quan trọng. |
| 5 | Dễ đọc và dễ bảo trì | 5 | /5 | Mã nguồn, script và kết quả rõ ràng, có cấu trúc, đặt tên dễ hiểu, ít trùng lặp và không lan phạm vi ngoài giai đoạn. |
| 6 | Tuân thủ rule, Memory/RAG và skill trong project | 5 | /5 | Người điều phối và tác nhân đã đọc rule trong project, ưu tiên Memory First/RAG First bằng `./.agents/skills/project-rag-search` khi cần ngữ cảnh, chọn skill phù hợp từ `./.agents/skills`, đọc hướng dẫn skill trước khi làm, ghi rule/skill trong prompt/báo cáo và không tạo bản rule hoặc skill trùng lặp ở nơi khác. |
| 7 | An toàn dữ liệu và dọn dẹp | 5 | /5 | Kiểm thử chụp nhanh và khôi phục cấu hình, không tạo rác ở Màn hình nền hoặc thư mục tạm, không lộ mã xác thực hoặc bí mật, không để lại tiến trình app hoặc kiểm thử. |
| | **Tổng điểm** | **100** | **/100** | **Điểm đạt tối thiểu để Release: 95/100** |

## Điều kiện bắt buộc đánh FAIL (NO-GO)
Giai đoạn phải bị đánh FAIL (NO-GO) nếu gặp bất kỳ lỗi nào dưới đây (điểm đánh giá bị vô hiệu):
1. Có đường dẫn tuyệt đối thật trong mã nguồn, script, kết quả hoặc tài liệu thuộc phạm vi giai đoạn.
2. Build thất bại.
3. Ứng dụng không mở được.
4. Surface tích hợp thật của runtime không sẵn sàng (ví dụ: IPC token/pipe, API endpoint, UI route, CLI command, SDK entrypoint hoặc service health).
5. Ca kiểm thử runtime chính thất bại.
6. Kiểm thử chỉ là kiểm thử đơn vị hoặc phản chiếu (reflection) mà chưa gọi vào runtime thật.
7. Có tiến trình app hoặc kiểm thử còn treo sau khi kiểm thử kết thúc.
8. Kết quả chứa mã xác thực, bí mật hoặc dữ liệu chưa được làm sạch.
9. Có luồng tự ý tắt app, service hoặc runtime trong khi luồng điều phối chính chưa cho phép.
10. Chưa đủ bằng chứng thực tế nhưng báo cáo đạt.
11. Bỏ qua các skill phù hợp sẵn có trong `./.agents/skills` mà không có lý do được chấp nhận.
12. Tự ý copy hoặc tạo bản sao skill, prompt hoặc workflow mới ở thư mục khác khi project đã có skill tương ứng.
13. Bỏ qua rule của project hoặc không chứng minh đã đọc rule bắt buộc.
14. Tạo rule song song làm lệch hướng `PROJECT_RULES.md`, `./.agents/AGENTS.md` hoặc `./.agents/AI_RULES.md`.
15. Quét mã nguồn hoặc hỏi thiết kế trước khi tra cứu Project Memory và dùng `./.agents/skills/project-rag-search` khi cần ngữ cảnh.
