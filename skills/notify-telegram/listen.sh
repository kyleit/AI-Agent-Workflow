#!/bin/bash
# notify-telegram: continuous listen mode — waits for ANY next message Ba sends on Telegram
# (not tied to a specific pending question), so Ba can message Claude at any time and have it
# picked up as real input to this session, approximating an always-on conversation channel.
#
# Usage: listen.sh <inbox_file> <offset_state_file> [max_rounds] [long_poll_seconds]
#   inbox_file        : outcome written here per run (one line per item, newline-joined if Ba
#                        sent several while Claude was busy):
#                          "<text>"                                   — a plain typed message
#                          "PHOTO_RECEIVED: <local_path> | caption: ." — an inline/compressed photo
#                          "FILE_RECEIVED: <local_path> (N KB) | caption: ." — a document attachment
#                                                                       (zip/markdown/pdf/anything)
#                          "IDLE_TIMEOUT: no message received after ~Ns"
#                        Read the local_path with the Read tool to actually view/process it.
#   offset_state_file : persists the last-consumed Telegram update_id across repeated invocations
#                        of this script, so re-arming the listener never re-processes an old
#                        message and never misses one that arrived in the brief gap between one
#                        invocation ending and the next starting (unlike poll_reply.sh's
#                        "baseline = now" reset, which is fine for a single one-shot question but
#                        wrong for a persistent listener that gets relaunched over and over).
#   max_rounds, long_poll_seconds: same meaning as poll_reply.sh (defaults 15, 25 => ~6.25 min).
#
# Design: Claude relaunches this script in the background every time it completes (whether a
# message arrived or it idle-timed-out), forming a perpetual loop for as long as this Claude Code
# session keeps running — this is what makes Telegram feel like a second, always-on channel for
# this same conversation, per Ba's request (2026-07-19): "chạy cùng session để tôi trao đổi liên
# tục... thay vì xong task hay cần hỏi mới kích hoạt."
#
# Real limitation (tell Ba this): this loop only advances while Claude keeps getting re-invoked
# (task-notification -> new turn -> relaunch). If the Claude Code session itself is closed, the
# loop stops — this is not a truly independent always-on server process.

set -euo pipefail

PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
  if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
  else
    echo "Error: Python is required but not installed." >&2
    exit 1
  fi
fi

INBOX_FILE="$1"
OFFSET_STATE_FILE="$2"
MAX_ROUNDS="${3:-15}"
LONG_POLL="${4:-25}"

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR=""
while [ -n "$CURRENT_DIR" ] && [ "$CURRENT_DIR" != "/" ]; do
  if [ -d "$CURRENT_DIR/.agents" ]; then
    AGENTS_DIR="$CURRENT_DIR/.agents"
    break
  fi
  PARENT_DIR="$(dirname "$CURRENT_DIR")"
  if [ "$PARENT_DIR" = "$CURRENT_DIR" ]; then
    break
  fi
  CURRENT_DIR="$PARENT_DIR"
done

if [ -n "$AGENTS_DIR" ] && [ -f "$AGENTS_DIR/config/.env.telegram-notify" ]; then
  set -a
  source "$AGENTS_DIR/config/.env.telegram-notify"
  set +a
else
  echo "Error: .agents/config/.env.telegram-notify not found!" >&2
  exit 1
fi

# If TELEGRAM_PROXY is set (real incident 2026-07-19: direct connectivity to api.telegram.org
# dropped from this machine, confirmed via a bare `curl https://api.telegram.org` timing out with
# HTTP 000; Ba supplied a working local proxy), route both curl AND Python's urllib (which also
# honors these env vars by default) through it. Remove/empty TELEGRAM_PROXY in the config once
# direct connectivity is confirmed restored.
if [ -n "${TELEGRAM_PROXY:-}" ]; then
  export https_proxy="${TELEGRAM_PROXY}"
  export HTTPS_PROXY="${TELEGRAM_PROXY}"
fi

export PYTHONIOENCODING=utf-8

# Discover project name from MANIFEST.json for project-scoped messaging
PROJECT_ROOT="$(dirname "$AGENTS_DIR")"
MANIFEST_FILE="${PROJECT_ROOT}/MANIFEST.json"
PROJECT_NAME="default"
if [ -f "${MANIFEST_FILE}" ]; then
  PROJECT_NAME=$($PYTHON_CMD -c "import json; print(json.load(open('${MANIFEST_FILE}'))['name'])" 2>/dev/null || echo "default")
fi
PROJECT_NAME_LOWER=$(echo "${PROJECT_NAME}" | tr '[:upper:]' '[:lower:]')

API="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}"

if [ -f "${OFFSET_STATE_FILE}" ]; then
  OFFSET=$(cat "${OFFSET_STATE_FILE}")
else
  # First run ever: skip pre-existing history, only listen from here forward.
  BASELINE=$(curl -s "${API}/getUpdates" | "$PYTHON_CMD" -c "
import json, sys
d = json.load(sys.stdin)
ids = [u['update_id'] for u in d.get('result', [])]
print(max(ids) if ids else 0)
")
  OFFSET=$((BASELINE + 1))
fi

PHOTOS_DIR="${INBOX_FILE}.photos"
FILES_DIR="${INBOX_FILE}.files"
mkdir -p "${PHOTOS_DIR}" "${FILES_DIR}"

for i in $(seq 1 "${MAX_ROUNDS}"); do
  RESP=$(curl -s --max-time "$((LONG_POLL + 10))" "${API}/getUpdates?offset=${OFFSET}&timeout=${LONG_POLL}")
  RAW_FILE="${INBOX_FILE}.raw.txt"
  rm -f "${RAW_FILE}"
  # Handles BOTH text and photo messages. A photo-only message (no caption) has no 'text' key —
  # the earlier version of this script silently dropped these while still advancing the offset
  # past them, permanently losing the image (Telegram's API never returns an already-consumed
  # update again). Real incident, 2026-07-19: Ba sent a screenshot for review and it vanished.
  # Fix: detect `photo` on the message, resolve the largest size via getFile, and download the
  # actual image bytes (via urllib, stdlib only) into PHOTOS_DIR before the offset advances past
  # it, so nothing is ever silently skipped again.
  NEW_OFFSET=$(echo "${RESP}" | "$PYTHON_CMD" -c "
import json, sys, os, urllib.request
d = json.load(sys.stdin)
chat_id = '${TELEGRAM_CHAT_ID}'
token = '${TELEGRAM_BOT_TOKEN}'
photos_dir = r'${PHOTOS_DIR}'
files_dir = r'${FILES_DIR}'

def fetch(file_id, dest_dir, fallback_name):
    with urllib.request.urlopen(f'https://api.telegram.org/bot{token}/getFile?file_id={file_id}', timeout=20) as resp:
        file_info = json.load(resp)
    remote_path = file_info['result']['file_path']
    name = fallback_name or os.path.basename(remote_path)
    local_path = os.path.join(dest_dir, name)
    urllib.request.urlretrieve(f'https://api.telegram.org/file/bot{token}/{remote_path}', local_path)
    return local_path

lines = []
max_id = ${OFFSET} - 1
for u in d.get('result', []):
    max_id = max(max_id, u['update_id'])
    msg = u.get('message', {})
    if str(msg.get('chat', {}).get('id')) != chat_id:
        continue
    photo = msg.get('photo')
    document = msg.get('document')
    caption = msg.get('caption')
    text = msg.get('text')
    if photo:
        # Telegram orders photo sizes ascending; last = largest.
        try:
            local_path = fetch(photo[-1]['file_id'], photos_dir, f'{u[\"update_id\"]}.jpg')
            lines.append('PHOTO_RECEIVED: ' + local_path + (' | caption: ' + caption if caption else ''))
        except Exception as e:
            lines.append('PHOTO_DOWNLOAD_FAILED: ' + str(e))
    elif document:
        # Covers zip/markdown/pdf/any-file Ba sends as a Telegram \"document\" attachment (as
        # opposed to a compressed inline photo) — keeps Telegram's own file_name (with update_id
        # prefixed to avoid collisions) so the extension/type is preserved for whoever reads it.
        try:
            real_name = document.get('file_name') or f'{u[\"update_id\"]}.bin'
            local_path = fetch(document['file_id'], files_dir, f'{u[\"update_id\"]}_{real_name}')
            size_kb = round((document.get('file_size') or 0) / 1024, 1)
            lines.append('FILE_RECEIVED: ' + local_path + f' ({size_kb} KB)' + (' | caption: ' + caption if caption else ''))
        except Exception as e:
            lines.append('FILE_DOWNLOAD_FAILED: ' + str(e))
    elif text:
        lines.append(text)
if lines:
    with open(r'${RAW_FILE}', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
print(max_id + 1)
")
  echo "${NEW_OFFSET}" > "${OFFSET_STATE_FILE}"
  if [ -f "${RAW_FILE}" ]; then
    MSG=$(cat "${RAW_FILE}")
    rm -f "${RAW_FILE}"
    
    # Check if message targets this project specifically
    MSG_LOWER=$(echo "${MSG}" | tr '[:upper:]' '[:lower:]')
    IS_FOR_THIS_PROJECT=false
    CLEAN_MSG=""
    
    if [[ "${MSG_LOWER}" == "${PROJECT_NAME_LOWER}"* ]]; then
      IS_FOR_THIS_PROJECT=true
      CLEAN_MSG=$(echo "${MSG}" | cut -d' ' -f2-)
    elif [[ "${MSG_LOWER}" == "["${PROJECT_NAME_LOWER}"]"* ]]; then
      IS_FOR_THIS_PROJECT=true
      CLEAN_MSG=$(echo "${MSG}" | cut -d']' -f2- | sed -e 's/^[[:space:]]*//')
    elif [[ "${MSG_LOWER}" == "${PROJECT_NAME_LOWER}:"* ]]; then
      IS_FOR_THIS_PROJECT=true
      CLEAN_MSG=$(echo "${MSG}" | cut -d':' -f2- | sed -e 's/^[[:space:]]*//')
    fi
    
    if [ "${IS_FOR_THIS_PROJECT}" = "false" ]; then
      # If message targets another project explicitly, skip it
      if [[ "${MSG}" =~ ^\[([a-zA-Z0-9_-]+)\] ]] || [[ "${MSG}" =~ ^([a-zA-Z0-9_-]+): ]]; then
        echo "Message is targeted at another project. Skipping."
        continue
      fi
      # If no project name was specified, fallback as broadcast/global command
      IS_FOR_THIS_PROJECT=true
      CLEAN_MSG="${MSG}"
    fi
    
    # Save clean message without project prefix to inbox
    echo "MESSAGE_RECEIVED: ${CLEAN_MSG}" > "${INBOX_FILE}"
    
    # Ack back showing which project picked up the command
    ACK_FILE="${INBOX_FILE}.ack.txt"
    printf '%s' "✅ [${PROJECT_NAME}] Đã nhận, đang chuyển tiếp cho Agent..." > "${ACK_FILE}"
    curl -s -X POST "${API}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text@${ACK_FILE}" > /dev/null
    rm -f "${ACK_FILE}"
    exit 0
  fi
done

echo "IDLE_TIMEOUT: no message received after ~$((MAX_ROUNDS * LONG_POLL))s" > "${INBOX_FILE}"
exit 0
