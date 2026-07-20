#!/bin/bash
# notify-telegram: send a question to Ba via Telegram, then wait for his reply using Telegram's
# own long-polling (near-instant — the HTTP request itself blocks server-side until a message
# arrives, instead of sleeping locally and re-asking every N seconds).
#
# Usage: poll_reply.sh <question_file> <result_file> [max_rounds] [long_poll_seconds]
#   question_file    : path to a UTF-8 text file containing the message to send (Write tool, not
#                      a bash heredoc, so Vietnamese diacritics survive intact).
#   result_file      : path to write the outcome to. On success: "REPLY_RECEIVED: <text>". On
#                      timeout: "TIMEOUT: no reply received".
#   max_rounds       : how many long-poll rounds to run (default 15).
#   long_poll_seconds: how long each round blocks waiting for a message (default 25, Telegram's
#                      practical max is ~50). Default total wait ~= 15*25 = 375s (~6.25 min),
#                      safely under the Bash tool's 10-minute cap.
#
# Run this via the Bash tool with run_in_background:true — it blocks for the wait duration, so
# backgrounding it lets Claude keep working and simply gets a task-notification the moment a
# reply arrives (or the window times out).

set -euo pipefail

QUESTION_FILE="$1"
RESULT_FILE="$2"
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

# Optional proxy fallback (real incident 2026-07-19, see listen.sh for details) — set/clear
# TELEGRAM_PROXY in the config, not here.
if [ -n "${TELEGRAM_PROXY:-}" ]; then
  export https_proxy="${TELEGRAM_PROXY}"
  export HTTPS_PROXY="${TELEGRAM_PROXY}"
fi

# Windows' default console codepage (cp1252) breaks Python's stdout the instant it prints any
# non-Latin1 character (emoji, Vietnamese, etc.) with a UnicodeEncodeError. Force real UTF-8 for
# every `python -c` call below.
export PYTHONIOENCODING=utf-8

API="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}"

# 1. Baseline offset: ignore every update that already exists before we ask the question, so an
#    old/stray message never gets misread as the answer to THIS question.
BASELINE=$(curl -s "${API}/getUpdates" | "$PYTHON_CMD" -c "
import json, sys
d = json.load(sys.stdin)
ids = [u['update_id'] for u in d.get('result', [])]
print(max(ids) if ids else 0)
")
OFFSET=$((BASELINE + 1))

# 2. Send the question. Capture the response and fail loudly on a Telegram-side rejection instead
#    of silently discarding it (a real bug found in the sibling buttons-script: piping to
#    /dev/null hid a 400 error and the question was never actually delivered).
SEND_RESP=$(curl -s -X POST "${API}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text@${QUESTION_FILE}")
if ! echo "${SEND_RESP}" | "$PYTHON_CMD" -c "import json,sys; sys.exit(0 if json.load(sys.stdin).get('ok') else 1)"; then
  echo "SEND_FAILED: ${SEND_RESP}" > "${RESULT_FILE}"
  exit 1
fi

# 3. Long-poll for a reply from Ba's chat_id. Each curl call blocks up to LONG_POLL seconds on
#    Telegram's server and returns the instant a new message arrives — no local sleep needed.
for i in $(seq 1 "${MAX_ROUNDS}"); do
  RESP=$(curl -s --max-time "$((LONG_POLL + 10))" "${API}/getUpdates?offset=${OFFSET}&timeout=${LONG_POLL}")
  REPLY=$(echo "${RESP}" | "$PYTHON_CMD" -c "
import json, sys
d = json.load(sys.stdin)
chat_id = '${TELEGRAM_CHAT_ID}'
for u in d.get('result', []):
    msg = u.get('message', {})
    if str(msg.get('chat', {}).get('id')) == chat_id and 'text' in msg:
        print(msg['text'])
        break
")
  if [ -n "${REPLY}" ]; then
    echo "REPLY_RECEIVED: ${REPLY}" > "${RESULT_FILE}"
    # Acknowledge receipt back to Ba immediately, so he knows it landed and doesn't need to
    # re-send/re-tap. Write to a file first (printf, a bash builtin — no subprocess argv
    # involved, so Vietnamese/emoji survive) rather than passing ${REPLY} inline to curl, which
    # is the same class of encoding bug already fixed elsewhere in this skill.
    ACK_FILE="${RESULT_FILE}.ack.txt"
    printf '%s' "✅ Đã nhận câu trả lời: ${REPLY}" > "${ACK_FILE}"
    curl -s -X POST "${API}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text@${ACK_FILE}" > /dev/null
    rm -f "${ACK_FILE}"
    exit 0
  fi
done

echo "TIMEOUT: no reply received after ~$((MAX_ROUNDS * LONG_POLL))s" > "${RESULT_FILE}"
exit 1
