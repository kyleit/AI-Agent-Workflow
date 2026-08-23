# Bus Schema — Cross-Project Session Bus v1.0

Tài liệu tham chiếu đầy đủ schema, versioning, và backward compatibility.

---

## 1. Versioning

| Version | Ngày | Thay đổi |
|---------|------|----------|
| 1.0     | 2026-08-06 | Initial release — Direct msg, Broadcast, Group/Topic |

Mọi message phải có `"bus_version": "1.0"`. Consumer bỏ qua (log warning) nếu version không tương thích.

---

## 2. Message Types

| type | Mô tả | `to` field |
|------|-------|------------|
| `msg` | Direct message 1-1 | `<session-id>` |
| `broadcast` | Gửi tất cả active | `"BROADCAST"` |
| `group_msg` | Gửi vào group | `"GROUP:<group-name>"` |
| `system` | Event hệ thống | `"BROADCAST"` hoặc `<session-id>` |
| `ack` | Xác nhận nhận tin | `<original-sender-id>` |
| `request` | Yêu cầu có response | `<session-id>` |
| `response` | Phản hồi request | `<session-id>` |

---

## 3. System Event Types

| event | Khi nào | payload |
|-------|---------|---------|
| `SESSION_JOINED` | JOIN bus | `{session_id, role, project_name}` |
| `SESSION_LEFT` | LEAVE bus | `{session_id, handoff_notes}` |
| `SESSION_HEARTBEAT` | Định kỳ ~5 phút | `{session_id, status, last_seen}` |
| `GROUP_JOINED` | Thêm vào group | `{session_id, group}` |
| `GROUP_LEFT` | Rời group | `{session_id, group}` |
| `SELF_DEACTIVATED` | Session tắt | `{reason, handoff_notes}` |
| `BUS_INIT` | Tạo bus lần đầu | `{created_by, created_at}` |

---

## 4. Full Message Schema

### 4.1 Direct Message

```json
{
  "from":               "<string:8-char-session-id>",
  "from_project":       "<string:absolute-path>",
  "from_project_name":  "<string:human-readable-name>",
  "to":                 "<string:8-char-session-id>",
  "to_project":         "<string:absolute-path>",
  "ts":                 "<string:ISO8601-with-tz>",
  "type":               "msg",
  "content":            "<string:message-body>",
  "bus_version":        "1.0",
  "msg_id":             "<string:uuid-v4-or-session-ts-random>",
  "reply_to":           "<string:msg_id | null>",
  "priority":           "normal | high | urgent"
}
```

Fields bắt buộc: `from`, `to`, `ts`, `type`, `content`, `bus_version`, `msg_id`
Fields tùy chọn: `to_project`, `reply_to`, `priority` (mặc định: `normal`)

### 4.2 Broadcast Message

```json
{
  "from":               "<string>",
  "from_project":       "<string>",
  "from_project_name":  "<string>",
  "to":                 "BROADCAST",
  "ts":                 "<ISO8601>",
  "type":               "broadcast",
  "content":            "<string>",
  "bus_version":        "1.0",
  "msg_id":             "<string>",
  "priority":           "normal | high | urgent"
}
```

### 4.3 Group Message

```json
{
  "from":               "<string>",
  "from_project":       "<string>",
  "from_project_name":  "<string>",
  "to":                 "GROUP:<group-name>",
  "ts":                 "<ISO8601>",
  "type":               "group_msg",
  "group":              "<string:group-name>",
  "content":            "<string>",
  "bus_version":        "1.0",
  "msg_id":             "<string>"
}
```

### 4.4 System Message

```json
{
  "from":         "<string>",
  "from_project": "<string>",
  "to":           "BROADCAST | <session-id>",
  "ts":           "<ISO8601>",
  "type":         "system",
  "event":        "<string:EVENT_TYPE>",
  "payload":      { "<key>": "<value>" },
  "bus_version":  "1.0",
  "msg_id":       "<string>"
}
```

### 4.5 Request / Response

```json
{
  "from":         "<string>",
  "from_project": "<string>",
  "to":           "<string>",
  "to_project":   "<string>",
  "ts":           "<ISO8601>",
  "type":         "request",
  "request_id":   "<string:uuid>",
  "action":       "<string:what-you-want>",
  "params":       { "<key>": "<value>" },
  "timeout_sec":  60,
  "content":      "<string:human-readable description>",
  "bus_version":  "1.0",
  "msg_id":       "<string>"
}
```

Response:
```json
{
  "from":         "<string>",
  "from_project": "<string>",
  "to":           "<string:original-requester>",
  "ts":           "<ISO8601>",
  "type":         "response",
  "request_id":   "<string:same-as-request>",
  "status":       "ok | error | pending | requires_approval",
  "result":       { "<key>": "<value>" },
  "content":      "<string>",
  "bus_version":  "1.0",
  "msg_id":       "<string>"
}
```

---

## 5. Registry Schema

### registry.jsonl — event log

Mỗi dòng = 1 sự kiện registry (JSONL). Không xóa. Khi cần append, phải ghi qua
`scripts/session_mailbox.py` hoặc helper tương đương có JSON serializer + lock;
không dùng `echo`, `>>`, here-string, hoặc JSON tự nối chuỗi.

```json
{
  "session_id":     "<string:8-char>",
  "project_path":   "<string:absolute>",
  "project_name":   "<string>",
  "role":           "<string:free-text mô tả vai trò>",
  "topics":         ["<string>"],
  "groups":         ["<string>"],
  "joined_at":      "<ISO8601>",
  "last_seen":      "<ISO8601>",
  "status":         "active | inactive | away | busy",
  "inbox_path":     "~/.aiwf/session-bus/sessions/<session-id>.inbox.jsonl",
  "bus_version":    "1.0"
}
```

Consumer logic: đọc toàn bộ file → nhóm theo `session_id` → lấy record cuối = trạng thái mới nhất.

### registry.snapshot.json — materialized view

Được ghi đè (KHÔNG append) bởi agent sau JOIN/LEAVE/HEARTBEAT:

```json
{
  "last_updated": "<ISO8601>",
  "bus_version":  "1.0",
  "sessions": {
    "<session-id>": {
      "project_path":   "<string>",
      "project_name":   "<string>",
      "role":           "<string>",
      "groups":         ["<string>"],
      "status":         "active | inactive | away | busy",
      "last_seen":      "<ISO8601>",
      "inbox_path":     "<string>"
    }
  }
}
```

> Snapshot có thể stale vài giây. Nếu cần chính xác, đọc `registry.jsonl`.

---

## 6. Group Members Schema

`~/.aiwf/session-bus/groups/<group-name>.members.json`:

```json
{
  "group":      "<string>",
  "created_by": "<session-id>",
  "created_at": "<ISO8601>",
  "description": "<string:optional>",
  "members": [
    {
      "session_id":   "<string>",
      "project_name": "<string>",
      "joined_at":    "<ISO8601>",
      "status":       "active | inactive"
    }
  ]
}
```

---

## 7. Backward Compatibility với session-mail

| Field | session-mail | session-mailbox |
|-------|-------------|-------------------|
| `from` | session-id | session-id |
| `to` | session-id | session-id / BROADCAST / GROUP:x |
| `ts` | ISO8601 | ISO8601 |
| `type` | `"msg"` | `msg/broadcast/group_msg/system/...` |
| `content` | string | string |
| `from_project` | ❌ không có | ✅ thêm mới |
| `bus_version` | ❌ không có | ✅ thêm mới |
| `msg_id` | ❌ không có | ✅ thêm mới |

Session chạy `session-mail` thuần có thể đọc message cross-bus (ignore unknown fields).
Agent hỗ trợ cross-bus phải ignore message thiếu `bus_version` (coi là legacy intra-project).

---

## 8. File Naming Conventions

```
sessions/<8-char-id>.inbox.jsonl          ← inbox của session
sessions/.<8-char-id>.cursor              ← cursor của session (số dòng đã đọc)
sessions/<8-char-id>.watcher.log          ← watcher log (optional)
groups/<group-name>.inbox.jsonl           ← inbox của group
groups/.<group-name>.cursor.<session-id>  ← cursor của 1 member trong group
groups/<group-name>.members.json          ← danh sách member của group
```

Tên group: lowercase, alphanumeric + hyphen, max 32 chars. Ví dụ: `infra`, `feat-035`, `release-v7`.

---

## 9. Deduplication

Mỗi consumer tự dedup nếu cần:
- Lưu `msg_id` của các tin đã xử lý trong session turn hiện tại
- Nếu gặp `msg_id` đã biết → bỏ qua, không xử lý lại
- Dedup không bắt buộc — bus không đảm bảo exactly-once, chỉ at-least-once

---

## 10. Error Handling

| Tình huống | Xử lý |
|-----------|-------|
| Inbox file không tồn tại | Tạo file rỗng (session chưa JOIN) |
| registry.snapshot.json không tồn tại | Tạo snapshot rỗng `{"last_updated":"...","sessions":{}}` |
| Message malformed (invalid JSON) | Log warning, bỏ qua dòng, advance cursor |
| `bus_version` không tương thích | Log warning, bỏ qua tin đó |
| Recipient không trong registry | Log warning, không gửi |
| Group không tồn tại | Tạo group mới hoặc báo lỗi tùy context |
