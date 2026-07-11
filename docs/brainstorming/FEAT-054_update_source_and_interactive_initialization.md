<!-- docs/brainstorming/FEAT-054_update_source_and_interactive_initialization.md -->

---
feature_id: FEAT-054
feature_name: Build update-source and Interactive Project Initialization
status: draft
stage: brainstorming
created_at: 2026-07-11
updated_at: 2026-07-11
previous_artifact: None
next_artifact: ../plans/FEAT-054_update_source_and_interactive_initialization_plan.md
---

# Master Requirement Document – Build update-source and Interactive Project Initialization

## 1. Feature ID & Name
- **Feature ID**: FEAT-054
- **Feature Name**: Build update-source and Interactive Project Initialization

## 2. Original Idea
Xây dựng và tích hợp hai lệnh CLI toàn cục:
1. `aiwf update-source`: Cập nhật mã nguồn trung tâm của framework an toàn qua Git.
2. `aiwf init`: Khởi tạo tương tác một dự án mới hoàn toàn trống, thu thập thông tin dự án, cấu hình Git, cài đặt `.agents` và sinh các tệp tin cấu hình.

## 3. Business Problem
- **Problem**: Người dùng gặp khó khăn khi muốn cập nhật mã nguồn khung phát triển (AIWF framework source) hoặc khi bắt đầu một dự án mới với AIWF. Hiện tại chưa có cách nào để tự động cập nhật mã nguồn an toàn mà không làm hỏng code thay đổi cục bộ của người dùng. Trình cài đặt `install.ps1` chưa có bộ câu hỏi tương tác để tùy biến sâu cấu trúc thư mục, loại dự án (DDD, Clean Architecture, monorepo), ngôn ngữ (Go, Python, TypeScript) hay cơ sở dữ liệu khi khởi tạo.
- **Why it matters**: Làm tăng chi phí thiết lập ban đầu và gây khó khăn khi đồng bộ nâng cấp framework từ thượng nguồn cho nhiều nhà phát triển.
- **Who is affected**: Nhà phát triển dự án và AI coding agents cần môi trường chuẩn hóa ngay từ đầu.
- **Expected outcome**: Lệnh CLI toàn cục trực quan, chạy mượt mà trên Windows (PowerShell) và macOS/Linux (Bash).

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Định nghĩa lệnh `aiwf update-source` hỗ trợ `--source`, `--remote`, `--branch` để cập nhật mã nguồn framework.
  - FR-02: Ngăn chặn tự động ghi đè/reset/rebase khi nhánh framework bị bẩn (dirty) hoặc lệch pha (diverged).
  - FR-03: Cung cấp chế độ `--check`, `--dry-run`, `--json`, `--yes` cho tự động hóa CI/CD.
  - FR-04: Định nghĩa lệnh `aiwf init` hỗ trợ `--path`, `--non-interactive`, `--config`, `--dry-run`, `--resume`.
  - FR-05: Tích hợp bộ câu hỏi wizard phân cấp gồm 18 phần (Project Identity, Type, Architecture, Toolchain, DB, v.v.).
  - FR-06: Hỗ trợ khuyến nghị thông minh (recommendation engine) dựa trên mô tả mong muốn của người dùng.
  - FR-07: Sinh cấu trúc thư mục và tệp cấu hình `.agents/project.config.json` và `.agents/PROJECT_PROFILE.md` chuẩn hóa.
- **Non-functional Requirements**:
  - NFR-01: Tốc độ phân giải và chuyển tiếp lệnh dưới 50ms.
  - NFR-02: Không lưu trữ trực tiếp key/secrets nhạy cảm trong cấu hình.
  - NFR-03: Chạy độc lập hoàn toàn, không yêu cầu kết nối mạng công cộng trừ khi tải thư viện/dependencies.
- **Technical Constraints**:
  - TC-01: Tương thích ngược hoàn toàn 100% với các lệnh `install`, `update`, `uninstall`, `doctor`, `version` hiện có.

## 5. Requirement Traceability Matrix
| Req ID | Priority (Must/Should/Could/Won't) | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Hỗ trợ `aiwf update-source` cập nhật framework qua Git | Proposal Code Changes | unit/test_update_source.py | Cập nhật ff-only thành công |
| FR-02 | Must | Cảnh báo dừng nếu cây thư mục bị bẩn | Proposal Code Changes | unit/test_update_source.py | Trả lỗi và đề xuất option |
| FR-05 | Must | Trình khởi tạo tương tác dự án mới `aiwf init` | Proposal Code Changes | unit/test_init_wizard.py | Sinh cấu hình và tệp profile |
| FR-06 | Should | Khuyến nghị thông minh theo stack và topology | Proposal Code Changes | unit/test_recommendations.py | Đưa ra đề xuất phù hợp |

## 6. Stakeholder Analysis
| Stakeholder | Category (Primary/Secondary/Internal/External) | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Developers | Primary | High | High | Dễ dàng setup dự án mới và nâng cấp framework |
| AI Coding Agents | Internal | High | High | Hiểu rõ kiến trúc và quy định dự án qua tệp profile |

## 7. Scope Boundary
- **In Scope**:
  - Thêm lệnh `update-source` và `init` vào PowerShell wrapper và Bash wrapper.
  - Xây dựng module Python quản lý logic Git, bảng câu hỏi wizard tương tác và render template.
- **Out of Scope**:
  - Ghi đè tự động các thư mục chứa mã nguồn của dự án của người dùng mà không được xác nhận.

## 8. Dependency Graph Preview
- FR-01: Update-Source logic (Must)
- FR-05: Init Wizard questionnaire framework (Must)
  └── FR-06: Recommendation Engine (Should)
      └── FR-07: Template renderer & Scaffold creator (Must)

## 9. Data Flow Preview
User CLI Command ──> aiwf wrapper ──> Python Core Engine ──> State/Git/FS ──> Output/Config Files

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation (Reuse/Extend/Refactor/Replace/Remove) | Rationale |
| :--- | :--- | :--- | :--- |
| CLI Entrypoint | `skills/workflow-runtime/scripts/workflow_runtime.py` | Extend | Tích hợp các subcommands mới |
| Wrapper script | `bootstrap.ps1` | Extend | Thêm case routing cho `update-source` và `init` |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: workflow-runtime, initialize-workflow
- **Affected Modules/Components**: CLI wrappers, session state
- **Impact Level**: Low (Hầu hết là code mới bổ sung và forward).

## 12. Migration Strategy
- **Backward Compatibility**: Tương thích ngược hoàn toàn. Các dự án đang chạy tiếp tục hoạt động bình thường mà không cần bất kỳ thay đổi nào.

## 13. Architecture Principles
- **Provider First**: Cho phép thay thế linh hoạt các module cấu hình.
- **Script First**: Logic chạy an toàn thông qua các tệp script độc lập.

## 14. Non Goals
- Không tự động đẩy code (git push) hay tạo repo trên GitHub/GitLab mà không có lệnh trực tiếp.

## 15. ROI Analysis
- **Estimated Implementation Cost**: Thấp đến trung bình.
- **Runtime Savings**: Tiết kiệm hàng giờ đồng hồ mỗi khi setup dự án mới hoặc nâng cấp framework.

## 16. Success Metrics
- Lệnh `aiwf update-source` cập nhật thành công an toàn.
- Lệnh `aiwf init` hoàn thành tạo khung dự án mẫu chuẩn trong vòng dưới 2 phút tương tác.

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Xung đột Git khi pull | High | Low | Dùng ff-only mặc định, từ chối chạy khi diverged | Architect |

## 18. Technical Questions
- Làm sao để trình wizard tương tác tốt trên Windows PowerShell không hỗ trợ đầy đủ các thư viện prompt phức tạp? (Sử dụng giải pháp prompt phân cấp kiểu text đơn giản hoặc qua SQLite state).

## 19. Open Decision Register
| Topic / Decision | Current Status (Resolved/Pending/Requires ADR/Requires Prototype/Requires Research) | Rationale & Next Steps |
| :--- | :--- | :--- |
| Wizard engine choice | Resolved | Sử dụng giao diện dòng lệnh dạng text-base chuẩn hóa của workflow-runtime để đảm bảo tính đa nền tảng |

## 20. ADR Detection
- **ADR Required**: No.

## 21. Knowledge Update Impact
- **project-summary**: Yes.
- **architecture**: Yes.

## 22. Test Strategy Preview
- **Unit Tests**: Kiểm thử module Git state, kiểm thử parsing cấu hình init.
- **Integration Tests**: Mô phỏng quá trình chạy `init` trong thư mục tạm.

## 23. Extension Impact
- Không ảnh hưởng trực tiếp đến UI Visualizer Extension ngoại trừ việc cập nhật trạng thái session.

## 24. Complexity Estimation
- **Implementation Complexity**: Medium.

## 25. Roadmap Alignment
- Tích hợp trực tiếp vào lộ trình phát triển cốt lõi của AIWF.

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Lệnh `aiwf init` có khởi tạo Git mặc định không? | Có, nếu thư mục chưa có Git và được người dùng đồng ý. |

## 27. Requirement Readiness Score
- **Score**: 100/100.
- **Status**: Ready.

## 28. Existing Project Context
- **Memory Source**: [project-summary.md](file:///E:/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: Centralized CLI routing via Python engine.

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk (Low/Med/High) | Relevance |
|---|---|---|---|---|---|---|---|
| CLI wrapper | `bootstrap.ps1` | release-manager | None | 90% | 10% | Low | Routing |

## 30. Solution Options Evaluated

### Option A: Pure Bash/PowerShell CLI wrapper implementation
- **Overview**: Viết toàn bộ logic Git check, wizard câu hỏi và ghi file trực tiếp trong shell scripts.
- **Advantages**: Không phụ thuộc vào Python core lúc khởi động.
- **Disadvantages**: Khó duy trì, trùng lặp logic cao giữa Windows (.ps1) và Unix (.sh).
- **Complexity**: High.
- **Risk**: High.

### Option B: Pure Python CLI Integration
- **Overview**: Viết tất cả logic trong Python core `workflow_runtime.py`.
- **Advantages**: Cực kỳ dễ tái sử dụng, tương đồng 100% logic trên mọi hệ điều hành.
- **Disadvantages**: Đòi hỏi máy phải cài Python trước (đã là yêu cầu tiên quyết của dự án).
- **Complexity**: Low.
- **Risk**: Low.

### Option C: Hybrid Architecture (Recommended)
- **Overview**: Wrapper CLI làm nhiệm vụ bắt lệnh và forward nhanh sang Python Core Engine. Python Core Engine chịu trách nhiệm xử lý các tác vụ nặng (Git check, Wizard, template rendering), sau đó cập nhật lại wrapper nếu cần thiết.
- **Advantages**: Giữ wrapper cực nhẹ, tập trung logic nghiệp vụ và giao diện người dùng tại một nơi (Python), tối ưu hóa trải nghiệm đa nền tảng.
- **Disadvantages**: Không có.
- **Complexity**: Medium.
- **Risk**: Low.

## 31. Solution Comparison Table
| Criteria | Option A | Option B | Option C |
|---|---|---|---|
| Complexity | High | Low | Medium |
| Risk | High | Low | Low |
| Performance | High | High | High |
| Maintainability | Low | High | High |
| Compatibility | Medium | High | High |
| Future Scalability | Low | High | High |
| Development Cost | High | Low | Low |

## 32. Selected Solution
- **Choice**: Option C — Hybrid Architecture.
- **Why Selected**: Tối ưu hóa giữa tính dễ bảo trì và trải nghiệm người dùng đa nền tảng, kế thừa hoàn hảo mô hình CLI hiện tại của AIWF.
- **Trade-offs Accepted**: Phụ thuộc vào runtime Python (đã có sẵn).
- **Technical Debt**: Không có.
- **Risk Mitigation**: Kiểm tra kỹ tính sẵn sàng của Git và Python khi chạy wrapper.

## 33. Risks & Assumptions
- **Risks**: Người dùng chạy lệnh trong môi trường không có kết nối mạng khi cài đặt dependencies ➔ Báo lỗi rõ ràng và cung cấp lệnh resume.

## 34. Acceptance Criteria
- [ ] AC-01: `aiwf update-source` thực hiện ff-only an toàn và báo cáo phiên bản.
- [ ] AC-02: `aiwf init` chạy tương tác hoàn thành tạo khung dự án mẫu chuẩn.

## 35. Final Planning Prompt
Triển khai kỹ năng `brainstorming-to-plan` để chuyển tài liệu này thành kế hoạch thực thi chi tiết.
- Xác định cấu trúc lớp cho `SourceRepositoryService`, `InitQuestionnaire`.
- Lập lịch kiểm thử đơn vị và kiểm thử tích hợp.
- Chuẩn bị tài liệu hướng dẫn và SemVer.
