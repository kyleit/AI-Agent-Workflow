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
    echo "      --scope SCOPE   Install scope: project (default) or global (~/.agents)"
    echo "      --assume-global Treat this project as if a global install exists (minimal mode)"
    echo "      --full          Force a full project install even if a global install is detected"
    echo "      --reclaim       With --scope global: after installing globally, slim the CURRENT"
    echo "                      project (remove duplicated payload, downgrade block to a pointer)"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Scope behavior:"
    echo "  --scope global      Installs the shared framework to ~/.agents, injects rules into"
    echo "                      global agent configs, and writes ~/.agents/aiwf-global.json."
    echo "  --scope project     If a global install is detected (marker present or --assume-global),"
    echo "                      installs MINIMAL: project-local state/config/hooks + a thin pointer"
    echo "                      to the global rules, avoiding duplicated prompt content."
    echo ""
    echo "Example:"
    echo "  ./install.sh --force --permission sandbox"
    echo "  ./install.sh --scope global"
}

# Parse options
FORCE=false
PERMISSION=""
DEPS_ONLY=false
SCOPE="project"
ASSUME_GLOBAL=false
FULL_INSTALL=false
RECLAIM=false
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
        --scope)
            SCOPE="$2"
            shift 2
            ;;
        --assume-global)
            ASSUME_GLOBAL=true
            shift
            ;;
        --full)
            FULL_INSTALL=true
            shift
            ;;
        --reclaim)
            RECLAIM=true
            shift
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

if [ "$SCOPE" != "project" ] && [ "$SCOPE" != "global" ]; then
    echo "Invalid --scope: $SCOPE (expected 'project' or 'global')"
    exit 1
fi

# Resolve a Python interpreter (>=3.9) once for scope-helper calls.
PY=""
for cand in python3 python "py -3"; do
    if $cand -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
        PY="$cand"
        break
    fi
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
# Global scope installs to ~/.agents and does not require a Git project.
if [ "$SCOPE" = "project" ]; then
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
else
    PROJECT_ROOT="$(pwd)"
    log_info "Global scope: installing shared framework into \$HOME/.agents"
fi

# Locate the framework package directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCOPE_HELPER="$SCRIPT_DIR/install-lib/aiwf_scope.py"
GLOBAL_HOME_AGENTS="$HOME/.agents"

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

remove_installed_transient_files() {
    local root=$1
    [ -d "$root" ] || return 0
    find "$root" -type d \( \
        -name scratch -o \
        -name __pycache__ -o \
        -name .pytest_cache -o \
        -name .mypy_cache -o \
        -name .ruff_cache \
    \) -prune -exec rm -rf {} +
}

merge_agents_block() {
    local file_path=$1
    local src_agents=$2
    local mode="${BLOCK_MODE:-full}"

    # Preferred: delegate to the shared scope helper so full/stub block rendering
    # and idempotent merging are identical across install.sh and install.ps1.
    if [ -n "$PY" ] && [ -f "$SCOPE_HELPER" ]; then
        if $PY "$SCOPE_HELPER" apply-block --file "$file_path" --mode "$mode" --home "$GLOBAL_HOME_AGENTS"; then
            log_info "Applied AIWF '$mode' rules block to $file_path"
            return 0
        fi
        log_warn "Scope helper failed for $file_path; falling back to inline full block."
    fi

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

GitHub Repository: https://github.com/your-org/AI-Agent-Workflow

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

do_global_install() {
    local target="$GLOBAL_HOME_AGENTS"
    log_info "Installing shared framework payload into $target ..."
    mkdir -p "$target"
    copy_item "$SCRIPT_DIR/AI_RULES.md" "$target/AI_RULES.md" false
    [ -f "$SCRIPT_DIR/SKILLS.md" ] && copy_item "$SCRIPT_DIR/SKILLS.md" "$target/SKILLS.md" false
    [ -d "$SCRIPT_DIR/$SKILL_DIR" ] && copy_item "$SCRIPT_DIR/$SKILL_DIR" "$target/$SKILL_DIR" true
    [ -d "$SCRIPT_DIR/$TEMPLATE_DIR" ] && copy_item "$SCRIPT_DIR/$TEMPLATE_DIR" "$target/$TEMPLATE_DIR" true
    [ -d "$SCRIPT_DIR/agents" ] && copy_item "$SCRIPT_DIR/agents" "$target/agents" true
    [ -d "$SCRIPT_DIR/runtime" ] && copy_item "$SCRIPT_DIR/runtime" "$target/runtime" true
    for governance_dir in contracts policies profiles; do
        [ -d "$SCRIPT_DIR/.agents/$governance_dir" ] && \
            copy_item "$SCRIPT_DIR/.agents/$governance_dir" "$target/$governance_dir" true
    done
    # Ship the scope helper globally so re-runs and uninstall can reuse it.
    mkdir -p "$target/install-lib"
    [ -f "$SCOPE_HELPER" ] && cp "$SCOPE_HELPER" "$target/install-lib/aiwf_scope.py"

    # Inject the FULL managed rules block into global agent configs (idempotent).
    BLOCK_MODE="full"
    merge_agents_block "$target/AGENTS.md" "$SCRIPT_DIR/AGENTS.md"
    mkdir -p "$HOME/.claude" "$HOME/.codex"
    merge_agents_block "$HOME/.claude/CLAUDE.md" "$SCRIPT_DIR/AGENTS.md"
    merge_agents_block "$HOME/.codex/AGENTS.md" "$SCRIPT_DIR/AGENTS.md"

    # Write the detection marker that puts future project installs into minimal mode.
    if [ -n "$PY" ] && [ -f "$SCOPE_HELPER" ]; then
        if $PY "$SCOPE_HELPER" marker-write --version "$VERSION" --home "$target" \
                --agents "claude,codex,antigravity"; then
            log_success "Global marker written: $target/aiwf-global.json"
        fi
    else
        log_warn "No Python interpreter: marker not written; project installs won't auto-detect global."
    fi
    # --reclaim: slim the CURRENT project (migrate an existing full install to minimal).
    if [ "$RECLAIM" = true ]; then
        if [ -n "$PY" ] && [ -f "$SCOPE_HELPER" ] && [ -d "$PROJECT_ROOT/.agents" ]; then
            log_info "Reclaiming existing project install at $PROJECT_ROOT into minimal mode..."
            $PY "$SCOPE_HELPER" slim-project --root "$PROJECT_ROOT" \
                --skill-dir "$SKILL_DIR" --template-dir "$TEMPLATE_DIR" | \
                while read -r line; do log_info "  reclaimed: $line"; done
            log_success "Project reclaimed: duplicated payload removed, rules block downgraded to pointer."
        else
            log_warn "--reclaim: no project .agents at $PROJECT_ROOT (or no Python); nothing to slim."
        fi
    fi

    log_success "Global AIWF install complete at $target."
    log_info "New/existing projects: run './install.sh' (project scope) -> minimal mode automatically."
    if [ "$RECLAIM" = false ]; then
        log_info "To migrate an existing project here: re-run with '--scope global --reclaim' from that project."
    fi
}

# 4. Copy required files/directories (Only if DEPS_ONLY is false)
if [ "$DEPS_ONLY" = false ]; then
    if [ "$SCOPE" = "global" ]; then
        do_global_install
        exit 0
    fi
    # --- Scope resolution: minimal (global present) vs full project install ---
    MINIMAL_MODE=false
    if [ "$SCOPE" = "project" ] && [ -n "$PY" ] && [ -f "$SCOPE_HELPER" ]; then
        DETECT_FLAGS=""
        [ "$ASSUME_GLOBAL" = true ] && DETECT_FLAGS="$DETECT_FLAGS --assume-global"
        [ "$FULL_INSTALL" = true ] && DETECT_FLAGS="$DETECT_FLAGS --full"
        # shellcheck disable=SC2086
        DETECT=$($PY "$SCOPE_HELPER" detect $DETECT_FLAGS 2>/dev/null || echo full)
        [ "$DETECT" = "minimal" ] && MINIMAL_MODE=true
    fi
    if [ "$MINIMAL_MODE" = true ]; then
        BLOCK_MODE="stub"
        log_info "Global AIWF install detected -> MINIMAL project mode: thin pointer only, shared payload (skills/rules/policies) skipped to avoid duplicated prompt content."
    else
        BLOCK_MODE="full"
    fi

    # Managed rules block: full (self-contained) or stub (pointer to global).
    merge_agents_block "AGENTS.md" "$SCRIPT_DIR/AGENTS.md"
    merge_agents_block "$INSTALL_TARGET/AGENTS.md" "$SCRIPT_DIR/AGENTS.md"

    SKILL_ERRORS=0
    if [ "$MINIMAL_MODE" = false ]; then
        # Full project install: ship the shared framework payload.
        copy_item "$SCRIPT_DIR/AI_RULES.md" "AI_RULES.md" false
        copy_item "$SCRIPT_DIR/AI_RULES.md" "$INSTALL_TARGET/AI_RULES.md" false
        copy_item "$SCRIPT_DIR/SKILLS.md" "$INSTALL_TARGET/SKILLS.md" false

        # Validate SKILL.md frontmatter before copying each skill
        validate_skill_md() {
            local skill_md=$1
            local skill_name=$2
            [ -f "$skill_md" ] || return 0
            local first3
            first3=$(head -c 3 "$skill_md" | od -An -tx1 | tr -d ' \n')
            if [ "$first3" = "efbbbf" ]; then
                log_warn "SKIP $skill_name: SKILL.md has UTF-8 BOM — frontmatter unreadable"
                return 1
            fi
            if ! head -n 1 "$skill_md" | grep -q '^---'; then
                log_warn "SKIP $skill_name: SKILL.md has no frontmatter delimiter"
                return 1
            fi
            local fm
            fm=$(awk 'NR > 1 { sub(/\r$/, ""); if ($0 == "---") exit; print }' "$skill_md")
            if ! echo "$fm" | grep -q '^name:'; then
                log_warn "SKIP $skill_name: SKILL.md missing 'name:' in frontmatter"
                return 1
            fi
            if ! echo "$fm" | grep -q '^description:'; then
                log_warn "SKIP $skill_name: SKILL.md missing 'description:' in frontmatter"
                return 1
            fi
            return 0
        }

        if [ -d "$SCRIPT_DIR/$SKILL_DIR" ]; then
            mkdir -p "$INSTALL_TARGET/$SKILL_DIR"
            for skill_src in "$SCRIPT_DIR/$SKILL_DIR"/*/; do
                [ -d "$skill_src" ] || continue
                local_skill_name=$(basename "$skill_src")
                skill_md_path="$skill_src/SKILL.md"
                if validate_skill_md "$skill_md_path" "$local_skill_name"; then
                    copy_item "$skill_src" "$INSTALL_TARGET/$SKILL_DIR/$local_skill_name" true
                else
                    log_warn "Keeping existing mirror for $local_skill_name (source has invalid SKILL.md)"
                    SKILL_ERRORS=$((SKILL_ERRORS + 1))
                fi
            done
        fi
        copy_item "$SCRIPT_DIR/$TEMPLATE_DIR" "$INSTALL_TARGET/$TEMPLATE_DIR" true
        copy_item "$SCRIPT_DIR/agents" "$INSTALL_TARGET/agents" true
        copy_item "$SCRIPT_DIR/runtime" "$INSTALL_TARGET/runtime" true

        # Provision the governance assets consumed by architecture and language
        # gates without copying the source repository's runtime state.
        for governance_dir in contracts policies profiles; do
            if [ -d "$SCRIPT_DIR/.agents/$governance_dir" ]; then
                copy_item "$SCRIPT_DIR/.agents/$governance_dir" "$INSTALL_TARGET/$governance_dir" true
            fi
        done
    else
        log_info "Skipped shared payload (AI_RULES.md, skills, templates, agents, runtime, contracts/policies/profiles) — provided by the global install at $GLOBAL_HOME_AGENTS."
    fi

    # Deploy AIWF source-write-gate enforcement (git hooks + gate core) and wire
    # git core.hooksPath so every AI/editor is blocked from committing
    # unapproved source changes.
    if [ -d "$SCRIPT_DIR/githooks" ]; then
        copy_item "$SCRIPT_DIR/githooks" "$INSTALL_TARGET/githooks" true
        chmod +x "$INSTALL_TARGET/githooks/pre-commit" "$INSTALL_TARGET/githooks/pre-push" 2>/dev/null || true
    fi
    if [ -d "$SCRIPT_DIR/aiwf-hooks" ]; then
        copy_item "$SCRIPT_DIR/aiwf-hooks" "$INSTALL_TARGET/aiwf-hooks" true
    fi
    # Keep the historical project-local command working as a thin bridge.
    # Bridge-mode projects do not receive a second gate implementation: this
    # file delegates to the authoritative launcher under .agents/aiwf-hooks.
    PROJECT_GATE_BRIDGE_DIR="$PROJECT_ROOT/tools/aiwf-hooks"
    PROJECT_GATE_BRIDGE_SRC="$SCRIPT_DIR/aiwf-hooks/aiwf_gate_bridge.py"
    PROJECT_GATE_BRIDGE="$PROJECT_GATE_BRIDGE_DIR/aiwf_gate.py"
    if [ -f "$PROJECT_GATE_BRIDGE_SRC" ] && [ ! -e "$PROJECT_GATE_BRIDGE" ]; then
        mkdir -p "$PROJECT_GATE_BRIDGE_DIR"
        cp "$PROJECT_GATE_BRIDGE_SRC" "$PROJECT_GATE_BRIDGE"
        chmod +x "$PROJECT_GATE_BRIDGE"
        log_info "Created AIWF gate bridge: $PROJECT_GATE_BRIDGE"
    fi
    # Deploy the config-driven release orchestrator (engine + entry).
    if [ -d "$SCRIPT_DIR/aiwf_release" ]; then
        copy_item "$SCRIPT_DIR/aiwf_release" "$INSTALL_TARGET/aiwf_release" true
    fi
    if [ -f "$SCRIPT_DIR/release.py" ]; then
        copy_item "$SCRIPT_DIR/release.py" "$INSTALL_TARGET/release.py" false
    fi
    if command -v git >/dev/null 2>&1 && git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 && [ -d "$INSTALL_TARGET/githooks" ]; then
        git -C "$PROJECT_ROOT" config core.hooksPath ".agents/githooks" 2>/dev/null || true
        log_success "Source-write gate enabled (git core.hooksPath -> .agents/githooks)."
    fi

    # Deploy the Claude Code auto-route layer (Claude-only per-prompt hooks):
    # UserPromptSubmit routes every natural-language prompt through AIWF without
    # requiring the user to type /aiwf; PreToolUse re-uses the source-write gate.
    # Codex and Antigravity route via AGENTS.md (auto-read) + the git hard-gate.
    HOOK_SRC=""
    for h in "$SCRIPT_DIR/aiwf-hooks" "$SCRIPT_DIR/tools/aiwf-hooks"; do
        [ -d "$h" ] && { HOOK_SRC="$h"; break; }
    done
    if [ -n "$HOOK_SRC" ] && [ -f "$HOOK_SRC/aiwf_prompt_router.py" ]; then
        mkdir -p "$INSTALL_TARGET/aiwf-hooks"
        cp "$HOOK_SRC/aiwf_prompt_router.py" "$INSTALL_TARGET/aiwf-hooks/aiwf_prompt_router.py" 2>/dev/null || true
    fi
    if [ -n "$HOOK_SRC" ] && [ -f "$HOOK_SRC/claude-settings.template.json" ]; then
        mkdir -p "$PROJECT_ROOT/.claude"
        if [ ! -e "$PROJECT_ROOT/.claude/settings.json" ]; then
            cp "$HOOK_SRC/claude-settings.template.json" "$PROJECT_ROOT/.claude/settings.json"
            log_success "Claude auto-route hooks installed (.claude/settings.json). Open /hooks or restart Claude Code to activate."
        else
            log_warn "Existing .claude/settings.json kept; merge AIWF hooks from $HOOK_SRC/claude-settings.template.json"
        fi
    fi

    remove_installed_transient_files "$INSTALL_TARGET"
    mkdir -p "$INSTALL_TARGET/docs"
    if [ -f "$SCRIPT_DIR/docs/release-guide.md" ]; then
        copy_item "$SCRIPT_DIR/docs/release-guide.md" "$INSTALL_TARGET/docs/release-guide.md" false
    elif [ -f "$SCRIPT_DIR/docs/features/release-public-export/docs/release-guide.md" ]; then
        copy_item "$SCRIPT_DIR/docs/features/release-public-export/docs/release-guide.md" "$INSTALL_TARGET/docs/release-guide.md" false
    else
        log_warn "release-guide.md not found in source directory, skipping."
    fi
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
    bash "$SCRIPT_DIR/install-aiwf-bin.sh" || log_warn "aiwf binary install skipped - will use PATH or embedded fallback."
else
    log_warn "install-aiwf-bin.sh not found - aiwf binary not bundled. Ensure 'aiwf' is in PATH."
fi

# Legacy: install Python deps only if aiwf is NOT found (backward compat)
if ! command -v aiwf &>/dev/null; then
    log_info "aiwf not found in PATH - installing Python dependencies as fallback..."
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
if [ "${MINIMAL_MODE:-false}" = true ]; then
    # Minimal mode: shared payload is global; only project-local artifacts are required.
    VALIDATE_FILES="AGENTS.md MANIFEST.json"
else
    VALIDATE_FILES="AGENTS.md AI_RULES.md MANIFEST.json $SKILL_DIR $TEMPLATE_DIR agents runtime"
fi
for file in $VALIDATE_FILES; do
    if [ ! -e "$INSTALL_TARGET/$file" ]; then
        log_error "Validation failed: Missing $INSTALL_TARGET/$file"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ "$MISSING_FILES" -gt 0 ]; then
    log_error "Installation was incomplete. Please review warnings above."
    exit 1
fi

if [ "${SKILL_ERRORS:-0}" -gt 0 ]; then
    log_error "Installation completed with warnings: $SKILL_ERRORS skill(s) skipped due to invalid SKILL.md frontmatter."
    exit 1
fi

# 6b. Initialize session with aiwf CLI (uses aiwf init)
if command -v aiwf &>/dev/null; then
    log_info "Initializing aiwf workspace..."
    AIWF_WORKSPACE_ROOT="$PROJECT_ROOT" aiwf init || log_warn "aiwf init failed - workspace dirs may need manual creation."
    log_info "Registering project in global registry..."
    AIWF_WORKSPACE_ROOT="$PROJECT_ROOT" aiwf config --check-only || log_warn "aiwf config check failed."
    remove_installed_transient_files "$INSTALL_TARGET"
else
    log_warn "aiwf CLI not found in PATH - skipping workspace initialization."
    log_warn "Run 'aiwf init' manually after installing the aiwf CLI."
fi

log_success "AI Skill Framework v$VERSION has been successfully installed!"
echo "--------------------------------------------------"
echo "Installation Summary:"
echo "  Location:  $INSTALL_TARGET/"
if [ "${MINIMAL_MODE:-false}" = true ]; then
    echo "  Mode:      MINIMAL (global install detected at $GLOBAL_HOME_AGENTS)"
    echo "  Rules:     $GLOBAL_HOME_AGENTS/AI_RULES.md (global; not duplicated per-project)"
    echo "  Skills:    $GLOBAL_HOME_AGENTS/$SKILL_DIR/ (global)"
    echo "  Project:   state/config/hooks + thin pointer block in AGENTS.md"
else
    echo "  Mode:      FULL project install"
    echo "  Rules:     $INSTALL_TARGET/AI_RULES.md"
    echo "  Skills:    $INSTALL_TARGET/$SKILL_DIR/"
    echo "  Templates: $INSTALL_TARGET/$TEMPLATE_DIR/"
fi
echo "--------------------------------------------------"
log_info "To use these skills, make sure your AI Agent workspace points to $INSTALL_TARGET/."
