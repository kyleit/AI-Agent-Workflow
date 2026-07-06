#!/usr/bin/env bash
# ==============================================================================
# AI Skill Framework Installer
# Usage: ./install.sh [options]
# Options:
#   -f, --force    Force overwrite of existing files without prompting
#   -h, --help     Show this help message
# ==============================================================================

set -euo pipefail

# Print help message
show_help() {
    echo "AI Skill Framework Installer"
    echo "Usage: ./install.sh [options]"
    echo ""
    echo "Options:"
    echo "  -f, --force    Force overwrite of existing files without prompting"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Example:"
    echo "  ./install.sh --force"
}

# Parse options
FORCE=false
for arg in "$@"; do
    case $arg in
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
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

# 1. Verify current directory is a Git project
if [ ! -d ".git" ]; then
    log_error "The current directory is not a Git repository."
    log_error "The AI Skill Framework must be installed at the root of a Git project."
    exit 1
fi

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

# 4. Copy required files/directories
copy_item "$SCRIPT_DIR/AGENTS.md" "$INSTALL_TARGET/AGENTS.md" false
copy_item "$SCRIPT_DIR/AI_RULES.md" "$INSTALL_TARGET/AI_RULES.md" false
copy_item "$SCRIPT_DIR/$SKILL_DIR" "$INSTALL_TARGET/$SKILL_DIR" true
copy_item "$SCRIPT_DIR/$TEMPLATE_DIR" "$INSTALL_TARGET/$TEMPLATE_DIR" true
copy_item "$SCRIPT_DIR/agents" "$INSTALL_TARGET/agents" true
copy_item "$SCRIPT_DIR/runtime" "$INSTALL_TARGET/runtime" true
mkdir -p "$INSTALL_TARGET/docs"
copy_item "$SCRIPT_DIR/docs/release-guide.md" "$INSTALL_TARGET/docs/release-guide.md" false
copy_item "$SCRIPT_DIR/MANIFEST.json" "$INSTALL_TARGET/MANIFEST.json" false

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

# 5. Validation and Summary
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

log_success "AI Skill Framework v$VERSION has been successfully installed!"
echo "--------------------------------------------------"
echo "Installation Summary:"
echo "  Location:  $INSTALL_TARGET/"
echo "  Rules:     $INSTALL_TARGET/AI_RULES.md"
echo "  Skills:    $INSTALL_TARGET/$SKILL_DIR/"
echo "  Templates: $INSTALL_TARGET/$TEMPLATE_DIR/"
echo "--------------------------------------------------"
log_info "To use these skills, make sure your AI Agent workspace points to $INSTALL_TARGET/."
