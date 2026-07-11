# ADR-048: Program B Cognitive Routing and Self-Healing

- **Status**: Proposed
- **Program**: Program B
- **Domain**: Intelligence
- **Related FEATs**: FEAT-110
- **Related Initiatives**: Initiative B1, B2
- **Related Capabilities**: Cap-003
- **Related AIWF v1 ADRs**: ADR-005, ADR-044

## Context & Problem
Chi phí token lớn khi gửi toàn bộ logs của chuỗi hội thoại dài và thiếu khả năng tự sửa lỗi khi validation build hỏng.

## Decision
Triển khai bộ lọc Context Compressor nén logs bằng NLP và bộ định tuyến thông minh (Model Router). Khi build lỗi, tự động kích hoạt Healer gửi prompt sửa lỗi tới LLM.

## Consequences
- **Positive**: Tiết kiệm 40% chi phí token và tự động sửa các lỗi cú pháp nhỏ.
- **Negative**: Tăng độ trễ tính toán nén ngữ cảnh.

## Backward Compatibility
Sử dụng cấu trúc context của v1 để làm đầu vào nén.
