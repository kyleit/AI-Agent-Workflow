---
feature_id: FEAT-003
feature_name: Claude Environment Configuration & Health Diagnostics
status: draft
stage: brainstorming
created_at: 2026-07-04
updated_at: 2026-07-04
previous_artifact: None
next_artifact: ../plans/FEAT-003_claude_environment_diagnostics_plan.md
---

# Master Requirement Document – Claude Environment Configuration & Health Diagnostics

## 1. Feature ID & Name
- **Feature ID**: FEAT-003
- **Feature Name**: Claude Environment Configuration & Health Diagnostics

## 2. Original Idea
I want to upgrade these skills to support Claude (tôi muốn nâng cấp các skills này hỗ trợ cho claude). This feature covers environment variables, bootstrap scripts, and diagnostic tools to support Claude/Anthropic setups.

## 3. Business Problem
- **Problem**: The AI Skill Framework currently only checks and bootstraps environment keys and diagnostic criteria for Google Gemini and local Ollama models. Developers utilizing Anthropic Claude (e.g., Sonnet 3.5) lack validation and bootstrapping capabilities, leading to configuration uncertainty and setup errors.
- **Why it matters**: Ensuring that Claude developers have verified environments with active credentials avoids runtime errors when agents invoke skills.
- **Who is affected**: AI developers and coding agents using Anthropic Claude models inside the AI Skill Framework.
- **Expected outcome**: Seamless bootstrap check and clear diagnostics reports for Claude/Anthropic API credentials.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Update `environment-bootstrap` to include checking and configuring `ANTHROPIC_API_KEY`.
  - FR-02: Update `environment-health` to inspect the presence of `ANTHROPIC_API_KEY` and report status.
  - FR-03: Update shell and PowerShell doctor scripts (`doctor.sh`, `doctor.ps1`) to include checks for Anthropic Claude provider support.
- **Non-functional Requirements**:
  - NFR-01: No external network API token consumption during simple health checks.
  - NFR-02: Backward-compatibility: Gemini/Ollama setups must continue to function perfectly without error if Claude configuration is missing.
- **Technical Constraints**:
  - TC-01: Detect both `ANTHROPIC_API_KEY` and fallback `CLAUDE_API_KEY` environment variables.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Which default Claude model should be used as the baseline test? | `claude-3-5-sonnet-20241022` or latest Sonnet 3.5. |
| Should the bootstrap script prompt for the Anthropic key if missing? | Yes, same as the Gemini API key prompting logic. |

## 6. Requirement Readiness Score
- **Score**: 95/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: `project-summary.md` and `MANIFEST.json`.
- **Existing Architecture Summary**: Bootstrapping and health checks are prompt-driven skills under `skills/environment-bootstrap/` and `skills/environment-health/`, supported by `doctor.sh` and `doctor.ps1` scripts in the root directory.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Environment Bootstrap | [skills/environment-bootstrap/SKILL.md](file:///e:/Cloud/_protected/agents/skills/environment-bootstrap/SKILL.md) | Prompts user for credentials and configs setup. |
| Environment Health | [skills/environment-health/SKILL.md](file:///e:/Cloud/_protected/agents/skills/environment-health/SKILL.md) | Reports presence and validity of active providers. |
| Doctor Script (Shell) | [doctor.sh](file:///e:/Cloud/_protected/agents/doctor.sh) | Verifies CLI environment and tools status. |
| Doctor Script (PowerShell) | [doctor.ps1](file:///e:/Cloud/_protected/agents/doctor.ps1) | Verifies CLI environment and tools status. |

## 9. Solution Options Evaluated

### Option A: Integrated Support in Existing Skills (Selected)
- **Overview**: Modify existing bootstrap and health checks directly to add Anthropic checks.
- **Advantages**: Single point of maintenance; doesn't duplicate core logic.
- **Disadvantages**: Minor increases in skill file sizes.
- **Complexity**: Low
- **Risk**: Low
- **Performance**: Instant
- **Maintainability**: High
- **Compatibility**: High
- **Future Scalability**: High

### Option B: Claude-Specific Companion Skills
- **Overview**: Create separate skills such as `claude-bootstrap` and `claude-health`.
- **Advantages**: Keeps Gemini-only skills completely clean.
- **Disadvantages**: Introduces duplicate code for workspace directory checking and CLI path settings.
- **Complexity**: Medium
- **Risk**: Low

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Low | Medium |
| Risk | Low | Low |
| Performance | Instant | Instant |
| Maintainability | High | Medium |
| Compatibility | High | Low |
| Future Scalability | High | Medium |
| Development Cost | Low | Medium |

## 11. Selected Solution
- **Choice**: Option A
- **Why Selected**: Merging the configuration check into the existing diagnostic scripts and skills ensures that users get a unified report of their environments (whether they use Gemini, Claude, or both).
- **Trade-offs Accepted**: Slightly larger file size for environment skills.
- **Technical Debt**: None.
- **Risk Mitigation**: Verify checks handle cases where only one of the API keys is present without failing.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: CLI environment variable changes might require terminal reload to take effect. -> Document this behavior in output messages.
- **Assumptions**:
  - A-01: Developers have an active Anthropic account and can provide their API keys.

## 13. Acceptance Criteria
- [ ] `environment-bootstrap` checks for `ANTHROPIC_API_KEY` and prompts if not configured.
- [ ] `environment-health` reports Claude status cleanly under providers check.
- [ ] `doctor.ps1` and `doctor.sh` run successfully and report Claude availability.

---

## 14. Final Planning Prompt

### Purpose
Provide a planning guideline for implementing Claude configuration & health diagnostics.

### Problem Statement
The framework needs to support verifying and bootstrapping Claude API credentials and diagnostic tools without breaking existing Gemini configurations.

### Objectives
- Add checks for `ANTHROPIC_API_KEY` in environment skills.
- Update `doctor` scripts to test and print Claude provider availability status.

### Verification Checklist
- [ ] docs/plans/FEAT-003_claude_environment_diagnostics_plan.md generated and approved
- [ ] docs/designs/FEAT-003_claude_environment_diagnostics_blueprint.md generated and approved
- [ ] Doctor scripts report Claude status correctly.
