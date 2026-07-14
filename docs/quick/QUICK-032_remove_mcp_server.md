<!-- File path: docs/quick/QUICK-032_remove_mcp_server.md -->
---
artifact_type: quick-feature-spec
feature_id: QUICK-032
workflow: quick-feature
status: pending
---
# Mini Plan & Feature Specification – Remove MCP Server and Keep Logical Workflow

## 1. Feature Goal
Loại bỏ hoàn toàn các thành phần liên quan đến MCP Server (bao gồm MCP server code, manager, auto-provisioning logic, các adapter và các tệp tin kiểm thử liên quan) khỏi codebase của dự án `ai-skill-framework`, nhằm khôi phục và tinh gọn hệ thống chỉ giữ lại logical workflow thuần túy và ổn định.

## 2. Quick Feature Justification
- **Estimated Complexity**: Low/Medium (Chủ yếu là xóa bỏ các file cô lập và tinh chỉnh/revert một số dòng code tích hợp trong runtime scripts)
- **Implementation Scope**: Scoped local refactoring (Chỉ thay đổi trong `skills/workflow-runtime/` và các thư mục liên quan)
- **Architectural Impact**: Low/Medium (Loại bỏ một tính năng phụ trợ/ngoại vi, làm tinh gọn core runtime)
- **Risk Level**: Low (Có bộ unit test phong phú để kiểm định không hồi quy)
- **Justification**: Đây là tác vụ dọn dẹp và tinh giản mã nguồn, không làm thay đổi các quy trình SDLC cốt lõi hay cấu trúc dữ liệu chính, hoàn toàn phù hợp với quy trình phát triển nhanh (Quick Feature).

## 3. Scope Boundary
- **In Scope**:
  - Xóa toàn bộ thư mục `skills/workflow-runtime/mcp/` (chứa manager, registry, server và các adapters cho vscode, cursor, antigravity).
  - Xóa toàn bộ thư mục `skills/workflow-runtime/adapters/` (chứa các wrapper mcp và antigravity gateway).
  - Xóa các tệp kiểm thử liên quan đến MCP trong `skills/workflow-runtime/tests/`:
    - `test_antigravity_workflow_adapter.py`
    - `test_mcp_antigravity_adapter.py`
    - `test_mcp_manager.py`
  - Sửa đổi `skills/workflow-runtime/scripts/workflow_runtime.py`:
    - Xóa hàm xử lý `do_mcp(args)`.
    - Xóa định nghĩa subcommand parser cho lệnh `mcp` (install, uninstall, status, doctor).
    - Loại bỏ `"mcp"` ra khỏi danh sách `modifying_actions`.
    - Loại bỏ entry `"mcp": do_mcp` ra khỏi dictionary mapping các action.
  - Sửa đổi `skills/workflow-runtime/scripts/session_bootstrap_guard.py`:
    - Loại bỏ phần import `manager` từ `mcp` và logic kiểm tra/cài đặt tự động (auto-provisioning) MCP wrapper cho Antigravity IDE trong hàm khởi động session.
- **Out of Scope**:
  - Không sửa đổi bất kỳ logic điều phối workflow cốt lõi nào (như `init`, `start`, `step`, `complete`, `blueprint`, `recovery`, `locks`, v.v.).
  - Không thay đổi các quy tắc kiểm thử và ghi nhật ký chung của hệ thống.
- **Not Modified**:
  - Các skill khác ngoài `workflow-runtime`.
  - Các cấu trúc lưu trữ dữ liệu của runtime state.

## 4. Trigger / Execution Flow
- **Entry Point**: Triển khai các chỉnh sửa code và chạy bộ kiểm thử để đảm bảo tính ổn định của core runtime sau khi loại bỏ MCP.
- **Completion Condition**: Mã nguồn liên quan đến MCP bị xóa hoàn toàn, các subcommand `mcp` không còn khả dụng, dự án chạy biên dịch và kiểm thử bình thường (PASS).

## 5. Runtime Sequence
```
Khởi động Session (Bootstrap)
   ↓
(Không còn chạy check/install MCP)
   ↓
Runtime nhận các action
   ↓
(Chặn/Không nhận action 'mcp' nữa)
```

## 6. Dependency Contract
- **Required Dependencies**: pytest để chạy kiểm thử xác thực.
- **Optional Dependencies**: None.
- **External Runtime**: Python 3.13+.

## 7. Error Matrix
| Condition | Expected Behavior | User Visibility | Recovery Action |
|---|---|---|---|
| Chạy lệnh `workflow_runtime.py mcp` | Trình parse CLI báo lỗi lệnh không tồn tại | invalid choice: 'mcp' | Sử dụng các subcommand hợp lệ khác |
| Lỗi import khi xóa mcp folder | Runtime crash | ImportError | Đảm bảo xóa sạch các lệnh import liên quan đến mcp trong scripts |

## 8. Non-functional Requirements
- **Performance Expectations**: Việc loại bỏ auto-provisioning MCP lúc khởi động session sẽ giúp giảm thời gian chạy lệnh `init` và tăng tốc độ khởi tạo phiên làm việc.
- **Blocking vs Asynchronous**: Đồng bộ.
- **Idempotency**: Các thao tác dọn dẹp là an toàn.

## 9. Logging Requirements
- Không còn log cảnh báo hay thông báo cài đặt MCP wrapper khi khởi tạo session.

## 10. Configuration Impact
- **Existing Configs Reused**: Không còn kiểm tra hay tạo các tệp cấu hình của MCP.

## 11. Design Constraints
- Loại bỏ hoàn toàn sự phụ thuộc vào các MCP client/server API.
- Chỉ giữ lại logical workflow trong core scripts.

## 12. Blast Radius
- **Affected Skills**: `workflow-runtime`
- **Affected Runtime**: workflow-runtime scripts
- **Affected Extension**: Không ảnh hưởng trực tiếp (extension Visualizer chỉ hiển thị UI telemetry).
- **Affected Memory**: None
- **Affected Documentation**: Xóa bỏ các báo cáo cũ `docs/releases/FEAT-315...` và `docs/releases/FEAT-316...` (nếu cần thiết) hoặc giữ lại dạng archive.
- **Affected Scripts**: `workflow_runtime.py`, `session_bootstrap_guard.py`
- **Impact Level**: Medium (Do can thiệp vào CLI parser và bootstrap guard).

## 13. File Change Scope
- **Modify**:
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `skills/workflow-runtime/scripts/session_bootstrap_guard.py`
- **Delete**:
  - `skills/workflow-runtime/mcp/` (Thư mục)
  - `skills/workflow-runtime/adapters/` (Thư mục)
  - `skills/workflow-runtime/tests/test_antigravity_workflow_adapter.py`
  - `skills/workflow-runtime/tests/test_mcp_antigravity_adapter.py`
  - `skills/workflow-runtime/tests/test_mcp_manager.py`

## 14. Success Metrics
- **Regression free**: Yes (Tất cả unit tests và E2E tests còn lại phải đạt trạng thái PASS).
- **CLI Cleanliness**: Lệnh `workflow_runtime.py -h` không hiển thị subcommand `mcp`.
- **Performance**: Thời gian khởi tạo `init` giảm nhẹ.

## 15. Rollback Strategy
- **Safe Rollback Steps**: `git checkout -- skills/workflow-runtime/ && git checkout HEAD -- skills/workflow-runtime/mcp skills/workflow-runtime/adapters skills/workflow-runtime/tests/test_*mcp*` (hoặc restore bằng git).

## 16. Expanded Acceptance Criteria
- [ ] AC-01 (Loại bỏ code): Xóa sạch các thư mục `mcp/`, `adapters/` và các file test liên quan.
- [ ] AC-02 (Loại bỏ CLI): Lệnh `python skills/workflow-runtime/scripts/workflow_runtime.py mcp` không còn hoạt động và báo lỗi parse.
- [ ] AC-03 (Loại bỏ Bootstrap): Khởi chạy `init` session không còn chạy bất kỳ tiến trình kiểm tra hay cài đặt MCP nào.
- [ ] AC-04 (Không hồi quy): Bộ unit test chạy qua `pytest` cho phần runtime còn lại (dashboard state, state cli, session, v.v.) phải PASS 100%.

## 17. Self Verification
- Chạy thử `pytest` cho toàn bộ thư mục `skills/workflow-runtime/tests` sau khi dọn dẹp code để kiểm chứng.
- Kiểm tra trợ giúp CLI: `python skills/workflow-runtime/scripts/workflow_runtime.py -h` xem còn lệnh `mcp` không.

## 18. Open Questions
- Không có.

## 19. Blueprint Handoff
Technical Design Blueprint ở Phase 2 sẽ xác định chính xác các dòng code cần xóa trong `workflow_runtime.py` và `session_bootstrap_guard.py` và các lệnh shell để dọn dẹp file.
