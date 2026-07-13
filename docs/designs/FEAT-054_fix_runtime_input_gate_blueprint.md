<!-- File path: docs/designs/FEAT-054_fix_runtime_input_gate_blueprint.md -->

---
feature_id: FEAT-054
feature_name: Fix Runtime Input Gate Bug
status: reviewed
stage: blueprint
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../plans/FEAT-054_fix_runtime_input_gate_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Design Blueprint & Implementation Contract – Fix Runtime Input Gate Bug

## 0. Baseline Context & References
- **Memory Baseline**: Hệ thống sử dụng một CLI Python trung tâm tại `skills/workflow-runtime/scripts/workflow_runtime.py` để cập nhật trạng thái phiên trong tệp `.session.json`. Quyền hạn workspace được gán lúc chạy lệnh `init`.
- **RAG Query Summaries**: `workflow_runtime.py` sử dụng hàm ghi atomic thông qua việc ghi vào tệp `.tmp` rồi đổi tên.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `.agents/.session.json`
  - `AI_RULES.md`

## 1. File-by-File Analysis & Proposed Mutations
| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Thêm logic chặn `waiting_input`, sinh `resume_token`, chặn nguồn AI, bổ sung sub-command `input submit` | None | Trung bình - Rủi ro ảnh hưởng tới các lệnh CLI khởi tạo khác |
| `AI_RULES.md` | MODIFY | Bổ sung chính sách an toàn "Runtime Input Gate Policy" | None | Thấp - Chỉ ảnh hưởng tới chỉ thị hướng dẫn AI |
| `skills/workflow-runtime/tests/test_runtime_gate.py` | NEW | Viết 10 test case bao phủ việc kiểm tra token và cấm nguồn AI | workflow_runtime.py | Thấp - Chỉ dùng cho chạy test tự động |

## 2. Target Folder Structure
```text
.
├── .agents
│   └── .session.json
├── AI_RULES.md
└── skills
    └── workflow-runtime
        ├── SKILL.md
        ├── scripts
        │   └── workflow_runtime.py
        └── tests
            └── test_runtime_gate.py
```

## 3. Complete Class & Module Design
Lớp hoặc thành phần mới được tích hợp vào `workflow_runtime.py`:
- **Class Name**: `RuntimeInputGate`
  - **Responsibilities**: Quản lý trạng thái chờ nhập liệu, sinh token bảo mật và xác thực đầu vào.
  - **Constructor Parameters**: None.
  - **Public Methods**:
    - `enter_waiting_state(prompt_id: str, question: str, options: list) -> dict`: Chuyển trạng thái session sang `waiting_input`, sinh và lưu `resume_token`, ghi lại cấu trúc câu hỏi.
    - `submit_input(prompt_id: str, value: str, source: str, token: str) -> bool`: Nhận đầu vào, thực hiện xác thực nguồn và token. Trả về `True` nếu hợp lệ.
  - **Internal Methods**:
    - `_generate_secure_token() -> str`: Sinh một chuỗi token ngẫu nhiên độ bảo mật cao bằng module `secrets`.
    - `_validate_source(source: str) -> bool`: Kiểm tra xem nguồn gửi lên có hợp lệ hay bị cấm.
  - **Dependencies**: Module `secrets`, module `json`, `SessionManager` (lớp hiện có quản lý session).
  - **Extension Points**: Có thể mở rộng để tích hợp các loại validation kiểu dữ liệu phức tạp hơn trong tương lai.

## 4. Detailed Interface Contracts
- **API Signature**: `enter_waiting_state(prompt_id: str, question: str, options: list) -> dict`
  - **Parameters**: 
    - `prompt_id` (str, bắt buộc, định danh duy nhất cho dấu nhắc)
    - `question` (str, bắt buộc, nội dung câu hỏi)
    - `options` (list, chứa danh mục các lựa chọn hợp lệ)
  - **Return Types**: `dict` chứa thông tin `pending_input` gồm `input_id`, `question`, `options`, `resume_token`, v.v.
  - **Exceptions**: None.
- **API Signature**: `submit_input(prompt_id: str, value: str, source: str, token: str) -> bool`
  - **Parameters**:
    - `prompt_id` (str, định danh duy nhất)
    - `value` (str, giá trị người dùng chọn)
    - `source` (str, nguồn gửi: `cli_user`, `user_chat`, `extension_ui`)
    - `token` (str, mã xác thực)
  - **Return Types**: `bool` (True nếu thành công, False nếu thất bại hoặc bị từ chối)
  - **Exceptions**: `ValueError` ném ra khi nguồn gửi là AI hoặc token không khớp.

## 5. Configuration Schema
- **Current Schema**: `.agents/.session.json` chỉ chứa thông tin checkpoint và trạng thái thô.
- **Target Schema**: Thêm trường `pending_input` vào schema của session:
  ```json
  "pending_input": {
    "input_id": "string",
    "question": "string",
    "options": "array",
    "source": "string",
    "allow_ai_default": "boolean",
    "allow_timeout_default": "boolean",
    "resume_token": "string",
    "created_at": "ISO-8601"
  }
  ```
- **Migration Rules**: Nếu trường này chưa tồn tại trong file session cũ, runtime tự động coi giá trị mặc định là `null`.

## 6. Database & Storage Design
- Không có thay đổi cơ sở dữ liệu vật lý nào. Chỉ lưu trữ trong bộ nhớ tạm thời thông qua tệp tin session JSON.

## 7. Cache Architecture
- Không áp dụng.

## 8. Error Model
- **Exception Class**: `ForbiddenAISourceError`
  - **Trigger Condition**: Khi nhận được dữ liệu submit có `source=ai` hoặc tương đương.
  - **Recovery Strategy**: Ghi log lỗi bảo mật, giữ nguyên trạng thái session ở `waiting_input` và dừng luồng.
- **Exception Class**: `InvalidResumeTokenError`
  - **Trigger Condition**: Khi mã xác thực token gửi lên lệch với mã lưu trong session.
  - **Recovery Strategy**: Thông báo lỗi token không khớp, giữ nguyên trạng thái chờ.

## 9. Skill Integration Contracts
- **Skill initialize-workflow**: Khi chạy lệnh khởi tạo cần chọn quyền hạn, gọi `RuntimeInputGate.enter_waiting_state()` để ghi nhận trạng thái và dừng. Sau khi nhận submit, resume lại skill từ checkpoint 1.

## 10. CLI & Runtime Contracts
- **Command Syntax**: `python skills/workflow-runtime/scripts/workflow_runtime.py input submit --input-id workspace_permission_mode --value sandbox --source cli_user --resume-token <token>`
  - **Parameters**:
    - `--input-id` (chuỗi định danh câu hỏi)
    - `--value` (lựa chọn gửi lên)
    - `--source` (nguồn gửi dữ liệu)
    - `--resume-token` (mã bảo mật)
  - **Output**: JSON string `{"success": true, "message": "Input accepted. Resuming workflow..."}` hoặc lỗi.
  - **Exit Codes**: `0` (thành công), `1` (lỗi token/nguồn bị từ chối).

## 11. Sequence Flows
- **Normal Flow**:
  1. CLI gọi khởi tạo -> cần nhập liệu -> gọi `enter_waiting_state()`.
  2. Runtime sinh token bảo mật, lưu vào `.session.json`, đặt trạng thái thành `waiting_input` và dừng.
  3. AI Agent thấy trạng thái `waiting_input` thì dừng lại và hiển thị câu hỏi cho Ba.
  4. Ba chọn phương án -> GUI/CLI gửi lệnh `input submit` kèm token và `source=cli_user`.
  5. Runtime xác thực token và nguồn hợp lệ -> xóa `pending_input` -> cập nhật status thành `completed` và chạy tiếp.
- **AI Attack Flow**:
  1. AI tự tạo lệnh submit với `source=ai` hoặc không truyền token.
  2. Runtime kiểm tra nguồn -> phát hiện nguồn bị cấm -> ném lỗi `ForbiddenAISourceError` -> tiếp tục khóa luồng.

## 12. Security & Safety
- **Workspace Boundary**: Chỉ đọc/ghi trong phạm vi tương đối của workspace.
- **Token Entropy**: `resume_token` được sinh ra sử dụng `secrets.token_hex(16)` có độ ngẫu nhiên cực cao chống tấn công dò đoán.
- **Source Hardening**: Chỉ chấp nhận nguồn do con người khởi phát.

## 13. Complete Test Matrix
| Requirement ID | Test Type | Test File Target | Mapped Component | Verification Assertion |
| :--- | :--- | :--- | :--- | :--- |
| FR-01 | Unit Test | `skills/workflow-runtime/tests/test_runtime_gate.py` | `workflow_runtime.py` | `self.assertEqual(session.status, "waiting_input")` |
| FR-04 | Unit Test | `skills/workflow-runtime/tests/test_runtime_gate.py` | `workflow_runtime.py` | `self.assertRaises(ForbiddenAISourceError)` khi source=ai |
| FR-02 | Unit Test | `skills/workflow-runtime/tests/test_runtime_gate.py` | `workflow_runtime.py` | `self.assertRaises(InvalidResumeTokenError)` khi token lệch |
| FR-06 | Integration Test | `skills/workflow-runtime/tests/test_runtime_gate.py` | `workflow_runtime.py` | `self.assertNotIn("pending_input", session)` sau khi resume thành công |

## 14. Requirement Traceability Matrix
- `FR-01` -> Task 1.1 -> Lớp `RuntimeInputGate` -> `workflow_runtime.py` -> `test_runtime_gate.py` -> Verified -> Released.
- `FR-04` -> Task 1.4 -> Bộ lọc `_validate_source` -> `workflow_runtime.py` -> `test_runtime_gate.py` -> Verified -> Released.

## 15. File-Level Implementation Contracts
- **File**: `skills/workflow-runtime/scripts/workflow_runtime.py`
  - **Purpose**: Đóng vai trò là nhân thực thi điều khiển luồng SDLC và quản lý session.
  - **Owner**: Coder.
  - **Inputs / Outputs**: Đầu vào là các tham số dòng lệnh CLI; đầu ra là session JSON được cập nhật.
  - **Risks**: Nguy cơ xung đột nếu sửa đổi hàm ghi ghi atomic gây mất đồng bộ dữ liệu. -> Cách giảm thiểu: Sử dụng khối try-finally và kiểm thử ghi tệp tin `.tmp` cẩn thận.
