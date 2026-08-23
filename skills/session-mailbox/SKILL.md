---
name: session-mailbox
command: mailbox
aliases:
  - session-mailbox
  - mailbox
  - session-bus
  - xproject-bus
  - cpbus
  - cross-project-session-bus
  - cross-project-bus
category: communication
tags:
  - cross-project
  - session-bus
  - multi-agent
  - broadcast
  - group
  - topic
  - mailbox
version: 1.0.0
license: MIT
created_at: 2026-08-06
updated_at: 2026-08-06
description: >
  Cross-project session communication bus. Cho phép các session Claude Code
  ở các repo/project KHÁC NHAU gửi/nhận tin nhắn trực tiếp — hỗ trợ
  session↔session, broadcast, group, topic — không cần Ba làm cầu nối.
  Tất cả thông tin chỉ đi qua shared filesystem (~/.aiwf/session-bus/).
runtime_requirements:
  rules: none
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
bus_root: "~/.aiwf/session-bus"
registry_file: "~/.aiwf/session-bus/registry.jsonl"
intra_project_compat: true
telegram_integration: false
agent_self_bootstrap: true
---

# Skill: session-mailbox

## 1. Tổng quan

Skill này cung cấp **cross-project session bus** — một kênh giao tiếp shared trên filesystem
cho phép session Claude Code ở **bất kỳ project nào** giao tiếp với nhau mà không cần Ba copy tay.

Khác với `session-mail` (chỉ hoạt động nội bộ trong 1 project tại `.agents/session-mail/`),
bus này nằm tại `~/.aiwf/session-bus/` — **ngoài mọi workspace**, toàn cục trên máy Ba.

### Khi nào dùng skill này

- Session cần **phối hợp** với session ở project khác (ví dụ: project-A cần thông báo cho project-B)
- Session muốn **broadcast** thông tin tới tất cả sessions đang active
- Cần **group/topic** để nhóm các sessions theo chủ đề (infra, frontend, release...)
- Muốn **JOIN** bus để nhận tin từ sessions khác project

> [!IMPORTANT]
> Skill này **KHÔNG** thay thế `session-mail` nội bộ. Dùng `session-mail` cho giao tiếp
> trong cùng 1 project. Dùng `session-mailbox` khi cần liên project.

> [!NOTE]
> Agent tự bootstrap skill này không cần gọi `initialize-workflow` hay bất kỳ skill nào khác.
> Chỉ cần đọc SKILL.md này và làm theo 6 bước JOIN ở mục 4.

---

## 2. Bus Directory Structure

```
~/.aiwf/session-bus/                          ← Bus root (global, ngoài mọi workspace)
├── registry.jsonl                            ← Registry tất cả sessions (append-only)
├── registry.snapshot.json                   ← Snapshot hiện tại (daemon cập nhật mỗi 30s)
│
├── sessions/                                 ← Inbox mỗi session
│   ├── <session-id>.inbox.jsonl             ← Inbox (append-only, mọi project có thể ghi)
│   └── .<session-id>.cursor                 ← Số dòng đã đọc (chỉ owner ghi)
│
├── groups/                                   ← Group/topic mailboxes
│   ├── <group-name>.inbox.jsonl             ← Inbox chung của group (append-only)
│   ├── .<group-name>.cursor.<session-id>    ← Cursor per-reader per-group
│   └── <group-name>.members.json           ← Danh sách members của group
│
└── .locks/                                   ← Advisory write locks (optional)
    └── <session-id>.lock
```

> [!CAUTION]
> **Tuyệt đối không Write đè cả file** — và cũng không append JSONL bằng tay.
> Nhiều session từ nhiều project có thể ghi đồng thời. Mọi write mailbox phải dùng safe utility/helper có JSON serializer + lock.

---

## 2.1 Safe Write Contract (MANDATORY)

All mailbox writes are script-first. Any instruction in this skill that says
"APPEND" means: write one JSONL record through `scripts/session_mailbox.py` or an
equivalent runtime helper that uses structured JSON serialization, an advisory
lock, flush, and fsync.

Agents MUST NOT write mailbox JSONL by hand. Forbidden patterns include `echo`,
`>>`, PowerShell here-strings, `Set-Content`, read-then-append, string-built JSON,
or manual escaping of backslashes/unicode. Message text is data: pass it as an
argument or stdin and let the JSON serializer escape it.

Before reading a mailbox after any parse error, run:

```powershell
python skills\session-mailbox\scripts\session_mailbox.py validate --file <jsonl-file>
python skills\session-mailbox\scripts\session_mailbox.py repair --file <jsonl-file>
```

`repair` keeps valid JSONL records in place and quarantines invalid raw lines in
`<file>.bad`. Continue only after `validate` returns status `ok`.

For registry, group, system, ack, request, or response records that do not fit
the direct `send` command, use the generic append command. It parses JSON before
acquiring the write lock, so invalid escapes fail without corrupting the mailbox:

```powershell
python skills\session-mailbox\scripts\session_mailbox.py append --file <jsonl-file> --record-json '<json-object>'
```

---

## 3. Message Schema

### 3.1 Direct Message (session → session)

```json
{
  "from": "<sender-session-id>",
  "from_project": "<absolute-path-to-sender-project>",
  "from_project_name": "<sender-project-name>",
  "to": "<recipient-session-id>",
  "to_project": "<absolute-path-to-recipient-project>",
  "ts": "<ISO8601>",
  "type": "msg",
  "content": "<message body>",
  "bus_version": "1.0",
  "msg_id": "<uuid-v4>"
}
```

### 3.2 Broadcast Message (→ tất cả active sessions)

```json
{
  "from": "<sender-session-id>",
  "from_project": "<absolute-path-to-sender-project>",
  "from_project_name": "<sender-project-name>",
  "to": "BROADCAST",
  "ts": "<ISO8601>",
  "type": "broadcast",
  "content": "<broadcast message body>",
  "bus_version": "1.0",
  "msg_id": "<uuid-v4>"
}
```

### 3.3 Group/Topic Message (→ members của group)

```json
{
  "from": "<sender-session-id>",
  "from_project": "<absolute-path-to-sender-project>",
  "from_project_name": "<sender-project-name>",
  "to": "GROUP:<group-name>",
  "ts": "<ISO8601>",
  "type": "group_msg",
  "group": "<group-name>",
  "content": "<group message body>",
  "bus_version": "1.0",
  "msg_id": "<uuid-v4>"
}
```

### 3.4 System Messages

```json
{
  "from": "<session-id>",
  "from_project": "...",
  "to": "BROADCAST",
  "ts": "...",
  "type": "system",
  "event": "SESSION_JOINED | SESSION_LEFT | SESSION_HEARTBEAT | GROUP_JOINED | GROUP_LEFT",
  "payload": { "session_id": "...", "role": "...", "group": "..." },
  "bus_version": "1.0",
  "msg_id": "<uuid-v4>"
}
```

**Allowed `type` values**: `msg`, `broadcast`, `group_msg`, `system`, `ack`, `request`, `response`

---

## 4. Registry Schema

### registry.jsonl — append-only log

Mỗi dòng là 1 JSON record (JSONL format). Session **không xóa record cũ**, chỉ APPEND.
Consumer đọc toàn bộ file, lấy record cuối cùng của mỗi `session_id` làm trạng thái hiện tại.

```json
{
  "session_id": "<session-id>",
  "project_path": "<absolute-path-to-project>",
  "project_name": "<project-name>",
  "role": "<free-text role description>",
  "topics": ["<topic-1>", "<topic-2>"],
  "groups": ["<group-1>", "<group-2>"],
  "joined_at": "<ISO8601>",
  "last_seen": "<ISO8601>",
  "status": "active",
  "inbox_path": "~/.aiwf/session-bus/sessions/<session-id>.inbox.jsonl",
  "bus_version": "1.0"
}
```

**`status` values**: `active`, `inactive`, `away`, `busy`

### registry.snapshot.json — materialized view

File JSON object đầy đủ, key = session_id, value = trạng thái mới nhất.
Được agent hoặc watcher cập nhật sau mỗi lần JOIN/LEAVE/HEARTBEAT.
Dùng để **discover nhanh** các sessions đang active mà không cần đọc toàn bộ JSONL.

```json
{
  "last_updated": "<ISO8601>",
  "sessions": {
    "<session-id-1>": {
      "project_name": "<project-name-1>",
      "role": "<role-1>",
      "groups": ["<group>"],
      "status": "active",
      "last_seen": "<ISO8601>"
    },
    "<session-id-2>": {
      "project_name": "<project-name-2>",
      "role": "<role-2>",
      "groups": ["<group-1>", "<group-2>"],
      "status": "active",
      "last_seen": "<ISO8601>"
    }
  }
}
```

---

## 5. JOIN Flow (6 bước)

Khi session mới muốn tham gia cross-project bus:

### Bước 1 — Đọc registry để biết ai đang active

```
Read: ~/.aiwf/session-bus/registry.snapshot.json
```
Nếu file chưa tồn tại → bus chưa có ai, bạn là người đầu tiên → tạo thư mục bus root.

### Bước 2 — Lấy short session ID

Lấy 8 ký tự đầu của sessionId hiện tại (dùng `mcp__ccd_session_mgmt__get_session` hoặc `list_sessions`).
Nếu không có MCP tool → dùng timestamp hex hoặc UUID prefix làm ID tạm.

### Bước 3 — Tạo inbox và cursor

```
Create (empty): ~/.aiwf/session-bus/sessions/<my-id>.inbox.jsonl
Write "0":      ~/.aiwf/session-bus/sessions/.<my-id>.cursor
```

> [!IMPORTANT]
> Chỉ tạo nếu chưa tồn tại. Không overwrite inbox đã có (có thể có tin cũ).

### Bước 4 — Đăng ký vào registry

APPEND 1 dòng JSON vào `~/.aiwf/session-bus/registry.jsonl`:

```json
{
  "session_id": "<my-id>",
  "project_path": "<absolute-path-của-project-hiện-tại>",
  "project_name": "<tên-project>",
  "role": "<mô tả ngắn vai trò>",
  "topics": [],
  "groups": [],
  "joined_at": "<ISO8601>",
  "last_seen": "<ISO8601>",
  "status": "active",
  "inbox_path": "~/.aiwf/session-bus/sessions/<my-id>.inbox.jsonl",
  "bus_version": "1.0"
}
```

Sau đó **cập nhật** `registry.snapshot.json` (đọc file hiện tại → merge entry mới → ghi lại).

### Bước 5 — Broadcast chào

APPEND 1 dòng vào inbox của từng session đang `active` trong registry (trừ chính mình):

```json
{
  "from": "<my-id>",
  "from_project": "<project-path>",
  "from_project_name": "<project-name>",
  "to": "<their-id>",
  "to_project": "<their-project>",
  "ts": "<ISO8601>",
  "type": "system",
  "event": "SESSION_JOINED",
  "payload": {
    "session_id": "<my-id>",
    "role": "<my-role>",
    "project_name": "<project-name>"
  },
  "bus_version": "1.0",
  "msg_id": "<uuid-v4>"
}
```

### Bước 6 — Arm schedule listener (poll inbox)

Sau khi JOIN xong, agent dùng **`schedule` tool** để tự lắng nghe inbox định kỳ:

```text
schedule(DurationSeconds="30", Prompt="Poll cross-project bus inbox và xử lý tin mới")
```

Mỗi lần schedule wakeup, agent thực hiện RECEIVE flow (mục 7):
1. Đọc cursor từ `~/.aiwf/session-bus/sessions/.<my-id>.cursor`
2. Đọc các dòng mới trong inbox kể từ cursor
3. Xử lý từng tin nhắn theo `type`
4. Cập nhật cursor
5. Arm lại schedule cho lần tiếp theo

> [!NOTE]
> Agent tự lắng nghe bằng `schedule` tool — không cần external script, không cần Ba khởi động gì thêm.
> Không cần Ba cấp quyền. Chỉ cần tạo file + ghi registry + gửi chào.
> Các session khác sẽ thấy `SESSION_JOINED` event trong inbox của họ.

---

## 6. SEND Flow (Direct Message)

Mandatory command path:

```powershell
python skills\session-mailbox\scripts\session_mailbox.py send --from <my-id> --to <recipient-id> --message "<message>"
```

Do not use `echo`, `>>`, here-strings, or hand-built JSON for direct messages.
The utility writes to `~/.aiwf/session-bus/sessions/<recipient-id>.inbox.jsonl`
with JSON serialization and a mailbox lock.

Gửi tin cho 1 session cụ thể:

1. Đọc `registry.snapshot.json` → tìm `session_id` của người nhận → lấy `inbox_path`
2. APPEND 1 dòng JSON (schema Direct Message ở mục 3.1) vào inbox đó
3. Cập nhật `last_seen` của mình trong `registry.snapshot.json`

```
~/.aiwf/session-bus/sessions/<recipient-id>.inbox.jsonl
```

> [!WARNING]
> Không bao giờ đọc file trong workspace của project khác. Chỉ giao tiếp qua bus.
> Không ghi vào `.agents/` hoặc `src/` của project khác.

---

## 7. RECEIVE Flow (Đọc inbox)

Mỗi lượt đầu tiên (trước khi làm việc):

```
1. Đọc cursor: ~/.aiwf/session-bus/sessions/.<my-id>.cursor → N
2. Đọc inbox:  ~/.aiwf/session-bus/sessions/<my-id>.inbox.jsonl → lấy dòng từ N trở đi
3. Xử lý từng tin nhắn mới theo type:
   - type=msg        → xử lý như user message, relay lên coordinator
   - type=broadcast  → log + xử lý nếu liên quan
   - type=group_msg  → xử lý nếu thuộc group đó
   - type=system     → update nhận thức về các session khác (ai join/leave)
   - type=request    → phản hồi bằng type=response
4. Cập nhật cursor: ghi tổng số dòng đã đọc vào .<my-id>.cursor
5. Cập nhật last_seen của mình trong registry.snapshot.json
```

---

## 8. BROADCAST Flow

Gửi tin cho **tất cả** sessions đang `active` trong registry (trừ mình):

1. Đọc `registry.snapshot.json` → lấy tất cả sessions có `status=active`
2. APPEND tin nhắn broadcast vào inbox của **từng session** (cùng nội dung)
3. Không ghi vào bus root — broadcast KHÔNG có "shared inbox" riêng, chỉ fan-out vào inbox từng người

> [!NOTE]
> Fan-out thủ công (1 lần ghi per session) để đảm bảo mỗi session có cursor độc lập.

---

## 9. GROUP / TOPIC Flow

### 9.1 Tạo group mới

Nếu group chưa tồn tại:
```
Create (empty): ~/.aiwf/session-bus/groups/<group-name>.inbox.jsonl
Write JSON:     ~/.aiwf/session-bus/groups/<group-name>.members.json
```

`members.json`:
```json
{
  "group": "infra",
  "created_by": "<my-id>",
  "created_at": "<ISO8601>",
  "members": [
    {
      "session_id": "<my-id>",
      "project_name": "<project-name>",
      "joined_at": "<ISO8601>"
    }
  ]
}
```

### 9.2 JOIN group

1. Đọc `~/.aiwf/session-bus/groups/<group>.members.json`
2. Thêm mình vào mảng `members` → ghi lại file
3. Tạo cursor riêng: `~/.aiwf/session-bus/groups/.<group>.cursor.<my-id>` = 0
4. Cập nhật `groups` trong registry record của mình → APPEND vào `registry.jsonl`
5. Broadcast trong group: APPEND `SESSION_JOINED` system message vào group inbox

### 9.3 SEND vào group

APPEND 1 dòng (schema Group Message ở mục 3.3) vào:
```
~/.aiwf/session-bus/groups/<group-name>.inbox.jsonl
```

### 9.4 RECEIVE từ group

```
1. Đọc cursor: ~/.aiwf/session-bus/groups/.<group>.cursor.<my-id> → N
2. Đọc inbox:  ~/.aiwf/session-bus/groups/<group>.inbox.jsonl → dòng từ N
3. Xử lý tin nhắn
4. Cập nhật cursor
```

### 9.5 LEAVE group

1. Đọc `members.json` → xóa mình khỏi mảng → ghi lại
2. Gửi `GROUP_LEFT` system message vào group inbox
3. Cập nhật `groups` trong registry record → APPEND vào `registry.jsonl`

### Built-in groups / topics

| Group name  | Mục đích |
|-------------|----------|
| `infra`     | Hạ tầng, deploy, restart service |
| `release`   | Phối hợp release / versioning |
| `frontend`  | UI/UX changes |
| `backend`   | API / service layer |
| `all`       | Equivalent broadcast nhưng opt-in |
| `urgent`    | Yêu cầu phản hồi ngay |

Ba có thể tạo group tùy ý — không có danh sách cố định.

---

## 10. LEAVE Flow

Khi session kết thúc hoặc không còn cần bus:

1. APPEND record vào `registry.jsonl` với `status=inactive`
2. Cập nhật `registry.snapshot.json`
3. Broadcast `SESSION_LEFT` system message tới tất cả active sessions
4. Ghi lại notes ngắn vào `~/.aiwf/session-bus/sessions/<my-id>.inbox.jsonl` cuối cùng:
   ```json
   {"type": "system", "event": "SELF_DEACTIVATED", "ts": "...", "handoff_notes": "..."}
   ```

---

## 11. Cross-Project Safety Rules

> [!CAUTION]
> **Các quy tắc bất khả xâm phạm:**

1. **Không đọc workspace của project khác**: Không mở file trong workspace của project-B, không read `.agents/` của project khác.
2. **Chỉ giao tiếp qua bus**: Toàn bộ dữ liệu trao đổi đi qua `~/.aiwf/session-bus/` — không có shortcut nào khác.
3. **Safe utility only**: Không write đè bất kỳ file inbox hay registry nào, và cũng không append JSONL bằng tay. Mọi write mailbox phải đi qua `scripts/session_mailbox.py` hoặc helper tương đương có JSON serializer + lock. Duy nhất cursor file và snapshot.json được ghi đè.
4. **Không tự duyệt yêu cầu có side-effect**: Khi nhận `request` có side-effect (đụng file, rebuild, thay đổi hợp đồng API), báo Ba qua Telegram trước khi thực hiện — giống quy tắc session-mail.
5. **msg_id unique**: Sinh UUID v4 (hoặc `<session-id>-<timestamp>-<random>`) cho mỗi tin. Dùng để dedup nếu cần.
6. **Bus version**: Luôn kèm `"bus_version": "1.0"` trong mọi message. Consumer bỏ qua message có version không tương thích.

---

## 12. Schedule-Based Listening

Agent lắng nghe bus bằng **`schedule` tool** — không cần external script hay process nào.

### Cơ chế

```
JOIN xong
  → arm schedule(DurationSeconds="30", Prompt="Poll bus inbox")
  → ... agent làm việc khác ...
  → schedule wakeup
  → RECEIVE flow (đọc inbox + groups từ cursor)
  → xử lý tin nhắn mới
  → arm schedule tiếp theo
  → lặp lại
```

### Poll interval khuyến nghị

| Mức độ | DurationSeconds | Dùng khi |
|--------|----------------|----------|
| Thường | `"30"` | Phối hợp không khẩn cấp |
| Nhanh  | `"10"` | Đang trao đổi tích cực với session khác |
| Chậm   | `"60"` | Session đang làm việc độc lập, cần biết tin tức mới |

### Tự điều chỉnh interval

- Sau khi nhận tin nhắn → arm `"10"` (session khác đang tích cực gửi)
- Sau N vòng im lặng → tăng lên `"30"` hoặc `"60"` để tiết kiệm token
- Khi join group `urgent` → arm `"10"` bất kể context

### Heartbeat

Mỗi 10 lần wakeup (≈ 5 phút với interval 30s), cập nhật `last_seen` trong `registry.snapshot.json`
để các session khác biết mình vẫn active.

---

## 13. Tương thích với session-mail nội bộ

Skill này **không thay thế** `.agents/session-mail/`. Hai cơ chế tồn tại song song:

| | session-mail | session-mailbox |
|---|---|---|
| Phạm vi | Nội bộ 1 project | Liên project trên cùng máy |
| Vị trí | `.agents/session-mail/` | `~/.aiwf/session-bus/` |
| Groups | Không | Có |
| Broadcast | Không | Có |
| Discovery | Đọc README | registry.snapshot.json |

Agent có thể dùng **cả hai** đồng thời: dùng session-mail cho giao tiếp trong project,
và session-mailbox cho giao tiếp liên project.

---

## 14. Quick Reference

```
JOIN:      Làm 6 bước ở mục 5
SEND:      python skills\session-mailbox\scripts\session_mailbox.py send --from <me> --to <to> --message "<message>"
RECEIVE:   Đọc inbox của mình từ cursor, advance cursor
BROADCAST: Fan-out through the same safe utility/helper; no raw JSON append
GROUP:     Write group JSONL through the same safe utility/helper; no raw JSON append
LEAVE:     Write registry inactive record through the same safe utility/helper
```
