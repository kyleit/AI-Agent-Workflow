---
feature_id: FEAT-045
feature_name: AIWF Knowledge Runtime
status: draft
stage: brainstorming
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: None
next_artifact: ../plans/FEAT-045_aiwf_knowledge_runtime_plan.md
---

# Master Requirement Document – AIWF Knowledge Runtime

## 1. Feature ID & Name
- **Feature ID**: FEAT-045
- **Feature Name**: AIWF Knowledge Runtime

## 2. Original Idea
Triển khai **AIWF Knowledge Runtime** dưới dạng lớp tri thức thế hệ mới của khung làm việc AI Skill Framework. Tách biệt API tri thức khỏi các nhà cung cấp dữ liệu (providers) cụ thể, tối ưu chi phí tìm kiếm, hỗ trợ bộ nhớ đệm (caching) để giảm độ trễ dưới 200ms, đồng thời tự động cập nhật liên kết ngược (backlinks), bài học kinh nghiệm (lessons) và mẫu thiết kế (patterns).

## 3. Business Problem
- **Problem**: Các Skill của AI hiện nay truy cập trực tiếp vào các tệp Markdown hoặc gọi các API tìm kiếm vector (như Qdrant) một cách phân tán. Điều này làm trùng lặp logic, tăng độ liên kết chặt (coupling) giữa Skill và cách lưu trữ dữ liệu, gây khó khăn cho việc bảo trì và nâng cấp khi cần thay thế nhà cung cấp tri thức.
- **Why it matters**: Làm chậm tốc độ phản hồi của AI agent, tăng chi phí gọi API bên ngoài, khó bảo vệ tính nhất quán dữ liệu tri thức trên các dự án khác nhau và cản trước việc hỗ trợ đa dạng nhà cung cấp (như SQLite hay Obsidian).
- **Expected outcome**: Một lớp API tri thức ổn định, tách biệt nhà cung cấp dữ liệu, hỗ trợ bộ nhớ đệm hiệu năng cao và tự động hóa toàn bộ việc cập nhật chỉ mục, bài học và liên kết ngược.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Giao diện API ổn định (`search()`, `read()`, `save()`, `update()`, `link()`, `find_patterns()`, `find_similar_errors()`, `refresh_index()`).
  - FR-02: Trừu tượng hóa lớp Provider hỗ trợ Markdown, SQLite, Obsidian, và Vector DB.
  - FR-03: Tìm kiếm tích hợp từ khóa, nhãn và liên kết ngược (backlinks).
  - FR-04: Định tuyến tối ưu chi phí tìm kiếm (Cheapest Strategy First).
  - FR-05: Hỗ trợ bộ đệm tri thức (knowledge caching) hiệu năng cao.
  - FR-06: Tự động trích xuất bài học kinh nghiệm (Lessons Learned) và mẫu thiết kế (Patterns).
  - FR-07: Tự động duy trì đồ thị liên kết tri thức (Backlinks Graph).
  - FR-08: Tích hợp Obsidian làm Provider tùy chọn đồng bộ đồ thị 2 chiều.
  - FR-09: Công cụ phân tích chất lượng tri thức (Knowledge Quality Analyzer).
- **Non-functional Requirements**:
  - NFR-01: Độ trễ tìm kiếm cache hit < 200ms.
  - NFR-02: Đảm bảo tương thích ngược 100% cho các Skills cũ.
  - NFR-03: Dependency Injection giúp thay thế Provider linh hoạt.
- **Technical Constraints**:
  - TC-01: Chạy trên môi trường Python 3.11+.
  - TC-02: Cấu hình mặc định sử dụng Markdown cục bộ, Qdrant/Obsidian là tùy chọn.
  - TC-03: Thiết lập tùy chọn theo năng lực (Capability-based fallback).

## 5. Requirement Traceability Matrix
| Req ID | Priority (Must/Should/Could/Won't) | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | API ổn định | Section 3 (Interfaces) | test_api.py | AC-01 (API hoạt động đúng) |
| FR-02 | Must | Provider Abstraction | Section 1 (Code Changes) | test_providers.py | AC-02 (Hoán đổi Provider) |
| FR-03 | Should | Tìm kiếm từ khóa & backlinks | Section 4 (Algorithms) | test_search.py | AC-03 (Chỉ mục backlinks) |
| FR-04 | Should | Fallback & Routing | Section 4 (Algorithms) | test_routing.py | AC-04 (Tự động fallback) |
| FR-05 | Must | Caching đệm | Section 4 (Algorithms) | test_cache.py | AC-05 (Độ trễ <200ms) |
| FR-06 | Should | Trích xuất bài học & patterns | Section 4 (Algorithms) | test_lessons.py | AC-06 (Cập nhật lessons) |
| FR-07 | Should | Backlinks Graph sync | Section 4 (Algorithms) | test_backlinks.py | AC-07 (Đồ thị backlinks) |
| FR-08 | Could | Obsidian Provider | Section 1 (Code Changes) | test_obsidian.py | AC-08 (Đồng bộ Obsidian) |
| FR-09 | Could | Quality Analyzer | Section 4 (Algorithms) | test_quality.py | AC-09 (Báo cáo orphan notes) |

## 6. Stakeholder Analysis
| Stakeholder | Category (Primary/Secondary/Internal/External) | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Coder Agent | Primary | Cao | Must | Gọi tri thức nhanh chóng, giảm token context |
| Planner Agent | Secondary | Trung bình | Should | Kế thừa phân loại rủi ro và phạm vi |
| Architect Agent | Secondary | Cao | Must | Nhận trực tiếp các nguyên tắc thiết kế |
| IDE Visualizer UI | Internal | Thấp | Could | Hiển thị thống kê tri thức trực quan |

## 7. Scope Boundary
- **In Scope**:
  - Triển khai Core API, Caching, và Incremental Indexing.
  - Markdown, SQLite, và Obsidian Providers.
  - Tự động trích xuất bài học, backlinks graph, và quality analyzer.
- **Out of Scope**:
  - Không sửa đổi mã nguồn workflow state check của workflow_runtime.py.
- **Deferred Scope**:
  - Đồng bộ hai chiều với wiki trên nền tảng GitHub/GitLab.
- **Future Scope**:
  - Cơ chế đồng bộ SQLite đa người dùng (multi-user shared DB sync).

## 8. Dependency Graph Preview
- FR-01: Knowledge API (Must)
  ├── FR-02: Provider Abstraction & Markdown/SQLite Providers (Must)
  │   ├── FR-05: JSON Caching Layer (Must)
  │   │   ├── FR-03: Keyword/Backlink Search Index (Should)
  │   │   │   └── FR-04: Capability-based Fallback & Routing (Should)
  │   │   └── FR-06: Lessons & Patterns Auto Extraction (Should)
  │   └── FR-08: Obsidian Provider integration (Could)
  └── FR-09: Knowledge Quality Analyzer (Could)

## 9. Data Flow Preview
- Skill Client
  └── calls ──> knowledge.search() (API Layer)
      └── checks ──> cache.get() (Cache Layer)
          ├── [Cache Hit] ──> returns cached results directly
          └── [Cache Miss] ──> routes to active provider (Markdown/SQLite/Qdrant)
              └── scans ──> database/filesystem index
                  └── updates cache ──> returns fresh results

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation (Reuse/Extend/Refactor/Replace/Remove) | Rationale |
| :--- | :--- | :--- | :--- |
| RAG Searcher | skills/project-rag-search/scripts/search.py | Extend | Tái cấu trúc RAGSearcher làm VectorDBProvider |
| Keyword Index | skills/project-memory-bootstrap/scripts/keyword_index.py | Reuse | Sử dụng logic so khớp từ khóa và tag |
| Memory Update | skills/project-memory-update/scripts/update.py | Extend | Trích xuất logic phân tích bài học kinh nghiệm |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: brainstorming, brainstorming-to-plan, plan-to-blueprint (Trung bình - cần bổ sung hooks gọi API tri thức).
- **Affected Modules/Components**: .agents/runtime/scripts/project_memory/ (Cao - gom toàn bộ vào thư mục gói knowledge_runtime).
- **Affected Runtime**: CLI commands trong workflow_runtime.py (Trung bình - bổ sung nhóm lệnh knowledge).
- **Affected Extension**: Không trực tiếp sửa đổi UI, chỉ cập nhật dữ liệu đầu ra trạng thái (Thấp).
- **Impact Level**: Trung bình (Medium).

## 12. Migration Strategy
- **Backward Compatibility**: Tương thích ngược cấu hình memory.config.json cũ thông qua một Adapter Class.
- **Adapter Strategy**: Các Skill cũ vẫn có thể truy cập trực tiếp file Markdown thông qua adapter cục bộ nếu chưa được di chuyển hoàn toàn.
- **Coexistence Period**: Cung cấp khoảng thời gian 2 tuần chạy song song cả project-memory cũ và API mới để đối chiếu kết quả.

## 13. Architecture Principles
- **API First**: Mọi truy cập tri thức của Skills bắt buộc đi qua lớp API.
- **Provider First**: Các công cụ lưu trữ dữ liệu là pluggable và swappable.
- **Script First**: Thực thi trực tiếp qua các tiến trình Python CLI.
- **Memory First**: Kiểm tra cache/index cục bộ trước khi quét đĩa.
- **Replaceable Providers**: Cho phép đổi Provider mà không sửa mã Skill.

## 14. Non Goals
- Sẽ **KHÔNG** làm thay đổi các kiểm tra checkpoint hoạt động của CLI workflow_runtime.py.
- Sẽ **KHÔNG** viết lại mã nguồn cốt lõi của extension trong đợt cập nhật này.

## 15. ROI Analysis
- **Estimated Implementation Cost**: Thấp-Trung bình (khoảng 3 ngày làm việc của 1 subagent).
- **Runtime Savings**: Giảm thời gian khởi động và tìm kiếm từ ~1.5s xuống <200ms.
- **Token Reduction Target**: Tiết kiệm trung bình 15-20% tokens cho mỗi cuộc hội thoại bằng cách loại bỏ việc nạp các tệp MD khổng lồ không liên quan.
- **API Call Reduction Target**: Giảm 40% số cuộc gọi API tìm kiếm vector nhờ cache cục bộ.
- **Maintenance Impact**: Tách biệt mã nguồn giúp giảm thời gian debug lỗi bộ nhớ xuống 50%.
- **Expected Break-Even**: Đạt được sau 10 phiên phát triển tính năng mới.
- **Long-Term ROI**: Tăng hiệu quả và tốc độ phản hồi của toàn bộ hệ thống đại lý.

## 16. Success Metrics
- **Latency Target**: Tìm kiếm có cache hit đạt độ trễ <200ms.
- **Memory Usage Limit**: <50MB overhead.
- **Cache Hit Ratio Target**: >80% sau khi warmup dự án.
- **Token Reduction Target**: Tiết kiệm tối thiểu 15% tokens đầu vào cho các pha Planning/Blueprint.

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Obsidian REST API bị ngắt kết nối hoặc timeout | Medium | Medium | Tự động fallback về Markdown Provider cục bộ và ghi log cảnh báo | Architect |
| Cơ sở dữ liệu SQLite cục bộ bị hỏng hoặc lỗi chỉ mục | High | Low | Cung cấp lệnh khôi phục tự động (restore) tái tạo từ tệp Markdown | Developer |

## 18. Technical Questions
- Làm thế nào để triển khai tìm kiếm tương đồng (similarity) hiệu quả trên SQLite mà không phụ thuộc vào thư viện ngoài? (Giải pháp: Sử dụng module SQLite Full-Text Search FTS5 có sẵn).

## 19. Open Decision Register
| Topic / Decision | Current Status (Resolved/Pending/Requires ADR/Requires Prototype/Requires Research) | Rationale & Next Steps |
| :--- | :--- | :--- |
| Định dạng của JSON cache file | Resolved | Sử dụng định dạng Key-Value phẳng với khóa là hash của câu truy vấn. |
| Sử dụng SQLite FTS5 cho tìm kiếm gần đúng | Pending | Cần làm bản mẫu thử nghiệm (Prototype) để kiểm tra tốc độ. |

## 20. ADR Detection
- **ADR Required**: Yes.
- **Rationale & Focus**: Đòi hỏi tạo tài liệu `ADR-012` ghi nhận quyết định kiến trúc lớp tri thức trung gian pluggable và cơ chế lưu cache.

## 21. Knowledge Update Impact
Identify which Project Memory layers will change:
- **project-summary**: Yes - Cập nhật thông số Knowledge Runtime.
- **architecture**: Yes - Thêm sơ đồ Provider Pattern.
- **modules**: Yes - Đăng ký gói `knowledge_runtime`.
- **lessons**: Yes - Ghi lại bài học về tối ưu hóa cache.
- **patterns**: Yes - Ghi nhận mô hình Provider.
- **ADR**: Yes - Thêm ADR-012.
- **SQLite**: Yes - Thêm cấu trúc bảng cache.
- **indexes**: Yes - Cập nhật tệp tin index.
- **vector metadata**: No.

## 22. Test Strategy Preview
- **Unit Tests**: test_api.py (kiểm tra các phương thức API chính), test_cache.py (kiểm tra invalidation và hit ratio).
- **Integration Tests**: test_integration.py (kiểm tra khả năng tích hợp của Coder và Planner với thư viện).
- **Compatibility Tests**: test_compatibility.py (kiểm tra khả năng tương thích ngược với cấu hình cũ).

## 23. Extension Impact
- **Extension UI Changes**: Bổ sung bảng hiển thị trạng thái chất lượng tri thức (orphan notes, broken links).
- **Affected ViewModels / Watchers**: State watcher cần quan sát thêm tệp `quality.json` mới sinh ra.

## 24. Complexity Estimation
- **Implementation Complexity**: Trung bình (Medium).
- **Estimated Refactoring Percentage**: ~25% mã nguồn liên quan đến project memory hiện hành.

## 25. Roadmap Alignment
- **Roadmap Phase**: Phase 2 của kế hoạch củng cố hệ thống tri thức.
- **Milestones**: Hoàn thành Core API (M1), Hoàn thành Obsidian/SQLite integration (M2).

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Làm thế nào để định cấu hình chuyển đổi giữa các Provider khác nhau? | Cấu hình sẽ được lưu trong tệp .agents/memory.config.json, quy định nhà cung cấp hoạt động chính (ví dụ: `markdown`, `sqlite`, `obsidian`, hoặc `vector_db`). |

## 27. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 28. Existing Project Context
- **Memory Source**: .agents/memory/project-summary.md và tệp tin cấu hình .agents/memory.config.json.
- **Existing Architecture Summary**: Hệ thống hiện tại có các script Python thực hiện quét và đồng bộ hóa bộ nhớ nằm trong thư mục .agents/runtime/scripts/project_memory/. Lớp tìm kiếm RAG hiện tại sử dụng REST API scroll của Qdrant hoặc tìm kiếm từ khóa thô trong markdown thông qua search.py và keyword_index.py. Chúng ta sẽ tái sử dụng và nâng cấp các mã nguồn này thành các lớp Provider cụ thể của Knowledge Runtime.

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk (Low/Med/High) | Relevance |
|---|---|---|---|---|---|---|---|
| RAG Searcher | skills/project-rag-search/scripts/search.py | Architect | `search()` | 80% | 20% | Low | Làm nền tảng cho lớp Vector DB Provider |
| Keyword Index | skills/project-memory-bootstrap/scripts/keyword_index.py | Developer | `match_keywords()` | 95% | 5% | Low | Tách từ khóa cho Markdown Provider |
| Memory Update | skills/project-memory-update/scripts/update.py | Developer | `update_lessons()` | 70% | 30% | Low | Cung cấp logic trích xuất bài học |

## 30. Solution Options Evaluated

### Option A: Thư viện Python nội bộ kết hợp CLI Wrapper (Khuyến nghị)
- **Overview**: Cài đặt Knowledge Runtime như một gói thư viện Python modular nằm trong .agents/skills/workflow-runtime/scripts/knowledge_runtime/. Các Skill khác import trực tiếp và CLI sẽ cung cấp giao diện command line.
- **Advantages**: Hiệu năng cực cao (<10ms cho import trực tiếp, <150ms cho CLI), không có overhead mạng, dễ dàng viết unit test độc lập.
- **Disadvantages**: Đòi hỏi các Skill hiện tại thay đổi cách import/gọi tài nguyên.
- **Complexity**: Low-Medium
- **Risk**: Low

### Option B: Dịch vụ HTTP API cục bộ (REST API Local Server)
- **Overview**: Khởi chạy một daemon server chạy ngầm ở localhost sử dụng FastAPI. Các Skill giao tiếp qua giao thức HTTP REST API.
- **Advantages**: Hoàn toàn độc lập với ngôn ngữ và runtime thực thi, dễ dàng tích hợp cho các extension IDE trong tương lai.
- **Disadvantages**: Overhead mạng làm tăng độ trễ, phức tạp trong việc quản lý daemon ngầm (start/stop), tăng khả năng xung đột cổng.
- **Complexity**: High
- **Risk**: Medium (Port conflict, daemon crash)

## 31. Solution Comparison Table
| Criteria | Option A (Khuyến nghị) | Option B |
|---|---|---|
| Complexity | Low-Medium | High |
| Risk | Low | Medium |
| Performance | Rất cao (<150ms CLI) | Trung bình-Cao (>250ms HTTP) |
| Maintainability | Rất cao | Trung bình |
| Compatibility | Rất cao (Tương thích ngược) | Cao |
| Future Scalability | Rất cao | Rất cao |
| Development Cost | Thấp | Cao |

## 32. Selected Solution
- **Choice**: Option A — Python-First Library with CLI Wrapper
- **Why Selected**:
  1. Mang lại hiệu năng tìm kiếm và cập nhật tri thức tối ưu nhất (hạn chế tối đa độ trễ do serialization).
  2. Không cần duy trì các tiến trình ngầm phức tạp trên hệ điều hành của người dùng, tránh được xung đột cổng mạng hoặc rủi ro sập tiến trình ngầm.
  3. Dễ dàng triển khai các Unit test độc lập trực tiếp từ Pytest.
- **Trade-offs Accepted**: Yêu cầu cập nhật mã nguồn của các Skill cốt lõi để chuyển hướng gọi tài nguyên từ trực tiếp sang thư viện.
- **Technical Debt**: Không tạo ra technical debt lớn; trái lại, nó sẽ xóa sạch các nợ kỹ thuật hiện tại về việc phân tán logic tìm kiếm và cập nhật bộ nhớ.
- **Risk Mitigation**: Cung cấp lớp tương thích ngược (Backward-Compatibility Adapter) để các lệnh cũ vẫn có thể thực thi bình thường mà không bị crash.

## 33. Risks & Assumptions
- **Risks**:
  - R-01: Đồng bộ hóa Obsidian có thể gặp xung đột ghi dữ liệu (race conditions). → *Mitigation*: Sử dụng cơ chế khóa ghi (lock file) nguyên tử tương tự như workflow.lock.
  - R-02: Cơ chế lập chỉ mục gia tăng có thể bị bỏ lỡ thay đổi nếu người dùng sửa file thủ công. → *Mitigation*: Sử dụng hash-check dựa trên kích thước file và thời gian chỉnh sửa mới nhất (mtime).
- **Assumptions**:
  - A-01: Hệ thống của người dùng đã cài đặt sẵn Python 3.11+.

## 34. Acceptance Criteria
- [ ] AC-01 (maps to FR-01): API hoạt động đúng với đầy đủ các phương thức. (Expected Test: test_api.py)
- [ ] AC-02 (maps to FR-02): Khả năng hoán đổi Provider linh hoạt. (Expected Test: test_providers.py)
- [ ] AC-05 (maps to FR-05): Tốc độ tìm kiếm cache hit đạt <200ms. (Expected Test: test_cache.py)

---

## 35. Final Planning Prompt

### Purpose
Lời gọi self-contained và đầy đủ thông tin nhất gửi tới Skill `brainstorming-to-plan` để xây dựng kế hoạch triển khai chi tiết cho **AIWF Knowledge Runtime** (v3.1 Upgrade).

### Problem Statement
Thiếu một lớp lưu trữ và truy vấn tri thức tập trung cho AIWF, dẫn đến trùng lặp logic tại các Skill và hạn chế khả năng tích hợp linh hoạt các nền tảng cơ sở dữ liệu (SQLite, Vector DB) hoặc công cụ ghi chú Obsidian.

### Objectives & Selected Solution
Xây dựng **AIWF Knowledge Runtime** theo **Phương án A**: Thư viện Python nội bộ kèm CLI Wrapper. API này sẽ phân tách rõ ràng các tầng: API giao tiếp, Provider lưu trữ (Markdown/SQLite/Obsidian), Cache lưu trữ đệm, và Index lập chỉ mục.

### Functional Requirements
- Triển khai API lớp tri thức ổn định.
- Tự động lập chỉ mục và lưu trữ liên kết ngược (Backlinks Graph).
- Xây dựng công cụ kiểm tra chất lượng tri thức (Knowledge Quality Analyzer) và bộ máy đề xuất (Recommendation Engine).
- Tích hợp lớp Knowledge Runtime vào vòng đời thực thi của các Skill hiện tại.

### Non-functional Requirements & Constraints
- Tốc độ tìm kiếm có cache <200ms.
- Hoạt động tương thích ngược hoàn hảo, không phá vỡ cấu trúc thư mục tài liệu `docs/` hiện có.

### Architectural Details
- Cấu trúc thư mục mới: `skills/knowledge-runtime/scripts/knowledge_runtime/`
- Tích hợp thông qua workflow_runtime.py và hook trong lớp orchestrator.

### Risks & Assumptions
- Tránh ghi đè dữ liệu Obsidian khi đồng bộ hai chiều.
- Xử lý mượt màng khi các dịch vụ bên ngoài (Qdrant, Obsidian) không sẵn sàng bằng cách fallback tự động về Markdown cục bộ.

### Verification Checklist
- [ ] docs/plans/FEAT-045_aiwf_knowledge_runtime_plan.md được tạo lập và phê duyệt.
- [ ] docs/designs/FEAT-045_aiwf_knowledge_runtime_blueprint.md được tạo lập và phê duyệt.
- [ ] Kiểm thử tự động (unit tests) phủ các tính huống cache hit, cache miss, fallback provider, và phân tích chất lượng tri thức thành công.
