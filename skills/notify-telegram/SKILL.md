---
name: notify-telegram
command: notify
aliases:
  - notify-ba
  - telegram-notify
category: notification
tags:
  - telegram
  - notification
  - human-in-the-loop
version: 1.0.0
license: MIT
created_at: 2026-07-19
updated_at: 2026-07-19
description: Sends a Telegram push notification to Ba (the project owner) whenever Claude reaches a point that needs Ba's decision/confirmation before continuing — so Ba can respond promptly instead of the session sitting idle waiting.
runtime_requirements:
  rules: required
  state: none
  approvals: none
  git: none
  memory: none
  rag: none
  workspace_scan: none
  environment: none
  version: none
  provider: none
  usage: none
---

# Skill: Notify Telegram

## Purpose

Ba is not always watching the chat. When Claude hits a point where it genuinely needs Ba's
input before it can continue — a real decision only Ba can make, a confirmation for a
sensitive/irreversible action, an `AskUserQuestion` call, or any other moment where the
session would otherwise sit idle waiting for a reply — this Skill sends a Telegram message to
Ba's phone so Ba can respond promptly instead of the session hanging with no visible progress.

Config: `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — bot **@claude_polling_bot** ("Claude"; Ba
rotated this from an earlier bot, @vitual_node_bot, on 2026-07-19), credentials stored at
`.agents/config/.env.telegram-notify` (gitignored, never commit this file or print its contents
into any shared/public output).

This Skill has four independent parts — use any alone, or combine them:
1. **Fire-and-forget notify** — send a message, don't wait for a reply (see "How to send a
   notification" below).
2. **Ask-and-wait (free text)** — send a message AND wait for Ba's typed reply, using real-time
   long-polling (see "Waiting for Ba's reply" below).
3. **Ask-and-wait (buttons)** — send a message with real Telegram inline-keyboard buttons Ba can
   tap instead of typing, and wait for either the tap or a typed reply (see "Asking with buttons"
   below). Prefer this over free-text whenever the question has a small set of discrete choices
   (matches how `AskUserQuestion` works in this chat) — it's faster for Ba and removes any
   ambiguity about what a one-word reply meant.
4. **Project inbox daemon route** — the shared Telegram daemon picks up ANY message Ba sends at
   ANY time and writes one valid JSON object to `.agents/inbox/inbox.json` inside the registered
   project workspace — see "Project inbox mode" below. This keeps Telegram as an always-on second
   channel without requiring agents to read files outside the project.
5. **Send/receive real files** — send any local file to Ba as a real Telegram document
   (`send_file.sh`), and receive photos or documents (zip/markdown/pdf/anything) Ba sends back,
   downloaded to a local path ready to read/process — see "Sending files" and "Receiving files
   (photos + documents)" below.

## When to use this Skill

**Ba's standing instruction (2026-07-19): use Telegram as a genuine second channel for this
whole conversation, not just a one-off alert.** Concretely:

- An `AskUserQuestion` call — always notify alongside it (use the buttons variant when the
  question has discrete options, matching what's shown in the chat).
- A confirmation request for a risky/destructive/irreversible action.
- **Whenever Claude finishes a significant chunk of work** (a phase, a multi-agent batch, a big
  audit, etc.) **and is about to decide or ask what to do next** — send a short completion
  summary + the next-step question (with buttons if there are discrete options) via
  `poll_reply.sh` / `poll_reply_with_options.sh`, the same way Claude would post an end-of-turn
  summary in this chat. This is what makes it feel like an ongoing conversation happening over
  Telegram, not a single alert-and-forget ping.
- Any other genuine "I am blocked, only Ba can unblock this" moment.

**Still avoid noise** for things that don't need Ba's input at all (e.g. an individual background
sub-agent finishing when 7 others are still running, a routine intermediate status check) — the
bar is "would Claude have written an end-of-turn summary and asked a question here in the chat?"
If yes, send it to Telegram too. If it's just routine progress, don't. This mirrors the built-in
`PushNotification` tool's own guidance ("err toward not sending one") — this Skill exists to
extend that same judgment to the Telegram channel Ba specifically asked for, not to bypass it.

## How to send a notification

Read the two values from `.agents/config/.env.telegram-notify` (format:
`KEY=value` per line) and POST to the Telegram Bot API.

**Important, verified 2026-07-19**: on this machine's Vietnamese text
inline as `--data-urlencode "text=<message with dấu>"` silently mangles the UTF-8 bytes and
Telegram rejects it (`400: strings must be encoded in UTF-8`) even though the string looks
correct in the command. Plain ASCII inline works fine; Vietnamese does not. The reliable fix:
write the message to a temp file first (with the `Write` tool, which encodes correctly), then
have curl read the field value FROM that file with `--data-urlencode text@<path>` instead of
`text=<message>`.

```bash
# 1. Write the message (use the Write tool, not a bash heredoc, so encoding is correct):
#    -> some scratch path, e.g. C:\...\scratchpad\telegram-msg.txt, content = the message text.
# 2. Send it:
set -a
source ".agents/config/.env.telegram-notify"
set +a
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
  --data-urlencode "text@/path/to/telegram-msg.txt"
```

If the message is pure ASCII (no Vietnamese diacritics), the inline `text=<message>` form is
fine and skips the extra file-write step.

## Replying to Telegram-originated inbox events

When the current turn was triggered by `.agents/inbox/inbox.json`, do not use the configured
default `TELEGRAM_CHAT_ID` unless the inbox event does not contain a usable `chat_id`. The inbox
event is the routing authority.

Preferred response flow, designed for IDEs/agents that are not allowed to run shell, Python, or
network commands without approval:
1. Read `.agents/inbox/inbox.json` as JSON.
2. Extract `chat_id` and `update_id` from the inbox event.
3. Write the final response as one valid JSON object to `.agents/inbox/outbox.json`.
4. The already-running shared Telegram daemon reads `outbox.json`, sends the Telegram message, and
   archives the sent payload to `.agents/inbox/outbox.sent.json`.
5. Only then consider the Telegram-originated turn complete. The agent should not run `curl`,
   Python, or any other command just to send the Telegram response.

Canonical outbox JSON shape:

```json
{
  "type": "TELEGRAM_REPLY",
  "content": "Con đã xử lý xong yêu cầu.",
  "chat_id": "-1001234567890",
  "reply_to_update_id": 123456789,
  "timestamp": "2026-07-21T08:31:00Z"
}
```

Write `.agents/inbox/outbox.json` atomically when possible by writing
`.agents/inbox/outbox.json.tmp` first and replacing it with `.agents/inbox/outbox.json`. If the
agent's environment cannot perform atomic replacement directly, writing the final JSON file with
the IDE's normal project-file editing capability is still preferable to running a blocked shell or
network command.

If `.agents/inbox/outbox.json` remains present after a reasonable daemon cycle, the daemon has not
confirmed delivery yet. Do not claim Ba received the Telegram response until the file is archived
as `.agents/inbox/outbox.sent.json` or the active chat clearly reports the delivery uncertainty.

Message content guidance:
- Vietnamese, short (1-3 sentences), lead with what Ba needs to decide/confirm — not a status
  dump. E.g.: `"Cần Ba xác nhận: xoá file credential test cũ ở local-agent để reset đăng nhập?"`
  or `"Cần Ba chọn: bắt đầu từ trang Accounts trước hay audit song song hết các trang?"`
- Never put secrets, credentials, or full file contents in the message body.
- If the Telegram API call itself fails (e.g. `"ok":false` in the response), fall back to just
  asking in chat as normal — do not block the actual question on Telegram delivery succeeding.

## Waiting for Ba's reply (ask-and-wait, real-time)

Ba explicitly wants to be able to answer FROM Telegram directly (not just get reminded to come
back to the Claude Code chat). Use `skills/notify-telegram/poll_reply.sh` for this — it
sends the question, then waits for Ba's reply using Telegram's own long-polling (the HTTP
request itself blocks server-side until a message arrives, so detection is near-instant —
not delayed by a local sleep/poll interval).

```bash
bash "e:/AgentsProject/skills/notify-telegram/poll_reply.sh" \
  "<path to UTF-8 question file>" \
  "<path to result file>" \
  [max_rounds=15] [long_poll_seconds=25]
```

Run this via the Bash tool with `run_in_background: true` — it blocks Claude's Bash call for up
to `max_rounds * long_poll_seconds` (defaults ≈ 375s / 6.25 min, safely under the 10-minute Bash
cap), so backgrounding it lets Claude keep working (e.g. continue other tasks, or just wait) and
a task-notification arrives the moment Ba's reply is detected (or the window times out). Read the
result file's content afterward: `REPLY_RECEIVED: <text>` or `TIMEOUT: no reply received after
~Ns`. If it times out, either re-run it for another window, or fall back to asking in the Claude
Code chat directly.

**Acknowledgment (2026-07-19)**: the moment Ba's reply is detected, the script sends a short
"✅ Đã nhận câu trả lời: ..." confirmation back to his Telegram chat, before returning — so he
knows it registered and doesn't need to re-type or re-tap. This is automatic; nothing extra to
do when calling the script.

**Known limitation**: the script's "ignore anything already in the queue" baseline is computed
right when the script starts — if Ba replies in the same instant, before the question is even
sent, that reply could be missed. Not worth engineering around; if it ever happens, just re-ask.

## Asking with buttons (ask-and-wait, inline keyboard)

Use `skills/notify-telegram/poll_reply_with_options.sh` when the question has a small
set of discrete choices — Ba taps a real button instead of typing, which is faster and removes
ambiguity.

```bash
bash "e:/AgentsProject/skills/notify-telegram/poll_reply_with_options.sh" \
  "<path to UTF-8 question file>" \
  "<path to UTF-8 options file, one option label per line>" \
  "<path to result file>" \
  [max_rounds=15] [long_poll_seconds=25]
```

Result file contents: `OPTION_SELECTED: <label>` (Ba tapped a button), `TEXT_RECEIVED: <text>`
(Ba typed instead — always handle this fallback), or the same `TIMEOUT: ...` as the plain
version. Keep option labels short (they become button text) and to ~8 or fewer options — this
mirrors `AskUserQuestion`'s own option-count guidance.

Same as `poll_reply.sh`: the moment a tap or free-text reply is detected, the script sends a
short "✅ Đã nhận lựa chọn: ..." / "✅ Đã nhận trả lời: ..." acknowledgment back to Ba automatically,
before returning.

**Ba can always answer with something other than the buttons** by just typing a reply instead of
tapping one (the script already handles this as `TEXT_RECEIVED`, same as `AskUserQuestion`'s
built-in "Other" option in this chat) — make that explicit in the question text itself, e.g. end
it with something like `"(hoặc trả lời khác nếu Ba có ý riêng)"`, so it's obvious from the
Telegram side, not just an undocumented fallback.

**Do not over-interpret a button tap as broader approval than what was literally asked.** A tap
answers the specific question sent — e.g. confirming a mechanism test, or answering one narrow
question — it is not blanket authorization to proceed with unrelated or larger follow-on work.
If there's any ambiguity about what a reply is approving, ask again explicitly rather than
assuming the widest possible interpretation. (Real incident, 2026-07-19: a button tap that was
only testing whether the notify mechanism worked was mistaken for approval to start real
implementation work, and an agent was dispatched before Ba had actually signed off.)

## Project inbox mode (standing, 2026-07-19, updated 2026-07-21)

Ba asked: *"có cách nào để nó chạy cùng session để tôi trao đổi liên tục không? thay vì xong task
hay cần hỏi mới kích hoạt"* (can it run within the same session so we can talk continuously,
instead of only activating when a task finishes or a question is needed).

Mechanism: `skills/workflow-runtime/scripts/telegram_daemon.py daemon` long-polls Telegram using
the global credentials and routes new updates into the registered project's local inbox. The
daemon writes exactly one valid JSON object to `.agents/inbox/inbox.json` using an atomic
`inbox.json.tmp` write followed by `os.replace`.

Canonical inbox JSON shape:

```json
{
  "type": "MESSAGE_RECEIVED",
  "content": "the message text or project-local file path",
  "update_id": 123456789,
  "chat_id": "-1001234567890",
  "timestamp": "2026-07-21T08:30:00Z"
}
```

Allowed `type` values:
- `MESSAGE_RECEIVED`
- `FILE_RECEIVED`
- `PHOTO_RECEIVED`
- `PHOTO_DOWNLOAD_FAILED`
- `FILE_DOWNLOAD_FAILED`

Agent handling rules:
- If `.agents/inbox/inbox.json` is absent, empty, unchanged, or invalid JSON, do not invent a
  Telegram reply and do not emit an idle status message.
- If `type` is `MESSAGE_RECEIVED`, treat `content` as Ba's current instruction with the same care
  as a normal chat message.
- If `type` is `PHOTO_RECEIVED` or `FILE_RECEIVED`, treat `content` as a project-relative path and
  inspect the file before making claims about it.
- If `type` is `PHOTO_DOWNLOAD_FAILED` or `FILE_DOWNLOAD_FAILED`, report the failed `file_id`
  clearly and ask Ba to resend only if the file is needed.
- If the current turn was triggered by `.agents/inbox/inbox.json`, the final response MUST be sent
  back to the Telegram `chat_id` from that JSON object before the turn is considered complete.
  A normal chat response alone is not sufficient for Telegram-originated input.
- Do not run shell, Python, curl, or other network commands just to send that response. Write
  `.agents/inbox/outbox.json` instead and let the shared Telegram daemon send it.
- Keep the Telegram response concise, but include the answer or completion status Ba needs.
- Do not send Telegram responses for idle timer checks, missing inbox files, unchanged inbox
  files, or invalid inbox JSON. Silence on idle is the required behavior.

**Standing files**:
`.agents/inbox/inbox.json` for project-local routed messages, `.agents/inbox/outbox.json` for
project-local replies waiting to be sent by the daemon, `.agents/inbox/outbox.sent.json` for the
last confirmed sent reply, and `~/.aiwf/telegram-offset.txt` for the daemon's Telegram update
offset. Do not route project messages through
`~/.aiwf/<project>/inbox.json`; some agents cannot read files outside the registered project
workspace.

**Real limitations — tell Ba these plainly, don't oversell it**:
- This is not an LLM loop. The daemon can poll Telegram without spending model tokens. Agents
  should only spend tokens when there is a new valid inbox event to process.
- If Claude is deep in other work when a message arrives, there's a small delay until the next
  turn picks up the JSON inbox event and acts — not instant during heavy multi-agent work, though
  the Telegram-side detection itself is still near-real-time.
- **A message arriving through this channel is real input and should be treated with the same
  care as a chat message** — including the standing caution above about not over-interpreting a
  short reply as broader approval than what it literally says.

## Sending files (added 2026-07-19)

**Hard standing rule (Ba, 2026-07-19): "không gửi code, ko gửi các file bảo mật, chỉ cho gửi file
báo cáo thôi"** — never send source code, never send secrets/credentials, only report-type
documents. This is enforced as a real gate inside `send_file.sh` itself (extension allowlist:
`md/pdf/txt/csv/png/jpg/jpeg`; path must be under `docs/` or a scratchpad/temp dir; sensitive
path/name markers like `.env`/`secret`/`token`/`credential`/`.pem`/`.key` are rejected regardless
of extension) — not just a documentation note. If a real task ever seems to need sending something
outside this allowlist (e.g. a zipped report bundle), ask Ba to explicitly loosen the rule first;
do not edit the gate to route around it silently.

Use `skills/notify-telegram/send_file.sh` to send Ba any local file as a real Telegram
document he can open on his phone/desktop directly from the chat — screenshots, reports, zipped
artifacts, exported logs, anything.

```bash
bash "e:/AgentsProject/skills/notify-telegram/send_file.sh" \
  "<absolute path to the file>" \
  ["<path to UTF-8 caption file, optional>"] \
  ["<path to result file, optional>"]
```

Result: `SENT: <file_path>` or `SEND_FAILED: <error>`. Same UTF-8-safety pattern as everything
else in this skill — if you want a caption with Vietnamese text, write it to a file with the
`Write` tool first and pass that path; never pass caption text inline through a bash variable.

**Real limit**: Telegram's Bot API caps `sendDocument` uploads at 50MB — the script checks this
and refuses larger files with a clear error rather than letting curl hang or silently truncate.

## Receiving files — photos + documents (fixed/added 2026-07-19)

**Real incident that started this**: Ba sent a screenshot via Telegram for review ("Đây là hình
chụp app, hãy kiểm tra lại"). `listen.sh`'s update-parsing only ever looked at `msg['text']` — a
photo-only message has no `text` key, so it was silently skipped while the offset still advanced
past it. Since Telegram's `getUpdates` never returns an already-acknowledged update again, the
photo was permanently lost the moment the offset moved past it — there is no way to recover it
after the fact; the only fix is to ask the sender to resend.

Fixed, then extended to cover Ba's explicit follow-up request ("gửi đc file, nhận và xử lý đc file
— zip, image, markdown, pdf"): the shared daemon now checks both:
- `msg['photo']` — an array of sizes; Telegram orders them ascending, so the last entry is the
  largest. Downloaded to `.agents/inbox/photos/<update_id>.jpg`. Inbox JSON:
  `{"type": "PHOTO_RECEIVED", "content": ".agents/inbox/photos/<update_id>.jpg", ...}`.
- `msg['document']` — covers zip/markdown/pdf/any file Ba sends as an actual file attachment
  (rather than a compressed inline photo). Downloaded to
  `.agents/inbox/files/<update_id>_<original_filename>`, preserving Telegram's own filename (and
  therefore its extension, so downstream processing knows what it's dealing with). Inbox JSON:
  `{"type": "FILE_RECEIVED", "content": ".agents/inbox/files/<update_id>_<original_filename>", ...}`.

Both use Python's stdlib `urllib.request` only (no extra dependency) to call `getFile` then
download the actual bytes, before the offset advances past that update — so nothing is silently
dropped the way the original photo was.

**How to actually process what arrives** (per Ba's ask — "receive AND process"):
- Image (`PHOTO_RECEIVED` or a `FILE_RECEIVED` `.png`/`.jpg`/etc.) → open the path from the JSON
  `content` field; it renders images directly, same as any screenshot.
- Markdown/text/PDF `FILE_RECEIVED` → read the path from the JSON `content` field directly.
- `.zip` `FILE_RECEIVED` → not directly readable; extract it first (e.g. `Bash`:
  `unzip -o "<content path>" -d "<some scratch dir>"`) then
  `Read`/`Glob`/`Grep` the extracted contents like any other files. Don't attempt to "read" a zip
  archive itself as if it were text.
- Whatever the type, treat the downloaded file exactly like a file the user attached in this chat
  — read it before acting on any claim about its contents, same as the standing rule for any
  file you did not write yourself.

**Still not supported**: other Telegram attachment types this hasn't been tested against yet
(videos, voice notes, stickers, plain contacts/location shares) will still be silently skipped the
same way photos originally were, until someone hits that gap for real and it gets fixed the same
way. If a message result seems to be missing content, check whether it might be an untested
attachment type before assuming nothing was sent.

## Proxy fallback for connectivity outages (added 2026-07-19)

**Real incident**: mid-session, direct connectivity from this machine to `api.telegram.org`
dropped entirely — a bare `curl https://api.telegram.org` returned `HTTP 000` (connection never
established) after a full 10s timeout, and every script in this skill started failing with
transient-looking `curl` exit code 28 (timeout) errors on every call, including the standing
`listen.sh` loop.

Ba supplied a working local network proxy (`http://192.168.1.11:8080`) — confirmed live via both
a bare connectivity check and a real `getMe` call through it. Fix: `.env.telegram-notify` gained
an optional `TELEGRAM_PROXY=<url>` line; every script in this skill (`poll_reply.sh`,
`poll_reply_with_options.sh`, `send_file.sh`) exports `https_proxy`/`HTTPS_PROXY` from that value
right after sourcing the config, if set. The shared Python daemon also loads this proxy setting
and passes it into its `urllib.request` opener for polling and file downloads.

**When direct connectivity is confirmed restored**: remove or empty the `TELEGRAM_PROXY` line in
`.env.telegram-notify` — every script falls back to direct connection automatically (the `if
[ -n "${TELEGRAM_PROXY:-}" ]` guard just skips exporting the proxy vars when it's unset). Don't
leave the proxy wired permanently once it's not needed — it's a real external dependency (Ba's own
local network device) that adds a failure point if left in place indefinitely.

## Verification notes (2026-07-19)

- Bot token confirmed valid via a read-only `getMe` call before wiring up; re-verified again
  after Ba rotated to the new @claude_polling_bot token mid-session.
- End-to-end fire-and-forget delivery confirmed with a live test message (both the old and new
  bot tokens).
- End-to-end ask-and-wait confirmed live: sent a test question, Ba replied "Ok" on Telegram, the
  script's long-poll loop captured it and wrote `REPLY_RECEIVED: Ok` to the result file.
- Root-caused and fixed a real bug during setup: `python3` on this machine resolves to a broken
  Windows Store "app execution alias" stub (prints an install nag, never runs), NOT a real
  Python — even though `which python3` appears to find it. The real interpreter is `python`
  (no "3"). The script uses `python`, not `python3`, for this reason — do not "fix" it back.
