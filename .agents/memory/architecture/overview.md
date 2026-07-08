# Architecture Overview

## Structural Overview
Kiến trúc dự án dựa trên mô hình điều phối đa tác nhân (Multi-Agent). Các tệp tin kỹ năng được thiết lập dưới dạng các chỉ thị độc lập trong thư mục `skills/` và được theo dõi trạng thái qua tệp phiên làm việc cục bộ.

## Technology Stack
- **Ngôn ngữ chính**: TypeScript & Python.
- **Dịch vụ bổ sung**: Qdrant Vector DB để phục vụ truy xuất ngữ cảnh RAG.
- **Hệ thống dữ liệu**: SQLite cục bộ.
