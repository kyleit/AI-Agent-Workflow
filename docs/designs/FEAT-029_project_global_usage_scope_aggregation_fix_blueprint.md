<!-- File path: docs/designs/FEAT-029_project_global_usage_scope_aggregation_fix_blueprint.md -->

---
feature_id: FEAT-029
feature_name: Project/Global Usage Scope Aggregation Fix
status: reviewed
stage: blueprint
created_at: 2026-07-08
updated_at: 2026-07-08
previous_artifact: ../plans/FEAT-029_project_global_usage_scope_aggregation_fix_plan.md
next_artifact: [Implementation (Source Code)](../../)
---

# Technical Blueprint & Implementation Contract – Project/Global Usage Scope Aggregation Fix

## 0. Baseline Context & References
- **Memory Baseline**: Memory Status is FRESH. Memory Confidence is High. Memory source matches [project-summary.md](file:///e:/AgentsProject/.agents/memory/project-summary.md).
- **RAG Query Summaries**: Local keyword search matches details of SQLite databases `project_runtime.db` and `global_runtime.db`.
- **Inspected Source Files**:
  - `skills/workflow-runtime/scripts/db.py` (lines 67-138, 207-357)
  - `skills/workflow-runtime/scripts/workflow_runtime.py` (lines 100-140)
  - `skills/workflow-runtime/tests/test_runtime.py` (lines 150-206)

## 1. File-by-File Analysis & Proposed Mutations

| File Path | Operation | Responsibility | Dependency | Impact & Risk |
| :--- | :--- | :--- | :--- | :--- |
| `skills/workflow-runtime/scripts/db.py` | MODIFY | Cập nhật `get_project_summary()` để nhận và lọc theo `project_id`. | `sqlite3` | Thấp. Tách biệt hoàn toàn thống kê của các dự án khác nhau. |
| `.agents/skills/workflow-runtime/scripts/db.py` | MODIFY | Cập nhật đồng bộ với tệp trên. | `sqlite3` | Thấp. |
| `skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Truyền kết quả của `get_project_id()` vào hàm gọi `get_project_summary()`. | `get_project_id`, `get_project_summary` | Thấp. |
| `.agents/skills/workflow-runtime/scripts/workflow_runtime.py` | MODIFY | Cập nhật đồng bộ với tệp trên. | `get_project_id`, `get_project_summary` | Thấp. |
| `skills/workflow-runtime/tests/test_runtime.py` | MODIFY | Cập nhật unit test `test_sqlite_databases_and_scopes` để truyền `proj_id` vào `get_project_summary()`. | `get_project_summary` | Thấp. |
| `.agents/skills/workflow-runtime/tests/test_runtime.py` | MODIFY | Cập nhật đồng bộ với tệp trên. | `get_project_summary` | Thấp. |

## 2. Target Folder Structure
Cấu trúc thư mục của dự án sau khi thực hiện thay đổi:
```text
.
├── .agents
│   └── skills
│       └── workflow-runtime
│           ├── scripts
│           │   ├── db.py
│           │   └── workflow_runtime.py
│           └── tests
│               └── test_runtime.py
├── skills
│   └── workflow-runtime
│       ├── scripts
│       │   ├── db.py
│       │   └── workflow_runtime.py
│       └── tests
│           └── test_runtime.py
└── docs
    └── designs
        └── FEAT-029_project_global_usage_scope_aggregation_fix_blueprint.md
```

## 3. Interface Contracts (Public & Internal)
- **Internal Component Contracts**:
  - Chữ ký hàm `get_project_summary` trong `db.py` thay đổi từ:
    `def get_project_summary() -> dict:`
    thành:
    `def get_project_summary(project_id: str) -> dict:`
  - Câu lệnh SQL tổng hợp thay đổi từ:
    ```sql
    SELECT SUM(input_tokens), SUM(output_tokens), SUM(cache_tokens),
           SUM(thinking_tokens), SUM(total_tokens), SUM(estimated_cost_usd)
    FROM usage_records
    ```
    thành:
    ```sql
    SELECT SUM(input_tokens), SUM(output_tokens), SUM(cache_tokens),
           SUM(thinking_tokens), SUM(total_tokens), SUM(estimated_cost_usd)
    FROM usage_records
    WHERE project_id = ?
    ```
- **Backward Compatibility**: Hàm vẫn trả về cấu trúc dictionary tương tự với các trường `input_tokens`, `output_tokens`, `cache_tokens`, `thinking_tokens`, `total_tokens`, và `estimated_cost_usd`.

## 4. Algorithms & Logic Specifications
### 1. get_project_summary
```python
def get_project_summary(project_id: str) -> dict:
    if not os.path.exists(PROJECT_DB):
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_tokens": 0,
            "thinking_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "updated_at": datetime.now().astimezone().isoformat()
        }

    conn = None
    try:
        conn = sqlite3.connect(PROJECT_DB)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(input_tokens), SUM(output_tokens), SUM(cache_tokens),
                   SUM(thinking_tokens), SUM(total_tokens), SUM(estimated_cost_usd)
            FROM usage_records
            WHERE project_id = ?
        """, (project_id,))
        row = cursor.fetchone()
        if row and row[4] is not None:
            return {
                "input_tokens": row[0],
                "output_tokens": row[1],
                "cache_tokens": row[2],
                "thinking_tokens": row[3],
                "total_tokens": row[4],
                "estimated_cost_usd": round(row[5], 4),
                "updated_at": datetime.now().astimezone().isoformat()
            }
    except sqlite3.OperationalError:
        pass
    finally:
        if conn:
            conn.close()
    
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_tokens": 0,
        "thinking_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "updated_at": datetime.now().astimezone().isoformat()
    }
```

### 2. Dọn dẹp dữ liệu cũ (Idempotent DB Normalization)
Hàm `normalize_database_records(db_path)` sẽ được kích hoạt để tự động chuẩn hóa dữ liệu khi khởi chạy CLI. Nếu tệp transcript của cuộc hội thoại cũ tồn tại, nó sẽ phân tích lại transcript và cập nhật đúng số liệu thực tế thay vì giữ số liệu khổng lồ.

## 5. State Machine & Transitions
Không có thay đổi về máy trạng thái SDLC.

## 6. Validation and Safety Constraints
- Tránh SQL injection bằng việc sử dụng tham số hóa truy vấn `(project_id,)`.
- Khóa chính `conversation_id` ngăn ngừa trùng lặp bản ghi cho cùng một phiên làm việc.

## 7. Backward Compatibility & Migration Mapping
Tất cả các bản ghi hiện tại vẫn giữ nguyên cấu trúc schema SQLite, chỉ số lượng token khổng lồ cũ được chuẩn hóa về mức thực tế thông qua hàm quét transcript.

## 8. Implementation Checklist
- [ ] Chỉnh sửa `get_project_summary` trong cả hai tệp `db.py` (cục bộ và dưới `.agents/`).
- [ ] Cập nhật lời gọi trong `workflow_runtime.py` (cục bộ và dưới `.agents/`).
- [ ] Cập nhật unit test `test_sqlite_databases_and_scopes` trong `test_runtime.py` (cục bộ và dưới `.agents/`).
- [ ] Chạy lệnh `python -m unittest tests/test_runtime.py` để xác minh.

## 9. Acceptance Criteria & Test Mapping

| Requirement ID | Requirement Description | Expected Result | Verification Method | Unit/Integration Test Target |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-001` | Lọc theo Project ID trong Project Summary | Chỉ hiển thị các dòng thuộc project chỉ định. | Chạy unit test. | `test_runtime.py: TestRuntimeEngine.test_sqlite_databases_and_scopes` |
| `REQ-002` | Khả năng chuẩn hóa dữ liệu cũ | Đặt lại số lượng token khổng lồ cũ về đúng thực tế. | Chạy test chuẩn hóa dữ liệu. | `test_runtime.py: TestRuntimeEngine.test_accurate_token_estimation_and_database_normalization` |

## 10. Disallowed Outputs Validation
- [x] Không sử dụng `file://` hay đường dẫn tuyệt đối.
- [x] Không chứa các ký tự giữ chỗ như `...` hoặc `etc.` trong code/cấu trúc thư mục ở các phần mô tả kịch bản chính.
