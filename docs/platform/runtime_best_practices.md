# AIWF Runtime Best Practices

Các thói quen tốt và hướng dẫn gỡ lỗi dành cho kỹ sư phát triển Skill.

## 1. Viết mã nguồn an toàn (Defensive Coding)
- Luôn kiểm tra quyền thực thi thông qua `CapabilityEngine` trước khi thực hiện các tác vụ nhạy cảm như ghi đĩa hoặc gọi git.
- Sử dụng cơ chế ghi tệp nguyên tử (atomic rename) để tránh hỏng dữ liệu khi gặp sự cố cúp nguồn đột ngột.

## 2. Gỡ lỗi
- Tra cứu trực tiếp logs sự kiện từ tệp tin timeline tập trung [timeline.jsonl](file:///.agents/state/timeline.jsonl).
