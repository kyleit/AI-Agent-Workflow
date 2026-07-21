const skillsData = [
  {
    "name": "architecture-review",
    "command": "/audit-arch",
    "category": "architecture",
    "checkpoint": "N/A",
    "purpose": "Đánh giá kiến trúc thiết kế giải pháp thiết lập trước khi tạo Technical Design Blueprint.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "blueprint-to-implementation",
    "command": "/implement",
    "category": "workflow",
    "checkpoint": "6",
    "purpose": "Enforces Blueprint validation as the sole inputs for implementation, upgraded to support v3.2 JSON blueprints.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "brainstorming",
    "command": "/brainstorm",
    "category": "workflow",
    "checkpoint": "N/A",
    "purpose": "Complete, self-contained prompt for the brainstorming-to-plan Skill.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "brainstorming-to-plan",
    "command": "/plan",
    "category": "workflow",
    "checkpoint": "4",
    "purpose": "Execute a planning prompt from a master brainstorming document and generate a complete, production-ready Implementation Plan under docs/plans/.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "create-adr",
    "command": "/adr",
    "category": "architecture",
    "checkpoint": "N/A",
    "purpose": "This Skill is used to record and document critical architectural decisions and their trade-offs. It is invoked when plan-to-blueprint recommends an ADR, or when a developer determines a significant architecture decision is required.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "csharp-dotnet-pro",
    "command": "/csharp-dotnet",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Guides advanced C# and .NET development including C#, CSharp, dotnet, .NET 8, .NET 9, ASP.NET Core, EF Core, LINQ, async/await, xUnit, NUnit, Clean Architecture, and Unity C#.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "debug-to-verify",
    "command": "/verify",
    "category": "workflow",
    "checkpoint": "9",
    "purpose": "Perform a final qualitative and quantitative audit on the active feature implementation to ensure it meets all acceptance criteria, technical design blueprints, and security/performance standards before staging for release.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "document-compliance-assessment",
    "command": "/verify-doc",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Đánh giá điểm tuân thủ tài liệu và truy vết dựa trên quy tắc điều phối hệ thống.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "environment-bootstrap",
    "command": "/bootstrap",
    "category": "environment",
    "checkpoint": "N/A",
    "purpose": "Prepare and configure the local machine for the full Memory-Driven AI Coding Workflow.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "environment-health",
    "command": "/doctor",
    "category": "environment",
    "checkpoint": "N/A",
    "purpose": "Perform a complete, read-only inspection of the local development environment and return a detailed Environment Health Report.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "frontend-design",
    "command": "/ui",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Design thinking and decision-making for web UI. Use when designing components, layouts, color schemes, typography, or creating aesthetic interfaces. Teaches principles, not fixed values.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "frontend-visual-debug",
    "command": "/visual-debug",
    "category": "workflow",
    "checkpoint": "8",
    "purpose": "Validate frontend implementation visually. This Skill acts as the entry-point coordinator for the Visual Intelligence Runtime (VIR).",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "go-development",
    "command": "/go-dev",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Guides Go development tasks including modules, building, testing, linting, and basic service structure.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "golang-pro",
    "command": "/golang-pro",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Guides advanced Go programming including concurrency (goroutines, channels), performance profiling, gRPC, generics, and microservices architecture.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "implementation-to-debug",
    "command": "/debug",
    "category": "workflow",
    "checkpoint": "7",
    "purpose": "Review the implementation, verify builds, resolve compilation and linting issues, and fix unit tests before code verification.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "implementation-to-release",
    "command": "/release",
    "category": "workflow",
    "checkpoint": "10",
    "purpose": "Enforces explicit user-driven releases and requires blueprint validation before any release activities.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "initialize-workflow",
    "command": "/init",
    "category": "runtime",
    "checkpoint": "1",
    "purpose": "The initialize-workflow Skill compiles a lightweight, unified runtime context so subsequent Skills do not duplicate checks. All expensive operations (memory load, RAG connect, workspace scan, env CLI checks) are deferred to the skills that actually need them via the Runtime Dependency Resolver.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "knowledge-runtime",
    "command": "/knowledge-runtime",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Hỗ trợ quy trình knowledge-runtime.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "okr-report-generator",
    "command": "/okr",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Tự động phân tích hình ảnh bảng OKRs và tạo các báo cáo kỹ thuật summary.md và completed_tasks.md",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "orchestrator",
    "command": "/orchestrate",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "(DEPRECATED) Legacy autonomous execution orchestrator. Use workflow-coordinator instead.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "plan-to-blueprint",
    "command": "/blueprint",
    "category": "workflow",
    "checkpoint": "5",
    "purpose": "Generate a production-grade Technical Blueprint (Markdown & JSON) from an approved Implementation Plan using a Memory-First strategy and the FEAT-XXX Feature ID format.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "post-release-lifecycle",
    "command": "/post-release",
    "category": "workflow",
    "checkpoint": "N/A",
    "purpose": "Thực hiện quy trình vận hành và kiểm tra 10 bước nghiêm ngặt sau khi phát hành phiên bản.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "project-discovery",
    "command": "/discover",
    "category": "environment",
    "checkpoint": "N/A",
    "purpose": "Discover target project's technologies (languages, frameworks, compilers, test frameworks, lint tools, database systems, runtime environments, and infrastructure) and generate .agents/project-profile.json.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "project-memory-bootstrap",
    "command": "/project-memory-bootstrap",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Perform a complete, first-time analysis of the current project and generate all Project Memory layers under .agents/memory/.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "project-memory-update",
    "command": "/project-memory-update",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Perform an incremental update of Project Memory based on files changed since the last memory sync.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "project-rag-search",
    "command": "/project-rag-search",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Provide semantic retrieval of Project Memory in response to a natural language query.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "python-development",
    "command": "/python-dev",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Guides python development tasks including package management, testing, formatting, and linting.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "python-patterns",
    "command": "/python-patterns",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Hỗ trợ quy trình python-patterns.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "quick-feature",
    "command": "/feature",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Enforces a three-stage workflow (Specification, Blueprint, and Implementation) for quick features, upgraded with v3.2 Mini Spec quality standards and rich planning sections.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "quick-fix",
    "command": "/fix",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Enforces a three-stage workflow (Specification, Blueprint, and Implementation) for quick fixes, upgraded with v3.2 Mini Spec quality standards and rich planning sections.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "resume-workflow",
    "command": "/resume",
    "category": "runtime",
    "checkpoint": "N/A",
    "purpose": "The resume-workflow Skill allows the user or orchestrator to recover and continue execution from the last valid checkpoint stored in .agents/.session.json. It prevents configuration loss, context drift, and branch misalignment.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "skill-self-verification",
    "command": "/skill-self-verification",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Hỗ trợ quy trình skill-self-verification.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "software-development-workflow",
    "command": "/workflow",
    "category": "workflow",
    "checkpoint": "N/A",
    "purpose": "This Skill is the central coordinator of the entire AI Coding Platform. It acts as a Project Manager to determine the current phase, verify Quality Gates, check Blueprint approvals, perform raw request classification, and recommend the single correct next Skill to run.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "vir-investigate",
    "command": "/vir-investigate",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Hỗ trợ quy trình vir-investigate.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "vir-memory-update",
    "command": "/vir-memory-update",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Hỗ trợ quy trình vir-memory-update.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "vir-runtime",
    "command": "/vir-runtime",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Hỗ trợ quy trình vir-runtime.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "vir-verify",
    "command": "/vir-verify",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Hỗ trợ quy trình vir-verify.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "web-design-guidelines",
    "command": "/web-audit",
    "category": "utility",
    "checkpoint": "N/A",
    "purpose": "Review web user interfaces (UI) and code for compliance with Web Interface Guidelines. Use when asked to review UI, check accessibility, audit design, review UX, or check a site against best practices.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "workflow-coordinator",
    "command": "/tick",
    "category": "workflow",
    "checkpoint": "N/A",
    "purpose": "The workflow-coordinator skill acts as the stateless entry gate and logical manager of the AI Engineering Workflow. It is invoked on every user tick to parse incoming instructions, enforce gates, load/verify split-state files, check active workflow resume priority, and output deterministic suggestions for the next skill to invoke. It explicitly prohibits the creation of background daemons, heartbeat monitors, or resident loops.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  },
  {
    "name": "workflow-runtime",
    "command": "/runtime",
    "category": "runtime",
    "checkpoint": "N/A",
    "purpose": "The workflow-runtime Skill acts as the centralized execution state controller for all AI skills. It encapsulates atomic session updates, Git check-pointing, token usage estimations, context drift checks, and workspace validations.",
    "input": "Tùy thuộc vào yêu cầu của skill.",
    "output": "Kết quả thực thi tương ứng.",
    "pitfall": "Không có thông tin cụ thể."
  }
];
