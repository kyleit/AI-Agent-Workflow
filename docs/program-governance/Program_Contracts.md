# AIWF OS v2 Program Contracts

Định nghĩa hợp đồng dữ liệu và các giao thức giao tiếp chung giữa các Program.

## 1. Giao thức truyền tin (IPC)
- **Chuẩn**: JSON-RPC 2.0 chạy qua mTLS gRPC.
- **Schema chung**:
  ```json
  {
    "jsonrpc": "2.0",
    "method": "program_rpc",
    "params": {},
    "id": 1
  }
  ```

## 2. Giao thức Bảo mật (Shared Security Contract)
- Mọi token ủy quyền xác thực phải sử dụng định dạng chữ ký số HMAC SHA-256 từ Core.
