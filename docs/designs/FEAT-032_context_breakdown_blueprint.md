<!-- File path: docs/designs/FEAT-032_context_breakdown_blueprint.md -->

---
feature_id: FEAT-032
feature_name: Phase 1 - Context Breakdown
status: reviewed
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-032_context_breakdown_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Phase 1 - Context Breakdown

## 0. Baseline Context & References
- **Memory Baseline**: Cấu trúc Split State trong dự án sử dụng các tệp JSON nhỏ lưu trữ các trạng thái độc lập (`context.json`, `usage.json`...) thay vì `.session.json` cồng kềnh.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/context.py`
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `extensions/visualizer/resources/webview.html`
  - `extensions/visualizer/src/extension.ts`

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/breakdown_engine.py` | `NEW` | Phân tích tệp log transcript và xuất ra `breakdown.json`. | `skills/workflow-runtime/scripts/context.py` | Low risk. Chạy độc lập để sinh dữ liệu trạng thái. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | `MODIFY` | Gọi cập nhật breakdown sau khi thay đổi trạng thái, thêm lệnh CLI. | `skills/workflow-runtime/scripts/breakdown_engine.py` | Low risk. Chỉ thêm gọi hàm và cờ command dòng lệnh. |
| `extensions/visualizer/src/extension.ts` | `MODIFY` | File Watcher giám sát `breakdown.json` và truyền `UPDATE_BREAKDOWN` sang webview. | `.agents/state/breakdown.json` | Low risk. Quá trình gửi nhận thông điệp qua postMessage. |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Thiết kế panel và giao diện Tree view, Progress bar và Highlight. | `extensions/visualizer/src/webviewHtml.ts` | Medium. Yêu cầu giao diện responsive, CSS mượt mà. |
| `skills/workflow-runtime/tests/test_breakdown.py` | `NEW` | Kiểm thử unit test tự động cho breakdown engine. | `skills/workflow-runtime/scripts/breakdown_engine.py` | Low. Chỉ phục vụ test tự động. |

## 2. Target Folder Structure
```text
.
├── .agents
│   ├── state
│   │   └── breakdown.json
├── docs
│   ├── brainstorming
│   │   └── FEAT-032_context_breakdown.md
│   ├── designs
│   │   └── FEAT-032_context_breakdown_blueprint.md
│   └── plans
│       └── FEAT-032_context_breakdown_plan.md
├── extensions
│   └── visualizer
│       ├── resources
│       │   └── webview.html
│       └── src
│           └── extension.ts
└── skills
    └── workflow-runtime
        ├── scripts
        │   ├── breakdown_engine.py
        │   └── workflow_runtime.py
        └── tests
            └── test_breakdown.py
```

## 3. Interface Contracts (Public & Internal)

### Public Interface Contracts
- **CLI Command Syntax**:
  `aiwf usage breakdown` (không có đối số, in ra bảng phân tách ở CLI).
- **Structured JSON Schema (`.agents/state/breakdown.json`)**:
  ```json
  {
    "conversation_id": "string",
    "timestamp": "string",
    "total_tokens": 15000,
    "breakdown": [
      {
        "category": "AI_RULES",
        "tokens": 1200,
        "percentage": 8.0,
        "loads": 1,
        "last_loaded": "string"
      },
      {
        "category": "Conversation History",
        "tokens": 4500,
        "percentage": 30.0,
        "loads": 1,
        "last_loaded": "string"
      }
    ]
  }
  ```

### ViewModel Schema & Extension Changes
- **ViewModel Schema**: Webview nhận `UPDATE_BREAKDOWN` chứa đối tượng dạng JSON schema ở trên.
- **File Watch Strategy**: `extension.ts` khởi chạy watcher giám sát tệp `.agents/state/breakdown.json`. Khi có sự kiện thay đổi, đọc tệp, chuyển đổi sang đối tượng và gửi postMessage với type `"UPDATE_BREAKDOWN"`.
- **Fallback Order**: Nếu không tồn tại `breakdown.json`, webview hiển thị thông báo trống (No breakdown data available).

## 4. Algorithms & Logic Specifications

### Algorithm Flow (breakdown_engine.py)
1. Đọc tệp transcript của `conversation_id` hiện tại tại:
   `~/.gemini/antigravity-ide/brain/{conversation_id}/.system_generated/logs/transcript.jsonl`
2. Tìm kiếm lượt prompt (`USER_INPUT`) cuối cùng hoặc khối context nạp cho `PLANNER_RESPONSE` cuối cùng.
3. Phân tách văn bản thô (raw prompt context) dựa trên biểu thức chính quy (Regex):
   - **AI_RULES**: Quét khối giới hạn bởi `<RULE[user_global]>` ... `</RULE[user_global]>` hoặc `AI_RULES.md`.
   - **AGENTS**: Quét khối `<RULE[AGENTS.md]>` ... `</RULE[AGENTS.md]>` hoặc `AGENTS.md`.
   - **Loaded Skills**: Các khối nạp chỉ dẫn `SKILL.md` (nhận dạng qua tên tệp tin hoặc tiêu đề tệp).
   - **RAG results**: Giới hạn bởi `<knowledge_items>` ... `</knowledge_items>`.
   - **Project Memory**: Giới hạn bởi `<memory_state>` ... `</memory_state>`.
   - **Workspace Reads**: Giới hạn bởi các khối đọc file dự án (ví dụ `view_file` tool call output).
   - **Conversation History**: Giới hạn bởi `<conversation_transcript>` ... `</conversation_transcript>`.
   - **Other**: Phần còn lại của văn bản đệm.
4. Ước lượng số lượng token bằng cách chia chiều dài ký tự của từng phân đoạn cho 3 (1 token = 3 ký tự).
5. Cộng dồn và tính tỷ lệ phần trăm:
   `percentage = (source_tokens / total_tokens) * 100`
   Nếu tổng các nguồn không đạt 100%, bổ sung phần sai số chênh lệch vào mục **Other**.

## 5. State Machine & Transitions
Không làm thay đổi hay giới thiệu trạng thái workflow mới. Chỉ bổ sung tệp Split State `breakdown.json` cập nhật song song với `usage.json`.

## 6. Validation and Safety Constraints
- Giới hạn quyền đọc tệp transcript chỉ trong thư mục của `conversation_id` hiện tại nằm dưới thư mục `.gemini/antigravity-ide/brain/`.
- Không sử dụng bất kỳ đường dẫn tuyệt đối nào khi push Git hay ghi tệp tin.

## 7. Backward Compatibility & Migration Mapping
Tệp `breakdown.json` là tệp trạng thái bổ sung mới, hoàn toàn không làm ảnh hưởng đến tính tương thích của các tệp trạng thái cũ (`context.json`, `usage.json`).

## 8. Implementation Checklist
- [ ] Viết tệp `skills/workflow-runtime/scripts/breakdown_engine.py` bóc tách log transcript.
- [ ] Liên kết gọi `update_breakdown` trong `workflow_runtime.py` và thêm lệnh CLI `usage breakdown`.
- [ ] Thêm file watcher cho `breakdown.json` và sự kiện `UPDATE_BREAKDOWN` trong `extension.ts`.
- [ ] Thiết kế Tree view, Progress bar và Highlighting lớn nhất trong `webview.html`.
- [ ] Viết automated tests `test_breakdown.py` kiểm chứng logic.

## 9. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-01` | Phân loại chính xác các nguồn context | Token phân bố chính xác | Chạy unit test tự động | `test_breakdown.py:test_context_classification` |
| `REQ-02` | Tổng phần trăm xấp xỉ 100% | Tổng phần trăm ~100% | Chạy unit test tự động | `test_breakdown.py:test_percentages_total_100` |
| `REQ-03` | CLI diagnostics hoạt động | In bảng biểu breakdown | Lệnh `aiwf usage breakdown` | Thủ công qua CLI |
| `REQ-04` | Visualizer Tree view hiển thị | Giao diện Tree view, Progress bar thể hiện % | Kiểm thử trực quan trên Webview | Trình duyệt và ảnh chụp màn hình |

## 10. Disallowed Outputs Validation
- [x] No `file://` or absolute paths used in workspace references.
- [x] No placeholders like `...` or `etc.` in code/structures.
- [x] No `TBD` or `To Be Determined` placeholders.
- [x] No unsafe permission values.
- [x] No unmapped legacy fields.
