<!-- File path: docs/issues/FIX-024_missing_obsidian_folder_mappings.md -->
---
artifact_type: fix-spec
issue_id: FIX-024
workflow: quick-fix
status: pending
---
# Mini Plan & Fix Specification – Missing Obsidian Folder Mappings

## 1. Issue Description
Khi chạy tiến trình đồng bộ bộ nhớ sang Obsidian (sync), chỉ có một phần các tài liệu tri thức trong `docs/` được sao chép (như `brainstorming`, `plans`, `designs`, `adr`, `releases`). Các tệp tri thức quan trọng khác bao gồm:
* `docs/quick/` (Đặc tả tính năng nhanh QUICK)
* `docs/issues/` (Đặc tả bản vá lỗi QUICK)
* `docs/prompts/` (Mẫu prompts hệ thống tái sử dụng)
* `docs/verification/` (Kết quả chạy walkthrough / self-verify)
* `docs/debug/` (Nhật ký sửa lỗi)
* `docs/archive/` (Tài liệu lưu trữ)

không nằm trong danh sách ánh xạ thư mục mặc định `folder_mapping`. Điều này làm cho đồ thị Graph View của Obsidian bị thiếu hụt các nốt tri thức quan trọng, gây đứt gãy tính liên kết tri thức của cả dự án.

## 2. Scope
- **In Scope**:
  - Bổ sung các thư mục tri thức bị thiếu vào cấu hình ánh xạ thư mục mặc định trong script [provider_manager.py](file:///Volumes/Kyle/AgentsProject/skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py).
  - Phân loại ánh xạ tri thức chính xác theo bản chất:
    - `"docs/quick": "Brainstorming"` (Quick Feature là Đặc tả tính năng, đồng bộ vào cùng thư mục Brainstorming).
    - `"docs/issues": "Plans"` (Quick Fix là Bản kế hoạch vá lỗi, đồng bộ vào cùng thư mục Plans).
    - `"docs/prompts": "Prompts"` (Đồng bộ vào thư mục Prompts).
    - `"docs/verification": "Verification"` (Đồng bộ vào thư mục Verification).
    - `"docs/debug": "Debug"` (Đồng bộ vào thư mục Debug).
    - `"docs/archive": "Archive"` (Đồng bộ vào thư mục Archive).
  - Cập nhật tệp cấu hình [memory.config.json](file:///Volumes/Kyle/AgentsProject/.agents/memory.config.json) của dự án để phản ánh các ánh xạ bổ sung này.
- **Out of Scope**:
  - Thay đổi logic so sánh mã băm MD5 hoặc logic dịch liên kết chéo của Obsidian Sync.

## 3. Quick Fix Justification
Giải thích lý do tác vụ đủ điều kiện vá lỗi nhanh thay vì chu trình SDLC đầy đủ:
- **Estimated Complexity**: Low (chỉ bổ sung cấu hình ánh xạ thư mục tĩnh).
- **Implementation Scope**: Single local configuration change (thay đổi file JSON cấu hình và 1 từ điển mặc định trong Python).
- **Architectural Impact**: Low / Purely additive configurations.
- **Risk Level**: Low (không ảnh hưởng tới mã nguồn logic động).
- **Justification**: Khắc phục lỗi thiếu sót cấu hình đồng bộ, đưa tài liệu Spec QUICK về đúng thư mục Brainstorming, Spec FIX về đúng thư mục Plans, và các thư mục tài liệu khác về đúng thư mục chuyên biệt trên Obsidian Graph View.

## 4. Trigger / Execution Flow
- **Entry Point**: Khi chạy đồng bộ Obsidian qua CLI `provider sync obsidian` hoặc khi kết thúc tiến trình `bootstrap` / `update` bộ nhớ.
- **Trigger Source**: User kích hoạt CLI hoặc tiến trình Project Memory tự động gọi ngầm.
- **Execution Order**: Tiến trình duyệt qua danh sách cấu hình `folder_mapping` (bao gồm các thư mục mới thêm) và sao chép từng thư mục tương ứng.
- **Completion Condition**: Toàn bộ tệp spec/tri thức mới được sao chép và dịch liên kết sang Obsidian thành công.

## 5. Runtime Sequence
```text
Gọi sync Obsidian (thủ công hoặc tự động)
               ↓
Đọc folder_mapping mới từ memory.config.json (hoặc default)
               ↓
Duyệt qua docs/quick, docs/issues, docs/prompts, docs/verification, docs/debug, docs/archive
               ↓
Sao chép & dịch liên kết Markdown sang wiki-links
               ↓
Cập nhật tệp ánh xạ obsidian-sync-map.json
```

## 6. Dependency Contract
- **Required Dependencies**: Obsidian provider được bật và cấu hình đường dẫn `vault_root` hợp lệ.
- **Expected Contracts**: Không thay đổi.

## 7. Error Matrix
| Condition | Expected Behavior | User Visibility | Recovery Action |
|---|---|---|---|
| Workspace directory empty | Bỏ qua không lỗi, in log warning | Log warning trong CLI | Tạo thư mục hoặc tiếp tục |

## 8. Non-functional Requirements
- **Performance Expectations**: Tăng thêm không quá 0.5 giây cho tiến trình đồng bộ tổng thể.
- **Idempotency**: Đảm bảo idempotency hoàn toàn dựa trên mã băm MD5.

## 9. Logging Requirements
- **Progress**: In log các tệp tin Spec QUICK/FIX và các tài liệu khác được chép sang Obsidian.

## 10. Configuration Impact
- **Existing Configs Reused**: Cập nhật trực tiếp tệp `memory.config.json`.
- **Backward Compatibility**: Tương thích hoàn toàn với cấu hình cũ.

## 11. Design Constraints
- Không đổi schema database hay thay đổi cấu trúc mã nguồn động.

## 12. Blast Radius
Xác định các thành phần bị ảnh hưởng và đánh giá mức độ tác động:
- **Affected Skills**: knowledge-runtime
- **Affected Runtime**: provider_manager.py
- **Affected Memory**: memory.config.json
- **Impact Level**: Low

## 13. File Change Scope
Biên giới tác động mã nguồn thực tế:
- **Modify**:
  - `skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py`
  - `.agents/memory.config.json`

## 14. Success Metrics
- **Regression free**: Yes
- **Backward compatible**: Yes
- **Implementation completeness**: 100%

## 15. Rollback Strategy
- Hoàn nguyên tệp tin bằng `git checkout`.

## 16. Expanded Acceptance Criteria
- [ ] AC-01 (Success Path): Chạy `python skills/workflow-runtime/scripts/workflow_runtime.py provider sync obsidian` -> Sao chép thành công toàn bộ Spec QUICK sang thư mục `Brainstorming` và Spec FIX sang thư mục `Plans` của Obsidian.
- [ ] AC-02 (Backward Compatibility): Các dự án cũ không có các thư mục này vẫn chạy đồng bộ bình thường mà không crash.
- [ ] AC-03 (No duplicate execution): Chạy lại lần 2 không sao chép trùng lặp tệp.

## 17. Self Verification
- [ ] Kiểm tra các tệp tin QUICK đã xuất hiện trong thư mục `Brainstorming` và FIX trong `Plans` trên Obsidian vault của dự án.
- [ ] Chạy `pytest` đảm bảo 23/23 tests pass.

## 18. Open Questions
- Không có câu hỏi nào.

## 19. Blueprint Handoff
Bản thiết kế kỹ thuật ở Phase 2 bắt buộc phải làm rõ:
- Cấu trúc cập nhật cụ thể của từ điển `folder_mapping` mặc định trong [provider_manager.py](file:///Volumes/Kyle/AgentsProject/skills/knowledge-runtime/scripts/knowledge_runtime/provider_manager.py).
- Cấu trúc cập nhật của [memory.config.json](file:///Volumes/Kyle/AgentsProject/.agents/memory.config.json).
