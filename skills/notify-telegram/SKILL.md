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
description: Sends a Telegram push notification to the user (the project owner) whenever Claude reaches a point that needs the user's decision/confirmation before continuing — so the user can respond promptly instead of the session sitting idle waiting.
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

The user is not always watching the chat. When Claude hits a point where it genuinely needs the user's
input before it can continue — a real decision only the user can make, a confirmation for a
sensitive/irreversible action, an `AskUserQuestion` call, or any other moment where the
session would otherwise sit idle waiting for a reply — this Skill sends a Telegram message to
the user's phone so the user can respond promptly instead of the session hanging with no visible progress.

Config: `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` — bot **@claude_polling_bot** (“Claude”).
Credentials được quản lý global bởi shared Telegram daemon (`aiwf telegram config`) —
agent **không cần đọc credentials hay gọi curl trực tiếp**.

Skill này có 3 chế độ độc lập, dùng bất kỳ một hoặc kết hợp:
1. **Fire-and-forget notify** — viết `outbox.json` dạng `TELEGRAM_REPLY`, daemon gửi ngay không cần đợi.
2. **Ask-and-wait (buttons)** — viết `outbox.json` dạng `TELEGRAM_SEND_BUTTONS`, daemon gửi kèm nút bấm, agent dùng `schedule` tool để chờ reply.
3. **Send/receive files** — viết `outbox.json` dạng `TELEGRAM_SEND_DOCUMENT` hoặc `TELEGRAM_SEND_PHOTO`, daemon upload lên Telegram API. Nhận file thông qua `FILE_RECEIVED` / `PHOTO_RECEIVED` trong `inbox.json`.
4. **Project inbox daemon route** — daemon luoôn đọ mọi tin nhắn từ user, ghi vào `.agents/inbox/inbox.json` thành JSON object chuẩn.

## When to use this Skill

**The user's standing instruction (2026-07-19): use Telegram as a genuine second channel for this
whole conversation, not just a one-off alert.** Concretely:

- An `AskUserQuestion` call — always notify alongside it (use the buttons variant when the
  question has discrete options, matching what's shown in the chat).
- A confirmation request for a risky/destructive/irreversible action.
- **Whenever Claude finishes a significant chunk of work** (a phase, a multi-agent batch, a big
  audit, etc.) **and is about to decide or ask what to do next** — send a short completion
  summary + the next-step question (with buttons if there are discrete options) by writing
  `outbox.json` with `TELEGRAM_SEND_BUTTONS` or `TELEGRAM_REPLY`, the same way Claude would post
  an end-of-turn summary in this chat. This is what makes it feel like an ongoing conversation happening over
  Telegram, not a single alert-and-forget ping.
- Any other genuine "I am blocked, only the user can unblock this" moment.

**Still avoid noise** for things that don't need the user's input at all (e.g. an individual background
sub-agent finishing when 7 others are still running, a routine intermediate status check) — the
bar is "would Claude have written an end-of-turn summary and asked a question here in the chat?"
If yes, send it to Telegram too. If it's just routine progress, don't. This mirrors the built-in
`PushNotification` tool's own guidance ("err toward not sending one") — this Skill exists to
extend that same judgment to the Telegram channel the user specifically asked for, not to bypass it.

## Cách gửi thông báo (How to send)

**Quy trình duy nhất**: viết JSON vào `.agents/inbox/outbox.json`, daemon sẽ gửi. Agent **không** gọi curl, không chạy script shell, không đọc file credentials.

**3 bước:**
1. Đọc `.agents/inbox/inbox.json` → lấy `chat_id` từ event hiện tại (nếu turn được trigger từ Telegram).
2. Soạn JSON object đúng kiểu (xem Canonical outbox types bên dưới).
3. Ghi vào `.agents/inbox/outbox.json`. Daemon đọc, gửi, lưu vào `outbox.sent.json`.

**Gửi nhiều message trong 1 lượt:** dùng JSON array `[{...}, {...}]` thay vì single object.
Daemon gửi tuần tự. **Không ghi đè nhiều lần** — mỗi lần ghi đè sẽ mất message trước đó.

**Gửi nhiều file cùng lúc:** đặt `file_path` thành mảng `["path1.md", "img1.png"]` trong type `TELEGRAM_SEND_DOCUMENT` hoặc `TELEGRAM_SEND_PHOTO`.
Daemon gửi chúng dưới dạng MediaGroup album.

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

Canonical outbox JSON — **7 supported types** (daemon: `aiwf telegram daemon`):

**1. Text reply**en
```json
{
  "type": "TELEGRAM_REPLY",
  "content": "Blueprint approved. Starting implementation.",
  "chat_id": "-1001234567890",
  "reply_to_update_id": 123456789,
  "timestamp": "2026-07-25T08:31:00Z"
}
```

**2. Send file/document/album** (`sendDocument` or `sendMediaGroup`)
```json
{
  "type": "TELEGRAM_SEND_DOCUMENT",
  "file_path": "docs/reports/FEAT-001/final_report.md",
  "caption": "Final implementation report.",
  "chat_id": "-1001234567890",
  "timestamp": "2026-07-25T08:31:00Z"
}
```
*Note: `file_path` can also be a JSON array of strings `["path1.md", "path2.md"]`. When an array is provided, the daemon sends them as a grouped album (MediaGroup).*

**3. Send image/screenshot/album** (`sendPhoto` or `sendMediaGroup`)
```json
{
  "type": "TELEGRAM_SEND_PHOTO",
  "file_path": "docs/reports/assets/FEAT-001/screenshot.png",
  "caption": "UI after fix.",
  "chat_id": "-1001234567890",
  "timestamp": "2026-07-25T08:31:00Z"
}
```
*Note: `file_path` can also be a JSON array of strings `["img1.png", "img2.png"]`. When an array is provided, the daemon sends them as a grouped album (MediaGroup).*

**4. Send URL with link preview** (`sendMessage`)
```json
{
  "type": "TELEGRAM_SEND_URL",
  "url": "https://github.com/your-org/AI-Agent-Workflow/releases/tag/v6.21.0",
  "caption": "New release:",
  "chat_id": "-1001234567890",
  "timestamp": "2026-07-25T08:31:00Z"
}
```

**5. Message with inline buttons** (`sendMessage` + `InlineKeyboardMarkup`)
```json
{
  "type": "TELEGRAM_SEND_BUTTONS",
  "content": "Blueprint ready. Please review:",
  "buttons": [
    [{"text": "\u2705 Approve", "callback_data": "approve"},
     {"text": "\u274c Reject",  "callback_data": "reject"}],
    [{"text": "\ud83d\udcce View Blueprint", "url": "https://github.com/..."}]
  ],
  "chat_id": "-1001234567890",
  "timestamp": "2026-07-25T08:31:00Z"
}
```
`buttons` is a 2-D array of rows. Each button: `text` + `callback_data` (for polling tap) OR `url` (link button).

**6. Update bot menu commands** (`setMyCommands`)
```json
{
  "type": "TELEGRAM_SEND_COMMANDS",
  "commands": [
    {"command": "status",  "description": "Check workflow status"},
    {"command": "approve", "description": "Approve pending blueprint"}
  ],
  "scope": {"type": "all_private_chats"},
  "chat_id": ""
}
```
`chat_id` can be empty for `TELEGRAM_SEND_COMMANDS` (global bot setting). `scope` is optional.

**7. Add emoji reaction** (`setMessageReaction`)
```json
{
  "type": "TELEGRAM_SEND_REACTION",
  "message_id": 123456789,
  "emoji": "\u2705",
  "chat_id": "-1001234567890",
  "timestamp": "2026-07-25T08:31:00Z"
}
```
Common emojis: \ud83d\udc4d \ud83d\udd25 \u2705 \u274c \u2764 \ud83c\udf89 \ud83d\ude80 \ud83d\udc40

Write `.agents/inbox/outbox.json` atomically when possible by writing
`.agents/inbox/outbox.json.tmp` first and replacing it with `.agents/inbox/outbox.json`. If the
agent's environment cannot perform atomic replacement directly, writing the final JSON file with
the IDE's normal project-file editing capability is still preferable to running a blocked shell or
network command.

**Important (New in v6.20.11):** You can write either a single JSON object `{}` or a JSON Array of objects `[{}, {}]` to `outbox.json`. When writing an array, the daemon will dispatch them sequentially. If you need to send multiple messages in a single turn, ALWAYS format `outbox.json` as an array to prevent data loss from overwriting.

If `.agents/inbox/outbox.json` remains present after a reasonable daemon cycle, the daemon has not
confirmed delivery yet. Do not claim the user received the Telegram response until the file is archived
as `.agents/inbox/outbox.sent.json` or the active chat clearly reports the delivery uncertainty.

Message content guidance:
- Vietnamese, short (1-3 sentences), lead with what the user needs to decide/confirm — not a status
  dump. E.g.: `"Cần bạn xác nhận: xoá file credential test cũ ở local-agent để reset đăng nhập?"`
  or `"Cần bạn chọn: bắt đầu từ trang Accounts trước hay audit song song hết các trang?"`
- Never put secrets, credentials, or full file contents in the message body.
- If the Telegram API call itself fails (e.g. `"ok":false` in the response), fall back to just
  asking in chat as normal — do not block the actual question on Telegram delivery succeeding.

## Interactive questions (ask-and-wait)

To ask the user a question and wait for a reply (either text or buttons):
1. Write the question to `.agents/inbox/outbox.json` using `TELEGRAM_REPLY` or `TELEGRAM_SEND_BUTTONS` (see Canonical JSON formats above).
2. Use the `schedule` tool (e.g., `DurationSeconds="10"`) to wait. The shared daemon will send the message and wait for the user's reply.

During `initialize-workflow` (Step 8), if the shared Telegram daemon is active, the agent automatically
arms the 10-second `schedule` monitor listener (`DurationSeconds="10"`) to check `.agents/inbox/inbox.json`
continuously.

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
- **Session Command Filter & Exclusive Routing Rule**: If `content` starts with a command `/<session_name>` (e.g. `/mallory`, `/alice`) belonging to another active session in `registry.json`, this agent MUST SKIP processing the message and remain silent so that session handles it exclusively without message collision.
- If `type` is `MESSAGE_RECEIVED`, treat `content` as the user's current instruction with the same care
  as a normal chat message.
- If `type` is `PHOTO_RECEIVED` or `FILE_RECEIVED`, treat `content` as a project-relative path and
  inspect the file before making claims about it.
- If `type` is `PHOTO_DOWNLOAD_FAILED` or `FILE_DOWNLOAD_FAILED`, report the failed `file_id`
  clearly and ask the user to resend only if the file is needed.
- If the current turn was triggered by `.agents/inbox/inbox.json`, the final response MUST be sent
  back to the Telegram `chat_id` from that JSON object before the turn is considered complete.
  A normal chat response alone is not sufficient for Telegram-originated input.
- Do not run shell, Python, curl, or other network commands just to send that response. Write
  `.agents/inbox/outbox.json` instead and let the shared Telegram daemon send it.
- Keep the Telegram response concise, but include the answer or completion status the user needs.
- Do not send Telegram responses for idle timer checks, missing inbox files, unchanged inbox
  files, or invalid inbox JSON. Silence on idle is the required behavior.

**Standing files**:
`.agents/inbox/inbox.json` for project-local routed messages, `.agents/inbox/outbox.json` for
project-local replies waiting to be sent by the daemon, `.agents/inbox/outbox.sent.json` for the
last confirmed sent reply, and `~/.aiwf/telegram-offset.txt` for the daemon's Telegram update
offset. Do not route project messages through
`~/.aiwf/<project>/inbox.json`; some agents cannot read files outside the registered project
workspace.

**Real limitations — tell the user these plainly, don't oversell it**:
- This is not an LLM loop. The daemon can poll Telegram without spending model tokens. Agents
  should only spend tokens when there is a new valid inbox event to process.
- If Claude is deep in other work when a message arrives, there's a small delay until the next
  turn picks up the JSON inbox event and acts — not instant during heavy multi-agent work, though
  the Telegram-side detection itself is still near-real-time.
- **A message arriving through this channel is real input and should be treated with the same
  care as a chat message** — including the standing caution above about not over-interpreting a
  short reply as broader approval than what it literally says.

## Sending files

**Hard standing rule: "không gửi code, ko gửi các file bảo mật, chỉ cho gửi file báo cáo thôi"**
Never send source code, never send secrets/credentials, only report-type documents. If a real task ever seems to need sending something outside this rule (e.g. a zipped report bundle), ask the user to explicitly loosen the rule first; do not route around it silently.

To send a file (report, screenshot, zip, etc.), write an `outbox.json` with the `TELEGRAM_SEND_DOCUMENT` or `TELEGRAM_SEND_PHOTO` type (see Canonical JSON formats above). The shared daemon will handle the upload directly using Telegram API.

**Real limit**: Telegram's Bot API caps `sendDocument` uploads at 50MB. Make sure the file is smaller than this before sending.

## Receiving files — photos + documents

**Real incident that started this**: the user sent a screenshot via Telegram for review ("Đây là hình
chụp app, hãy kiểm tra lại"). The legacy parser only ever looked at `msg['text']` — a
photo-only message has no `text` key, so it was silently skipped while the offset still advanced
past it.

Fixed, then extended to cover the user's explicit follow-up request ("gửi đc file, nhận và xử lý đc file
— zip, image, markdown, pdf"): the shared daemon now checks both:
- `msg['photo']` — an array of sizes; Telegram orders them ascending, so the last entry is the
  largest. Downloaded to `.agents/inbox/photos/<update_id>.jpg`. Inbox JSON:
  `{"type": "PHOTO_RECEIVED", "content": ".agents/inbox/photos/<update_id>.jpg", ...}`.
- `msg['document']` — covers zip/markdown/pdf/any file the user sends as an actual file attachment
  (rather than a compressed inline photo). Downloaded to
  `.agents/inbox/files/<update_id>_<original_filename>`, preserving Telegram's own filename (and
  therefore its extension, so downstream processing knows what it's dealing with). Inbox JSON:
  `{"type": "FILE_RECEIVED", "content": ".agents/inbox/files/<update_id>_<original_filename>", ...}`.

Both use Python's stdlib `urllib.request` only (no extra dependency) to call `getFile` then
download the actual bytes, before the offset advances past that update — so nothing is silently
dropped the way the original photo was.

**How to actually process what arrives** (per the user's ask — "receive AND process"):
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

## Verification notes

- Bot token confirmed valid via a read-only `getMe` call before wiring up.
- End-to-end fire-and-forget delivery confirmed with a live test message.
- End-to-end ask-and-wait confirmed live via the JSON inbox/outbox system.
