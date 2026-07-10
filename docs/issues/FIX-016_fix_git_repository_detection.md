<!-- File path: docs/issues/FIX-016_fix_git_repository_detection.md -->
---
artifact_type: fix-spec
issue_id: FIX-016
workflow: quick-fix
status: pending
---
# Fix Specification – Fix aiwf Git Detection for Worktrees/Submodules

## 1. Issue Description
Khi người dùng chạy `aiwf install`, `aiwf update`, hoặc `aiwf doctor` trong một Git worktree hoặc submodule (nơi `.git` là một tệp chứa tham chiếu `gitdir: ...` thay vì một thư mục), hoặc chạy từ một thư mục con lồng nhau, script cài đặt báo lỗi `[ERROR] The current directory is not a Git repository`. Lý do là các script này kiểm tra sự tồn tại của thư mục `.git` một cách cứng nhắc (`[ ! -d ".git" ]` hoặc `Test-Path ".git"` mà không nhảy về Project Root).

## 2. Scope

### In Scope:
Cập nhật các tệp script cài đặt, cập nhật và chẩn đoán để hỗ trợ Git worktree, submodule, và chạy từ thư mục con:
* `install.sh`
* `install.ps1`
* `update.sh`
* `update.ps1`
* `doctor.sh`
* `doctor.ps1`
* Các tệp tương ứng trong `public_export/`

### Out of Scope:
* Không thay đổi logic hoạt động cốt lõi của các skill khác.
* Không thay đổi hành vi Git commit/push của các agent khác.

## 3. Implementation Plan & Git Root Detection Strategy
Sử dụng `git rev-parse --is-inside-work-tree` để kiểm tra xem có đang ở trong một Git repository hợp lệ hay không.
Sử dụng `git rev-parse --show-toplevel` để tìm project root và thực hiện `cd` / `Set-Location` về project root trước khi chạy phần logic cài đặt hoặc cập nhật.
Fallback sang kiểm tra sự tồn tại của `.git` (dưới dạng file hoặc thư mục) tại thư mục hiện tại nếu lệnh `git` không hoạt động.
