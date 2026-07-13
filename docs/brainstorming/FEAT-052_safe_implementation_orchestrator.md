---
feature_id: FEAT-052
feature_name: Safe Implementation Orchestrator (DAG, Locks, Workers, Patches)
status: draft
stage: brainstorming
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: None
next_artifact: ../plans/FEAT-052_safe_implementation_orchestrator_plan.md
---

# Master Requirement Document – Safe Implementation Orchestrator (DAG, Locks, Workers, Patches)

## 1. Feature ID & Name
- **Feature ID**: FEAT-052
- **Feature Name**: Safe Implementation Orchestrator (DAG, Locks, Workers, Patches)

## 2. Original Idea
[Prompt: Harden `/implement` and Orchestrator for Safe Task Execution Without Code Loss. Prevent code loss by building task DAG, acquiring file locks, tracking workers, and using patch-based parallel execution or sequential fallback.]

## 3. Business Problem
- **Problem**: Khi chạy song song nhiều tác vụ, các AI Agent có thể ghi đè lên các tệp tin của nhau dẫn đến mất mát mã nguồn. Đồng thời, các tiến trình con chạy ngầm mồ côi (orphan workers) có thể tiếp tục thay đổi mã nguồn sau khi orchestrator đã báo hoàn tất, gây mất tính nhất quán.
- **Why it matters**: Mất mát code là rủi ro nghiêm trọng nhất trong AI coding workflow, phá hủy niềm tin của người dùng vào hệ thống.
- **Who is affected**: Developer vận hành AIWF và các AI Agent thực hiện thay đổi mã nguồn.
- **Expected outcome**: Triển khai cơ chế điều phối an toàn tuyệt đối: tuần tự hóa mặc định, chạy song song có kiểm soát (Controlled Parallel) bằng cách sử dụng khóa tệp (File Locks), định danh tiến trình con (Worker PIDs), và kiểm tra mồ côi (Orphan Check) trước khi kết thúc.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: **Bộ dựng đồ thị DAG**: Phân tích blueprint để xây dựng đồ thị DAG, phát hiện vòng lặp và thứ tự thực thi hợp lệ.
  - FR-02: **Khóa tệp an toàn (File Locking)**: Đăng ký khóa ghi file vào `file-locks.json` trước khi thực hiện tác vụ. Ngăn chặn tác vụ khác ghi đè lên file đang bị khóa.
  - FR-03: **Theo dõi tiến trình (Worker Registry)**: Ghi nhận PID của mọi tiến trình con vào `workers.json`.
  - FR-04: **Kiểm tra tiến trình mồ côi (Orphan Checks)**: Trước khi báo hoàn tất phase, bắt buộc kiểm tra xem còn worker nào sống hay không. Dọn dẹp tiến trình mồ côi nếu có.
  - FR-05: **Ghi đè tuần tự hoặc Patch-based**: Ưu tiên tạo tệp patch cô lập (`Task_X.patch`) rồi mới áp dụng tuần tự vào workspace chính để triệt tiêu xung đột ghi file.
- **Non-functional Requirements**:
  - NFR-01: **Sequential Fallback**: Nếu không xác định rõ `write_set` hoặc phát hiện nguy cơ xung đột, tự động hạ cấp về thực thi tuần tự hoàn toàn.
- **Technical Constraints**:
  - TC-01: Khóa tệp phải sử dụng đường dẫn tương đối để đảm bảo chạy được chéo hệ điều hành (macOS, Linux, Windows).

## 5. Requirement Traceability Matrix
| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Parse blueprint DAG topologically | DAG Planner | test_dag_topological_sort | Topologically sorted execution sequence |
| FR-02 | Must | Register file locks in file-locks.json | File Locks | test_file_lock_acquisition | Lock prevents second task writing |
| FR-03 | Must | Register worker PIDs in workers.json | Workers | test_worker_registration | Active PIDs tracked in workers.json |
| FR-04 | Must | Prevent phase completion with live workers | Workers | test_completion_gate_fails_active | Fail completion if workers are still alive |
| FR-05 | Must | Apply changes sequentially/patch-based | Patch Apply | test_patch_application_conflict | Stop execution if patch application conflicts |

## 6. Stakeholder Analysis
| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| AI Agent | Primary | High | High | Không bị ghi đè thành quả lao động, code ổn định |
| Developer | Primary | High | High | Không bao giờ lo bị mất code tự động, tin tưởng vào hệ thống |

## 7. Scope Boundary
- **In Scope**:
  - Xây dựng DAG Planner, Lock Manager, Worker Manager trong `workflow_runtime.py`.
  - Viết logic dọn dẹp tiến trình và thu hồi khóa file khi gặp lỗi hoặc dừng khẩn cấp (`implement abort`, `implement resume`).
- **Out of Scope**:
  - Không thay đổi nghiệp vụ cụ thể của từng task lập trình.

## 8. Dependency Graph Preview
- State Registry & Splitting State (FEAT-050) (Must)
  └── File Locks & Worker Registry mechanisms (Must)
      └── Topolocial DAG Planner (Must)
          └── Safe Orchestrator Controller (Must)

## 9. Data Flow Preview
- Task 1.2 started
  └── checks write_set files ──> acquires locks in file-locks.json
      └── spawns shell process ──> registers PID in workers.json
          └── writes output patch ──> applies sequentially ──> releases locks

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| workflow_runtime.py | `skills/workflow-runtime/scripts/workflow_runtime.py` | Extend | Bổ sung logic điều phối, quản lý tiến trình con và khóa tệp |
| process_wrapper.py | `skills/workflow-runtime/scripts/process_wrapper.py` | Extend | Tích hợp đăng ký PID của tiến trình vào registry |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: workflow-runtime, blueprint-to-implementation.
- **Affected Core Scripts**: process_wrapper.py.
- **Impact Level**: High (Thay đổi cách khởi chạy tiến trình và áp dụng code thay đổi).

## 12. Migration Strategy
- Không ảnh hưởng đến dữ liệu cũ. Các tệp khóa và worker registry sẽ được tạo tự động khi có tiến trình chạy mới.

## 13. Architecture Principles
- **Lock-Before-Write**: Luôn giành quyền khóa ghi trước khi chạm vào tệp tin.
- **No Orphan Left Behind**: Tuyệt đối không để tiến trình con bị bỏ rơi chạy nền.
- **Safe Fallback**: Thà chạy chậm mà chắc (tuần tự) còn hơn chạy nhanh mà hỏng code (song song không kiểm soát).

## 14. Non Goals
- Không hỗ trợ chia sẻ ổ đĩa mạng phân tán.

## 15. ROI Analysis
- **Estimated Implementation Cost**: Trung bình - Cao (Đòi hỏi quản lý luồng tiến trình kỹ càng).
- **Runtime Savings**: Loại bỏ hoàn toàn chi phí debug mã nguồn bị hỏng do xung đột ghi chéo.

## 16. Success Metrics
- **Concurrent Write Overwrites**: 0 trường hợp.
- **Orphan Processes Remaining**: 0 tiến trình sau khi báo hoàn tất.

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Deadlock do tranh chấp khóa | High | Low | Sử dụng timeouts và tự động giải phóng khóa khi worker chết | Coder |

## 18. Technical Questions
- Làm sao để phát hiện PID đã chết trên các nền tảng khác nhau? (Dùng `os.kill(pid, 0)` trong Python, bắt lỗi OSError).

## 19. Open Decision Register
| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Xác thực PID sống/chết | Resolved | Sử dụng os.kill(pid, 0) cross-platform |

## 20. ADR Detection
- **ADR Required**: Yes
- **Rationale & Focus**: Cơ chế File Locking và Quản lý Tiến trình song song của AIWF.

## 21. Knowledge Update Impact
- **patterns**: Yes (Mẫu khóa file ghi đĩa an toàn)
- **lessons**: Yes (Ghi nhận bài học về orphan process)

## 22. Test Strategy Preview
- **Unit Tests**: Kiểm tra cơ chế lock/unlock, kiểm tra phát hiện cycle trong DAG.
- **Integration Tests**: Giả lập 2 tiến trình con tranh chấp khóa ghi file để xem tiến trình 2 có bị chặn thành công không.

## 23. Extension Impact
- **Extension UI Changes**: Hiển thị danh sách Lock đang giữ và danh sách Worker đang hoạt động thời gian thực.

## 24. Complexity Estimation
- **Implementation Complexity**: High
- **Estimated Refactoring Percentage**: 25% hệ thống runtime.

## 25. Roadmap Alignment
- **Roadmap Phase**: Phase 3 of Workflow Hardening.

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Có cho phép bỏ qua khóa file không? | Không, đây là cơ chế bảo vệ cốt lõi, bắt buộc đối với mọi file nằm trong write_set. |

## 27. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 28. Existing Project Context
- Đã có mã nguồn wrapper ghi log tiến trình trong `process_wrapper.py` (FEAT-047). Chúng ta sẽ tích hợp đăng ký PID vào chính wrapper này.

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| process_wrapper.py | `skills/workflow-runtime/scripts/process_wrapper.py` | Runtime | Chạy lệnh con | 70% | 30% | Medium | Ghi log và giám sát PID |

## 30. Solution Options Evaluated

### Option A: Lock & Worker Managed Sequential/Parallel Controller (Recommended)
- **Overview**: Cài đặt đồ thị DAG, tệp khóa file-locks.json, và worker registry workers.json. Hỗ trợ chạy song song cô lập.
- **Advantages**: Cực kỳ an toàn, tận dụng được thế mạnh chạy song song khi không xung đột, quản lý chặt chẽ.
- **Disadvantages**: Đòi hỏi viết thuật toán điều phối luồng và lock phức tạp.

### Option B: Strict Sequential Fallback Only
- **Overview**: Vô hiệu hóa hoàn toàn song song, ép toàn bộ task chạy tuần tự lần lượt.
- **Advantages**: Rất dễ cài đặt, không lo xung đột ghi đè.
- **Disadvantages**: Giảm hiệu năng chạy của Agent khi có nhiều tác vụ độc lập.

## 31. Solution Comparison Table
| Criteria | Option A (Managed Controller) | Option B (Sequential Only) |
|---|---|---|
| Complexity | High | Low |
| Risk | Low | Very Low |
| Performance | High (Chạy song song khi an toàn) | Medium |
| Maintainability | High | High |
| Compatibility | High | High |
| Future Scalability | High | Low |
| Development Cost | High | Low |

## 32. Selected Solution
- **Choice**: Option A.
- **Why Selected**: Đây là giải pháp toàn diện nhất, vừa đảm bảo an toàn vừa mở đường cho hiệu năng cao sau này. Bản thân nó cũng hỗ trợ tự động fallback về Option B khi phát hiện nguy hiểm.

## 33. Risks & Assumptions
- Giả định rằng hệ điều hành cho phép truy vấn trạng thái tiến trình qua PID thông qua thư viện tiêu chuẩn Python.

## 34. Acceptance Criteria
- [ ] AC-01: Đồ thị DAG được sắp xếp topologically đúng thứ tự.
- [ ] AC-02: File bị khóa bởi Task A không thể bị ghi đè bởi Task B.
- [ ] AC-03: Không có worker mồ côi nào còn sót lại khi hoàn thành phase.

## 35. Final Planning Prompt
- Hãy xây dựng bộ điều phối an toàn hỗ trợ DAG, Lock Manager và Worker Registry. Tích hợp dọn dẹp tiến trình khẩn cấp khi abort hoặc resume.
