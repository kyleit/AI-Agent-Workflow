---
artifact_type: blueprint
issue_id: FIX-026
workflow: quick-fix
status: draft
---
# Technical Design Blueprint – Add Init and Test Commands to AIWF CLI

## 1. Proposed Code Changes

### [bootstrap.ps1](file:///E:/AgentsProject/bootstrap.ps1)
- **Operation**: MODIFY
- **Responsibility**: Bổ sung hỗ trợ các lệnh `bootstrap`, `init` và `test` vào wrapper CLI PowerShell toàn cục `aiwf.ps1`.
- **Changes**:
  - Cập nhật hàm `Show-Help` hiển thị 3 lệnh mới.
  - Bổ sung 3 case-branch tương ứng trong switch-case của `aiwf.ps1` generated script block.

## 2. Target Folder Structure
Kiến trúc thư mục không thay đổi:
```text
.
├── bootstrap.ps1
└── docs/
    ├── issues/
    │   └── FIX-026_add_init_to_aiwf_cli.md
    └── designs/
        └── FIX-026_add_init_to_aiwf_cli_blueprint.md
```

## 3. Interface & Data Contracts
- **API/CLI Contracts**:
  - `aiwf bootstrap [args...]` ➔ gọi `bootstrap.ps1`
  - `aiwf init [args...]` ➔ gọi `workflow_runtime.py init`
  - `aiwf test [args...]` ➔ gọi `workflow_runtime.py test`

## 4. Algorithms & Key Logic
Switch case mapping:
```powershell
switch ($Command) {
    "bootstrap" {
        & (Join-Path $FrameworkRoot "bootstrap.ps1") @args
    }
    "init" {
        python (Join-Path $FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") init @args
    }
    "test" {
        python (Join-Path $FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") test @args
    }
    # ... các lệnh cũ ...
}
```

## 5. Validation Rules
- Lệnh con không hợp lệ sẽ hiển thị thông báo lỗi `Unknown command` cùng với danh sách trợ giúp.

## 6. Implementation Checklist
- [ ] Cập nhật hàm `Show-Help` và switch-case trong `bootstrap.ps1`.
- [ ] Chạy `bootstrap.ps1` cục bộ để tái lập trình / đăng ký lại wrapper CLI toàn cục trong `$env:LOCALAPPDATA/aiwf/bin`.
- [ ] Chạy xác thực bằng cách gọi thử `aiwf init` và `aiwf test validate`.

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: `aiwf bootstrap` khởi chạy thành công trình cài đặt.
  - *REQ-002*: `aiwf init` khởi tạo lại session trạng thái.
  - *REQ-003*: `aiwf test validate` kiểm tra thành công cấu trúc kiến trúc kiểm thử.
