# ADR-055: Distributed Resource-Aware Scheduler

- **Status**: Proposed
- **Program**: Program B
- **Domain**: Distributed Scheduler
- **Related FEATs**: FEAT-203
- **Context & Problem**: Lập lịch v2 chỉ chạy đơn máy, cần khả năng điều phối tác vụ chéo node dựa trên tài nguyên trống.
- **Decision**: Triển khai thuật toán lập lịch Kahn mở rộng chéo máy; Node định kỳ gửi metric CPU/RAM/GPU trống để Master định tuyến.
- **Consequences**: Cân bằng tải tối ưu chéo cluster.
- **Backward Compatibility**: Trả về scheduler cục bộ nếu kết nối cloud thất bại.
