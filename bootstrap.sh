#!/usr/bin/env bash
# ==============================================================================
# AI Skill Framework Global Bootstrap Installer (Unix)
# Installs the global 'aiwf' command-line interface.
# ==============================================================================

set -euo pipefail

# Logging helpers
log_info() { echo -e "\033[1;34m[INFO]\033[0m $1"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }
log_error() { echo -e "\033[1;31m[ERROR]\033[0m $1"; }
log_success() { echo -e "\033[1;32m[SUCCESS]\033[0m $1"; }

# 1. Detect source framework location (where bootstrap.sh is located)
FRAMEWORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
log_info "Framework source located at: $FRAMEWORK_DIR"

# 2. Determine installation directory for global binary wrapper
INSTALL_DIR="$HOME/.local/share/aiwf"
BIN_DIR="$INSTALL_DIR/bin"
mkdir -p "$BIN_DIR"

# 3. Create the global 'aiwf' executable CLI wrapper
CLI_PATH="$BIN_DIR/aiwf"
log_info "Creating CLI wrapper at: $CLI_PATH"

cat << 'EOF' > "$CLI_PATH"
#!/usr/bin/env bash
# ==============================================================================
# AI Skill Framework Global CLI Wrapper (aiwf)
# ==============================================================================
set -euo pipefail

# Dynamic framework directory replaced during bootstrap
FRAMEWORK_ROOT="REPLACE_FRAMEWORK_ROOT"

show_help() {
    echo "AI Skill Framework CLI"
    echo "Usage: aiwf <command> [options]"
    echo ""
    echo "Commands:"
    echo "  install      Install framework skills into the current Git project"
    echo "  update       Synchronize installed skills with latest repo version"
    echo "  uninstall    Safely remove framework skills from the current project"
    echo "  doctor       Perform diagnostic verification of framework state"
    echo "  version      Report current CLI and repository versions"
    echo "  memory       Manage project memory (bootstrap, update, search)"
    echo "  blueprint    Register or approve design blueprints"
    echo "  registry     Manage centralized global project registry"
    echo "  provider     Manage external knowledge providers (sync, list, config)"
    echo "  sync         Sync project memory/documentation to external providers (e.g. Obsidian)"
    echo "  bootstrap    Run framework environment bootstrap installer"
    echo "  init         Initialize a new project workspace"
    echo "  update-source Update the centralized framework source repository safely via Git"
    echo "  test         Execute unit, integration, or e2e test validation runner"
    echo "  config       Check and bootstrap AIWF runtime services"
    echo "  runtime      Manage runtime daemon, command bus, and policy"
    echo "  workflow     Submit, inspect, track, or manage active SDLC workflows"
    echo "  session      Recover, inspect, lock, or update active workspace sessions"
    echo "  telegram     Manage Telegram global configuration, shared daemon, and project links"
    echo "  var          Execute Visual Agentic Runtime checks/audits (Phase 2)"
    echo "  vir          Legacy alias for var"
    echo "  help         Show this help message"
    echo ""
    echo "Common subcommands:"
    echo "  aiwf config                         Check/register project and start configured services"
    echo "  aiwf config --check-only            Check configuration without starting daemons"
    echo "  aiwf runtime status                 Show runtime daemon and current project context"
    echo "  aiwf runtime start|stop|restart     Manage runtime daemon for this login session"
    echo "  aiwf runtime reload                 Restart runtime daemon and shared Telegram daemon"
    echo "  aiwf runtime enable|disable         Enable/disable runtime daemon login autostart"
    echo "  aiwf telegram status                Show Telegram daemon and project link status"
    echo "  aiwf telegram start|stop|restart    Manage shared Telegram daemon"
    echo "  aiwf telegram enable|disable        Enable/disable Telegram daemon login autostart"
    echo "  aiwf telegram config|link           Configure Telegram token or link project chat"
    echo "  aiwf prompt select --question ...   Show a runtime-visible structured approval prompt"
}

if [ $# -lt 1 ]; then
    show_help
    exit 1
fi

COMMAND=$1
shift

case "$COMMAND" in
    bootstrap)
        "$FRAMEWORK_ROOT/bootstrap.sh" "$@"
        ;;
    init)
        python3 "$FRAMEWORK_ROOT/skills/workflow-runtime/scripts/workflow_runtime.py" init "$@"
        ;;
    update-source)
        python3 "$FRAMEWORK_ROOT/skills/workflow-runtime/scripts/workflow_runtime.py" update-source "$@"
        ;;
    test)
        python3 "$FRAMEWORK_ROOT/skills/workflow-runtime/scripts/workflow_runtime.py" test "$@"
        ;;
    install)
        "$FRAMEWORK_ROOT/install.sh" "$@"
        ;;
    update)
        "$FRAMEWORK_ROOT/update.sh" "$@"
        ;;
    uninstall)
        "$FRAMEWORK_ROOT/uninstall.sh" "$@"
        ;;
    doctor)
        "$FRAMEWORK_ROOT/doctor.sh" "$@"
        ;;
    version)
        "$FRAMEWORK_ROOT/version.sh" "$@"
        ;;
    memory)
        python3 "$FRAMEWORK_ROOT/runtime/scripts/project_memory/cli.py" "$@"
        ;;
    blueprint)
        python3 "$FRAMEWORK_ROOT/skills/workflow-runtime/scripts/workflow_runtime.py" blueprint "$@"
        ;;
    registry)
        python3 "$FRAMEWORK_ROOT/skills/workflow-runtime/scripts/workflow_runtime.py" registry "$@"
        ;;
    provider)
        python3 "$FRAMEWORK_ROOT/skills/workflow-runtime/scripts/workflow_runtime.py" provider "$@"
        ;;
    sync)
        python3 "$FRAMEWORK_ROOT/skills/workflow-runtime/scripts/workflow_runtime.py" provider sync "$@"
        ;;
    var|vir)
        python3 "$FRAMEWORK_ROOT/skills/vir-runtime/scripts/vir.py" "$@"
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        python3 "$FRAMEWORK_ROOT/skills/workflow-runtime/scripts/workflow_runtime.py" "$COMMAND" "$@"
        ;;
esac
EOF

# Inject the actual framework directory into the wrapper
# Using sed with alternate delimiter to handle path slashes safely and writing to a temp file
# to maintain compatibility with both macOS (BSD) and Linux (GNU) sed.
sed "s|REPLACE_FRAMEWORK_ROOT|$FRAMEWORK_DIR|g" "$CLI_PATH" > "$CLI_PATH.tmp" && mv "$CLI_PATH.tmp" "$CLI_PATH"
chmod +x "$CLI_PATH"

# 4. PATH Configuration in Shell Profiles
SHELL_PROFILES=()
[ -f "$HOME/.bashrc" ] && SHELL_PROFILES+=("$HOME/.bashrc")
[ -f "$HOME/.zshrc" ] && SHELL_PROFILES+=("$HOME/.zshrc")

PATH_LINE="export PATH=\"\$PATH:$BIN_DIR\""

update_profile() {
    local profile=$1
    if ! grep -Fq "$BIN_DIR" "$profile"; then
        log_info "Adding $BIN_DIR to PATH in $profile"
        echo "" >> "$profile"
        echo "# AI Skill Framework CLI path configuration" >> "$profile"
        echo "$PATH_LINE" >> "$profile"
    else
        log_info "PATH configuration already exists in $profile"
    fi
}

for profile in "${SHELL_PROFILES[@]}"; do
    update_profile "$profile"
done

# 5. Success Summary and verification instructions
log_success "AI Skill Framework CLI wrapper 'aiwf' has been created!"
echo "--------------------------------------------------"
echo "Global Bootstrap Summary:"
echo "  CLI Location:      $CLI_PATH"
echo "  Framework Source:  $FRAMEWORK_DIR"
echo "  Configured Shells: ${SHELL_PROFILES[*]}"
echo "--------------------------------------------------"
log_info "To use the CLI immediately in this terminal, run:"
echo "  export PATH=\"\$PATH:$BIN_DIR\""
echo ""
log_info "Then verify using:  aiwf version"
log_info "Or diagnostic test: aiwf doctor"
