<!-- File path: docs/designs/FEAT-044_visualizer_tabbed_sidebar_blueprint.md -->

---
feature_id: FEAT-044
feature_name: Visualizer Tabbed Sidebar
status: approved
stage: blueprint
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../plans/FEAT-044_visualizer_tabbed_sidebar_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Visualizer Tabbed Sidebar

## 0. Baseline Context & References
- **Memory Baseline**: Cấu trúc UI của Visualizer Extension hiển thị qua tệp `webview.html`, là tệp nguồn để biên dịch sang `webviewHtml.ts` thông qua `build.js`.
- **RAG Query Summaries**: Không có truy vấn RAG bổ sung, kế hoạch sử dụng lại các token và kiểu dáng CSS hiện có của extension.
- **Inspected Source Files**:
  - `extensions/visualizer/resources/webview.html` (chứa toàn bộ giao diện và logic tương tác).

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `extensions/visualizer/resources/webview.html` | `MODIFY` | Thêm kiểu dáng CSS cho Custom Select và hệ thống Tab; Tái cấu trúc cấu trúc HTML phân tách 2 Tab panel; Bổ sung logic JavaScript xử lý chuyển đổi Tab và Custom Select UI. | `build.js` | Rất thấp. Cải thiện trải nghiệm trực quan mà không ảnh hưởng tới luồng dữ liệu. |
| `extensions/visualizer/src/webviewHtml.ts` | `MODIFY` | Tệp giao diện được tự động biên dịch lại. | `webview.html` | Thấp. Được quản lý bởi trình biên dịch. |

## 2. Target Folder Structure
```text
.
├── docs
│   ├── brainstorming
│   │   └── FEAT-044_visualizer_tabbed_sidebar.md
│   ├── designs
│   │   └── FEAT-044_visualizer_tabbed_sidebar_blueprint.md
│   └── plans
│       └── FEAT-044_visualizer_tabbed_sidebar_plan.md
└── extensions
    └── visualizer
        ├── resources
        │   └── webview.html
        └── src
            └── webviewHtml.ts
```

## 3. Interface Contracts (Public & Internal)
- **ViewModel Schema**: Tương thích ngược hoàn toàn với dữ liệu `.agents/.session.json` hiện có.
- **Custom Select Interface**:
  - Các phần tử HTML ẩn có dạng `<input type="hidden" id="diff-select-a">` và `<input type="hidden" id="diff-select-b">` để lưu giữ giá trị được lựa chọn.
  - Khi người dùng thay đổi giá trị trên Custom Select UI, sự kiện `change` sẽ được dispatch lên hai thẻ ẩn này, đảm bảo các hàm so sánh token diff hoạt động bình thường mà không cần sửa đổi mã nguồn xử lý sự kiện.

## 4. Algorithms & Key Logic

### A. Hệ thống chuyển đổi Tab (Tab Switcher)
- Gán sự kiện click lên các nút Tab:
  ```javascript
  let currentActiveTab = 'checkpoints';
  function switchTab(tabId) {
      currentActiveTab = tabId;
      document.getElementById('panel-checkpoints').style.display = tabId === 'checkpoints' ? 'block' : 'none';
      document.getElementById('panel-stats').style.display = tabId === 'stats' ? 'block' : 'none';
      
      document.getElementById('btn-tab-checkpoints').classList.toggle('active', tabId === 'checkpoints');
      document.getElementById('btn-tab-checkpoints').setAttribute('aria-selected', tabId === 'checkpoints' ? 'true' : 'false');
      
      document.getElementById('btn-tab-stats').classList.toggle('active', tabId === 'stats');
      document.getElementById('btn-tab-stats').setAttribute('aria-selected', tabId === 'stats' ? 'true' : 'false');
  }
  ```
- Trong hàm `updateUI`, kiểm tra và thiết lập lại `display: block/none` dựa trên trạng thái của biến `currentActiveTab` để không bị nhảy tab khi làm mới dữ liệu.

### B. Custom Select UI Controller
- Sử dụng cấu trúc HTML tùy biến với các lớp `.custom-select-wrapper`, `.custom-select-trigger`, và `.custom-select-options`.
- Thêm sự kiện click lên trigger để thêm/bớt lớp `.open` để ẩn/hiện danh sách tùy chọn.
- Lắng nghe click toàn cục trên `document` để tự động đóng dropdown khi click ra ngoài.

## 5. State Machine & Transitions
- **Các trạng thái Tab**:
  - `Checkpoints`: Mặc định. Hiển thị danh sách checkpoint và logs.
  - `Stats`: Hiển thị phân tích context, accumulated API cost và lịch sử request.

## 6. Validation and Safety Constraints
- Đảm bảo kiểm tra sự tồn tại của các phần tử DOM trước khi gán sự kiện hoặc thay đổi kiểu dáng.
- Giới hạn chiều cao tối đa của dropdown Custom Select để không làm tràn khung giao diện của sidebar.

## 7. Backward Compatibility & Migration Mapping
- Không thay đổi các biến trạng thái, giữ nguyên cấu trúc phẳng để tương thích với phiên bản hiện tại.

## 8. Implementation Checklist
- [ ] Bổ sung các lớp CSS cho Custom Select UI và hệ thống Tab trong thẻ `<style>` của `webview.html`.
- [ ] Thêm cấu trúc HTML cho hệ thống Tab mới ngay dưới khối `Workflow Session`.
- [ ] Tạo div bọc `#panel-checkpoints` chứa `#workflow-panel` và `#analysis-agents-section`.
- [ ] Tạo div bọc `#panel-stats` chứa các card thống kê và lịch sử request.
- [ ] Thay thế thẻ `<select>` mặc định bằng mã HTML Custom Select UI.
- [ ] Bổ sung mã JavaScript xử lý chuyển đổi Tab và điều khiển Custom Select UI ở phần cuối thẻ `<script>`.
- [ ] Biên dịch bằng `node build.js` trong thư mục `extensions/visualizer/`.

## 9. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Session box hiển thị cố định | Khối Workflow Session luôn hiển thị ở trên cùng khi chuyển đổi giữa cả hai tab. | Kiểm thử trực quan | Manual |
| `REQ-002` | Author box hiển thị cố định | Khối Framework Author luôn hiển thị ở dưới cùng khi chuyển đổi giữa cả hai tab. | Kiểm thử trực quan | Manual |
| `REQ-003` | Tab Checkpoints phân tách | Chỉ hiển thị checkpoint timeline và logs. | Chọn tab Checkpoints và kiểm tra | Manual |
| `REQ-004` | Tab Statistics phân tách | Chỉ hiển thị các card phân tích và token diff. | Chọn tab Context / Statistics và kiểm tra | Manual |
| `REQ-005` | Custom Select UI hoạt động | Thay thế hộp chọn mặc định bằng Custom Select, nhấn mở dropdown đẹp mắt và tương tác bình thường. | Bấm chọn request so sánh trên UI | Manual |

## 10. Disallowed Outputs Validation
- [x] Không sử dụng đường dẫn tuyệt đối hoặc `file://`.
- [x] Không sử dụng các từ viết tắt `TBD` hoặc placeholder rỗng.
- [x] Không gán các giá trị phân quyền không an toàn.
