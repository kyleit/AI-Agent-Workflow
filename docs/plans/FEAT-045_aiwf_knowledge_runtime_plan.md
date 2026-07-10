<!-- File path: docs/plans/FEAT-045_aiwf_knowledge_runtime_plan.md -->

---
feature_id: FEAT-045
feature_name: AIWF Knowledge Runtime
status: reviewed
stage: planning
created_at: 2026-07-09
updated_at: 2026-07-09
previous_artifact: ../brainstorming/FEAT-045_aiwf_knowledge_runtime.md
next_artifact: ../designs/FEAT-045_aiwf_knowledge_runtime_blueprint.md
---

# FEAT-045: AIWF Knowledge Runtime

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Expose Core API (`knowledge.search()`, v.v.) | [x] |
| FR-02 | Phase 1 | Task 1.2 | `BaseProvider` contract & `MarkdownProvider` | [x] |
| FR-03 | Phase 2 | Task 2.3 | Tích hợp backlinks parser & index | [x] |
| FR-04 | Phase 2 | Task 2.4 | Bộ định tuyến API Fallback Router | [x] |
| FR-05 | Phase 1 | Task 1.3 | SQLite cache database & JSON cache layer | [x] |
| FR-06 | Phase 2 | Task 2.5 | Trích xuất lessons learned & patterns | [x] |
| FR-07 | Phase 2 | Task 2.3 | Backlinks graph generator | [x] |
| FR-08 | Phase 2 | Task 2.2 | Obsidian Provider REST integration | [x] |
| FR-09 | Phase 3 | Task 3.1 | Knowledge Quality Analyzer | [x] |

## 2. Task Ownership & Roles
- **Task 1.1**: [Architect] - Định nghĩa giao diện API lõi và signature các hàm.
- **Task 1.2**: [Coder] - Triển khai `BaseProvider` và `MarkdownProvider`.
- **Task 1.3**: [Coder] - Triển khai `SQLiteProvider` và JSON Cache.
- **Task 2.1**: [Coder] - Tái cấu trúc bộ tìm kiếm RAG thành `VectorDBProvider`.
- **Task 2.2**: [Coder] - Xây dựng kết nối REST với Obsidian và đồng bộ đồ thị.
- **Task 2.3**: [Coder] - Phát triển bộ tạo và phân tích đồ thị liên kết ngược.
- **Task 2.4**: [Architect] - Xây dựng bộ định tuyến định tuyến tối ưu chi phí và fallback.
- **Task 2.5**: [Coder] - Triển khai bộ phân tích và lưu trữ bài học kinh nghiệm.
- **Task 3.1**: [Coder] - Phát triển công cụ tìm lỗi tri thức (Quality Analyzer).
- **Task 3.2**: [Coder] - Tích hợp API vào các kỹ năng Động não, Kế hoạch, Thiết kế.
- **Task 3.3**: [Documentation] - Cập nhật tệp hướng dẫn sử dụng và changelog.

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2 -> Task 1.3 -> Task 2.4
- **Parallel Tasks**: [Task 2.1, Task 2.2, Task 2.3, Task 2.5]
- **Blocking Tasks**: Task 1.1 (blocks mọi task), Task 2.4 (blocks Phase 3)
- **Independent Tasks**: Task 3.1
- **Recommended Execution Groups**:
  - Group 1: Task 1.1 (Core API Interface)
  - Group 2: Task 1.2 (Markdown Provider)
  - Group 3: Task 1.3 (SQLite Provider & Cache)
  - Group 4: Task 2.1, Task 2.2, Task 2.3, Task 2.5 (Phát triển song song các Provider/Parser)
  - Group 5: Task 2.4 (Fallback Router)
  - Group 6: Task 3.1, Task 3.2 (Quality Analyzer & Skill Integration)
  - Group 7: Task 3.3 (Documentation Update)

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation (Create/Modify/Delete/Do Not Modify) | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | `skills/knowledge-runtime/scripts/knowledge_runtime/__init__.py` | Create | Khởi tạo gói tri thức |
| Task 1.1 | `skills/knowledge-runtime/scripts/knowledge_runtime/api.py` | Create | Expose Core API |
| Task 1.2 | `skills/knowledge-runtime/scripts/knowledge_runtime/providers/base.py` | Create | Khai báo Provider contract |
| Task 1.2 | `skills/knowledge-runtime/scripts/knowledge_runtime/providers/markdown.py` | Create | Markdown Provider |
| Task 1.3 | `skills/knowledge-runtime/scripts/knowledge_runtime/providers/sqlite.py` | Create | SQLite Provider |
| Task 1.3 | `skills/knowledge-runtime/scripts/knowledge_runtime/cache.py` | Create | Cache Layer |
| Task 2.1 | `skills/knowledge-runtime/scripts/knowledge_runtime/providers/vector.py` | Create | Vector DB Provider |
| Task 2.2 | `skills/knowledge-runtime/scripts/knowledge_runtime/providers/obsidian.py` | Create | Obsidian Provider |
| Task 2.3 | `skills/knowledge-runtime/scripts/knowledge_runtime/index.py` | Create | Backlinks Indexer |
| Task 3.1 | `skills/knowledge-runtime/scripts/knowledge_runtime/analyzer.py` | Create | Quality Analyzer |
| Task 3.2 | `skills/brainstorming/SKILL.md` | Modify | Tích hợp RAG/Memory hooks v3.2 |
| Task 3.2 | `skills/brainstorming-to-plan/SKILL.md` | Modify | Tích hợp RAG/Memory hooks v3.2 |
| Task 3.2 | `skills/plan-to-blueprint/SKILL.md` | Modify | Tích hợp RAG/Memory hooks v3.2 |

## 5. Blueprint Preparation Inputs
- **Interfaces / Classes / Modules**: `BaseProvider` class, `MarkdownProvider(BaseProvider)`, `SQLiteProvider(BaseProvider)`.
- **Provider Pattern details**: Swappable storage engine, API chỉ gọi `active_provider.search()`.
- **Data Flow / Sequence Flow**: API -> Cache check -> hit? return : route to active provider -> update cache -> return.
- **Migration Strategy & Testing Architecture**: Sử dụng Adapter Class ánh xạ `memory.config.json` cũ.

## 6. Verification Strategy & Test Mapping
- **Unit Tests**: `test_api.py` (Task 1.1), `test_cache.py` (Task 1.3), `test_providers.py` (Task 1.2, 2.1, 2.2).
- **Integration Tests**: `test_integration.py` (Task 3.2).
- **Compatibility / Regression Tests**: `test_compatibility.py` (Task 1.2).

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] 100% Unit tests pass.
  - [ ] API cục bộ Markdown/SQLite hoạt động đúng, độ trễ cache hit <200ms.
- **Phase 2 Exit Criteria**:
  - [ ] Fallback Router hoạt động hoàn hảo khi tắt dịch vụ Qdrant.
- **Phase 3 Exit Criteria**:
  - [ ] Bộ công cụ trích xuất bài học và kiểm tra chất lượng hoạt động đúng.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Gặp lỗi kiểm thử hệ thống nghiêm trọng không thể khắc phục nhanh.
  - Steps: Revert git commit, delete new files under `skills/knowledge-runtime/`, restore `memory.config.json` backup.
  - Recovery: Trả về trạng thái hoạt động bình thường trên main.

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | No | No | Yes | Yes | No |
| Task 1.3 | Yes | Yes | No | No | Yes | Yes | Yes |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: docs/designs/FEAT-045_blueprint.md
- **Phase 2 Artifacts**: docs/adr/ADR-012.md, docs/releases/Release_Notes.md

## 11. Token & Execution Optimization
- **Sequential execution cost**: Cao (yêu cầu nạp toàn bộ context tệp tri thức thô trong suốt quá trình).
- **Parallel execution opportunities**: Có thể phát triển song song các Provider ở Phase 2 độc lập.
- **Expected token savings**: Tiết kiệm ~30% token context cho subagent nhờ chia nhỏ tác vụ.
- **Recommended execution strategy**: Phân chia các Task song song ở Phase 2 cho các subagent xử lý độc lập.

## Recommended Next Skill
/blueprint
