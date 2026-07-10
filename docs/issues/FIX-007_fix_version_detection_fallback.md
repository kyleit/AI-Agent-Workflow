<!-- File path: docs/issues/FIX-007_fix_version_detection_fallback.md -->

---
artifact_type: quick-fix
feature_id: FIX-007
workflow: quick-fix
status: PASS
---


# Quick Fix Specification – Sửa lỗi hiển thị phiên bản v0.0.0 mặc dù kho Git có Tags

## 1. Nguyên nhân lỗi (Issue Cause)
Trong tệp [validator.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/validator.py), hàm `get_version_info()` được viết như sau:
```python
def get_version_info() -> dict:
    info = {"version": "0.0.0", "source": "unknown"}
    if os.path.exists("MANIFEST.json"):
        try:
            with open("MANIFEST.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                info["version"] = data.get("version", "0.0.0")
                info["source"] = "MANIFEST.json"
        except (json.JSONDecodeError, IOError):
            pass
    return info
```

Các vấn đề dẫn đến hiển thị `v0.0.0`:
1.  Khi người dùng cài đặt framework và chạy trong một dự án của họ (Active Project), tệp `MANIFEST.json` của framework nằm tại `.agents/MANIFEST.json` chứ không nằm ở thư mục gốc của dự án. Vì hàm chỉ kiểm tra `"MANIFEST.json"` tại thư mục hiện tại (`os.path.exists`), nó luôn trả về `False` và fallback về `"0.0.0"`.
2.  Mặc dù kho Git có nhiều thẻ phiên bản (tags) như `v2.10.11`, hàm `get_version_info` hoàn toàn không có cơ chế dự phòng (fallback) để đọc phiên bản từ Git tags khi không tìm thấy `MANIFEST.json`.

## 2. Giải pháp đề xuất (Proposed Solution)
Cập nhật hàm `get_version_info()` để thực hiện tìm kiếm phiên bản theo thứ tự ưu tiên:
1.  **Bước 1**: Tìm `MANIFEST.json` ở thư mục hiện tại (dành cho môi trường phát triển chính của framework).
2.  **Bước 2**: Tìm `.agents/MANIFEST.json` ở dự án (dành cho môi trường cài đặt cục bộ).
3.  **Bước 3**: Tìm trong Git tags gần nhất bằng lệnh `git describe --tags --abbrev=0`. Nếu tìm thấy tag dạng `vX.Y.Z` hoặc `X.Y.Z`, bóc tách ký tự `v` ở đầu và lấy giá trị đó làm phiên bản, nguồn ghi nhận là `"git tag"`.
4.  **Bước 4**: Fallback về `"0.0.0"` nếu tất cả các bước trên đều thất bại.

## 3. Các tệp tin ảnh hưởng (Affected Files)
| Action | File Path | Responsibility |
| :--- | :--- | :--- |
| Modify | [skills/workflow-runtime/scripts/validator.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/validator.py) | Cập nhật logic tìm kiếm phiên bản và fallback Git tag |

## 4. Kế hoạch kiểm thử (Test Plan)
1.  Chạy unittest cho `workflow-runtime` để đảm bảo không bị hỏng cấu trúc.
2.  Chạy lệnh xuất bản `make export` để cập nhật sang `public_export`.
3.  Giả lập chạy `workflow_runtime` trong `public_export` để xác nhận nó nhận diện đúng phiên bản từ Git tag hoặc `MANIFEST.json`.
