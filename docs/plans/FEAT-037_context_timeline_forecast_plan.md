<!-- File path: docs/plans/FEAT-037_context_timeline_forecast_plan.md -->

---
feature_id: FEAT-037
feature_name: Context Timeline & Predictive Analytics
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-037_context_timeline_forecast.md
next_artifact: ../designs/FEAT-037_context_timeline_forecast_blueprint.md
---

# FEAT-037: Context Timeline & Predictive Analytics

## Objective
- **Business Objective**: Cung cấp cho nhà phát triển một bảng biểu diễn dòng thời gian (Context Timeline) phản ánh chính xác các sự kiện hoạt động của workflow, đi kèm công cụ phân tích dự báo (Predictive Engine) giúp cảnh báo sớm trước khi context quá tải.
- **Expected Outcome**:
  - Ghi nhận 12 loại sự kiện AIWF và lưu vào SQLite.
  - Phân tích hồi quy dự đoán thời điểm hết hạn context, xác suất quá tải và dự toán chi phí còn lại.
  - Thêm tab Timeline trực quan với đồ thị, markers, và panel dự báo.
  - CLI hỗ trợ các lệnh: `usage timeline` và `usage forecast`.

## Scope

### Included
- Thiết kế bảng SQLite `timeline_events`.
- Phát triển module `forecaster.py` chịu trách nhiệm dự đoán.
- CLI hỗ trợ các subcommand timeline và forecast.
- Giao diện Tab Timeline Dashboard vẽ đồ thị xu hướng và list sự kiện.

### Excluded
- Không tích hợp thư viện vẽ biểu đồ nặng bên ngoài (như Chart.js, D3.js) để tránh làm phình extension. Chúng ta sẽ tự vẽ đồ thị bằng SVG thuần hoặc Canvas để đảm bảo hiệu năng tối ưu nhất.

## Project Impact
- **Database**: Thêm 1 bảng SQLite mới.
- **CLI**: Mở rộng các subcommands dòng lệnh của `workflow_runtime.py`.
- **Webview**: Thêm tab Timeline và các thành phần DOM.

## Dependencies
- Dữ liệu lịch sử request từ `provider_requests`.

## Risks
- **Risk**: Dự báo độ lệch cao do lịch sử ít request.
  - **Mitigation**: Hiển thị mức độ tin cậy (Confidence levels) dạng thấp (Low) khi số lượng request < 3.

## Acceptance Criteria
- [ ] Sự kiện ghi nhận đúng loại vào SQLite.
- [ ] Công thức dự toán tính toán chính xác và ổn định.
- [ ] Giao diện Webview hiển thị đầy đủ thông tin dòng sự kiện và dự báo.

## Deliverables
- Module `forecaster.py`.
- Sửa đổi di trú SQLite trong `db.py`.
- Sửa đổi lệnh CLI trong `workflow_runtime.py`.
- Trang tab Timeline trong `webview.html` & `extension.ts`.

## Estimated Complexity
- **Medium**: Cần phối hợp xử lý toán học dự báo và vẽ giao diện dòng sự kiện SVG.
