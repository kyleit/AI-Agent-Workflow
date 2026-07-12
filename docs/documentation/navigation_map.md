# Documentation Navigation Map

Bản đồ cấu trúc điều hướng cho trang tài liệu tương tác v2.

```mermaid
graph TD
  Home[Trang chủ] --> GettingStarted[Getting Started]
  Home --> RuntimeArchitecture[Runtime Architecture]
  RuntimeArchitecture --> ResidentOrchestrator[Resident Orchestrator]
  RuntimeArchitecture --> ResidentManager[Resident Runtime Manager]
  Home --> APIReference[API Reference]
  Home --> SDKReference[SDK Reference]
```
Hệ thống điều hướng tích hợp Breadcrumbs ở phía trên đầu trang và các liên kết Previous/Next ở chân trang để tạo luồng đọc mượt mà.
