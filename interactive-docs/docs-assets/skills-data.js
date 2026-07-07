// File path: docs/docs-assets/skills-data.js
const skillsData = [
  {
    name: "initialize-workflow",
    command: "/init",
    category: "runtime",
    checkpoint: "1",
    purpose: "Khởi tạo môi trường phát triển AI, cấu hình Git, đồng bộ RAG và chọn mức độ phân quyền (permission mode).",
    input: "workspace_path (auto), permission_mode (1, 2 hoặc 3)",
    output: "Khởi tạo tệp .agents/.session.json ghi nhận phiên làm việc.",
    pitfall: "Lệnh chạy không tương tác (non-interactive). Cần chọn chế độ 2 (Full Access) ngay từ đầu để hạn chế xác nhận Proceed liên tiếp khi AI viết code."
  },
  {
    name: "resume-workflow",
    command: "/resume",
    category: "runtime",
    checkpoint: "N/A",
    purpose: "Khôi phục lại phiên làm việc trước đó sau khi bị đứt quãng hoặc chuyển đổi giữa các cuộc hội thoại.",
    input: "Không có tham số bắt buộc.",
    output: "Đọc tệp .session.json, khôi phục nhánh Git và tự động đưa AI về đúng checkpoint đang làm dở.",
    pitfall: "Nếu tệp .session.json bị hỏng, lệnh sẽ tìm bản sao lưu .session.json.bak để tự phục hồi."
  },
  {
    name: "project-memory-update",
    command: "/memory-sync",
    category: "memory",
    checkpoint: "2",
    purpose: "Quét và phân tích toàn bộ git diff của dự án để cập nhật cơ sở dữ liệu vector RAG và file lessons learned.",
    input: "Được gọi tự động sau khi bắt đầu hoặc hoàn thành một tác vụ.",
    output: "Đồng bộ hóa bộ nhớ RAG của Agent với trạng thái thay đổi code thực tế trên đĩa.",
    pitfall: "Quên chạy lệnh này sau khi tự tay sửa code ngoài luồng có thể khiến Agent bị trôi lệch ngữ cảnh (context drift)."
  },
  {
    name: "brainstorming",
    command: "/brainstorm",
    category: "workflow",
    checkpoint: "3",
    purpose: "Phân tích yêu cầu, khảo sát kiến trúc mã nguồn hiện tại và lập giải pháp kỹ thuật sơ bộ dạng ý tưởng.",
    input: "Mô tả yêu cầu tính năng từ người dùng.",
    output: "Tạo file docs/brainstorming/FEAT-XXX_slug.md chứa kết quả khảo sát và ý tưởng giải pháp.",
    pitfall: "Nghiêm cấm viết code triển khai trong pha này. Chỉ dừng lại ở mức khảo sát ý tưởng."
  },
  {
    name: "brainstorming-to-plan",
    command: "/plan",
    category: "workflow",
    checkpoint: "4",
    purpose: "Chuyển đổi tài liệu brainstorm thành một kế hoạch thực thi chính thức gồm danh sách việc cần làm cụ thể.",
    input: "Tài liệu brainstorm đã duyệt.",
    output: "Tạo file docs/plans/FEAT-XXX_slug_plan.md và tệp theo dõi công việc task.md.",
    pitfall: "Bắt buộc phải áp dụng quy tắc Plan Synchronization: Sao chép implementation_plan.md từ IDE vào đúng thư mục docs/plans/ của dự án."
  },
  {
    name: "plan-to-blueprint",
    command: "/blueprint",
    category: "workflow",
    checkpoint: "5",
    purpose: "Thiết kế chi tiết cấu trúc hàm, định nghĩa API, cấu trúc bảng dữ liệu và chữ ký của code trước khi lập trình.",
    input: "Kế hoạch thực thi (Plan) đã được phê duyệt.",
    output: "Tạo file docs/designs/FEAT-XXX_slug_blueprint.md.",
    pitfall: "Bản thiết kế kỹ thuật (Blueprint) là bắt buộc. Agent không được tự tiện viết code nếu Blueprint chưa được người dùng gõ duyệt 'Y' (Approved)."
  },
  {
    name: "blueprint-to-implementation",
    command: "/implement",
    category: "workflow",
    checkpoint: "6",
    purpose: "Thực thi viết mã nguồn, sửa đổi logic các file trong dự án dựa theo đúng các chỉ dẫn trong Blueprint.",
    input: "Bản thiết kế kỹ thuật Blueprint đã được duyệt.",
    output: "Mã nguồn dự án được cập nhật thực tế.",
    pitfall: "Không được tự tiện refactor mã nguồn nằm ngoài phạm vi mô tả của Blueprint."
  },
  {
    name: "implementation-to-debug",
    command: "/debug",
    category: "workflow",
    checkpoint: "7",
    purpose: "Biên dịch dự án, chạy linter/compiler, phát hiện lỗi cú pháp, chạy tests và tự động sửa các lỗi này.",
    input: "Mã nguồn vừa chỉnh sửa.",
    output: "Tạo tệp chẩn đoán lỗi docs/debug/FEAT-XXX_debug.md với trạng thái PASS.",
    pitfall: "Phải đảm bảo dự án build thành công và không còn lỗi linting nghiêm trọng trước khi chuyển bước."
  },
  {
    name: "frontend-visual-debug",
    command: "/visual-debug",
    category: "workflow",
    checkpoint: "8",
    purpose: "Chạy kiểm QA giao diện trên WebView hoặc trình duyệt để kiểm tra trực quan các thay đổi UI (nếu có stack UI).",
    input: "Tệp mã nguồn UI vừa sửa.",
    output: "Báo cáo kiểm thử giao diện trực quan.",
    pitfall: "Sẽ tự động bị bỏ qua (skip) nếu cấu hình project-profile.json phát hiện dự án chỉ thuần Backend."
  },
  {
    name: "debug-to-verify",
    command: "/verify",
    category: "workflow",
    checkpoint: "9",
    purpose: "Kiểm tra tổng thể toàn bộ tính năng, đối chiếu với spec ban đầu và ký chấp nhận chất lượng sản phẩm để chuẩn bị release.",
    input: "Tệp chẩn đoán debug đạt trạng thái PASS.",
    output: "Tạo tệp nghiệm thu docs/verification/FEAT-XXX_verify.md trạng thái PASS.",
    pitfall: "Đây là cổng kiểm soát chất lượng cuối cùng trước khi code được phép đóng gói phát hành."
  },
  {
    name: "implementation-to-release",
    command: "/release",
    category: "workflow",
    checkpoint: "10",
    purpose: "Cập nhật số phiên bản (version bump), kết xuất changelog, commit, đánh tag git và push code lên GitLab/GitHub.",
    input: "Tệp nghiệm thu chất lượng verify đạt trạng thái PASS.",
    output: "Phát hành phiên bản mới lên Gitlab (code đầy đủ) và Github (bản xuất bản sạch public_export).",
    pitfall: "Nghiêm cấm tự động release. Tiến trình push và tag bắt buộc phải có lệnh duyệt thủ công từ người dùng."
  },
  {
    name: "software-development-workflow",
    command: "/workflow",
    category: "workflow",
    checkpoint: "N/A",
    purpose: "Điều phối viên trung tâm kiểm tra trạng thái workspace và chỉ dẫn bước đi/skill tiếp theo cho Agent.",
    input: "Tham số kiểm tra tự động.",
    output: "Báo cáo nhịp tim hệ thống và đề xuất lệnh chạy tiếp theo.",
    pitfall: "Luôn chạy lệnh này khi không biết Agent nên làm gì tiếp theo trong quy trình."
  },
  {
    name: "quick-fix",
    command: "/fix",
    category: "utility",
    checkpoint: "Rút gọn",
    purpose: "Sửa bug nhanh thông qua quy trình 3 pha rút gọn (Spec -> Blueprint -> Implement) bỏ qua các bước lập kế hoạch rườm rà.",
    input: "Mô tả bug cần sửa.",
    output: "Tạo file docs/issues/FIX-XXX_slug.md và hoàn thành sửa lỗi.",
    pitfall: "Chỉ được dùng cho các lỗi nhỏ, cô lập, có thời gian sửa dưới 4 tiếng."
  },
  {
    name: "quick-feature",
    command: "/feature",
    category: "utility",
    checkpoint: "Rút gọn",
    purpose: "Triển khai tính năng nhỏ thông qua quy trình 3 pha rút gọn (Spec -> Blueprint -> Implement) để tiết kiệm thời gian.",
    input: "Mô tả tính năng nhỏ cần thêm.",
    output: "Tạo file docs/quick/QUICK-XXX_slug.md và hoàn thành viết code.",
    pitfall: "Chỉ áp dụng cho tính năng đơn lẻ, không thay đổi cấu trúc bảng dữ liệu lớn hoặc kiến trúc lõi."
  },
  {
    name: "frontend-design",
    command: "/ui",
    category: "utility",
    checkpoint: "N/A",
    purpose: "Cung cấp các quy tắc tâm lý học hành vi người dùng, phối màu và bố cục typographic cho giao diện.",
    input: "Bản thiết kế giao diện UI.",
    output: "Hệ thống giao diện trực quan đạt chuẩn trải nghiệm người dùng.",
    pitfall: "Bắt buộc phải đọc file ux-psychology.md trước khi bắt đầu thiết kế."
  },
  {
    name: "project-discovery",
    command: "/discover",
    category: "environment",
    checkpoint: "N/A",
    purpose: "Quét cấu trúc thư mục dự án để tự động nhận diện ngôn ngữ, framework, database và công nghệ đang sử dụng.",
    input: "Mã nguồn dự án.",
    output: "Tạo tệp cấu hình project-profile.json điều hướng luồng SDLC.",
    pitfall: "Cần chạy khi mới tham gia dự án để Agent nắm được tech stack."
  },
  {
    name: "environment-bootstrap",
    command: "/bootstrap",
    category: "environment",
    checkpoint: "N/A",
    purpose: "Tự động tải và cài đặt các phụ trợ cần thiết cho môi trường làm việc của AI Coding.",
    input: "Lệnh cài đặt tự động.",
    output: "Môi trường lập trình được thiết lập sẵn sàng.",
    pitfall: "Một số công cụ chưa rõ nguồn gốc bắt buộc phải hỏi duyệt xác nhận từ người dùng."
  },
  {
    name: "environment-health",
    command: "/doctor",
    category: "environment",
    checkpoint: "N/A",
    purpose: "Khảo sát và chẩn đoán tình trạng sức khỏe môi trường của máy cục bộ (Git, Python, Docker, Qdrant, SQLite).",
    input: "Không có tham số.",
    output: "Bản báo cáo chẩn đoán chi tiết tình trạng hệ thống.",
    pitfall: "Là lệnh an toàn, chỉ đọc, không thay đổi bất cứ cấu hình hệ thống nào."
  },
  {
    name: "create-adr",
    command: "/adr",
    category: "architecture",
    checkpoint: "N/A",
    purpose: "Ghi chép và lưu trữ các quyết định thiết kế kiến trúc quan trọng có ảnh hưởng dài hạn đến dự án.",
    input: "Quyết định kiến trúc kỹ thuật.",
    output: "Tạo file docs/adr/ADR-XXX_slug.md.",
    pitfall: "Chỉ nên tạo khi dự án có sự thay đổi lớn về công nghệ hoặc mô hình lưu trữ."
  }
];
