---
feature_id: FEAT-053
feature_name: AIWF Runtime Integration and Stress Testing Suite
status: draft
stage: brainstorming
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: None
next_artifact: ../plans/FEAT-053_aiwf_runtime_integration_stress_testing_plan.md
---

# Master Requirement Document – AIWF Runtime Integration and Stress Testing Suite

## 1. Feature ID & Name
- **Feature ID**: FEAT-053
- **Feature Name**: AIWF Runtime Integration and Stress Testing Suite

## 2. Original Idea
[Prompt: AIWF Runtime Integration, Audit, and Stress Testing Suite. Implement unit, integration, stress, and failure injection testing under skills/workflow-runtime/tests/ verifying migration, event sourced reducer, lock safety, gates, and compatibility, validating 50+ mock blueprints.]

## 3. Business Problem
- **Problem**: Sau các đợt refactor cực kỳ lớn liên quan đến Split State, Event Sourcing, và Bộ điều phối an toàn (locks/workers/DAG), chúng ta cần đảm bảo hệ thống tuyệt đối ổn định và không phát sinh lỗi phá vỡ hệ thống cũ (Regressions).
- **Why it matters**: Bất kỳ lỗi nhỏ nào ở runtime cũng có thể làm gián đoạn workflow hoặc gây hỏng/drift dữ liệu trạng thái của nhà phát triển.
- **Who is affected**: Nhóm phát triển AIWF Core và QA Automation.
- **Expected outcome**: Bộ công cụ kiểm thử tích hợp tự động toàn diện, giả lập các kịch bản chịu tải lớn (stress test) và tiêm lỗi (failure injection) để chứng minh độ bền bỉ của hệ thống.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: **Test di trú trạng thái**: Kiểm tra di trú từ `.session.json` cũ và từ split state phẳng sang cấu trúc canonical mới.
  - FR-02: **Test Event Reducer & Aggregator**: Xác thực tính đúng đắn và tính đơn trị (determinism) khi replay chuỗi sự kiện.
  - FR-03: **Test Release Gates**: Kiểm tra các trường hợp chặn release sớm, chặn release khi thiếu verify/debug.
  - FR-04: **Test DAG & Lock Safety**: Giả lập tranh chấp khóa file để xác minh việc tuần tự hóa hoặc chặn luồng thành công.
  - FR-05: **Test chịu tải (Stress Test)**: Giả lập chạy tự động ít nhất 50 blueprint phức tạp ngẫu nhiên (chứa 10-30 task, nhiều phase, lỗi giả lập, lock stale, worker orphan) xem trạng thái có bị hỏng hay không.
  - FR-06: **Test tiêm lỗi (Failure Injection)**: Giả lập lỗi mất nguồn ghi file JSON dở dang, permission denied trên lock file, conflict patch.
- **Non-functional Requirements**:
  - NFR-01: **Cô lập vùng nhớ**: Tất cả các bài test phải chạy trên thư mục tạm thời (`tempfile.mkdtemp()`), không bao giờ được chạm vào hoặc ghi đè thư mục gốc của dự án thật.
  - NFR-02: **Tốc độ thực thi**: Các bài test tích hợp nhanh phải chạy dưới 30 giây để đưa lên CI. Stress test chạy opt-in riêng.

## 5. Requirement Traceability Matrix
| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Validate state migration idempotency | Migration Tests | test_state_migration_idempotent | Running migration twice produces identical files |
| FR-02 | Must | Verify event playback equivalent state | Event Playback | test_event_replay_consistency | Replaying events rebuilds exact same state |
| FR-03 | Must | Validate debug/verify/release gates | Release Gates | test_gate_blocking_conditions | Release fails under all block conditions |
| FR-04 | Must | Verify file lock safety conflicts | Lock Safety | test_lock_conflict_prevention | Lock is successfully kept and rejects overlaps |
| FR-05 | Must | Stress test with 50+ mock blueprints | Stress Suite | test_stress_scale | 50+ mock runs completed with zero JSON corruption |
| FR-06 | Must | Failure injection for atomic writes | Failure Injection | test_interrupted_json_write | Atomic writer rolls back or recovers on write fail |

## 6. Stakeholder Analysis
| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| QA Engineer | Primary | High | High | Tự động hóa kiểm thử toàn diện, phát hiện lỗi nhanh |
| Core Developer | Primary | High | High | Tự tin refactor hệ thống mà không sợ làm hỏng các skill khác |

## 7. Scope Boundary
- **In Scope**:
  - Xây dựng các tệp tin kiểm thử dưới `skills/workflow-runtime/tests/`.
  - Tạo các dữ liệu giả lập (fixtures) cho blueprint và trạng thái cũ.
  - Viết tài liệu hướng dẫn và playbook xử lý sự cố.
- **Out of Scope**:
  - Không xây dựng các pipeline CI/CD thật nếu dự án không yêu cầu, chỉ tạo các script chạy kiểm thử.

## 8. Dependency Graph Preview
- State & Orchestrator Implementation (FEAT-050, FEAT-051, FEAT-052) (Must)
  └── Mock Blueprint & State Fixtures (Must)
      └── Basic Unit & Integration Tests (Must)
          └── Failure Injection & Stress Testing Suite (Must)
              └── Documentation Playbooks (Must)

## 9. Data Flow Preview
- Stress Test Runner
  └── generates mock blueprints ──> spawns isolated workspace
      └── emits fake event streams ──> triggers aggregator & validators
          └── verifies final status = healthy & locks = empty

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| tests/ | `skills/workflow-runtime/tests/` | Extend | Bổ sung các tệp tin kiểm thử tích hợp mới |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: workflow-runtime.
- **Affected Scripts**: Toàn bộ tệp test cũ.
- **Impact Level**: Medium (Không sửa trực tiếp code hệ thống nhưng chạy quét toàn diện).

## 12. Migration Strategy
- Không áp dụng di trú cho mã nguồn, bộ test suite được phân tách rõ ràng.

## 13. Architecture Principles
- **Isolability**: Mọi bài test đều tự trị và biệt lập trong không gian tạm thời.
- **Idempotency**: Các bài test di trú hoặc hồi phục có thể chạy lặp đi lặp lại nhiều lần với cùng một kết quả.
- **Failure Resilience**: Chứng minh hệ thống sống sót và phục hồi được khi gặp sự cố phần cứng/đĩa ghi.

## 14. Non Goals
- Không chạy kiểm thử tải mạng internet thực tế.

## 15. ROI Analysis
- **Estimated Implementation Cost**: Trung bình.
- **Runtime Savings**: Tránh các đợt rollback code hoặc gián đoạn triển khai do lỗi runtime không mong muốn.

## 16. Success Metrics
- **Test Coverage**: Đạt trên 85% dòng lệnh của bộ runtime core mới.
- **Regressions Found**: 0 lỗi sót lại sau khi chạy suite test.

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Stress test chạy quá lâu làm nghẽn local test | Medium | Medium | Tách biệt các bài test nhanh và stress test bằng các cờ tùy chọn pytest | QA |

## 18. Technical Questions
- Làm sao để mô phỏng chính xác lỗi ghi đĩa nửa chừng? (Bằng cách mock hàm write của file object để quăng lỗi Exception giữa luồng).

## 19. Open Decision Register
| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Cách tiêm lỗi ghi file | Resolved | Dùng patch mock để quăng IOError |

## 20. ADR Detection
- **ADR Required**: Yes
- **Rationale & Focus**: Chiến lược kiểm thử tự động và giả lập tải trạng thái AIWF.

## 21. Knowledge Update Impact
- **lessons**: Yes (Ghi nhận cách chạy test và phát hiện lỗi)
- **indexes**: Yes (Cập nhật sơ đồ chỉ mục tệp test)

## 22. Test Strategy Preview
- **Unit Tests**: Test di trú, test reducer, test locks, test workers.
- **Integration Tests**: Chạy e2e qua CLI lệnh `workflow_runtime.py state`.
- **Stress Tests**: Chạy 50 blueprint giả lập.

## 23. Extension Impact
- Cần đảm bảo Webview Visualizer đọc đúng dữ liệu được tạo ra từ môi trường test và không bị treo giao diện.

## 24. Complexity Estimation
- **Implementation Complexity**: Medium
- **Estimated Refactoring Percentage**: Thêm mới 100% cho phần stress/failure injection.

## 25. Roadmap Alignment
- **Roadmap Phase**: Phase 4 of Workflow Hardening.

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Có cần kiểm thử trên Windows không? | Có, tệp khóa file và ghi đĩa cần được chạy thử trên cả Windows để đảm bảo tính tương thích đa nền tảng. |

## 27. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 28. Existing Project Context
- Đã có khung kiểm thử bằng Pytest hoạt động tốt trong `skills/workflow-runtime/tests/`. Chúng ta sẽ bổ sung các tệp kiểm thử mới vào thư mục này.

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| pytest suite | `skills/workflow-runtime/tests/` | QA | test_runtime.py, test_script_first.py | 90% | 10% | Low | Nền tảng chạy test |

## 30. Solution Options Evaluated

### Option A: Test Harness & Automated Stress Suite (Recommended)
- **Overview**: Cài đặt 10+ tệp test chuyên sâu bao gồm Stress Suite giả lập 50+ blueprint và Failure Injection.
- **Advantages**: Cực kỳ tin cậy, phát hiện mọi lỗi nhỏ nhất về concurrency, lock, hoặc file corruption.
- **Disadvantages**: Mất thời gian viết mã test giả lập phức tạp.

### Option B: Basic Gate Tests Only
- **Overview**: Chỉ viết test unit cơ bản cho luồng rẽ nhánh gate, không viết stress test hoặc tiêm lỗi.
- **Advantages**: Cài đặt nhanh.
- **Disadvantages**: Không thể phát hiện được các lỗi chạy song song bất định (race conditions) hoặc lỗi hệ điều hành.

## 31. Solution Comparison Table
| Criteria | Option A (Stress Harness) | Option B (Basic Tests) |
|---|---|---|
| Complexity | Medium | Low |
| Risk | Low | Medium |
| Performance | High | High |
| Maintainability | High | Medium |
| Compatibility | High | High |
| Future Scalability | High | Low |
| Development Cost | Medium | Low |

## 32. Selected Solution
- **Choice**: Option A.
- **Why Selected**: Đảm bảo chất lượng ở cấp độ sản xuất (production-grade), chứng minh độ ổn định tuyệt đối của hệ thống lõi trước khi cho phép AI Agent vận hành trên mã nguồn thật của khách hàng.

## 33. Risks & Assumptions
- Giả định rằng máy chạy test có đủ tài nguyên CPU/Memory để thực thi 50 kịch bản stress test song song.

## 34. Acceptance Criteria
- [ ] AC-01: Chạy thành công toàn bộ các tệp test tích hợp mới.
- [ ] AC-02: Hoàn tất stress test 50 blueprint giả lập không gặp lỗi hỏng trạng thái hay deadlock.
- [ ] AC-03: Cung cấp tài liệu playbook khôi phục trạng thái khi gặp sự cố.

## 35. Final Planning Prompt
- Hãy xây dựng bộ test suite tích hợp đầy đủ kiểm thử di trú, kiểm thử reducer/aggregator, kiểm thử locks/workers, kịch bản tiêm lỗi ghi đĩa, và stress test chịu tải 50 blueprint.
