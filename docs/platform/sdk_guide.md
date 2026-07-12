# AIWF Runtime SDK Guide

Hướng dẫn phát triển ứng dụng tích hợp SDK.

## 1. Khởi tạo kết nối Client
```python
from hierarchical_runtime import HierarchicalRuntime

client = HierarchicalRuntime("MY-APP")
client.receive_command("set concurrency 4")
```

## 2. Lắng nghe sự kiện qua Named Pipes
Các Skills sử dụng cơ chế lắng nghe thụ động để cập nhật trạng thái tiến trình thực tế.
