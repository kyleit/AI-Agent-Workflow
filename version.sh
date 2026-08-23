#!/usr/bin/env bash
# ==============================================================================
# AI Skill Framework Version Tool
# Reports active and repository version information.
# ==============================================================================

set -euo pipefail

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

VERSION=$(get_manifest_val "version" "$SCRIPT_DIR/MANIFEST.json")
OS_PLATFORM="$(uname -s) ($(uname -m))"

echo "--------------------------------------------------"
echo "AI Skill Framework CLI"
echo "  Framework Version:  v${VERSION:-unknown}"
echo "  Repository Version: v${VERSION:-unknown}"
echo "  Location:           $SCRIPT_DIR"
echo "  Supported Platform: $OS_PLATFORM"
echo "--------------------------------------------------"
