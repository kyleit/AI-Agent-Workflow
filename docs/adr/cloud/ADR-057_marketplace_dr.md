# ADR-057: Cloud Marketplace and Multi-Region DR

- **Status**: Proposed
- **Program**: Program E
- **Domain**: Ecosystem & DR
- **Related FEATs**: FEAT-208, FEAT-209, FEAT-210
- **Context & Problem**: Phân phối gói kỹ năng, marketplace client và khôi phục thảm họa dữ liệu chéo vùng địa lý.
- **Decision**: Lưu trữ plugin Marketplace và artifact trên AWS S3 Cross-Region; database nhân bản chéo vùng qua PostgreSQL.
- **Consequences**: Độ sẵn sàng 99.99% uptime.
- **Backward Compatibility**: Kỹ năng cũ không có chữ ký số chạy dưới legacy jail sandbox.
