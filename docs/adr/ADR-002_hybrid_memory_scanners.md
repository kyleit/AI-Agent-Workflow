<!-- File path: docs/adr/ADR-002_hybrid_memory_scanners.md -->

# ADR-002: Tích hợp Kiến trúc Hybrid (CLI Script-First + LLM Contextual Polishing) cho Project Memory

## Status
Proposed

## Related Feature
QUICK-002

## Context
Sau khi nâng cấp thành công hệ thống Bộ nhớ Dự án (Project Memory) và RAG sang cấu trúc Script-First (FEAT-013), chúng ta đã giải quyết được các vấn đề:
1.  **Tiết kiệm token**: Giảm hơn 95% lượng token tiêu thụ của các kỹ năng.
2.  **Độ chính xác**: Các chỉ mục JSON (`file-map.json`), vector plan được sinh bằng script Python (sử dụng AST parser) chính xác tuyệt đối.
3.  **Tốc độ**: Quét dự án chỉ mất chưa đầy 0.1 giây thay vì vài phút.

Tuy nhiên, việc chạy Script thuần túy gặp phải hạn chế về **nhận thức ngữ nghĩa (semantics)**:
- Script Python chỉ có thể trích xuất các thông tin tĩnh (tên file, ngôn ngữ, các symbol import, class, function).
- Script không thể "đọc hiểu" mục đích kinh doanh hoặc kiến trúc nghiệp vụ tổng thể của một module để viết phần mô tả chất lượng cao trong `project-summary.md`. Phần mô tả này hiện tại đang bị trống hoặc rất sơ sài.

## Decision
Chúng ta quyết định áp dụng **Kiến trúc Hybrid (Kết hợp)**:
1.  **Script Python**: Quét mã nguồn, phân tích cú pháp AST, cập nhật cơ sở dữ liệu SQLite, cập nhật `file-map.json` và tạo ra phiên bản sơ thảo của tệp `project-summary.md` (chứa đầy đủ các đề mục cấu trúc và bảng biểu công nghệ).
2.  **LLM Agent (IDE)**: Sau khi script CLI chạy xong, LLM Agent sẽ đọc tệp sơ thảo này và sử dụng khả năng hiểu biết ngữ nghĩa của mình để **bổ sung, điền đầy và làm mịn (Contextual Polishing)** các mô tả nghiệp vụ của từng module chính trước khi hoàn tất công việc.

Quy tắc này sẽ được hướng dẫn trực tiếp trong phần hướng dẫn của các kỹ năng `project-memory-bootstrap/SKILL.md` và `project-memory-update/SKILL.md`.

## Trade-offs

*   **Điểm tốt (Pros)**:
    *   Tài liệu tri thức dự án (`project-summary.md`) đạt chất lượng giải thích ngữ nghĩa cao nhất (do LLM viết).
    *   Giữ nguyên được các ưu điểm của Script-First: tốc độ quét file cực nhanh, index JSON chính xác 100%, không bị hỏng cấu trúc cú pháp JSON.
    *   Tối ưu hóa token vì LLM chỉ đọc file tóm tắt trung gian và điền thêm thông tin chứ không phải đọc toàn bộ code nguồn thô của hàng trăm file.
*   **Điểm yếu (Cons)**:
    *   Đòi hỏi LLM Agent phải thực hiện thêm 1 bước ghi tệp tin bổ sung sau khi lệnh CLI hoàn tất.

## Consequences
Các tệp `SKILL.md` của `project-memory-bootstrap` và `project-memory-update` sẽ có thêm bước chỉ dẫn Agent thực hiện "làm mịn tài liệu" (polishing step).

## Risks
*   **Rủi ro**: LLM Agent có thể ghi đè làm hỏng hoặc định dạng sai các phần bảng biểu mà script đã tạo.
*   **Mitigation**: Chỉ dẫn rõ trong `SKILL.md` rằng LLM chỉ được phép sửa đổi/bổ sung nội dung text mô tả, không được thay đổi cấu trúc bảng biểu hoặc định dạng JSON.
