# AIWF Runtime Governance

Quy định quản trị và bảo vệ tính toàn vẹn của nền tảng Runtime Foundation v1.

## 1. Nguyên tắc cốt lõi
- **Chỉ một Orchestrator sống**: Cấm hoàn toàn việc chạy song song hai orchestrators trên cùng một thư mục làm việc.
- **Thực thi phân cấp**: Các Subagents chỉ được phân quyền chạy các công cụ được chỉ định và không được tự ý sinh hoặc điều phối các tác nhân con khác ngoài tầm kiểm soát của Supervisor.
- **Split-state integrity**: Không lưu thông tin trạng thái ở các vị trí tuỳ tiện. Vị trí duy nhất được cho phép là `.agents/state/`.
