// File path: docs/docs-assets/skills-data.js
const skillsData = [
  {
    name: "initialize-workflow",
    command: "/init",
    category: "runtime",
    checkpoint: "1",
    purpose: "Khởi tạo nhẹ phiên AIWF: nạp guardrails, đọc split-state cache, kiểm tra Git tối thiểu và thiết lập permission mode.",
    input: "workspace_path, permission_mode, optional --non-interactive",
    output: "Split-state runtime dưới .agents/state/ được cập nhật; memory/RAG nặng được deferred cho skill cần dùng.",
    pitfall: "Init không được dùng để scan toàn repo, sync transcript nặng, hoặc tự động release. Nó chỉ chuẩn bị runtime context nhẹ."
  },
  {
    name: "resume-workflow",
    command: "/resume",
    category: "runtime",
    checkpoint: "N/A",
    purpose: "Khôi phục phiên làm việc từ split-state và context snapshot sau khi chuyển thread hoặc gián đoạn.",
    input: "Không có tham số bắt buộc.",
    output: "Runtime khôi phục checkpoint, current skill, command, step và suggested next action nếu có.",
    pitfall: "Resume không thay thế approval gate. Nếu bước tiếp theo là state-changing action, vẫn phải xin duyệt."
  },
  {
    name: "project-memory-update",
    command: "/memory-sync",
    category: "memory",
    checkpoint: "2",
    purpose: "Cập nhật Project Memory theo Git diff bằng script-first pipeline và đồng bộ bề mặt tri thức liên quan.",
    input: "Git diff hiện tại hoặc tùy chọn full rebuild khi được yêu cầu.",
    output: "Project Memory, memory state và provider sync maps được cập nhật theo Knowledge Runtime/provider delegation.",
    pitfall: "Không tự viết logic diff trong prompt. Hãy để CLI/script xử lý deterministic steps và chỉ polish phần mô tả nếu skill yêu cầu."
  },
  {
    name: "brainstorming",
    command: "/brainstorm",
    category: "workflow",
    checkpoint: "3",
    purpose: "Khám phá yêu cầu, ràng buộc và hướng giải pháp ở mức discovery trước khi có kế hoạch hoặc blueprint.",
    input: "Yêu cầu tính năng hoặc vấn đề từ người dùng.",
    output: "Tài liệu discovery trong docs/brainstorming/.",
    pitfall: "Không viết code, không scaffold implementation và không bypass approval chỉ vì yêu cầu có vẻ nhỏ."
  },
  {
    name: "brainstorming-to-plan",
    command: "/plan",
    category: "workflow",
    checkpoint: "4",
    purpose: "Chuyển discovery đã duyệt thành implementation plan hướng stakeholder: scope, deliverables, risk và acceptance path.",
    input: "Brainstorming/spec đã được duyệt.",
    output: "Plan chính thức trong docs/plans/.",
    pitfall: "Plan không được mô tả class, hàm, database schema hoặc pseudo-code. Chi tiết kỹ thuật thuộc blueprint."
  },
  {
    name: "plan-to-blueprint",
    command: "/blueprint",
    category: "workflow",
    checkpoint: "5",
    purpose: "Tạo Technical Blueprint đầy đủ làm hợp đồng kỹ thuật duy nhất cho implementation.",
    input: "Plan đã duyệt.",
    output: "Blueprint trong docs/designs/ với file-by-file analysis, API/data contracts, checklist và test plan.",
    pitfall: "Blueprint có placeholder, vague instruction hoặc thiếu file mapping thì chưa được approve. No Blueprint, No Code."
  },
  {
    name: "blueprint-to-implementation",
    command: "/implement",
    category: "workflow",
    checkpoint: "6",
    purpose: "Triển khai đúng các file và hành vi đã được blueprint approve.",
    input: "Approved Technical Blueprint.",
    output: "Source/docs files được cập nhật trong phạm vi blueprint.",
    pitfall: "Không refactor ngoài scope, không sửa file ngoài write set, không đổi Runtime API v1 nếu blueprint không cho phép."
  },
  {
    name: "implementation-to-debug",
    command: "/debug",
    category: "workflow",
    checkpoint: "7",
    purpose: "Chạy build, lint, typecheck, tests và self-fix loop có giới hạn cho các lỗi trong scope task.",
    input: "Implementation vừa hoàn thành.",
    output: "Debug/diagnostic result và trạng thái PASS/FAILED.",
    pitfall: "Nếu lỗi nằm ngoài file thuộc task scope, dừng và báo thay vì sửa lan rộng."
  },
  {
    name: "frontend-visual-debug",
    command: "/visual-debug",
    category: "workflow",
    checkpoint: "8",
    purpose: "Kiểm tra trực quan UI bằng browser/screenshot khi workflow có bề mặt frontend.",
    input: "UI hoặc static site vừa thay đổi.",
    output: "Visual QA result cho desktop/mobile hoặc target viewport.",
    pitfall: "Không dùng thay thế test kỹ thuật. Đây là lớp kiểm chứng visual bổ sung."
  },
  {
    name: "debug-to-verify",
    command: "/verify",
    category: "workflow",
    checkpoint: "9",
    purpose: "Quality gate cuối: đối chiếu implementation với blueprint, acceptance criteria và checklist nghiệm thu.",
    input: "Debug/build/test đã PASS hoặc Not Configured.",
    output: "Verification report PASS/FAIL và Go/No-Go decision.",
    pitfall: "Không claim hoàn tất nếu verify chưa chạy hoặc còn test gap quan trọng chưa nêu rõ."
  },
  {
    name: "implementation-to-release",
    command: "/release",
    category: "workflow",
    checkpoint: "10",
    purpose: "Thực hiện release explicit: version, changelog, commit, tag, push sau khi người dùng yêu cầu release.",
    input: "Verify PASS và yêu cầu release rõ ràng.",
    output: "Release artifacts/git operations nếu được approve.",
    pitfall: "Release không bao giờ tự động. Commit, tag, push, version bump và changelog đều là hard-gated actions."
  },
  {
    name: "software-development-workflow",
    command: "/workflow",
    category: "workflow",
    checkpoint: "N/A",
    purpose: "Đọc trạng thái workflow và đề xuất skill/command tiếp theo theo checkpoint hiện tại.",
    input: "Runtime state hiện tại.",
    output: "Routing/status summary và suggested next command.",
    pitfall: "Đây là advisor, không phải giấy phép bypass blueprint hoặc approval gates."
  },
  {
    name: "quick-fix",
    command: "/fix",
    category: "utility",
    checkpoint: "Rút gọn",
    purpose: "Sửa lỗi cục bộ bằng quy trình FIX Spec -> FIX Blueprint -> scoped implementation.",
    input: "Mô tả bug nhỏ, localized và low-risk.",
    output: "docs/issues/FIX-XXX_slug.md, docs/designs/FIX-XXX_slug_blueprint.md và code fix sau approval.",
    pitfall: "Không dùng cho lỗi rộng, thay đổi kiến trúc, database redesign hoặc hành vi chưa rõ root cause."
  },
  {
    name: "quick-feature",
    command: "/feature",
    category: "utility",
    checkpoint: "Rút gọn",
    purpose: "Tính năng nhỏ theo quy trình QUICK Spec -> Blueprint -> Implementation, vẫn bắt buộc có approval gates.",
    input: "Yêu cầu tính năng local, additive, ít rủi ro.",
    output: "docs/quick/QUICK-XXX_slug.md, blueprint tương ứng và implementation scoped.",
    pitfall: "Quick không có nghĩa là bỏ blueprint. Chỉ rút ngắn planning, không rút ngắn safety."
  },
  {
    name: "frontend-design",
    command: "/ui",
    category: "utility",
    checkpoint: "N/A",
    purpose: "Hỗ trợ quyết định UI/UX, layout, typography, responsive behavior và visual polish.",
    input: "Yêu cầu thiết kế giao diện hoặc visual QA.",
    output: "Design guidance hoặc UI implementation plan phù hợp stack hiện có.",
    pitfall: "Không tạo landing page hoặc redesign ngoài yêu cầu. Với frontend thay đổi source vẫn cần blueprint."
  },
  {
    name: "project-discovery",
    command: "/discover",
    category: "environment",
    checkpoint: "N/A",
    purpose: "Nhận diện tech stack, module boundaries và verification commands để cấu hình workflow checkpoints.",
    input: "Workspace dự án.",
    output: "Project profile và discovery metadata.",
    pitfall: "Không dùng broad scan thay Memory/RAG-first khi đã có context mục tiêu."
  },
  {
    name: "environment-bootstrap",
    command: "/bootstrap",
    category: "environment",
    checkpoint: "N/A",
    purpose: "Chuẩn bị môi trường AIWF bằng script-first setup cho toolchain cần thiết.",
    input: "Bootstrap configuration và user approvals cần thiết.",
    output: "Môi trường local sẵn sàng cho workflow.",
    pitfall: "Không tự cài công cụ nhạy cảm hoặc đổi permission mode nếu chưa được approve."
  },
  {
    name: "environment-health",
    command: "/doctor",
    category: "environment",
    checkpoint: "N/A",
    purpose: "Kiểm tra sức khỏe môi trường ở chế độ read-only: Git, Python, Node, Docker, SQLite, Qdrant và cache.",
    input: "Không có tham số bắt buộc.",
    output: "Báo cáo diagnostics môi trường.",
    pitfall: "Doctor chỉ quan sát. Không dùng nó để sửa/cài đặt tự động."
  },
  {
    name: "create-adr",
    command: "/adr",
    category: "architecture",
    checkpoint: "N/A",
    purpose: "Ghi lại quyết định kiến trúc dài hạn khi có trade-off đáng kể.",
    input: "Quyết định kiến trúc đã được cân nhắc.",
    output: "docs/adr/ADR-XXX_slug.md.",
    pitfall: "Không tạo ADR cho thay đổi nhỏ hoặc tài liệu vận hành không đổi kiến trúc."
  },
  {
    name: "orchestrator",
    command: "/orchestrate",
    category: "workflow",
    checkpoint: "N/A",
    purpose: "Điểm vào trung tâm cho workflow phức tạp: phân loại scope, điều phối phase owner, analysis subagents và implementation workers theo policy.",
    input: "Yêu cầu workflow hoặc approved blueprint cần execution planning.",
    output: "Execution plan, read/write sets, worker scheduling và aggregated results.",
    pitfall: "Parallel chỉ được chọn ở đầu implementation. Analysis agents là read-only; worker agents phải có write set không chồng lấn và file locks."
  },
  {
    name: "workflow-runtime",
    command: "/runtime",
    category: "runtime",
    checkpoint: "N/A",
    purpose: "CLI/runtime engine quản lý checkpoint, split-state, leases, locks, execution mode, analysis agents và workflow telemetry.",
    input: "Runtime subcommands như status, validate, start, step, complete, lock, execution, analysis-agent.",
    output: "Structured state updates và operational status cho dashboard/skills.",
    pitfall: "Không sửa state JSON thủ công nếu có runtime command tương ứng; dùng CLI để tránh drift."
  },
  {
    name: "knowledge-runtime",
    command: "/knowledge",
    category: "memory",
    checkpoint: "N/A",
    purpose: "Lớp truy cập tri thức hợp nhất cho Markdown, SQLite, Qdrant, Obsidian và provider adapters.",
    input: "Search/read/write/index request từ workflow skills.",
    output: "Kết quả tri thức có cấu trúc hoặc provider operation result.",
    pitfall: "Skills không đọc provider backend trực tiếp. Tất cả knowledge operations phải đi qua Knowledge Runtime trừ adapter compatibility được approve."
  },
  {
    name: "vir-runtime",
    command: "/vir-runtime",
    category: "runtime",
    checkpoint: "N/A",
    purpose: "Visual Intelligence Runtime cung cấp observation sandbox và event/evidence primitives cho điều tra giao diện.",
    input: "Target observation request hoặc runtime verification context.",
    output: "Evidence objects, observations và structured visual runtime events.",
    pitfall: "VIR runtime quan sát và thu evidence; không tự đưa ra kết luận cognitive nếu skill khác mới là owner."
  },
  {
    name: "vir-investigate",
    command: "/vir-investigate",
    category: "workflow",
    checkpoint: "N/A",
    purpose: "Điều tra nguyên nhân bằng evidence, contradiction checks và structured RCA cho lỗi phức tạp.",
    input: "Bug, visual mismatch hoặc failure report cần RCA.",
    output: "Investigation report và candidate root causes.",
    pitfall: "Không nhảy thẳng sang fix khi evidence chưa đủ hoặc hypothesis còn mâu thuẫn."
  },
  {
    name: "vir-verify",
    command: "/vir-verify",
    category: "workflow",
    checkpoint: "N/A",
    purpose: "Quality gate visual sử dụng weighted consensus, visual audits và SDLC compliance checks.",
    input: "Implementation result, screenshots, target criteria hoặc verification bundle.",
    output: "PASS/FAIL visual verification report.",
    pitfall: "Không thay thế debug/build tests; đây là lớp verify trực quan và compliance bổ sung."
  },
  {
    name: "vir-memory-update",
    command: "/vir-memory-update",
    category: "memory",
    checkpoint: "N/A",
    purpose: "Củng cố bài học từ visual verification và lưu baseline/evidence lessons cho lần sau.",
    input: "Verified visual evidence hoặc lesson outcome.",
    output: "Memory update notes, baseline references hoặc learning artifacts.",
    pitfall: "Chỉ cập nhật memory khi có kết quả đã xác minh; không lưu giả thuyết chưa kiểm chứng như fact."
  },
  {
    name: "project-memory-bootstrap",
    command: "/memory-init",
    category: "memory",
    checkpoint: "N/A",
    purpose: "Phân tích toàn diện dự án lần đầu tiên và tạo ra đầy đủ các lớp Project Memory trong thư mục .agents/memory/ theo kiến trúc Script-First.",
    input: "Thư mục gốc dự án (workspace), cấu hình memory.config.json",
    output: "Các file Project Memory bao gồm .agents/memory/project-summary.md và .agents/memory/memory-state.json",
    pitfall: "Không chạy bootstrap nếu memory đã tồn tại và đang hoạt động tốt; tránh quét toàn bộ workspace lặp đi lặp lại."
  },
  {
    name: "project-rag-search",
    command: "/memory-search",
    category: "memory",
    checkpoint: "N/A",
    purpose: "Cung cấp khả năng tìm kiếm ngữ nghĩa nhanh chóng cho tri thức dự án phục vụ các kỹ năng AI khác theo kiến trúc Script-First.",
    input: "Câu truy vấn tìm kiếm bằng ngôn ngữ tự nhiên",
    output: "Danh sách các đoạn văn bản tri thức liên quan nhất kèm theo nguồn và điểm số tương đồng (similarity scores)",
    pitfall: "Tránh lạm dụng tìm kiếm RAG khi tri thức mục tiêu đã có sẵn trong Project Memory cục bộ được cache."
  },
  {
    name: "skill-self-verification",
    command: "/verify-skill",
    category: "quality",
    checkpoint: "N/A",
    purpose: "Tự động hóa kiểm thử chấp nhận hành vi (BAT) để đánh giá luồng tương tác, trải nghiệm người dùng (UX) và giá trị của các kỹ năng mới/sửa đổi trước khi phát hành.",
    input: "Tên kỹ năng cần kiểm thử, tham số cấu hình BAT, các kịch bản kiểm thử giả lập",
    output: "Báo cáo kết quả Behavioral Acceptance Testing (BAT), so sánh diff mã nguồn và đánh giá UX quantitative",
    pitfall: "Tránh chạy tự động không có mục tiêu hoặc bỏ qua các approval gates thật sự được mock trong quá trình chạy."
  },
  {
    name: "python-development",
    command: "/python-dev",
    category: "implementation",
    checkpoint: "N/A",
    purpose: "Hướng dẫn các tác vụ phát triển Python bao gồm quản lý gói, kiểm thử, định dạng mã và kiểm tra lỗi (linting).",
    input: "Yêu cầu sửa đổi/viết mã Python, mã nguồn hiện tại, tài liệu blueprint",
    output: "Mã nguồn Python chất lượng cao đã qua định dạng, kiểm thử và linting đầy đủ",
    pitfall: "Tránh chạy pip install global khi chưa xác nhận virtualenv; tránh bỏ qua pytest warnings."
  },
  {
    name: "python-patterns",
    command: "/python-patterns",
    category: "architecture",
    checkpoint: "N/A",
    purpose: "Hướng dẫn áp dụng các mẫu thiết kế (design patterns) Python, quyết định kiến trúc, nguyên lý OOP và các thực hành viết code sạch (clean code).",
    input: "Yêu cầu thiết kế kiến trúc, blueprint kỹ thuật, sơ đồ cấu trúc",
    output: "Bản phác thảo thiết kế kiến trúc, đề xuất mẫu thiết kế phù hợp và code mẫu chuẩn hóa",
    pitfall: "Tránh lạm dụng các mẫu thiết kế phức tạp (over-engineering) cho các tác vụ đơn giản; giữ cấu trúc tối giản và dễ bảo trì."
  },
  {
    name: "go-development",
    command: "/go-dev",
    category: "implementation",
    checkpoint: "N/A",
    purpose: "Hướng dẫn các tác vụ phát triển Go bao gồm modules, build, test, lint và cấu trúc dịch vụ cơ bản.",
    input: "Yêu cầu sửa đổi/viết mã nguồn Go, tài liệu blueprint kỹ thuật",
    output: "Mã nguồn Go idiomatic, đã build và chạy test/lint thành công",
    pitfall: "Tránh bỏ qua xử lý lỗi tường minh (if err != nil); không sử dụng package global bừa bãi."
  },
  {
    name: "golang-pro",
    command: "/golang-pro",
    category: "implementation",
    checkpoint: "N/A",
    purpose: "Hướng dẫn lập trình Go nâng cao bao gồm lập trình đồng thời (goroutines, channels), đo kiểm hiệu năng (profiling), gRPC, generics và kiến trúc microservices.",
    input: "Yêu cầu tối ưu hóa hiệu năng, xử lý concurrency, gRPC API design",
    output: "Mã nguồn Go tối ưu, không có race condition, gRPC files, profiling data",
    pitfall: "Cảnh giác với goroutine leaks do thiếu hủy context; sử dụng mutex/channel không cẩn thận gây deadlock."
  },
  {
    name: "csharp-dotnet-pro",
    command: "/csharp-dotnet",
    category: "implementation",
    checkpoint: "N/A",
    purpose: "Hướng dẫn phát triển C# và .NET nâng cao bao gồm .NET 8/9, ASP.NET Core, EF Core, LINQ, async/await, xUnit/NUnit, Clean Architecture và Unity C#.",
    input: "Yêu cầu sửa đổi/viết mã C#/.NET, cấu hình dự án, tài liệu blueprint",
    output: "Mã nguồn C#/.NET chất lượng cao, các file project cập nhật, các unit tests tương thích",
    pitfall: "Cảnh giác với blocking async calls (.Result hoặc .Wait()); không giải phóng đúng tài nguyên dùng IDisposable."
  },
  {
    name: "web-design-guidelines",
    command: "/web-audit",
    category: "quality",
    checkpoint: "N/A",
    purpose: "Đánh giá mã nguồn giao diện web (UI) và tính tuân thủ các Hướng dẫn Giao diện Web (Web Interface Guidelines), khả năng truy cập (accessibility) và trải nghiệm người dùng (UX).",
    input: "Đường dẫn file/thư mục UI cần đánh giá, tài liệu thiết kế",
    output: "Báo cáo audit chi tiết chỉ ra các vi phạm UI/UX, đề xuất cải tiến và giải pháp khắc phục",
    pitfall: "Tránh tự ý sửa đổi code giao diện trước khi người dùng đồng ý với báo cáo audit; không áp dụng các quy chuẩn quá cứng nhắc làm mất đi tính độc đáo của thiết kế."
  }
];

