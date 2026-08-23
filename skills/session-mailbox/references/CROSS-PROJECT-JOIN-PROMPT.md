# Prompt cho session MỚI JOIN Cross-Project Session Bus

> **Cách dùng:** Khi Ba mở session Claude Code mới ở **bất kỳ project nào** và muốn nó
> phối hợp với các session đang chạy ở **các project khác**, chỉ cần copy khối dưới dán
> vào session đó. Session sẽ tự JOIN bus, đăng ký, chào các session cũ, và poll tin tức tự động.
>
> Cross-project bus nằm ở `~/.aiwf/session-bus/` — toàn cục trên máy, không phụ thuộc project nào.
>
> Schema + flow đầy đủ ở `.agents/skills/session-mailbox/SKILL.md` (trong AgentsProject).
>
> Safe-write rule: mọi ghi mailbox/registry phải dùng
> `skills/session-mailbox/scripts/session_mailbox.py` hoặc helper tương đương có JSON serializer + lock.
> Không dùng `echo`, `>>`, here-string, read-then-append, hoặc JSON tự nối chuỗi.

---

## Template cơ bản (Direct Message + Broadcast)

```
Bạn đang chạy trên [TÊN PROJECT / ĐƯỜNG DẪN PROJECT] và cần phối hợp với các session Claude Code
đang chạy ở các project khác qua cross-project session bus.

Đọc skill hướng dẫn: `.agents/skills/session-mailbox/SKILL.md`
(nếu không access được, đọc references/BUS-SCHEMA.md và tự suy luận từ schema).

Sau khi đọc xong, hãy JOIN bus theo 6 bước trong mục 5 của SKILL.md:

1. Đọc registry: ~/.aiwf/session-bus/registry.snapshot.json (nếu tồn tại) để biết ai đang active.
2. Lấy short session id của bạn = 8 ký tự đầu của sessionId.
3. Tạo inbox: ~/.aiwf/session-bus/sessions/<id>.inbox.jsonl (rỗng, nếu chưa có) + cursor = 0.
4. Ghi registry record bằng safe mailbox utility/helper; không append JSON tay.
5. Cập nhật snapshot: ~/.aiwf/session-bus/registry.snapshot.json.
6. Gửi chào bằng safe mailbox utility/helper (SESSION_JOINED event vào inbox của từng session đang active).

Sau khi JOIN, mỗi lượt bắt đầu: đọc inbox của mình (từ cursor), xử lý tin mới, advance cursor.

Vai trò của bạn trong bus: [MÔ TẢ NGẮN VAI TRÒ — ví dụ: "coordinator-frontend maxbrowserfarm"]
```

---

## Template với GROUP (khi cần tham gia topic cụ thể)

```
Bạn đang chạy trên [TÊN PROJECT] và cần phối hợp qua cross-project session bus,
đặc biệt là group "[TÊN GROUP — ví dụ: infra, release, frontend]".

Đọc skill: `.agents/skills/session-mailbox/SKILL.md`

Làm theo 6 bước JOIN cơ bản (mục 5), sau đó thêm:
- JOIN group "[TÊN GROUP]" theo mục 9.2:
  * Đọc/tạo ~/.aiwf/session-bus/groups/<group>.members.json
  * Tạo cursor: ~/.aiwf/session-bus/groups/.<group>.cursor.<my-id> = 0
  * Ghi GROUP_JOINED system event vào group inbox bằng safe mailbox utility/helper
  * Cập nhật groups[] trong registry record của mình

Mỗi lượt: đọc cả session inbox lẫn group inbox (các group bạn đã join), xử lý tin mới.

Vai trò: [MÔ TẢ]
Groups cần join: [DANH SÁCH GROUP]
```

---

## Template khi biết cụ thể sessions đang chạy

```
Bạn đang chạy trên [TÊN PROJECT / ĐƯỜNG DẪN].

Đọc skill session-mailbox: `.agents/skills/session-mailbox/SKILL.md`

JOIN bus theo 6 bước. Các session hiện đang active:
- <session-id-1> — [project name] — [role]  → inbox: ~/.aiwf/session-bus/sessions/<id1>.inbox.jsonl
- <session-id-2> — [project name] — [role]  → inbox: ~/.aiwf/session-bus/sessions/<id2>.inbox.jsonl

Gửi tin cho session cụ thể: dùng safe mailbox utility/helper theo SKILL.md mục 6.
Nhận tin: đọc inbox của mình từ cursor (mục 7).

Vai trò của bạn: [MÔ TẢ]
Công việc: [MÔ TẢ NGẮN CÔNG VIỆC HIỆN TẠI]
Cần phối hợp: [AI CẦN PHỐI HỢP VÀ VỀ VẤN ĐỀ GÌ]
```

---

## Ghi chú

- **Ba không cần làm cầu nối**: Sau khi JOIN, session tự gửi/nhận với nhau.
- **Tin cần Ba quyết**: vẫn đi Telegram (theo skill notify-telegram). Bus chỉ là kênh session↔session.
- **An toàn**: Không đọc file workspace của project khác. Chỉ giao tiếp qua bus.
- **Khi session kết thúc**: LEAVE theo mục 10 của SKILL.md (ghi status=inactive bằng safe mailbox utility/helper).
- **Schema đầy đủ**: `.agents/skills/session-mailbox/references/BUS-SCHEMA.md`
