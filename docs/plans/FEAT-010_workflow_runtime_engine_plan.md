<!-- File path: docs/plans/FEAT-010_workflow_runtime_engine_plan.md -->

---
feature_id: FEAT-010
feature_name: AI Workflow Runtime Engine Refactor
status: draft
stage: planning
created_at: 2026-07-06
updated_at: 2026-07-06
previous_artifact: ../brainstorming/FEAT-010_workflow_runtime_engine.md
next_artifact: ../designs/FEAT-010_workflow_runtime_engine_blueprint.md
---

# Project Plan – AI Workflow Runtime Engine Refactor

Bản kế hoạch quản lý dự án xây dựng công cụ điều khiển Runtime tập trung thưa Ba.

## 1. Mục tiêu dự án
*   **Mục tiêu chính**: Trích xuất toàn bộ logic điều khiển tệp `.session.json`, chẩn đoán sức khỏe, ước lượng token, kiểm tra Git branch, tạo báo cáo chẩn đoán và nhịp tim (heartbeat) ra khỏi chỉ dẫn của kỹ năng. Đóng gói thành một công cụ dòng lệnh (CLI Runtime Engine) Python dùng chung.
*   **Mục tiêu chất lượng**: Đảm bảo 100% khả năng tương thích ngược của cấu trúc `.session.json` đối với Visualizer extension. Toàn bộ 26 kỹ năng được cập nhật thành công để chuyển sang gọi API CLI.

## 2. Phạm vi thực hiện (Scope & Boundaries)
*   **Nằm trong phạm vi**:
    *   Xây dựng mã nguồn Runtime Engine dưới dạng CLI Python trong thư mục `skills/workflow-runtime/scripts/`.
    *   Tách biệt cấu trúc thành các tệp chuyên biệt (session, context, validator, heartbeat, v.v.), giới hạn tối đa 200 dòng/tệp.
    *   Tái cấu trúc và tối ưu hóa toàn bộ 26 kỹ năng dưới `skills/` để gọi CLI Runtime.
    *   Xây dựng bộ unit tests toàn diện cho CLI Runtime Engine.
    *   Tài liệu hóa kiến trúc mới trong `workflow-runtime/README.md` và viết báo cáo di trú `docs/runtime_refactor_report.md`.
*   **Nằm ngoài phạm vi**:
    *   Không thay đổi quy trình SDLC hoặc cơ cấu các bước/checkpoint (từ 1 đến 10).
    *   Không đóng gói MCP Tool hay viết extension code trong giai đoạn này (chỉ thiết kế API mở để sẵn sàng cho tương lai).

## 3. Các đầu mục công việc & Các pha (Tasks & Milestones)
*   **Pha 1: Thiết kế kỹ thuật (Technical Blueprint)**
    *   Định nghĩa đặc tả chi tiết giao diện CLI (Runtime API).
    *   Phác thảo cấu trúc và trách nhiệm các tệp Python.
*   **Pha 2: Phát triển Runtime Engine & Unit Tests**
    *   Triển khai mã nguồn Python CLI dưới `skills/workflow-runtime/scripts/`.
    *   Viết unit tests bao phủ các tình huống ghi lỗi, phục hồi phiên chạy lỗi, xung đột đồng thời ghi, v.v. dưới `skills/workflow-runtime/tests/`.
*   **Pha 3: Tái cấu trúc kỹ năng (Skills Refactoring)**
    *   Cập nhật 26 kỹ năng chuyển sang gọi lệnh CLI.
    *   Đồng bộ thay đổi vào thư mục `.agents/skills/`.
*   **Pha 4: Kiểm duyệt & Lập báo cáo di trú**
    *   Chạy chẩn đoán workspace qua `doctor.ps1` và xác thực hoạt động của hệ thống.
    *   Viết báo cáo di trú `docs/runtime_refactor_report.md`.

## 4. Rủi ro & Giải pháp giảm thiểu (Risks & Mitigations)
*   **Rủi ro 1: Sai lệch cấu trúc tệp `.session.json` làm hỏng Webview**
    *   *Giảm thiểu*: Tích hợp cơ chế tự động xác thực schema JSON (validator.py) trước khi ghi tệp nguyên tử.
*   **Rủi ro 2: CLI hoạt động không nhất quán trên các HĐH**
    *   *Giảm thiểu*: Sử dụng thư viện chuẩn của Python (`os`, `json`, `argparse`, `shutil`) tương thích đa nền tảng.

## 5. Kế hoạch kiểm duyệt chất lượng (Verification Plan)
*   [ ] Biên dịch và chạy thành công bộ unit tests cho Runtime CLI.
*   [ ] Chạy `powershell .\update.ps1 -Force` thành công.
*   [ ] Chạy chẩn đoán `doctor.ps1` đạt kết quả PASS hoàn toàn.
