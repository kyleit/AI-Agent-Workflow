# AI Workflow Runtime Engine

Technical guide for the AI Workflow CLI Runtime Engine.

## 1. Architecture
Hệ thống điều khiển Runtime được phân tách thành các mô-đun Python chuyên biệt độc lập:
*   `workflow_runtime.py`: Entry point điều hướng tham số và gọi các xử lý tương ứng.
*   `session.py`: Giao tiếp tệp `.session.json` nguyên tử bằng cơ chế rename.
*   `context.py`: Ước lượng số lượng tokens đã sử dụng qua kích thước tệp nhật ký.
*   `checkpoint.py`: Ánh xạ và kiểm định mốc quy trình.
*   `validator.py`: Đo đạc sức khỏe workspace, git branch và phiên bản.
*   `drift.py`: Phát hiện sai lệch ngữ cảnh.
*   `heartbeat.py`: In ra màn hình bảng nhịp tim trạng thái.

## 2. CLI Reference
Mọi kỹ năng và MCP Tool có thể giao tiếp với Runtime thông qua CLI:

### Khởi tạo session
```bash
python scripts/workflow_runtime.py init
```

### Bắt đầu Kỹ năng
```bash
python scripts/workflow_runtime.py start \
  --skill blueprint-to-implementation \
  --command implement \
  --checkpoint 5 \
  --step "Starting implementation"
```

### Cập nhật bước nhỏ
```bash
python scripts/workflow_runtime.py step \
  --step "Running unit tests" \
  --log "Executing test suites..."
```

### Hoàn thành Kỹ năng
```bash
python scripts/workflow_runtime.py complete \
  --checkpoint 5 \
  --next-skill implementation-to-debug \
  --next-command debug
```

### Đánh dấu thất bại
```bash
python scripts/workflow_runtime.py fail \
  --step "Tests Failed" \
  --log "Assertion error in test suite"
```

### Hiển thị nhịp tim
```bash
python scripts/workflow_runtime.py heartbeat
```

## 3. Session Schema Compatibility
Tệp `.agents/.session.json` luôn được giữ nguyên định dạng để đảm bảo tương thích 100% với VS Code Extension:
```json
{
  "workspace": { "path": ".", "valid": true },
  "git": { "is_git_repository": true, "branch": "main", "working_tree": "dirty", "latest_tag": "v2.10.0" },
  "work_item": { "type": "FEAT", "id": "FEAT-010", "title": "Refactor Runtime" },
  "version": { "version": "2.10.1", "source": "MANIFEST.json" },
  "memory": { "status": "FRESH", "last_updated": "..." },
  "rag": { "connected": true, "provider": "qdrant" },
  "checkpoint": 5,
  "status": "in_progress",
  "current_skill": "blueprint-to-implementation",
  "current_command": "implement",
  "current_step": "...",
  "current_logs": [],
  "updated_at": "...",
  "context_health": "healthy"
}
```

## 4. Recovery & Resume
Nếu tệp cấu hình phiên chạy bị lỗi cú pháp JSON hoặc bị xóa ngoài ý muốn, hệ thống sẽ tự động khôi phục từ trạng thái mặc định an toàn khi chạy lệnh `init`.
Để tiếp tục quy trình đã dừng:
```bash
python scripts/workflow_runtime.py validate --checkpoint "exactly 5"
```
Lệnh này sẽ xác thực tính hợp lệ của mốc trước khi tiến hành thực hiện bước tiếp theo.
