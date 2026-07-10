# Hướng Dẫn Tích Hợp & Đồng Bộ Obsidian Cho AI Skill Framework

Tài liệu này hướng dẫn chi tiết từng bước giúp Ba thiết lập Obsidian làm Kho Lưu Trữ Tri Thức Dài Hạn (Knowledge Vault) và đồng bộ hóa với AI Skill Framework.

---

## 1. Chuẩn Bị & Cấu Hình Trên Phần Mềm Obsidian

### Bước 1.1: Tạo Vault Tri Thức
1. Mở phần mềm **Obsidian** trên máy tính của Ba.
2. Chọn **Create new vault** (Tạo vault mới).
3. Đặt tên vault (ví dụ: `AIWF-Knowledge`) và chọn đường dẫn lưu trữ.
   > [!IMPORTANT]
   > Đường dẫn thư mục chứa Vault này (ví dụ `/path/to/your/obsidian/vaults`) sẽ được sử dụng làm cấu hình `vault_root` ở các bước cấu hình dự án tiếp theo.

### Bước 1.2: Cài đặt và Cấu hình plugin "Local REST API" (Chỉ khi dùng chế độ REST)
*Lưu ý: Nếu Ba chỉ dùng chế độ đồng bộ file cục bộ (`file-sync` - khuyến nghị vì đơn giản và nhanh), Ba có thể bỏ qua bước này.*

1. Trong Obsidian, nhấn vào biểu tượng bánh răng **Settings** (Cài đặt) ở góc dưới bên trái.
2. Chọn mục **Community plugins** ➔ Nhấn **Turn on community plugins** để bật tính năng cài plugin bên ngoài.
3. Nhấn **Browse** và tìm kiếm từ khóa: `Local REST API`.
4. Nhấn **Install** ➔ Nhấn **Enable** để kích hoạt plugin.
5. Sau khi kích hoạt, ở phần cấu hình plugin **Local REST API**:
   - Chọn **Enable HTTPS** (hoặc tắt đi tùy thuộc vào môi trường).
   - Ba sẽ nhìn thấy ô **API Key**. Hãy sao chép (Copy) khóa API này để sử dụng khi cấu hình CLI.

---

## 2. Khởi Tạo & Cấu Hình Dự Án Mới

Mỗi khi bắt đầu một dự án mới (ví dụ: `gh-vnc`), Ba thực hiện cấu hình theo 1 trong 2 cách sau:

### Cách 1: Cấu hình tự động bằng dòng lệnh (Khuyến nghị)
1. Mở Terminal và di chuyển vào thư mục gốc của dự án.
2. Chạy lệnh cấu hình tương tác:
   ```bash
   aiwf provider add obsidian --project
   ```
3. Nhập các thông số tương tác:
   * **vault_root**: Nhập đường dẫn thư mục cha chứa Vault Obsidian của Ba (ví dụ: `/path/to/your/obsidian/vaults`).
   * **project_folder_pattern**: Nhập định dạng tên thư mục Vault của dự án (mặc định: `AIWF-Knowledge-{project_slug}`).
   * **mode**: Nhập chế độ đồng bộ:
     * Nhập `file-sync` (ấn **Enter** chọn mặc định): Đồng bộ ghi chép trực tiếp qua tệp tin (không yêu cầu API Key).
     * Nhập `rest` hoặc `bidirectional`: Đồng bộ qua mạng HTTPS (yêu cầu điền API Key sao chép ở Bước 1.2).
   * **Create if missing? (y/n)**: Chọn `y` (để hệ thống tự tạo thư mục Vault con cho dự án nếu chưa có).
   * **Sync structure? (y/n)**: Chọn `y` (để tự động phân chia tri thức thành 11 thư mục theo bản chất dữ liệu).

---

### Cách 2: Cấu hình thủ công bằng tệp JSON
Ba tạo tệp tin tại đường dẫn:
➔ `[project-root]/.agents/memory.config.json`

Và ghi đè nội dung cấu hình chuẩn hóa sau:
```json
{
  "project_id": "gh-vnc",
  "memory_root": ".agents/memory",
  "providers": {
    "obsidian": {
      "enabled": true,
      "mode": "file-sync",
      "vault_root": "/path/to/your/obsidian/vaults",
      "project_folder_pattern": "AIWF-Knowledge-{project_slug}",
      "create_if_missing": true,
      "sync_structure": true,
      "folder_mapping": {
        "docs/brainstorming": "Brainstorming",
        "docs/plans": "Plans",
        "docs/quick": "Brainstorming",
        "docs/issues": "Plans",
        "docs/designs": "Blueprints",
        "docs/adr": "ADRs",
        "docs/releases": "Releases",
        ".agents/memory": "Project Memory",
        "lessons": "Lessons",
        "patterns": "Patterns",
        "docs/prompts": "Prompts",
        "docs/verification": "Verification",
        "docs/debug": "Debug",
        "docs/archive": "Archive"
      }
    }
  }
}
```

---

## 3. Kích Hoạt Đồng Bộ Hóa Sang Obsidian

Sau khi cấu hình xong, Ba có thể thực hiện đồng bộ hóa tri thức bất kỳ lúc nào bằng 1 trong các cách sau:

### Cách 3.1: Đồng bộ hóa thủ công
Chạy lệnh đồng bộ trực tiếp:
```bash
aiwf sync obsidian
```

### Cách 3.2: Đồng bộ hóa tự động kèm Cập nhật bộ nhớ dự án
Mỗi khi có thay đổi code hoặc tài liệu, Ba chạy lệnh cập nhật bộ nhớ toàn cục, Obsidian sẽ tự động đồng bộ ở bước cuối cùng:
```bash
aiwf memory sync
```

---

## 4. Quản Lý & Phân Phối Thư Mục Trong Obsidian

Sau khi đồng bộ hoàn tất, cấu trúc tri thức của Ba trong Obsidian Vault sẽ hiển thị trực quan như sau:

* 📂 **`Brainstorming/`**: Chứa các tệp đặc tả tính năng (`docs/quick/QUICK-XXX.md`) và ý tưởng thiết kế.
* 📂 **`Plans/`**: Chứa các kế hoạch vá lỗi (`docs/issues/FIX-XXX.md`) và kế hoạch triển khai.
* 📂 **`Blueprints/`**: Bản thiết kế kỹ thuật chi tiết (`docs/designs/FEAT-XXX_blueprint.md`).
* 📂 **`ADRs/`**: Các quyết định kiến trúc quan trọng (`docs/adr/`).
* 📂 **`Releases/`**: Nhật ký phát hành và phân phối (`docs/releases/`).
* 📂 **`Prompts/`**: Kho mẫu Prompts tái sử dụng (`docs/prompts/`).
* 📂 **`Verification/`**: Kết quả chạy kiểm định (`docs/verification/`).
* 📂 **`Debug/`**: Nhật ký gỡ lỗi (`docs/debug/`).
* 📂 **`Archive/`**: Lưu trữ tài liệu cũ (`docs/archive/`).
* 📂 **`Project Memory/`**: Các tệp tin tóm tắt dự án của Agent.

> [!TIP]
> Tất cả các tài liệu được đồng bộ sang Obsidian đều tự động được chuyển đổi liên kết sang dạng **`[[tên_ghi_chú]]`** (Wiki-Links), giúp Ba xem biểu đồ liên kết tri thức (Graph View) của Obsidian cực kỳ trực quan và sinh động!
