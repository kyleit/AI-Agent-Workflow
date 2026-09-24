#!/usr/bin/env bash
# ==============================================================================
# AI Skill Framework Uninstaller
# Usage: ./uninstall.sh [options]
# Options:
#   -f, --force    Force uninstall without prompting for confirmation
#   -h, --help     Show this help message
# ==============================================================================

set -euo pipefail

# Print help message
show_help() {
    echo "AI Skill Framework Uninstaller"
    echo "Usage: ./uninstall.sh [options]"
    echo ""
    echo "Options:"
    echo "  -f, --force    Force uninstall without prompting for confirmation"
    echo "  -g, --global   Uninstall the GLOBAL install (~/.agents + marker + global config blocks)"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Example:"
    echo "  ./uninstall.sh --force"
    echo "  ./uninstall.sh --global --force"
}

# Parse options
FORCE=false
GLOBAL_UNINSTALL=false
for arg in "$@"; do
    case $arg in
        -f|--force)
            FORCE=true
            shift
            ;;
        -g|--global)
            GLOBAL_UNINSTALL=true
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

# Global uninstall: remove ~/.agents, the detection marker, and the managed
# rules block from the global agent configs. Does not require a project manifest.
if [ "$GLOBAL_UNINSTALL" = true ]; then
    GLOBAL_HOME_AGENTS="$HOME/.agents"
    PY=""
    for cand in python3 python "py -3"; do
        if $cand -c 'import sys' >/dev/null 2>&1; then PY="$cand"; break; fi
    done
    SCOPE_HELPER="$GLOBAL_HOME_AGENTS/install-lib/aiwf_scope.py"
    [ -f "$SCOPE_HELPER" ] || SCOPE_HELPER="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install-lib/aiwf_scope.py"

    if [ "$FORCE" = false ]; then
        echo -n -e "\033[1;31m[PROMPT]\033[0m Uninstall the GLOBAL AIWF install at $GLOBAL_HOME_AGENTS? (y/N): "
        read -r response
        [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]] || { log_info "Global uninstall cancelled."; exit 0; }
    fi

    if [ -n "$PY" ] && [ -f "$SCOPE_HELPER" ]; then
        $PY "$SCOPE_HELPER" marker-remove && log_info "Removed global marker."
        for cfg in "$HOME/.claude/CLAUDE.md" "$HOME/.codex/AGENTS.md" "$GLOBAL_HOME_AGENTS/AGENTS.md"; do
            [ -f "$cfg" ] && $PY "$SCOPE_HELPER" remove-block --file "$cfg" && log_info "Stripped managed block: $cfg"
        done
    else
        log_warn "No Python/helper: skipped marker + block cleanup. Remove them manually."
        rm -f "$GLOBAL_HOME_AGENTS/aiwf-global.json" 2>/dev/null || true
    fi

    if [ -d "$GLOBAL_HOME_AGENTS" ]; then
        rm -rf "$GLOBAL_HOME_AGENTS"
        log_success "Removed global framework directory: $GLOBAL_HOME_AGENTS"
    fi
    log_success "Global AIWF uninstall complete."
    log_info "Existing projects in minimal mode: re-run './install.sh --full' to restore a full project install."
    exit 0
fi

# Default target directory
INSTALL_TARGET=".agents"
TARGET_MANIFEST="$INSTALL_TARGET/MANIFEST.json"

if [ ! -f "$TARGET_MANIFEST" ]; then
    log_error "No active installation manifest found at $TARGET_MANIFEST"
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
    sed -n '/"skills":[[:space:]]*\[/,/\]/p' "$file" | grep -o -E '"[^"]+"' | sed 's/"//g' | grep -v '^skills$' || echo ""
}

VERSION=$(get_manifest_val "version" "$TARGET_MANIFEST")
SKILL_DIR=$(get_manifest_val "skill_directory" "$TARGET_MANIFEST")
TEMPLATE_DIR=$(get_manifest_val "template_directory" "$TARGET_MANIFEST")
SKILLS=$(get_skills_list "$TARGET_MANIFEST")

# Prompt for confirmation
if [ "$FORCE" = false ]; then
    echo -n -e "\033[1;31m[PROMPT]\033[0m Are you sure you want to uninstall AI Skill Framework v$VERSION? (y/N): "
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        log_info "Uninstallation cancelled."
        exit 0
    fi
fi

log_info "Removing framework-managed files..."

# Safe removal count
REMOVED_FILES_COUNT=0

# 1. Remove individual skills listed in manifest
if [ -d "$INSTALL_TARGET/$SKILL_DIR" ]; then
    for skill in $SKILLS; do
        SKILL_PATH="$INSTALL_TARGET/$SKILL_DIR/$skill"
        if [ -d "$SKILL_PATH" ]; then
            log_info "Removing skill: $SKILL_PATH"
            rm -rf "$SKILL_PATH"
            REMOVED_FILES_COUNT=$((REMOVED_FILES_COUNT + 1))
        fi
    done
    
    # Remove skills/ directory if it is empty
    if [ -z "$(ls -A "$INSTALL_TARGET/$SKILL_DIR" 2>/dev/null)" ]; then
        rmdir "$INSTALL_TARGET/$SKILL_DIR"
    else
        log_warn "Skills folder contains user-customized skills. Folder was not deleted."
    fi
fi

# 2. Remove templates
if [ -d "$INSTALL_TARGET/$TEMPLATE_DIR" ]; then
    # We can delete all files under templates if they exist
    rm -rf "$INSTALL_TARGET/$TEMPLATE_DIR"
    REMOVED_FILES_COUNT=$((REMOVED_FILES_COUNT + 1))
fi

# 3. Remove metadata, rules, agents, and runtime files
if [ -f "$INSTALL_TARGET/AI_RULES.md" ]; then
    log_info "Removing rules: $INSTALL_TARGET/AI_RULES.md"
    rm -f "$INSTALL_TARGET/AI_RULES.md"
    REMOVED_FILES_COUNT=$((REMOVED_FILES_COUNT + 1))
fi

if [ -d "$INSTALL_TARGET/agents" ]; then
    log_info "Removing agents definition directory: $INSTALL_TARGET/agents"
    rm -rf "$INSTALL_TARGET/agents"
    REMOVED_FILES_COUNT=$((REMOVED_FILES_COUNT + 1))
fi

if [ -d "$INSTALL_TARGET/runtime" ]; then
    log_info "Removing runtime directory: $INSTALL_TARGET/runtime"
    rm -rf "$INSTALL_TARGET/runtime"
    REMOVED_FILES_COUNT=$((REMOVED_FILES_COUNT + 1))
fi

if [ -f "$INSTALL_TARGET/docs/release-guide.md" ]; then
    log_info "Removing release guide: $INSTALL_TARGET/docs/release-guide.md"
    rm -f "$INSTALL_TARGET/docs/release-guide.md"
    REMOVED_FILES_COUNT=$((REMOVED_FILES_COUNT + 1))
    if [ -z "$(ls -A "$INSTALL_TARGET/docs" 2>/dev/null)" ]; then
        rmdir "$INSTALL_TARGET/docs"
    fi
fi

if [ -f "$TARGET_MANIFEST" ]; then
    log_info "Removing manifest: $TARGET_MANIFEST"
    rm -f "$TARGET_MANIFEST"
    REMOVED_FILES_COUNT=$((REMOVED_FILES_COUNT + 1))
fi

# 4. Remove .agents folder if empty
if [ -d "$INSTALL_TARGET" ]; then
    if [ -z "$(ls -A "$INSTALL_TARGET" 2>/dev/null)" ]; then
        rmdir "$INSTALL_TARGET"
        log_info "Removed empty target directory: $INSTALL_TARGET/"
    else
        log_warn "$INSTALL_TARGET/ contains other files (e.g. project memory). Directory was not deleted."
    fi
fi

log_success "AI Skill Framework v$VERSION uninstalled successfully!"
echo "--------------------------------------------------"
echo "Uninstall Summary:"
echo "  Removed $REMOVED_FILES_COUNT framework components."
echo "  User configurations and custom memory files were preserved."
echo "--------------------------------------------------"
