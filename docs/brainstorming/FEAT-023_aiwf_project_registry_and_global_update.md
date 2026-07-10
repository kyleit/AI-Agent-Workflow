# Master Requirement Document – Project Registry & Global Update CLI

## 1. Feature ID & Name
- **Feature ID**: FEAT-023
- **Feature Name**: Project Registry & Global Update CLI

## 2. Original Idea
Thêm cơ chế **Project Registry** toàn cục để CLI biết những project nào đã từng cài AIWF.
- Khi chạy `aiwf install` trong một project, CLI phải tự động lưu path project đó vào một file registry trên máy.
- Khi chạy `aiwf update` từ bất kỳ đâu, mặc định phải có khả năng update toàn bộ project đã đăng ký, không cần cd vào từng project.
- Những project đã install trước khi có tính năng registry sẽ bị thiếu trong registry, nên cần thêm lệnh `aiwf register` để kiểm tra project hiện tại và đăng ký nó vào registry nếu chưa có.
- Cần hỗ trợ unregister/cleanup để tránh registry chứa path không còn tồn tại.
- Phải chạy được trên Windows PowerShell, Windows CMD, Linux, macOS.

## 3. Business Problem
- **Problem**: Hiện tại `aiwf update` chỉ cập nhật được cho dự án hiện tại (nơi lập trình viên đang đứng chạy lệnh). Khi có nhiều dự án cùng sử dụng framework, việc cập nhật thủ công từng thư mục bằng cách `cd` vào từng nơi rất tốn thời gian, dễ bỏ sót và làm tăng chi phí quản lý vận hành.
- **Why it matters**: Lập trình viên dễ quên cập nhật các dự án cũ, dẫn đến việc các dự án chạy các phiên bản skill/rules cũ không nhất quán và thiếu các cập nhật an toàn quan trọng.
- **Who is affected**: Nhà phát triển và AI Coding Agents sử dụng AI Skill Framework trên máy cục bộ.
- **Expected outcome**:
  - Tự động hóa đăng ký dự án khi cài đặt mới.
  - Cập nhật toàn bộ các dự án đã đăng ký chỉ với một lệnh duy nhất: `aiwf update --all`.
  - Quản lý danh sách dự án gọn gàng, tự động dọn dẹp các đường dẫn rác/không còn tồn tại.
  - Hoạt động mượt mà, phi tương tác (non-interactive) trên mọi hệ điều hành (macOS, Linux, Windows).

## 4. Requirement Discovery
- **Functional Requirements**:
  - **FR-01 (Global Registry)**: Thiết lập một tệp registry JSON tại thư mục AppData chuẩn của hệ điều hành.
  - **FR-02 (Auto Register)**: Tự động đăng ký dự án mới vào registry ngay sau khi chạy `aiwf install` thành công.
  - **FR-03 (Manual Register)**: Thêm lệnh `aiwf register [--path <path>] [--force]` để đăng ký thủ công một dự án đã cài đặt cũ hoặc tại một đường dẫn chỉ định.
  - **FR-04 (Registry Management)**: Hỗ trợ các lệnh con quản lý registry:
    - `aiwf list`: Liệt kê các dự án đang đăng ký, trạng thái, phiên bản, ngày cập nhật.
    - `aiwf unregister [--path <path>]`: Hủy đăng ký dự án hiện tại hoặc dự án tại đường dẫn chỉ định.
    - `aiwf registry doctor`: Chẩn đoán trạng thái registry (kiểm tra các đường dẫn có tồn tại hay không, có bị mất thư mục `.agents/` hay không).
    - `aiwf registry cleanup`: Dọn dẹp/xóa bỏ hoặc đánh dấu missing các dự án có đường dẫn không còn tồn tại.
  - **FR-05 (Global Update)**: Nâng cấp `aiwf update` hỗ trợ `--all` để lặp qua tất cả các dự án hoạt động trong registry và thực hiện cập nhật. Hỗ trợ cập nhật tuần tự, ghi nhận lỗi riêng lẻ và tổng hợp báo cáo (Summary Report).
  - **FR-06 (Compatibility)**: Giữ nguyên hành vi mặc định `aiwf update` (hoặc `aiwf update --current`) cho dự án hiện tại.

- **Non-functional Requirements**:
  - **NFR-01 (Atomic Writes)**: Đọc/ghi tệp registry JSON phải thực hiện nguyên tử (atomic: ghi ra file `.tmp` rồi rename) để tránh hỏng file khi tiến trình bị ngắt đột ngột.
  - **NFR-02 (Corrupted Recovery)**: Nếu file registry JSON bị hỏng cấu trúc, tự động tạo file backup `<name>.bak.<timestamp>` và khởi tạo lại tệp registry mới, không được gây crash CLI.
  - **NFR-03 (Path Normalization)**: Đường dẫn dự án lưu trong registry phải là đường dẫn tuyệt đối đã chuẩn hóa. Trên Windows, việc so sánh đường dẫn phải không phân biệt chữ hoa chữ thường (case-insensitive).
  - **NFR-04 (Multi-platform support)**: Đảm bảo tương thích trên PowerShell, Bash và Windows CMD.

- **Technical Constraints**:
  - **TC-01**: Không sử dụng các thư viện ngoài phức tạp để tránh gây lỗi phụ thuộc môi trường. Tận dụng thư viện chuẩn của Python.
  - **TC-02**: Không thay đổi hoặc làm mất các file memory, cấu hình tùy biến (customization) của người dùng khi chạy cập nhật đồng loạt.

## 5. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Registry path cụ thể trên các OS là gì? | - Windows: `%APPDATA%\aiwf\projects.json` (hoặc `~/.aiwf/projects.json` làm fallback). <br>- macOS: `~/Library/Application Support/aiwf/projects.json` (hoặc `~/.aiwf/projects.json` làm fallback). <br>- Linux: `~/.config/aiwf/projects.json` (hoặc `~/.aiwf/projects.json` làm fallback). |
| Có hiển thị prompt khi chạy `aiwf update --all` từ môi trường interactive không? | Có, nếu chạy trong terminal tương tác, hiển thị menu lựa chọn: <br>1. Chỉ cập nhật dự án hiện tại<br>2. Cập nhật tất cả dự án đã đăng ký<br>3. Hủy bỏ. <br>Trong môi trường non-interactive hoặc khi truyền tham số cụ thể (`--all` / `--current`), bỏ qua prompt. |

## 6. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 7. Existing Project Context
- **Memory Source**: `project-profile.json` và cấu trúc CLI hiện có.
- **Existing Architecture Summary**:
  - CLI `aiwf` là một shell wrapper mỏng phân phối (dispatch) lệnh đến script Python lõi `workflow_runtime.py`.
  - Cơ chế đồng bộ SQLite được tích hợp trong Workflow Runtime để lưu trữ session cục bộ.

## 8. Existing Modules & Services
| Module/Service | Location | Relevance |
|---|---|---|
| Workflow Runtime Script | [skills/workflow-runtime/scripts/workflow_runtime.py](file:///Volumes/Kyle/AgentsProject/skills/workflow-runtime/scripts/workflow_runtime.py) | Điểm tiếp nhận lệnh chính của CLI. |
| Installer Script | [install.sh](file:///Volumes/Kyle/AgentsProject/install.sh) | Cần cập nhật để tự động đăng ký sau khi cài đặt thành công. |
| Update Script | [update.sh](file:///Volumes/Kyle/AgentsProject/update.sh) | Cần cập nhật để tích hợp lệnh cập nhật toàn cục. |

## 9. Solution Options Evaluated

### Option A: Tích hợp Module `aiwf_registry.py` chuyên biệt dưới Runtime Scripts
- **Overview**: Viết module Python mới `skills/workflow-runtime/scripts/aiwf_registry.py` chứa toàn bộ logic xử lý registry, chuẩn hóa path, ghi tệp nguyên tử. Đăng ký sub-command `registry` trong `workflow_runtime.py`.
- **Architecture**: CLI `aiwf` gọi qua `workflow_runtime.py registry <cmd>`.
- **Advantages**: Rất sạch sẽ, chia sẻ chung các utility JSON của runtime, dễ viết tests độc lập.
- **Disadvantages**: Cần tích hợp cẩn thận các tham số argparse trong tệp runtime chính.

### Option B: Viết CLI Registry độc lập ở thư mục root
- **Overview**: Viết script `tools/aiwf_registry.py` độc lập ở root, các script shell gọi trực tiếp script này thay vì đi qua `workflow_runtime.py`.
- **Advantages**: Hoàn toàn cô lập khỏi runtime session engine.
- **Disadvantages**: Trùng lặp code xử lý ghi JSON nguyên tử, khó tích hợp chẩn đoán lỗi đồng nhất.

## 10. Selected Solution
- **Choice**: Option A — Centralized `aiwf_registry.py` under Runtime Scripts.
- **Why Selected**: Mang lại cấu trúc CLI đồng nhất nhất, shell wrappers không cần thay đổi phức tạp mà chỉ cần delegate sang Python CLI hiện có.

## 11. Acceptance Criteria
- [ ] `aiwf install` tự động đăng ký dự án hiện tại vào registry.
- [ ] `aiwf register` cho phép đăng ký dự án cũ thủ công.
- [ ] `aiwf list` hiển thị đầy đủ danh sách dự án.
- [ ] `aiwf update --all` cập nhật thành công tất cả các dự án trong registry và ghi Summary Report.
- [ ] Ghi tệp JSON registry bằng cơ chế ghi nguyên tử an toàn (atomic write) và tự động khôi phục nếu file JSON bị hỏng cấu trúc.
- [ ] Windows PowerShell, Windows CMD, Linux, macOS đều hoạt động tốt.

---

## 12. Final Planning Prompt

### Purpose
Tạo prompt hoàn chỉnh để chuyển giao sang bước lập kế hoạch thực hiện (`plan`).

### Objectives & Selected Solution
- Nâng cấp CLI `aiwf` hỗ trợ Project Registry toàn cục và cơ chế cập nhật toàn bộ dự án (`aiwf update --all`).
- Triển khai tệp registry Python mới `skills/workflow-runtime/scripts/aiwf_registry.py` và đăng ký sub-commands tương ứng trong `workflow_runtime.py`.
- Cập nhật các scripts cài đặt/cập nhật đa nền tảng (`install`, `update`, `doctor`).

### Verification Checklist
- [ ] Viết unit tests kiểm tra toàn bộ logic của `aiwf_registry.py` (atomic write, recovery, path normalization).
- [ ] Tạo môi trường temp dự án giả lập để chạy thử nghiệm thực tế đăng ký, hiển thị danh sách, dọn dẹp và cập nhật toàn bộ.
