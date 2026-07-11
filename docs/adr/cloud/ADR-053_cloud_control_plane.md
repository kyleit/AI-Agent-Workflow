# ADR-053: Cloud Control Plane Architecture

- **Status**: Proposed
- **Program**: Program D
- **Domain**: Cloud Control Plane
- **Related FEATs**: FEAT-201
- **Context & Problem**: Cần một trung tâm điều phối trạng thái tập trung cho hàng nghìn worker nodes.
- **Decision**: Triển khai Control Plane dạng cụm microservices chạy trên Kubernetes (EKS), giao tiếp qua API REST và WebSockets.
- **Consequences**: Khả năng chịu tải và mở rộng tốt chéo vùng mạng.
- **Backward Compatibility**: Tương thích hoàn toàn với các định dạng REST cũ của v2.
