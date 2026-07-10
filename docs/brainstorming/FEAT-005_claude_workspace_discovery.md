---
feature_id: FEAT-005
feature_name: Workspace & Global Customization Discovery for Claude
status: draft
stage: brainstorming
created_at: 2026-07-04
updated_at: 2026-07-04
previous_artifact: None
next_artifact: ../plans/FEAT-005_claude_workspace_discovery_plan.md
---

# Master Requirement Document – Workspace & Global Customization Discovery for Claude

## 1. Feature ID & Name
- **Feature ID**: FEAT-005
- **Feature Name**: Workspace & Global Customization Discovery for Claude

## 2. Original Idea
I want to upgrade these skills to support Claude (tôi muốn nâng cấp các skills này hỗ trợ cho claude). This feature covers discovery configuration files and workspace integration for Claude CLI/Claude Code.

## 3. Business Problem
- **Problem**: The AI Skill Framework uses a specific config folder layout (`.agents/skills/`) to load project skills and `~/.gemini/config` for global custom configurations. Tool suites like Claude Code CLI or Claude Desktop have their own global config directory locations and rule loading mechanisms. Without integration guidance and configuration hooks, Claude cannot discover and load these skills automatically.
- **Why it matters**: Supporting seamless loading of project and global configurations for Claude enables developers to use the Claude environment with full capability.
- **Who is affected**: Claude Code CLI and Claude Desktop users.
- **Expected outcome**: Documented integration workflow and scripts to symlink/configure custom skills for Claude.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Update `INSTALL.md` and `README.md` to explain how to load skills using Claude Desktop/Claude Code.
  - FR-02: Document the global customization folders for Claude (e.g., config directories on Windows, Linux, and macOS).
  - FR-03: Create integration scripts or modify environment bootstrap to configure custom system prompts in Claude configuration directories if supported.
- **Non-functional Requirements**:
  - NFR-01: No changes to the standard `.agents/` folder path: we must maintain a unified project layout for all agents.
- **Technical Constraints**:
  - TC-01: Claude Code CLI loads configuration from its own files; we must interface with these standard configuration points.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Does Claude Code CLI allow local folder rules? | Yes, it reads instructions or system prompts provided in the workspace root or custom config directories. |
| Where is the Claude Desktop configuration file located? | Usually `config.json` inside the user app data directory (e.g., `AppData/Roaming/Claude/` on Windows). |

## 6. Requirement Readiness Score
- **Score**: 90/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: `INSTALL.md` and `MANIFEST.json`.
- **Existing Architecture Summary**: The workspace customization folders are detailed in `INSTALL.md`. Global customization root is currently default set to `~/.gemini/config`.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Installation Guide | [INSTALL.md](file:///e:/Cloud/_protected/agents/INSTALL.md) | Details layout setup and custom folder discovery. |
| Bootstrap Script | [bootstrap.ps1](file:///e:/Cloud/_protected/agents/bootstrap.ps1) | Sets up environment system variables and configurations. |

## 9. Solution Options Evaluated

### Option A: Documented Integration & Symlinking (Selected)
- **Overview**: Provide instructions in `INSTALL.md` and a custom script to link the `.agents/` project folder and global config folders into Claude's configuration path.
- **Advantages**: Minimal code changes; leverages existing folder architecture.
- **Disadvantages**: Minor manual steps for developers.
- **Complexity**: Low
- **Risk**: Low
- **Performance**: High
- **Maintainability**: High
- **Compatibility**: High
- **Future Scalability**: High

### Option B: Automatic Config File Rewriting
- **Overview**: Add logic in `bootstrap` scripts to automatically locate and write to Claude Desktop's `config.json` and Claude Code config directories.
- **Advantages**: Completely automated.
- **Disadvantages**: Dangerous, as automated config overwrites could corrupt a user's pre-existing Claude configuration.
- **Complexity**: High
- **Risk**: High

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Low | High |
| Risk | Low | High |
| Performance | High | High |
| Maintainability | High | Low |
| Compatibility | High | Medium |
| Future Scalability | High | Medium |
| Development Cost | Low | High |

## 11. Selected Solution
- **Choice**: Option A
- **Why Selected**: Respects the user's manual configuration control and avoids high risk of file corruption during automated installation scripts.
- **Trade-offs Accepted**: Developers need to read the manual section to configure Claude Desktop integration.
- **Technical Debt**: None.
- **Risk Mitigation**: Provide clear copy-paste commands for symlinking.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Claude's config location changes in future releases. -> Keep instructions modular and refer to official Anthropic documentation links.
- **Assumptions**:
  - A-01: Claude CLI reads rules from standard project locations like `.agents/` or system configuration files.

## 13. Acceptance Criteria
- [ ] `INSTALL.md` contains a dedicated section for "Claude Desktop and Claude Code Integration".
- [ ] Integration instructions are verified on Windows and Unix systems.
- [ ] Environment bootstrap has a clear log output pointing to Claude integration tips.

---

## 14. Final Planning Prompt

### Purpose
Provide a planning guideline for implementing Claude Workspace Discovery.

### Problem Statement
We need to guide Claude Desktop and Claude Code users on how to load custom policies and skills from the `.agents/` folder structure.

### Objectives
- Add Claude configuration and integration instructions to `INSTALL.md`.
- Validate symlinking commands to Claude configuration paths.

### Verification Checklist
- [ ] docs/plans/FEAT-005_claude_workspace_discovery_plan.md generated and approved
- [ ] docs/designs/FEAT-005_claude_workspace_discovery_blueprint.md generated and approved
- [ ] Verification steps completed successfully.
