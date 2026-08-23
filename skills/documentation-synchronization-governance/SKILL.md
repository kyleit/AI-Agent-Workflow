---
name: documentation-synchronization-governance
description: Supports transactional synchronization between source code changes and workflow documentation.
canonical_entrypoint: false
user_invokable: false
governance_support_skill: true
path_policy: REPOSITORY_RELATIVE
repository_root_representation: "."
allow_absolute_paths: false
---

# Skill: documentation-synchronization-governance

## 1. Overview & Core Invariants
Skill `documentation-synchronization-governance` chịu trách nhiệm duy trì tính đồng bộ giao dịch (transactional synchronization) tuyệt đối giữa thay đổi mã nguồn và toàn bộ bộ tài liệu workflow.

> [!CRITICAL]
> **Three Mandatory Invariants**:
> 1. `NO REQUIRED DOCUMENT = NO CODE`: Không được phép ghi mã nguồn khi thiếu bất kỳ tài liệu bắt buộc nào.
> 2. `NO BLUEPRINT = NO CODE`: Không được phép ghi mã nguồn khi chưa có Technical Design Blueprint hoàn chỉnh, đạt canonical `CODE_BLOCK_GATE = PASS` từ `strict-code-block-gate`, có `blueprint_full_sha256` khớp hiện tại, và đã được phê duyệt.
> 3. `NO DOCUMENT UPDATE = NO SOURCE CHANGE COMPLETION`: Thay đổi mã nguồn và cập nhật tài liệu liên quan BẮT BUỘC nằm trong cùng một giao dịch (`SOURCE_DOCUMENT_CHANGESET`). Không được phép coi nguồn xong khi tài liệu bị `STALE` hoặc `MISSING`.

---

## 2. Document Lifecycle States
Mỗi tài liệu trong workflow chỉ có đúng một trong các trạng thái sau:
- `MISSING`: Chưa tạo tệp.
- `DRAFT`: Đang trong quá trình tạo/sửa.
- `READY_FOR_REVIEW`: Chờ thẩm định độc lập.
- `APPROVED`: Đã được phê duyệt bởi cơ quan phê duyệt tương ứng.
- `FROZEN`: Đã đông băng sau phê duyệt (không được sửa nếu không qua Change Request).
- `CURRENT`: Đồng bộ hoàn toàn với mã nguồn và SHA-256 hiện tại.
- `STALE`: Lỗi thời do mã nguồn hoặc tài liệu phụ thuộc phía trên đã thay đổi.
- `INVALIDATED`: Bị hủy hiệu lực do thay đổi Blueprint/đầu vào.
- `BACKFILL_REQUIRED`: Cần bổ sung tài liệu sau khi phát hiện thiếu hụt.
- `NOT_APPLICABLE`: Không áp dụng cho biến thể workflow hiện tại.

---

## 3. DOCUMENTATION_SYNC_GATE Execution Points
`DOCUMENTATION_SYNC_GATE` bắt buộc phải tự động kích hoạt tại các điểm:
1. Ngay sau mỗi `SOURCE_DOCUMENT_CHANGESET`.
2. Trước khi hoàn tất phase (`phase completion`).
3. Trước khi thực thi lệnh `@aiwf next`.
4. Trong lệnh `@aiwf continue` tại cuối mỗi phase độc lập.
5. Trước khi đánh dấu `FEATURE_IMPLEMENTATION_COMPLETED`.
6. Trước khi chuyển sang trạng thái `READY_FOR_DEBUG`.

---

## 4. Blueprint Invalidation Rules
Nếu một thay đổi mã nguồn chạm vào các vùng đã freeze (architecture, public interface, schema, behavior, AC, ownership, state machine, security, migration, compatibility):
1. Đặt `BLUEPRINT_CHANGE_REQUIRED = true`.
2. Dừng ngay lập tức thao tác ghi mã nguồn.
3. Tạo `Blueprint Change Request`.
4. Đánh dấu Blueprint là `STALE`.
5. Hủy hiệu lực (`INVALIDATED`): `CODE_BLOCK_GATE`, `Blueprint Approval`, `Blueprint Freeze`, `Implementation Approval`. Bất kỳ thay đổi nào ở code block, metadata (`id`, `language`, `file`, `operation`, `implementation_ready`), strict language profile registry, hoặc target path đều làm stale `code-block-gate.json` và bắt buộc chạy lại `strict-code-block-gate`.
6. Yêu cầu tạo mới Blueprint và chạy lại toàn bộ quy trình thẩm định/phê duyệt trước khi cấp quyền ghi mã nguồn mới.
