#!/bin/bash
# notify-telegram: send a local file to Ba as a real Telegram document (not just text/photo).
# Use this for screenshots, reports, logs, zipped artifacts — anything Ba should be able to open
# on his phone/desktop directly from the chat.
#
# Usage: send_file.sh <file_path> [caption_file] [result_file]
#   file_path    : absolute path to the file to send. Telegram's Bot API caps uploads via
#                  sendDocument at 50MB — check size first for anything that might be large
#                  (screen recordings, big archives) and warn/refuse rather than let curl hang.
#   caption_file : optional path to a UTF-8 text file with a short caption (Write tool, not a
#                  bash heredoc, so Vietnamese diacritics survive intact). Omit for no caption.
#   result_file  : optional path to write the outcome to. On success: "SENT: <file_path>". On
#                  failure: "SEND_FAILED: <telegram error body>". If omitted, only prints to stdout.
#
# Real limits to know (Telegram Bot API):
#   - Upload (bot -> Telegram): 50MB max via sendDocument.
#   - Any file Ba later sends back that you need to download: 20MB max fetchable via getFile
#     (a Bot API server-side cap, not something this script can raise).
#
# HARD STANDING RULE (Ba, 2026-07-19): "không gửi code, ko gửi các file bảo mật, chỉ cho gửi file
# báo cáo thôi" — never send source code, never send secrets/credentials, only report-type
# documents. This is enforced below as a real gate (allowed extension + allowed directory), not
# just a comment — do not bypass it even if a task seems to justify sending something else; ask
# Ba to loosen the rule explicitly first if a real need comes up (e.g. he later asks to send a
# zipped report bundle, currently excluded on purpose since a zip can hide anything).

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

FILE_PATH="$1"
CAPTION_FILE="${2:-}"
RESULT_FILE="${3:-}"

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

# Optional proxy fallback (real incident 2026-07-19, see listen.sh for details) — set/clear
# TELEGRAM_PROXY in the config, not here.
if [ -n "${TELEGRAM_PROXY:-}" ]; then
  export https_proxy="${TELEGRAM_PROXY}"
  export HTTPS_PROXY="${TELEGRAM_PROXY}"
fi

export PYTHONIOENCODING=utf-8

API="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}"

if [ ! -f "${FILE_PATH}" ]; then
  echo "SEND_FAILED: file not found: ${FILE_PATH}" | tee ${RESULT_FILE:+"${RESULT_FILE}"}
  exit 1
fi

# --- Report-only gate (Ba's standing rule) ---------------------------------------------------
# 1. Extension allowlist: report/document/image formats only. No source-code extensions, no
#    archives (a .zip can hide anything — excluded on purpose even though listen.sh CAN receive
#    one from Ba; sending one back out is a different, not-yet-approved capability).
# 2. Path allowlist: must live under this repo's docs/ tree (where every report/brainstorming/
#    plan/blueprint/architecture-review already lives by convention) or under a scratchpad/temp
#    directory (for ephemera generated for a report, e.g. an exported chart). Anything under a
#    source directory (backend/, local-frontend/, remote-frontend/, maxcare/, shared-ui/, sdk/) is
#    rejected regardless of extension, and anything with an obviously sensitive name/path segment
#    is rejected regardless of location.
ALLOWED_EXT_REGEX='\.(md|pdf|txt|csv|png|jpg|jpeg)$'
SENSITIVE_REGEX='(\.env|secret|token|credential|password|\.pem$|\.key$|id_rsa|auth\.json|\.agents/config)'

FILE_PATH_LOWER=$(echo "${FILE_PATH}" | tr '[:upper:]' '[:lower:]')

if ! echo "${FILE_PATH_LOWER}" | grep -qE "${ALLOWED_EXT_REGEX}"; then
  echo "SEND_FAILED: blocked by report-only rule — file extension not in the allowlist (md/pdf/txt/csv/png/jpg/jpeg): ${FILE_PATH}" | tee ${RESULT_FILE:+"${RESULT_FILE}"}
  exit 1
fi

if echo "${FILE_PATH_LOWER}" | grep -qE "${SENSITIVE_REGEX}"; then
  echo "SEND_FAILED: blocked by report-only rule — path looks security-sensitive: ${FILE_PATH}" | tee ${RESULT_FILE:+"${RESULT_FILE}"}
  exit 1
fi

if ! echo "${FILE_PATH_LOWER}" | grep -qE '(/docs/|\\\\docs\\\\|/scratchpad/|\\\\scratchpad\\\\|/temp/|\\\\temp\\\\)'; then
  echo "SEND_FAILED: blocked by report-only rule — must be under docs/ or a scratchpad/temp dir, not a source tree: ${FILE_PATH}" | tee ${RESULT_FILE:+"${RESULT_FILE}"}
  exit 1
fi
# --- end report-only gate ---------------------------------------------------------------------

FILE_SIZE=$("$PYTHON_CMD" -c "import os,sys; print(os.path.getsize(sys.argv[1]))" "${FILE_PATH}")
if [ "${FILE_SIZE}" -gt 52428800 ]; then
  echo "SEND_FAILED: file is ${FILE_SIZE} bytes, over Telegram's 50MB sendDocument limit" | tee ${RESULT_FILE:+"${RESULT_FILE}"}
  exit 1
fi

CURL_ARGS=(-s -X POST "${API}/sendDocument" -F "chat_id=${TELEGRAM_CHAT_ID}" -F "document=@${FILE_PATH}")
if [ -n "${CAPTION_FILE}" ] && [ -f "${CAPTION_FILE}" ]; then
  # Passing Vietnamese text through a bash variable into curl's argv (`-F "caption=${VAR}"`)
  # corrupts the UTF-8 bytes on this machine — the same class of bug documented elsewhere in this
  # skill for text/reply_markup fields. The `-F` fix here is different from `--data-urlencode`'s
  # `field@file` (that always uploads as a file part): for a plain multipart VALUE (not a file
  # upload) curl's own syntax is `field=<filename` (note `<`, not `@`) — reads the file's bytes
  # directly into the field value without going through shell argv at all.
  CURL_ARGS+=(-F "caption=<${CAPTION_FILE}")
fi

RESP=$(curl "${CURL_ARGS[@]}")

if echo "${RESP}" | "$PYTHON_CMD" -c "import json,sys; sys.exit(0 if json.load(sys.stdin).get('ok') else 1)"; then
  echo "SENT: ${FILE_PATH}" | tee ${RESULT_FILE:+"${RESULT_FILE}"}
  exit 0
else
  echo "SEND_FAILED: ${RESP}" | tee ${RESULT_FILE:+"${RESULT_FILE}"}
  exit 1
fi
