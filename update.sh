#!/usr/bin/env bash
# ==============================================================================
# AI Skill Framework Updater
# Usage: ./update.sh [options]
# Options:
#   -f, --force    Force update even if version is already up to date
#   -h, --help     Show this help message
# ==============================================================================

set -euo pipefail

# Print help message
show_help() {
    echo "AI Skill Framework Updater"
    echo "Usage: ./update.sh [options]"
    echo ""
    echo "Options:"
    echo "  -f, --force    Force update even if version is already up to date"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Example:"
    echo "  ./update.sh --force"
}

# Logging helpers
log_info() { echo -e "\033[1;34m[INFO]\033[0m $1"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }
log_error() { echo -e "\033[1;31m[ERROR]\033[0m $1"; }
log_success() { echo -e "\033[1;32m[SUCCESS]\033[0m $1"; }

# Parse options
FORCE=false
UPDATE_ALL=false
UPDATE_CURRENT=false
for arg in "$@"; do
    case $arg in
        -f|--force)
            FORCE=true
            ;;
        -a|--all)
            UPDATE_ALL=true
            ;;
        -c|--current)
            UPDATE_CURRENT=true
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
    esac
done

# Locate SCRIPT_DIR
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$UPDATE_ALL" = true ]; then
    log_info "Updating all registered projects globally..."
    python3 "$SCRIPT_DIR/skills/workflow-runtime/scripts/workflow_runtime.py" update --all
    exit 0
fi

# Verify MANIFEST.json exists in source
if [ ! -f "$SCRIPT_DIR/MANIFEST.json" ]; then
    log_error "MANIFEST.json not found in source directory ($SCRIPT_DIR)."
    exit 1
fi

# Helper to read JSON values
get_manifest_val() {
    local key=$1
    local file=$2
    grep -o -E '"'"$key"'"\s*:\s*"[^"]*"' "$file" | head -n 1 | cut -d'"' -f4 || echo ""
}

# Helper to extract skills list
get_skills_list() {
    local file=$1
    python3 -c "
import json, sys
try:
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        data = json.load(f)
    skills = data.get('skills', [])
    names = []
    for s in skills:
        if isinstance(s, dict):
            names.append(s.get('name'))
        else:
            names.append(str(s))
    print(' '.join(filter(None, names)))
except Exception:
    pass
" "$file"
}

SRC_INSTALL_TARGET=$(get_manifest_val "installation_target" "$SCRIPT_DIR/MANIFEST.json")
SRC_VERSION=$(get_manifest_val "version" "$SCRIPT_DIR/MANIFEST.json")
SRC_SKILL_DIR=$(get_manifest_val "skill_directory" "$SCRIPT_DIR/MANIFEST.json")
SRC_TEMPLATE_DIR=$(get_manifest_val "template_directory" "$SCRIPT_DIR/MANIFEST.json")

# Verify current directory has target installation
is_git_worktree() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1
}

get_git_root() {
  git rev-parse --show-toplevel 2>/dev/null
}

IS_GIT_REPO=false
PROJECT_ROOT="."

if command -v git &> /dev/null && is_git_worktree; then
    IS_GIT_REPO=true
    PROJECT_ROOT="$(get_git_root)"
elif [ -d ".git" ] || [ -f ".git" ]; then
    IS_GIT_REPO=true
    PROJECT_ROOT="."
fi

if [ "$IS_GIT_REPO" = true ]; then
    cd "$PROJECT_ROOT" || exit 1
fi

TARGET_MANIFEST="$SRC_INSTALL_TARGET/MANIFEST.json"
if [ ! -f "$TARGET_MANIFEST" ]; then
    log_error "No active installation found at $SRC_INSTALL_TARGET/MANIFEST.json"
    log_error "Please run install.sh first to set up the framework."
    exit 1
fi

TARGET_VERSION=$(get_manifest_val "version" "$TARGET_MANIFEST")
log_info "Detected Installed Version: v$TARGET_VERSION"
log_info "Available Repository Version: v$SRC_VERSION"

# Version comparison
if [ "$SRC_VERSION" = "$TARGET_VERSION" ] && [ "$FORCE" = false ]; then
    log_success "AI Skill Framework is already up to date (v$TARGET_VERSION)."
    exit 0
fi

# Function to check version newer (simple string/integer comparison)
# Returns 0 if newer, 1 otherwise
version_gt() {
    test "$(echo "$@" | tr " " "\n" | sort -rV | head -n 1)" == "$1";
}

if ! version_gt "$SRC_VERSION" "$TARGET_VERSION" && [ "$FORCE" = false ]; then
    log_warn "Installed version v$TARGET_VERSION is newer than source version v$SRC_VERSION."
    log_warn "Use --force to downgrade."
    exit 1
fi

log_info "Synchronizing installation..."

# Calculate changes in skills
SRC_SKILLS=$(get_skills_list "$SCRIPT_DIR/MANIFEST.json")
TARGET_SKILLS=$(get_skills_list "$TARGET_MANIFEST")

NEW_SKILLS=""
UPDATED_SKILLS=""
REMOVED_SKILLS=""

for skill in $SRC_SKILLS; do
    if echo "$TARGET_SKILLS" | grep -q "^$skill$"; then
        UPDATED_SKILLS="$UPDATED_SKILLS $skill"
    else
        NEW_SKILLS="$NEW_SKILLS $skill"
    fi
done

for skill in $TARGET_SKILLS; do
    if ! echo "$SRC_SKILLS" | grep -q "^$skill$"; then
        REMOVED_SKILLS="$REMOVED_SKILLS $skill"
    fi
done

# Perform copy updates
copy_diff_item() {
    local src=$1
    local dest=$2
    
    # Simple copy if different or doesn't exist
    if [ ! -e "$dest" ] || ! diff -r "$src" "$dest" >/dev/null 2>&1; then
        log_info "Updating: $dest"
        rm -rf "$dest"
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

# Copy changed runtime files
merge_agents_block "$SRC_INSTALL_TARGET/AGENTS.md" "$SCRIPT_DIR/AGENTS.md"
copy_diff_item "$SCRIPT_DIR/AI_RULES.md" "$SRC_INSTALL_TARGET/AI_RULES.md"
copy_diff_item "$SCRIPT_DIR/SKILLS.md" "$SRC_INSTALL_TARGET/SKILLS.md"
copy_diff_item "$SCRIPT_DIR/agents" "$SRC_INSTALL_TARGET/agents"
copy_diff_item "$SCRIPT_DIR/runtime" "$SRC_INSTALL_TARGET/runtime"
mkdir -p "$SRC_INSTALL_TARGET/docs"
copy_diff_item "$SCRIPT_DIR/docs/release-guide.md" "$SRC_INSTALL_TARGET/docs/release-guide.md"
copy_diff_item "$SCRIPT_DIR/MANIFEST.json" "$SRC_INSTALL_TARGET/MANIFEST.json"

# Initialize a clean .session.json if missing, or upgrade if it is in the old flat format
SESSION_FILE="$SRC_INSTALL_TARGET/.session.json"
if [ ! -f "$SESSION_FILE" ] || ! grep -q '"workspace": {' "$SESSION_FILE"; then
    log_info "Creating or upgrading .session.json to the new nested format..."
    cat << 'EOF' > "$SESSION_FILE"
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
    "type": "N/A",
    "id": "N/A",
    "title": "Awaiting active task selection..."
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
  "checkpoint": 1,
  "current_skill": "initialize-workflow",
  "current_step": "Awaiting initial command",
  "context_health": "healthy"
}
EOF
fi

# Update active skills
for skill in $SRC_SKILLS; do
    copy_diff_item "$SCRIPT_DIR/$SRC_SKILL_DIR/$skill" "$SRC_INSTALL_TARGET/$SRC_SKILL_DIR/$skill"
done

# Update templates
if [ -d "$SCRIPT_DIR/$SRC_TEMPLATE_DIR" ]; then
    mkdir -p "$SRC_INSTALL_TARGET/$SRC_TEMPLATE_DIR"
    cp -r "$SCRIPT_DIR/$SRC_TEMPLATE_DIR/"* "$SRC_INSTALL_TARGET/$SRC_TEMPLATE_DIR/" 2>/dev/null || true
fi

# Print report summary
log_success "AI Skill Framework has been successfully updated to v$SRC_VERSION!"
echo "--------------------------------------------------"
echo "Upgrade Summary:"
if [ -n "$NEW_SKILLS" ]; then
    echo "  New Skills:     $NEW_SKILLS"
fi
if [ -n "$UPDATED_SKILLS" ]; then
    echo "  Updated Skills: $UPDATED_SKILLS"
fi
if [ -n "$REMOVED_SKILLS" ]; then
    echo -e "  \033[1;33m[DEPRECATED]\033[0m Legacy skills found in installation target (safe deletion recommended):"
    for rskill in $REMOVED_SKILLS; do
        echo "    - $SRC_INSTALL_TARGET/$SRC_SKILL_DIR/$rskill"
    done
fi
echo "--------------------------------------------------"
log_info "Run project-memory-update to sync changes with Project Memory."
