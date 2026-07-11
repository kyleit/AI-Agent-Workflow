<!-- File path: docs/plans/FEAT-097_ast_parser_plan.md -->

---
feature_id: FEAT-097
feature_name: AST Incremental Parser Engine
status: reviewed
stage: planning
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: ../brainstorming/FEAT-097_ast_parser.md
next_artifact: ../designs/FEAT-097_ast_parser_blueprint.md
---

# FEAT-097: AST Incremental Parser Engine

## 1. Requirement Coverage Matrix
| Req ID | Phase | Task ID | Deliverable | Covered? |
| :--- | :--- | :--- | :--- | :---: |
| FR-01 | Phase 1 | Task 1.1 | Tree-sitter parser wrapper | [x] |
| FR-02 | Phase 1 | Task 1.2 | CodeDB SQLite indexing | [x] |

## 2. Task Ownership & Roles
Phân bổ người chịu trách nhiệm thực thi các tác vụ:
- **Task 1.1**: [Architect] - Xây dựng lớp phân tích cú pháp Tree-sitter Parser
- **Task 1.2**: [Coder] - Triển khai lưu trữ chỉ mục cú pháp vào CodeDB SQLite

## 3. Parallel Execution Plan
- **Sequential Tasks**: Task 1.1 -> Task 1.2
- **Parallel Tasks**: None.
- **Blocking Tasks**: Task 1.1 (blocks Task 1.2)
- **Independent Tasks**: None.
- **Recommended Execution Groups**:
  - Group 1: Task 1.1
  - Group 2: Task 1.2

## 4. File Change Plan (Implementation Boundary)
| Task ID | File Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Task 1.1 | skills/workflow-runtime/scripts/parser.py | NEW | Triển khai... |
| Task 1.2 | skills/workflow-runtime/scripts/codedb.py | NEW | Triển khai... |

## 5. Blueprint Preparation Inputs
Cung cấp định hướng cho pha Blueprint thiết kế chi tiết:
- **Interfaces / Classes / Modules**: Triển khai thiết kế chi tiết cho module ast_parser.
- **Provider Pattern details**: Định hình cấu trúc provider thay thế.
- **Data Flow / Sequence Flow**: Lên luồng dữ liệu sequence flow.

## 6. Verification Strategy & Test Mapping
- **Unit Tests**: Mapped to Task 1.1 -> `tests/test_ast_parser.py`

## 7. Exit Criteria
- **Phase 1 Exit Criteria**:
  - [ ] 100% các điều kiện đầu ra được đáp ứng.
  - [ ] Kiểm thử tự động chạy qua thành công.

## 8. Rollback Strategy
- **Phase 1 Rollback**:
  - Trigger: Lỗi biên dịch bindings Tree-sitter
  - Steps: Revert codedb.py và parser.py

## 9. Change Impact Matrix
| Task ID | Files | Modules | Runtime | Extension | Documentation | Memory | Database |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Task 1.1 | Yes | Yes | Yes | No | Yes | Yes | No |
| Task 1.2 | Yes | Yes | Yes | No | Yes | Yes | No |

## 10. Artifact Production Plan
- **Phase 1 Artifacts**: docs/designs/FEAT-097_ast_parser_blueprint.md

## 11. Token & Execution Optimization
- **Sequential execution cost**: Thấp.
- **Parallel execution opportunities**: Không có.
- **Expected token savings**: Tiết kiệm tài nguyên nhờ bộ cache của runtime.

## Recommended Next Skill
/blueprint
