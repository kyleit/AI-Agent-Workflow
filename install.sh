# Options:
#   -f, --force         Force overwrite of existing files without prompting
#   -p, --permission    Set permission mode (sandbox, full_access, unrestricted)
#   -h, --help          Show this help message
# ==============================================================================

set -euo pipefail

# Print help message
show_help() {
    echo "AI Skill Framework Installer"
    echo "Usage: ./install.sh [options]"
    echo ""
    echo "Options:"
    echo "  -f, --force         Force overwrite of existing files without prompting"
    echo "  -d, --deps-only     Only install/verify dependencies without copying files"
    echo "  -p, --permission    Set permission mode (sandbox, full_access, unrestricted)"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Example:"
    echo "  ./install.sh --force --permission sandbox"
}

# Parse options
FORCE=false
PERMISSION=""
DEPS_ONLY=false
while [ $# -gt 0 ]; do
    case "$1" in
        -f|--force)
            FORCE=true
            shift
            ;;
        -d|--deps-only)
            DEPS_ONLY=true
            shift
            ;;
        -p|--permission)
            PERMISSION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Logging helpers
log_info() { echo -e "\033[1;34m[INFO]\033[0m $1"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }
log_error() { echo -e "\033[1;31m[ERROR]\033[0m $1"; }
log_success() { echo -e "\033[1;32m[SUCCESS]\033[0m $1"; }

is_git_worktree() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1
}

get_git_root() {
  git rev-parse --show-toplevel 2>/dev/null
}

# 1. Verify current directory is a Git project (supporting worktrees and submodules)
if ! command -v git &> /dev/null; then
    # Git command not found, check fallback
    if [ -d ".git" ] || [ -f ".git" ]; then
        PROJECT_ROOT="."
    else
        log_error "git command line tool is missing, and no .git folder/file found."
        log_error "Please install git or run this script from a Git repository root."
        exit 1
    fi
else
    # Git command exists
    if ! is_git_worktree; then
        if [ -d ".git" ] || [ -f ".git" ]; then
            PROJECT_ROOT="."
        else
            log_error "The current directory is not a Git repository."
            log_error "The AI Skill Framework must be installed at the root of a Git project."
            exit 1
        fi
    else
        PROJECT_ROOT="$(get_git_root)"
    fi
fi

cd "$PROJECT_ROOT" || exit 1
log_success "Git repository detected."
log_info "Project root: $PROJECT_ROOT"
log_info "Installing AI Skill Framework into $PROJECT_ROOT/.agents"

# Locate the framework package directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Verify MANIFEST.json exists in source
if [ ! -f "$SCRIPT_DIR/MANIFEST.json" ]; then
    log_error "MANIFEST.json not found in source directory ($SCRIPT_DIR)."
    exit 1
fi

# 2. Read MANIFEST.json (using simple bash string extraction to avoid jq dependency)
get_manifest_val() {
    local key=$1
    grep -o -E '"'"$key"'"\s*:\s*"[^"]*"' "$SCRIPT_DIR/MANIFEST.json" | head -n 1 | cut -d'"' -f4 || echo ""
}

INSTALL_TARGET=$(get_manifest_val "installation_target")
SKILL_DIR=$(get_manifest_val "skill_directory")
TEMPLATE_DIR=$(get_manifest_val "template_directory")
VERSION=$(get_manifest_val "version")

if [ -z "$INSTALL_TARGET" ] || [ -z "$SKILL_DIR" ] || [ -z "$TEMPLATE_DIR" ]; then
    log_error "Invalid or corrupt MANIFEST.json in source directory."
    exit 1
fi

log_info "Installing AI Skill Framework v$VERSION..."
log_info "Target Directory: $INSTALL_TARGET/"

# 3. Create target directory if missing
if [ ! -d "$INSTALL_TARGET" ]; then
    log_info "Creating target directory $INSTALL_TARGET/"
    mkdir -p "$INSTALL_TARGET"
fi

# Helper to copy with overwrite check
copy_item() {
    local src=$1
    local dest=$2
    local is_dir=$3

    if [ -e "$dest" ]; then
        if [ "$FORCE" = true ]; then
            log_info "Overwriting: $dest (forced)"
            rm -rf "$dest"
            cp -r "$src" "$dest"
        else
            echo -n -e "\033[1;33m[PROMPT]\033[0m $dest already exists. Overwrite? (y/N): "
            read -r response
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                log_info "Overwriting: $dest"
                rm -rf "$dest"
                cp -r "$src" "$dest"
            else
                log_warn "Skipped: $dest"
            fi
        fi
    else
        log_info "Creating: $dest"
        cp -r "$src" "$dest"
    fi
}

merge_agents_block() {
    local file_path=$1
    local src_agents=$2
    
    local block_content='<!-- AIWF:RULES:BEGIN -->
# AI Engineering Workflow Agents

Every AI agent working inside this project **MUST** follow the AI Workflow Framework.

## Primary Workflow

Before executing any task:

1. Load and follow all policies defined in `AI_RULES.md` (the single source of truth).
2. Load the workflow resources from:

   * `.agents/skills/`
   * `.agents/runtime/`
   * `.agents/templates/`
3. Use the matching workflow Skill whenever one exists.
4. Respect runtime checkpoints and resume rules.
5. Never bypass approval gates or other framework policies.

## Global Policies

The following policies are defined in `AI_RULES.md` and apply to every task:

1. Approval Gate Policy
2. Git Workflow Policy
3. Memory First Policy
4. RAG Policy
5. Artifact Policy
6. Versioning Policy
7. Documentation Policy
8. Testing Policy
9. Release Policy
10. Workflow Phase Separation Policy
11. Absolute Path Prohibition Policy

`AI_RULES.md` is the **single source of truth** for all shared framework behavior. If any instruction conflicts with another document, follow `AI_RULES.md`.

GitHub Repository: https://github.com/kyleit/AI-Agent-Workflow

<!-- AIWF:RULES:END -->'

    if [ ! -f "$file_path" ]; then
        log_info "Creating: $file_path (copying template)"
        cp "$src_agents" "$file_path"
    else
        log_info "Updating managed block in $file_path"
        python3 -c "
import sys, re
file_path = sys.argv[1]
block = sys.argv[2]
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

begin = '<!-- AIWF:RULES:BEGIN -->'
end = '<!-- AIWF:RULES:END -->'
has_begin = begin in content
has_end = end in content

if has_begin and has_end:
    new_content = re.sub(re.escape(begin) + r'.*?' + re.escape(end), block, content, flags=re.DOTALL)
elif has_begin or has_end:
    clean = content.replace(begin, '').replace(end, '').strip()
    new_content = (clean + '\n\n' + block) if clean else block
else:
    trimmed = content.strip()
    new_content = block if not trimmed else trimmed + '\n\n' + block

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)
" "$file_path" "$block_content"
    fi
}

# 4. Copy required files/directories (Only if DEPS_ONLY is false)
if [ "$DEPS_ONLY" = false ]; then
    merge_agents_block "$INSTALL_TARGET/AGENTS.md" "$SCRIPT_DIR/AGENTS.md"
    copy_item "$SCRIPT_DIR/AI_RULES.md" "$INSTALL_TARGET/AI_RULES.md" false
    copy_item "$SCRIPT_DIR/SKILLS.md" "$INSTALL_TARGET/SKILLS.md" false
    copy_item "$SCRIPT_DIR/$SKILL_DIR" "$INSTALL_TARGET/$SKILL_DIR" true
    copy_item "$SCRIPT_DIR/$TEMPLATE_DIR" "$INSTALL_TARGET/$TEMPLATE_DIR" true
    copy_item "$SCRIPT_DIR/agents" "$INSTALL_TARGET/agents" true
    copy_item "$SCRIPT_DIR/runtime" "$INSTALL_TARGET/runtime" true
    mkdir -p "$INSTALL_TARGET/docs"
    copy_item "$SCRIPT_DIR/docs/release-guide.md" "$INSTALL_TARGET/docs/release-guide.md" false
    copy_item "$SCRIPT_DIR/MANIFEST.json" "$INSTALL_TARGET/MANIFEST.json" false

    # Ensure .gitignore exists in target and ignores logs
    ensure_gitignore() {
        local gitignore_file="$INSTALL_TARGET/.gitignore"
        if [ ! -f "$gitignore_file" ]; then
            log_info "Creating: $gitignore_file"
            cat << 'EOF' > "$gitignore_file"
.session.json
state/
runtime/*.db
runtime/*.db-journal
runtime/*.db-wal
runtime/env_cache.json
runtime/logs/
EOF
        else
            if ! grep -Fxq "runtime/logs/" "$gitignore_file" && ! grep -Fxq "runtime/logs" "$gitignore_file"; then
                log_info "Adding runtime/logs/ to $gitignore_file"
                echo "runtime/logs/" >> "$gitignore_file"
            fi
        fi
    }
    ensure_gitignore

    # Initialize a clean .session.json if it doesn't exist
    if [ ! -f "$INSTALL_TARGET/.session.json" ]; then
        log_info "Initializing default .session.json for visualizer UI..."
        cat << 'EOF' > "$INSTALL_TARGET/.session.json"
{
  "workspace": {
    "path": ".",
    "valid": true
  },
  "git": {
    "is_git_repository": true,
    "branch": "main",
    "working_tree": "clean",
    "default_branch": "main",
    "latest_tag": "none"
  },
  "work_item": {
    "type": "FEAT",
    "id": "FEAT-001",
    "title": "Initial Scaffolding"
  },
  "version": {
    "version": "1.0.0",
    "source": "MANIFEST.json"
  },
  "memory": {
    "status": "MISSING",
    "last_updated": ""
  },
  "rag": {
    "connected": false,
    "provider": "none"
  },
  "blueprint": {
    "path": "",
    "exists": false,
    "approved": false,
    "approved_at": "",
    "approved_by": ""
  },
  "suggestion_gate": {
    "active": false,
    "raw_request": "",
    "classification": "",
    "recommended_skill": "",
    "options": [],
    "status": "idle"
  },
  "checkpoint": 1,
  "status": "completed",
  "current_skill": "initialize-workflow",
  "current_command": "init",
  "current_step": "Initialization Complete",
  "current_logs": [
    "> Initialization completed successfully."
  ],
  "suggested_next_skill": "project-discovery",
  "suggested_next_command": "discover",
  "context_health": "healthy"
}
EOF
    fi
fi

# 5. Install aiwf CLI binary
log_info "Installing aiwf CLI binary..."
if [ -f "$SCRIPT_DIR/install-aiwf-bin.sh" ]; then
    bash "$SCRIPT_DIR/install-aiwf-bin.sh" || log_warn "aiwf binary install skipped — will use PATH or embedded fallback."
else
    log_warn "install-aiwf-bin.sh not found — aiwf binary not bundled. Ensure 'aiwf' is in PATH."
fi

# Legacy: install Python deps only if aiwf is NOT found (backward compat)
if ! command -v aiwf &>/dev/null; then
    log_info "aiwf not found in PATH — installing Python dependencies as fallback..."
    if command -v pip3 &>/dev/null; then
        pip3 install --quiet --upgrade pyyaml psutil pytest || log_warn "Failed to install dependencies via pip3."
    elif command -v pip &>/dev/null; then
        pip install --quiet --upgrade pyyaml psutil pytest || log_warn "Failed to install dependencies via pip."
    else
        log_warn "pip/pip3 not found. Install PyYAML, psutil, and pytest manually for Python fallback."
    fi
fi

# If only installing dependencies, exit successfully here
if [ "$DEPS_ONLY" = true ]; then
    log_success "Dependencies installation/verification completed successfully (no files copied)."
    exit 0
fi

# 6. Validation and Summary
MISSING_FILES=0
for file in "AGENTS.md" "AI_RULES.md" "MANIFEST.json" "$SKILL_DIR" "$TEMPLATE_DIR" "agents" "runtime" "docs/release-guide.md"; do
    if [ ! -e "$INSTALL_TARGET/$file" ]; then
        log_error "Validation failed: Missing $INSTALL_TARGET/$file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ "$MISSING_FILES" -gt 0 ]; then
    log_error "Installation was incomplete. Please review warnings above."
    exit 1
fi

# 6b. Initialize session with aiwf CLI (replaces workflow_runtime.py init)
if command -v aiwf &>/dev/null; then
    log_info "Initializing aiwf workspace..."
    AIWF_WORKSPACE_ROOT="$PROJECT_ROOT" aiwf init || log_warn "aiwf init failed — workspace dirs may need manual creation."
    log_info "Registering project in global registry..."
    AIWF_WORKSPACE_ROOT="$PROJECT_ROOT" aiwf config --check-only || log_warn "aiwf config check failed."
elif command -v python3 >/dev/null 2>&1; then
    log_info "Falling back to Python runtime for initialization..."
    INIT_ARGS=""
    if [ -n "$PERMISSION" ]; then
        INIT_ARGS="--permission $PERMISSION"
    fi
    python3 "$INSTALL_TARGET/$SKILL_DIR/workflow-runtime/scripts/workflow_runtime.py" init $INIT_ARGS || log_warn "Failed to sync initial session with SQLite."
    python3 "$INSTALL_TARGET/$SKILL_DIR/workflow-runtime/scripts/workflow_runtime.py" registry register --source install --framework-root "$SCRIPT_DIR" || log_warn "Failed to register project in global registry."
else
    log_warn "Neither aiwf nor python3 found — skipping workspace initialization."
    log_warn "Run 'aiwf init' manually after installing the aiwf CLI."
fi

log_success "AI Skill Framework v$VERSION has been successfully installed!"
echo "--------------------------------------------------"
echo "Installation Summary:"
echo "  Location:  $INSTALL_TARGET/"
echo "  Rules:     $INSTALL_TARGET/AI_RULES.md"
echo "  Skills:    $INSTALL_TARGET/$SKILL_DIR/"
echo "  Templates: $INSTALL_TARGET/$TEMPLATE_DIR/"
echo "--------------------------------------------------"
log_info "To use these skills, make sure your AI Agent workspace points to $INSTALL_TARGET/."
