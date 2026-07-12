# AIWF Runtime Contract v1

Các quy tắc giao diện dữ liệu bắt buộc (Data Schemas) của hệ thống.

## 1. Trạng thái nhiệm vụ (Task Schema)
Mọi tác vụ trong đồ thị (DAG) phải tuân thủ schema:
```json
{
  "name": "Tên tác vụ",
  "role": "discovery | planning | blueprint | implementation | debug | verify | release",
  "status": "ready | pending | running | completed | failed | blocked",
  "dependencies": ["ID_Tác_Vụ_Cha"],
  "write_scope": "Thư mục phạm vi ghi của tác vụ"
}
```

## 2. Nhật ký sự kiện (Event Schema)
Mọi sự kiện được xuất bản lên bus phải chứa:
```json
{
  "event_type": "Tên loại sự kiện",
  "timestamp": "ISO-8601 String",
  "message": "Nội dung thông điệp mô tả sự kiện"
}
```
