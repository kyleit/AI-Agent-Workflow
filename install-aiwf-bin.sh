#!/usr/bin/env bash
# ==============================================================================
# install-aiwf-bin.sh — Install or update the aiwf CLI binary
#
# Detects the current OS + architecture, copies the matching prebuilt binary
# from the framework's bin/ directory to ~/.local/bin/ (macOS/Linux) or
# %USERPROFILE%\.aiwf\bin\ (Windows via MSYS/Git Bash), and makes it executable.
#
# Called automatically by install.sh and update.sh.
# Can also be run standalone:
#   bash install-aiwf-bin.sh [--bin-dir /path/to/bin] [--dest /path/to/install]
#
# Environment:
#   AIWF_BIN_SRC_DIR   Override the directory containing platform binaries
#   AIWF_BIN_DEST_DIR  Override the install destination directory
# ==============================================================================

set -euo pipefail

log_info()    { echo -e "\033[1;34m[INFO]\033[0m $1"; }
log_warn()    { echo -e "\033[1;33m[WARN]\033[0m $1"; }
log_error()   { echo -e "\033[1;31m[ERROR]\033[0m $1"; }
log_success() { echo -e "\033[1;32m[SUCCESS]\033[0m $1"; }

# ── Detect platform ──────────────────────────────────────────────────────────
detect_platform() {
    local os arch
    os="$(uname -s | tr '[:upper:]' '[:lower:]')"
    arch="$(uname -m)"

    # Normalize arch names
    case "$arch" in
        x86_64|amd64)  arch="amd64" ;;
        aarch64|arm64) arch="arm64" ;;
        *)
            log_error "Unsupported architecture: $arch"
            return 1
            ;;
    esac

    # Normalize OS names
    case "$os" in
        linux)  echo "aiwf_linux_${arch}" ;;
        darwin) echo "aiwf_darwin_${arch}" ;;
        mingw*|msys*|cygwin*|windows*)
            echo "aiwf_windows_${arch}.exe"
            ;;
        *)
            log_error "Unsupported OS: $os"
            return 1
            ;;
    esac
}

# ── Main ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source directory: framework's bin/ next to this script
BIN_SRC_DIR="${AIWF_BIN_SRC_DIR:-$SCRIPT_DIR/bin}"

# Destination: ~/.local/bin on macOS/Linux, ~/.aiwf/bin on Windows-like
if [[ -n "${AIWF_BIN_DEST_DIR:-}" ]]; then
    BIN_DEST_DIR="$AIWF_BIN_DEST_DIR"
elif [[ "$(uname -s)" == MINGW* ]] || [[ "$(uname -s)" == MSYS* ]] || [[ "$(uname -s)" == CYGWIN* ]]; then
    BIN_DEST_DIR="${USERPROFILE:-$HOME}/.aiwf/bin"
else
    BIN_DEST_DIR="${HOME}/.local/bin"
fi

# Detect platform binary name
PLATFORM_BIN="$(detect_platform)" || exit 1
SRC_FILE="$BIN_SRC_DIR/$PLATFORM_BIN"

log_info "aiwf binary: $PLATFORM_BIN"
log_info "Source:      $SRC_FILE"
log_info "Destination: $BIN_DEST_DIR/aiwf"

# Check if source binary exists and is real (not a stub)
if [ ! -f "$SRC_FILE" ]; then
    log_warn "aiwf binary not found at $SRC_FILE — skipping binary install."
    log_warn "The framework will fall back to PATH resolution or manual install."
    exit 0
fi

FSIZE=$(wc -c < "$SRC_FILE" | tr -d ' ')
if [ "$FSIZE" -lt 32 ]; then
    log_warn "aiwf binary at $SRC_FILE appears to be a stub ($FSIZE bytes) — skipping."
    exit 0
fi

# Determine dest binary name (keep .exe on Windows-like)
DEST_NAME="aiwf"
if [[ "$PLATFORM_BIN" == *.exe ]]; then
    DEST_NAME="aiwf.exe"
fi
DEST_FILE="$BIN_DEST_DIR/$DEST_NAME"

# Create destination dir
mkdir -p "$BIN_DEST_DIR"

# Copy binary
cp -f "$SRC_FILE" "$DEST_FILE"
chmod +x "$DEST_FILE"

log_success "aiwf binary installed: $DEST_FILE"

# Hint if destination is not in PATH
case ":$PATH:" in
    *":$BIN_DEST_DIR:"*)
        : ;;
    *)
        log_warn "$BIN_DEST_DIR is not in your PATH."
        log_warn "Add this to your shell profile:"
        log_warn "  export PATH=\"\$PATH:$BIN_DEST_DIR\""
        ;;
esac
