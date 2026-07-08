---
name: skill-self-verification
description: Tự động kiểm tra và xác thực các Skill trong AI Skill Framework để bảo đảm chất lượng và tính ổn định.
command: /verify-skill
aliases:
  - verify-skill
  - skill-verify
  - self-verify
category: quality
tags:
  - verification
  - testing
  - skills
  - runtime
---

# Skill Self-Verification

Skill này dùng để kiểm tra tính đúng đắn và sự tương thích của các Skill khác trong hệ thống trước khi phát hành (release).

## 1. Purpose & Scope
Mục tiêu là tự động hóa quá trình xác thực các Skill mới được tạo hoặc chỉnh sửa để đảm bảo:
- Cấu trúc thư mục, tệp tin và metadata trong `SKILL.md` hợp lệ.
- Không vi phạm các chính sách an toàn của `AI_RULES.md` (chẳng hạn như cấm sử dụng link `file://` tuyệt đối).
- Các luồng nghiệp vụ thông thường (Happy Path) và lỗi đầu vào (Invalid Inputs) hoạt động chính xác.
- Tương tác với người dùng giả lập được mô phỏng đầy đủ.

## 2. Input Schema
- `skill` (string, required): Tên thư mục của Skill cần kiểm tra.

## 3. Workflow
1. **Static Analysis Phase**: Quét metadata, YAML frontmatter, và đường dẫn tương đối trong `SKILL.md`.
2. **Simulation Phase**: Thực thi các kịch bản tương tác người dùng giả lập để kiểm tra phản hồi.
3. **Runtime & Boundary Phase**: Kiểm tra sự tương thích với state engine thông qua tệp `.agents/.session.json`.
4. **Report Generation Phase**: Xuất báo cáo markdown tại `docs/verification/SKILL-VERIFY_<skill-name>.md`.

## 4. Run Commands
```bash
python skills/skill-self-verification/scripts/verify_skill.py verify --skill <skill-name>
```

## 5. Completion Criteria
- Báo cáo xác thực được tạo thành công với kết quả `PASS`.
- Không phát hiện vi phạm quy tắc an toàn.
