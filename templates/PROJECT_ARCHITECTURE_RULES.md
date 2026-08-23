# 🏛️ PROJECT ARCHITECTURE & ENGINEERING RULES
## Bounded Contexts (DDD) + Clean Architecture 4 Lớp + Dependency Injection (DI Container)

> **Cấp độ tài liệu**: Quy chuẩn Kiến trúc Bắt buộc (Mandatory Architecture Standard)
> **Áp dụng cho**: Mọi dự án mới và các module mở rộng trong hệ thống.

---

## 🧭 1. NGUYÊN TẮC CỐT LÕI (CORE PRINCIPLES)

1. **Mô hình Modular Monolith (Vertical Slice theo Bounded Context)**:
   - Không gom chung code theo layer ngang toàn cục (tránh tạo các thư mục rác như `/controllers`, `/services`, `/models` chung cho cả dự án).
   - Mỗi nghiệp vụ lớn PHẢI là một **Bounded Context (Module độc lập)** nằm trong thư mục riêng (Ví dụ: `task-router/`, `workload-balancer/`, `agent_communication/`, `resource_governor/`, v.v.).

2. **Cấu trúc Clean Architecture 4 Lớp bên trong MỖI Bounded Context**:
   - 🟢 `domain/`: Chứa Entities, Value Objects, Domain Events, Interface/Ports (Abstract Repositories/Engines). Tuyệt đối **KHÔNG phụ thuộc** vào framework, database, hay thư viện bên ngoài.
   - 🔵 `application/`: Chứa Use Cases (mỗi use case là 1 file độc lập), DTOs/Schemas. Chỉ phụ thuộc vào `domain/`.
   - 🟠 `infrastructure/`: Chứa triển khai cụ thể của Interface (Repositories, Adapters, Storage, API Clients, Event Bus). Phụ thuộc vào `domain/`.
   - 🟣 `interface/` (hoặc `presentation/`): Chứa API Endpoints (FastAPI/Fiber/ASP.NET), CLI commands, WebSocket handlers. Gọi Use Cases thông qua Dependency Injection.

3. **Nguyên tắc Đảo ngược phụ thuộc & DI Container (Dependency Injection)**:
   - Toàn bộ Use Cases và Handlers **KHÔNG ĐƯỢC PHÉP tự khởi tạo trực tiếp (hardcode `new` / import trực tiếp instance)** các lớp Infrastructure.
   - Dự án PHẢI có một **DI Container trung tâm (`container.py` / `Container.cs` / `wire.go`)** đóng vai trò là Composition Root để khởi tạo Repositories, inject vào Use Cases và cung cấp ra ngoài cho Presentation/Daemon.

---

## 📁 2. CẤU TRÚC THƯ MỤC CHUẨN MẪU (STANDARDIZED DIRECTORY STRUCTURE)

```text
ProjectRoot/
├── CoreModule/                     # Module Lõi & Khởi động
│   ├── kernel/                     # Kernel, Config, Base Entities
│   ├── container.py                # DI Container (Composition Root trung tâm)
│   └── daemon.py / main.py         # App Lifecycle & Server Dispatch Loop
├── <BoundedContext_A>/             # Module nghiệp vụ A (Ví dụ: task-router)
│   ├── domain/
│   │   ├── entities/               # Thực thể nghiệp vụ
│   │   ├── value_objects/          # Đối tượng giá trị bất biến
│   │   ├── events/                 # Domain Events
│   │   └── interfaces/             # Abstract Repositories / Ports
│   ├── application/
│   │   └── use_cases/              # Từng Use Case chuyên biệt (1 file = 1 usecase)
│   ├── infrastructure/
│   │   └── repositories/           # Triển khai lưu trữ (JSON, SQL, Redis, v.v.)
│   └── interface/                  # (Tùy chọn nếu có CLI / Adapter riêng)
├── <BoundedContext_B>/             # Module nghiệp vụ B (Ví dụ: communication)
│   ├── domain/ ...
│   ├── application/ ...
│   ├── infrastructure/ ...
│   └── interface/ ...
├── presentation_web/               # (Tùy chọn) Giao diện hoặc REST API Gateway gom router
│   ├── backend/api/                # Các FastAPI Routers kết nối Use Cases qua DI
│   └── frontend/                   # UI (Svelte / React / Vue)
└── tests/                          # Unit Tests độc lập theo từng Use Case & Entity
```
