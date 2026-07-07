# Hướng dẫn sử dụng AI Skill Framework

Tài liệu này hướng dẫn chi tiết cách cấu hình, sử dụng và vận hành các AI Skill trong toàn bộ vòng đời phát triển phần mềm (SDLC) của dự án.

---

## 🚀 1. Khởi động nhanh (Quick Start)

### Bước 1: Cài đặt CLI Toàn cục (`aiwf`)
Để có thể gọi các lệnh CLI từ bất kỳ đâu, hãy mở terminal tại thư mục của Framework này và chạy:

* **Trên Windows (PowerShell):**
  ```powershell
  .\bootstrap.ps1
  ```
* **Trên Linux/macOS:**
  ```bash
  ./bootstrap.sh
  ```

### Bước 2: Thiết lập dự án của bạn
Di chuyển terminal đến dự án Git mà bạn muốn sử dụng các Skill, sau đó khởi tạo gói Skill cục bộ:
```bash
aiwf install
```
Lệnh này sẽ tạo thư mục `.agents/` chứa luật cấu hình `AI_RULES.md`, danh sách `skills/` và các mẫu prompts tại `templates/`.

### ⚙️ Lựa chọn Workspace Permission Mode (Chế độ Phân quyền)
Khi bắt đầu khởi chạy lệnh `/init` (hoặc `/initialize-workflow`), bạn sẽ được hỏi lựa chọn chế độ phân quyền:
* **Sandbox Mode** (Lựa chọn 1 - Mặc định): An toàn tối đa. Agent luôn dừng lại hỏi ý kiến bạn trước khi chỉnh sửa file, sửa code, chạy build/test hoặc update memory.
* **Full Access Mode** (Lựa chọn 2): Tiết kiệm thời gian. Agent tự động thực hiện các hành động phát triển thông thường mà không cần hỏi lại. Tuy nhiên các hành động quan trọng (git commit, git push, git tag, release, delete file lớn...) vẫn giữ nguyên cơ chế Hard-gated (phải hỏi duyệt).
* **Unrestricted Mode** (Lựa chọn 3 - VÙNG NGUY HIỂM): Tự động hóa hoàn toàn. Bỏ qua toàn bộ chốt chặn hỏi ý kiến của tất cả mọi hành động (kể cả git push, release). Để kích hoạt, bạn bắt buộc phải nhập mã xác nhận `CONFIRM_UNRESTRICTED`.

Cách chạy init kèm chế độ phân quyền bằng CLI:
- Để chọn Sandbox:
  ```bash
  aiwf init --permission 1
  ```
- Để chọn Full Access:
  ```bash
  aiwf init --permission 2
  ```
- Để chọn Unrestricted:
  ```bash
  aiwf init --permission 3
  ```

---

## 🔄 2. Quy trình làm việc hàng ngày (SDLC Workflow)

### 🧠 Tự động hóa điều phối điều hành (/orchestrate) — *Khuyên dùng làm điểm đầu vào*
Thay vì gọi các Skill đơn lẻ thủ công, bạn chỉ cần gọi lệnh `/orchestrate` cùng với mục tiêu phát triển. Hệ thống sẽ tự động chẩn đoán công cụ, phân tích intent để xác định quy trình, phân chia tác vụ song song, thực thi an toàn bằng cơ chế khóa tệp và tự động tích hợp mã nguồn.
* **Cách kích hoạt**:
  ```bash
  /orchestrate "Mô tả tính năng hoặc bug cần xử lý ở đây"
  ```
* **Ví dụ**:
  - `/orchestrate Sửa lỗi login bị đơ`
  - `/orchestrate Thêm hệ thống caching cho tệp tĩnh Playwright`
  - `/orchestrate Xây dựng giao diện đăng ký tài khoản`
* **Xử lý song song**: Chạy song song chỉ được phép thực hiện trong pha triển khai (Implementation/Execution). Các pha trước đó (Discovery, Brainstorming, Planning, Blueprint) sẽ luôn chạy tuần tự. Khi bắt đầu bước triển khai, hệ thống sẽ đề xuất biểu đồ tác vụ (DAG) và hiển thị menu lựa chọn Parallel/Sequential để bạn quyết định.

Mỗi tính năng mới trong dự án sẽ được quản lý dưới một mã số duy nhất (**Feature ID** - dạng `FEAT-001`, `FEAT-002`,...) và đi qua các bước tuần tự dưới đây. 


### 🔒 Chốt chặn Gợi ý Kỹ năng tự động (Skill Suggestion Gate)
Khi bạn gửi một yêu cầu ngôn ngữ tự nhiên thuần (không bắt đầu bằng lệnh cụ thể như `/workflow`, `/quick-fix`, `/quick-feature`, `/brainstorm`), Agent sẽ dừng lại và hiển thị phân loại đề xuất.
* **Cách xác nhận**: Bạn có thể gõ `Y`, `Yes`, `Proceed` hoặc chọn số thứ tự phương án đề xuất để Agent tiếp tục.
* **Xác nhận bằng CLI**:
  ```bash
  aiwf suggest --choose Y
  ```

---

### Pha 1: Khám phá Yêu cầu (Product Discovery)
Chuyển hóa ý tưởng thô của bạn thành tài liệu đặc tả hoàn chỉnh.
* **Cách kích hoạt**: 
  ```bash
  /brainstorm idea="Mô tả ý tưởng của bạn ở đây"
  ```
* **Luồng xử lý**: Skill sẽ hỏi bạn các câu hỏi làm rõ nếu độ sẵn sàng của yêu cầu (Readiness Score) dưới 85.
* **Sản phẩm đầu ra**: File master requirements tại `docs/brainstorming/FEAT-XXX_<feature_name>.md`.

---

### Pha 2: Lên Kế hoạch triển khai (Technical Planning)
Phân tích blast radius của code hiện tại và lập trình kế hoạch chi tiết.
* **Cách kích hoạt**: 
  ```bash
  /plan prompt_file="docs/brainstorming/FEAT-XXX_<feature_name>.md"
  ```
* **Sản phẩm đầu ra**: Kế hoạch tại `docs/plans/FEAT-XXX_<feature_name>_plan.md`.

---

### Pha 3: Thiết kế Kỹ thuật (Technical Design Blueprint)
Thiết kế các interface, sơ đồ sequence diagram và đánh giá sự cần thiết của ADR.
* **Cách kích hoạt**: 
  ```bash
  /blueprint source_plan="docs/plans/FEAT-XXX_<feature_name>_plan.md"
  ```
* **Phê duyệt Blueprint**: Sau khi Agent tạo file thiết kế tại `docs/designs/FEAT-XXX_<feature_name>_blueprint.md`, bạn bắt buộc phải duyệt Blueprint để cho phép sửa đổi source code:
  ```bash
  aiwf blueprint --path docs/designs/FEAT-XXX_<feature_name>_blueprint.md --approve
  ```
* **Sản phẩm đầu ra**: Bản thiết kế tại `docs/designs/FEAT-XXX_<feature_name>_blueprint.md`.

---

### [Tùy chọn] Pha 4: Quyết định Kiến trúc (ADR)
Lưu giữ lại quyết định thay đổi kiến trúc hệ thống quan trọng nếu Bản thiết kế ở Pha 3 yêu cầu (`ADR Required: Yes`).
* **Cách kích hoạt**: 
  ```bash
  /adr title="Tiêu đề quyết định" related_feature="docs/brainstorming/FEAT-XXX_*.md"
  ```
* **Sản phẩm đầu ra**: File quyết định độc lập tại `docs/adr/ADR-XXX_*.md`.

---

### Pha 5: Triển khai Code (Implementation)
Thực hiện chỉnh sửa mã nguồn và viết test case kiểm thử.
* **Cách kích hoạt**: 
  ```bash
  /implement design_file="docs/designs/FEAT-XXX_<feature_name>_blueprint.md"
  ```
* **Ràng buộc an toàn**: Chỉ được phép thực hiện khi bản thiết kế Blueprint tương ứng đã được bạn **phê duyệt** rõ ràng qua lệnh `aiwf blueprint`. Mọi hành vi sửa code không có Blueprint được duyệt sẽ bị CLI chặn ngay lập tức.
* **Sản phẩm đầu ra**: Mã nguồn hoàn chỉnh trong dự án của bạn.

---

### Pha 6: Phát hành tính năng (Release)
Băm phiên bản, ghi log release và commit/push lên Git.
* **Cách kích hoạt**:
  Bạn phải yêu cầu tường minh (ví dụ gõ `/release`, `release`, `bump version` hoặc gọi `/implementation-to-release`). Agent tuyệt đối không bao giờ tự động chuyển tiếp hay tự ý Release.
* **Cách chạy**:
  ```bash
  /release
  ```
* **Sản phẩm đầu ra**: Cập nhật trực tiếp vào file `CHANGELOG.md` gốc, tạo commit release và đẩy lên Remote Git.

---

## 🛠️ 3. Quản lý hệ thống bằng CLI `aiwf`

Trong terminal dự án, bạn có thể chạy các lệnh quản trị tiện ích:

| Lệnh | Ý nghĩa / Tác dụng |
|------|--------------------|
| `aiwf doctor` | Khởi chạy trình kiểm tra sức khỏe, báo cáo lỗi/cảnh báo cấu hình. |
| `aiwf version` | Báo cáo thông tin phiên bản CLI và repository gốc đang liên kết. |
| `aiwf install` | Cài đặt các tệp tin runtime cần thiết vào dự án cục bộ `.agents/`. |
| `aiwf update` | Cập nhật các AI Skill cục bộ lên phiên bản mới nhất của framework. |
| `aiwf uninstall` | Gỡ cài đặt an toàn (chỉ xóa các file framework, giữ lại dữ liệu của bạn). |
| `aiwf memory bootstrap` | Khởi tạo Project Memory từ đầu (phát hiện ngôn ngữ, frameworks, parser symbols và lưu trữ SQLite/file). |
| `aiwf memory update [--full]` | Cập nhật tăng cường tri thức dự án thông qua git-diff hoặc timestamp fallback. |
| `aiwf memory search "<query>"` | Truy vấn tìm kiếm RAG kết hợp từ khóa cục bộ và vector Qdrant. |


---

## 💡 4. Nguyên tắc cốt lõi khi làm việc với AI Agent

Để tối ưu hóa chi phí token và đạt chất lượng tốt nhất, các Skill tuân thủ nguyên tắc:
1. **Memory-First**: Luôn đọc Project Memory (`.agents/memory/`) và kết quả RAG trước khi tiến hành đọc chi tiết toàn bộ mã nguồn.
2. **Không tự động chuyển pha**: Mỗi Skill kết thúc sẽ tạm dừng và đưa ra khuyến nghị Skill tiếp theo. Quyết định chạy bước tiếp theo hoàn toàn thuộc về bạn (Ba).
3. **Cấu trúc thư mục tối giản**: Tránh phân tán tài liệu ở nhiều nơi, hãy giữ đúng cấu trúc trong thư mục `docs/` để Agent dễ dàng theo dấu.
