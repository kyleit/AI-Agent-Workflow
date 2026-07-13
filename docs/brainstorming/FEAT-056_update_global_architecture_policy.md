---
feature_id: FEAT-056
feature_name: Update Global Architecture Policy
status: draft
stage: brainstorming
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: None
next_artifact: ../plans/FEAT-056_update_global_architecture_policy_plan.md
---

# Master Requirement Document – Update Global Architecture Policy

## 1. Feature ID & Name
- **Feature ID**: FEAT-056
- **Feature Name**: Update Global Architecture Policy (DDD & Clean Architecture Standards)

## 2. Original Idea
Update the framework rules so that all software development workflows follow a default architecture standard: DDD, Clean Architecture, Project-aware technology selection, Clear backend/frontend framework suggestion rules, File size guidelines and refactor triggers. This update must be implemented as a global policy so every Skill can inherit it through the centralized rule system (AI_RULES.md).

## 3. Business Problem
- **Problem**: Các AI Agent phát triển phần mềm hiện tại chưa có các chỉ dẫn ràng buộc về mặt kiến trúc toàn cục, dẫn đến việc thiết kế cấu trúc thư mục lộn xộn hoặc tạo ra các tệp tin quá lớn (hàng ngàn dòng) gây khó khăn cho việc đọc hiểu, kiểm thử và bảo trì mã nguồn lâu dài.
- **Why it matters**: Việc thiếu tiêu chuẩn kiến trúc thống nhất làm tăng nợ kỹ thuật (technical debt), lãng phí token do AI phải đọc và viết lại các file quá lớn, và làm giảm độ tin cậy của mã nguồn được sinh ra.
- **Who is affected**: Nhà phát triển dự án, các nhân tố AI Coder, Architect.
- **Expected outcome**: Thiết lập một chính sách kiến trúc trung tâm trong `AI_RULES.md` bắt buộc tuân thủ DDD + Clean Architecture, các quy tắc phân vùng công nghệ tự động và giới hạn mềm kích thước tệp tin (Soft Line Limits).

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Bổ sung mục `"Architecture & Code Organization Policy"` vào tệp chính sách trung tâm `AI_RULES.md`.
  - FR-02: Định nghĩa các tầng kiến trúc backend mặc định: Domain, Application, Infrastructure và Transport/Interface kèm quy tắc hướng phụ thuộc (Dependency Direction Rules).
  - FR-03: Ràng buộc các quy tắc công nghệ mặc định cho Backend (Go prefer Fiber/Gin, Python prefer FastAPI/Typer) và Frontend (Svelte/SvelteKit theo mặc định nếu không có preference của dự án).
  - FR-04: Thiết lập bảng hướng dẫn giới hạn mềm (Soft Limits) số dòng code cho mỗi loại tệp tin (ví dụ: Domain entity tối đa 150 dòng, service/repository 250 dòng, test 400 dòng).
  - FR-05: Cập nhật chỉ thị hướng dẫn ngắn gọn cho các Skill liên quan (`plan-to-blueprint`, `quick-feature`, `quick-fix`, v.v.) để tham chiếu đến chính sách mới này.
  - FR-06: Cập nhật công cụ memory-bootstrap/update để tự động phân tích và lưu trữ các đặc tính kiến trúc của dự án vào tệp tóm tắt.
- **Non-functional Requirements**:
  - NFR-01: Tiết kiệm tối đa dung lượng token bằng cách chỉ dùng các đường link tham chiếu ngắn gọn trong Skill thay vì sao chép toàn bộ chính sách.
  - NFR-02: Tương thích ngược: Không bắt buộc viết lại các dự án cũ đã có kiến trúc ổn định khác.
- **Technical Constraints**:
  - TC-01: Nếu tệp tin vượt quá giới hạn mềm hơn 20% trong lúc viết code, Agent bắt buộc phải dừng lại và đề xuất phương án tách lớp/refactor trong Blueprint trước khi làm tiếp.
  - TC-02: Cấm để logic nghiệp vụ rò rỉ vào tầng HTTP Handlers hay Database Adapters.

## 5. Requirement Traceability Matrix
| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Thêm chính sách kiến trúc vào `AI_RULES.md` | Policy Specification | test_policy_specification | `AI_RULES.md` chứa định nghĩa chính sách mới |
| FR-02 | Must | Quy tắc phân tầng DDD và Clean Architecture | Architecture Standards | test_ddd_layered_boundaries | Kiểm tra tính tuân thủ hướng phụ thuộc |
| FR-03 | Must | Quy định lựa chọn công nghệ mặc định | Tech Selection Rules | test_tech_selection_svelte | Ưu tiên Svelte/SvelteKit cho frontend mới |
| FR-04 | Must | Thiết lập Soft Limits dòng code của file | File Size Guidelines | test_file_size_limit_check | Có cảnh báo khi file vượt quá 20% giới hạn |
| FR-05 | Must | Cập nhật tham chiếu chính sách ở các Skill | Skill Instructions Update | test_skill_references_updated | Các file `SKILL.md` của các skill được cập nhật |
| FR-06 | Should | Cập nhật tài liệu dự án (README/USAGE) | Documentation Update | test_docs_reflect_architecture | Tài liệu công khai ghi nhận kiến trúc DDD |

## 6. Stakeholder Analysis
| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Nhà phát triển (Ba) | Primary | Lớn | Cao | Nhận được mã nguồn sạch sẽ, tuân thủ đúng chuẩn công nghiệp, dễ bảo trì |
| AI Architect | Internal | Rất lớn | Cao | Có hợp đồng thiết kế kỹ thuật rõ ràng để đối chiếu |
| AI Coder | Internal | Rất lớn | Cao | Giảm thiểu mã nguồn thừa, kiểm soát kích thước file tốt hơn |

## 7. Scope Boundary
- **In Scope**:
  - Sửa đổi `AI_RULES.md` và các tệp `SKILL.md` của các skill được chỉ định.
  - Cập nhật tài liệu `README.md`, `USAGE.md`, `INSTALL.md` và `AGENTS.md`.
  - Cấu hình phân tích kiến trúc cho Skill memory bootstrap.
- **Out of Scope**:
  - Không tự ý tái cấu trúc (refactor) các dự án hiện có nếu không có yêu cầu cụ thể từ Ba.
  - Không viết công cụ tự động chia nhỏ file (auto-splitter) bằng code.

## 8. Dependency Graph Preview
- Requirement discovery
  └── Cập nhật AI_RULES.md với Architecture Policy (Must)
      └── Sửa đổi các file SKILL.md để bổ sung tham chiếu chính sách (Must)
          └── Cập nhật các tài liệu dự án USAGE/README (Should)
              └── Tích hợp logic kiểm tra file size vào bộ gỡ lỗi/kiểm thử (Must)

## 9. Data Flow Preview
- AI Agent proposed changes
  └── Check file size limits ──> Exceeds limit by >20%?
      ├── Yes ──> Stop ──> Propose refactor/split in blueprint ──> User approved? ──> Refactor
      └── No ──> Proceed implementation directly

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Central Rules | `AI_RULES.md` | Extend | Bổ sung phần Architecture & Code Organization Policy |
| Brainstorming Skill | `skills/brainstorming-to-plan/SKILL.md` | Extend | Bổ sung tham chiếu chính sách kiến trúc |
| Blueprint Skill | `skills/plan-to-blueprint/SKILL.md` | Extend | Thêm phần đánh giá rủi ro kích thước tệp tin |
| Implementation Skill | `skills/blueprint-to-implementation/SKILL.md` | Extend | Thêm kiểm tra ranh sách Clean Architecture trước khi code |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: `brainstorming-to-plan`, `plan-to-blueprint`, `blueprint-to-implementation`, `quick-feature`, `quick-fix`, `project-memory-bootstrap`, `project-memory-update`.
- **Affected Documentation**: `README.md`, `USAGE.md`, `INSTALL.md`, `AGENTS.md`.
- **Impact Level**: High (Thay đổi định hướng thiết kế và triển khai của toàn bộ hệ thống phát triển).

## 12. Migration Strategy
- **Backward Compatibility**: Các tệp tin hiện tại vượt quá số dòng quy định sẽ được bỏ qua (exempt) và chỉ áp dụng quy tắc giới hạn mềm đối với các file viết mới hoặc các module được sửa đổi/tách lớp lớn trong kế hoạch thiết kế mới.
- **Coexistence Period**: Cho phép duy trì các kiến trúc cũ (như MVC, Monolith đơn giản) nếu dự án cũ đã cấu trúc như vậy từ trước.

## 13. Architecture Principles
- **Clean Architecture & DDD**: Tách biệt rõ ràng domain logic khỏi giao diện vận chuyển (HTTP/CLI) và cơ sở hạ tầng.
- **Single Source of Truth**: Tập trung chính sách tại `AI_RULES.md` để tránh phân mảnh luật lệ.
- **Cohesive Modules**: Thà có một tệp tin lớn có tính kết dính cao còn hơn chia nhỏ thành nhiều file vụn vặt không liên quan.

## 14. Non Goals
- Không ép buộc chuyển đổi các dự án PHP, Java hay C# sang cấu trúc DDD của Go/Python nếu không phù hợp Stack.
- Không viết code tự động sinh các thư mục DDD khi khởi tạo dự án.

## 15. ROI Analysis
- **Estimated Implementation Cost**: Thấp (chủ yếu là chỉnh sửa tài liệu và chính sách trong 1-2 ngày).
- **Runtime Savings**: Tiết kiệm 20-30% dung lượng token hội thoại nhờ giảm thiểu kích thước tệp tin cần đọc/ghi, tăng độ chính xác của logic nghiệp vụ được sinh ra.

## 16. Success Metrics
- 100% tài liệu Skill mới kế thừa chính xác chính sách kiến trúc từ `AI_RULES.md`.
- Tất cả các file code sinh mới tuân thủ đúng giới hạn số dòng (hoặc được giải trình rõ ràng trong Blueprint nếu vượt giới hạn).

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Chia nhỏ file quá mức làm mất tính kết dính của module | Medium | Medium | Đưa ra quy tắc ưu tiên tính kết dính (cohesion) lên trước giới hạn số dòng | Architect |
| AI Agent quên tham chiếu chính sách khi viết code | Low | Medium | Đưa chỉ thị tham chiếu chính sách vào checklist tự kiểm tra của Skill | Coder |

## 18. Technical Questions
- Làm thế nào để AI nhận biết dự án cũ đã có kiến trúc riêng? -> AI Coder bắt buộc phải đọc `project-summary.md` và kiểm tra cấu trúc thư mục hiện có trước khi đề xuất giải pháp.

## 19. Open Decision Register
| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Công cụ frontend mặc định | Resolved | Ưu tiên Svelte/SvelteKit vì tính nhẹ nhàng, ít phụ thuộc runtime phức tạp và hiệu năng cao. |

## 20. ADR Detection
- **ADR Required**: No (Chỉ là thiết lập và hướng dẫn chính sách kiến trúc chung qua tài liệu).

## 21. Knowledge Update Impact
- **project-summary**: Yes. Ghi nhận chính sách kiến trúc toàn cục.
- **lessons**: Yes. Bài học về việc kiểm soát kích thước file.

## 22. Test Strategy Preview
- **Unit Tests**: Kiểm tra tính toàn vẹn của các liên kết Markdown trong tài liệu chính sách để tránh broken links.
- **Verification Gate**: Chạy thử quy trình tạo blueprint để kiểm tra xem AI có tự động phát hiện rủi ro quá kích thước file hay không.

## 23. Extension Impact
- **Extension UI Changes**: Không có.

## 24. Complexity Estimation
- **Implementation Complexity**: Low
- **Estimated Refactoring Percentage**: < 5% (chỉ cập nhật nội dung chính sách).

## 25. Roadmap Alignment
- **Roadmap Phase**: Phase 7 (Hardening Campaign)
- **Milestones**: Cập nhật AI_RULES.md -> Cập nhật các Skill -> Cập nhật USAGE/README -> Kiểm tra.

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Quy tắc giới hạn dòng code áp dụng cho các file nào? | Chỉ áp dụng cho các file logic do AI viết mới hoặc sửa đổi lớn. Loại trừ các file tự động sinh, file cấu hình, lock files và migrations. |

## 27. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 28. Existing Project Context
- **Memory Source**: `.agents/memory/project-summary.md`
- Hệ thống sử dụng tệp `AI_RULES.md` làm gốc chính sách.

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| Central Policies | `AI_RULES.md` | release-manager | Markdown | 90% | 10% | Low | Gốc chính sách |

## 30. Solution Options Evaluated
### Option A: Centralized Architecture Policy (Selected)
- **Overview**: Cập nhật chính sách tại `AI_RULES.md` và dẫn link ở các Skill.
- **Complexity**: Low
- **Efficiency**: Tiết kiệm token, dễ bảo trì.

### Option B: Inline Rules in Templates
- **Overview**: Đưa luật vào từng file template/blueprint.
- **Complexity**: Low
- **Risk**: Lãng phí token ngữ cảnh.

## 31. Solution Comparison Table
| Criteria | Option A (Centralized) | Option B (Inline) |
|---|---|---|
| Complexity | Low | Low |
| Risk | Low | Medium |
| Performance | High | Low |
| Maintainability | High | Low |
| Compatibility | High | High |

## 32. Selected Solution
- **Choice**: Option A — Centralized Architecture Policy.
- **Why Selected**: Đảm bảo cấu trúc sạch, nhất quán và cực kỳ tiết kiệm token cho các phiên hội thoại.

## 33. Risks & Assumptions
- **Assumptions**: Giả định rằng các Skill hiện tại và tương lai đều được lập trình để luôn đọc `AI_RULES.md` trước khi thực thi.

## 34. Acceptance Criteria
- [ ] AC-01 (maps to FR-01): `AI_RULES.md` được bổ sung phần "Architecture & Code Organization Policy".
- [ ] AC-02 (maps to FR-04): Bảng giới hạn số dòng dòng code được định nghĩa rõ ràng.
- [ ] AC-03 (maps to FR-05): Các tệp tin Skill của Planner/Architect/Coder được cập nhật chỉ thị tham chiếu chính sách.

## 35. Final Planning Prompt
Hãy lập kế hoạch chi tiết để cập nhật `AI_RULES.md`, bổ sung chính sách kiến trúc DDD + Clean Architecture, các quy tắc gợi ý công nghệ frontend/backend và giới hạn số dòng dòng code, đồng thời cập nhật các tệp `SKILL.md` của các Skill liên quan để tham chiếu chính xác đến chính sách này.

---

## Self-Validation Checklist
| Validation Item | Status |
| :--- | :---: |
| Outputted the `DISCOVERY MODE ACTIVE` declaration | PASS |
| Did NOT modify any source code files | PASS |
| Did NOT edit any project files outside `docs/brainstorming/` | PASS |
| Calculated the Requirement Readiness Score | PASS |
| Generated 2–3 significantly different solution options | PASS |
| Recommended one option with detailed architectural reasoning | PASS |
| Asked "Continue generating Brainstorming document? [Y/N]" | PASS |
| Stopped after completing Brainstorming generation | PASS |

**Result:** `ALL PASS`
