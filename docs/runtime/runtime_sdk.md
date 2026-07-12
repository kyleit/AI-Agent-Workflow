# AIWF Runtime SDK

Hướng dẫn tích hợp SDK để tương tác với Resident Orchestrator từ mã nguồn của các Skills.

## 1. Tích hợp Python Client
Mọi Skill trong Python nên kế thừa hoặc sử dụng `RuntimeClient` để tương tác chéo tiến trình:
```python
from hierarchical_runtime import HierarchicalRuntime

class RuntimeSDK:
    def __init__(self):
        self.runtime = HierarchicalRuntime("SDK-CLIENT")

    def submit_command(self, cmd: str):
        self.runtime.receive_command(cmd)
```
Hàm trên sẽ tự động ghi lệnh vào hộp thư Queue và gửi thông báo tín hiệu tới Watchdog.
