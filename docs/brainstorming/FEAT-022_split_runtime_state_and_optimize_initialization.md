<!-- docs/brainstorming/FEAT-022_split_runtime_state_and_optimize_initialization.md -->

---
feature_id: FEAT-022
feature_name: Split Runtime State, Optimize Initialize Workflow, and Update Extension
status: draft
stage: brainstorming
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: None
next_artifact: ../plans/FEAT-022_split_runtime_state_and_optimize_initialization_plan.md
---

# Master Requirement Document – Split Runtime State, Optimize Initialize Workflow, and Update Extension

## 1. Feature ID & Name
- **Feature ID**: FEAT-022
- **Feature Name**: Split Runtime State, Optimize Initialize Workflow, and Update Extension

## 2. Original Idea
```text
# AI Engineering Refactoring Task
## Split Runtime State, Optimize Initialize Workflow, and Update Extension

Refactor the framework so that initialization, runtime state, workflow state, approvals, usage, and extension integration are cleanly separated.
The current design stores too much information inside .agents/.session.json.
(Chi tiết như yêu cầu trong USER_REQUEST của Ba)
```

## 3. Business Problem
- **Problem**: File `.agents/.session.json` đang gánh vác quá nhiều thông tin hỗn hợp. Việc này dẫn đến tần suất ghi đè cao (~vài giây một lần khi chạy step), nguy cơ mất/lỗi context cao khi crash, tốc độ khởi động chậm do quét lại môi trường liên tục, và gây lag giao diện Extension do phải parse lại tệp JSON monolit và vẽ lại toàn bộ UI liên tục.
- **Why it matters**: Giảm tuổi thọ thiết bị lưu trữ khi ghi đè liên tục, làm giảm trải nghiệm của nhà phát triển khi Visualizer bị lag/nhấp nháy, và tiêu tốn tài nguyên xử lý không đáng có cho các tác vụ khởi động trùng lặp.
- **Who is affected**: AI Coding Agents chạy workflow và Nhà phát triển sử dụng Visualizer Dashboard Extension.
- **Expected outcome**: 
  - Khởi động nhanh (từ vài giây xuống vài mili-giây).
  - Visualizer UI mượt mà, live update cục bộ không lag/nhấp nháy.
  - Tách biệt rõ ràng các file trạng thái chuyên biệt.
  - Khả năng phục hồi dữ liệu khi bị hỏng.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Tách trạng thái thành 8 file JSON riêng biệt trong `.agents/state/` (`context.json`, `workflow.json`, `runtime.json`, `approvals.json`, `usage.json`, `agents.json`, `rules.json`, `recovery.json`).
  - FR-02: Triển khai Lớp tương thích hai chiều (Bi-directional Sync) giữa các file con và `.agents/.session.json`.
  - FR-03: Triển khai Project Fingerprint và lưu cache vào `context.json` để bỏ qua các bước quét đắt đỏ ở `initialize-workflow`.
  - FR-04: Cập nhật Extension để watch thư mục `.agents/state/` và ghép ViewModel động cho Live Update từng phần UI.
  - FR-05: Bổ sung 5 lệnh CLI mới cho `workflow_runtime.py`.
  - FR-06: Viết bộ test case bao phủ toàn bộ các kịch bản state-splitting, initialization optimization, và recovery.
- **Non-functional Requirements**:
  - NFR-01: Tốc độ khởi động (`initialize-workflow`) khi đã có cache phải dưới 50ms.
  - NFR-02: Việc cập nhật file trạng thái con phải thực hiện nguyên tử (write to tmp and rename) để chống tranh chấp ghi.
  - NFR-03: Giao diện Visualizer không được redraw lại toàn bộ khi chỉ có file `runtime.json` thay đổi.
- **Technical Constraints**:
  - TC-01: Duy trì khả năng tương thích ngược hoàn toàn với các agent hoặc extension đời cũ thông qua `.session.json`.
  - TC-02: Hoạt động đa nền tảng (macOS, Linux, Windows).

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Làm thế nào để giải quyết tranh chấp ghi (Concurrent Write) khi nhiều Agent chạy song song? | Sử dụng cơ chế File Locking hiện có (`.agents/runtime/file-locks.json`) thông qua `SessionLock` trong `workflow_runtime.py` trước khi thực hiện ghi bất kỳ file trạng thái nào. |
| Project Fingerprint sẽ được tính như thế nào? | Tính hash SHA-256 dựa trên: Đường dẫn tuyệt đối của thư mục gốc, URL Git remote, Hash của file `MANIFEST.json` và tệp cấu hình gói (`package.json`, `pyproject.toml`, v.v.). |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready (≥ 85)

## 7. Existing Project Context
- **Memory Source**: Đọc từ `.agents/memory/project-summary.md` và các rules trong `AI_RULES.md`.
- **Existing Architecture Summary**: Hệ thống hiện tại sử dụng một CLI duy nhất `workflow_runtime.py` và lưu trữ trạng thái tại `.agents/.session.json`. VS Code Extension đọc trực tiếp file này qua cơ chế Watch file.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| CLI Runtime Engine | `skills/workflow-runtime/scripts/workflow_runtime.py` | Nơi lưu trữ logic đọc/ghi session và các subcommands hiện tại. |
| Visualizer Extension | `extensions/visualizer/` | Tiện ích mở rộng VS Code cần cập nhật cơ chế đọc/ghép file trạng thái và cơ chế watch mới. |
| Central Rules | `AI_RULES.md` | Tài liệu quy tắc trung tâm cần cập nhật đặc tả kiến trúc mới. |

## 9. Solution Options Evaluated

### Option A: CLI-Managed Rebuild with Dual-Layer Extension (Selected)
- **Overview**: CLI quản lý việc chia nhỏ file trạng thái sang thư mục `.agents/state/`. Đồng thời duy trì `.agents/.session.json` tổng hợp thông qua cơ chế ghi đè nguyên tử. Extension watch thư mục `state/` để cập nhật UI cục bộ, đồng thời giữ fallback đọc `.session.json`.
- **Advantages**: 
  - Đảm bảo tương thích ngược 100%.
  - Tối ưu hóa UI update cục bộ, mượt mà.
  - Phục hồi dữ liệu thông minh khi bị lỗi.
- **Disadvantages**: Tốn thêm một lượng nhỏ tài nguyên CPU để tổng hợp tệp tương thích ngược `.session.json`.
- **Complexity**: Medium
- **Risk**: Low
- **Performance**: High (Live Update mượt mà)
- **Maintainability**: High
- **Compatibility**: High
- **Future Scalability**: High

### Option B: Pure Decentralized State Engine
- **Overview**: Bỏ hoàn toàn `.session.json`, chỉ dùng các file trạng thái con.
- **Advantages**: Đơn giản, không cần lớp tương thích.
- **Disadvantages**: Gây lỗi tương thích ngược nghiêm trọng cho các agent và extension phiên bản cũ.
- **Complexity**: Low
- **Risk**: High
- **Performance**: High
- **Maintainability**: Medium
- **Compatibility**: Low
- **Future Scalability**: Medium

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Medium | Low |
| Risk | Low | High |
| Performance | High | High |
| Maintainability | High | Medium |
| Compatibility | High | Low |
| Future Scalability | High | Medium |
| Development Cost | Medium | Low |

## 11. Selected Solution
- **Choice**: Option A — CLI-Managed Rebuild with Dual-Layer Extension
- **Why Selected**: Đảm bảo tính tương thích ngược hoàn toàn, bảo vệ dữ liệu tối đa và mang lại hiệu năng Live Update mượt mà không nhấp nháy cho visualizer UI.
- **Trade-offs Accepted**: Tốn thêm một chút overhead nhỏ cho việc tổng hợp file `.session.json` sau mỗi lần ghi file con, nhưng hoàn toàn xứng đáng vì đảm bảo an toàn hệ thống.
- **Technical Debt**: Không có.
- **Risk Mitigation**: Sử dụng File Lock để chống tranh chấp ghi đồng thời và cơ chế ghi đè nguyên tử.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Lệch pha dữ liệu khi ghi đè bị gián đoạn -> Giải quyết: Sử dụng cơ chế ghi nguyên tử `.tmp` rồi rename, nếu rename thất bại thì roll back hoặc khôi phục từ tệp backup.
- **Assumptions**:
  - A-01: Máy chạy hỗ trợ tốt các thao tác đổi tên file nguyên tử (POSIX `rename` trên macOS/Linux và Windows API tương đương).

## 13. Acceptance Criteria
- [ ] Thư mục `.agents/state/` được tự động tạo và chứa đủ 8 file JSON sau khi khởi chạy.
- [ ] Xóa file `.session.json` và chạy một lệnh CLI bất kỳ sẽ tự động phục hồi lại `.session.json` từ các file con mà không làm mất context (như `conversation_id`).
- [ ] Chạy `initialize-workflow` lần 2 mất dưới 50ms khi fingerprint không đổi.
- [ ] Visualizer Dashboard cập nhật trạng thái log mới mà không redraw lại phần project metadata.
- [ ] Chạy được 5 lệnh CLI mới mà không gặp lỗi cú pháp.

---

## 14. Final Planning Prompt

### Purpose
Complete, self-contained prompt for the `brainstorming-to-plan` Skill.

### Problem Statement
Tái cấu trúc cơ chế lưu trữ trạng thái của AI Workflow Framework để giải quyết các vấn đề hiệu năng của tệp `.session.json` monolithic (tải lượng ghi đĩa cao, rủi ro mất context, khởi động chậm, và visualizer lag).

### Objectives & Selected Solution
Triển khai Option A: Chia tách trạng thái thành 8 file chuyên biệt trong `.agents/state/`, xây dựng lớp đồng bộ tương thích ngược hai chiều với `.session.json`, tối ưu hóa khởi chạy bằng cache Project Fingerprint, và cập nhật Extension để watch và update UI cục bộ theo từng file trạng thái.

### Functional Requirements
- Tách trạng thái thành 8 file JSON trong `.agents/state/` ghi đè nguyên tử.
- Xây dựng logic đồng bộ hai chiều (Aggregate & Deconstruct).
- Tối ưu hóa quét môi trường bằng cache `context.json` và fingerprint.
- Cập nhật Extension sử dụng ViewModel động và Watch thư mục `state/` để cập nhật UI cục bộ.
- Thêm 5 lệnh CLI mới.
- Viết 11 kịch bản unit tests bao phủ.
- Cập nhật 5 file tài liệu hướng dẫn.

### Architectural Details
- Cấu trúc thư mục mới: `.agents/state/`
- Cơ chế ghi: Atomic write (`write_to_file` tmp -> rename).
- CLI Routing: Thêm subcommands: `context`, `rules status`, `state status`, `state recover`, `state validate`.

### Verification Checklist
- [ ] docs/plans/FEAT-022_split_runtime_state_and_optimize_initialization_plan.md generated and approved
- [ ] docs/designs/FEAT-022_split_runtime_state_and_optimize_initialization_blueprint.md generated and approved
- [ ] All Acceptance Criteria mapped to implementation tasks
