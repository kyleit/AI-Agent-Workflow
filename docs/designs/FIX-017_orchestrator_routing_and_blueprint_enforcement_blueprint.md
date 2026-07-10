---
artifact_type: blueprint
issue_id: FIX-017
workflow: quick-fix
status: draft
---
# Technical Design Blueprint – Fix Orchestrator Routing & Blueprint Enforcement

## 1. Proposed Code Changes

### [skills/workflow-runtime/scripts/workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py)
- **Operation**: MODIFY
- **Responsibility**: Bổ sung validation chặn cứng tại hàm `do_start` của CLI engine.
- **Changes**:
  - Trong hàm `do_start(args)`, trước khi lưu trạng thái session, kiểm tra xem nếu `args.skill == "blueprint-to-implementation"` hoặc `args.checkpoint` $\ge 6$:
    - Lấy thông tin `blueprint` từ session.
    - Nếu `blueprint` chưa tồn tại hoặc `approved` là `False`:
      - In thông báo lỗi chi tiết ra stdout/stderr và thoát bằng `sys.exit(1)`.
      - Ngăn chặn hoàn toàn việc chuyển trạng thái session sang Phase 6 (Implementation) khi chưa được duyệt Blueprint.

### [skills/orchestrator/SKILL.md](file:///Volumes/Kyle/AgentsProject/skills/orchestrator/SKILL.md)
- **Operation**: MODIFY
- **Responsibility**: Cập nhật quy tắc hành vi điều phối, cơ chế tự động Dispatch Skill và tuân thủ Blueprint của Orchestrator.
- **Changes**:
  - **Tự động Dispatch Skill**:
    - Khi Orchestrator phân loại (detect) được yêu cầu của người dùng tương ứng với một Workflow Skill (như `quick-fix`, `quick-feature`, hoặc `brainstorming`):
      - Orchestrator **PHẢI ngay lập tức chuyển quyền điều phối (dispatch)** cho Skill đó chạy tiếp.
      - Agent bắt buộc phải tuân thủ nghiêm ngặt 100% quy trình (rules & guides) của Skill mục tiêu đó (ví dụ đối với `quick-fix` và `quick-feature` là mô hình 3 Phase: Specification -> Blueprint -> Implementation; đối với `brainstorming` là Brainstorming -> Planning -> Blueprint).
      - Nghiêm cấm Agent tự ý bỏ qua quy trình để viết code trực tiếp.
  - **Quy tắc phối hợp giữa Antigravity IDE và Framework**:
    - `implementation_plan.md` (artifact của IDE Antigravity) chỉ đóng vai trò là "cầu nối phê duyệt" kỹ thuật với IDE (chứa danh sách thay đổi và checklist kiểm thử).
    - Nội dung của `implementation_plan.md` phải tuân thủ và khớp 100% với tệp Design Blueprint (`docs/designs/FEAT-XXX_*` hoặc `docs/designs/FIX-XXX_*`) trong dự án.
    - Agent không được tự biên tự diễn giải pháp mới trong `implementation_plan.md` nếu chưa có Design Blueprint được duyệt.

---

## 2. Target Folder Structure
Không thay đổi cấu trúc thư mục hiện tại.

---

## 3. Interface & Data Contracts
Không thay đổi giao diện CLI hoặc các state models của session hiện tại. Chỉ thêm validation logic.

---

## 4. Algorithms & Key Logic

### Logic validate blueprint trong `do_start`:
```python
def do_start(args):
    session = load_session()
    if not session:
        session = {"workspace": {"path": ".", "valid": True}}
        
    # Check blueprint approval before implementation
    is_impl = (args.skill == "blueprint-to-implementation") or (args.checkpoint is not None and args.checkpoint >= 6)
    if is_impl:
        bp = session.get("blueprint", {})
        if not bp.get("approved"):
            print("Error: Cannot start implementation. Technical Design Blueprint is not approved.", file=sys.stderr)
            print("Please create a design blueprint and approve it using: aiwf blueprint --approve <path> first.", file=sys.stderr)
            sys.exit(1)
            
    session["status"] = "in_progress"
    ...
```

---

## 5. Validation Rules
- Lệnh `aiwf start --skill blueprint-to-implementation` phải trả về exit code 1 và in thông báo lỗi nếu tệp `.session.json` có `"blueprint": {"approved": false}`.

---

## 6. Implementation Checklist
- [ ] Sửa đổi hàm `do_start` trong `skills/workflow-runtime/scripts/workflow_runtime.py`
- [ ] Sửa đổi `skills/orchestrator/SKILL.md` bổ sung cơ chế Dispatch Skill và hướng dẫn hành vi điều phối phối hợp với `implementation_plan.md`

---

## 7. Verification & Test Plan

### Automated Tests
- Chạy unit tests:
  `PYTHONPATH=skills/workflow-runtime/scripts pytest skills/workflow-runtime/tests/`
- Viết thêm một test case trong `test_runtime.py` để kiểm tra việc chặn của `do_start` khi chưa duyệt blueprint.

### Manual Verification
- Sửa `"blueprint": {"approved": false}` trong `.session.json`.
- Chạy:
  `python3 skills/workflow-runtime/scripts/workflow_runtime.py start --skill blueprint-to-implementation --command implement --checkpoint 6 --step "Testing"`
- Xác nhận CLI báo lỗi và trả về exit code `1`.
