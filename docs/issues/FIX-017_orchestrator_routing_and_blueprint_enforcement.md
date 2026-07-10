---
artifact_type: fix-spec
issue_id: FIX-017
workflow: quick-fix
status: pending
---
# Fix Specification – Fix Orchestrator Routing & Blueprint Enforcement

## 1. Issue Description
Người dùng (Ba) phản ánh hai lỗi hành vi nghiêm trọng liên quan đến cơ chế điều phối và tuân thủ Blueprint của AI Skill Framework:
- **Lỗi 1 (Không điều phối, tự ý code)**: Khi Ba gọi lệnh `/orchestrator` (hoặc `aiwf` CLI tương ứng), hệ thống không điều phối chạy bất kỳ Skill nào của framework (như `brainstorming`, `planning`, `blueprint`). Hệ thống đã nhảy trực tiếp vào bước code và sửa đổi các tệp nguồn (`install.sh`, `workflow_runtime.py`,...) mà không có bất kỳ Design Blueprint nào được phê duyệt trước đó. Đây là hành vi vi phạm nghiêm trọng quy tắc an toàn: *"Không có blueprint trên thư mục quy định thì không code"*.
- **Lỗi 2 (Tự vẽ ra file kế hoạch trùng lặp)**: Khi dự án đã có sẵn Design Blueprint trong `docs/designs/`, Agent vẫn tự tạo thêm tệp `implementation_plan.md` (của Antigravity IDE) và yêu cầu người dùng chấp nhận thay vì trực tiếp thực thi dựa trên Design Blueprint đã có sẵn. Điều này gây khó hiểu, trùng lặp và làm giảm vai trò của Design Blueprint.

## 2. Scope
- **In Scope**:
  - Phân tích và sửa đổi cơ chế lập lịch / điều phối của `orchestrator` trong `skills/orchestrator/SKILL.md` và Python CLI engine `workflow_runtime.py` để bắt buộc kiểm tra sự tồn tại và phê duyệt của Blueprint tại Project level (`docs/designs/FEAT-XXX_*_blueprint.md` hoặc `docs/designs/FIX-XXX_*_blueprint.md`) trước khi cho phép bất kỳ hành vi sửa đổi mã nguồn nào.
  - Cải tiến hướng dẫn hành vi của Agent để làm rõ mối quan hệ giữa `implementation_plan.md` (mặt tiếp xúc IDE bắt buộc của Antigravity) và `Design Blueprint` (tài liệu thiết kế gốc của framework): `implementation_plan.md` của Antigravity chỉ được phép đóng vai trò là danh sách các tệp sẽ thay đổi và checklist kiểm thử **dựa trên** nội dung của Design Blueprint đã được approve, tuyệt đối không được tự vẽ ra giải pháp thiết kế mới khác với Design Blueprint.
  - Đảm bảo khi gọi `/orchestrator`, hệ thống luôn định tuyến chính xác qua các skill trung gian của Phase (Brainstorming -> Planning -> Blueprint) trước khi chuyển sang Phase Implementation.
- **Out of Scope**:
  - Không thay đổi các thuật toán lập lịch song song (Parallel execution) hoặc cấu trúc logic khóa tệp (file locking) không liên quan.
