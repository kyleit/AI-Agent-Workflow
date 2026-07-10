<!-- docs/brainstorming/FEAT-025_project_workflow_templates.md -->

---
feature_id: FEAT-025
feature_name: Project-specific Workflow Templates & Release Configuration
status: draft
stage: brainstorming
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: None
next_artifact: ../plans/FEAT-025_project_workflow_templates_plan.md
---

# Master Requirement Document – Project-specific Workflow Templates & Release Configuration

## 1. Feature ID & Name
- **Feature ID**: FEAT-025
- **Feature Name**: Project-specific Workflow Templates & Release Configuration

## 2. Original Idea
Mỗi project có một cách release khác nhau.
Ví dụ cho project này:
- Project này release là push lên gitlab
- Sau đó make publish-github để push lên github
- Nếu có sửa extension thì phải bump version cho extension, viết changelog và make package
Ví dụ 1 project khác:
- Họ không checkout từ master để làm việc mà checkout từ branch dev
- Sau đó release thì merge vào master để release, và merge vào 1 số branch khác cho service khác (dùng chung code) sau đó mới rebase lại master lại cho branch dev rồi mới push lên

Có cách nào để tôi init template cho từng project không?
Template bao gồm: làm việc thì checkout từ branch nào, cơ chế release ra sao.

## 3. Business Problem
- **Problem**: Quy trình SDLC (Git Flow, branching, release pipelines) đang được fix cứng trong mã nguồn CLI hoặc các Skills. Điều này cản trở khả năng làm việc của Agent trên các dự án có cấu trúc nhánh khác nhau (ví dụ: dev/master flow thay vì feature/main flow) hoặc cơ chế phát hành phức tạp (push đa remotes, chạy build/pack custom, v.v.).
- **Why it matters**: Nếu không có cơ chế cấu hình linh hoạt, AI Agent sẽ chạy sai quy trình Git của dự án dẫn đến xung đột code, hoặc không thực hiện đúng các bước đóng gói thủ tục của dự án (như make publish, npm publish), đòi hỏi sự can thiệp thủ công từ lập trình viên.
- **Who is affected**: Lập trình viên và AI Agent làm việc trên nhiều dự án khác nhau.
- **Expected outcome**: Cho phép khai báo cấu hình quy trình SDLC và Release dạng cấu trúc mẫu (Template) tại mỗi dự án. AI Agent sẽ tự động đọc cấu hình này để thực thi chính xác các bước checkout branch, rebase, merge và chạy pipeline release của dự án đó.

## 4. Requirement Discovery
- **Functional Requirements**:
  - **FR-01 (Workflow Template Config)**: Cho phép tạo tệp cấu hình `.agents/workflow.config.json` (hoặc mở rộng `release.config.json`) định nghĩa:
    * `git_flow`: Nhánh phát triển gốc (`development_branch`), nhánh phát hành chính (`release_branch`), cấu trúc tiền tố nhánh tính năng (`feature_prefix`), phương thức đồng bộ (`merge` hoặc `rebase`).
    * `release_steps`: Mảng các hành động cần thực thi tuần tự trong pha release.
    * `release_commands`: Các lệnh shell/Makefile tùy chỉnh cần chạy cho từng sự kiện.
  - **FR-02 (CLI Integration)**: Nâng cấp lớp `session.py` và `workflow_runtime.py` để đọc và áp dụng các thông số từ tệp cấu hình dự án.
  - **FR-03 (Dynamic Git Branch Dispatcher)**: Tự động checkout nhánh tính năng từ nhánh `development_branch` đã khai báo thay vì mặc định là `main`/`master`.
- **Non-functional Requirements**:
  - **NFR-01 (Fallback Defaults)**: Khi dự án không khai báo cấu hình tùy chỉnh, hệ thống tự động sử dụng quy trình mặc định hiện tại để đảm bảo tương thích ngược 100%.
  - **NFR-02 (Dry-run Mode)**: Hỗ trợ hiển thị danh sách các lệnh Git/Shell sẽ chạy trước khi thực hiện để lập trình viên xác nhận.
- **Technical Constraints**:
  - **TC-01**: Các câu lệnh tùy chỉnh (custom commands) chỉ được chạy sau khi có sự phê duyệt rõ ràng từ người dùng thông qua Choice Protocol (để tránh rủi ro bảo mật chạy code lạ).

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Có cần hỗ trợ các nhánh phát hành phụ (cho các service dùng chung code) không? | Có, cấu hình cho phép khai báo mảng `extra_push_branches` để push đồng thời sang các nhánh khác khi release. |
| Nếu việc tự động merge/rebase bị xung đột (conflict) thì xử lý thế nào? | CLI sẽ dừng lại ngay lập tức tại bước bị lỗi, khôi phục trạng thái an toàn (stash) và yêu cầu người dùng giải quyết xung đột thủ công. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready (>= 85)

## 7. Existing Project Context
- **Memory Source**: `.agents/memory/project-summary.md`
- **Existing Architecture Summary**: Hệ thống hiện đã có `release.config.json` để phân loại dự án đơn lẻ hoặc đa module (`multi-module`) và kiểm tra nhánh mặc định, nhưng chưa hỗ trợ cấu hình Git Flow chi tiết và các Custom Release Commands.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Workflow Runtime | `skills/workflow-runtime/` | CLI quản lý vòng đời và checkpoint. Cần được cập nhật để đọc tệp cấu hình mới. |
| Release Manager | `skills/workflow-runtime/scripts/release_manager.py` | Lớp thực thi lệnh Release. Cần chuyển đổi từ chạy mock sang chạy kịch bản thực tế dựa theo template. |

## 9. Solution Options Evaluated

### Option A: Cấu hình Declarative trong `workflow.config.json`
- **Overview**: Khai báo cấu trúc Git và các câu lệnh custom thuần túy bằng tệp JSON.
- **Architecture**: Sử dụng tệp JSON tĩnh để chỉ định các tham số.
- **Advantages**: Cực kỳ dễ đọc, chuẩn hóa cao.
- **Disadvantages**: Kém linh hoạt nếu dự án có các tác vụ rẽ nhánh logic phức tạp.

### Option B: Khai báo kịch bản bằng Bash Hooks (`.agents/hooks/`)
- **Overview**: Sử dụng các file script shell để xử lý các bước Git/Release.
- **Architecture**: AI sẽ thực thi các tệp `.sh` tương ứng tại mỗi Checkpoint.
- **Advantages**: Khả năng tùy biến vô hạn.
- **Disadvantages**: Khó kiểm soát an toàn bảo mật, khó viết script cho nhiều nền tảng OS khác nhau.

### Option C: Thiết kế Hybrid (Declarative Config với Command Hooks)
- **Overview**: Cấu hình các thông số nhánh bằng JSON, đồng thời cho phép khai báo các chuỗi câu lệnh tùy chỉnh (như `make publish-github` hoặc `npm run build`) dưới dạng mảng commands chạy ở các pha pre/post-release.
- **Architecture**: Tích hợp các câu lệnh shell được cấu hình sẵn vào luồng thực thi của Python CLI.
- **Advantages**: Đạt được cả sự đơn giản, an toàn và độ linh hoạt cao.
- **Disadvantages**: Đòi hỏi thiết kế parser an toàn trong CLI.

## 10. Solution Comparison Table
| Criteria | Option A | Option B | Option C (Recommended) |
|---|---|---|---|
| Complexity | Low | Medium | Medium |
| Risk | Low | Medium | Low |
| Performance | High | High | High |
| Maintainability | High | Medium | High |
| Compatibility | High | High | High |
| Future Scalability | Medium | High | High |
| Development Cost | Low | Medium | Medium |

## 11. Selected Solution
- **Choice**: Option C — Hybrid Solution
- **Why Selected**: Cung cấp cấu hình JSON dễ hiểu cho branching strategy (nhánh dev, master), đồng thời hỗ trợ mảng `custom_commands` để chạy các tác vụ biên dịch hoặc đẩy mã nguồn bổ sung mà không ảnh hưởng tới an toàn của hệ thống.
- **Trade-offs Accepted**: Việc thực thi các lệnh shell do người dùng khai báo trong JSON đòi hỏi phải hiển thị tường minh qua cổng duyệt phê duyệt (Approval Gate) để tránh rủi ro chạy mã độc hại nếu tệp config bị sửa đổi ngoài ý muốn.
- **Technical Debt**: None.
- **Risk Mitigation**: Áp dụng Choice Protocol bắt buộc trước khi thực thi bất kỳ `custom_command` nào được đọc từ file config.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Lập trình viên vô tình khai báo lệnh xóa file hoặc lệnh phá hỏng Git. → *Mitigation*: Luôn hiển thị câu lệnh đầy đủ trên CLI và yêu cầu xác nhận duyệt rõ ràng.
- **Assumptions**:
  - A-01: Dự án đã cấu hình sẵn các lệnh Makefile hoặc NPM tương ứng trước khi khai báo vào JSON.

## 13. Acceptance Criteria
- [ ] Cho phép định nghĩa nhánh phát triển chính (`development_branch`) và nhánh phát hành (`release_branch`) tùy chỉnh.
- [ ] Cho phép khai báo danh sách lệnh release tùy biến (ví dụ: `make publish-github`).
- [ ] Agent tự động checkout đúng nhánh đích tùy chỉnh khi bắt đầu công việc.
- [ ] Agent tự động thực thi các lệnh release tùy chỉnh và merge/rebase đúng theo quy trình đã khai báo khi chạy `/release`.

---

## 14. Final Planning Prompt

### Purpose
Tài liệu này đóng vai trò là prompt hoàn chỉnh để chuyển tiếp cho bước lập Kế hoạch thực thi (`brainstorming-to-plan`).

### Problem Statement
Xây dựng giải pháp cấu hình quy trình SDLC và Release tùy biến cho từng dự án bằng cách sử dụng cấu hình Hybrid (JSON + Command Hooks). Cập nhật CLI để nạp và thực thi chính xác quy trình đã khai báo.

### Verification Checklist
- [ ] docs/plans/FEAT-025_project_workflow_templates_plan.md được sinh ra và phê duyệt.
- [ ] docs/designs/FEAT-025_project_workflow_templates_blueprint.md được phê duyệt.
- [ ] Các kịch bản Git merge/rebase chạy đúng theo cấu hình dự án.
