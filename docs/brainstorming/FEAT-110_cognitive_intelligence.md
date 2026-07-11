<!-- docs/brainstorming/FEAT-110_cognitive_intelligence.md -->

---
feature_id: FEAT-110
feature_name: Cognitive Intelligence & Optimization
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-110_cognitive_intelligence_plan.md
---

# Master Requirement Document – Cognitive Intelligence & Optimization

## Executive Summary
Triển khai hệ thống tự sửa lỗi (self-healing), tối ưu hóa token bằng nén ngữ cảnh ngữ nghĩa và định tuyến model thông minh.

## Background
Chi phí token của các LLM cao cấp lớn và khả năng lập kế hoạch dài hạn dễ bị lệch mục tiêu ban đầu.

## Current AIWF v1 Analysis
Tự động ngắt khi vượt hạn mức Token qua `BudgetController`.

## Gap Analysis
Chưa có khả năng tự động viết lại code sửa lỗi khi validation thất bại mà không cần can thiệp từ người dùng.

## Objectives
Tự động khôi phục và tinh chỉnh prompt ngữ cảnh thông minh.

## Scope
- Nén ngữ cảnh log bằng NLP.
- Định tuyến prompt theo độ phức tạp.

## Out of Scope
- Tự động huấn luyện mô hình (fine-tuning).

## Functional Requirements
- **FR-01**: Tóm tắt tự động chat log dài.
- **FR-02**: Tự phát hiện và sửa cú pháp lỗi khi build hỏng.

## Non-Functional Requirements
- **NFR-01**: Giảm tối thiểu 40% lượng token gửi đi.

## Architecture Proposal
Sử dụng Lớp đệm Transformer (Context Compressor Layer) lọc và định vị các dòng logs quan trọng trước khi gửi đi.

## Runtime Components
- `ContextCompressor`
- `ErrorSelfHealer`

## Data Model
Lưu trữ lịch sử hội thoại dạng vector embeddings thu gọn.

## Runtime State
`COMPRESSING` -> `ROUTING` -> `SELF_HEALING`.

## Integration Points
Tương tác trực tiếp với `ValidationEngine` của v1 để kích hoạt logic sửa lỗi.

## Public APIs
- `compress_context(prompt: str) -> str`

## Internal APIs
- `_calculate_complexity(prompt: str) -> str`

## Event Model
- `token_limit_warning`: Phát ra khi sắp cạn token budget.

## State Machine
- `OPTIMIZING` -> `HEALING` -> `RESUMING`

## Sequence Flow
1. Kiểm thử lỗi -> Kích hoạt healer.
2. Nén ngữ cảnh -> Gửi prompt mới.

## Security
Không lọc bỏ các quy định an toàn hệ thống (system prompt) khi nén.

## Performance
Thời gian nén văn bản nhỏ hơn 200ms.

## Scalability
Hỗ trợ nén lịch sử chat dài tới 1 triệu token.

## Fault Tolerance
Fallback sang model gốc chất lượng cao nhất nếu model tối ưu bị lỗi kết quả.

## Disaster Recovery
Lưu trữ cache prompt cục bộ tránh mất kết nối API.

## Multi-Tenant Considerations
Hạn mức token được kiểm soát độc lập cho từng session ID.

## Observability
Báo cáo tỷ lệ token tiết kiệm được lên Dashboard.

## Risks
- Nén quá đà làm mất thông tin lỗi cốt lõi. Giải pháp: Giữ nguyên logs lỗi gần nhất.

## Trade-offs
- Trễ nén tăng nhẹ đổi lại tiết kiệm đáng kể chi phí.

## Migration Strategy
Nâng cấp cấu hình `workflow.config.json` để thêm các tham số mô hình mới.

## Backward Compatibility
Tương thích hoàn toàn với cấu trúc state của v1.

## Acceptance Criteria
- [ ] Sửa lỗi build tự động thành công.
- [ ] Giảm chi phí token đúng chỉ tiêu.

## Estimated ADR Count
4 ADRs.

## Estimated Blueprint Count
2 Blueprints.

## Estimated Implementation Phases
2 Phases.
