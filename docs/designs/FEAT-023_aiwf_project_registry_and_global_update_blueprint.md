<!-- File path: docs/designs/FEAT-023_aiwf_project_registry_and_global_update_blueprint.md -->

---
feature_id: FEAT-023
feature_name: Project Registry & Global Update CLI
status: reviewed
stage: blueprint
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../plans/FEAT-023_aiwf_project_registry_and_global_update_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Project Registry & Global Update CLI

## 0. Baseline Context & References
- **Memory Baseline**: CLI `aiwf` là shell wrapper gọi trực tiếp Python script chính `skills/workflow-runtime/scripts/workflow_runtime.py` chịu trách nhiệm điều phối toàn bộ workflow.
- **RAG Query Summaries**: Cấu hình registry toàn cục sẽ được lưu trữ cục bộ dưới dạng tệp JSON tại thư mục AppData/config chuẩn theo hệ điều hành mà không phát sinh dữ liệu mạng.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/workflow_runtime.py`
  - `install.sh`
  - `update.sh`
  - `doctor.sh`
  - `install.ps1`
  - `update.ps1`
  - `doctor.ps1`

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/aiwf_registry.py` | `[NEW]` | Module helper xử lý đọc/ghi registry JSON nguyên tử, chuẩn hóa path, và thực hiện các nghiệp vụ quản lý dự án. | Không phụ thuộc thư viện ngoài, chỉ dùng thư viện chuẩn Python (`os`, `sys`, `json`, `platform`, `hashlib`, `datetime`, `shutil`). | Thấp. Code mới được kiểm thử độc lập. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | `[MODIFY]` | Đăng ký command parser `registry` mới; cập nhật command parser `update` nhận diện thêm các tham số `--all` / `--current`; tích hợp dispatch các tác vụ registry. | `skills/workflow-runtime/scripts/aiwf_registry.py` | Trung bình. Cần bảo toàn các lệnh hiện có không bị ảnh hưởng. |
| `install.sh` | `[MODIFY]` | Sau khi cài đặt hoàn tất, tự động gọi đăng ký dự án thông qua Python CLI. | `skills/workflow-runtime/scripts/workflow_runtime.py` | Thấp. Chỉ bổ sung lệnh gọi bổ trợ. |
| `update.sh` | `[MODIFY]` | Hỗ trợ parse tham số `--all` / `--current` và truyền tương ứng xuống Python runtime. | `skills/workflow-runtime/scripts/workflow_runtime.py` | Thấp. Chỉ bổ sung phân phối tham số. |
| `doctor.sh` | `[MODIFY]` | Tích hợp gọi kiểm tra đăng ký registry của dự án hiện tại. | `skills/workflow-runtime/scripts/workflow_runtime.py` | Thấp. |
| `install.ps1` | `[MODIFY]` | Tự động gọi đăng ký dự án qua Python CLI sau khi hoàn thành. | `skills/workflow-runtime/scripts/workflow_runtime.py` | Thấp. |
| `update.ps1` | `[MODIFY]` | Hỗ trợ parse tham số và chuyển xuống Python CLI. | `skills/workflow-runtime/scripts/workflow_runtime.py` | Thấp. |
| `doctor.ps1` | `[MODIFY]` | Gọi kiểm tra đăng ký registry của dự án hiện tại. | `skills/workflow-runtime/scripts/workflow_runtime.py` | Thấp. |
| `MANIFEST.json` | `[MODIFY]` | Đăng ký bổ sung module `aiwf_registry` vào danh sách catalog. | `None` | Thấp. |
| `SKILLS.md` | `[MODIFY]` | Bổ sung hướng dẫn sử dụng CLI registry mới vào catalog tài liệu. | `None` | Thấp. |

## 2. Target Folder Structure
```text
.
├── MANIFEST.json
├── SKILLS.md
├── install.sh
├── update.sh
├── doctor.sh
├── install.ps1
├── update.ps1
├── doctor.ps1
└── skills/
    ├── orchestrator/
    │   └── SKILL.md
    └── workflow-runtime/
        └── scripts/
            ├── aiwf_registry.py
            └── workflow_runtime.py
```

## 3. Interface Contracts (Public & Internal)

### CLI Command Syntax
```bash
# Đăng ký dự án hiện tại hoặc đường dẫn chỉ định
aiwf register [--path <project_path>] [--force]

# Liệt kê danh sách dự án
aiwf list

# Hủy đăng ký dự án hiện tại hoặc đường dẫn chỉ định
aiwf unregister [--path <project_path>]

# Chẩn đoán trạng thái registry
aiwf registry doctor

# Dọn dẹp các đường dẫn rác không còn tồn tại
aiwf registry cleanup

# Cập nhật toàn bộ dự án
aiwf update --all
```

### JSON Schema của `projects.json`
Tệp registry được lưu trữ tại đường dẫn AppData của hệ điều hành:
- Windows: `%APPDATA%\aiwf\projects.json` (Fallback: `~/.aiwf/projects.json`)
- macOS: `~/Library/Application Support/aiwf/projects.json` (Fallback: `~/.aiwf/projects.json`)
- Linux: `~/.config/aiwf/projects.json` (Fallback: `~/.aiwf/projects.json`)

```json
{
  "schema_version": 1,
  "updated_at": "YYYY-MM-DDTHH:MM:SSZ",
  "projects": [
    {
      "id": "md5_hash_of_normalized_path",
      "path": "/absolute/normalized/path",
      "name": "folder_name",
      "registered_at": "YYYY-MM-DDTHH:MM:SSZ",
      "last_seen_at": "YYYY-MM-DDTHH:MM:SSZ",
      "last_installed_at": "YYYY-MM-DDTHH:MM:SSZ",
      "last_updated_at": "YYYY-MM-DDTHH:MM:SSZ",
      "aiwf_version": "6.2.0",
      "install_source": "install",
      "status": "active"
    }
  ]
}
```

### Enum Constraints
- `install_source`: `install`, `register`, `migration`
- `status`: `active`, `missing`, `inactive`
- `permission_mode` (được cấu hình trong dự án): Chỉ cho phép `sandbox`, `full_access` (Duyệt tuyệt đối không có `unrestricted`).

## 4. Algorithms & Logic Specifications

### Chuẩn hóa đường dẫn & Tạo ID dự án
- Hàm python `normalize_path(p: str) -> str`:
  1. Chuyển đổi thành đường dẫn tuyệt đối: `os.path.realpath(os.path.abspath(p))`.
  2. Trên Windows, chuyển toàn bộ ký tự thành chữ thường (lowercase) để so sánh case-insensitive.
- ID dự án được tạo bằng hàm băm MD5 của đường dẫn chuẩn hóa để tránh trùng lặp:
  `hashlib.md5(normalized_path.encode('utf-8')).hexdigest()`.

### Ghi tệp nguyên tử (Atomic Write)
Để tránh mất mát/hỏng dữ liệu khi tiến trình bị tắt đột ngột:
1. Ghi nội dung JSON mới ra tệp tạm cùng thư mục: `projects.json.tmp`.
2. Sử dụng `os.replace('projects.json.tmp', 'projects.json')` để đổi tên tệp đè lên tệp gốc. Hệ điều hành sẽ xử lý việc thay thế này dưới dạng một thao tác nguyên tử duy nhất.

### Khôi phục lỗi cấu hình JSON hỏng
Khi đọc file `projects.json`:
1. Nếu phát hiện lỗi cú pháp `json.JSONDecodeError`:
   - Sao lưu tệp hỏng thành `projects.json.bak.<timestamp>`.
   - Khởi tạo một tệp registry rỗng mới với `projects = []`.
   - Log cảnh báo ra console, tuyệt đối không được crash tiến trình.

### Logic Cập nhật Toàn cục (`update --all`)
1. Đọc tệp registry `projects.json`.
2. Lọc ra danh sách các dự án có trạng thái `active`.
3. Duyệt qua từng dự án:
   - Kiểm tra đường dẫn dự án có thực sự tồn tại trên đĩa.
   - Kiểm tra thư mục `.agents/` và tệp `MANIFEST.json` có tồn tại.
   - Chạy script cập nhật hiện có cho dự án đó (`update.sh`).
   - Gói logic cập nhật trong khối `try/except` để nếu một dự án bị lỗi (ví dụ: mất quyền write), tiến trình vẫn tiếp tục cập nhật các dự án còn lại.
4. Tổng hợp kết quả và in bảng báo cáo chi tiết: số lượng thành công, thất bại, bỏ qua, đường dẫn lỗi và lý do.

## 5. State Machine & Transitions
Không có máy trạng thái phức tạp. Trạng thái dự án chuyển đổi qua các sự kiện CLI:
- Dự án mới cài đặt: `active`.
- Chạy doctor phát hiện mất đường dẫn: chuyển sang `missing`.
- Chạy cleanup: xóa khỏi danh sách hoặc giữ lại trạng thái `missing` nếu muốn giữ history.

## 6. Validation and Safety Constraints
- **Đường dẫn cấm**: File registry chỉ được lưu trữ ngoài thư mục dự án (ở thư mục AppData toàn cục). Không ghi absolute path vào bất kỳ tệp tĩnh nào trong repository.
- **Bảo toàn dữ liệu người dùng**: Tiến trình cập nhật toàn cục chỉ thay thế các file quản lý của framework, giữ nguyên thư mục `.agents/memory/` và các cấu hình customization.

## 7. Backward Compatibility & Migration Mapping
Các phiên bản cài đặt AIWF trước đây chưa hỗ trợ Registry sẽ được đăng ký thủ công vào tệp JSON mới thông qua lệnh `aiwf register` mà không làm thay đổi các file trạng thái cũ.

## 8. Implementation Checklist
- [ ] Thiết lập module helper `skills/workflow-runtime/scripts/aiwf_registry.py`.
- [ ] Đăng ký sub-command `registry` và các tham số `--all` / `--current` của `update` vào `skills/workflow-runtime/scripts/workflow_runtime.py`.
- [ ] Cập nhật tệp shell `install.sh` / `install.ps1` tự động gọi lệnh register.
- [ ] Cập nhật tệp shell `update.sh` / `update.ps1` hỗ trợ nhận diện và chuyển tiếp tham số.
- [ ] Cập nhật tệp shell `doctor.sh` / `doctor.ps1` chẩn đoán registry.
- [ ] Viết unit tests kiểm tra toàn diện logic registry (`skills/workflow-runtime/tests/test_state_engine.py` hoặc file test mới `test_registry.py`).
- [ ] Tạo môi trường mockup tạm thời để chạy thử và kiểm thử tích hợp (integration tests).
- [ ] Cập nhật tài liệu hướng dẫn và changelog.

## 9. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Đăng ký tự động khi install | Chạy `install.sh` dự án được tự động đưa vào registry JSON. | Chạy `./install.sh --force --permission sandbox` và kiểm tra tệp `projects.json`. | `test_registry.py::test_auto_register` |
| `REQ-002` | Lệnh register thủ công | Chạy `aiwf register` trên dự án đã có `.agents/` sẽ đăng ký thành công. | Chạy `python3 skills/workflow-runtime/scripts/workflow_runtime.py registry register` | `test_registry.py::test_manual_register` |
| `REQ-003` | Không trùng lặp dự án | Đăng ký cùng một dự án nhiều lần không tạo bản ghi trùng lặp. | Chạy đăng ký dự án 2 lần và kiểm tra số lượng dự án trong registry. | `test_registry.py::test_idempotent_register` |
| `REQ-004` | So sánh đường dẫn case-insensitive | Trên Windows, đường dẫn chữ hoa/chữ thường khác nhau đều map về cùng một ID. | Mock môi trường Windows, so sánh hai đường dẫn khác case. | `test_registry.py::test_windows_case_insensitive` |
| `REQ-005` | Liệt kê danh sách dự án | Lệnh `aiwf list` hiển thị danh sách dạng bảng đầy đủ. | Chạy `python3 skills/workflow-runtime/scripts/workflow_runtime.py registry list` | `test_registry.py::test_list_projects` |
| `REQ-006` | Hủy đăng ký dự án | Lệnh `aiwf unregister` xóa dự án khỏi registry. | Chạy unregister và xác nhận dự án biến mất khỏi tệp JSON. | `test_registry.py::test_unregister_project` |
| `REQ-007` | Chẩn đoán registry | `aiwf registry doctor` báo lỗi nếu có đường dẫn không tồn tại. | Sửa tay tệp JSON trỏ đến đường dẫn sai và chạy doctor. | `test_registry.py::test_registry_doctor` |
| `REQ-008` | Dọn dẹp registry | `aiwf registry cleanup` xóa các đường dẫn hỏng. | Chạy cleanup và kiểm tra các đường dẫn sai đã bị xóa bỏ. | `test_registry.py::test_registry_cleanup` |
| `REQ-009` | Cập nhật toàn cục | `aiwf update --all` cập nhật tuần tự toàn bộ dự án hoạt động. | Tạo 2 dự án giả lập, chạy update --all và kiểm tra phiên bản mới. | `test_registry.py::test_update_all_projects` |
| `REQ-010` | Bỏ qua lỗi khi update batch | Nếu 1 dự án lỗi, các dự án còn lại vẫn được cập nhật tiếp. | Thiết lập 1 dự án lỗi và 1 dự án đúng, chạy update --all. | `test_registry.py::test_update_all_ignores_errors` |
| `REQ-011` | Khôi phục JSON hỏng | Tự động backup và tạo lại tệp registry mới nếu JSON bị hỏng cú pháp. | Ghi chuỗi vô nghĩa vào tệp registry, chạy lệnh registry bất kỳ. | `test_registry.py::test_registry_recovery_from_corrupted_json` |
| `REQ-012` | Ghi tệp nguyên tử | Tệp ghi đè bằng thao tác rename nguyên tử. | Kiểm thử ghi tệp và kiểm tra sự tồn tại của tệp tạm. | `test_registry.py::test_atomic_write` |

## 10. Disallowed Outputs Validation
- [x] Không sử dụng link `file://` hay đường dẫn tuyệt đối trong blueprint.
- [x] Không sử dụng ký tự đại diện `...` hay `etc.` trong code hoặc cấu trúc thư mục.
- [x] Không sử dụng các giá trị `TBD`.
- [x] Không cấu hình giá trị `unrestricted` cho chế độ phân quyền.
- [x] Không ghi absolute path cục bộ vào mã nguồn tĩnh của repo.
