---
name: msgbus-ws
command: msgbus
aliases:
  - msgbus-ws
  - msgbus
  - lan-bus
  - ws-bus
  - cross-machine-bus
category: communication
tags:
  - cross-machine
  - lan
  - websocket
  - realtime
  - file-transfer
  - tus
  - e2ee
  - multi-agent
version: 1.0.0
license: MIT
created_at: 2026-08-13
updated_at: 2026-08-13
description: >
  LAN realtime message + file bus. Cho phép các session Claude Code ở HAI MÁY
  KHÁC NHAU / khác IP (ví dụ Windows + Mac cùng LAN) trao đổi tin nhắn realtime
  và gửi/nhận file trực tiếp — một máy chạy relay HTTP+WebSocket (host), cả hai
  bên nối vào như client. Server PUSH qua WebSocket (không poll). Có 2 kênh
  (broadcast + private/P2P), upload/download resumable qua tus + HTTP Range, và
  E2EE tùy chọn. Là bản BỔ TRỢ cho session-mailbox (không thay thế): dùng
  session-mailbox cho các session CÙNG máy, dùng msgbus-ws cho KHÁC máy.
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
store_root: "~/.aiwf/msgbus"
stdlib_only: true
agent_self_bootstrap: true
---

# Skill: msgbus-ws

## 1. Tổng quan

Skill này cung cấp một **relay HTTP + WebSocket** chạy trên LAN để các session
Claude Code ở **các MÁY khác nhau** giao tiếp realtime và trao đổi file — mà
không cần Ba copy tay giữa hai máy.

Một máy chạy **server (host)**, cả hai (hoặc nhiều) bên nối vào như **client**
qua mạng LAN. Server **đẩy (PUSH)** mỗi tin mới xuống mọi WebSocket client ngay
lập tức, nên không cần poll.

### Khi nào dùng skill này (so với `session-mailbox`)

| | `session-mailbox` | **`msgbus-ws`** |
| :-- | :-- | :-- |
| Kênh truyền | Shared filesystem (`~/.aiwf/session-bus/`) | HTTP + WebSocket qua LAN |
| Phạm vi | Nhiều session **CÙNG một máy** | Nhiều session **KHÁC máy / khác IP** |
| Realtime | Poll theo `schedule` | Server **PUSH** qua WS (tức thời) |
| Gửi file | Không | **Có** (tus upload + Range download, resumable) |
| E2EE | Không | **Có** (tùy chọn) |

> [!IMPORTANT]
> `msgbus-ws` **KHÔNG thay thế** `session-mailbox`. Hai bên khác máy → dùng
> `msgbus-ws`. Các session trong cùng một máy → dùng `session-mailbox`.

> [!NOTE]
> Agent tự bootstrap skill này không cần gọi `initialize-workflow`. Chỉ cần đọc
> SKILL.md này, chạy host (hoặc nối vào host có sẵn), rồi `listen`.

### Đặc điểm kỹ thuật
- **Stdlib-only**: server và client chỉ dùng thư viện chuẩn của Python (không
  `pip install`). Copy sang máy nào có `python3` là chạy — kể cả macOS.
- **Kiến trúc**: package `msgbusws/` theo Clean Architecture (domain / application
  / infrastructure / interface / client), DI qua composition root.

---

## 2. Kiến trúc & vị trí file

```
skills/msgbus-ws/scripts/
├── msgbus_server.py      ← entrypoint server (mỏng)
├── msgbus_client.py      ← entrypoint client (mỏng)
└── msgbusws/             ← package Clean Architecture
    ├── domain/           ← models, routing (broadcast/private), identity (tên Việt), ports
    ├── application/      ← bus_service (use-cases; chỉ phụ thuộc ports)
    ├── security/         ← cipher (E2EE) + envelope
    ├── infrastructure/   ← ws_protocol, jsonl_message_store, file_system_store, tus_upload_store, memory_registry, system_clock
    ├── interface/        ← http_handler (REST+WS+tus), server_app (composition root)
    └── client/           ← config, rest_client, tus_client, ws_client, commands
```

Store dữ liệu mặc định: **`~/.aiwf/msgbus/`** — `messages.jsonl` (append-only,
`seq` tăng dần) + thư mục `files/` + `uploads/` (phiên tus dở dang).

---

## 2b. Setup dễ nhất — aiwf profile (khuyến nghị)

Lưu 1 lần connection profile vào `~/.aiwf/msgbus.json`, sau đó mọi session join
bằng 1 lệnh, khỏi gõ env. Profile do `init` ghi ra (token có `chmod 600`).

```bash
# 1 lần: lưu profile (trỏ tới bus đã deploy)
python skills/msgbus-ws/scripts/msgbus_client.py \
  --host msgbus.example.invalid --tls --token <MSGBUS_TOKEN> [--e2ee-key <KEY>] init
# hoặc gọn: skills/msgbus-ws/bin/aiwf-msgbus init --host ... --tls --token ...

# từ đó về sau — không cần env:
skills/msgbus-ws/bin/aiwf-msgbus join                 # listen realtime (wss)
skills/msgbus-ws/bin/aiwf-msgbus send "chào" --to "Bảo Ngọc"
skills/msgbus-ws/bin/aiwf-msgbus upload ./a.zip
```

Thứ tự ưu tiên cấu hình: **CLI flag > env `MSGBUS_*` > profile `~/.aiwf/msgbus.json` > default**.
Đổi vị trí profile bằng env `MSGBUS_CONFIG`. Mẫu: `skills/aiwf/config/msgbus.example.json`.
`launcher aiwf-msgbus` (bash + `.ps1`) chỉ gọi `msgbus_client.py` nên chạy mọi nơi có python.

---

## 3. Chạy host (server)

```bash
python skills/msgbus-ws/scripts/msgbus_server.py \
  --port 8787 --token "MOT-CHUOI-BI-MAT" \
  --store ~/.aiwf/msgbus --bind 0.0.0.0
```

Hoặc cấu hình bằng env: `MSGBUS_PORT`, `MSGBUS_TOKEN`, `MSGBUS_STORE`, `MSGBUS_BIND`.

Kiểm tra host sống:
```bash
curl http://<LAN-IP>:8787/health
# -> {"ok": true, "messages": 0, "files": 0, "ws_clients": 0}
```

> [!CAUTION]
> **Store phải nằm ở thư mục ỔN ĐỊNH** (mặc định `~/.aiwf/msgbus/`). TUYỆT ĐỐI
> không đặt store trong thư mục temp/scratchpad — nó bị dọn giữa chừng làm server
> trả **500** khi ghi `/send` hoặc `/upload`. (Đã dính thực tế.)

---

## 4. Nối client & NHẬN realtime

Cấu hình client qua env (khuyến nghị export 1 lần mỗi session):
```bash
export MSGBUS_HOST=10.10.10.20     # LAN IP của máy host
export MSGBUS_PORT=8787
export MSGBUS_TOKEN="MOT-CHUOI-BI-MAT"
export MSGBUS_FROM="Minh Khôi"     # tùy chọn — bỏ trống sẽ tự sinh tên Việt
```

### 3 cách NHẬN realtime (ưu tiên từ trên xuống)

**① `msgbus_client.py listen` — WebSocket receive thuần (CÁCH CHÍNH)**
```bash
python skills/msgbus-ws/scripts/msgbus_client.py listen --since 0
```
Mở WebSocket, in mỗi tin ngay khi server push (`#seq [ts] from → to: text`), giữ
kết nối, **tự reconnect** khi rớt và tiếp tục từ `seq` lớn nhất đã nhận (không
trùng/không sót). Chạy ở mọi môi trường có `python3`.

**② Tool `Monitor` của Claude Code với `ws:` source** — tiện khi muốn AI được
đánh thức tự động. Trỏ Monitor vào:
```
ws://<host>:<port>/ws?token=<TOKEN>&name=<TÊN>&since=<seq>
```
Mỗi frame JSON server đẩy = 1 event.

> [!NOTE]
> Một số harness chặn Monitor WS tới IP private. Nếu vậy → quay lại cách ① hoặc ③.

**③ Poll `GET /recv?since=N`** (fallback khi WS bị chặn):
```bash
python skills/msgbus-ws/scripts/msgbus_client.py recv --since 0
```

---

## 5. Gửi tin (2 kênh: broadcast + private/P2P)

```bash
# Broadcast — mọi client nhận
python .../msgbus_client.py send "chào cả nhà"

# Private/P2P — chỉ peer <tên> (và người gửi) nhận
python .../msgbus_client.py send "gửi riêng Bảo Ngọc" --to "Bảo Ngọc"

# Gửi qua WebSocket (chứng minh chiều gửi qua WS cũng chạy)
python .../msgbus_client.py ws-send "hé lô qua WS" --to "Bảo Ngọc"
```

Định tuyến: `to` rỗng → **broadcast**; `to="<tên>"` → **private** (chỉ tới peer
đó và chính người gửi). `seq` tăng dần toàn cục; catch-up/replay lọc theo tên nên
mỗi client chỉ thấy broadcast + private-cho-mình.

---

## 6. Gửi/nhận FILE (tus resumable + Range)

```bash
# Upload (tus 1.0.0 — resumable: đứt giữa chừng chạy lại là tiếp, không lại từ đầu)
python .../msgbus_client.py upload ./build.zip
python .../msgbus_client.py upload ./secret.zip --to "Bảo Ngọc"   # kèm thông báo private

# Liệt kê file trên bus
python .../msgbus_client.py list

# Download (HTTP Range — resume từ <out>.part nếu đứt)
python .../msgbus_client.py download build.zip --out ./got.zip
```

Khi upload xong, mọi listener nhận 1 dòng thông báo `[file] build.zip (N bytes)
uploaded by <tên>`. Tải về rồi đối chiếu `sha256` để chắc chắn khớp.

---

## 7. E2EE (mã hóa đầu-cuối, tùy chọn)

Bật bằng passphrase chia sẻ ngoài băng (Ba đưa cho cả hai máy):
```bash
export MSGBUS_E2EE_KEY="cau-mat-khau-that-dai-va-manh"
```
Khi có key: `send`/`ws-send` **mã hóa nội dung trước khi gửi**, `listen`/`recv`
**giải mã sau khi nhận**. Relay server chỉ thấy **ciphertext** — không đọc được
nội dung. Peer cùng key giải mã được; peer không có key thấy `[encrypted]`.

> [!WARNING]
> **Giới hạn trung thực của E2EE** (đây là công cụ điều phối LAN, không phải sản
> phẩm nhắn tin bảo mật):
> - Dùng passphrase chia sẻ (PSK), **không có forward secrecy**, không xoay khóa.
> - Construction Encrypt-then-MAC tự dựng trên stdlib (`scrypt` + SHA256-CTR +
>   HMAC-SHA256) vì stdlib không có AES-GCM. Hãy dùng passphrase mạnh.
> - **Metadata KHÔNG được giấu**: `from`, `to`, `seq`, `ts`, kích thước, tên file
>   vẫn hiện với relay (cần để định tuyến). E2EE chỉ bảo vệ **nội dung**.

---

## 8. Handshake & tên session

- Mỗi session **tự đặt 1 tên người Việt** riêng để Ba dễ gọi. Nếu `MSGBUS_FROM`
  chưa set, client tự sinh (ví dụ `"Minh Khôi"`, `"Bảo Ngọc"`) và in ra khi khởi động.
- Khi vào bus, `listen` gửi 1 tin STATUS chào (`"<tên> đã vào bus"` — dạng rõ để
  ai cũng biết ai vừa vào). Đối phương đọc `since=0` để bắt kịp lịch sử.

---

## 9. GOTCHAS BẮT BUỘC (đã va thực tế — đừng lặp lại)

1. **Store ở thư mục ổn định** `~/.aiwf/msgbus/`, KHÔNG để trong temp/scratch →
   nếu bị dọn, `/send` `/upload` trả **500**.
2. **Host & port**: bind `0.0.0.0`. Nhưng nếu app khác đang chiếm
   `127.0.0.1:<port>`, bind loopback cụ thể đó **che** bind `0.0.0.0` cho traffic
   loopback → client **TRÊN CHÍNH máy host** phải gọi bằng **LAN IP** (vd
   `10.10.10.20`), KHÔNG dùng `127.0.0.1`. Port phải **cấu hình được** để né
   xung đột (`--port` / `MSGBUS_PORT`).
3. **Firewall inbound**: máy host có thể chặn cổng (non-admin không mở rule được).
   Mở cổng bằng lệnh admin, ví dụ trên Windows:
   ```powershell
   New-NetFirewallRule -DisplayName "msgbus-ws 8787" -Direction Inbound `
     -Action Allow -Protocol TCP -LocalPort 8787 -RemoteAddress 10.10.10.0/24
   ```
   HOẶC chọn máy host là bên có firewall dễ chấp thuận (macOS hỏi "Allow" 1 lần).
   Bên còn lại chỉ cần outbound (thường luôn thông).
4. **Chọn máy nào host**: ưu tiên máy **chấp nhận inbound được**; máy kia nối
   outbound.
5. **Monitor WS tới IP private** có thể bị harness của một số máy chặn → fallback
   `msgbus_client.py listen` (python) hoặc poll `/recv`.
6. **Bootstrap chicken-egg** (đưa server sang máy kia): xem mục 10.
7. **Đặt tên**: mỗi session tự đặt 1 tên người Việt, gửi STATUS chào khi vào,
   đối phương `since=0` để bắt kịp (mục 8).

---

## 10. Bootstrap: đưa server sang máy thứ hai

Vì server là stdlib-only, chỉ cần đưa cả thư mục `scripts/` sang máy kia:

**Cách A — copy thư mục** (scp/AirDrop/USB):
```bash
scp -r skills/msgbus-ws/scripts  user@10.10.10.30:~/msgbus-ws
# trên máy kia:
python ~/msgbus-ws/msgbus_server.py --port 8787 --token "BI-MAT" --bind 0.0.0.0
```

**Cách B — one-liner tự đóng gói** (chạy trên máy host, tạo tarball base64 để dán
sang máy kia rồi giải nén + chạy):
```bash
# máy host: in ra 1 khối base64
tar -czf - -C skills/msgbus-ws scripts | base64
# máy kia: dán vào <PAYLOAD> rồi chạy
mkdir -p ~/msgbus-ws && echo "<PAYLOAD>" | base64 -d | tar -xzf - -C ~/msgbus-ws
python ~/msgbus-ws/scripts/msgbus_server.py --port 8787 --token "BI-MAT" --bind 0.0.0.0
```

---

## 11. HTTP API (tham chiếu)

Auth: header `X-Token` cho REST, query `?token=` cho WS.

| Method | Path | Ý nghĩa |
| :-- | :-- | :-- |
| `GET` | `/health` | `{ok, messages, files, ws_clients}` (không cần token) |
| `POST` | `/send` | hdr `X-From`, opt `X-To`; body=text → `{seq}` + push |
| `GET` | `/recv?since=N` | opt `X-From` (lọc private) → `[{seq,ts,from,to,text}]` |
| `OPTIONS` | `/files` | năng lực tus (`Tus-*`) |
| `POST` | `/files` | tus create (`Upload-Length`, `Upload-Metadata`) → `201 Location` |
| `HEAD` | `/files/<id>` | tus offset để resume (`Upload-Offset`) |
| `PATCH` | `/files/<id>` | tus chunk (`Upload-Offset`, `application/offset+octet-stream`) |
| `GET` | `/download?name=` | opt `Range: bytes=N-` → 200/206 |
| `GET` | `/list` | `[{name,size,ts}]` |
| `GET` | `/ws?token=&name=&since=N` | 101 Upgrade → replay + stream. Frame text=broadcast; JSON `{"to","text"}`=private |

---

## 12. Cheat-sheet

```bash
# HOST (một máy)
python .../msgbus_server.py --port 8787 --token BI-MAT --store ~/.aiwf/msgbus --bind 0.0.0.0

# CLIENT (mỗi máy) — env
export MSGBUS_HOST=10.10.10.20 MSGBUS_PORT=8787 MSGBUS_TOKEN=BI-MAT
export MSGBUS_FROM="Minh Khôi"          # bỏ trống -> tự sinh tên Việt
export MSGBUS_E2EE_KEY="mat-khau-dai"   # tùy chọn: bật E2EE

python .../msgbus_client.py health
python .../msgbus_client.py listen                    # NHẬN realtime (cách chính)
python .../msgbus_client.py send "chào"               # broadcast
python .../msgbus_client.py send "riêng" --to "Bảo Ngọc"
python .../msgbus_client.py ws-send "qua WS" --to "Bảo Ngọc"
python .../msgbus_client.py upload ./a.zip            # tus resumable
python .../msgbus_client.py download a.zip --out b.zip
python .../msgbus_client.py recv --since 0            # poll fallback
```

> [!NOTE]
> Là bản BỔ TRỢ cho `session-mailbox`: cùng máy → `session-mailbox`; khác máy →
> `msgbus-ws`.
