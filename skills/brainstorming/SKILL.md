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
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Skill definition.
---

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
| The ONLY file I may write is: `docs/brainstorm/FEAT-XXX_feature_name.md` |
| And ONLY after explicit user confirmation (Y/N). |

> This output is mandatory. Do not skip it. Do not abbreviate it.
> Output it BEFORE reading the user's requirement. Output it BEFORE any analysis.
> This is your behavioral commitment for this entire execution.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "exactly 2"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "brainstorming" --command "brainstorm" --checkpoint 3 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 3 --step "Step Complete" --next-skill "brainstorming-to-plan" --next-command "plan"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## Wrong Behavior Detection

**Before taking any action, check yourself:**

```
IF you are about to:
  ✗ Use write_file() on any path except docs/brainstorm/
  ✗ Use edit_file(), replace_file(), or multi_replace_file()
  ✗ Run any shell command that modifies files
  ✗ Read source code files to find bugs to fix
  ✗ Generate a plan (docs/plans/) or blueprint (docs/designs/)
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

Feature IDs are determined **ONLY** by scanning `docs/brainstorm/`:

1. Scan `docs/brainstorm/` for files matching `FEAT-XXX_*.md` (3-digit number).
2. Ignore: `docs/plans/`, `docs/designs/`, `docs/adr/`, memory, git history, `CHANGELOG.md`.
3. Empty directory (or only `.gitkeep`) → start at `FEAT-001`.
4. Files exist → next ID = highest existing ID + 1.
5. Resume/Selection mode → reuse the Feature ID under discussion.

> [!WARNING]
> Never pre-assign FEAT-XXX IDs during Feature Decomposition.
> Use temporary labels **Feature 1, Feature 2, Feature 3** until user confirms strategy.
> Assign FEAT-XXX IDs only in Step 15 when writing the final document.

---

## Workflow Sequence

Execute this sequence strictly. Each STOP is non-negotiable and cannot be skipped.

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
Step 14: User Confirmation Gate
         [→ STOP, display Y/N prompt, wait for explicit Y before writing any file]
              ↓
Step 15: Generate Brainstorming Document(s)
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
| The ONLY file I may write is: `docs/brainstorm/FEAT-XXX_feature_name.md` |
| And ONLY after explicit user confirmation (Y/N). |

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

### Step 14: User Confirmation Gate

**This step is a mandatory gate. Do NOT write any file before this step completes.**

Display this exact prompt and **STOP**:

```text
────────────────────────────────────────────────────
Requirement Discovery Complete

Feature:                  [Feature Name]
Readiness Score:          [XX/100]
Recommended Solution:     Option [A/B/C] — [Name]

Continue generating Brainstorming document?

  [Y] Yes — Generate docs/brainstorm/FEAT-XXX_feature_name.md
  [N] No  — Stop. I will revise or choose a different option.
────────────────────────────────────────────────────
```

> [!CAUTION]
> **Do NOT write any file until the user explicitly responds Y (or "yes").**
> If the user responds N or requests changes: apply changes, repeat from the appropriate step.
> If the user selects a different option: update recommendation and ask again.

---

### Step 15: Generate Brainstorming Document(s)

Only after Y confirmation:

1. Scan `docs/brainstorm/` to calculate the next Feature ID.
2. Write: `docs/brainstorm/FEAT-XXX_feature_name.md`
   (one file per independent feature if decomposition was chosen)
3. Use **relative paths only** for all artifact links.

---

## Brainstorming Document Template

```markdown
<!-- docs/brainstorm/FEAT-XXX_feature_name.md -->

---
feature_id: FEAT-XXX
feature_name: Human Readable Name
status: draft
stage: brainstorming
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
previous_artifact: None
next_artifact: ../plans/FEAT-XXX_feature_name_plan.md
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

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| [Q1] | [A1 or "Pending"] |
| [Q2] | [A2 or "Pending"] |

## 6. Requirement Readiness Score
- **Score**: [XX/100]
- **Status**: [Ready ≥ 85 | Below Threshold < 85]

## 7. Existing Project Context
- **Memory Source**: [project-summary.md and RAG results referenced]
- **Existing Architecture Summary**: [Relevant patterns and decisions]

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| [Module] | [Relative path] | [How it relates to this feature] |

## 9. Solution Options Evaluated

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

## 10. Solution Comparison Table
| Criteria | Option A | Option B | Option C |
|---|---|---|---|
| Complexity | | | |
| Risk | | | |
| Performance | | | |
| Maintainability | | | |
| Compatibility | | | |
| Future Scalability | | | |
| Development Cost | | | |

## 11. Selected Solution
- **Choice**: Option [A/B/C] — [Name]
- **Why Selected**: [Detailed architectural reasoning]
- **Trade-offs Accepted**: [...]
- **Technical Debt**: [...]
- **Risk Mitigation**: [...]

## 12. Risks & Assumptions
- **Risks**:
  - R-01: [Risk] → [Mitigation]
  - R-02: [Risk] → [Mitigation]
- **Assumptions**:
  - A-01: [...]

## 13. Acceptance Criteria
- [ ] [Verifiable, testable criterion]
- [ ] [Verifiable, testable criterion]

---

## 14. Final Planning Prompt

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
- [ ] docs/plans/FEAT-XXX_feature_name_plan.md generated and approved
- [ ] docs/designs/FEAT-XXX_feature_name_blueprint.md generated and approved
- [ ] All Acceptance Criteria mapped to implementation tasks

---

> ⚠ The next Skill is `brainstorming-to-plan`.
> It must be invoked **manually** by the user.
> This Skill does NOT invoke it automatically.
```

---

## Self-Validation Checklist

Before exiting, verify each item. Report any FAIL explicitly.

### 📋 Self-Validation Checklist

| Validation Item | Status |
| :--- | :---: |
| Outputted the `DISCOVERY MODE ACTIVE` declaration as the first action | [ ] PASS |
| Did NOT modify any source code files | [ ] PASS |
| Did NOT edit any project files outside `docs/brainstorm/` | [ ] PASS |
| Treated all user input as requirements (not implementation commands) | [ ] PASS |
| Calculated the Requirement Readiness Score | [ ] PASS |
| Asked clarification questions when score < 85 and stopped | [ ] PASS |
| Generated 2–3 significantly different solution options | [ ] PASS |
| Recommended one option with detailed architectural reasoning | [ ] PASS |
| Asked "Continue generating Brainstorming document? [Y/N]" and stopped | [ ] PASS |
| Waited for explicit Y before writing any file | [ ] PASS |
| Stopped after completing Brainstorming generation | [ ] PASS |
| Did NOT invoke or suggest invoking another Skill automatically | [ ] PASS |

**Result:** `[ALL PASS | FAILED: list failed items]`

---

## Completion Report

Output at end of execution:

### 📊 Requirement Discovery Report

> [!NOTE]
> **Status:** `[Paused – Awaiting feature selection | Paused – Awaiting clarification | Paused – Awaiting user confirmation | Completed]`

| Metric / Field | Details |
| :--- | :---: |
| **Active Feature(s)** | `[FEAT-XXX: Name | Feature 1, 2, 3 — pending user selection]` |
| **Readiness Score** | `[XX/100]` |
| **Requirement Gaps** | `[List or "None"]` |
| **Solutions Generated** | `[Option A: Name, Option B: Name, Option C: Name (if applicable)]` |
| **Recommended Solution** | `Option [A/B/C] — [Name]` |
| **User Confirmed** | `[Yes | No | Pending]` |
| **Brainstorming File(s)** | `[docs/brainstorm/FEAT-XXX_feature_name.md | None]` |
| **Self-Validation** | `[ALL PASS | FAILED: item list]` |

---
**Workflow Paused.** Skill responsibility is complete.
The next Skill (`brainstorming-to-plan`) must be invoked manually.

