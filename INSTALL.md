# Installation and Upgrade Guide

This document describes how to install, configure, verify, and upgrade the AI Skill Framework in your projects.

---

## Installation Philosophy

* **Explicit Installation Only**: The AI Skill Library never automatically installs or hooks itself into a project. Installation must be performed explicitly by a developer or designated workflow script.
* **Independence**: The framework repository itself remains completely independent and decoupled from target project repositories. It is designed to be pulled, linked, or embedded.
* **Standard Target Location**: Skills must always be installed inside the project's relative path:
  ```text
  .agents/skills/
  ```

---

## Recommended Project Layout

For AI Coding Agents (e.g., Antigravity IDE, Cursor, Claude Code) to seamlessly discover project guidelines, memory, and skills, the following directory layout is recommended at the root of your project:

```text
<project-root>/
├── .agents/
│   ├── memory/              # Project memory files (summary, architecture, etc.)
│   ├── skills/              # Installed AI skills (from this framework)
│   │   ├── environment-bootstrap/
│   │   ├── environment-health/
│   │   ├── brainstorming/
│   │   └── ... (other skills)
├── AGENTS.md                # Custom system rules, managed rules block, and guidelines for the project
├── docs/                    # Feature documentation structure (Feature-Centric)
│   ├── brainstorming/       # Requirement discovery documents (FEAT-XXX_*.md)
│   ├── plans/               # Project plans (FEAT-XXX_*_plan.md)
│   ├── designs/             # Technical design blueprints (FEAT-XXX_*_blueprint.md)
│   └── adr/                 # Optional Architecture Decision Records (ADR-XXX_*.md)
```

---

## Installation Methods

> [!NOTE]
> The installation script (`aiwf install` or `./install.sh`) automatically detects standard Git repositories, Git worktrees, Git submodules, and supports execution from nested directories. It resolves the true project root via `git rev-parse` and sets up the framework files at the workspace root.

### Method 1: Directory Copying (Recommended for Simplicity)
Simply copy the `skills/` directory from this framework into your project's `.agents/` folder.

**On Linux/macOS:**
```bash
mkdir -p .agents/skills/
cp -r /path/to/ai-skill-framework/skills/* .agents/skills/
```

**On Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path .agents\skills\
Copy-Item -Path C:\path\to\ai-skill-framework\skills\* -Destination .agents\skills\ -Recurse -Force
```

---

### Method 2: Git Submodule (Recommended for Version Tracking)
If your project is a Git repository, you can add this framework as a submodule, pinning it to a specific tag or commit.

```bash
git submodule add https://gitlab.com/hngan.it/ai-workflow-skills.git .agents/skills-framework
```

Then, symlink or copy specific skills into `.agents/skills/`.

---

### Method 3: Symlink (Recommended for Local Development)
To share a single local copy of the skills and receive updates instantly, create symlinks.

**On Linux/macOS:**
```bash
ln -s /path/to/ai-skill-framework/skills/ .agents/skills
```

**On Windows (PowerShell - run as Administrator):**
```powershell
New-Item -ItemType SymbolicLink -Path .agents\skills -Value C:\path\to\ai-skill-framework\skills
```

---

### Method 4: Future Package Manager Integration
A package manager (e.g., `npm`, `pip`, or custom AI package manager) will eventually support declarative installation via the `MANIFEST.json`. The manifest specifies:
```json
{
  "skill_directory": "skills",
  "installation_target": ".agents/skills"
}
```
A CLI tool will be able to run `aiskill install` or `npx aiskill install` to parse the manifest and automate download and mapping.

---

### Method 5: Claude Desktop and Claude Code Integration
To integrate the AI Skill Framework with Anthropic Claude tools:

1. **Claude Code CLI**:
   Claude Code CLI reads rules from `AGENTS.md` and `.agents/` project layouts natively. Simply run `aiwf install` in your project root to ensure Claude Code detects the project policies and skills.
   
2. **Claude Desktop**:
   You can add custom commands or reference rules in Claude Desktop's global configuration (`config.json`). Add a symlink from Claude's global settings folder to the `.agents/skills` directory, or instruct Claude in your system prompts to consult the `.agents/` folder using:
   ```text
   Review workspace policies in .agents/AI_RULES.md and load instructions from .agents/skills/ when executing workflow tasks.
   ```

---

## Verification

To verify that the skills have been correctly installed and are discoverable by AI Coding Agents:

1. **Check Folder Integrity**: Verify that every skill folder contains a `SKILL.md` file. For instance, `.agents/skills/environment-health/SKILL.md` must exist.
2. **Review Customization Root**: Ensure your active workspace points to `.agents` (under Workspace Customizations Root).
3. **Check Documentation Folders**: Ensure `docs/brainstorming/`, `docs/plans/`, `docs/designs/`, and optional `docs/adr/` folders are present in the project to support feature-centric tracing.
4. **Execute Diagnostics**: Trigger the `environment-health` skill to verify that the environment-wide agent runner recognizes all active skills.
5. **Verify Memory CLI**: Run `aiwf memory update` in the terminal to verify that the script-first memory engine can scan the codebase and update indexes.


---

## Upgrade Strategy

### How Skills are Updated
Skills follow **Semantic Versioning** (`MAJOR.MINOR.PATCH`).
* **PATCH updates** (`1.0.x`) are backward-compatible bug fixes and documentation improvements.
* **MINOR updates** (`1.x.0`) introduce new skills or backward-compatible inputs/outputs.
* **MAJOR updates** (`x.0.0`) introduce breaking workflow or schema changes.

### Synchronizing Skills
* **Manual copies**: To update, delete `.agents/skills/` and re-copy the fresh framework version.
* **Git Submodule**: Move to the submodule folder, pull, and update the parent repository pointer.

### Safe AGENTS.md Integration
* **Installation**: Creates `AGENTS.md` in the project root if it does not already exist. If it exists, it appends/merges the managed rules block safely.
* **Updates**: Refreshes only the managed block in `AGENTS.md`, preserving all user-customized rules outside the markers.
* **Idempotency**: Multiple installations or updates will always maintain exactly one managed rules block and will never duplicate it.

### Backward Compatibility
* Existing workflows should continue to work with minor/patch upgrades.
* Input and output schemas (expressed in YAML in each `SKILL.md`) will deprecate parameters rather than remove them abruptly. Deprecation notices will be documented in the `CHANGELOG.md`.

### Handling Deprecated Skills
When a skill is deprecated:
1. It will be marked with a warning badge in the `SKILLS.md` catalog.
2. The `MANIFEST.json` will list `"deprecated": true` inside the skill object.
3. The orchestrator skill `software-development-workflow` will warn the developer when triggering it.
4. Developers should migrate to the recommended replacement skill as indicated in `SKILLS.md`.
