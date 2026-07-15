#!/usr/bin/env bash
# ==============================================================================
# AI Skill Framework Updater (Unix/Linux/macOS version)
# Usage: ./update.sh [options]
# Options:
#   -f, --force    Force update even if version is already up to date or downgrade
#   -a, --all      Update all registered projects globally
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
    echo "  -a, --all      Update all registered projects globally"
    echo "  -h, --help     Show this help message"
    echo ""
}

# Logging helpers
log_info() { echo -e "\033[1;34m[INFO]\033[0m $1"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }
log_error() { echo -e "\033[1;31m[ERROR]\033[0m $1"; }
log_success() { echo -e "\033[1;32m[SUCCESS]\033[0m $1"; }

# Parse options
FORCE=false
UPDATE_ALL=false
for arg in "$@"; do
    case $arg in
        -f|--force)
            FORCE=true
            ;;
        -a|--all)
            UPDATE_ALL=true
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

# Compare SemVer versions in Bash
# Returns 1 if v1 > v2, -1 if v1 < v2, 0 if equal
compare_semver() {
    local v1=$(echo "$1" | sed 's/^v//')
    local v2=$(echo "$2" | sed 's/^v//')
    
    if [ "$v1" == "$v2" ]; then
        echo 0
        return
    fi
    
    local main1=$(echo "$v1" | cut -d'-' -f1)
    local pre1=$(echo "$v1" | cut -s -d'-' -f2-)
    
    local main2=$(echo "$v2" | cut -d'-' -f1)
    local pre2=$(echo "$v2" | cut -s -d'-' -f2-)
    
    # Compare main versions
    local IFS='.'
    read -ra m1 <<< "$main1"
    read -ra m2 <<< "$main2"
    IFS=$' \t\n'
    
    for i in 0 1 2; do
        local n1=${m1[$i]:-0}
        local n2=${m2[$i]:-0}
        if (( n1 > n2 )); then
            echo 1
            return
        fi
        if (( n1 < n2 )); then
            echo -1
            return
        fi
    done
    
    # Compare prerelease tags
    if [ -z "$pre1" ] && [ -n "$pre2" ]; then
        echo 1
        return
    fi
    if [ -n "$pre1" ] && [ -z "$pre2" ]; then
        echo -1
        return
    fi
    if [ -z "$pre1" ] && [ -z "$pre2" ]; then
        echo 0
        return
    fi
    
    # Both have prerelease, split by '.'
    local IFS='.'
    read -ra p1 <<< "$pre1"
    read -ra p2 <<< "$pre2"
    IFS=$' \t\n'
    
    local len1=${#p1[@]}
    local len2=${#p2[@]}
    local max=$(( len1 > len2 ? len1 : len2 ))
    
    for ((i=0; i<max; i++)); do
        local part1=${p1[$i]:-}
        local part2=${p2[$i]:-}
        
        if [ -z "$part1" ]; then
            echo -1
            return
        fi
        if [ -z "$part2" ]; then
            echo 1
            return
        fi
        
        if [[ "$part1" =~ ^[0-9]+$ ]] && [[ "$part2" =~ ^[0-9]+$ ]]; then
            if (( 10#$part1 > 10#$part2 )); then
                echo 1
                return
            fi
            if (( 10#$part1 < 10#$part2 )); then
                echo -1
                return
            fi
        else
            if [[ "$part1" > "$part2" ]]; then
                echo 1
                return
            fi
            if [[ "$part1" < "$part2" ]]; then
                echo -1
                return
            fi
        fi
    done
    echo 0
}

# Helper to read JSON values
get_manifest_val() {
    local key=$1
    local file=$2
    grep -o -E '"'"$key"'"\s*:\s*"[^"]*"' "$file" | head -n 1 | cut -d'"' -f4 || echo ""
}

SRC_INSTALL_TARGET=".agents"
TARGET_MANIFEST="$SRC_INSTALL_TARGET/MANIFEST.json"
SESSION_FILE="$SRC_INSTALL_TARGET/.session.json"
CONTEXT_FILE="$SRC_INSTALL_TARGET/state/context.json"

CURRENT_VERSION="0.0.0"
RELEASE_CHANNEL="stable"

# Read version from local installation if exists
if [ -f "$TARGET_MANIFEST" ]; then
    CURRENT_VERSION=$(get_manifest_val "version" "$TARGET_MANIFEST" || echo "0.0.0")
    RELEASE_CHANNEL=$(get_manifest_val "release_channel" "$TARGET_MANIFEST" || echo "stable")
fi

# Override release_channel from context.json or .session.json
if [ -f "$CONTEXT_FILE" ]; then
    RELEASE_CHANNEL=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1])).get('release_channel', 'stable'))" "$CONTEXT_FILE" 2>/dev/null || echo "stable")
elif [ -f "$SESSION_FILE" ]; then
    RELEASE_CHANNEL=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1])).get('release_channel', 'stable'))" "$SESSION_FILE" 2>/dev/null || echo "stable")
fi

if [[ ! "$RELEASE_CHANNEL" =~ ^(stable|beta|alpha)$ ]]; then
    log_warn "Invalid release channel value '$RELEASE_CHANNEL'. Defaulting to 'stable'."
    RELEASE_CHANNEL="stable"
fi

log_info "Detected Installed Version: v$CURRENT_VERSION"
log_info "Release Channel: $RELEASE_CHANNEL"

# Helper for local sync mode (original behavior)
run_local_sync() {
    log_info "Running Local Sync Mode..."
    if [ ! -f "$SCRIPT_DIR/MANIFEST.json" ]; then
        log_error "MANIFEST.json not found in source directory ($SCRIPT_DIR)."
        exit 1
    fi
    local src_version=$(get_manifest_val "version" "$SCRIPT_DIR/MANIFEST.json")
    log_info "Available Repository Version: v$src_version"
    
    local cmp=$(compare_semver "$src_version" "$CURRENT_VERSION")
    if [ "$cmp" -eq 0 ] && [ "$FORCE" = false ]; then
        log_success "AI Skill Framework is already up to date (v$CURRENT_VERSION)."
        exit 0
    fi
    if [ "$cmp" -lt 0 ] && [ "$FORCE" = false ]; then
        log_error "Repository version ($src_version) is older than installed version ($CURRENT_VERSION). Use --force to downgrade."
        exit 1
    fi
    
    copy_diff_item() {
        local src=$1
        local dest=$2
        if [ ! -e "$dest" ] || ! diff -r "$src" "$dest" >/dev/null 2>&1; then
            log_info "Updating: $dest"
            rm -rf "$dest"
            cp -r "$src" "$dest"
        fi
    }
    
    # Merge AGENTS.md block
    if [ -f "$SCRIPT_DIR/AGENTS.md" ] && [ ! -f "$SRC_INSTALL_TARGET/AGENTS.md" ]; then
        cp "$SCRIPT_DIR/AGENTS.md" "$SRC_INSTALL_TARGET/AGENTS.md"
    fi
    
    copy_diff_item "$SCRIPT_DIR/AI_RULES.md" "$SRC_INSTALL_TARGET/AI_RULES.md"
    copy_diff_item "$SCRIPT_DIR/SKILLS.md" "$SRC_INSTALL_TARGET/SKILLS.md"
    copy_diff_item "$SCRIPT_DIR/agents" "$SRC_INSTALL_TARGET/agents"
    copy_diff_item "$SCRIPT_DIR/runtime" "$SRC_INSTALL_TARGET/runtime"
    mkdir -p "$SRC_INSTALL_TARGET/docs"
    copy_diff_item "$SCRIPT_DIR/docs/release-guide.md" "$SRC_INSTALL_TARGET/docs/release-guide.md"
    
    # Copy active skills
    local src_skills=$(python3 -c "import json, sys; print(' '.join([s.get('name') if isinstance(s, dict) else str(s) for s in json.load(open(sys.argv[1])).get('skills', [])]))" "$SCRIPT_DIR/MANIFEST.json" 2>/dev/null || echo "")
    for skill in $src_skills; do
        copy_diff_item "$SCRIPT_DIR/skills/$skill" "$SRC_INSTALL_TARGET/skills/$skill"
    done
    
    # Copy templates
    if [ -d "$SCRIPT_DIR/templates" ]; then
        mkdir -p "$SRC_INSTALL_TARGET/templates"
        cp -r "$SCRIPT_DIR/templates/"* "$SRC_INSTALL_TARGET/templates/" 2>/dev/null || true
    fi
    
    # Update local manifest.json
    python3 -c "
import json, sys
data = json.load(open(sys.argv[1]))
data['release_channel'] = sys.argv[3]
json.dump(data, open(sys.argv[2], 'w'), indent=2, ensure_ascii=False)
" "$SCRIPT_DIR/MANIFEST.json" "$TARGET_MANIFEST" "$RELEASE_CHANNEL"
    
    log_success "AI Skill Framework has been successfully updated locally to v$src_version!"
}

# 3. Fetch online manifest
BASE_URL="https://raw.githubusercontent.com/kyleit/AI-Agent-Workflow/main"
MANIFEST_URL="$BASE_URL/releases/manifest.json"
if [ "$RELEASE_CHANNEL" = "beta" ]; then
    MANIFEST_URL="$BASE_URL/releases/manifest-beta.json"
elif [ "$RELEASE_CHANNEL" = "alpha" ]; then
    MANIFEST_URL="$BASE_URL/releases/manifest-alpha.json"
fi

log_info "Fetching online manifest from $MANIFEST_URL..."
HTTP_CODE=0
MANIFEST_CONTENT=""

if command -v curl &> /dev/null; then
    MANIFEST_CONTENT=$(curl -sSL -w "%{http_code}" -o tmp_manifest.json "$MANIFEST_URL" || echo "000")
    HTTP_CODE="${MANIFEST_CONTENT: -3}"
    MANIFEST_CONTENT="${MANIFEST_CONTENT%???}"
    if [ "$HTTP_CODE" -eq 200 ] && [ -f tmp_manifest.json ]; then
        MANIFEST_CONTENT=$(cat tmp_manifest.json)
        rm -f tmp_manifest.json
    else
        rm -f tmp_manifest.json
        HTTP_CODE=0
    fi
elif command -v wget &> /dev/null; then
    if wget -q -O tmp_manifest.json "$MANIFEST_URL"; then
        HTTP_CODE=200
        MANIFEST_CONTENT=$(cat tmp_manifest.json)
        rm -f tmp_manifest.json
    fi
fi

if [ "$HTTP_CODE" -ne 200 ]; then
    log_warn "Failed to connect to the update server. HTTP status: $HTTP_CODE"
    if [ -f "$SCRIPT_DIR/MANIFEST.json" ]; then
        run_local_sync
        exit 0
    else
        log_error "Offline and no local repository source found. Cannot update."
        exit 1
    fi
fi

# Parse target version using Python
TARGET_VERSION=$(python3 -c "
import json, sys
data = json.loads(sys.argv[1])
channel = sys.argv[2]
ver = data.get('latest_' + channel)
if not ver:
    releases = data.get('releases', [])
    matched = []
    for r in releases:
        c = r.get('channel', 'stable')
        is_ok = False
        if channel == 'alpha':
            is_ok = True
        elif channel == 'beta':
            if c in ('stable', 'beta') or '-rc.' in r.get('version', ''):
                is_ok = True
        else:
            if c == 'stable':
                is_ok = True
        if is_ok:
            matched.append(r)
    if matched:
        def semver_key(r):
            v = r.get('version', '').lstrip('v')
            parts = v.split('-')
            main = [int(x) if x.isdigit() else x for x in parts[0].split('.')]
            pre = parts[1] if len(parts) > 1 else 'z'
            return (main, pre)
        matched.sort(key=semver_key, reverse=True)
        ver = matched[0].get('version')
print(ver or '')
" "$MANIFEST_CONTENT" "$RELEASE_CHANNEL")

if [ -z "$TARGET_VERSION" ]; then
    log_error "Could not find a valid release version for channel '$RELEASE_CHANNEL' in manifest."
    exit 1
fi

DOWNLOAD_URL=$(python3 -c "
import json, sys
data = json.loads(sys.argv[1])
version = sys.argv[2]
for r in data.get('releases', []):
    if r.get('version') == version:
        print(r.get('download_url', ''))
        break
" "$MANIFEST_CONTENT" "$TARGET_VERSION")

EXPECTED_HASH=$(python3 -c "
import json, sys
data = json.loads(sys.argv[1])
version = sys.argv[2]
for r in data.get('releases', []):
    if r.get('version') == version:
        print(r.get('sha256', ''))
        break
" "$MANIFEST_CONTENT" "$TARGET_VERSION")

if [ -z "$DOWNLOAD_URL" ]; then
    log_error "Could not find download URL for version $TARGET_VERSION in manifest."
    exit 1
fi

log_info "Available Online Version: v$TARGET_VERSION"

# Version check
CMP=$(compare_semver "$TARGET_VERSION" "$CURRENT_VERSION")
if [ "$CMP" -eq 0 ] && [ "$FORCE" = false ]; then
    log_success "AI Skill Framework is already up to date (v$CURRENT_VERSION)."
    exit 0
fi
if [ "$CMP" -lt 0 ] && [ "$FORCE" = false ]; then
    log_error "Remote version ($TARGET_VERSION) is older than current version ($CURRENT_VERSION). Downgrade blocked. Use --force to downgrade."
    exit 1
fi

# Download ZIP package
log_info "Downloading release v$TARGET_VERSION from $DOWNLOAD_URL..."
TEMP_ZIP="/tmp/ai-agent-workflow-update.zip"
if [ ! -d "/tmp" ]; then
    TEMP_ZIP="$SCRIPT_DIR/ai-agent-workflow-update.zip"
fi
rm -f "$TEMP_ZIP"

if command -v curl &> /dev/null; then
    curl -sSL -o "$TEMP_ZIP" "$DOWNLOAD_URL"
elif command -v wget &> /dev/null; then
    wget -q -O "$TEMP_ZIP" "$DOWNLOAD_URL"
fi

if [ ! -f "$TEMP_ZIP" ]; then
    log_error "Failed to download ZIP package from $DOWNLOAD_URL"
    exit 1
fi

# Verify Checksum
log_info "Verifying checksum..."
if command -v sha256sum &> /dev/null; then
    CALCULATED_HASH=$(sha256sum "$TEMP_ZIP" | cut -d' ' -f1)
elif command -v shasum &> /dev/null; then
    CALCULATED_HASH=$(shasum -a 256 "$TEMP_ZIP" | cut -d' ' -f1)
else
    CALCULATED_HASH=$(python3 -c "
import hashlib, sys
h = hashlib.sha256()
with open(sys.argv[1], 'rb') as f:
    for chunk in iter(lambda: f.read(65536), b''):
        h.update(chunk)
print(h.hexdigest())
" "$TEMP_ZIP")
fi

CLEAN_EXPECTED_HASH=$(echo "$EXPECTED_HASH" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')
CLEAN_CALCULATED_HASH=$(echo "$CALCULATED_HASH" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')

if [ "$CLEAN_CALCULATED_HASH" != "$CLEAN_EXPECTED_HASH" ]; then
    log_error "Checksum verification failed!"
    log_error "Expected SHA256: $CLEAN_EXPECTED_HASH"
    log_error "Actual SHA256:   $CLEAN_CALCULATED_HASH"
    rm -f "$TEMP_ZIP"
    exit 1
fi
log_success "Checksum verified successfully."

# Backup configurations
log_info "Backing up local configurations..."
BACKUP_TEMP_DIR="$SCRIPT_DIR/.agents_backup_temp"
rm -rf "$BACKUP_TEMP_DIR"
mkdir -p "$BACKUP_TEMP_DIR"

FILES_TO_BACKUP=(
    ".session.json"
    "state"
    "config"
    "memory.config.json"
    "obsidian.config.json"
    "project.config.json"
    "workflow.config.json"
    "release.config.json"
)

for item in "${FILES_TO_BACKUP[@]}"; do
    src_path="$SRC_INSTALL_TARGET/$item"
    if [ -e "$src_path" ]; then
        cp -R "$src_path" "$BACKUP_TEMP_DIR/$item"
    fi
done

# Safe extraction
log_info "Extracting update package..."
try_unzip() {
    if [ -d "$SRC_INSTALL_TARGET" ]; then
        rm -rf "$SRC_INSTALL_TARGET"/*
    else
        mkdir -p "$SRC_INSTALL_TARGET"
    fi

    if command -v unzip &> /dev/null; then
        unzip -q -o "$TEMP_ZIP" -d "$SRC_INSTALL_TARGET"
    else
        python3 -c "
import zipfile, sys
with zipfile.ZipFile(sys.argv[1], 'r') as zip_ref:
    zip_ref.extractall(sys.argv[2])
" "$TEMP_ZIP" "$SRC_INSTALL_TARGET"
    fi

    # Unpack nested directory
    local nested_count=$(ls -1 "$SRC_INSTALL_TARGET" | wc -l | tr -d '[:space:]')
    if [ "$nested_count" -eq 1 ] && [ -d "$SRC_INSTALL_TARGET"/* ]; then
        local nested_dir=$(echo "$SRC_INSTALL_TARGET"/*)
        log_info "Unpacking nested folder: $(basename "$nested_dir")"
        mv "$nested_dir"/* "$SRC_INSTALL_TARGET"/ 2>/dev/null || true
        mv "$nested_dir"/.* "$SRC_INSTALL_TARGET"/ 2>/dev/null || true
        rm -rf "$nested_dir"
    fi
}

if ! try_unzip; then
    log_error "Failed to extract ZIP update. Reverting changes..."
    if [ -d "$BACKUP_TEMP_DIR" ]; then
        mkdir -p "$SRC_INSTALL_TARGET"
        cp -R "$BACKUP_TEMP_DIR"/* "$SRC_INSTALL_TARGET"/ 2>/dev/null || true
        cp -R "$BACKUP_TEMP_DIR"/.* "$SRC_INSTALL_TARGET"/ 2>/dev/null || true
        log_info "Rollback completed. Original configuration restored."
    fi
    rm -f "$TEMP_ZIP"
    rm -rf "$BACKUP_TEMP_DIR"
    exit 1
fi

# Restore configurations
log_info "Restoring configurations..."
if [ -d "$BACKUP_TEMP_DIR" ]; then
    cp -R "$BACKUP_TEMP_DIR"/* "$SRC_INSTALL_TARGET"/ 2>/dev/null || true
    cp -R "$BACKUP_TEMP_DIR"/.* "$SRC_INSTALL_TARGET"/ 2>/dev/null || true
    rm -rf "$BACKUP_TEMP_DIR"
fi

# Update version in target manifest
if [ -f "$TARGET_MANIFEST" ]; then
    python3 -c "
import json, sys
path = sys.argv[1]
ver = sys.argv[2]
channel = sys.argv[3]
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['version'] = ver
    data['release_channel'] = channel
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
except Exception as e:
    print('Warn: failed to update target manifest version:', e)
" "$TARGET_MANIFEST" "$TARGET_VERSION" "$RELEASE_CHANNEL"
fi

rm -f "$TEMP_ZIP"
log_success "AI Skill Framework has been successfully updated online to v$TARGET_VERSION!"
echo "--------------------------------------------------"
log_info "Run doctor.sh to confirm workspace integrity."
