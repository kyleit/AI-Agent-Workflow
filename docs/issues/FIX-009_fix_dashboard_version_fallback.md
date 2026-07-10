# Issue Fix – Fix Dashboard Version Fallback (FIX-009)

## 1. Vấn đề (Issue)
Trường hiển thị phiên bản ở góc trên bên trái của **Workflow Session Dashboard** trong Sidebar hiển thị `v0.0.0` thay vì phiên bản thực tế của bộ Skills Framework (ví dụ `2.13.0` hoặc `2.13.1`).

### Nguyên nhân gốc:
- Giao diện Webview kết xuất phiên bản bằng cách đọc thuộc tính `data.version.version` được gửi từ Extension Backend lên thông qua tin nhắn `UPDATE_SESSION`.
- Extension Backend (`extension.ts`) đọc trường này từ tệp `.session.json` của dự án đích.
- Khi dự án mới được khởi tạo bằng `initialize-workflow`, hoặc khi CLI chưa chạy cập nhật session sau khi khởi tạo, tệp `.session.json` lưu giá trị mặc định là `"version": { "version": "0.0.0" }`, dẫn đến giao diện hiển thị sai lệch.

---

## 2. Giải pháp khắc phục (Proposed Fix)
Thay vì phụ thuộc vào việc cập nhật gián tiếp của CLI qua tệp `.session.json`, Extension Backend của IDE sẽ luôn tự động **đọc trực tiếp và ghi đè** phiên bản thực tế từ tệp `.agents/MANIFEST.json` vào dữ liệu session trước khi gửi lên Webview để hiển thị.

### Chi tiết thay đổi trong [extension.ts](file:///Volumes/Kyle/AgentsProject/extensions/visualizer/src/extension.ts):
```typescript
// Trong hàm updateSessionData()
// Force version to always reflect the actual version from MANIFEST.json directly
const currentAgentsDir = path.dirname(this._sessionPath);
const currentManifestPath = path.join(currentAgentsDir, 'MANIFEST.json');
if (fs.existsSync(currentManifestPath)) {
    try {
        const manifest = JSON.parse(fs.readFileSync(currentManifestPath, 'utf8'));
        if (manifest.version) {
            session.version = {
                version: manifest.version,
                source: 'MANIFEST.json'
            };
        }
    } catch (e) {
        // ignore
    }
}
```

---

## 3. Kết quả xác thực (Verification Results)
- Đã biên dịch lại extension thành công bằng `npm run compile`.
- Logic đọc file JSON trực tiếp từ `MANIFEST.json` hoạt động chính xác, đảm bảo đồng bộ hóa thông tin phiên bản tức thì ngay khi mở panel visualizer.
- Khi cập nhật thư mục `.agents/` bằng lệnh `aiwf update`, tệp `MANIFEST.json` cập nhật phiên bản mới sẽ được Extension nhận diện ngay lập tức để tắt banner thông báo cập nhật một cách tự động.
