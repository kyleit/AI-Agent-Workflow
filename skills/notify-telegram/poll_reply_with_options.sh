#!/bin/bash
# notify-telegram: send a question WITH clickable buttons (Telegram inline keyboard) to Ba, then
# wait for either a button tap or a free-text reply, using long-polling (near-instant).
#
# Usage: poll_reply_with_options.sh <question_file> <options_file> <result_file> [max_rounds] [long_poll_seconds]
#   question_file : UTF-8 text file with the question (Write tool, not a bash heredoc).
#   options_file  : UTF-8 text file, ONE option label per line (each becomes its own button,
#                   stacked vertically). Max practical: ~8-10 short options.
#   result_file   : outcome written here:
#                     "OPTION_SELECTED: <label>"   — Ba tapped a button
#                     "TEXT_RECEIVED: <text>"      — Ba typed a free-text reply instead
#                     "TIMEOUT: no reply received after ~Ns"
#   max_rounds, long_poll_seconds: same as poll_reply.sh (defaults 15, 25 => ~6.25 min total).
#
# Run via the Bash tool with run_in_background:true.

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

QUESTION_FILE="$1"
OPTIONS_FILE="$2"
RESULT_FILE="$3"
MAX_ROUNDS="${4:-15}"
LONG_POLL="${5:-25}"

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

# 1. Baseline offset: ignore everything already pending before this question is sent.
BASELINE=$(curl -s "${API}/getUpdates" | "$PYTHON_CMD" -c "
import json, sys
d = json.load(sys.stdin)
ids = [u['update_id'] for u in d.get('result', [])]
print(max(ids) if ids else 0)
")
OFFSET=$((BASELINE + 1))

# 2. Build the inline keyboard JSON from the options file (index-based callback_data keeps this
#    unambiguous regardless of option text/encoding), writing it straight to a file — passing
#    UTF-8 JSON through a bash variable into curl (`reply_markup=${VAR}`) silently mangles
#    multi-byte characters on this machine (the same class of bug already fixed for `text=`),
#    so this must also go through `--data-urlencode field@file`, never `field=${VAR}` inline.
KEYBOARD_FILE="${RESULT_FILE}.keyboard.json"
"$PYTHON_CMD" -c "
import json, sys
with open(sys.argv[1], encoding='utf-8') as f:
    options = [line.rstrip('\n') for line in f if line.strip()]
keyboard = {'inline_keyboard': [[{'text': opt, 'callback_data': str(i)}] for i, opt in enumerate(options)]}
with open(sys.argv[2], 'w', encoding='utf-8') as out:
    out.write(json.dumps(keyboard, ensure_ascii=False))
" "${OPTIONS_FILE}" "${KEYBOARD_FILE}"

# 3. Send the question with buttons attached. Capture the response and fail loudly instead of
#    silently swallowing a Telegram-side rejection (a real bug from an earlier version of this
#    script: piping this to /dev/null hid a 400 error and the question was never delivered).
SEND_RESP=$(curl -s -X POST "${API}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text@${QUESTION_FILE}" \
  --data-urlencode "reply_markup@${KEYBOARD_FILE}")
if echo "${SEND_RESP}" | "$PYTHON_CMD" -c "import json,sys; sys.exit(0 if json.load(sys.stdin).get('ok') else 1)"; then
  :
else
  echo "SEND_FAILED: ${SEND_RESP}" > "${RESULT_FILE}"
  exit 1
fi

# 4. Long-poll for either a button tap (callback_query) or a free-text message.
for i in $(seq 1 "${MAX_ROUNDS}"); do
  RESP=$(curl -s --max-time "$((LONG_POLL + 10))" "${API}/getUpdates?offset=${OFFSET}&timeout=${LONG_POLL}")
  PARSED=$(echo "${RESP}" | "$PYTHON_CMD" -c "
import json, sys
d = json.load(sys.stdin)
chat_id = '${TELEGRAM_CHAT_ID}'
for u in d.get('result', []):
    cq = u.get('callback_query')
    if cq and str(cq.get('message', {}).get('chat', {}).get('id')) == chat_id:
        print('CALLBACK|' + cq['id'] + '|' + cq['data'])
        break
    msg = u.get('message', {})
    if str(msg.get('chat', {}).get('id')) == chat_id and 'text' in msg:
        print('TEXT|' + msg['text'])
        break
")
  if [ -z "${PARSED}" ]; then
    continue
  fi

  KIND="${PARSED%%|*}"
  REST="${PARSED#*|}"

  if [ "${KIND}" = "CALLBACK" ]; then
    CQ_ID="${REST%%|*}"
    OPTION_INDEX="${REST#*|}"
    # Acknowledge the tap so Telegram clears the button's loading spinner.
    curl -s -X POST "${API}/answerCallbackQuery" \
      --data-urlencode "callback_query_id=${CQ_ID}" > /dev/null
    OPTION_LABEL=$("$PYTHON_CMD" -c "
import sys
with open(sys.argv[1], encoding='utf-8') as f:
    options = [line.rstrip('\n') for line in f if line.strip()]
idx = int(sys.argv[2])
print(options[idx] if 0 <= idx < len(options) else '<unknown option index>')
" "${OPTIONS_FILE}" "${OPTION_INDEX}")
    echo "OPTION_SELECTED: ${OPTION_LABEL}" > "${RESULT_FILE}"
    rm -f "${KEYBOARD_FILE}"
    # Acknowledge the tap back to Ba so he knows it registered (don't tap again).
    ACK_FILE="${RESULT_FILE}.ack.txt"
    printf '%s' "✅ Đã nhận lựa chọn: ${OPTION_LABEL}" > "${ACK_FILE}"
    curl -s -X POST "${API}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text@${ACK_FILE}" > /dev/null
    rm -f "${ACK_FILE}"
    exit 0
  else
    echo "TEXT_RECEIVED: ${REST}" > "${RESULT_FILE}"
    rm -f "${KEYBOARD_FILE}"
    # Acknowledge the free-text reply back to Ba so he knows it registered.
    ACK_FILE="${RESULT_FILE}.ack.txt"
    printf '%s' "✅ Đã nhận trả lời: ${REST}" > "${ACK_FILE}"
    curl -s -X POST "${API}/sendMessage" \
      --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text@${ACK_FILE}" > /dev/null
    rm -f "${ACK_FILE}"
    exit 0
  fi
done

rm -f "${KEYBOARD_FILE}"
echo "TIMEOUT: no reply received after ~$((MAX_ROUNDS * LONG_POLL))s" > "${RESULT_FILE}"
exit 1
