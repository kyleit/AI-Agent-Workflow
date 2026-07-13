<!-- File path: docs/plans/FEAT-056_update_global_architecture_policy_plan.md -->

---
feature_id: FEAT-056
feature_name: Update Global Architecture Policy
status: reviewed
stage: planning
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: ../brainstorming/FEAT-056_update_global_architecture_policy.md
next_artifact: ../designs/FEAT-056_update_global_architecture_policy_blueprint.md
---

# FEAT-056: Update Global Architecture Policy

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Viết mục chính sách "Architecture & Code Organization Policy" trong `AI_RULES.md` | [x] |
| FR-02 | Phase 1 | Task 1.2 | Định nghĩa các quy tắc phân tầng dốc phụ thuộc DDD + Clean Architecture | [x] |
| FR-03 | Phase 1 | Task 1.3 | Thiết lập quy định lựa chọn công nghệ mặc định (Fiber, FastAPI, SvelteKit) | [x] |
| FR-04 | Phase 1 | Task 1.4 | Thiết lập bảng chỉ số giới hạn mềm kích thước dòng code (Soft line limits) | [x] |
| FR-05 | Phase 1 | Task 1.5 | Cập nhật tham chiếu chính sách trong các tệp `SKILL.md` của các Skill liên quan | [x] |
| FR-06 | Phase 2 | Task 2.1 | Cập nhật tài liệu dự án public: `README.md`, `USAGE.md`, `INSTALL.md`, `AGENTS.md` | [x] |
| - | Phase 2 | Task 2.2 | Cấu hình cho RAG và Memory bootstrap nhận biết phân tích kiến trúc dự án | [x] |

## 2. Task Ownership & Roles
Phân bổ người chịu trách nhiệm thực thi các tác vụ:
- **Task 1.1**: [Architect] - Thiết lập dự thảo chính sách kiến trúc trung tâm.
- **Task 1.2**: [Architect] - Phân lớp và định nghĩa hướng phụ thuộc.
- **Task 1.3**: [Architect] - Biên soạn bộ gợi ý ngôn ngữ/framework.
- **Task 1.4**: [Architect] - Thiết lập bảng soft limits số dòng code.
- **Task 1.5**: [Coder] - Cập nhật liên kết tham chiếu tại tất cả các file `SKILL.md` được chỉ định.
- **Task 2.1**: [Technical Writer] - Đồng bộ hóa tài liệu hướng dẫn công khai.
- **Task 2.2**: [Runtime Developer] - Cập nhật các Skill phân tích bộ nhớ.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.4 -> Task 1.5
- **Parallel Tasks**: [Task 1.3, Task 2.1]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.5)
- **Independent Tasks**: Task 2.1
- **Recommended Execution Groups**:
  - Group 1: Task 1.1, Task 1.2, Task 1.3, Task 1.4
  - Group 2: Task 1.5 (Parallel)
  - Group 3: Task 2.1, Task 2.2

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `AI_RULES.md` | Modify | Thêm mục chính sách "Architecture & Code Organization Policy" |
| Task 1.2 | `AI_RULES.md` | Modify | Đặc tả 4 lớp DDD và Clean Architecture |
| Task 1.3 | `AI_RULES.md` | Modify | Quy định gợi ý tech stack mặc định |
| Task 1.4 | `AI_RULES.md` | Modify | Ghi bảng Soft Line Limits cho tệp tin |
| Task 1.5 | `.agents/skills/*/SKILL.md` | Modify | Thêm dòng tham chiếu ngắn gọn đến Architecture Policy |
| Task 2.1 | `README.md`, `USAGE.md`, `INSTALL.md`, `AGENTS.md` | Modify | Cập nhật thông tin tiêu chuẩn kiến trúc dự án công khai |
| Task 2.2 | `.agents/skills/project-memory-bootstrap/SKILL.md` | Modify | Hướng dẫn ghi lại kiến trúc dự án khi bootstrap bộ nhớ |

## 5. Blueprint Preparation Inputs
Cung cấp định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Đặc tả danh sách cụ thể các tệp tin Skill cần cập nhật.
- **Provider Pattern details**: Không áp dụng.
- **Data Flow / Sequence Flow**: Không áp dụng.
- **Migration Strategy & Testing Architecture**: Hướng dẫn loại trừ các file tự động sinh và kiểm tra broken links.

## 6. Verification Strategy & Test Mapping
- **Unit Tests**: Kiểm tra tính toàn vẹn và không bị trùng lặp của văn bản chính sách (Mapped to Task 1.1).
- **Integration Tests**: Kiểm thử việc sinh Blueprint có tích hợp đánh giá rủi ro kích thước tệp tin (Mapped to Task 1.5).
- **Compatibility / Regression Tests**: Đảm bảo các Skill khác không bị hỏng cấu trúc Markdown (Mapped to Task 1.5).

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] Chính sách được chèn chính xác vào `AI_RULES.md` không có lỗi đánh dấu Markdown.
  - [ ] 100% các Skill chỉ định đã được bổ sung dòng tham chiếu.
- **Phase 2 Exit Criteria**:
  - [ ] Tài liệu README, USAGE, INSTALL, AGENTS đồng bộ nội dung kiến trúc mới.
  - [ ] Không có broken links.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Gặp lỗi cú pháp Markdown hoặc trùng lặp làm hỏng cấu trúc tệp chính sách.
  - Steps: Hoàn tác git commit trên `AI_RULES.md` và các tệp `SKILL.md`.
  - Recovery: Trả lại trạng thái tài liệu sạch ban đầu.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | No | No | No | Yes | Yes | No |
| Task 1.2 | Yes | No | No | No | Yes | Yes | No |
| Task 1.3 | Yes | No | No | No | Yes | Yes | No |
| Task 1.4 | Yes | No | No | No | Yes | Yes | No |
| Task 1.5 | Yes | No | No | No | Yes | Yes | No |
| Task 2.1 | Yes | No | No | No | Yes | No | No |
| Task 2.2 | Yes | No | No | No | Yes | Yes | No |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: docs/designs/FEAT-056_update_global_architecture_policy_blueprint.md
- **Phase 2 Artifacts**: docs/adr/ADR-056_architecture_standards.md

## 11. Token & Execution Optimization
- **Sequential execution cost**: Sửa đổi tài liệu lần lượt.
- **Expected token savings**: Giảm thiểu sự trùng lặp quy tắc trong từng Skill, tối ưu hóa kích thước ngữ cảnh hội thoại.

## Recommended Next Skill
/blueprint
