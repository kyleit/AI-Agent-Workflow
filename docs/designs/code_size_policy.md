# Design Specification – Code Size Governance Policy

Mô tả thiết kế và đặc tả chính sách kiểm soát kích thước mã nguồn tự động trong quy trình phát triển phần mềm AIWF.

## 1. Mục tiêu
Ngăn ngừa nợ kỹ thuật bằng cách đặt ra các giới hạn kích thước tệp tin, lớp (class) và hàm (function), đồng thời phát hiện sớm các "God Files" và "God Classes" để đưa ra đề xuất tái cấu trúc mã nguồn (Refactoring Recommendations).

## 2. Các giới hạn chính sách (Limits Policy)
Hệ thống sử dụng cấu hình dưới dạng YAML/JSON tại dự án:

| Ngưỡng (Metrics) | Cảnh báo (Warning) | Giới hạn cứng (Hard Limit) |
| :--- | :---: | :---: |
| **Dòng code tối đa trên mỗi File** | 400 dòng | 500 dòng |
| **Dòng code tối đa trên mỗi Hàm** | 45 dòng | 60 dòng |
| **Dòng code tối đa trên mỗi Lớp** | N/A | 300 dòng |
| **Số phương thức tối đa trong Lớp**| N/A | 20 phương thức |

## 3. Quy trình thực thi (Enforcement Flow)

```
    Pha Debug (Cảnh báo & Gợi ý)
           ↓
    Phát hiện vượt ngưỡng cảnh báo / giới hạn cứng
           ↓
    Sinh báo cáo đề xuất tái cấu trúc (Extraction Candidates)
           ↓
    Pha Verification (Chốt chặn bắt buộc)
           ↓
    Vượt giới hạn cứng (Hard Limit) mà không được miễn trừ?
           ↓
    [FAIL] Chặn đứng Release (Khóa phiên bản)
```

## 4. Cơ chế miễn trừ ngoại lệ (Exceptions)
Các file được sinh tự động (generated code), thư viện nhúng (vendored code) hoặc tệp migration có thể được đưa vào danh sách loại trừ trong cấu hình `exceptions` gồm:
- Đường dẫn bị ảnh hưởng (`affected_path`)
- Lý do miễn trừ (`reason`)
- Người sở hữu (`owner`)
- Ngày hết hạn (`expiration_date`)
- ADR liên quan (`related_adr`)
