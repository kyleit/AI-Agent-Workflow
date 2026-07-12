# AIWF Skill Development Guide

Hướng dẫn từng bước thiết kế và tích hợp Skill mới vào hệ sinh thái AIWF.

## 1. Viết cấu hình SKILL.md
Mọi Skill phải khai báo YAML frontmatter đầy đủ:
```yaml
name: ten-skill
command: lenh-chay
checkpoint: checkpoint-sdlc
```

## 2. Giao tiếp qua SDK
- Cấm tự khởi tạo orchestrator riêng.
- Sử dụng SDK để yêu cầu khóa tài nguyên trước khi ghi đĩa.
