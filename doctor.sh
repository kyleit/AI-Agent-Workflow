#!/usr/bin/env bash
# ==============================================================================
# AI Skill Framework Diagnostic Tool (doctor)
# Verifies the global and local framework installation state.
# ==============================================================================

set -euo pipefail

# Logging helpers
log_info() { echo -e "\033[1;34m[INFO]\033[0m $1"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }
log_error() { echo -e "\033[1;31m[ERROR]\033[0m $1"; }
log_success() { echo -e "\033[1;32m[SUCCESS]\033[0m $1"; }

STATUS_PASS=0
STATUS_WARN=0
STATUS_FAIL=0

check_item() {
    local label=$1
    local condition=$2
    local rec=$3

    if eval "$condition"; then
        log_success "  [PASS] $label"
    else
        if [ "$rec" = "critical" ]; then
            log_error "  [FAIL] $label"
            STATUS_FAIL=$((STATUS_FAIL + 1))
        else
            log_warn "  [WARN] $label"
            log_warn "         -> Recommendation: $rec"
            STATUS_WARN=$((STATUS_WARN + 1))
        fi
    fi
}

echo "=================================================="
echo "      AI Skill Framework Doctor Diagnostic        "
echo "=================================================="

# Locate SCRIPT_DIR
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Helper to read JSON values
get_manifest_val() {
    local key=$1
    local file=$2
    if [ -f "$file" ]; then
        grep -o -E '"'"$key"'"\s*:\s*"[^"]*"' "$file" | head -n 1 | cut -d'"' -f4 || echo ""
    else
        echo ""
    fi
}

# Check 1: MANIFEST.json present
check_item "MANIFEST.json exists in framework" \
           "[ -f '$SCRIPT_DIR/MANIFEST.json' ]" \
           "critical"

# Check 2: Version is readable
VERSION=$(get_manifest_val "version" "$SCRIPT_DIR/MANIFEST.json")
check_item "Framework version is readable (v$VERSION)" \
           "[ ! -z '$VERSION' ]" \
           "critical"

# Check 3: Skills directory exists
SKILL_DIR=$(get_manifest_val "skill_directory" "$SCRIPT_DIR/MANIFEST.json")
SKILL_DIR=${SKILL_DIR:-skills}
check_item "Skills directory exists ($SKILL_DIR/)" \
           "[ -d '$SCRIPT_DIR/$SKILL_DIR' ]" \
           "critical"

# Check 4: Templates directory exists
TEMPLATE_DIR=$(get_manifest_val "template_directory" "$SCRIPT_DIR/MANIFEST.json")
TEMPLATE_DIR=${TEMPLATE_DIR:-templates}
check_item "Templates directory exists ($TEMPLATE_DIR/)" \
           "[ -d '$SCRIPT_DIR/$TEMPLATE_DIR' ]" \
           "critical"

# Check 5: CLI wrapper available in PATH
check_item "aiwf CLI wrapper is available in PATH" \
           "command -v aiwf >/dev/null 2>&1" \
           "Add ~/.local/share/aiwf/bin or global executable path to your PATH environment variable."

# Check 5.5: API Keys for AI Providers (Gemini / Anthropic)
HAS_GEMINI_KEY=${GEMINI_API_KEY:-""}
HAS_ANTHROPIC_KEY=${ANTHROPIC_API_KEY:-""}
check_item "AI Provider API Key is configured (Gemini or Anthropic)" \
           "[ ! -z '$HAS_GEMINI_KEY' ] || [ ! -z '$HAS_ANTHROPIC_KEY' ]" \
           "Set either GEMINI_API_KEY or ANTHROPIC_API_KEY environment variable to use AI coding skills."

# Check 6: Check active project environment
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
    log_info "Active Git repository detected at $PROJECT_ROOT."
    
    # Check if framework is installed in the active project
    INSTALL_TARGET=$(get_manifest_val "installation_target" "$SCRIPT_DIR/MANIFEST.json")
    INSTALL_TARGET=${INSTALL_TARGET:-.agents}
    
    check_item "Framework installed in active project ($INSTALL_TARGET/)" \
               "[ -d '$INSTALL_TARGET' ]" \
               "Run 'aiwf install' to deploy framework skills into this project."
               
    if [ -d "$INSTALL_TARGET" ]; then
        check_item "AI_RULES.md present in project" \
                   "[ -f '$INSTALL_TARGET/AI_RULES.md' ]" \
                   "Run 'aiwf update --force' to restore missing rules file."
                   
        check_item "MANIFEST.json present in project" \
                   "[ -f '$INSTALL_TARGET/MANIFEST.json' ]" \
                   "Run 'aiwf update --force' to restore missing manifest."
    fi
else
    log_info "No active Git project detected at current path. Skipping local workspace check."
fi

# Check 7: Registry status
if command -v python3 >/dev/null 2>&1; then
    log_info "Diagnosing global project registry..."
    python3 "$SCRIPT_DIR/skills/workflow-runtime/scripts/workflow_runtime.py" registry doctor || log_warn "Failed to diagnose project registry."
fi

echo "=================================================="
echo "Diagnostic Summary:"
echo "  Errors:   $STATUS_FAIL"
echo "  Warnings: $STATUS_WARN"
echo "=================================================="

if [ "$STATUS_FAIL" -gt 0 ]; then
    log_error "STATUS: ERROR"
    log_error "Please fix critical errors to restore framework capabilities."
    exit 1
elif [ "$STATUS_WARN" -gt 0 ]; then
    log_warn "STATUS: WARNING"
    log_warn "Review recommendations to optimize your workspace."
    exit 0
else
    log_success "STATUS: PASS"
    log_success "AI Skill Framework is healthy and ready to use."
    exit 0
fi
