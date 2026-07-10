---
feature_id: FEAT-013
feature_name: Refactor Project Memory and RAG Skills to Script-First Architecture
status: draft
stage: brainstorming
created_at: 2026-07-06
updated_at: 2026-07-06
previous_artifact: None
next_artifact: ../plans/FEAT-013_refactor_project_memory_script_first_plan.md
---

# Master Requirement Document – Refactor Project Memory and RAG Skills to Script-First Architecture

## 1. Feature ID & Name
- **Feature ID**: FEAT-013
- **Feature Name**: Refactor Project Memory and RAG Skills to Script-First Architecture

## 2. Original Idea
 completely redesign the following three Skills:
- project-memory-bootstrap
- project-memory-update
- project-rag-search
The goal is to migrate them from Prompt-Driven Skills into a Script-First Architecture similar to the existing Workflow Runtime Engine.
I want all deterministic logic moved into Python scripts. The AI should only decide WHEN to execute, interpret the returned information, summarize results, and continue the workflow.

## 3. Business Problem
- **Problem**: 
  - Các tệp `SKILL.md` của hệ thống Project Memory và RAG hiện tại có dung lượng quá lớn, chứa đầy các quy tắc phức tạp bằng ngôn ngữ tự nhiên để hướng dẫn LLM cách quét thư mục, phân loại thay đổi, tạo tệp Markdown/JSON, cập nhật SQLite và tạo kế hoạch đồng bộ vector database.
  - Điều này khiến LLM tiêu tốn một lượng token ngữ cảnh (prompt tokens) rất lớn mỗi lần nạp skill, đồng thời khiến hành vi của LLM trở nên thiếu nhất quán (không mang tính xác thực - non-deterministic), dễ bị lỗi logic khi cấu trúc dự án thay đổi.
  - Quá trình quét dự án diễn ra lặp đi lặp lại không hiệu quả dù Project Memory đã tồn tại.
- **Why it matters**: 
  - Gây lãng phí chi phí vận hành token LLM (đặc biệt khi ngữ cảnh phình to).
  - Tốc độ phản hồi chậm do LLM phải tự suy luận các tác vụ tính toán tĩnh.
  - Tỉ lệ lỗi trong quá trình duy trì cấu trúc bộ nhớ dự án tăng khi codebase lớn lên.
- **Who is affected**: Nhà phát triển sử dụng AI Workflow Framework và chính các tác nhân AI khi thực hiện các pha SDLC.
- **Expected outcome**: 
  - Dung lượng các tệp `SKILL.md` giảm ít nhất 90%.
  - Toàn bộ logic quét, tạo chỉ mục, phân tích và đồng bộ hóa do các kịch bản Python chịu trách nhiệm.
  - CLI thống nhất `aiwf memory` hỗ trợ tất cả các lệnh bộ nhớ.

## 4. Requirement Discovery
- **Functional Requirements**:
  - **FR-01**: Tạo gói Python mô-đun tại `runtime/scripts/project_memory/` chứa các module hỗ trợ: quét mã nguồn, phân tích cú pháp, trích xuất cấu trúc dự án, tạo markdown/JSON/SQLite, xây dựng đồ thị phụ thuộc và đồng bộ hóa vector.
  - **FR-02 (Bootstrap Engine)**: Kịch bản Python tự động nhận diện ngôn ngữ, framework, cấu trúc thư mục, module, API, entity và tạo các tệp `project-summary.md`, `architecture/overview.md`, và `memory-state.json`.
  - **FR-03 (Update Engine)**: Tính toán Git diff (hoặc timestamp), so khớp `file-map.json`, xác định phân lớp bị ảnh hưởng và cập nhật từng phần (incremental) cho `known-problems.md`, `vector-sync-plan.json`.
  - **FR-04 (RAG Search Engine)**: Trích xuất từ khóa, truy vấn chỉ mục cục bộ, đồ thị phụ thuộc và gọi Qdrant Vector DB qua API HTTP để trả về kết quả JSON có cấu trúc.
  - **FR-05 (CLI Interface)**: Hỗ trợ CLI `aiwf memory <subcommand>` (ví dụ: `bootstrap`, `update`, `search`).
  - **FR-06 (Session Integration)**: Các kịch bản Python tự động gọi các hàm điều phối session (`start`, `step`, `complete`, `fail`) của `workflow-runtime`.
  - **FR-07 (SKILL.md Reduction)**: Rút gọn các tệp `SKILL.md` cũ xuống dưới 50 dòng, loại bỏ toàn bộ quy tắc tạo markdown, JSON, SQLite hay phân tích, chỉ giữ lại Purpose, Input, Script invocation, Expected output, Boundary rules.
  - **FR-08 (Automated Testing)**: Viết test tự động bao quát các ca kiểm thử dự án trống, dự án Node/Go, cập nhật tăng cường, xóa tệp, tìm kiếm RAG và các tình huống lỗi.
- **Non-functional Requirements**:
  - **NFR-01 (Hiệu năng)**: Thời gian quét và cập nhật bộ nhớ phải dưới 5 giây đối với các dự án vừa và nhỏ.
  - **NFR-02 (Tương thích đa nền tảng)**: Hoạt động trơn tru trên Windows, Linux và macOS.
  - **NFR-03 (Tối ưu hóa token)**: Giảm tối thiểu 90% prompt token tiêu hao cho mỗi kỹ năng bộ nhớ.
- **Technical Constraints**:
  - **TC-01**: Sử dụng thư viện chuẩn của Python 3, không phụ thuộc vào các thư viện bên ngoài để tránh lỗi cài đặt.
  - **TC-02**: Gọi API HTTP của Qdrant thông qua `urllib.request` của Python thay vì thư viện client Qdrant bên ngoài.
  - **TC-03**: Duy trì tương thích ngược với các lệnh AI Skill cũ.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Làm thế nào để duy trì tương thích ngược với các lệnh cũ? | Các thư mục kỹ năng cũ vẫn được giữ nguyên nhưng tệp `SKILL.md` bên trong sẽ chỉ chứa lệnh gọi kịch bản CLI Python tương ứng. |
| Làm thế nào để gọi API Qdrant một cách gọn nhẹ? | Viết một module HTTP client tối giản bằng `urllib` của Python để thực hiện các yêu cầu GET/POST tới API REST của Qdrant tại cổng 6333. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: [project-summary.md](file:///Volumes/Kyle/AgentsProject/.agents/memory/project-summary.md)
- **Existing Architecture Summary**: Hệ thống hiện tại sử dụng kịch bản điều khiển [workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) bằng Python để quản lý trạng thái phiên `.session.json` và lưu trữ lịch sử sử dụng token vào cơ sở dữ liệu SQLite cục bộ `project_runtime.db`. Dự án có cấu trúc thư mục rõ ràng phân chia giữa các `skills` và `runtime` điều phối.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| workflow-runtime | [skills/workflow-runtime/](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/) | Quản lý trạng thái phiên, tính toán token, lưu trữ cơ sở dữ liệu SQLite cục bộ. Cung cấp API tích hợp cho các script bộ nhớ mới. |
| project-memory-bootstrap | [skills/project-memory-bootstrap/](file:///Volumes/Kyle/AgentsProject/skills/project-memory-bootstrap/) | Chứa kỹ năng khởi tạo bộ nhớ cần được tái cấu trúc. |
| project-memory-update | [skills/project-memory-update/](file:///Volumes/Kyle/AgentsProject/skills/project-memory-update/) | Chứa kỹ năng đồng bộ tăng cường cần được tái cấu trúc. |
| project-rag-search | [skills/project-rag-search/](file:///Volumes/Kyle/AgentsProject/skills/project-rag-search/) | Chứa kỹ năng tìm kiếm RAG cần được tái cấu trúc. |

## 9. Solution Options Evaluated

### Option A: Mở rộng CLI Workflow Runtime hiện có
- **Overview**: Tích hợp các lệnh bộ nhớ trực tiếp vào CLI chính `workflow_runtime.py` hiện tại dưới dạng các lệnh con (subcommands) mới.
- **Architecture**: Mở rộng parser của `workflow_runtime.py` và import các module con tại `runtime/scripts/project_memory/`.
- **Advantages**: Không cần thay đổi nhiều trong installer và script wrapper `aiwf`.
- **Disadvantages**: Làm phình to tệp điều khiển chính, trộn lẫn trách nhiệm quản lý phiên làm việc với công việc quét dự án/RAG.

### Option B: Công cụ CLI Memory độc lập (Selected)
- **Overview**: Xây dựng một kịch bản CLI riêng biệt tại `runtime/scripts/project_memory/cli.py` làm cổng tiếp nhận duy nhất cho các lệnh `memory`. CLI này sẽ import trực tiếp các module tiện ích từ `workflow-runtime` thông qua điều chỉnh `sys.path`.
- **Architecture**: `cli.py` tiếp nhận các subcommand và chuyển tiếp cho `bootstrap.py`, `update.py`, hoặc `search.py`. Nó tự động gọi các hàm quản lý session trong `workflow-runtime` để cập nhật tiến trình một cách nguyên tử.
- **Advantages**: 
  - Phân chia trách nhiệm rõ ràng (Separation of Concerns).
  - Tách bạch cấu trúc file nguồn giúp dễ dàng bảo trì và viết kiểm thử độc lập.
  - Tốc độ thực thi nhanh và an toàn.
- **Disadvantages**: Cần cập nhật nhẹ các tệp installer (`bootstrap.sh` và `bootstrap.ps1`) để định nghĩa lệnh gọi `aiwf memory`.

## 10. Solution Comparison Table
| Criteria | Option A | Option B (Selected) |
|---|---|---|
| Complexity | Trung bình | Thấp (Mã nguồn độc lập) |
| Risk | Trung bình (Dễ lỗi lan truyền) | Thấp |
| Performance | Cao | Cao |
| Maintainability | Trung bình | Rất cao |
| Compatibility | Cao | Cao |
| Future Scalability | Thấp | Rất cao |
| Development Cost | Thấp | Trung bình |

## 11. Selected Solution
- **Choice**: Option B — Independent CLI with Direct Module Import
- **Why Selected**: Tách biệt rõ ràng trách nhiệm giữa công cụ quản lý workflow và tri thức dự án. Cải thiện cấu trúc mã nguồn, nâng cao khả năng kiểm thử tự động, đồng thời vẫn giữ được sự tích hợp chặt chẽ về dữ liệu sử dụng token và tiến trình phiên làm việc.
- **Trade-offs Accepted**: Cần cập nhật lại các tệp kịch bản cài đặt hệ thống (`bootstrap.sh`/`bootstrap.ps1`) để tích hợp lệnh gọi mới.
- **Technical Debt**: Không có nợ kỹ thuật lớn phát sinh.
- **Risk Mitigation**: Đường dẫn tương đối và kiểm tra nền tảng sẽ được đóng gói trong một lớp helper dùng chung (`common.py` hoặc `filesystem.py`) để tránh các lỗi ký tự phân cách trên Windows.

## 12. Risks & Assumptions
- **Risks**:
  - R-01: Khác biệt môi trường chạy Python giữa các máy trạm dẫn đến lỗi import. → *Mitigation*: Sử dụng `sys.path.append` động để tìm thư mục gốc dự án và nạp gói `workflow-runtime`.
  - R-02: Lỗi phân đoạn và trích xuất dữ liệu của script không khớp chính xác với chỉ mục cũ. → *Mitigation*: Kiểm thử chặt chẽ định dạng đầu ra Markdown và JSON so với các tệp bộ nhớ mẫu hiện tại của dự án.
- **Assumptions**:
  - A-01: Máy trạm đã được cài đặt sẵn Python 3.

## 13. Acceptance Criteria
- [ ] Dung lượng các tệp `SKILL.md` của 3 kỹ năng được cắt giảm ít nhất 90% so với bản gốc.
- [ ] Lệnh CLI `aiwf memory bootstrap` chạy thành công, tự động khởi tạo bộ nhớ dự án từ số không và ghi đầy đủ tệp `project-summary.md` cùng `memory-state.json`.
- [ ] Lệnh CLI `aiwf memory update` tự động phát hiện tệp thay đổi từ Git diff, cập nhật `known-problems.md` tăng cường và sinh tệp `rag/vector-sync-plan.json`.
- [ ] Lệnh CLI `aiwf memory search` tìm kiếm chính xác các tài liệu bộ nhớ theo từ khóa, hỗ trợ fallback quét trực tiếp thư mục nếu bộ nhớ chưa được chỉ mục và trả về định dạng JSON chuẩn.
- [ ] Các lệnh trên tự động cập nhật tiến trình vào `.session.json` (ghi nhận logs và checkpoint tăng dần) thông qua API của `workflow-runtime`.
- [ ] Toàn bộ bộ test tự động chạy và vượt qua thành công trên cả macOS, Linux, và Windows.

---

## 14. Final Planning Prompt

### Purpose
Cung cấp đầy đủ thông tin yêu cầu cho kỹ năng `brainstorming-to-plan` để xây dựng một bản Kế hoạch Triển khai (Implementation Plan) chi tiết nhằm thực hiện tái cấu trúc hệ thống Project Memory và RAG Skills sang cấu trúc Script-First Architecture.

### Problem Statement
Hệ thống AI Workflow hiện tại có 3 kỹ năng quan trọng liên quan đến bộ nhớ dự án và RAG (`project-memory-bootstrap`, `project-memory-update`, `project-rag-search`) đang hoạt động theo cơ chế Prompt-Driven (chứa các hướng dẫn rất lớn trong tệp `SKILL.md`). Điều này gây lãng phí token ngữ cảnh lớn, làm chậm tốc độ phản hồi và hành vi không xác thực. Cần tái cấu trúc toàn bộ logic deterministic của 3 kỹ năng này sang ngôn ngữ Python để tối ưu hóa hiệu năng, giảm dung lượng prompt và chuẩn hóa hành vi hệ thống.

### Objectives & Selected Solution
- Thiết kế hệ thống CLI độc lập `aiwf memory` quản lý toàn bộ các tác vụ bộ nhớ và RAG.
- Triển khai gói mã nguồn Python mô-đun tại `runtime/scripts/project_memory/` tương thích đa nền tảng và không phụ thuộc thư viện ngoài.
- Rút gọn 3 tệp `SKILL.md` của các kỹ năng tương ứng xuống dưới 50 dòng, loại bỏ logic lập luận phức tạp của LLM.
- Tích hợp tự động tiến trình chạy của các script bộ nhớ với `workflow-runtime`.

### Functional Requirements
- Xây dựng CLI chính tại [runtime/scripts/project_memory/cli.py](file:///Volumes/Kyle/AgentsProject/runtime/scripts/project_memory/cli.py).
- Triển khai kịch bản khởi tạo bộ nhớ [bootstrap.py](file:///Volumes/Kyle/AgentsProject/runtime/scripts/project_memory/bootstrap.py).
- Triển khai kịch bản đồng bộ tăng cường [update.py](file:///Volumes/Kyle/AgentsProject/runtime/scripts/project_memory/update.py) sử dụng Git diff.
- Triển khai kịch bản tìm kiếm RAG [search.py](file:///Volumes/Kyle/AgentsProject/runtime/scripts/project_memory/search.py) gọi REST API của Qdrant Vector DB qua `urllib.request`.
- Tích hợp ghi nhận logs, token usage và checkpoint tự động vào [.session.json](file:///Volumes/Kyle/AgentsProject/.agents/.session.json) thông qua gói `workflow-runtime`.
- Tương thích ngược với các lệnh cũ của AI Skill Framework.
- Cập nhật các tệp tin hướng dẫn cài đặt và sử dụng: `README.md`, `INSTALL.md`, `USAGE.md`, và `CHANGELOG.md`.

### Non-functional Requirements & Constraints
- Tốc độ quét và đồng bộ tăng cường dưới 5 giây.
- Giảm thiểu 90% prompt token cho các tệp `SKILL.md`.
- Hoạt động ổn định trên cả Windows, Linux và macOS.

### Architectural Details
Gói mã nguồn Python `project_memory` bao gồm các tệp mô-đun:
- `cli.py`: Điểm tiếp nhận lệnh chính.
- `bootstrap.py`: Điều phối việc khởi tạo bộ nhớ dự án.
- `update.py`: Điều phối việc đồng bộ tăng cường bộ nhớ.
- `search.py`: Điều phối việc truy vấn RAG.
- `scanner.py`: Quét cấu trúc dự án và phát hiện ngôn ngữ/framework.
- `analyzer.py`: Phân tích chi tiết các thành phần lớp mã nguồn.
- `parser.py`: Trích xuất thông tin cấu trúc tệp tin.
- `markdown_writer.py`: Sinh nội dung các tệp markdown tri thức.
- `json_writer.py`: Sinh các tệp JSON chỉ mục và tệp cấu hình.
- `sqlite_writer.py`: Ghi thông tin chỉ mục vào SQLite cục bộ (nếu cần).
- `git_diff.py`: Tính toán các tệp tin thay đổi bằng lệnh Git CLI.
- `filesystem.py` và `common.py`: Xử lý tệp tin và đường dẫn chéo nền tảng.
- `vector_manifest.py`: Tạo phân đoạn tài liệu và đồng bộ hóa vector.
- `keyword_index.py`: Tìm kiếm và đối chiếu theo từ khóa cục bộ.
- `dependency_graph.py`: Bản đồ liên kết các thành phần dự án.

### Risks & Assumptions
- Đường dẫn chéo nền tảng (Windows vs UNIX) phải được giải quyết triệt để trong `filesystem.py`.
- Việc tích hợp module của `workflow-runtime` yêu cầu chèn động đường dẫn dự án vào `sys.path`.

### Verification Checklist
- [ ] docs/plans/FEAT-013_refactor_project_memory_script_first_plan.md được tạo và phê duyệt.
- [ ] docs/designs/FEAT-013_refactor_project_memory_script_first_blueprint.md được tạo và phê duyệt.
- [ ] Tất cả tiêu chí nghiệm thu được ánh xạ thành các ca kiểm thử tự động thành công.

---

> ⚠ The next Skill is `brainstorming-to-plan`.
> It must be invoked **manually** by the user.
> This Skill does NOT invoke it automatically.
