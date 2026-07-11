<!-- File path: docs/adr/ADR-026_storage_contract.md -->

# ADR-026: Storage Contract

## Status
Accepted

## Related Feature
FEAT-089

## Context
Xây dựng nền tảng thiết kế quản trị cho Storage Contract phục vụ kiến trúc AIWF OS. Đây là một hợp đồng kiến trúc cốt lõi quy định ranh giới cho các Blueprint và Implementation.

## Decision
Đồng ý cấu trúc hóa giao thức và các đặc tả thiết kế của Storage Contract theo mô hình modular, bảo mật và tương thích ngược.

## Alternatives Considered
- Option A: Thiết kế tự do cấp Skill. (Bị loại bỏ vì thiếu nhất quán).
- Option B: Tĩnh hóa toàn bộ ở mức CLI. (Lựa chọn được phê duyệt).

## Trade-offs
- Ưu điểm: Đảm bảo tính nhất quán tuyệt đối của hệ thống.
- Nhược điểm: Tăng chi phí thiết kế ban đầu.

## Consequences
Tất cả các Blueprint tương lai bắt buộc phải tuân thủ và ánh xạ trực tiếp tới đặc tả của hợp đồng này.

## Risks
- Rủi ro trôi lệch kiến trúc do triển khai sai đặc tả. Giải pháp: Validation Engine tự động đối chiếu các liên kết ADR.

## References
- related feature: FEAT-089
