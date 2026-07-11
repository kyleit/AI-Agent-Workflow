# Hướng dẫn Quản lý Phân quyền Dự án qua CLI (FEAT-052)

Tài liệu này hướng dẫn Ba cách cấu hình, hiển thị, thay đổi và xác thực chế độ phân quyền (Permission Mode) của dự án sử dụng giao diện dòng lệnh (CLI).

---

## 1. Tổng quan về Cơ chế Phân quyền mới

Để đảm bảo tính an toàn và ngăn chặn các AI Agent tự ý thay đổi quyền hạn hoặc tự nâng quyền khi chưa được sự cho phép của Ba:
- Quyền hạn dự án được lưu trữ **tĩnh** trong tệp cấu hình: `.agents/config/permissions.json`.
- Mọi Skill và Runtime Command chỉ có quyền **đọc** cấu hình này (Read-Only) để thực thi.
- Thay đổi quyền chỉ có thể thực hiện thông qua **lệnh CLI thủ công do Ba chạy**.
- Mặc định khởi tạo sẽ chạy ở chế độ **Sandbox Mode** (an toàn nhất).

---

## 2. Các lệnh CLI Quản lý Phân quyền

Ba có thể thực thi phân quyền dễ dàng bằng cách sử dụng tập lệnh toàn cục `aiwf` (hoặc chạy trực tiếp tệp python `python skills/workflow-runtime/scripts/workflow_runtime.py`).

### 2.1. Khởi tạo Phân quyền (`init`)
Sử dụng lệnh này để tạo tệp cấu hình phân quyền tĩnh lần đầu tiên cho dự án.

```bash
# Khởi tạo mặc định ở chế độ Sandbox (An toàn)
aiwf permissions init --mode sandbox

# Khởi tạo trực tiếp ở chế độ Full Access (Cho phép chỉnh sửa code/file tự động)
aiwf permissions init --mode full_access

# Khởi tạo đè lên file cũ đã có (sử dụng thêm cờ --force)
aiwf permissions init --mode sandbox --force
```

> [!TIP]
> **Tự động di chuyển (Legacy Migration)**: Nếu Ba không truyền tham số `--mode`, hệ thống sẽ tự động tìm kiếm cấu hình quyền cũ trong phiên làm việc hiện tại của Ba để di chuyển và thiết lập cho tệp tin mới.
> ```bash
> aiwf permissions init
> ```

---

### 2.2. Xem Quyền hiện tại (`show`)
Hiển thị nội dung tệp tin cấu hình quyền dưới dạng JSON định dạng đẹp để kiểm tra.

```bash
aiwf permissions show
```

Nội dung trả về mẫu:
```json
{
  "schema_version": "1.0.0",
  "initialized": true,
  "mode": "sandbox",
  "config_revision": 1,
  "initialized_at": "2026-07-11T06:25:49.556177+07:00",
  "updated_at": "2026-07-11T06:25:49.556194+07:00",
  "updated_by": "user",
  "source": "cli"
}
```

---

### 2.3. Thay đổi chế độ Phân quyền (`change`)
Sử dụng lệnh này để nâng hoặc hạ chế độ phân quyền của dự án.

```bash
# Thay đổi sang Sandbox Mode (Hạ cấp đặc quyền - Diễn ra ngay lập tức)
aiwf permissions change --mode sandbox

# Thay đổi sang Full Access Mode (Leo thang đặc quyền - Bắt buộc xác nhận)
aiwf permissions change --mode full_access
```

> [!WARNING]
> **Cổng phê duyệt leo thang đặc quyền (Escalation Prompt Gate)**: 
> Khi Ba thực hiện thay đổi quyền làm tăng đặc quyền (ví dụ từ `sandbox` lên `full_access` hoặc `unrestricted`), CLI sẽ hiển thị cảnh báo đỏ và yêu cầu Ba xác nhận thủ công:
> ```text
> WARNING: Escalating permission mode from 'sandbox' to 'full_access'.
> This allows AI agents to execute code or write files with higher privileges.
> Are you sure you want to proceed? (y/N): 
> ```
> Ba cần nhập `y` hoặc `yes` để đồng ý thực hiện. Nếu chạy tự động trong script, Ba có thể truyền thêm tham số `--force` để bỏ qua bước xác nhận này:
> ```bash
> aiwf permissions change --mode full_access --force
> ```

---

### 2.4. Kiểm tra tính Hợp lệ của File Cấu hình (`validate`)
Xác thực cấu trúc JSON và các trường dữ liệu bắt buộc của tệp `.agents/config/permissions.json`.

```bash
aiwf permissions validate
```

- Nếu thành công, in ra: `Validation succeeded: permissions.json is valid.`
- Nếu tệp bị hỏng hoặc cấu trúc sai, in lỗi chi tiết và kết thúc với mã lỗi `1`.

---

## 3. Các Chế độ Phân quyền khả dụng (Permission Modes)

| Tên Chế độ | Mô tả Hành vi | Mức độ An toàn |
|---|---|---|
| `sandbox` | **Sandbox Mode**: Chế độ an toàn mặc định. Chặn các lệnh thực thi hệ thống hoặc thay đổi mã nguồn tự động của Agent trừ khi được Ba duyệt từng hành động (Per-action approval). | 🟢 Cao nhất |
| `full_access` | **Full Access Mode**: Cho phép Agent tự do tạo tệp tin, chỉnh sửa mã nguồn và cấu hình các bước trong phạm vi dự án mà không cần hỏi Ba nhiều lần. | 🟡 Trung bình |
| `unrestricted` | **Unrestricted Mode**: Quyền hạn tối đa. Cho phép truy cập mạng và thực thi các lệnh đặc quyền lớn hơn. | 🔴 Thấp nhất |
