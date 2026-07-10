---
feature_id: FEAT-028
feature_name: Pure Split State Management
status: draft
stage: brainstorming
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: None
next_artifact: ../plans/FEAT-028_pure_split_state_management_plan.md
---

# Master Requirement Document – Pure Split State Management

## 1. Feature ID & Name
- **Feature ID**: FEAT-028
- **Feature Name**: Pure Split State Management (Loại bỏ hoàn toàn tệp `.session.json`)

## 2. Original Idea
mục tiêu sinh ra thư mục state này là để chỉnh sửa những file nhỏ, vậy tại sao phải dùng lại file .session.json này? tại sao không sửa lại toàn bộ từ skills (sửa các file nhỏ trong này thôi) đến extension đọc dữ liệu trong các file trong này thôi

## 3. Business Problem
- **Problem**: Hiện tại hệ thống đang sử dụng kiến trúc lai (hybrid). Trạng thái phiên làm việc vừa được lưu thành các tệp nhỏ trong thư mục `state/` (nhằm tối ưu hóa hiệu năng, giảm xung đột khi ghi đồng thời), nhưng đồng thời vẫn gộp lại thành một tệp lớn duy nhất `.agents/.session.json` mỗi khi có thay đổi. Điều này gây dư thừa dữ liệu trên đĩa, tốn tài nguyên I/O đĩa để gộp file và duy trì độ phức tạp không đáng có trong mã nguồn của cả Skills, CLI và Extension.
- **Why it matters**: Việc loại bỏ hoàn toàn `.session.json` và chuyển hẳn sang Pure Split State sẽ làm tăng tốc độ ghi trạng thái của các Skills, loại bỏ hoàn toàn nguy cơ tranh chấp khóa (lock contention) trên tệp `.session.json`, và giữ cho kiến trúc hệ thống sạch sẽ, nhất quán.
- **Who is affected**: Lập trình viên phát triển AI Skills, các Agents hoạt động đồng thời và Visualizer Extension.
- **Expected outcome**: Hệ thống hoạt động bình thường mà không cần có sự hiện diện của tệp `.agents/.session.json`. Mọi thông tin trạng thái đều được đọc/ghi trực tiếp từ `.agents/state/*.json` bởi cả Skills và Extension.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Visualizer Extension phải đọc trực tiếp các tệp nhỏ (`context.json`, `workflow.json`, `runtime.json`, `approvals.json`, `usage.json`, `agents.json`) từ thư mục `.agents/state/` và tự động gộp dữ liệu hiển thị trong bộ nhớ (In-memory aggregation).
  - FR-02: Toàn bộ các CLI commands và script nội bộ (ví dụ: `workflow_runtime.py`, `aiwf` wrapper) phải chuyển sang đọc/ghi trực tiếp trên các tệp trạng thái nhỏ mà không tìm kiếm hay ghi đè vào `.session.json`.
  - FR-03: Xóa bỏ hoàn toàn tệp tin `.session.json` và cơ chế gộp `aggregate_state` ghi xuống đĩa.
- **Non-functional Requirements**:
  - NFR-01: Hiệu năng ghi trạng thái của hệ thống tăng tối thiểu 20% do giảm kích thước tệp ghi xuống đĩa và không cần chạy hàm gộp file đĩa.
  - NFR-02: Giảm tỷ lệ lỗi ghi khóa tệp xuống 0% do các tiến trình song song ghi vào các tệp khác nhau (ví dụ: Agent ghi vào `runtime.json` không khóa luồng ghi `usage.json` của hệ thống thu thập thống kê).
- **Technical Constraints**:
  - TC-01: Phải đảm bảo không phá vỡ khả năng tự động đồng bộ hóa trạng thái giữa các dự án đăng ký trên CLI `aiwf`.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Có cần duy trì tệp `.session.json` như một bản sao lưu (backup) không? | Không cần thiết. Các tệp nhỏ trong `state/` đã chứa đầy đủ và an toàn hơn khi tách biệt. |
| Làm thế nào để xử lý các dự án cũ chưa chuyển đổi sang cấu trúc thư mục `state/`? | CLI và Extension sẽ tự động khởi tạo thư mục `state/` nếu nó chưa tồn tại (di trú tự động trong bước khởi tạo). |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: Trạng thái lai (hybrid) hiện có đã triển khai các hàm `aggregate_state` và `deconstruct_state` trong `state_sync.py`. Visualizer Extension cũng đã có hàm `aggregateStateFromFiles` trong `extension.ts` nhưng vẫn giữ logic fallback đọc từ `.session.json`.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| State Sync Helper | [.agents/skills/workflow-runtime/scripts/state_sync.py](file:///e:/AgentsProject/.agents/skills/workflow-runtime/scripts/state_sync.py) | Cần refactor để bỏ hàm ghi `aggregate_state` ra đĩa và cập nhật logic `deconstruct_state`. |
| VS Code Extension | [extensions/visualizer/src/extension.ts](file:///e:/AgentsProject/extensions/visualizer/src/extension.ts) | Thay đổi đường dẫn theo dõi (file watcher) từ `.session.json` sang toàn bộ thư mục `state/` và loại bỏ fallback. |

## 9. Solution Options Evaluated

### Option A: Giữ nguyên cơ chế lai hiện tại (Hybrid)
- **Overview**: Tiếp tục duy trì cả thư mục `state/` và tệp `.session.json`.
- **Advantages**: Cực kỳ an sau, không có rủi ro phá vỡ tương thích.
- **Disadvantages**: Dư thừa tài nguyên đĩa, I/O đĩa kém tối ưu.
- **Complexity**: Low
- **Risk**: Low

### Option B: Pure Split State (Bỏ hẳn `.session.json`)
- **Overview**: Xóa bỏ hoàn toàn tệp `.session.json` trên đĩa. Toàn bộ các công cụ và extension chỉ hoạt động với các file nhỏ trong `state/`.
- **Advantages**: Sạch sẽ, hiệu năng tối ưu nhất, loại bỏ hoàn toàn lỗi xung đột ghi tệp lớn.
- **Disadvantages**: Cần chỉnh sửa diện rộng ở cả phần Skills và phần Extension.
- **Complexity**: Medium
- **Risk**: Medium

## 10. Solution Comparison Table
| Criteria | Option A | Option B |
|---|---|---|
| Complexity | Low | Medium |
| Risk | Low | Medium |
| Performance | Medium | High |
| Maintainability | Low | High |
| Compatibility | High | Medium |
| Future Scalability | Medium | High |
| Development Cost | None | Medium |

## 11. Selected Solution
- **Choice**: Option B — Pure Split State
- **Why Selected**: Đây là giải pháp triệt để nhất để tối ưu hiệu năng I/O đĩa, giải quyết tận gốc các vấn đề xung đột ghi đĩa từ các agents song song và giúp hệ thống có kiến trúc nhất quán, hiện đại.
- **Trade-offs Accepted**: Chấp nhận chi phí lập trình để refactor đồng bộ giữa Skills (Python) và Extension (Typescript).
- **Technical Debt**: Loại bỏ được nợ kỹ thuật (technical debt) của tệp cấu hình cồng kềnh lai cũ.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Có thể có script tiện ích bên ngoài chưa cập nhật đọc từ `state/` dẫn đến không lấy được trạng thái. -> *Mitigation*: Cung cấp một lệnh CLI `aiwf state status` hoặc xuất ra JSON khi cần thiết để hỗ trợ các script ngoài.

## 13. Acceptance Criteria
- [ ] Xóa bỏ hoàn toàn tệp `.agents/.session.json` khỏi dự án.
- [ ] Mọi hoạt động cập nhật trạng thái của Skills chỉ ghi đè lên các tệp JSON nhỏ trong `.agents/state/`.
- [ ] Visualizer Extension hoạt động ổn định, cập nhật trực tiếp dữ liệu hiển thị khi các file nhỏ trong thư mục `state/` thay đổi.

---

## 14. Final Planning Prompt

### Purpose
Lời gọi thiết kế chi tiết tiếp theo cho Skill `brainstorming-to-plan`.

### Objectives & Selected Solution
Thực hiện cấu trúc Pure Split State hoàn toàn, loại bỏ tệp `.session.json` trên đĩa.

### Functional Requirements
- Refactor tệp `state_sync.py` và `session.py` để không ghi tệp `.session.json`.
- Cập nhật Visualizer Extension (`extension.ts` và `webview.html` nếu cần) để theo dõi và tải trực tiếp dữ liệu gộp từ `.agents/state/`.
- Đồng bộ hóa các lệnh CLI của `workflow_runtime.py` với cấu trúc mới.

### Verification Checklist
- [ ] docs/plans/FEAT-028_pure_split_state_management_plan.md được phê duyệt.
