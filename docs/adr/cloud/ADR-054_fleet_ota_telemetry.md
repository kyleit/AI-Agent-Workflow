# ADR-054: Fleet OTA Updates and ClickHouse Telemetry

- **Status**: Proposed
- **Program**: Program A
- **Domain**: Operations
- **Related FEATs**: FEAT-202, FEAT-206
- **Context & Problem**: Cần một kênh thu thập logs phân tán lưu lượng lớn và phân phối cập nhật phần mềm Over-The-Air (OTA) an toàn.
- **Decision**: Sử dụng ClickHouse làm DB tập trung gom log/telemetry; phân phối file signed ZIP OTA cho các client Node.
- **Consequences**: Giảm tải máy chủ chính và logs được nén an toàn cấp CDN.
- **Backward Compatibility**: Telemetry adapter tương thích với Event Journal SQLite của v2.
