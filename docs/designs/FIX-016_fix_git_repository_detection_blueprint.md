<!-- File path: docs/designs/FIX-016_fix_git_repository_detection_blueprint.md -->
---
feature_id: FIX-016
feature_name: Fix Git Repository Detection for Worktrees/Submodules
status: reviewed
stage: blueprint
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: docs/issues/FIX-016_fix_git_repository_detection.md
next_artifact: install.sh
---

# Technical Design Blueprint – Fix Git Repository Detection for Worktrees/Submodules

## 0. Baseline Context & References
- **Memory Baseline**: Đã phân tích các script `install.sh`, `install.ps1`, `update.sh`, `update.ps1`, `doctor.sh`, `doctor.ps1`.
- **RAG Query Summaries**: Đã quét các file script chứa từ khóa `.git`.
- **Inspected Source Files**:
  - `install.sh` (dòng 52)
  - `install.ps1` (dòng 24)
  - `doctor.sh` (dòng 94)
  - `doctor.ps1` (dòng 83)
  - `update.sh` (dòng 93)
  - `update.ps1` (dòng 50)

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `install.sh` | `MODIFY` | Thay thế việc kiểm tra thư mục `.git` cứng nhắc bằng kiểm tra worktree thông qua `git rev-parse` và tự động `cd` về Git root. | `git` command | Thấp. Giúp cài đặt chính xác hơn trên macOS/Linux. |
| `install.ps1` | `MODIFY` | Cập nhật logic kiểm tra tương tự `install.sh` trên Windows PowerShell. | `git` command | Thấp. Giúp cài đặt chính xác hơn trên Windows. |
| `doctor.sh` | `MODIFY` | `cd` về Git root trước khi chẩn đoán trạng thái dự án. | `git` command | Thấp. Tránh bỏ qua kiểm tra khi chạy ngoài root. |
| `doctor.ps1` | `MODIFY` | `Set-Location` về Git root trước khi chẩn đoán trạng thái dự án. | `git` command | Thấp. Tránh bỏ qua kiểm tra trên Windows. |
| `update.sh` | `MODIFY` | Tự động chuyển về Git root trước khi thực hiện cập nhật framework. | `git` command | Thấp. |
| `update.ps1` | `MODIFY` | Tự động chuyển về Git root trước khi thực hiện cập nhật framework trên Windows. | `git` command | Thấp. |
| `public_export/install.sh` | `MODIFY` | Đồng bộ các sửa đổi của `install.sh`. | `git` command | Thấp. |
| `public_export/install.ps1` | `MODIFY` | Đồng bộ các sửa đổi của `install.ps1`. | `git` command | Thấp. |
| `public_export/doctor.sh` | `MODIFY` | Đồng bộ các sửa đổi của `doctor.sh`. | `git` command | Thấp. |
| `public_export/doctor.ps1` | `MODIFY` | Đồng bộ các sửa đổi của `doctor.ps1`. | `git` command | Thấp. |
| `public_export/update.sh` | `MODIFY` | Đồng bộ các sửa đổi của `update.sh`. | `git` command | Thấp. |
| `public_export/update.ps1` | `MODIFY` | Đồng bộ các sửa đổi của `update.ps1`. | `git` command | Thấp. |

## 2. Target Folder Structure
```text
.
├── doctor.ps1
├── doctor.sh
├── install.ps1
├── install.sh
├── update.ps1
├── update.sh
└── public_export
    ├── doctor.ps1
    ├── doctor.sh
    ├── install.ps1
    ├── install.sh
    ├── update.ps1
    └── update.sh
```

## 3. Interface Contracts (Public & Internal)
- **Public Interface Contracts**:
  - Không thay đổi tham số đầu vào của các script.
- **Internal Component Contracts**:
  - Các script phải giữ nguyên luồng cài đặt và chỉ thay đổi cách phát hiện thư mục cài đặt.

## 4. Algorithms & Logic Specifications

### 4.1. Thuật toán kiểm tra và chuyển hướng trong Bash (`.sh` files):
```bash
is_git_worktree() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1
}

get_git_root() {
  git rev-parse --show-toplevel 2>/dev/null
}

# Kiểm tra sự tồn tại của git CLI
if ! command -v git &> /dev/null; then
    # Git không tồn tại, kiểm tra xem có tệp/thư mục .git ở đây không
    if [ -d ".git" ] || [ -f ".git" ]; then
        PROJECT_ROOT="."
    else
        log_error "git command line tool is missing, and no .git folder/file found."
        exit 1
    fi
else
    # Git tồn tại, kiểm tra worktree
    if ! is_git_worktree; then
        if [ -d ".git" ] || [ -f ".git" ]; then
            PROJECT_ROOT="."
        else
            log_error "The current directory is not a Git repository."
            exit 1
        fi
    else
        PROJECT_ROOT="$(get_git_root)"
    fi
fi

cd "$PROJECT_ROOT" || exit 1
```

### 4.2. Thuật toán kiểm tra và chuyển hướng trong PowerShell (`.ps1` files):
```powershell
function Test-GitWorkTree {
    $gitExists = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitExists) {
        return $false
    }
    git rev-parse --is-inside-work-tree 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Get-GitRoot {
    $root = git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($root)) {
        return $null
    }
    return $root.Trim()
}

$IsGit = $false
$ProjectRoot = "."

if (Test-GitWorkTree) {
    $IsGit = $true
    $ProjectRoot = Get-GitRoot
} elseif (Test-Path ".git") {
    $IsGit = $true
    $ProjectRoot = "."
}

if (-not $IsGit) {
    $gitExists = Get-Command git -ErrorAction SilentlyContinue
    if (-not $gitExists) {
        Log-Error "git command line tool is missing, and no .git folder/file found."
    } else {
        Log-Error "The current directory is not a Git repository."
    }
    exit 1
}

Set-Location $ProjectRoot
```

## 5. Backward Compatibility & Migration Mapping

| Old Field | New File | New Field | Migration Rule | Recovery Rule |
| :--- | :--- | :--- | :--- | :--- |
| N/A | N/A | N/A | Không thay đổi dữ liệu cấu hình lưu trữ, do đó hoàn toàn tương thích ngược 100%. | N/A |

## 6. Disallowed Outputs Validation
- [x] Không sử dụng `file://` hoặc đường dẫn tuyệt đối.
- [x] Không sử dụng các placeholders `...` hay `etc.` trong code/sơ đồ.
- [x] Không sử dụng các giá trị `permission_mode` không an toàn.
- [x] Không sử dụng `TBD`.
- [x] Đã ánh xạ toàn bộ trường legacy (không có).

## 7. Implementation Checklist
- [ ] Cập nhật logic phát hiện Git trong `install.sh` và `public_export/install.sh`.
- [ ] Cập nhật logic phát hiện Git trong `install.ps1` và `public_export/install.ps1`.
- [ ] Cập nhật logic phát hiện Git trong `doctor.sh` và `public_export/doctor.sh`.
- [ ] Cập nhật logic phát hiện Git trong `doctor.ps1` and `public_export/doctor.ps1`.
- [ ] Cập nhật logic phát hiện Git trong `update.sh` và `public_export/update.sh`.
- [ ] Cập nhật logic phát hiện Git trong `update.ps1` và `public_export/update.ps1`.

## 8. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Cài đặt thành công khi `.git` là thư mục | Script phát hiện và cài đặt vào `.agents/` tại Project Root. | Chạy thử `./install.sh`. | N/A (Kiểm thử thủ công) |
| `REQ-002` | Cài đặt thành công khi `.git` là tệp (worktree/submodule) | Script phát hiện chính xác thông qua `git rev-parse`. | Khởi tạo Git worktree giả lập và chạy `./install.sh`. | N/A (Kiểm thử thủ công) |
| `REQ-003` | Cài đặt thành công khi chạy từ thư mục con | Script tự động `cd` về Project Root và tạo thư mục `.agents/` tại gốc dự án. | `cd src` và chạy `../install.sh`. | N/A (Kiểm thử thủ công) |
| `REQ-004` | Doctor CLI phát hiện chính xác Git root | doctor.sh chẩn đoán đúng các tệp của framework khi chạy từ thư mục con. | `cd src` và chạy `../doctor.sh`. | N/A (Kiểm thử thủ công) |
| `REQ-005` | Update CLI hoạt động từ thư mục con | update.sh tự động tìm thấy `.agents/` ở project root và cập nhật framework. | `cd src` và chạy `../update.sh`. | N/A (Kiểm thử thủ công) |
| `REQ-006` | Windows PowerShell tương đương Bash | Cả 3 script `.ps1` hoạt động tương thích hoàn toàn. | Chạy thử trên Windows PowerShell (nếu có). | N/A (Kiểm thử thủ công) |
| `REQ-007` | Lỗi rõ ràng khi thiếu lệnh `git` và không có `.git` file/folder | In thông báo "git command line tool is missing, and no .git folder/file found." và thoát với mã lỗi 1. | Tạm thời đổi tên lệnh git và chạy `./install.sh`. | N/A (Kiểm thử thủ công) |
| `REQ-008` | Cảnh báo rõ ràng khi chạy ngoài Git repository | In thông báo "The current directory is not a Git repository." và thoát với mã lỗi 1. | Di chuyển ra ngoài Git repo và chạy `./install.sh`. | N/A (Kiểm thử thủ công) |
