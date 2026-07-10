<!-- File path: docs/plans/FEAT-003_claude_environment_diagnostics_plan.md -->

---
feature_id: FEAT-003
feature_name: Claude Environment Configuration & Health Diagnostics
status: reviewed
stage: planning
created_at: 2026-07-04
updated_at: 2026-07-04
previous_artifact: ../brainstorming/FEAT-003_claude_environment_diagnostics.md
next_artifact: ../designs/FEAT-003_claude_environment_diagnostics_blueprint.md
---

# FEAT-003: Claude Environment Configuration & Health Diagnostics

## Objective
- Introduce validation checks for Anthropic Claude environment keys and configurations into the AI Skill Framework setup pipeline.
- Ensure developers can easily verify if their Claude-based coding workspace is ready for execution, maintaining parity with existing Gemini configurations.

## Scope
### Included
- Bootstrapping check for `ANTHROPIC_API_KEY` (prompting user if not found during workspace bootstrap).
- Health status verification for the Anthropic Claude provider in workspace diagnostics.
- CLI environment doctor script updates for detecting Claude provider availability.

### Excluded
- Installation or integration of specific LLM runtimes or SDKs.
- Automatic routing of agent queries (handled by individual IDE settings).

## Project Impact
- **Impacted Areas**: Environment Diagnostics, Bootstrap/Setup utilities, Doctor validation scripts.

## Dependencies
- Existing `environment-bootstrap` and `environment-health` skills.
- Local command-line doctor execution scripts (`doctor.ps1` and `doctor.sh`).

## Risks
- **Risk**: Missing dependencies or API connection failures block the overall health diagnostics reporting.
- **Mitigation**: Ensure Claude checks fail gracefully (returning a warning status instead of a terminal failure) when other providers like Gemini are fully active.

## Acceptance Criteria
- [ ] `environment-bootstrap` successfully identifies the existence of Claude environment credentials.
- [ ] `environment-health` lists the Claude provider status under active configuration checks.
- [ ] System diagnostics commands `doctor` successfully report Claude setup status.

## Deliverables
- Updated Environment Bootstrap and Environment Health instruction files.
- Refactored environment chấn đoán (doctor) shell and PowerShell validation scripts.

## Estimated Complexity
- **Low**: Involves adding checks and logging flags without introducing new application layers or compiler settings.

## Recommended Blueprint Focus
- Safe scanning of environment variables and fallback keys.

## Recommended Next Skill
/blueprint
