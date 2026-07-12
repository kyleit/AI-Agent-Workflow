# Technical Design Blueprint – Full Access Autonomous Delivery Contract

## 1. Overview
Hợp đồng thiết kế quy định quyền hạn và hành vi của Resident Orchestrator khi hoạt động dưới chế độ phân quyền `full_access`. 
Mục tiêu là tối đa hóa tính tự chủ trong phạm vi công việc được giao (Work Item), bỏ qua tất cả các xác nhận trung gian không cần thiết, nhưng đồng thời thiết lập ranh giới bảo mật cứng chống lại các thao tác phát hành/hủy hoại ngoài ý muốn.

## 2. Authorization Schema Definition
Mỗi Work Item chạy trong chế độ `full_access` sẽ đi kèm một bản ghi phân quyền duy nhất có cấu trúc:

```json
{
  "authorization_id": "AUTH-FEAT-115",
  "project_id": "project-id",
  "workspace_id": "workspace-id",
  "work_item_id": "FEAT-115",
  "workflow_id": "WF-FEAT-115",
  "permission_mode": "full_access",
  "authorization_status": "active",
  "source": "explicit_user_request",
  "allowed_phases": [
    "discovery",
    "brainstorming",
    "planning",
    "blueprint",
    "architecture_validation",
    "implementation",
    "debug",
    "test",
    "browser_validation",
    "verification",
    "final_review"
  ],
  "allow_document_create": true,
  "allow_document_modify": true,
  "allow_source_create": true,
  "allow_source_modify": true,
  "allow_test_create": true,
  "allow_test_modify": true,
  "allow_runtime_state_modify": true,
  "allow_agent_spawn": true,
  "allow_agent_reassignment": true,
  "allow_parallel_execution": true,
  "allow_retry": true,
  "allow_replan": true,
  "allow_commit": false,
  "allow_merge": false,
  "allow_rebase": false,
  "allow_tag": false,
  "allow_push": false,
  "allow_release": false,
  "allow_publish": false,
  "allow_deploy": false,
  "stop_at": "release_approval",
  "expires_when": "release_approved_or_work_item_cancelled",
  "created_at": "ISO-8601",
  "terminated_at": null
}
```

## 3. Gate Resolution Model
Các cổng trung gian sẽ được phân giải động dựa trên chính sách phân quyền hiện tại thay vì hỏi trực tiếp stdin:
- **AUTHORIZED_BY_FULL_ACCESS**: Hành động được phê chuẩn tự động vì nằm trong phạm vi cho phép của phân quyền active.
- **USER_APPROVAL_REQUIRED**: Cần xác nhận trực tiếp từ người dùng.
- **OUT_OF_SCOPE**: Hành động nhắm vào một tài nguyên hoặc dự án ngoài phạm vi cho phép.
- **BLOCKED_BY_RELEASE_BOUNDARY**: Thao tác bị chặn cứng do nằm trong danh sách các thao tác phát hành nhạy cảm (git commit, git push, release).

## 4. Compatibility Matrix
| Permission Mode | Allow Doc Edit | Allow Source Edit | Auto Phase Transition | Bypass intermediate Y/N | Stop at Release Gate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `read_only` | No | No | No | No | Yes |
| `sandbox` | Yes (Limited) | No | No | No | Yes |
| `full_access` | Yes | Yes | Yes | Yes | Yes |
