<!-- File path: docs/plans/FEAT-005_project_planning_refactoring_plan.md -->

# Kế hoạch triển khai - Phân tách Lập kế hoạch dự án (Project Planning) và Thiết kế kỹ thuật (Technical Design Blueprint)

Chào Ba, đây là bản kế hoạch lưu trong dự án để phân rã rõ ràng ranh giới trách nhiệm giữa pha Lập kế hoạch (Planning) và Thiết kế (Blueprint).

## 1. Mục tiêu
- **Pha Lập kế hoạch (Project Planning)**: Tập trung hoàn toàn vào khía cạnh quản lý dự án (Tại sao cần làm? Phạm vi? Ảnh hưởng? Rủi ro? Tiêu chí nghiệm thu?). Tuyệt đối không thiết kế các cấu trúc kỹ thuật (sơ đồ lớp, database schema, API, code signature).
- **Pha Thiết kế (Technical Design Blueprint)**: Trở thành nguồn chân lý kỹ thuật duy nhất, sở hữu toàn bộ các cấu trúc kỹ thuật đã loại bỏ khỏi Lập kế hoạch.

## 2. Các thay đổi chi tiết
- **skills/planning-prompt-to-plan/SKILL.md**: Cập nhật khuôn mẫu sinh file `docs/plans/FEAT-XXX_*.md` chỉ tập trung vào khía cạnh quản lý dự án.
- **skills/plan-to-blueprint/SKILL.md**: Cập nhật luồng đọc đầu vào (từ cả `docs/brainstorming/` và `docs/plans/`) để sinh ra blueprint kỹ thuật đầy đủ chi tiết.
- **AGENTS.md & AI_RULES.md**: Cập nhật quy tắc hướng dẫn Agent để tôn trọng ranh giới phân vai mới.
- **README.md, SKILLS.md, INSTALL.md**: Đồng bộ hóa mô tả các pha.
- **MANIFEST.json & CHANGELOG.md**: Bumps phiên bản lên 1.6.0.

## 3. Kế hoạch kiểm tra
- Đọc kiểm tra chéo các Skill để đảm bảo tính nhất quán.
- Xác thực cú pháp tệp cấu hình MANIFEST.json.
