<!-- File path: docs/plans/FEAT-065_vir_design_authority_plan.md -->

---
feature_id: FEAT-065
feature_name: Visual Intelligence Runtime — Design Authority & Design Knowledge Base
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-065_vir_design_authority_and_design_knowledge_base.md
next_artifact: ../designs/FEAT-065_vir_design_authority_blueprint.md
---

# FEAT-065: Visual Intelligence Runtime — Design Authority & Design Knowledge Base

## 1. Requirement Coverage Matrix

| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Model and define YAML schemas for Design Knowledge Base rules | [x] |
| FR-02 | Phase 1 | Task 1.2 | Implement search query filters by component and design categories | [x] |
| FR-04 | Phase 1 | Task 1.3 | Map design token variables (spacing, typography, hex colors) | [x] |
| FR-06 | Phase 1 | Task 1.4 | Expose REST-like Python helper class for internal DB lookups | [x] |
| FR-07 | Phase 1 | Task 1.5 | Audit codebase verifying zero hardcoded px or hex values in agents | [x] |
| FR-09 | Phase 1 | Task 1.6 | Register Design Authority Agent contract and veto domains | [x] |
| FR-11 | Phase 1 | Task 1.7 | Bind VLM output reports as inputs for agent evaluations | [x] |
| FR-12 | Phase 1 | Task 1.8 | Define structural `DesignFinding` Evidence subtype model fields | [x] |
| FR-13 | Phase 1 | Task 1.9 | Enforce VETO outputs on MUST token/WCAG rules failure | [x] |
| FR-14 | Phase 1 | Task 1.10| Enforce advisory-only WARN markings on SHOULD violations | [x] |
| FR-03 | Phase 2 | Task 2.1 | Implement design system pinning version selectors | [x] |
| FR-05 | Phase 2 | Task 2.2 | Build Pattern Library positive/negative ref screenshot catalogs | [x] |
| FR-08 | Phase 2 | Task 2.3 | Support project-level overrides YAML rule extension loaders | [x] |
| FR-10 | Phase 2 | Task 2.4 | Parse Layer 4 semantic observations comparing with Design KB rules | [x] |
| FR-15 | Phase 2 | Task 2.5 | Implement proposal workflow updates targeting `frontend-design` | [x] |

---

## 2. Task Ownership & Roles

Phân bổ người chịu trách nhiệm thực thi các tác vụ (Architect, Coder, Reviewer, Verifier, Documentation, Runtime):
- **Task 1.1**: [Architect] - Thiết kế lược đồ cấu trúc YAML cho cơ sở tri thức Thiết kế.
- **Task 1.2**: [Coder] - Viết trình phân tích và lọc dữ liệu cơ sở tri thức.
- **Task 1.3**: [Coder] - Cài đặt cấu trúc định dạng lưu trữ design tokens.
- **Task 1.4**: [Coder] - Triển khai thư viện Python API hỗ trợ tra cứu quy tắc thiết kế.
- **Task 1.5**: [Verifier] - Quét mã nguồn ngăn chặn các giá trị màu sắc/pixel viết cứng (hardcode) trong logic agent.
- **Task 1.6**: [Architect] - Định cấu hình đăng ký hợp đồng Agent có domain=`design`.
- **Task 1.7**: [Coder] - Định luồng tiếp nhận tin VLM để làm dữ liệu thô phục vụ kiểm tra chéo.
- **Task 1.8**: [Architect] - Thiết kế cấu trúc lớp `DesignFinding` kế thừa từ `Evidence`.
- **Task 1.9**: [Verifier] - Triển khai logic phát hành quyết định VETO nếu vi phạm quy tắc MUST.
- **Task 1.10**: [Verifier] - Đảm bảo các lỗi thuộc mức SHOULD chỉ phát sinh cảnh báo, không chặn quy trình PASS.
- **Task 2.1**: [Coder] - Tích hợp phân nhánh thư mục lưu trữ tri thức theo phiên bản hệ thống thiết kế (Design System versions).
- **Task 2.2**: [Documentation] - Xây dựng bộ sưu tập ảnh anti-pattern làm cơ sở dữ liệu mẫu.
- **Task 2.3**: [Coder] - Viết trình nạp chồng (override) tệp tin `custom-rules.yaml` cục bộ của dự án.
- **Task 2.4**: [Coder] - So khớp kết quả VLM với các token giới hạn của Design KB.
- **Task 2.5**: [Coder] - Viết trình đề xuất cập nhật tự động cho skill `frontend-design` kèm phê duyệt từ người dùng.

---

## 3. Parallel Execution Plan

- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.4 -> Task 1.6 -> Task 1.9
- **Parallel Tasks**: [Task 1.3, Task 1.5], [Task 1.7, Task 1.8, Task 1.10], [Task 2.1, Task 2.3], [Task 2.2, Task 2.5]
- **Blocking Tasks**: Task 1.1 (blocks Task 1.3), Task 1.4 (blocks Task 1.6), Task 2.3 (blocks Task 2.4)
- **Independent Tasks**: Task 1.5, Task 2.2
- **Recommended Execution Groups**:
  - **Group 1**: Task 1.1, Task 1.2, Task 1.3, Task 1.4 (Design Knowledge Base database and lookups)
  - **Group 2**: Task 1.6, Task 1.7, Task 1.8, Task 1.9, Task 1.10 (Design Authority Agent logic and VETOs)
  - **Group 3**: Task 1.5, Task 2.3 (Overriding rules loading & source checker checks)
  - **Group 4**: Task 2.1, Task 2.2, Task 2.4, Task 2.5 (Advanced pattern matches & dynamic enhancements)

---

## 4. File Change Plan (Implementation Boundary)

| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `.agents/visual-runtime/design-kb/rules.yaml` | Create | Lưu giữ các quy tắc thiết kế cơ bản |
| Task 1.3 | `.agents/visual-runtime/design-kb/tokens.json` | Create | Lưu giữ bảng Design Tokens mẫu |
| Task 1.4 | `vir_runtime/design/kb.py` | Create | Lớp API tra cứu tri thức thiết kế |
| Task 1.6 | `vir_runtime/design/agent.py` | Create | Cài đặt Design Authority Agent |
| Task 1.8 | `vir_runtime/domain/design_finding.py` | Create | Mô tả cấu trúc DesignFinding |
| Task 1.9 | `vir_runtime/design/veto.py` | Create | Trình xử lý phủ quyết VETO và phân loại mức lỗi |
| Task 2.3 | `vir_runtime/design/overrides.py` | Create | Trình nạp chồng luật bổ sung của dự án |

---

## 5. Blueprint Preparation Inputs

Định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Chi tiết cấu trúc API của `DesignKnowledgeBase` và `DesignAuthorityAgent`.
- **Provider Pattern details**: Giao thức nạp các token từ định dạng Figma JSON hoặc Tailwind config thông qua Token Converter.
- **Data Flow / Sequence Flow**: Vẽ luồng khi nhận kết quả VLM -> truy vấn danh sách token từ Design KB -> so khớp contrast và spacing -> nếu vi phạm MUST rule -> phát lệnh VETO gửi Consensus Engine.
- **Migration Strategy & Testing Architecture**: Sử dụng các file YAML rules giả định để chạy test unit kiểm tra độ nhạy của bộ lọc VETO.

---

## 6. Verification Strategy & Test Mapping

- **Unit Tests**:
  - `tests/unit/test_kb_queries.py` (Mapped to Task 1.4): Xác thực đọc đúng các quy tắc typography và palette từ tệp tin YAML.
  - `tests/unit/test_design_veto.py` (Mapped to Task 1.9): Inject lỗi màu sắc tương phản kém (vi phạm WCAG MUST); đảm bảo agent phát ra VETO thành công.
  - `tests/unit/test_design_advisory.py` (Mapped to Task 1.10): Inject lỗi vi phạm rule SHOULD; đảm bảo hệ thống chỉ sinh cảnh báo DesignFinding và trả về PASS.
- **Integration Tests**:
  - `tests/integration/test_token_validation.py` (Mapped to Task 2.4): Thử nghiệm so sánh layout render thực tế (qua DOM computed style) với Design Tokens, đảm bảo bắt đúng sai lệch padding.

---

## 7. Exit Criteria

- **Phase 1 Exit Criteria**:
  - [ ] 100% các cuộc truy vấn quy tắc từ KB hoàn thành trong < 50ms.
  - [ ] VETO phát ra chính xác khi gặp lỗi MUST, chặn đứng quyết định xuất bản chất lượng.
  - [ ] Không có mã màu hex hoặc pixel viết cứng nào tồn tại trong logic của các quan sát viên.
- **Phase 2 Exit Criteria**:
  - [ ] Hỗ trợ nạp chồng quy tắc của riêng dự án thành công mà không gây xung đột luật lõi.

---

## 8. Rollback Strategy

- **Phase 1 Rollback**:
  - *Trigger*: Quy tắc VETO quá nghiêm khắc gây chặn nhầm (false-positive) hàng loạt các thay đổi giao diện hợp lệ.
  - *Steps*: Thay đổi phân loại quy tắc MUST thành SHOULD tạm thời trong rules.yaml, khôi phục trạng thái an toàn.
  - *Recovery*: Đảm bảo CI/CD tiếp tục hoạt động trong khi điều chỉnh lại thông số thiết kế.

---

## 9. Change Impact Matrix

| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | No | No | No | Yes | Yes | No |
| Task 1.4 | Yes | Yes | Yes | Yes | No | No | No |
| Task 1.6 | Yes | Yes | Yes | No | No | Yes | No |
| Task 1.9 | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Task 2.3 | Yes | Yes | Yes | No | No | No | No |

---

## 10. Artifact Production Plan

- **Phase 1 Artifacts**: docs/designs/FEAT-065_vir_design_authority_blueprint.md
- **Phase 2 Artifacts**: .agents/visual-runtime/design-kb/rules.yaml
- **Phase 3 Artifacts**: docs/adr/ADR-013_design_tokens_validation.md

---

## 11. Token & Execution Optimization

- **Sequential execution cost**: Lập kế hoạch quản lý thiết kế tiêu tốn ~5,000 tokens.
- **Parallel execution opportunities**: Viết cấu trúc DesignFinding và quét cứng mã nguồn (Task 1.5, 1.8) song song với kb.py.
- **Expected token savings**: Tiết kiệm ~35% tokens nhờ chạy các kiểm thử tích hợp trên mock token files không cần nạp VLM mô hình lớn thực tế.
- **Recommended execution strategy**: Hoàn thành sớm lược đồ YAML rule và API truy vấn trước khi xây dựng agent phủ quyết.

---

## Recommended Next Skill
/blueprint
