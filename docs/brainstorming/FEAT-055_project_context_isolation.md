---
feature_id: FEAT-055
feature_name: Project Context Isolation System
status: draft
stage: brainstorming
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: None
next_artifact: ../plans/FEAT-055_project_context_isolation_plan.md
---

# Master Requirement Document – Project Context Isolation System

## 1. Feature ID & Name
- **Feature ID**: FEAT-055
- **Feature Name**: Project Context Isolation System (Context Firewall)

## 2. Original Idea
Design and implement a Project Context Isolation System for the AI Workflow Framework so that AI agents never mix context, memory, transcripts, or conversation history from unrelated projects. The active project is the only valid context source. The AI MUST NOT retrieve or reuse context belonging to any other project unless the user explicitly requests cross-project comparison. Every retrieval operation must be validated against the active project scope before the retrieved context is exposed to any Skill.

## 3. Business Problem
- **Problem**: Khi làm việc trên nhiều dự án khác nhau trên cùng một môi trường máy chủ, AI có thể tự động đọc và trộn lẫn lịch sử, RAG, bộ nhớ SQLite hoặc các tài liệu hướng dẫn của dự án này sang dự án khác.
- **Why it matters**: Điều này có thể dẫn đến rò rỉ dữ liệu nhạy cảm giữa các dự án, hoặc AI sinh mã nguồn sử dụng các thư viện và cấu trúc của một dự án khác gây lỗi biên dịch nghiêm trọng.
- **Who is affected**: Người phát triển chạy đa dự án, quản trị viên bảo mật dữ liệu.
- **Expected outcome**: Một bộ lọc "Context Firewall" trung tâm sẽ cách ly hoàn toàn dữ liệu. AI chỉ có thể nhìn thấy dữ liệu nằm trong phạm vi dự án hiện tại (`project_id`, `workspace_root`, `git_root`, v.v.).

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Định nghĩa và lưu trữ cấu hình phạm vi dự án (`project_id`, `workspace_root`, `git_root`, `memory_root`, `vector_collection`, `sqlite_database`, `conversation_scope`, `allow_cross_project_context`) vào tệp `.agents/.session.json`.
  - FR-02: Triển khai một bộ lọc trung tâm "Context Firewall" ở tầng runtime để chặn và kiểm tra tất cả các yêu cầu lấy ngữ cảnh từ Skill.
  - FR-03: Trình tự lọc dữ liệu: Xác định dự án -> Xác thực project_id -> Xác thực workspace/git_root -> Loại bỏ dữ liệu lệch phạm vi -> Xếp hạng dữ liệu hợp lệ -> Trả về kết quả lọc.
  - FR-04: Cách ly lịch sử hội thoại: Chỉ cho phép tái sử dụng lịch sử chat khi có cùng `project_id`, `workspace` và `git_repository`. Nếu lệch, tự động hủy bỏ và hiển thị cảnh báo mismatch.
  - FR-05: Cập nhật công cụ `project-rag-search` để chèn bộ lọc phạm vi dự án vào mọi truy vấn vector database.
  - FR-06: Cập nhật Visualizer dashboard để hiển thị trạng thái cách ly dự án, các nguồn context đã sử dụng và số lượng context bị chặn do lệch dự án.
- **Non-functional Requirements**:
  - NFR-01: Bộ lọc Context Firewall phải thực hiện kiểm tra với độ trễ (latency overhead) dưới 50ms.
  - NFR-02: Duy trì tính tương thích ngược, các Skill cũ vẫn hoạt động mà không bị sập.
- **Technical Constraints**:
  - TC-01: `allow_cross_project_context` mặc định là `false`. Chỉ được bật khi có yêu cầu rõ ràng từ người dùng.
  - TC-02: Lịch sử hội thoại cũ không được là nguồn ngữ cảnh ưu tiên số một.

## 5. Requirement Traceability Matrix
| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Định nghĩa phạm vi dự án trong Session | Project Scope definition | test_project_scope_persisted | Cấu hình dự án xuất hiện trong `.session.json` |
| FR-02 | Must | Triển khai Context Firewall trung tâm | Context Firewall Engine | test_context_firewall_filters | Các ngữ cảnh ngoài thư mục dự án bị từ chối |
| FR-03 | Must | Cập nhật thứ tự ưu tiên tìm kiếm ngữ cảnh | Context Retrieval Order | test_retrieval_priority_order | RAG và Memory luôn được ưu tiên hơn Chat History |
| FR-04 | Must | Cách ly và cảnh báo mismatch hội thoại | Conversation Isolation | test_conversation_mismatch_discarded | Chat history lệch project_id bị hủy và hiển thị cảnh báo |
| FR-05 | Must | Cấu hình tìm kiếm RAG theo dự án | Project-aware RAG | test_rag_never_searches_global | RAG chỉ truy vấn collection của dự án hiện hành |
| FR-06 | Should | Hiển thị trên Visualizer | Visualizer Dashboard | manual_visualizer_verification | Dashboard vẽ được biểu đồ Context Isolation Status |

## 6. Stakeholder Analysis
| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Người dùng (Ba) | Primary | Lớn | Cao | Đảm bảo tính bảo mật và chính xác tuyệt đối của dữ liệu các dự án độc lập |
| QA Reviewer | Internal | Vừa | Vừa | Dễ dàng gỡ lỗi dữ liệu chéo |

## 7. Scope Boundary
- **In Scope**:
  - Viết module `ContextFirewall` trong nhân runtime.
  - Sửa đổi lệnh tìm kiếm của `project-rag-search`.
  - Cập nhật schema `.session.json` và bổ sung chính sách vào `AI_RULES.md`.
  - Thêm cảnh báo mismatch vào console output của Agent.
- **Out of Scope**:
  - Không sửa đổi cấu hình lưu trữ vật lý của cơ sở dữ liệu Vector (như thay đổi cấu trúc cài đặt Qdrant) mà chỉ thay đổi cách truy vấn.
  - Không cách ly các file toàn cục trong thư mục cấu hình cá nhân của IDE (như `.gemini/config/skills`).

## 8. Dependency Graph Preview
- Requirement discovery
  └── Thiết lập Session Schema mới lưu Project Scope (Must)
      └── Viết lớp Context Firewall trung tâm (Must)
          └── Cập nhật các API lấy RAG và Lịch sử hội thoại (Must)
              └── Thiết kế giao diện cảnh báo trên Visualizer & Kiểm thử (Should)

## 9. Data Flow Preview
- Skill Request Context
  └── Context Firewall ──> [Đối chiếu project_id, workspace_root, git_root]
      ├── Hợp lệ ──> Trả về dữ liệu lọc cho Skill
      └── Không hợp lệ ──> Loại bỏ ──> Ghi nhận vào log chặn và cảnh báo trên Visualizer

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Runtime State | `skills/workflow-runtime/scripts/workflow_runtime.py` | Extend | Tích hợp lớp kiểm tra Context Firewall |
| RAG Skill | `skills/project-rag-search/` | Extend | Truyền các tham số phạm vi dự án vào khi thực hiện tìm kiếm vector |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: Tất cả các Skill thực hiện tìm kiếm hoặc đọc bộ nhớ (`project-memory-bootstrap`, `project-memory-update`, `project-rag-search`, `brainstorming`, v.v.).
- **Affected Modules/Components**: Tầng RAG Search và Session State.
- **Impact Level**: High (Ảnh hưởng đến toàn bộ luồng nạp ngữ cảnh của các Skill).

## 12. Migration Strategy
- **Backward Compatibility**: Nếu một dự án cũ chưa được khởi tạo cấu hình dự án, hệ thống sẽ tự động gán các giá trị mặc định dựa trên thư mục hiện tại (`workspace_root = "."`) để đảm bảo không làm sập luồng làm việc cũ.
- **Coexistence Period**: Hỗ trợ chạy không có firewall nếu biến môi trường `DISABLE_CONTEXT_FIREWALL=true` được thiết lập (chỉ dành cho mục đích gỡ lỗi).

## 13. Architecture Principles
- **API First**: Các phương thức của Context Firewall được đóng gói sạch sẽ để các Skill gọi mà không cần biết logic lọc chi tiết bên dưới.
- **Provider First**: Khả năng chuyển đổi cơ sở dữ liệu metadata từ SQLite sang cấu trúc tệp tin JSON mà không làm thay đổi logic firewall.
- **Strict Isolation**: Nguyên tắc mặc định là từ chối (default deny).

## 14. Non Goals
- Không mã hóa dữ liệu trên đĩa (Data Encryption at Rest).
- Không chặn việc sao chép thủ công các tệp tin của người dùng giữa các thư mục bằng lệnh shell ngoài.

## 15. ROI Analysis
- **Estimated Implementation Cost**: Trung bình (3-4 ngày làm việc).
- **Runtime Savings**: Tiết kiệm rất nhiều token lãng phí do nạp sai lịch sử chat không liên quan, tăng tốc độ xử lý của mô hình.

## 16. Success Metrics
- 100% các yêu cầu đọc dữ liệu ngoài phạm vi dự án bị chặn đứng.
- Không có bất kỳ lỗi biên dịch chéo nào xảy ra do tham chiếu sai thư mục dự án.
- Visualizer phản ánh chính xác số lượng tài nguyên bị chặn.

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Chặn nhầm ngữ cảnh hợp lệ do cấu hình sai git_root | High | Low | Cung cấp cảnh báo chi tiết và cho phép ghi đè qua cấu hình `allow_cross_project_context` | Coder |
| Hiệu năng tìm kiếm RAG giảm do thêm bộ lọc | Low | Medium | Đánh chỉ mục (index) trường project_id trong Qdrant | Architect |

## 18. Technical Questions
- Làm sao để xác định `project_id` duy nhất? -> Sử dụng mã băm của git repository URL hoặc kết hợp tên thư mục và git commit đầu tiên.

## 19. Open Decision Register
| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Cách xác định project_id mặc định | Resolved | Ưu tiên đọc trường `project_id` trong `memory.config.json` nếu có, nếu không tự động hash git remote URL. |

## 20. ADR Detection
- **ADR Required**: Yes. Do đây là thay đổi lớn về cơ chế quản lý ngữ cảnh toàn cục, cần tạo một ADR mô tả cấu trúc của Context Firewall.

## 21. Knowledge Update Impact
- **project-summary**: Yes. Ghi nhận kiến trúc cô lập ngữ cảnh.
- **architecture**: Yes. Bổ sung thành phần Context Firewall vào sơ đồ kiến trúc runtime.

## 22. Test Strategy Preview
- **Unit Tests**: Kiểm thử lớp `ContextFirewall` với các trường hợp dữ liệu giả lập đúng/sai thông tin dự án.
- **Integration Tests**: Chạy thử Skill RAG search để đảm bảo nó không trả về kết quả của collection thuộc dự án khác.

## 23. Extension Impact
- **Extension UI Changes**: Visualizer cần hiển thị thêm widget thông tin: Project Scope, Blocked Items Count và Cảnh báo Project Mismatch dạng thông báo nổi (toast).

## 24. Complexity Estimation
- **Implementation Complexity**: Medium
- **Estimated Refactoring Percentage**: Khoảng 15% mã nguồn liên quan đến RAG và Runtime.

## 25. Roadmap Alignment
- **Roadmap Phase**: Phase 6 (Hardening Campaign)
- **Milestones**: Thiết kế Firewall -> Tích hợp RAG -> Cập nhật Visualizer -> Đóng gói.

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Có cho phép so sánh chéo các dự án không? | Bị chặn mặc định, chỉ kích hoạt khi `allow_cross_project_context` được set thành `true` bởi người dùng. |

## 27. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 28. Existing Project Context
- **Memory Source**: `.agents/memory/project-summary.md`
- Hệ thống RAG hiện tại tìm kiếm trên collection được khai báo trong `memory.config.json`.

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| RAG Search Skill | `skills/project-rag-search/` | planner | search APIs | 70% | 30% | High | Nguồn cung cấp ngữ cảnh chính |

## 30. Solution Options Evaluated
### Option A: Centralized Context Firewall (Selected)
- **Overview**: Lọc tập trung tại runtime, bảo vệ toàn bộ Skill một cách trong suốt.
- **Complexity**: Medium
- **Security**: Tuyệt đối.

### Option B: Decentralized Filtering in Skills
- **Overview**: Mỗi Skill tự lọc.
- **Complexity**: Medium
- **Security**: Thấp (dễ sót).

## 31. Solution Comparison Table
| Criteria | Option A (Firewall) | Option B (Decentralized) |
|---|---|---|
| Complexity | Medium | Medium |
| Risk | Low | High |
| Performance | High | Medium |
| Maintainability | High | Low |
| Compatibility | High | High |

## 32. Selected Solution
- **Choice**: Option A — Centralized Context Firewall.
- **Why Selected**: Đảm bảo tính bảo mật tập trung, giảm thiểu lỗi lập trình khi viết các Skill mới.

## 33. Risks & Assumptions
- **Assumptions**: Giả định rằng mọi dự án đều có cấu hình Git hoặc `memory.config.json` hợp lệ để lấy thông tin định danh dự án.

## 34. Acceptance Criteria
- [ ] AC-01 (maps to FR-02): Context Firewall từ chối trả về dữ liệu lệch `workspace_root` hoặc `project_id`.
- [ ] AC-02 (maps to FR-04): Đưa ra thông báo "Project mismatch detected" và hủy nạp lịch sử chat lệch dự án.
- [ ] AC-03 (maps to FR-06): Visualizer hiển thị đúng trạng thái Project Isolation Status.

## 35. Final Planning Prompt
Hãy thiết kế chi tiết lớp `ContextFirewall`, cấu trúc schema `.session.json` lưu trữ thông tin dự án và cách thức tích hợp vào Skill `project-rag-search` để hoàn thành mục tiêu cách ly ngữ cảnh dự án một cách an toàn và trong suốt.

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
