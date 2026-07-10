---
artifact_type: blueprint
feature_id: QUICK-028
workflow: quick-feature
status: draft
---
# Technical Design Blueprint – Add Provider Command to AIWF CLI

## 1. Proposed Code Changes

### [bootstrap.sh](file:///Volumes/Kyle/AgentsProject/bootstrap.sh)
- **Operation**: MODIFY
- **Responsibility**: Bổ sung hiển thị lệnh trợ giúp và ánh xạ định tuyến lệnh Unix.
- **Changes**:
  - Hàm `show_help()`: Thêm hai dòng mô tả cho `provider` và `sync`.
  - Khối `case "$COMMAND" in`: Thêm nhánh xử lý cho `provider` và `sync`.

### [bootstrap.ps1](file:///Volumes/Kyle/AgentsProject/bootstrap.ps1)
- **Operation**: MODIFY
- **Responsibility**: Bổ sung hiển thị lệnh trợ giúp và ánh xạ định tuyến lệnh Windows PowerShell.
- **Changes**:
  - Hàm `Show-Help`: Thêm hai dòng mô tả cho `provider` và `sync`.
  - Khối `switch ($Command)`: Thêm nhánh xử lý cho `"provider"` và `"sync"`.

---

## 2. Target Folder Structure
Giữ nguyên cấu trúc thư mục hiện tại của dự án:
```text
.
├── bootstrap.sh
└── bootstrap.ps1
```

---

## 3. Interface & Data Contracts
- **CLI Commands Added**:
  - `aiwf provider [subaction] [options]`: Gọi chuyển tiếp đến `workflow_runtime.py provider [subaction] [options]`
  - `aiwf sync [provider_name] [options]`: Gọi chuyển tiếp trực tiếp đến `workflow_runtime.py provider sync [provider_name] [options]`

---

## 4. Algorithms & Key Logic
Wrapper chỉ làm nhiệm vụ chuyển tiếp nguyên trạng tham số qua `$@` (Unix) hoặc `@args` (PowerShell) đến tệp đích Python:

**Unix shell forwarding logic:**
```bash
    provider)
        python3 "$FRAMEWORK_ROOT/skills/workflow-runtime/scripts/workflow_runtime.py" provider "$@"
        ;;
    sync)
        python3 "$FRAMEWORK_ROOT/skills/workflow-runtime/scripts/workflow_runtime.py" provider sync "$@"
        ;;
```

**PowerShell forwarding logic:**
```powershell
    "provider" {
        python (Join-Path `$FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") provider @args
    }
    "sync" {
        python (Join-Path `$FrameworkRoot "skills/workflow-runtime/scripts/workflow_runtime.py") provider sync @args
    }
```

---

## 5. Validation Rules
- Lệnh `sync` và `provider` chỉ chạy thành công nếu dự án đã cấu hình và tích hợp Python 3 cùng thư viện `knowledge-runtime`.

---

## 6. Implementation Checklist
- [ ] Cập nhật tệp `bootstrap.sh` (Hàm trợ giúp và case statement).
- [ ] Cập nhật tệp `bootstrap.ps1` (Hàm trợ giúp và switch-case).
- [ ] Chạy lệnh tái cài đặt wrapper: `./bootstrap.sh` để kiểm tra.

---

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - `aiwf` hoặc `aiwf help` phải liệt kê `provider` và `sync`.
  - `aiwf sync obsidian` chạy thành công tiến trình đồng bộ sang Obsidian.
