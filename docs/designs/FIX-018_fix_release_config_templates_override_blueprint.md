<!-- File path: docs/designs/FIX-018_fix_release_config_templates_override_blueprint.md -->
---
artifact_type: blueprint
issue_id: FIX-018
workflow: quick-fix
status: approved
---
# Technical Design Blueprint – Fix Release Config Templates Hardcoding

## 1. Proposed Code Changes
Thay thế cấu hình hardcode trong hai tệp cấu hình mẫu thành mẫu chuẩn hóa tổng quát và cập nhật phân phối.

### `templates/release.config.json`
- **Operation**: MODIFY
- **Responsibility**: Khai báo cấu hình dự án đơn lẻ mặc định (`single` project_type) thay thế cho cấu hình `multi-module` của aiwf.
- **Changes**: Thay đổi toàn bộ nội dung tệp JSON sang cấu hình tổng quát.

### `.agents/templates/release.config.json`
- **Operation**: MODIFY
- **Responsibility**: Khai báo cấu hình mẫu an toàn, không chứa thông tin hardcode của dự án hiện tại.
- **Changes**: Thay đổi toàn bộ nội dung tệp JSON sang cấu hình tổng quát.

### `templates/workflow.config.json.template` [NEW]
- **Operation**: NEW
- **Responsibility**: Cung cấp tệp cấu hình quy trình mẫu tổng quát không chứa thông tin hardcode của dự án hiện tại.
- **Changes**: Tạo mới tệp với các câu lệnh echo tượng trưng.

### `.agents/templates/workflow.config.json.template`
- **Operation**: MODIFY
- **Responsibility**: Cập nhật tệp cấu hình quy trình mẫu thành nội dung tổng quát chuẩn hóa.
- **Changes**: Thay đổi toàn bộ sang cấu hình mẫu tổng quát.

### `MANIFEST.json` & `.agents/MANIFEST.json`
- **Operation**: MODIFY
- **Responsibility**: Khai báo tệp templates/workflow.config.json.template vào danh sách templates của Framework.
- **Changes**: Thêm phần tử vào danh sách `"templates"`.

## 2. Target Folder Structure
```text
.
├── .agents
│   ├── MANIFEST.json
│   └── templates
│       ├── release.config.json
│       └── workflow.config.json.template
├── MANIFEST.json
└── templates
    ├── release.config.json
    └── workflow.config.json.template
```

## 3. Interface & Data Contracts
- **`release.config.json` Schema**:
```json
{
  "project_type": "single",
  "modules": [
    {
      "name": "core",
      "path": ".",
      "version_file": "package.json",
      "changelog_file": "CHANGELOG.md"
    }
  ],
  "default_branch": "main",
  "remote_name": "origin"
}
```

- **`workflow.config.json.template` Schema**:
```json
{
  "project_name": "example-project",
  "git_flow": {
    "development_branch": "main",
    "release_branch": "main",
    "feature_prefix": "feature/FEAT-",
    "sync_method": "merge",
    "extra_push_branches": []
  },
  "release_pipeline": {
    "steps": [
      "bump_version",
      "update_changelog",
      "git_commit",
      "git_tag",
      "custom_commands",
      "git_push"
    ],
    "custom_commands": {
      "core": [
        "echo 'Chạy lệnh build/test cho module core ở đây!'"
      ],
      "global": [
        "echo 'Chạy lệnh release global ở đây!'"
      ]
    }
  }
}
```

## 4. Algorithms & Key Logic
Không thay đổi thuật toán. Khi người dùng chạy cài đặt/cập nhật, tệp cấu hình mẫu tổng quát này sẽ được copy sang dự án của họ.

## 5. Validation Rules
Mã JSON hợp lệ và tuân thủ định dạng của `release_manager.py`.

## 6. Implementation Checklist
- [x] Chỉnh sửa `templates/release.config.json` thành cấu hình tổng quát.
- [x] Chỉnh sửa `.agents/templates/release.config.json` thành cấu hình tổng quát.
- [x] Tạo mới/Chỉnh sửa `templates/workflow.config.json.template` và `.agents/templates/workflow.config.json.template` thành cấu hình tổng quát.
- [x] Đăng ký trong `MANIFEST.json` và `.agents/MANIFEST.json`.

## 7. Verification & Test Plan
- **Acceptance Assertions**:
  - *REQ-001*: Kiểm tra cú pháp JSON hợp lệ của các tệp config mới chỉnh sửa.
  - *REQ-002*: Chạy unit tests hệ thống để đảm bảo không lỗi.

