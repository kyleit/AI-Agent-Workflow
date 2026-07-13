# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.15.3] - 2026-07-13

### Added
- **Mandatory Entry Gateway Enforcement (FEAT-313)**:
  - Triển khai `WorkflowEntryGateway` bắt buộc toàn bộ các yêu cầu kỹ thuật tự nhiên phải đi qua `workflow_runtime.py workflow submit`.
  - Cập nhật quy tắc toàn cục `Workflow First Enforcement Policy` chặn đứng việc Agent tự viết code ngoài workflow context.
  - Ghi nhận nhật ký sự kiện đồng bộ vào `.agents/state/events.jsonl` tại root của state.

## [6.15.1] - 2026-07-13

### Fixed
- **Verification Gate (FEAT-401)**:
  - Khởi tạo thành công và lập báo cáo kiểm định chất lượng đạt trạng thái PASS cho Work Item FEAT-401 tại docs/verification/FEAT-401_verify.md.

## [6.15.0] - 2026-07-13

### Added
- **Workflow Supervisor & Skill Governance (FEAT-302 / FEAT-304)**:
  - Tái cấu trúc Orchestrator từ Resident Daemon sang mô hình Workflow Supervisor chạy theo phiên (session-based) an toàn.
  - Tích hợp ghi nhận nhật ký sự kiện Observability chi tiết vào `.agents/state/events.jsonl` (gồm workflow.started, phase.started, agent.started, agent.completed, phase.completed, workflow.completed).
  - Cập nhật CLI lệnh `aiwf orchestrator` hỗ trợ các subcommands: start, stop, status, follow, và agents.
  - Triển khai Skill Governance Engine kiểm duyệt vật lý sự tồn tại của tệp tin tài liệu (`docs/brainstorming/`, `docs/planning/`, `docs/blueprints/`) trước khi cho phép vượt qua các cổng kiểm soát trong chế độ autonomous.

## [6.14.2] - 2026-07-13

### Added
- **Session Runtime Redesign (FEAT-211)**:
  - Tái thiết kế Session Runtime Core chuyển đổi từ mô hình đa tiến trình daemon sang in-process async engine siêu nhẹ.
  - Tích hợp SQLite WAL Event Store lưu trữ dòng sự kiện lịch sử phục vụ event replay/recovery và audit trail.
  - Xây dựng Shared Session Context Engine bất biến kết hợp Copy-on-Write và Optimistic Concurrency Control (OCC) loại bỏ xung đột dữ liệu đa tác nhân.
  - Triển khai Scheduler & Bounded Worker Pool quản lý xếp hàng tác vụ và chống quá tải tài nguyên thông qua CPU throttling.
  - Triển khai Tool Executor cô lập tiến trình kết hợp validator toàn cục chặn cuộc gọi subprocess lậu ngoài luồng kiểm duyệt.
  - Thiết lập ranh giới phân quyền phân cấp Permission Boundary đa lớp (Global -> Session -> Agent -> Tool) chống privilege/scope escalation.
  - Xây dựng máy chủ Runtime API v3 JSON-RPC cùng Runtime SDK v3 Client và Adapter tương thích ngược v1/v2 phát cảnh báo di trú.

## [6.14.0] - 2026-07-13

### Added
- **Dynamic Agent Registry**:
  - Triển khai Dynamic Agent discovery và validation sử dụng JSON Schema (`agent.schema.json`).
  - Tự động biên dịch 41 file markdown agent sang tệp registry duy nhất `registry.json`.
  - Cập nhật quyền ghi `scoped-write` hợp lý cho Frontend, Backend, Database và Test Developer Agents.
- **TESTER Agent Ownership Enforcement**:
  - Monkey patch toàn cục `subprocess.run` và `subprocess.Popen` nhằm ngăn chặn mọi hoạt động thực thi test command trái phép (không có active test task hoặc được gán sai owner).
- **Autonomous Workflow & Adaptive Capacity Planning (v1)**:
  - Tích hợp Confidence Gates (yêu cầu >= 95% cho brainstorm/planning/blueprint).
  - Triển khai Adaptive Team Planner và Capacity Controller giúp điều phối tối ưu concurrency dựa trên CPU/RAM và tự động tuyển dụng (dynamic recruitment) specialists.

## [6.13.2] - 2026-07-13

### Fixed
- **OS File Locking & Process Resiliency (FEAT-051 / Multi-Agent Safety)**:
  - Khôi phục công cụ an toàn ghi đa tác nhân [safe_multi_agent_writes.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/safe_multi_agent_writes.py) và các tệp kiểm thử đi kèm.
  - Sửa đổi cơ chế khóa `OSFileLock` trong [session.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/session.py) để cô lập cờ bypass lock chỉ kích hoạt trong môi trường kiểm thử pytest (`PYTEST_CURRENT_TEST`), đảm bảo lock vật lý luôn hoạt động trên production.
  - Bổ sung cơ chế khóa tiến trình `OSFileLock` cho `LeaseManager` trong `safe_multi_agent_writes.py` nhằm loại bỏ rủi ro tranh chấp ghi file đĩa đồng thời trên Windows.
  - Bổ sung cơ chế thử lại (atomic replace retry loop) tối đa 5 lần cho `write_json_atomic` tăng cường khả năng phục hồi lỗi khóa tệp Windows.
  - Dọn dẹp triệt để các tiến trình mồ côi (zombie python tasks) giúp tái tạo môi trường làm việc sạch.
  - Khắc phục 18 bài kiểm thử bị lỗi liên quan đến đường dẫn import chéo và mock liveness PID sai lệch.

## [6.13.1] - 2026-07-13

### Fixed
- **Incident Recovery & Hardening (FEAT-118)**:
  - Khắc phục sự cố tràn tiến trình Python gây OOM bằng cách tối ưu hóa kết nối SQLite trong [db.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/db.py) (tránh truy vấn khóa độc quyền ghi khi đọc dữ liệu).
  - Tích hợp kiểm tra PID kết hợp `process_create_time` qua `psutil` trong [workflow_runtime.py](file:///e:/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) nhằm loại bỏ lỗi nhận diện sai tiến trình trùng lặp PID trên Windows.
  - Áp dụng cơ chế nhóm Windows Job Object để tự động dọn dẹp các tiến trình con khi tiến trình cha daemon bị kết thúc.
  - Tự động bỏ qua (bypass) các cổng phê duyệt trung gian (`blueprint_approval`) khi kích hoạt chế độ tự động `autonomous_delivery`, ngoại trừ cổng kiểm soát phát hành (`release_approval`).
  - Hoàn thiện lập lịch thông minh Adaptive Team Planner và giới hạn tài nguyên tính toán cho `RuntimeScheduler`.

## [6.13.0] - 2026-07-12

### Added
- **Autonomous Delivery Mode (FEAT-116)**:
  - Triển khai cờ khởi chạy CLI `--autonomous` cho phép tự động bypass các cổng phê duyệt thủ công trung gian đối với các hành động thông thường (normal writes/compiles/tests).
  - Tích hợp tính năng tự động ghi nhận thuộc tính `autonomous_delivery` và tính toán động `progress_percentage` trong pha lưu trữ phân tách Pure Split State.
  - Tích hợp nhãn trạng thái `⚡ AUTONOMOUS DELIVERY` động và thanh tiến độ thực thi trực quan trên Visualizer Sidebar.
  - Bổ sung quy tắc theo dõi và thông báo tiến độ kiểm thử chạy ngầm (background tests) mỗi 5% tiến trình vào chính sách kiểm thử [AI_RULES.md](file:///e:/AgentsProject/AI_RULES.md).

## [6.12.0] - 2026-07-12

### Added
- **Quality & Quality Governance Upgrade (DDD, Clean Architecture & Code Size Governance)**:
  - Triển khai **Code Size Policy Governance** phân tích AST Python và bracket-balancing Go, tự động cảnh báo hoặc báo lỗi cứng khi kích thước file/class/function vượt ngưỡng quy định.
  - Tích hợp đề xuất SRP Refactoring khuyến cáo cách trích xuất hàm và phân rã tệp tin vi phạm.
  - Triển khai **DDD & Clean Architecture Validator** quét dependency imports tự động cho Go và Python, tính toán điểm số tuân thủ kiến trúc (yêu cầu tối thiểu 95/100).
  - Tích hợp cổng kiểm soát chất lượng kiến trúc và Code Size vào pha Debug & Verification của `validation_runner.py`.
  - Nâng cấp Visualizer Dashboard Webview bổ sung tab **Code Size** thể hiện Neon status (PASSED/FAILED), top 5 vi phạm lớn nhất và các đề xuất SRP refactor trực quan.
  - Tái cấu trúc thành công Golang Wails App tại thư mục `desktop/` chuyển sang kiến trúc DDD chuẩn (`domain`, `application`, `infrastructure`, `delivery`), loại bỏ hoàn toàn các cấu trúc file phẳng cũ.

## [6.11.0] - 2026-07-12

### Added
- **FEAT-112: Resident Orchestrator Service & Dynamic Subagent Runtime**:
  - Triển khai tiến trình ngầm (daemon/service) trú đóng dài hạn luôn luôn hoạt động.
  - Tích hợp tính năng tự động khởi chạy service qua sự kiện khởi tạo workspace.
  - Xếp hàng và nhận chỉ thị phi đồng bộ ngoài luồng Command Inbox phản hồi < 100ms.
  - Phân tích đồ thị DAG tác vụ để sinh động và thu hồi Subagents nhàn rỗi (ephemeral workers).
  - Tích hợp WebSocket trực tiếp vào Visualizer Dashboard để cập nhật trạng thái động của daemon.

## [6.10.0] - 2026-07-12

### Added
- **FEAT-111: Hierarchical Multi-Agent Runtime Platform Foundation**:
  - Triển khai bộ điều phối phân cấp đa tác nhân chạy nền phi block với hàng đợi Command Inbox.
  - Hỗ trợ lập lịch song song thực sự (Real Parallel Scheduler) tối đa 6 tác vụ chạy đồng thời.
  - Triển khai cơ chế cách ly tiến trình (Worker Process Isolation) cùng dấu hiệu sống Heartbeats.
  - Quản lý vòng đời uỷ quyền thời gian thực (`authorization.json` tự động hết hạn).
  - Tích hợp sâu vào bảng quản trị giao diện Visualizer và loại bỏ hoàn toàn `.session.json` cũ.

## [6.9.0] - 2026-07-12

### Added
- **AIWF OS v2 Core Upgrade**:
  - Triển khai động cơ thực thi liên tục và 4 chế độ chạy (Step, Sprint, Program, Objective).
  - Tích hợp hàng đợi thực thi bền vững và phục hồi điểm kiểm soát SQLite.
  - Tích hợp lớp giám sát tự trị và tự chữa lành (Self-Healing) cho AIWF OS v2.
  - Thiết kế và phân rã lộ trình đám mây AIWF Cloud (FEAT-201 đến FEAT-210) cùng báo cáo đánh giá chiến lược, khung quản trị và kiến trúc North Star cho 5 chương trình Cloud chính.

## [6.8.0] - 2026-07-12

### Added
- **Visual Intelligence Runtime (VIR) Integration & Relocation**:
  - Di chuyển mã nguồn và tệp tests của VIR Runtime vào mô hình Skill đóng gói (Publishable Skill Package) tại `skills/vir-runtime/`.
  - Tạo tệp entry-point chính thức `skills/vir-runtime/scripts/vir.py` hỗ trợ chạy CLI đa nền tảng và phân giải import tương đối an toàn.
  - Tích hợp điều phối pha VIR Visual QA vào workflow orchestrator trung tâm `skills/software-development-workflow/SKILL.md`.
  - Đăng ký và đồng bộ các Skill mới (`vir-runtime`, `vir-investigate`, `vir-verify`, `vir-memory-update`) trong manifest và catalogs (`MANIFEST.json`, `SKILLS.md`).
  - Triển khai quy trình tự động hóa xuất bản thông qua lệnh **`make publish-github`** để đồng bộ hóa mã nguồn sang GitLab/GitHub và cập nhật liên kết submodule **`public_export`** của dự án cha.

## [6.7.0] - 2026-07-11

### Added
- **FEAT-054: Build update-source and Interactive Project Initialization**:
  - Triển khai lệnh CLI `aiwf update-source` hỗ trợ kiểm tra và cập nhật an toàn mã nguồn framework trung tâm qua Git fast-forward-only.
  - Triển khai lệnh CLI `aiwf init` hỗ trợ bộ câu hỏi tương tác wizard 18 phần, sinh tệp tin cấu hình dự án `.agents/project.config.json` và tệp profile `.agents/PROJECT_PROFILE.md` tự động.
  - Tích hợp bộ khuyến nghị stack thông minh RecommendationEngine và ScaffoldPlanner thực thi tạo cấu trúc thư mục chuẩn.

## [6.6.2] - 2026-07-11

### Fixed
- **FIX-026: Add bootstrap, init, and test Commands to AIWF CLI Wrapper**:
  - Bổ sung các lệnh con `bootstrap`, `init`, và `test` vào PowerShell wrapper CLI toàn cục (`bootstrap.ps1`).
  - Hỗ trợ gọi trực tiếp trình cài đặt môi trường (`aiwf bootstrap`), khởi tạo phiên làm việc mới (`aiwf init`) và chạy bộ kiểm thử/xác thực tĩnh (`aiwf test [args...]`).
  - Cập nhật tài liệu hướng dẫn nhanh Show-Help trong wrapper CLI.

## [6.6.1] - 2026-07-11

### Added
- **QUICK-029: Permanent Testing Architecture Rules & CI Validation**:
  - Ban hành Quy định cấu trúc thư mục kiểm thử vĩnh viễn (`smoke/`, `unit/`, `integration/`, `concurrency/`).
  - Di chuyển toàn bộ 35 tệp tin test và gắn thẻ marker pytest tương ứng khớp 100% với tên thư mục chứa.
  - Bổ sung lệnh CLI `aiwf test validate` để tự động kiểm tra tĩnh cấu trúc thư mục, marker pytest, tính đầy đủ của impact mapping, trùng lặp file và obsolete mappings.
  - Định cấu hình `pythonpath` trong `pytest.ini` giải quyết triệt để vấn đề phân giải import đường dẫn tương đối trong các thư mục kiểm thử lồng nhau.

## [6.6.0] - 2026-07-11

### Added
- **FEAT-050: Lightweight Runtime Initialization and Runtime Dependency Resolver**:
  - Tái cấu trúc kỹ năng `initialize-workflow` thành bộ khởi tạo siêu nhẹ (<800ms, loại bỏ hoàn toàn các lệnh kiểm tra công cụ CLI, quét workspace, nạp full bộ nhớ và kết nối RAG).
  - Bổ sung bộ giải quyết phụ thuộc thời gian chạy **Runtime Dependency Resolver** (`dependency_resolver.py`) hỗ trợ quét và xác thực khai báo `runtime_requirements` của các kỹ năng.
  - Bổ sung bộ quản lý đồ thị công cụ và máy trạng thái công việc **Task Dependency Graph & State Machine** (`task_orchestrator.py`) kiểm soát chặt chẽ 19 trạng thái công việc và ngăn chặn các phím tắt chuyển trạng thái bất hợp lệ.
  - Cấu hình cổng kiểm soát hoàn thành pha **Phase Completion Gate** yêu cầu 100% độ bao phủ công việc và các tiêu chí chất lượng nghiêm ngặt trước khi chuyển pha.
  - Bổ sung các lệnh CLI hữu ích `deps inspect/validate/resolve/doctor/fix` và `task graph/state/next` vào `workflow_runtime.py`.
  - Đồng bộ cập nhật khai báo `runtime_requirements` cho toàn bộ 52 kỹ năng trong hệ thống.
  - Biên soạn tài liệu hướng dẫn phát triển tích hợp [Runtime Dependency Resolver Guide](docs/guides/runtime-dependency-resolver.md).

## [6.5.2] - 2026-07-09

### Added
- **QUICK-028: Add Provider and Sync Commands to Wrapper CLI**:
  - Bổ sung lệnh con `provider` và `sync` trực tiếp vào wrapper `aiwf` (Bash & PowerShell) để gọi nhanh các tác vụ quản lý tri thức.
  - Hỗ trợ lệnh viết tắt tiện lợi `aiwf sync <provider_name>` để đồng bộ hóa nhanh sang Obsidian.

## [6.5.1] - 2026-07-09

### Added
- **QUICK-028: Upgrade Quick Feature & Quick Fix into Blueprint-Ready Mini Plans**:
  - Làm giàu các mẫu tài liệu đặc tả ở Phase 1 của `quick-feature` và `quick-fix` thành các bản **Mini Plan** hoàn chỉnh chứa đầy đủ 19 mục thông tin hoạt động, ràng buộc kiến trúc, kiểm tra phụ thuộc và ma trận xử lý lỗi.
- **FIX-024: Missing Obsidian Folder Mappings**:
  - Bổ sung cấu hình mặc định trong `provider_manager.py` và `.agents/memory.config.json` để đồng bộ hóa đầy đủ 11 thư mục tri thức dưới `docs/` sang Obsidian.
  - Phân loại tri thức chính xác theo bản chất: QUICK specs ➔ `Brainstorming`, FIX specs ➔ `Plans`, các tài liệu chuyên biệt khác ➔ `Prompts`, `Verification`, `Debug`, `Archive`.

## [6.5.0] - 2026-07-09

### Added
- **QUICK-023: Ensure New Skills Always Generate a Complete AIWF Skill Skeleton**:
  - Thêm chính sách bắt buộc `Mandatory Skill Skeleton Policy` vào tệp quy tắc trung tâm `AI_RULES.md`.
  - Cấu hình kỹ năng Thiết kế (`skills/plan-to-blueprint/SKILL.md`) để từ chối và báo lỗi xác thực nếu bản thiết kế tạo kỹ năng mới mà không định nghĩa đầy đủ tệp `SKILL.md`.

## [6.4.2] - 2026-07-09

### Added
- **QUICK-022: Upgrade plan-to-blueprint Skill to v3.2 (Complete Implementation Contract)**:
  - Đồng bộ hóa 100% dữ liệu thiết kế giữa hai định dạng Markdown và JSON (`FEAT-XXX_blueprint.json`).
  - Bổ sung cấu trúc gói thực thi lập trình `implementation_packages` vào tệp JSON thiết kế để hỗ trợ hạ nguồn lập trình tự động hóa.
  - Mở rộng chi tiết thiết kế lớp (Class Contracts), thiết kế lưu trữ (Storage Design), CLI và tích hợp.

## [6.4.1] - 2026-07-09

### Added
- **QUICK-021: Upgrade plan-to-blueprint Skill into an Implementation Contract Generator**:
  - Nâng cấp kỹ năng Thiết kế (`skills/plan-to-blueprint/SKILL.md`) hỗ trợ tạo Technical Design Blueprint v3.2 với 13 phần phân tích mới.
  - Hỗ trợ xuất đồng bộ tệp thiết kế có cấu trúc JSON (`FEAT-XXX_blueprint.json`) giúp hạ nguồn triển khai nhanh chóng.
  - Cấu hình `skills/blueprint-to-implementation/SKILL.md` để ưu tiên đọc tệp JSON thiết kế trước khi bắt đầu lập trình.

## [6.4.0] - 2026-07-09

### Added
- **QUICK-020: Upgrade quick-feature Skill Based on QUICK-018 Review**:
  - Nâng cấp kỹ năng Phát triển nhanh (`skills/quick-feature/SKILL.md`) hỗ trợ tạo đặc tả Mini Spec v3.2 với 7 phần bắt buộc nâng cao chất lượng.
  - Phân định scope rõ ràng (In/Out/Not Modified/Future Work) và cấm tuyệt đối sinh đường dẫn tuyệt đối trong tài liệu spec.

## [6.3.9] - 2026-07-09

### Added
- **QUICK-019: Upgrade brainstorming-to-plan Skill into an Execution Planning Engine**:
  - Nâng cấp kỹ năng Lập kế hoạch (`skills/brainstorming-to-plan/SKILL.md`) hỗ trợ tạo Execution Plan v3.2 với 11 phần phân tích mới.
  - Hỗ trợ xuất đồng bộ tệp kế hoạch có cấu trúc JSON (`FEAT-XXX_plan.json`) giúp các pha hạ nguồn nạp dữ liệu nhanh chóng.
  - Cấu hình `skills/plan-to-blueprint/SKILL.md` để ưu tiên đọc tệp JSON kế hoạch trước.
  - Sửa lỗi đường dẫn tương đối trong tất cả các tệp kỹ năng.

## [6.3.8] - 2026-07-09

### Added
- **FEAT-046: Upgrade Brainstorming Skill to v3 (Master Requirement Discovery)**:
  - Nâng cấp mẫu tài liệu Động não (`skills/brainstorming/SKILL.md`) hỗ trợ 14 phần phân tích tri thức mới phục vụ hạ nguồn.
  - Tinh giản tệp hướng dẫn `skills/brainstorming-to-plan/SKILL.md` và `skills/plan-to-blueprint/SKILL.md` để Planner và Architect không phải phân tích lại.

## [6.3.7] - 2026-07-09

### Fixed
- **Gemini Cache Discount Cost Calculation**: Fixed token accounting in `parse_transcript` and `sync_request_history` of `context.py` to calculate accurate accumulated Gemini cost by applying a 75% prompt caching hit discount.
- **Memory & RAG Telemetry Sync**: Updated `get_workflow_summary` in `db.py` to fetch, aggregate, and return `memory_hit_ratio` and `rag_hit_ratio` to the UI provider.

---

## [6.3.6] - 2026-07-08

### Added
- **FEAT-029: Project/Global Usage Scope Aggregation & Normalization Fix**:
  - Hỗ trợ lọc thống kê sử dụng token và chi phí API chính xác theo từng mã dự án riêng biệt (`project_id`).
  - Hỗ trợ câu lệnh `usage normalize` để tự động dọn dẹp, chuẩn hóa và sửa đổi các số liệu token rác/khổng lồ của các phiên cũ về mức thực tế.
- **FEAT-030: Config-driven Telemetry & Cost Warning Thresholds**:
  - Nạp động cấu hình các ngưỡng tỷ lệ phần trăm đầy Context và cảnh báo chi phí tích lũy từ tệp cấu hình dự án.
- **FEAT-031: Redesigned AIWF Context Status Visualizer UX**:
  - Phân tách giao diện Footer hiển thị thông số sử dụng thành 3 thẻ card riêng biệt: **Context Analytics**, **Accumulated API Usage**, và **Efficiency & Optimization**.
  - Trực quan hóa trạng thái `🟢 Healthy` trung tính, không sử dụng hộp cảnh báo hay biểu tượng khẩn cấp gây hiểu lầm.
  - Căn lề dọc hoàn hảo cho các biểu tượng cảnh báo bên trong Alert Boxes.


## [6.3.5] - 2026-07-08

### Added
- **FEAT-027: Investigate and Fix AIWF Runtime Token Accounting**:
  - Khắc phục các giá trị token không nhất quán và không hợp lý trên bảng điều khiển bằng cách sửa đổi logic phân tích cú pháp transcript.
  - Tách biệt dữ liệu Active Context (chỉ đại diện cho kích thước context hoạt động) và các số liệu tích lũy (Input/Output/Cost/Request).
- **FEAT-028: Pure Split State Management**:
  - Loại bỏ hoàn toàn tệp tin trạng thái lớn `.agents/.session.json` để chuyển hẳn sang sử dụng cơ chế lưu trữ phân tách (Pure Split State) trong thư mục `.agents/state/`.
  - Giảm thiểu I/O đĩa thừa, tránh lỗi tranh chấp ghi khóa tệp và tối ưu hóa tốc độ khởi tạo.

## [6.3.4] - 2026-07-08

### Fixed
- **FIX-018: Standardize generic workflow templates and auto-generate actual configuration files**:
  - Chuyển đổi các tệp mẫu cấu hình `release.config.json` và `workflow.config.json.template` thành dạng tổng quát (`single` project_type).
  - Tích hợp logic tự động sinh tệp cấu hình thực tế cho dự án đích khi chạy lệnh `discover`.
  - Loại bỏ trường dư thừa `feature_prefix` trong tất cả cấu hình mẫu và script runtime.
  - Thêm quy tắc an toàn bảo mật `Absolute Path Prohibition Policy` vào `AI_RULES.md` ngăn chặn rò rỉ username và đường dẫn tuyệt đối khi push Git.

## [6.3.3] - 2026-07-08

### Added
- **FEAT-025: Project-specific Workflow Templates & Release Configuration**:
  - Hỗ trợ cơ chế cấu hình quy trình Git Flow (development_branch, release_branch, feature_prefix, sync_method) tùy biến riêng cho từng dự án thông qua `.agents/workflow.config.json`.
  - Hỗ trợ Release Pipeline tùy biến thông qua custom commands cho từng module bị ảnh hưởng và custom commands global.
  - Tự động hóa các tác vụ Git Flow (merge/rebase) và release pipeline shell commands trong `release_manager.py`.

## [6.3.0] - 2026-07-08

### Added
- **QUICK-015: Upgrade skill-self-verification into a Behavioral Acceptance Testing (BAT) Skill**:
  - Nâng cấp bộ xác thực Skill sang kiểm thử hành vi thực tế (Behavioral Acceptance Testing - BAT).
  - Tích hợp giả lập User Personas đa nhân vật, sinh Simulated Conversation Transcript tương tác với các Cổng kiểm soát (Gates) và Prompts.
  - Tự động so sánh git diff Trước vs Sau (**Before vs After**) cho các Skill được chỉnh sửa.
  - Đo lường đánh giá UX Review, Productivity Impact và Token/API Cost.
  - Xuất báo cáo BAT nghiệm thu đầy đủ 12 chương mục chất lượng cao dưới `docs/verification/`.
- **FIX-017: Fix Orchestrator Routing & Blueprint Enforcement**:
  - Khắc phục lỗi Orchestrator tự ý code bỏ qua blueprint. Tự động dispatch sang `quick-fix`/`quick-feature`/`brainstorming` nếu phát hiện và tuân thủ rule/guide từng Phase.
  - Chặn cứng Phase 6 (Implementation) từ CLI nếu tệp Design Blueprint tương ứng chưa được phê duyệt (`blueprint.approved == True`).

## [6.2.0] - 2026-07-08

### Added
- **QUICK-013: Stricter Blueprint Generation**:
  - Nâng cấp `plan-to-blueprint` Skill để Technical Design Blueprint đóng vai trò là hợp đồng triển khai (Implementation Contract) chặt chẽ.
  - Áp dụng các quy tắc tự kiểm tra nghiêm ngặt: cấm link `file://` và đường dẫn tuyệt đối, yêu cầu tương thích ngược, enum an toàn cho `permission_mode`, xác thực đường dẫn pseudo-code, và mô tả đầy đủ acceptance criteria & extension changes.
- **FIX-016: Fix aiwf Git Repository Detection for Worktrees/Submodules**:
  - Khắc phục sự cố cài đặt, cập nhật, và chẩn đoán framework (`install`, `update`, `doctor`) không hoạt động trên Git worktrees, submodules (nơi `.git` là một tệp văn bản) và khi chạy từ thư mục con lồng nhau.
  - Sử dụng `git rev-parse --is-inside-work-tree` và `git rev-parse --show-toplevel` làm nguồn dữ liệu tin cậy nhất để tự động phát hiện project root và di chuyển vị trí thực thi.

## [6.1.0] - 2026-07-08

### Added
- **FEAT-022: Split Runtime State, Optimize Initialize Workflow, and Update Extension**:
  - Tái cấu trúc cơ chế lưu trữ trạng thái: Tách tệp tin `.session.json` monolit thành 8 file trạng thái con chuyên biệt trong `.agents/state/` (`context.json`, `workflow.json`, v.v.).
  - Triển khai lớp đồng bộ hai chiều (Aggregate & Deconstruct) bảo đảm tương thích ngược với các Agent đời cũ.
  - Tối ưu hóa tốc độ khởi động `initialize-workflow` bằng cơ chế kiểm tra cache vân tay dự án (Project Fingerprint SHA-256), giảm thời gian tải xuống dưới 50ms.
  - Cập nhật VS Code Extension watch thư mục `state/` để ghép ViewModel in-memory và live update giao diện mượt mà không nhấp nháy.
  - Bổ sung 5 lệnh CLI quản trị trạng thái mới: `context`, `rules status`, `state status/recover/validate`.

## [6.0.0] - 2026-07-08

### Added
- **FEAT-021: Convert Deterministic Skills to Script-First Execution**:
  - Tách toàn bộ logic kiểm tra/thẩm định mang tính chất thủ tục (init, resume, project stack discovery, project memory bootstrap/sync/search, env health, test runner, verify checklist, release gates) thành các script Python chạy tập trung.
  * Bổ sung các lệnh CLI JSON-returning mới: `discover`, `classify`, `memory bootstrap/update/search`, `env health`, `validate artifact/blueprint/session`, `debug run`, `verify run`, `release plan/execute`.
  * Viết bộ kiểm thử tự động `test_script_first.py` bao quát toàn bộ 17 kịch bản nghiệp vụ đặc thù.
  * Cập nhật đặc tả phân nhóm Group A (Script-First), Group B (Hybrid), Group C (LLM-driven) trong `SKILLS.md` và `AI_RULES.md`.

## [5.2.1] - 2026-07-07

### Added
- **FIX-014: Orchestrator Scope Correction (Parallel Only During Implementation)**:
  - Giới hạn lựa chọn chạy song song (Parallel execution) chỉ kích hoạt khi bắt đầu pha Triển khai (Implementation) sau khi đã duyệt Blueprint (checkpoint >= 5).
  - Các pha trước đó (discovery, brainstorming, planning, blueprint) và pha release phía sau bắt buộc chạy tuần tự (Sequential).
  - Nâng cấp CLI `workflow_runtime.py` từ chối kích hoạt song song và trả về mã lỗi `1` nếu checkpoint < 5.
  - Bổ sung 3 trường trạng thái mới (`implementation_execution_mode`, `parallel_allowed_phase`, `parallel_allowed`) vào tệp cấu hình và đồng bộ hóa qua nhịp tim hệ thống.
  - Cập nhật tài liệu tương tác `interactive-docs` bổ sung quy trình điều phối Orchestrator, đồng thời sửa lỗi gập vỡ giao diện tab trên mobile bằng bố cục lưới 2x2.

## [5.2.0] - 2026-07-07

### Added
- **FEAT-016: Interactive CLI & Workflow Prompts via IDE Dialogs**:
  - Tích hợp hàm `prompt_select` tại `utils.py` hiển thị thẻ XML tương tác `<interactive_prompt>` giúp Agent nhận diện và mở giao diện bảng đối thoại `ask_question` trên IDE thay vì nhập tay trong CLI.
  - Tự động phát hiện môi trường kiểm thử (bằng `TESTING=1` và `select.select` trên `stdin`) để tránh bị treo trong các tiến trình con unit tests.
  - Thay thế toàn bộ cổng gõ tay tương tác (chọn chế độ phân quyền và cảnh báo unrestricted) trong `workflow_runtime.py` bằng bảng đối thoại trực quan.
  - Bổ sung Section 16 (Interactive CLI Prompts Bridge Policy) và cập nhật Section 1, 14 trong `AI_RULES.md` để Agent bắt buộc sử dụng `ask_question`.

## [5.1.3] - 2026-07-07

### Added
- **QUICK-007: Interactive Docs & Workflow Simulator Website & Extension Tweak**:
  - Xây dựng một trang web tài liệu tĩnh (HTML/CSS/JS) chạy Client-side, tích hợp thông tin của 19 skills và hướng dẫn chi tiết theo 3 quy trình chính (Standard, Quick Feature, Quick Fix).
  - Tích hợp **Interactive Workflow Simulator** mô phỏng chạy CLI và gác duyệt của 3 quy trình.
  - Thiết kế Responsive (hỗ trợ Tablet và Mobile với Menu hamburger và sticky header).
  - Thiết kế thanh cuộn Neon scrollbar giống hệt extension và cố định chiều cao Terminal di động là 400px với tính năng tự động cuộn xuống cuối (scroll to bottom).
  - Thêm 2 nút liên kết kèm biểu tượng chính thức của VS Code ribbon và Puzzle piece dẫn tới 2 extension: **Visualizer (VS Code)** trên Marketplace và **Visualizer (Open VSX)** trên Open VSX Registry.
  - Di chuyển website sang thư mục riêng `interactive-docs/` ngoài thư mục `docs/`.
  - Tích hợp `interactive-docs/` vào quy trình xuất bản `make export` sang `public_export`.
  - Loại trừ thư mục `screenshots` kiểm thử ra khỏi Git thông qua `.gitignore`.
  - **VS Code Extension (v1.0.30)**: Tích hợp nút **Docs** (mở trang tài liệu tĩnh) kèm biểu tượng quyển sách mở vào header webview của extension.


## [5.1.2] - 2026-07-07

### Fixed
- **FIX-012: Auto-Sync Conversation ID on Rollover**:
  - Tự động trích xuất `conversationId` từ biến môi trường `ANTIGRAVITY_SOURCE_METADATA` trong hàm `update_context_health` của `workflow_runtime.py`.
  - Đồng bộ kịp thời và ghi đè trực tiếp `conversation_id` mới vào `.agents/.session.json` bất cứ khi nào bất kỳ thao tác nào của CLI Runtime được gọi.
  - Khắc phục triệt để lỗi tính toán Fallback Token Estimation bị giữ ở mức 85% của thread cũ khi chuyển sang hội thoại mới.
  - Khôi phục subcommand `compact` và `permission` trong `workflow_runtime.py` bị mất do thao tác checkout.

### Added
- **Global Rule 6: Mandatory SDLC Skill Binding**:
  - Bổ sung quy tắc bắt buộc mọi hoạt động thay đổi mã nguồn phải diễn ra trong phạm vi của một SDLC Skill tương ứng (`quick-fix`, `quick-feature`), cấm tự ý sửa đổi file trực tiếp trong `AI_RULES.md`.

## [5.1.1] - 2026-07-07

### Fixed
- **FIX-011: Prevent Session Drift on Memory Sync**:
  - Modified session helpers in `runtime/scripts/project_memory/common.py` to check the active skill before modifying workflow routing fields.
  - Prevents the visualizer from jumping back and forth to step 2 when memory updates are executed ngầm as side effects (background/unrelated steps).
  - Preserves RAG and memory health syncing in the session metadata on completion.

## [5.1.0] - 2026-07-07

### Added
- **Unrestricted Mode (AI_RULES.md Section 15)**:
  - Added a 3rd permission level "Unrestricted Mode" which bypasses all approval gates.
  - Implemented a Two-Factor Confirmation Gate requiring CLI input `CONFIRM_UNRESTRICTED` to unlock.
- **Session Durability (Recovery & Backup Strategy)**:
  - Added automatic backup `.session.json.bak` before saving.
  - Implemented Self-Healing in `load_session()` to automatically restore from `.bak` if the main session file is corrupted, empty, or fails JSON parsing.
- **CLI Permission Inspection Subcommand**:
  - Added `permission` command to `workflow_runtime.py` to print a structured layout mapping common actions to status (`ALLOWED` or `REQUIRED_APPROVAL`).

### Changed
- **Unit Tests Isolation**:
  - Isolated test backups to `.testbackup` to avoid conflict with runtime `.bak` file recovery.

## [5.0.0] - 2026-07-07

### Added
- **Workspace Permission Modes Policy (AI_RULES.md Section 15)**:
  - Enforced Workspace Permission Modes: Sandbox Mode (default, prompts for every change) and Full Access Mode (bypasses confirmation gates for normal, non-destructive workflow tasks).
- **CLI Permission Helpers & Arguments**:
  - Added `get_permission_mode()` and `requires_approval(action_type)` to `workflow_runtime.py`.
  - Added `--permission` parameter to `init` command.
- **Permission Session Schema**:
  - Integrated `permission_mode` fields in session schema.

### Changed
- **Workflow Skills Integration**:
  - Updated all core workflow skills (`initialize-workflow`, `software-development-workflow`, `quick-fix`, `quick-feature`, `brainstorming`, `blueprint-to-implementation`) to query `requires_approval()` and adapt prompts dynamically.

## [4.0.0] - 2026-07-06

### Added
- **Skill Suggestion Gate Policy (AI_RULES.md Section 14)**:
  - Enforced a pre-workflow Suggestion Gate for all unclassified natural language user requests. The AI must stop, classify the request using a Classification Matrix, suggest a workflow Skill or present options, and wait for confirmation.
- **CLI Suggestion Subcommand**:
  - Integrated `suggest` subcommand in `workflow_runtime.py` to register and verify raw user requests, options, and status.

### Changed
- **SDLC Orchestrator Suggestion Routing**:
  - Upgraded `software-development-workflow` to handle unclassified requests and enforce suggestion gate logic.
- **Workflow Skills Enforcement**:
  - Updated all core workflow skills (`quick-fix`, `quick-feature`, `brainstorming`, `blueprint-to-implementation`, `implementation-to-release`, `resume-workflow`) to reference the Suggestion Gate Policy.

## [3.0.0] - 2026-07-06

### Added
- **Blueprint Mandatory Execution Policy (AI_RULES.md Section 13)**:
  - Enforced Design Blueprint as the sole legal input for code generation or modification. Implementation from specifications, brainstorms, planning documents, or conversation text is strictly forbidden.
- **Explicit Release Policy (AI_RULES.md Section 9)**:
  - Enforced manual user-driven releases. The AI Agent is strictly prohibited from running version updates, committing, tagging, or pushing automatically unless explicitly requested by the user.

### Changed
- **Three-Stage Quick-Fix Workflow**:
  - Redesigned `quick-fix` skill to separate work into three strictly gated phases: Spec Generation -> Design Blueprint -> Code Implementation.
- **Three-Stage Quick-Feature Workflow**:
  - Redesigned `quick-feature` skill identically to follow a three-stage gated flow.
- **SDLC Orchestrator Upgrade**:
  - Upgraded `software-development-workflow` to track blueprint approval status (`blueprint.approved` inside session) and enforce manual release stops.
- **CLI Runtime Upgrades**:
  - Upgraded CLI parser in `workflow_runtime.py` to add `blueprint` subcommand for registering and approving design blueprints on session files.

## [2.13.2] - 2026-07-06

### Fixed
- **Visualizer Extension Dashboard Version Display (v1.0.28)**:
  - Fixed a dashboard display bug where the session version fell back to `v0.0.0` by forcing the visualizer backend to read the version directly from `.agents/MANIFEST.json` instead of relying solely on the session file.

## [2.13.1] - 2026-07-06

### Fixed
- **Visualizer Extension & CLI Session Sync (v1.0.27)**:
  - Resolved an issue where running `workflow_runtime.py validate` calculated token values in memory but failed to persist the updated session variables back to `.session.json` on disk.
  - Fixed a display inconsistency in the visualizer's fallback logic where the progress bar token count and details (Input/Output/Cache/Thinking) were out of sync.

## [2.13.0] - 2026-07-06

### Added
- **Visualizer Extension (v1.0.27)**:
  - Integrated asynchronous skills update notifications by polling the raw GitHub stable channel.
  - Implemented client-side version skipping features backed by VS Code `globalState` and browser `localStorage`.
  - Added a dismissable close button (`&times;`) to temporarily hide update alerts.
  - Added a glassmorphism Custom HTML Confirm Modal to prevent accidental version skipping.
- **Script-First Project Memory CLI Engine**:
  - Implemented `runtime/scripts/project_memory/` Python package featuring modules for filesystem scanning (`filesystem.py`), git diff parsing (`git_diff.py`), language/framework detection (`scanner.py`), abstract syntax tree parsing (`parser.py`), architecture/database analysis (`analyzer.py`), index builders (`markdown_writer.py`, `json_writer.py`, `sqlite_writer.py`), and RAG search logic (`search.py`).
  - Added centralized CLI controller `cli.py` exposing `bootstrap`, `update` (incremental sync), and `search` subcommands.
  - Registered the new CLI engine as `aiwf memory` command inside the global bootstrappers `bootstrap.sh` and `bootstrap.ps1`.
  - Added automated tests for all memory subcommands under `skills/workflow-runtime/tests/test_project_memory.py`.


### Changed
- **Refactored Prompt-Driven Skills to Script-First**:
  - Reduced `SKILL.md` token footprints by over 95% for `project-memory-bootstrap`, `project-memory-update`, and `project-rag-search` skills.
  - Migrated complex scanning, indexing, chunking, and search logic from prompt instructions into the Python execution layer.

### Fixed
- **Version Detection Fallback**:
  - Resolved an issue where the Workflow Session dashboard displayed version `v0.0.0` inside user projects by extending `get_version_info` in `validator.py` to search for `MANIFEST.json` inside `.agents/` directory and automatically fallback to parsing the nearest Git tag (`git describe --tags`) if no manifest exists.

## [2.12.5] - 2026-07-06



### Fixed
- **Visualizer Extension (v1.0.26)**:
  - Implemented client-side fallback estimations for token categories (`input_tokens`, `output_tokens`, `cache_tokens`, `thinking_tokens`), cost estimation, `provider`, and `model` in the webview to prevent displays of `0` or `N/A` when the session file contains a total token count but is missing breakdown details.
  - Upgraded extension parse validation to trigger active estimation if the loaded session's summary is missing essential properties like `provider` or `input_tokens`.

---

## [2.12.4] - 2026-07-06

### Fixed
- **Token Estimation & Database Overwriting**:
  - Implemented `get_fallback_usage` on Python side to dynamically estimate tokens based on checkpoint when active logs are missing.
  - Added a protection check in database handler `save_usage_to_dbs` to prevent overwriting correct token/cost history metrics with smaller or zero fallback estimates during initialization.
  - Resolved `OperationalError` when initializing databases on a fresh workspace without a pre-existing `.agents` directory.
- **Visualizer Extension (v1.0.25)**:
  - Updated `README.md` to show the correct new JSON structure and include all missing session fields (`logs`, `suggested_next_skill`, etc.).
  - Upgraded the extension's default/fallback values nạp logic so that `workflow_usage_summary`, `project_usage_summary`, and `global_usage_summary` are always initialized correctly from session data.

---

## [2.12.3] - 2026-07-06

### Fixed
- **Workflow Runtime & Token Estimation Path**:
  - Fixed a critical cross-platform compatibility issue where `BRAIN_ROOT` was hardcoded to a Windows directory, causing token estimation and context percentage calculations to fail on macOS and Linux systems.
  - Dynamically resolved the IDE `brain` directory path using `os.path.expanduser` to support macOS, Linux, and Windows seamlessly.
- **Visualizer Extension (v1.0.24)**:
  - Updated the Workflow Usage token count label to show `active_tokens` (current context window size) instead of `total_tokens` (accumulated tokens), resolving the mathematical mismatch with the percentage bar.
  - Eliminated the blank loading state box when token usage is zero at initialization, ensuring the full layout card remains visible with default zero values.

## [2.12.2] - 2026-07-06

### Fixed
- **Installer & SQLite/UI Synchronization**:
  - Fixed a critical installer packaging issue where the `docs/` folder (specifically `release-guide.md`) was missing from the `public_export` directory, causing installation crashes.
  - Corrected the Python CLI runtime executable path in bash (`install.sh`) and PowerShell (`install.ps1`) installers, changing it to use `$INSTALL_TARGET/$SKILL_DIR/workflow-runtime/scripts/workflow_runtime.py`.
  - Added automatic SQLite initialization sync to `install.sh` and `install.ps1` to populate initial session metrics immediately upon framework setup.
  - Updated `migrate_session_to_db.py` to push calculated project and global usage summaries back into `.session.json` after running SQLite migration, ensuring Visualizer extension displays correct metrics.
  - Adjusted VS Code Visualizer webview CSS (`webview.html` & `webviewHtml.ts`) to change `.step-row` `scroll-margin-top` from `190px` to `250px`, resolving UI overlay issues under the sticky header.
  - Excluded `temp_extract` from visualizer extension `tsconfig.json` to prevent compilation failures.

## [2.12.1] - 2026-07-06

### Fixed
- **Safe & Idempotent AGENTS.md Integration**:
  - Refactored `install.ps1`, `install.sh`, `update.ps1`, and `update.sh` to safely merge rules block inside the project root `AGENTS.md` instead of creating/overwriting `.agents/AGENTS.md`.
  - Added new E2E test suite `test_agents_merge.py` covering all 7 scenarios of the test matrix (fresh install, existing user rules, old block replacement, multiple installs, corrupted block repair, and user customization preservation).

## [2.12.0] - 2026-07-06

### Added
- **Script-First Runtime Engine**:
  - Refactored the token and cost calculation into a fully deterministic Python pipeline.
  - Implemented SQLite database storage local to the project (`.agents/project_runtime.db`) and globally in OS AppData directory (`global_runtime.db`) to track three independent scopes: Workflow, Project, and Global usage.
  - Added new CLI subcommands: `usage sync`, `usage report`, `usage diagnose`, `usage export`.
  - Updated the Visualizer Sidebar webview to show three distinct scope cards, with Workflow context limit comparing current active window tokens instead of accumulated totals.

## [2.11.1] - 2026-07-06

### Added
- **Visualizer Extension Session Usage**:
  - Integrated a new visual "Session Usage" metadata card into the visualizer sidebar extension template (`webview.html`).
  - Added token and cost visualization including total tokens, input/output/cache/thinking counts, context limit, usage percentage, cost USD, provider name, active model, accuracy, and last updated time.
  - Implemented color-changing progress bar indicating token capacity warning states (Green < 60%, Yellow 60%-85%, Red > 85%).
  - Added a toggleable empty state fallback container to gracefully handle missing session metrics.

## [2.11.0] - 2026-07-06

### Added
- **Centralized CLI Runtime Engine**:
  - Implemented a modular, executable Python CLI Runtime Engine under `skills/workflow-runtime/scripts/`.
  - Exposed Runtime CLI API: `init`, `validate`, `start`, `step`, `complete`, `fail`, `heartbeat`.
  - Moved session schema validation, atomic file writing, token estimation, drift check, and heartbeat formatting into the Runtime Engine.
  - Refactored all 26 skills to call this CLI instead of natural language prompt edits, resulting in major token savings and robust execution.
  - Added comprehensive automated unit tests under `skills/workflow-runtime/tests/`.

## [2.10.1] - 2026-07-06

### Optimized
- **Token Usage Optimization**: Refactored all 26 workflow skills to centralize repeated policy descriptions (approval gates, git workflow, memory strategy, RAG retrieval) inside `AI_RULES.md`, reducing prompt sizes by ~3,000 tokens per agent context load while preserving 100% behavior.

## [2.10.0] - 2026-07-06

### Added
- **Dynamic Project-Aware Checkpoints**:
  - Introduced the `project-discovery` skill (`/discover`) to scan codebase structure (configuration files, package managers, frameworks, and databases) and generate `.agents/project-profile.json`.
  - Refactored the orchestrator (`software-development-workflow`) and other SDLC skills to dynamically skip checkpoints (e.g., skip `frontend-visual-debug` for backend-only/CLI projects) according to the project profile.
  - Upgraded the VS Code Visualizer extension to support dynamic project-aware checkpoint rendering.

### Fixed
- **Framework Installer Export Bug**:
  - Fixed a packaging bug in `tools/export.js` that missed copying the `templates`, `agents`, and `runtime` folders to the public export directory, resolving installer failures during `aiwf install`.

---

## [2.9.0] - 2026-07-04

### Added
- **Claude (Anthropic) Support Integration**: Added environment, prompt, and discovery support for Anthropic Claude.
  - Upgraded `skills/environment-bootstrap/SKILL.md` to prompt and configure `ANTHROPIC_API_KEY`.
  - Added key verification diagnostics for Gemini and Anthropic in `doctor.ps1` and `doctor.sh`.
  - Defined XML tagging guidelines in `AI_RULES.md` to wrap boundaries for optimal instruction-following on Claude.
  - Added step-by-step Claude Desktop and Claude Code integration guides in `INSTALL.md`.
  - Upgraded VS Code Extension (`extensions/visualizer`) to version `1.0.10` with custom installation instructions in its README, compiled and packaged to `.vsix` packages.

---

## [2.8.3] - 2026-07-04

### Added
- **Visualizer Extension Webview Separation & Branding**: Upgraded the VS Code Extension (`extensions/visualizer`) to version `1.0.5` to separate inline webview HTML/CSS/JS code into resources file, implement build-time code-gen, and attach the missing Marketplace branding Icon.
  - Linked official logo image to extension manifest.
  - Staged, compiled and packaged the extension to `extensions/visualizer/ai-workflow-visualizer-1.0.5.vsix`.

---

## [2.8.2] - 2026-07-03

### Added
- **Visualizer Extension Author Profile**: Upgraded the VS Code Extension (`extensions/visualizer`) to version `1.0.4` to display the Framework Author profile card containing name, email, and website at the bottom of the sidebar explorer webview.
  - Staged, compiled and packaged the extension to `extensions/visualizer/ai-workflow-visualizer-1.0.4.vsix`.

---

## [2.8.1] - 2026-07-03

### Added
- **Visualizer Extension Upgrade**: Upgraded the VS Code Extension (`extensions/visualizer`) to version `1.0.3` to render checkpoint execution status badges:
  - Rendered pulsing orange `"Running"` badge when checkpoint is `"in_progress"`.
  - Rendered red `"Failed"` badge when checkpoint is `"failed"`.
  - Rendered green `"Complete"` badge when checkpoint is `"completed"`.
  - Staged, compiled and packaged the extension to `extensions/visualizer/ai-workflow-visualizer-1.0.3.vsix`.

---

## [2.8.0] - 2026-07-03

### Added
- **Checkpoint Status Tracking**: Introduced checkpoint execution status (`status: "in_progress" | "completed" | "failed"`) to the session state `.session.json` to allow the Visualizer UI Extension to accurately reflect current running and completed steps.
  - Updated `skills/workflow-runtime/SKILL.md` schema to include the `"status"` field and define update rules.
  - Integrated status checks into `skills/resume-workflow/SKILL.md` and `skills/software-development-workflow/SKILL.md` to recommend retrying/running the exact interrupted skill when a checkpoint has status `"in_progress"` or `"failed"`.
  - Added status update instructions to all checkpoint-changing skills (`brainstorming`, `brainstorming-to-plan`, `plan-to-blueprint`, `blueprint-to-implementation`, `implementation-to-release`, `quick-fix`, `quick-feature`, `project-memory-bootstrap`, `project-memory-update`).

---

## [2.7.0] - 2026-07-03

### Added
- **Standardized Author Metadata**: Integrated professional author metadata across the framework.
  - Added structured author details (Kyle Dang, email, website), license (MIT), repository URL, creation date (`created_at: 2026-07-03`), and last update (`updated_at: 2026-07-03`) to the frontmatter of all 22 `SKILL.md` files.
  - Declared the `"author"` block at the root level of `MANIFEST.json` as the single source of truth, and bumped framework version to `2.7.0`.
  - Added an **Author** bio section to the end of `README.md`.
  - Enforced a strict no-signature constraint in Section 7 of `AI_RULES.md` to prevent agents from appending personal signatures to generated engineering plans, blueprints, or implementations.

---

## [2.6.0] - 2026-07-03

### Added
- **Command-Based Architecture**: Redesigned metadata system to support concise command interactions (`/command` style) instead of verbose skill folder name invocations, while preserving folder paths and skill names for 100% backward compatibility.
  - Added `command`, `aliases`, `category`, and `tags` to the frontmatter of all 22 `SKILL.md` files.
  - Re-structured `MANIFEST.json` list of skills from a string array to an array of objects detailing command properties, and added a `"categories"` configuration grouping the skills.
  - Updated all user-facing documentation (`USAGE.md`, `README.md`, `SKILLS.md`) to use short command invocation examples (e.g. `/workflow`, `/plan`, `/blueprint`, `/implement`).
  - Replaced legacy commands inside skill instruction files (e.g. `/plan-to-blueprint` -> `/blueprint`).

---

## [2.5.0] - 2026-07-03

### Changed
- **Workflow Phase Separation & Project Planning Refactor**: Refactored the Planning phase into Project Planning, separating project scope and technical details.
  - Slashed code implementation details, folder layout, databases, APIs, classes, SQL, and pseudo-code from the Planning phase (`planning-prompt-to-plan` and `brainstorming-to-plan`).
  - Strengthened `plan-to-blueprint` to read both brainstorming and plan files, consolidating all technical design specifications (database schemas, public APIs, sequence diagrams, migration/rollback strategy, folder structure) into a single technical design document.
  - Added "Workflow Phase Separation Policy" as Section 10 to `AI_RULES.md` and updated `AGENTS.md` to define these boundaries.
  - Updated `README.md`, `SKILLS.md`, and `INSTALL.md` to document the new boundaries.

---

## [2.4.6] - 2026-07-03

### Fixed
- **SDLC Checkpoint Alignment**: Fixed target checkpoint transitions in `brainstorming` and `brainstorming-to-plan` skills to write Checkpoint `3` (Architecture Analysis Complete) to `.session.json` upon successful execution (fixing legacy specs that erroneously set it to 1 or 2).

---

## [2.4.5] - 2026-07-03

### Changed
- **Active Runtime Context Tracking**: Mandated executing agents inside `initialize-workflow` and `workflow-runtime` skills to dynamically calculate and save active conversation token usage (calculated from local transcript JSONL logs) to the `"context_usage"` field in `.agents/.session.json` during state updates.

---

## [2.4.4] - 2026-07-03

### Added
- **Default Session Initialization**: Configured installation (`install.sh` / `install.ps1`) and update (`update.sh` / `update.ps1`) scripts to automatically create or upgrade `.agents/.session.json` to the new nested format with elegant initial values to prevent Webview loading issues on empty workspaces.

---

## [2.4.3] - 2026-07-03

### Changed
- **Unified Session State Schema**: Aligned the `.agents/.session.json` schema inside `workflow-runtime` skill with the rich, nested format expected by the VS Code UI Visualizer Extension (including `git`, `work_item`, `version`, `memory`, `rag`, and `context_usage` objects).

---

## [2.4.2] - 2026-07-03

### Changed
- **Strict Relative Path Guards**: Strengthened behavioral rules in `initialize-workflow` and `workflow-runtime` skills to explicitly force runtime agents to save workspace directory paths as `"."` under `.agents/.session.json` to eliminate absolute path outputs completely.

---

## [2.4.1] - 2026-07-03

### Changed
- **Relative Path Optimization**: Configured workspace session state and initialization scripts to report project paths using relative representations (e.g. `.`) rather than absolute paths to prevent local file path leakage.

---

## [2.4.0] - 2026-07-03

### Added
- **Configuration-Driven Releases (`release.config.json`)**: Refactored the release subsystem to read layout metadata from a centralized project configuration. Supports single projects, multi-module (backend/frontend), mobile, desktop, and monorepos.
- **Affected Module Detection**: Added Git diff scanning to identify modified modules and bump versions/changelogs only for affected components.
- **Shared Module Detection**: Added dependency propagation so that modifications to common folders (like `shared/`, `common/`, `libs/`) prompt the user to decide on dependent module updates.
- **Release Guide Document (`release-guide.md`)**: Created detailed documentation explaining release modes, schemas, and safety gates.
- **Auto-Detection Fallback**: Implemented automatic language/framework detection to suggest configuration structures to the user if `release.config.json` is missing.

---

## [2.3.0] - 2026-07-03

### Added
- **Multi-Agent Role Contracts (`agents/`)**: Added role specifications, artifact ownership rules, and execution constraints for `planner`, `architect`, `coder`, `reviewer`, and `release-manager` agents.
- **Handoff Runtime Schemas & State Files (`runtime/`)**: Created JSON schema specifications and tracking files for handoffs (`handoffs.json`), checkpoints (`checkpoints.json`), and system state (`state.schema.json`) to track role transitions and prevent illegal workspace alterations.
- **Script Support & Installers**: Updated `install.*`, `update.*`, and `uninstall.*` utility scripts to support deploying, upgrading, and removing the new multi-agent `agents/` and `runtime/` directories.

---

## [2.2.0] - 2026-07-03

### Added
- **Workflow Runtime Controller (`workflow-runtime`)**: Introduced a new core Skill that acts as the runtime controller for execution state management, session handling (`.agents/.session.json`), validation checkpoints, and resume-workflow recovery capabilities.
- **Unified Checkpoints and Heartbeats**: Added checkpoint transitions (1 to 7) and plain text heartbeat logging to all SDLC Feature and Fast-track/Quick skills to detect context drift (unexpected branch/work item/version changes) and ensure resumable, robust execution.

---

## [2.1.0] - 2026-07-03

### Added
- **Workflow Initialization Skill (`initialize-workflow`)**: Introduced a new core Skill acting as the mandatory entry point of the entire AI Engineering Workflow. It aggregates workspace validation, policy loading, project memory status, Git checking, active work item discovery, version detection, and tool inspection into a single runtime context.
- **Reference-Driven Initialization Check**: Updated all 12 core Skills to assume `initialize-workflow` has executed and to verify context before running, eliminating redundant environment and configuration parsing checks in individual Skills.

---

## [2.0.1] - 2026-07-03

### Changed
- **Plain Text Orchestrator Report**: Refactored the `software-development-workflow` output layout from Markdown tables to a clean, structured plain text block format to align with other Skill Completion Contracts and prevent UI line-wrap issues.

---

## [2.0.0] - 2026-07-03

### Added
- **Centralized Policy Architecture (`AI_RULES.md`)**: Created a centralized global policies file in the repository root as the single source of truth for all shared behaviors, constraints, and SDLC gates.
- **Reference-Driven Skills**: Refactored all core Skills (`software-development-workflow`, `brainstorming`, `brainstorming-to-plan`, `plan-to-blueprint`, `blueprint-to-implementation`, `quick-fix`, `quick-feature`, `implementation-to-release`, `project-memory-bootstrap`, `project-memory-update`, `project-rag-search`, `environment-bootstrap`, `environment-health`) to reference `AI_RULES.md` instead of duplicating rules, satisfying DRY principles and enabling policy-driven architecture.

---

## [1.9.1] - 2026-07-03

### Changed
- **Unicode Box Art Migration**: Replaced Unicode box art boundary boxes with native Markdown tables and plain text headers in all skill definitions (`brainstorming`, `quick-fix`, `quick-feature`, `software-development-workflow`, `environment-health`, `environment-bootstrap`) to guarantee stable font rendering across all IDEs and chat clients while preserving the behavioral anchor constraints.

---

## [1.9.0] - 2026-07-03

### Changed
- **Unified Global Approval Gate Policy**: Implemented strict approval gates before any state-changing action in the workspace (modifying source code, creating/deleting files, branch checkouts, merging, version bumps, commits, tags, pushing). Agents must display changes, list affected files, current branch, and stop to await `Y`/`Yes`/`Proceed`/`Continue`.
- **Pre-Implementation Git Gate**: Refactored `blueprint-to-implementation`, `quick-fix` (Phase 2), and `quick-feature` (Phase 2) to display the active branch and status, prompt the user with branch options (continue on branch, create new branch with suggested names `feature/FEAT-XXX-slug`, `fix/FIX-XXX-slug`, `quick/QUICK-XXX-slug`, or stop), and wait for approval before any coding.
- **Merge Gate & Release Workflow Order**: Refactored `implementation-to-release` to follow the strict sequential release workflow (Build/Test, Detect version, Update version, Update CHANGELOG, Approval, Commit, Create Tag `vX.Y.Z`, Push Branch, Push Tag). If not on main/master, the agent must explicitly ask for merge permission. Skipped Git steps automatically for Non-Git projects.
- **Workflow Orchestration Reminders**: Upgraded `software-development-workflow` to remind executing agents about branch and merge gates during Implementation and Release cases.

---

## [1.8.0] - 2026-07-03

### Changed
- **New Documentation Folders Alignment**: Refactored `quick-fix` and `quick-feature` Skills to conform to the new project directory architecture:
  - **`quick-fix`**: Generates Fix files under `docs/issues/FIX-XXX_issue_name.md` instead of `docs/brainstorming/`. Updates Phase 2 execution to read from `docs/issues/`.
  - **`quick-feature`**: Generates Spec files under `docs/quick/QUICK-XXX_feature_name.md` instead of `docs/brainstorming/`. Calculates IDs by scanning `docs/quick/`. Updates Phase 2 execution to read from `docs/quick/`.
- **Project Memory & RAG Upgrades**: Updated `project-memory-bootstrap`, `project-memory-update`, and `project-rag-search` Skills to index and search files inside `docs/issues/` and `docs/quick/` alongside standard SDLC folders.
- Preserved the existing standard workflow.

---

## [1.7.1] - 2026-07-03

### Changed
- **Rename fast-fix to quick-fix**: Renamed the `fast-fix` Skill directory to `skills/quick-fix/` and all internal/external CLI references to `/quick-fix`.
- **Mandatory Mode Active Blocks**: Added `🔒 QUICK-FEATURE MODE ACTIVE` and `🔒 QUICK-FIX MODE ACTIVE` behavioral anchor blocks to establish immediate approval gate boundaries.
- **Mandatory Specification Creation**: Enforced that `docs/brainstorming/FEAT-XXX_feature_name.md` (for `quick-feature`) and `docs/brainstorming/FIX-XXX_issue_name.md` (for `quick-fix`) must be generated during Phase 1. Source code modifications are strictly blocked until the user confirms with `Y` or `Yes`.

---

## [1.7.0] - 2026-07-03

### Added
- **New `quick-feature` Skill**: Introduced a lightweight parallel workflow designed specifically for low-risk, small feature requests (e.g. adding one API endpoint, button, dialog, filter, validation, search field, export function, configuration option). Eligible features bypass standard planning/blueprint overhead. Includes:
  - Scope/Eligibility Matrix (low impact, single module context).
  - Mini Feature Specification template generated at `docs/brainstorming/FEAT-XXX_feature_name.md`.
  - User Approval Gate blocking code modifications until explicit Y/N confirmation.
  - Automatic compilation/test verification and Quick Feature Summary output formatting.
  - Self-Validation checklist for compliance.

### Changed
- **Workflow Orchestration Integration**: Upgraded the `software-development-workflow` Skill to support the parallel **Option 3: Quick-Feature Workflow** track. The orchestrator now automatically classifies incoming tasks and recommends `quick-feature` based on scope, risk, and impact analysis of the `task_description`.
- Registered `quick-feature` in `MANIFEST.json` and cataloged it in `SKILLS.md`.

---

## [1.6.2] - 2026-07-03

### Changed
- **Two-Phase Quick-Fix Workflow**: Refactored the `quick-fix` Skill from an immediate implementation skill into a two-phase workflow with an explicit User Approval Gate:
  - **Phase 1 (Analysis)**: Generates a formal Fix document at `docs/brainstorming/FIX-XXX_issue_name.md` containing metadata, symptoms, root cause, proposed fix, acceptance criteria, and a test plan. Bypasses source code modifications.
  - **User Approval Gate**: Automatically stops after writing the Fix document and prompts the user `Continue? [Y/N]`.
  - **Phase 2 (Implementation)**: Executes minimal source code changes only after receiving explicit Y/yes confirmation from the user.
- Updated `skills/quick-fix/SKILL.md` to establish the `QUICK-FIX MODE ACTIVE` behavioral anchor and wrong behavior check patterns.

---

## [1.6.1] - 2026-07-03

### Fixed
- **CLI Updater macOS/BSD Compatibility**: Fixed a bug where `aiwf update` and `aiwf uninstall` failed to sync or remove skills on macOS because of the non-portable `\s` regex pattern in `sed`. Replaced it with a POSIX-compliant `[[:space:]]` pattern and added a grep filter to exclude target prefixes.
- Deployed identical fixes to both `update.sh` and `uninstall.sh`.

---

## [1.6.0] - 2026-07-03

### Added
- **New `quick-fix` Skill**: Introduced a lightweight parallel workflow designed specifically for low-risk, small bug fixes (e.g. routing errors, null pointers, typos, configuration changes, simple validations). Eligible fixes bypass the full SDLC (No Brainstorming, Planning, Blueprint, or ADR). Includes:
  - Scope/Eligibility Matrix (low impact, single module context).
  - Decision Matrix for auto-classification (Quick-Fix vs Standard Workflow).
  - Automatic compilation checks and test suite verification.
  - Comprehensive Quick-Fix Implementation Summary output formatting.
  - Verification checklist for compliance.

### Changed
- **Workflow Orchestration Integration**: Upgraded the `software-development-workflow` Skill to accept `task_description` input. The orchestrator now automatically classifies incoming tasks and recommends either the `quick-fix` track or the `brainstorming` standard workflow based on scope and risk analysis.
- Registered the `quick-fix` skill in `MANIFEST.json` and cataloged it in `SKILLS.md`.

---

## [1.5.5] - 2026-07-03

### Changed
- **Completion Report Layout Refactoring**: Refactored the `Self-Validation Checklist` and `Completion Report` text blocks in the `brainstorming` skill into beautiful, native Markdown tables and callout alert boxes to prevent ugly line wraps and layout breaks in chat interfaces.

---

## [1.5.4] - 2026-07-03

### Changed
- **Skill Renamed**: `idea-to-planning-prompt` → `brainstorming` — invocation is now `/brainstorming`. Directory renamed to `skills/brainstorming/`.
- **Skill Renamed**: `planning-prompt-to-plan` → `brainstorming-to-plan` — invocation is now `/brainstorming-to-plan`. Directory renamed to `skills/brainstorming-to-plan/`.
- Updated all cross-references in: `MANIFEST.json`, `SKILLS.md`, `README.md`, `INSTALL.md`, `USAGE.md`, `CHANGELOG.md`, and Skills: `software-development-workflow`, `environment-bootstrap`, `environment-health`, `project-rag-search`, `project-memory-update`.

---

## [1.5.3] - 2026-07-03

### Changed
- **Behavior Anchoring: brainstorming**: Root cause identified — previous guardrails were passive warnings that LLM helpfulness bias could override. Fixed with: (1) Mandatory First Output declaration block — AI must print "DISCOVERY MODE ACTIVE" verbatim before any other action, creating a behavioral commitment anchor; (2) Wrong Behavior Detection pattern — explicit checklist of prohibited tool calls with a right vs wrong examples table; (3) Restructured workflow with `[MANDATORY]` step before Step 1; (4) Identical SKILL.md deployed to both framework source and installed project `.agents/`.
- **Repository Metadata Sync**: Bumped framework version to `1.5.3` in `MANIFEST.json`.

---

## [1.5.2] - 2026-07-03

### Changed
- **Production Hardening: brainstorming**: Performed root cause analysis identifying 8 critical/high/medium defects. Refactored the Skill with: (1) Requirement Readiness Score gate (0–100, threshold 85), (2) explicit Y/N user confirmation before document generation, (3) free-text invocation replacing YAML input parsing, (4) corrected Feature labels during decomposition to prevent ID naming conflicts, (5) added Impact Analysis and Risk Analysis to discovery checklist, (6) top-level STOP RULE block preventing auto-transition to downstream phases, (7) expanded 14-section Brainstorming document template per production spec, (8) resolved Capability Boundary vs Completion Report conflict.
- **Repository Metadata Sync**: Bumped framework version to `1.5.2` in `MANIFEST.json`.

---

## [1.5.1] - 2026-07-03

### Changed
- **Strict Requirement Discovery & Feature Decomposition**: Refactored `brainstorming` skill to focus purely on read-only requirement discovery and solution discovery, preventing direct implementation or auto-execution of downstream tasks. Added multi-feature decomposition support.
- **Repository Metadata Sync**: Bumped framework version to `1.5.1` in `MANIFEST.json`.

---

## [1.5.0] - 2026-07-03

### Changed
- **Solution Architect Workshop Upgrade**: Refactored `brainstorming` (now Interactive Solution Discovery) to conduct in-depth architectural design reviews. It maps context, generates 2-3 significantly different solution options, provides trade-offs and complexity ratings, recommends the best choice, and requires user selection (`user_selection`) before writing `docs/brainstorming/` files.
- **Repository Metadata Sync**: Bumped framework version to `1.5.0` in `MANIFEST.json` and synchronized descriptions/inputs in `SKILLS.md`.

---

## [1.4.0] - 2026-07-03

### Added
- **Global Bootstrap Installers**: Added `bootstrap.sh` (macOS/Linux), `bootstrap.ps1` (Windows PowerShell), and `bootstrap.bat` (Windows CMD) to easily configure a global PATH environment variable one-time setup.
- **Global `aiwf` CLI Wrapper**: Added light-weight binary and script command-line wrappers redirecting project-level actions (`install`, `update`, `uninstall`, `doctor`, `version`) back to the framework repository location.
- **Diagnostics and Doctor Scripts**: Added `doctor.sh` and `doctor.ps1` to test the validity of PATH setups and project structure integrity.
- **Version Reporting CLI**: Added `version.sh` and `version.ps1` to display framework core metadata.
- **Windows CLI Complete parity**: Added `update.ps1` and `uninstall.ps1` to provide native CLI powershell support under Windows.

---

## [1.3.0] - 2026-07-03

### Added
- **Framework Installer**: Added `install.sh` (Linux/macOS) and `install.ps1` (Windows/PowerShell Core) to deploy framework files (`AI_RULES.md`, `MANIFEST.json`, `skills/`, `templates/`) into target projects under the `.agents/` folder.
- **Idempotency and Safeguards**: Both installers are fully idempotent, enforce Git repository detection, and prevent overwriting existing custom configs unless explicitly requested.
- **Framework Synchronizer**: Added `update.sh` to compare target versions and update changed skills/files without deleting user-created content.
- **Framework Uninstaller**: Added `uninstall.sh` to perform clean removals of only framework-managed files.
- **Package Manifest**: Updated `MANIFEST.json` to schema `1.3.0` containing repository URLs, supported OS list, and file structure rules.
- **New Folders**: Added placeholder `templates/` and `examples/` folders.

---

## [1.2.0] - 2026-07-03

### Added
- **New Skill: `create-adr`**: Added a dedicated skill under `skills/create-adr/SKILL.md` to generate Architecture Decision Records (ADRs) under `docs/adr/ADR-XXX_*.md`.
- **FEAT-XXX Padded Feature IDs**: Pinned Feature IDs to the unified `FEAT-001`, `FEAT-002`, `FEAT-003` prefix standard.
- **ADR Assessment & Validation Gates**:
  - `plan-to-blueprint` now assesses and recommends ADR requirements (it does not write ADR files).
  - `blueprint-to-implementation` now blocks execution and requests `/create-adr` if a blueprint requires an ADR that does not exist or is not Accepted.
  - `software-development-workflow` now detects pending ADR creation steps.

### Changed
- **Release Tracking**: Refactored `implementation-to-release` to document releases directly into `CHANGELOG.md` instead of creating release files.
- **Clean Documentation Folders**: Kept only the 4 core folders (`docs/brainstorming/`, `docs/plans/`, `docs/designs/`, and `docs/adr/`).
- **All Skills Refactored**: Refactored all 13 existing skills and framework files (README, SKILLS, INSTALL, AGENTS, MANIFEST) to conform to the `FEAT-XXX` format and simplified folders.

### Removed
- Removed legacy folders `docs/releases/` and `docs/archive/`.

---

## [1.1.0] - 2026-07-03

### Added
- **Feature-Centric Documentation Structure**: Added `docs/brainstorming/` (for discovery requirements), `docs/designs/` (for blueprints), `docs/releases/` (for release notes), `docs/adr/` (for Architectural Decision Records), and `docs/archive/` (for deprecated features).
- **Feature ID Traceability**: Introduced unified Feature IDs (e.g. `001`, `002`) to link all artifacts generated during a feature's lifecycle (Discovery -> Plan -> Blueprint -> Release).
- **ID Allocation Algorithm**: Standardized the Feature ID calculation to read only from `docs/brainstorming/`.

### Changed
- **Orchestrator Refactoring**: Updated `software-development-workflow` to track status based on Feature IDs and detect active phase files using the new directory structure.
- **Requirement Discovery Upgrade**: Updated `brainstorming` to write master requirements files under `docs/brainstorming/` formatted as `NNN_<feature_name>.md`. Tweak to include Traceability headers.
- **Planning Prompt to Plan Refactoring**: Updated `brainstorming-to-plan` to read from `docs/brainstorming/` and output plans to `docs/plans/` using Feature IDs.
- **Plan to Blueprint Refactoring**: Updated `plan-to-blueprint` to read plans from `docs/plans/` and output blueprints to `docs/designs/` using Feature IDs.
- **Blueprint Execution Refactoring**: Updated `blueprint-to-implementation` to use technical designs in `docs/designs/`.
- **Git Release Refactoring**: Updated `implementation-to-release` to output release logs to `docs/releases/` using Feature IDs.
- **Repository Metadata Sync**: Updated `MANIFEST.json` (bumped to 1.1.0), `README.md`, `SKILLS.md`, `INSTALL.md`, and `AGENTS.md` to document the new feature-centric layout and rules.

---

## [1.0.0] - 2026-07-03

### Added
- **AI Skill Library**: Initial collection of 13 modular AI Agent skills for managing the Software Development Life Cycle (SDLC).
- **Environment Bootstrapping & Diagnostics**: Added `environment-bootstrap` and `environment-health` skills for automated workspace provisioning and health checks.
- **Project Memory Management**: Added `project-memory-bootstrap` and `project-memory-update` for maintaining a persistent, memory-first workspace metadata layer.
- **RAG & Search capabilities**: Added `project-rag-search` for lightning-fast semantic context retrieval.
- **Planning & Design Engine**: Added `brainstorming-to-plan` and `plan-to-blueprint` to build implementation plans and blueprints from structured requirements.
- **Code implementation**: Added `blueprint-to-implementation` and `implementation-to-release` to generate code and release software in a standardized, controlled fashion.
- **Frontend Design Thinking**: Added `frontend-design` containing core styling guidelines and accessibility rules.
- **OKR Reporting**: Added `okr-report-generator` for processing objective matrices.
- **Workflow Orchestration**: Added `software-development-workflow` to supervise the current phase of development.
- **Package Manifest**: Added `MANIFEST.json` containing machine-readable definitions for the skill library.
- **Documentation**: Added `README.md`, `INSTALL.md`, `SKILLS.md`, `LICENSE`, and this `CHANGELOG.md`.

### Changed
- **Interactive Requirement Discovery**: Refactored the `brainstorming` skill to use a 10-phase interactive workshop model. Calculates a Readiness Score and prompts clarifications when below 85 before producing a planning prompt.
