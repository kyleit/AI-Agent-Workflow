<!-- docs/designs/FEAT-010_workflow_runtime_engine_blueprint.md -->

---
feature_id: FEAT-010
feature_name: AI Workflow Runtime Engine Refactor
status: draft
stage: design
created_at: 2026-07-06
updated_at: 2026-07-06
previous_artifact: ../plans/FEAT-010_workflow_runtime_engine_plan.md
next_artifact: None
---

# Technical Blueprint – AI Workflow Runtime Engine Refactor

Bản vẽ thiết kế kỹ thuật chi tiết cấu trúc mô-đun và API của CLI Runtime Engine thưa Ba.

## 1. Kiến trúc thư mục (Directory Structure Layout)
Công cụ điều khiển Runtime sẽ được cấu trúc hóa sạch sẽ như sau:

```text
skills/workflow-runtime/
├── SKILL.md             # Tài liệu định nghĩa kỹ năng thu gọn chỉ gọi CLI
├── README.md            # Tài liệu hướng dẫn sử dụng API CLI
├── scripts/
│   ├── workflow_runtime.py  # CLI Entry point: Điều phối lệnh và tham số
│   ├── session.py           # Quản lý đọc/ghi tệp .session.json nguyên tử
│   ├── context.py           # Tính toán token tiêu thụ tự động
│   ├── checkpoint.py        # Bản đồ mốc và quy tắc xác thực checkpoint
│   ├── validator.py         # Kiểm tra sức khỏe môi trường và git
│   ├── heartbeat.py         # Định dạng và in khối nhịp tim (heartbeat)
│   ├── drift.py             # Phát hiện sai lệch ngữ cảnh (context drift)
│   └── utils.py             # Tiện ích chung (đường dẫn, thời gian ISO)
└── tests/
    └── test_runtime.py      # Bộ unit tests cho CLI Engine
```

---

## 2. Đặc tả CLI API & Tham số (CLI Contract)
Tập lệnh entry point `workflow_runtime.py` sẽ thực thi qua lệnh `python workflow_runtime.py <command> [options]` với các API:

### Lệnh 1: `init`
Khởi tạo tệp `.session.json` mới nếu chưa tồn tại.
*   **Tham số**: Không yêu cầu.
*   **Hành vi**: Nếu chưa có tệp session, sinh GUID mới làm `conversation_id`. Nếu đã có, giữ nguyên.

### Lệnh 2: `validate`
Thực thi kiểm tra tính hợp lệ của workspace, checkpoint và sai lệch nhánh.
*   **Tham số**: `--checkpoint <int>`
*   **Hành vi**: So sánh checkpoint hiện tại trong session với giá trị yêu cầu. Trả về mã lỗi `1` nếu không khớp hoặc bị lệch nhánh.

### Lệnh 3: `start`
Cập nhật trạng thái phiên chạy sang `"in_progress"`.
*   **Tham số**: `--skill <str> --command <str> --checkpoint <int> --step <str>`
*   **Hành vi**: Ghi đè trạng thái, cập nhật checkpoint, và thêm dòng nhật ký khởi tạo vào danh sách `current_logs`.

### Lệnh 4: `step`
Ghi nhận tiến trình bước nhỏ đang thực thi.
*   **Tham số**: `--step <str> --log <str>`
*   **Hành vi**: Cập nhật `current_step` và thêm chuỗi `--log` vào mảng `current_logs`.

### Lệnh 5: `complete`
Cập nhật trạng thái hoàn tất thành công.
*   **Tham số**: `--checkpoint <int> --next-skill <str> --next-command <str>`
*   **Hành vi**: Đặt `status` là `"completed"`, đề xuất kỹ năng tiếp theo, và ghi nhận thời gian hoàn tất.

### Lệnh 6: `fail`
Đánh dấu phiên chạy thất bại do lỗi biên dịch/kiểm thử.
*   **Tham số**: `--step <str> --log <str>`
*   **Hành vi**: Đặt `status` là `"failed"`, cập nhật `current_step` và thêm chi tiết lỗi vào `current_logs`.

### Lệnh 7: `heartbeat`
Định dạng và hiển thị thông tin nhịp tim.
*   **Tham số**: Không yêu cầu.

---

## 3. Bản vẽ thiết kế các mô-đun Python (Class & Module Signatures)

### Mô-đun: `session.py` (Giới hạn < 150 dòng)
```python
def get_session_path() -> str:
    """Trả về đường dẫn tuyệt đối của tệp .session.json trong dự án."""

def load_session() -> dict:
    """Đọc và phân tích cú pháp tệp .session.json."""

def save_session_atomic(data: dict) -> None:
    """Ghi dữ liệu nguyên tử: ghi ra .session.json.tmp rồi đổi tên thay thế."""
```

### Mô-đun: `context.py` (Giới hạn < 100 dòng)
```python
def estimate_context_usage() -> dict:
    """
    Đọc kích thước tệp C:\\Users\\Kyle\\.gemini\\antigravity-ide\\brain\\<conv_id>\\.system_generated\\logs\\transcript.jsonl
    Ước lượng số lượng tokens = kích thước / 3 và tính toán phần trăm so với giới hạn 2,000,000.
    """
```

### Mô-đun: `validator.py` & `drift.py` (Giới hạn < 180 dòng)
```python
def run_workspace_check() -> dict:
    """Kiểm tra sự tồn tại của .git, các thư mục docs/ và cấu hình profile."""

def check_context_drift(session_data: dict) -> tuple[bool, str]:
    """So sánh Git branch hiện tại với branch lưu trong session để phát hiện sai lệch."""
```

---

## 4. Thiết kế các ca kiểm thử (Test Matrix)
Bộ mã kiểm thử `tests/test_runtime.py` sẽ sử dụng framework `unittest` chuẩn của Python để bao phủ các trường hợp:
1.  **Test Ghi Nguyên Tử**: Ghi đè tệp tin và xác nhận không có thời điểm nào tệp bị rỗng hoặc lỗi cú pháp JSON.
2.  **Test Bảo Toàn Conversation ID**: Chạy lệnh `init` nhiều lần và xác nhận `conversation_id` không bao giờ bị thay đổi.
3.  **Test Phát Hiện Drift**: Giả lập sai lệch nhánh git và xác nhận trả về mã lỗi thích hợp.
4.  **Test Hồi Phục Thất Bại**: Thử nghiệm đọc tệp JSON bị hỏng và tự động phục hồi từ cấu trúc mặc định.
