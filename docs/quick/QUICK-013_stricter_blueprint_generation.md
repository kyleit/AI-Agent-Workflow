<!-- File path: docs/quick/QUICK-013_stricter_blueprint_generation.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-013
workflow: quick-feature
status: pending
---
# Mini Feature Specification – Stricter Blueprint Generation

## 1. Feature Goal
Nâng cấp `plan-to-blueprint` Skill để Technical Design Blueprint được sinh ra trong tương lai đóng vai trò là một "Hợp đồng triển khai" (Implementation Contract) chặt chẽ, chính xác và không có yếu tố mơ hồ. Người kỹ sư hoặc AI triển khai tiếp theo sẽ không phải đưa ra bất kỳ quyết định kiến trúc nào khác.

## 2. Scope

### In Scope:
Cập nhật tệp `skills/plan-to-blueprint/SKILL.md` để bắt buộc áp dụng các quy tắc kiểm tra (validation rules) sau khi sinh Blueprint:

1. **Đường dẫn tương đối**: Cấm hoàn toàn việc sinh đường dẫn tuyệt đối hoặc định dạng `file://` links trong thiết kế và sơ đồ của Blueprint. Tất cả tham chiếu tệp phải là đường dẫn tương đối từ gốc workspace.
2. **Tính tương thích ngược của Schema**: Mọi schema trạng thái mới phải giữ tính tương thích ngược với `.agents/.session.json` hiện tại. Định nghĩa rõ ràng vị trí và luật di trú (migration rules) cho các trường cũ (legacy fields).
3. **Enum an sau**: Đối với trường `permission_mode`, chỉ cho phép hai giá trị hợp lệ: `sandbox` và `full_access`. Tuyệt đối cấm tự chế các giá trị không an toàn như `unrestricted`.
4. **Xác thực đường dẫn Pseudo-code**: Đảm bảo các đường dẫn tệp trong pseudo-code hoặc thuật toán là chính xác (ví dụ: `.agents/.session.json` không được biến thành `.agents/session.json`).
5. **Đầy đủ Acceptance Criteria**: Khai báo bao nhiêu test cases/assertions thì phải liệt kê và ánh xạ chi tiết toàn bộ (ví dụ: nếu ghi có 11 tests thì phải mô tả và map đủ 11 tests, không viết "Task 2..11").
6. **Yêu cầu đối với thay đổi Extension**: Nếu tính năng ảnh hưởng đến extension (VSCode/Antigravity extension), Blueprint bắt buộc phải định nghĩa:
   - ViewModel schema
   - File watch strategy
   - Debounce behavior
   - Fallback order
   - Giao diện người dùng khi state bị thiếu/hỏng (missing/corrupted state UI)
   - Các quy tắc làm mới một phần (partial refresh rules)
7. **Mục "Backward Compatibility & Migration Mapping" bắt buộc**: Chứa bảng ánh xạ gồm:
   - old field
   - new file
   - new field
   - migration rule
   - recovery rule
8. **Mục "Disallowed Outputs" validation bắt buộc**: Chứa phần cam kết và kiểm tra tự động trước khi lưu:
   - no file://
   - no absolute paths
   - no `...`
   - no TBD
   - no unsafe permission values
   - no unmapped legacy fields

### Out of Scope:
* Không refactor cấu trúc thư mục của các skill khác.
* Không thay đổi mã nguồn của CLI workflow runtime trừ khi cần thiết để hỗ trợ validation (ở đây chỉ cập nhật luật của skill sinh Blueprint).

## 3. Acceptance Criteria
* Tệp `skills/plan-to-blueprint/SKILL.md` được cập nhật đầy đủ 8 quy tắc validation trên.
* Toàn bộ test suite của workflow-runtime chạy pass thành công.
