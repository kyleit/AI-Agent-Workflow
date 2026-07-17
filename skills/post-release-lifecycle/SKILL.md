---
name: post-release-lifecycle
command: post-release
aliases:
  - post-ship
  - post-lifecycle
category: review
tags:
  - release
  - post-release
  - operational
  - monitoring
  - maintenance
version: 1.0.0
license: MIT
repository: https://gitlab.com/hngan.it/ai-workflow-skills
created_at: 2026-07-17
updated_at: 2026-07-17
description: Thực hiện quy trình vận hành và kiểm tra 10 bước nghiêm ngặt sau khi phát hành phiên bản.
runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
---

# Skill: Post-Release Lifecycle

Thực hiện quy trình vận hành, giám sát và kiểm tra 10 bước nghiêm ngặt sau khi phát hành mã nguồn để đảm bảo tính ổn định của hệ thống production.

---

## 🔒 WORKFLOW RUNTIME & INITIALIZATION CHECK

Skill này bắt buộc phải kết nối với Python CLI Runtime Engine:
- **Validate Checkpoint**: Xác nhận checkpoint hiện tại trước khi thực thi.
- **Tiến trình**:
  - *Start*: `python skills/workflow-runtime/scripts/workflow_runtime.py start --skill "post-release-lifecycle" --command "post-release" --checkpoint 11 --step "Starting post-release validation..."`
  - *Complete*: `python skills/workflow-runtime/scripts/workflow_runtime.py complete --checkpoint 11 --step "Post-Release Lifecycle Complete"`

---

## 📋 Quy trình 10 bước Hậu Phát hành (Post-Release Lifecycle)

Quy trình bắt buộc đi qua đầy đủ 10 bước hành động sau để lập báo cáo vận hành:

### Bước 1: Chạy Post-Release Validation
Thực thi kiểm tra khói (smoke check) bằng script kiểm tra tự động để đảm bảo hệ thống runtime khởi động bình thường.
```bash
python skills/workflow-runtime/scripts/post_release_lifecycle.py <version> <commit>
```

### Bước 2: Tạo báo cáo Post-Release Validation Report
Hệ thống tự động xuất tệp tin `docs/reviews/post_release_validation_report.md` chứa kết quả chạy thử nghiệm và cấu hình.

### Bước 3: Thiết lập Production Monitoring
Kích hoạt các tác vụ giám sát nền (cron job/health checker) để giám sát tài nguyên và lỗi.

### Bước 4: Tạo báo cáo Production Monitoring Report
Xuất tệp tin `docs/reviews/production_monitoring_report.md` ghi nhận xu hướng sử dụng tài nguyên (CPU/RAM) và tỷ lệ lỗi.

### Bước 5: Thực hiện Maintenance Transition
Thực hiện dọn dẹp hệ thống, vacuum cơ sở dữ liệu SQLite và kiểm tra zombie process.

### Bước 6: Tạo báo cáo Maintenance Status Report
Xuất tệp tin `docs/reviews/maintenance_status_report.md` liệt kê các giới hạn vận hành hiện tại và các lỗi ngoại lệ phát hiện.

### Bước 7: Đánh giá Runtime Governance
Kiểm tra tính bảo mật, cấu hình quyền hạn và phân loại mức độ thay đổi của phiên bản vừa release.
* Báo cáo ghi nhận tại `docs/reviews/runtime_governance_report.md`.

### Bước 8: Phân tích Cải tiến Liên tục (Continuous Improvement)
Nhận diện các điểm nghẽn hiệu năng phát sinh trong phiên bản mới và lưu báo cáo cải tiến tại `docs/reviews/continuous_improvement_report.md`.

### Bước 9: Đánh giá độ trưởng thành vận hành (Operational Maturity Assessment)
Chấm điểm các thước đo vận hành gồm: Reliability, Security, và Observability.
* Yêu cầu đạt mức điểm tối thiểu 95/100 điểm tổng thể.
* Báo cáo ghi nhận tại `docs/reviews/operational_maturity_assessment.md`.

### Bước 10: Xây dựng Runtime Roadmap
Thiết lập lộ trình phát triển và các thứ tự ưu tiên của các tính năng tiếp theo tại `docs/reviews/runtime_roadmap.md`.

---

## 🛑 Điều kiện bắt buộc chặn (NO-GO)

Hệ thống sẽ bị coi là lỗi vận hành nghiêm trọng và đánh trạng thái FAILED nếu:
1. Gặp lỗi khi chạy kiểm tra khói ở Bước 1.
2. Tỷ lệ lỗi (Error Rate) của runtime vượt quá 0.5%.
3. Điểm Operational Maturity Assessment đạt dưới 90/100 điểm.
4. Phát hiện tiến trình zombie không tự động dọn dẹp sau khi kiểm tra.
