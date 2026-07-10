---
name: environment-bootstrap
command: bootstrap
aliases:
  - setup
  - install-env
category: environment
tags:
  - setup
  - bootstrap
  - environment
version: 2.5.0
author:
  name: Kyle Dang
  email: kyleit@klexpress.net
  website: https://www.klexpress.net
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-03
updated_at: 2026-07-03
description: Prepare the local machine for the AI Coding workflow. Installs and configures required tools (Git, Python, Node.js, SQLite, Tree-sitter, QMD), initializes Project Memory configuration, verifies AI Skills, and validates optional infrastructure (Docker, Qdrant, Ollama). Safe components are installed automatically. Unsafe components require explicit user confirmation.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: none
  rag: none
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
  usage: none
---

# Skill: Environment Bootstrap

## Purpose

**Prepare and configure** the local machine for the full **Memory-Driven AI Coding Workflow**.

Unlike `environment-health` (which only inspects), this Skill is authorized to:
- Install safe missing components
- Initialize project configuration
- Configure Project Memory
- Validate and repair the environment

This Skill runs **once** when setting up a new machine, and again whenever `environment-health` reports critical or warning issues.

---

## Role

You are acting as a **Principal AI Platform Engineer** and **DevOps Environment Specialist**.

You have full access to the local system to inspect, install, and configure the environment.

You follow a **safe-first installation policy**: install safe components automatically, require explicit user confirmation for unsafe ones.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

This Skill MUST interface with the centralized Python CLI Runtime Engine:
- **Validate Checkpoint**: Run `python skills/workflow-runtime/scripts/workflow_runtime.py validate --checkpoint "at least 1"` before taking any action. If validation fails, halt execution immediately.
- **Progress Tracking**:
  - *Start*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "environment-bootstrap" --command "bootstrap" --checkpoint 1 --step "Starting execution..."`
  - *Step Updates*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py step --step "<step_desc>" --log "<progress_message>"` progressively during major steps.
  - *Completion*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 1 --step "Step Complete" --next-skill "project-discovery" --next-command "discover"` when execution finishes successfully.
  - *Failure*: Run `python skills/workflow-runtime/scripts/workflow_runtime.py fail --step "<error_step>" --log "<error_details>"` if any phase fails.

## 🔒 GLOBAL POLICY REFERENCES

This Skill MUST strictly adhere to the global policies defined in [AI_RULES.md](../../AI_RULES.md):
- **Approval Gate Policy** (Section 1) - Seek explicit confirmation before modifying code or creating files.
- **Git Workflow Policy** (Section 2) - Perform branch checks and commits/tags/pushes only with approval.
- **Memory First Policy** (Section 3) - Consult project summary/memory before source files or user questions.
- **RAG Policy** (Section 4) - Follow retrieval sequence levels.
- **Artifact Policy** (Section 5) - Strictly follow path boundaries and naming formats.
- **Testing Policy** (Section 8) - Run compilation, build, and tests, halting on failures.

## Multi-Agent Contract

Runs under the Multi-Agent Workflow. Respect agent ownership and handoff rules defined in [agents/](../../agents/) and [runtime/](../../runtime/).

---

## Installation Policy

### ✅ Safe — Install Automatically (no confirmation needed)

| Component | Installation Method |
|-----------|-------------------|
| Python (if not found) | OS package manager |
| pip / pip3 | OS package manager or get-pip.py |
| Node.js | nvm or OS package manager |
| npm / npx | Comes with Node.js |
| SQLite | OS package manager |
| Tree-sitter CLI | `brew install tree-sitter-cli` (macOS) or `npm install -g tree-sitter-cli` or `cargo install tree-sitter-cli` |
| QMD CLI | `npm install -g @qmd/cli` or `pip install qmd` |
| Python packages (sentence-transformers, nomic) | `pip install` |

### ⚠ Unsafe — Require Explicit Confirmation `[y/N]`

| Component | Why Confirmation Required |
|-----------|--------------------------|
| Docker | System-level service, elevated privileges |
| Qdrant | Server process, Docker dependency |
| Ollama | Large binary, model downloads (GBs) |
| Large embedding models | Bandwidth/storage intensive |
| OS-level packages (apt install, brew install) | System-wide changes |
| System services (systemctl, launchctl) | System daemon management |

---

## OS Detection & Package Manager Selection

Detect OS and select package manager **before any installation**:

```bash
# macOS
uname -s  # → Darwin
which brew 2>/dev/null  # preferred
# Fallback: manual install instructions

# Linux — Debian/Ubuntu
cat /etc/os-release | grep ID  # → ubuntu, debian
which apt 2>/dev/null

# Linux — Fedora/RHEL
cat /etc/os-release | grep ID  # → fedora, rhel, centos
which dnf 2>/dev/null || which yum 2>/dev/null

# Linux — Arch
cat /etc/os-release | grep ID  # → arch
which pacman 2>/dev/null

# Windows
echo %OS%  # → Windows_NT
where winget 2>nul || where choco 2>nul
```

Record `detected_os` and `package_manager` and use them for all subsequent installs.

---

## Workflow

### Phase 1 — Pre-Bootstrap: Environment Scan

Before any installation, run a quick read-only scan (equivalent to `environment-health` summary):

```
Scanning environment...

OS:         [macOS 14.x | Ubuntu 22.04 | Windows 11]
Package Mgr: [brew | apt | winget]

Required Tools:
  Git:        [found vX.X | MISSING]
  Python:     [found 3.X | MISSING]
  Node.js:    [found vXX | MISSING]
  SQLite:     [found 3.X | MISSING]
  Tree-sitter:[found vX.X | MISSING]

Optional:
  Docker:     [running | stopped | MISSING]
  Qdrant:     [running | MISSING]
  Ollama:     [running | stopped | MISSING]
  QMD:        [found | MISSING]

Project Config:
  .agents/memory.config.json: [exists | MISSING]

Project Memory:
  State: [FRESH | STALE | NOT GENERATED | NOT INITIALIZED]

AI Skills:
  Found: [N / 11]
```

Print the scan, then proceed to installation.

---

### Phase 2 — Install Required Tools

Install in this order. Skip any already installed.

---

#### Step 2.1 — Git

```bash
git --version 2>/dev/null
```

If missing:
```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt install -y git

# Fedora/RHEL
sudo dnf install -y git

# Windows
winget install --id Git.Git -e
```

After install, check git user configuration:
```bash
git config --global user.name
git config --global user.email
```

If either is empty, prompt:
```
Git user identity is not configured.

Enter your name for Git commits: [user input]
Enter your email for Git commits: [user input]

Configuring:
  git config --global user.name "[name]"
  git config --global user.email "[email]"
```

---

#### Step 2.2 — Python

```bash
python3 --version 2>/dev/null || python --version 2>/dev/null
```

If missing or version < 3.9:
```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt install -y python3 python3-pip

# Fedora/RHEL
sudo dnf install -y python3 python3-pip

# Windows
winget install --id Python.Python.3.11
```

Verify pip:
```bash
pip3 --version 2>/dev/null || pip --version 2>/dev/null
```

If pip missing:
```bash
python3 -m ensurepip --upgrade
# OR
curl https://bootstrap.pypa.io/get-pip.py | python3
```

---

#### Step 2.3 — Node.js

```bash
node --version 2>/dev/null
```

If missing or version < 18:
```bash
# Preferred: nvm (safe, no sudo)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null
nvm install --lts
nvm use --lts

# macOS fallback
brew install node

# Ubuntu/Debian fallback
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Windows
winget install --id OpenJS.NodeJS.LTS
```

Verify npm and npx:
```bash
npm --version
npx --version
```

---

#### Step 2.4 — SQLite

```bash
sqlite3 --version 2>/dev/null
```

If missing:
```bash
# macOS (usually pre-installed)
brew install sqlite

# Ubuntu/Debian
sudo apt install -y sqlite3

# Fedora/RHEL
sudo dnf install -y sqlite

# Windows
winget install --id SQLite.SQLite
```

---

#### Step 2.5 — Tree-sitter CLI

```bash
tree-sitter --version 2>/dev/null
```

If missing:
```bash
# macOS
brew install tree-sitter-cli

# Preferred: npm global install
npm install -g tree-sitter-cli

# Fallback: Rust cargo
cargo install tree-sitter-cli

# Verify
tree-sitter --version
```

---

### Phase 3 — Install Optional AI Infrastructure

For each optional component, check if already installed before prompting.

---

#### Step 3.1 — Docker

```bash
docker --version 2>/dev/null
docker info 2>/dev/null
```

If missing:
```
Docker is not installed.
Docker enables running Qdrant (vector database) for semantic search.

```bash
python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Install Docker?" --options "Yes|No" --default "No"
```

If `y`:
```
Docker requires system-level installation.
Please install Docker Desktop from: https://docs.docker.com/get-docker/

macOS:   https://docs.docker.com/desktop/install/mac-install/
Linux:   https://docs.docker.com/engine/install/
Windows: https://docs.docker.com/desktop/install/windows-install/

After installing, restart this Skill to continue setup.
```

If Docker is installed but not running:
```
Docker is installed but the daemon is not running.

```bash
python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Start Docker?" --options "Yes|No" --default "No"
```

If `y`:
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
sudo systemctl enable docker

# Windows: Start Docker Desktop from system tray
```

---

#### Step 3.2 — Qdrant

```bash
curl -s --max-time 3 http://localhost:6333/healthz 2>/dev/null
```

If not running and Docker is available:
```
Qdrant vector database is not running.
Qdrant enables semantic search via project-rag-search.

```bash
python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Start Qdrant using Docker?" --options "Yes|No" --default "No"
```

If `y`:
```bash
docker pull qdrant/qdrant
docker run -d \
  -p 6333:6333 \
  -p 6334:6334 \
  -v "$(pwd)/.qdrant_storage:/qdrant/storage" \
  --name qdrant \
  --restart unless-stopped \
  qdrant/qdrant

# Verify
sleep 3
curl -s http://localhost:6333/healthz
```

After starting, check if configured collection exists:
```bash
COLLECTION=$(cat .agents/memory.config.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('vector_collection',''))" 2>/dev/null)

curl -s http://localhost:6333/collections/$COLLECTION 2>/dev/null
```

If collection missing:
```
Collection "[name]" does not exist in Qdrant.

```bash
python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Create collection?" --options "Yes|No" --default "No"
```

---

#### Step 3.3 — QMD CLI

```bash
qmd --version 2>/dev/null
```

If missing (safe — auto-install):
```bash
# npm preferred
npm install -g @qmd/cli

# pip fallback
pip install qmd

# Verify
qmd --version
```

---

#### Step 3.4 — Embedding Provider Verification

Check all providers. If NONE detected:
```
No embedding provider is configured.
Embedding providers are used for semantic search.
```

```bash
python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Choose embedding provider to configure/install:" --options "Ollama (local, free)|Sentence Transformers (local Python)|OpenAI (cloud, paid)|Google Gemini (cloud)|Anthropic Claude (cloud)|None" --default "None"
```

**Ollama installation (if user confirms):**
```
Installing Ollama and embedding model.
This will download approximately 350MB.

```bash
python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Proceed with Ollama installation?" --options "Yes|No" --default "No"
```

If `y`:
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: download from https://ollama.com/download/windows

# After install:
ollama serve &
sleep 2
ollama pull nomic-embed-text

# Verify
ollama list
```

**Sentence Transformers (if user confirms):**
```bash
pip install sentence-transformers
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

---

### Phase 4 — Initialize Project Configuration

#### Step 4.1 — Create .agents/ Directory Structure

If `.agents/` does not exist:
```
.agents/ directory not found.

```bash
python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Create project AI configuration directory?" --options "Yes|No" --default "No"
```

If `y`:
```bash
mkdir -p .agents/skills
mkdir -p .agents/memory
echo "Created: .agents/"
echo "Created: .agents/skills/"
echo "Created: .agents/memory/"
```

#### Step 4.2 — Initialize Memory Configuration

If `.agents/memory.config.json` does not exist:
```
Project Memory configuration not found.

```bash
python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Initialize .agents/memory.config.json?" --options "Yes|No" --default "No"
```

This will create:
{
  "project_id": "[current-directory-name]",
  "memory_root": ".agents/memory",
  "vector_provider": "none"
}

You can change vector_provider to "qdrant" later when Qdrant is running.
```

If `y`:
```bash
PROJECT_ID=$(basename "$(pwd)" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')

cat > .agents/memory.config.json << EOF
{
  "project_id": "${PROJECT_ID}",
  "memory_root": ".agents/memory",
  "vector_provider": "none",
  "vector_collection": "${PROJECT_ID}-memory",
  "embedding_model": "nomic-embed-text"
}
EOF

echo "Created: .agents/memory.config.json"
echo "project_id: ${PROJECT_ID}"
```

If exists but fields are invalid/missing, print specific field errors:
```
⚠ .agents/memory.config.json has invalid fields:
  ❌ project_id: missing
  ❌ memory_root: missing

```bash
python3 .agents/skills/workflow-runtime/scripts/workflow_runtime.py prompt select --question "Repair configuration?" --options "Yes|No" --default "No"
```

---

### Phase 5 — Verify AI Skills

For each required Skill, check in:
1. `.agents/skills/[skill-name]/SKILL.md`
2. `~/.gemini/config/skills/[skill-name]/SKILL.md`

Required Skills:

| Skill |
|-------|
| `software-development-workflow` |
| `brainstorming` |
| `brainstorming-to-plan` |
| `plan-to-blueprint` |
| `blueprint-to-implementation` |
| `implementation-to-release` |
| `project-memory-bootstrap` |
| `project-memory-update` |
| `project-rag-search` |
| `environment-health` |
| `environment-bootstrap` |

For each **missing** Skill, print:
```
❌ MISSING Skill: [skill-name]

Expected location:
  .agents/skills/[skill-name]/SKILL.md
  OR
  ~/.gemini/config/skills/[skill-name]/SKILL.md

To install this Skill:
  1. Copy the SKILL.md to one of the paths above.
  2. Re-run environment-bootstrap to verify.

This Skill cannot be auto-generated. It must be copied from the Skills repository.
```

---

### Phase 6 — Verify Project Memory State

Read `.agents/memory.config.json` to determine `memory_root`.

Check `<memory_root>/project-summary.md`:
- **Exists and fresh** → Memory ready.
- **Exists but stale** → Recommend `project-memory-update`.
- **Missing** → Recommend `project-memory-bootstrap`.

---

### Phase 7 — Final Bootstrap Report

```
### Environment Bootstrap Report
**Generated:** [ISO8601 timestamp]

Operating System
  [macOS 14.x | Ubuntu 22.04 | Windows 11]
  Package Manager: [brew | apt | winget]

══════════════════════════════════════════════════════════
REQUIRED TOOLS
══════════════════════════════════════════════════════════

Git            [✅ READY | ✅ INSTALLED | ❌ FAILED]
Python         [✅ READY | ✅ INSTALLED | ❌ FAILED]
Node.js        [✅ READY | ✅ INSTALLED | ❌ FAILED]
  npm:         [✅ available]
  npx:         [✅ available]
SQLite         [✅ READY | ✅ INSTALLED | ❌ FAILED]
Tree-sitter    [✅ READY | ✅ INSTALLED | ❌ FAILED]

══════════════════════════════════════════════════════════
OPTIONAL INFRASTRUCTURE
══════════════════════════════════════════════════════════

Docker         [✅ RUNNING | ⚠ SKIPPED | ℹ NOT INSTALLED]
Qdrant         [✅ RUNNING | ⚠ SKIPPED | ℹ NOT CONFIGURED]
Embedding      [✅ AVAILABLE | ⚠ NONE CONFIGURED]
  Provider:    [Ollama | OpenAI | Gemini | Anthropic | Sentence-BERT | none]
QMD            [✅ READY | ✅ INSTALLED | ℹ SKIPPED]

══════════════════════════════════════════════════════════
PROJECT CONFIGURATION
══════════════════════════════════════════════════════════

.agents/               [✅ created | ✅ existed]
.agents/skills/        [✅ created | ✅ existed]
.agents/memory/        [✅ created | ✅ existed]
memory.config.json     [✅ valid | ✅ created | ❌ invalid]
  project_id:          [value]
  memory_root:         [value]
  vector_provider:     [value]

══════════════════════════════════════════════════════════
AI CODING SKILLS
══════════════════════════════════════════════════════════

  software-development-workflow    [✅ FOUND | ❌ MISSING]
  brainstorming          [✅ FOUND | ❌ MISSING]
  brainstorming-to-plan          [✅ FOUND | ❌ MISSING]
  plan-to-blueprint                [✅ FOUND | ❌ MISSING]
  blueprint-to-implementation      [✅ FOUND | ❌ MISSING]
  implementation-to-release        [✅ FOUND | ❌ MISSING]
  project-memory-bootstrap         [✅ FOUND | ❌ MISSING]
  project-memory-update            [✅ FOUND | ❌ MISSING]
  project-rag-search               [✅ FOUND | ❌ MISSING]
  environment-health               [✅ FOUND | ❌ MISSING]
  environment-bootstrap            [✅ FOUND | ❌ MISSING]

══════════════════════════════════════════════════════════
PROJECT MEMORY
══════════════════════════════════════════════════════════

  State: [FRESH | STALE | NOT GENERATED | NOT INITIALIZED]

══════════════════════════════════════════════════════════
OVERALL STATUS
══════════════════════════════════════════════════════════

  [✅ READY | ⚠ PARTIALLY READY | ❌ NOT READY]

══════════════════════════════════════════════════════════
REMAINING ISSUES
══════════════════════════════════════════════════════════

(Only printed if issues remain after bootstrap)

❌ [component]: [what is still needed]
⚠ [component]: [what is recommended]
ℹ [component]: [optional improvement]
```

---

### Phase 8 — Recommend Next Step

**If all required tools are ready AND memory is FRESH:**
```
Environment is fully prepared.

Recommended Next Skill:
software-development-workflow

Workflow Paused.
```

**If all required tools are ready AND memory is NOT GENERATED:**
```
Environment tools are ready.
Project Memory has not been generated yet.

Recommended Next Skill:
project-memory-bootstrap

Run project-memory-bootstrap to generate Project Memory,
then use software-development-workflow to start development.

Workflow Paused.
```

**If all required tools are ready AND memory is STALE:**
```
Environment tools are ready.
Project Memory is stale ([N] days old).

Recommended Next Skill:
project-memory-update

Then run:
software-development-workflow

Workflow Paused.
```

**If required tools have failures:**
```
❌ Environment is NOT fully ready.

Unresolved issues:
[list of failures]

Please resolve the above issues and re-run environment-bootstrap.

Workflow Paused.
```

---

## Parameters

```yaml
workspace: auto
# Current working directory

install_safe: true
# Auto-install safe components without prompting

prompt_unsafe: true
# Prompt before installing unsafe components (Docker, Qdrant, Ollama)

init_memory_config: prompt
# Options: prompt | auto | skip

check_skills: true
# Verify all required AI Skills are present

check_qdrant: true
# Check and optionally start Qdrant

check_embedding: true
# Verify embedding provider availability

network_timeout_seconds: 3
# HTTP health check timeout
```

---

## IDE Skill Hardening & Boundary Rules

### 1. Single Responsibility
Prepare the local environment for AI Coding. Once the Bootstrap Report is printed, STOP.

### 2. Never Execute Next Phase
Do NOT invoke `project-memory-bootstrap`, `software-development-workflow`, or any other Skill automatically. Only recommend.

### 3. Confirmation Before Unsafe Actions
Print `[y/N]` prompts before all unsafe installations. Default is always `N` (no).

### 4. Idempotent
Running multiple times must produce the same result. Skip already-installed components.

### 5. No Memory Generation
Never run `project-memory-bootstrap`. Only initialize `memory.config.json` and recommend the next step.

### 6. No Source Code Modification
Project source files are strictly read-only. Only `.agents/` configuration files may be created.

---

## Completion Contract

```text
=== Environment Bootstrap — Completion Report ===

Current Phase: Environment Bootstrap
Status: Completed

Overall Status: [✅ READY | ⚠ PARTIALLY READY | ❌ NOT READY]

Required Tools:   [N / 5 ready]
Optional Tools:   [N configured]
Skills Found:     [N / 11]
Memory Config:    [VALID | CREATED | INVALID]
Memory State:     [FRESH | STALE | NOT GENERATED | NOT INITIALIZED]

Actions Taken:
  (list installed or configured components)

Remaining Issues:
  (list unresolved items)

Recommended Next Skill:
  [project-memory-bootstrap | project-memory-update | software-development-workflow]

Workflow Paused.
```
