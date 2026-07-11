<!-- docs/brainstorming/FEAT-112_plugin_ecosystem.md -->

---
feature_id: FEAT-112
feature_name: Plugin & Skill Marketplace
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-112_plugin_ecosystem_plan.md
---

# Master Requirement Document – Plugin & Skill Marketplace

## Executive Summary
Hệ sinh thái phân phối và nạp động (hot-reload) các kỹ năng (Skills), MCP Runtime Engine và chứng thực chữ ký số gói tải về.

## Background
Quy trình thêm kỹ năng mới trong v1 yêu cầu chép tay thư mục vào `.agents/skills` và thiếu cơ chế sandbox bảo vệ.

## Current AIWF v1 Analysis
Quét thư mục phẳng `.agents/skills/` để nạp kỹ năng.

## Gap Analysis
Thiếu chữ ký xác thực an toàn và cơ chế cập nhật tự động (OTA updates).

## Objectives
Xây dựng client nạp động kỹ năng qua mạng và xác thực chứng chỉ số bảo mật.

## Scope
- Plugin marketplace client.
- Model Context Protocol (MCP) native connector.

## Out of Scope
- Cổng thanh toán mua bán trực tiếp plugin.

## Functional Requirements
- **FR-01**: Tải và xác minh chữ ký gói Skill.
- **FR-02**: Nạp động Skill mới mà không cần khởi động lại CLI.

## Non-Functional Requirements
- **NFR-01**: Thời gian xác thực chữ ký gói nhỏ hơn 5ms.

## Architecture Proposal
Sử dụng gói đóng dạng zip đã ký số bằng khóa công khai. MCP runtime chạy qua lớp giao tiếp Stdpipe độc lập.

## Runtime Components
- `MarketplaceClient`
- `MCPConnector`

## Data Model
`Manifest` định nghĩa quyền hạn (permissions) mà plugin được phép sử dụng.

## Runtime State
`DOWNLOADING` -> `VERIFYING` -> `LOADING`.

## Integration Points
Tích hợp với `PolicyEnforcementEngine` để giới hạn quyền hạn truy cập hệ thống của plugin.

## Public APIs
- `install_plugin_package(plugin_url: str) -> bool`

## Internal APIs
- `_verify_signature(package_path: str) -> bool`

## Event Model
- `plugin_loaded`: Phát đi khi nạp plugin thành công.

## State Machine
- `UNINSTALLED` -> `VERIFIED` -> `ACTIVE`

## Sequence Flow
1. Yêu cầu tải -> Kiểm tra chữ ký số.
2. Giải nén -> Cấu hình phân quyền -> Nạp nóng vào bộ nhớ.

## Security
Chặn cài đặt nếu chữ ký số không hợp lệ hoặc cố tình yêu cầu quyền hạn ngoài cấu hình.

## Performance
Thời gian nạp nóng kỹ năng mới dưới 100ms.

## Scalability
Hỗ trợ nạp tối đa 500 kỹ năng hoạt động cùng lúc.

## Fault Tolerance
Tự động cô lập và vô hiệu hóa plugin nếu nó gây ra crash luồng hệ thống liên tục.

## Disaster Recovery
Lưu danh sách plugin an toàn ở local; tự phục hồi từ local zip nếu cài đặt lỗi.

## Multi-Tenant Considerations
Mỗi session được giới hạn danh sách plugin được phép kích hoạt riêng.

## Observability
Theo dõi lượng tài nguyên (CPU/RAM) tiêu thụ của từng plugin riêng biệt.

## Risks
- Mã độc ẩn náu trong plugin. Giải pháp: Chạy plugin trong Docker sandbox.

## Trade-offs
- Mở rộng hệ sinh thái đi kèm với việc phải quản lý rủi ro bảo mật gói tin chặt chẽ.

## Migration Strategy
Kỹ năng cũ v1 không có chữ ký số sẽ được xếp vào lớp legacy và chạy dưới quyền hạn tối thiểu.

## Backward Compatibility
Hoạt động bình thường với tất cả kỹ năng cũ v1.

## Acceptance Criteria
- [ ] Cài đặt kỹ năng có chữ ký hợp lệ thành công.
- [ ] Chặn cài đặt gói tin bị sửa đổi nội dung.

## Estimated ADR Count
5 ADRs.

## Estimated Blueprint Count
2 Blueprints.

## Estimated Implementation Phases
2 Phases.
