---
feature_id: FEAT-050
feature_name: Refactor AIWF Runtime State from session.json to Split State + Event-Sourced Aggregator
status: draft
stage: brainstorming
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: None
next_artifact: ../plans/FEAT-050_refactor_aiwf_runtime_state_split_state_event_aggregator_plan.md
---

# Master Requirement Document – Refactor AIWF Runtime State from session.json to Split State + Event-Sourced Aggregator

## 1. Feature ID & Name
- **Feature ID**: FEAT-050
- **Feature Name**: Refactor AIWF Runtime State from session.json to Split State + Event-Sourced Aggregator

## 2. Original Idea
[Prompt: Refactor AIWF Runtime State from `.session.json` to Split State + Event-Sourced Aggregator. Target is to deprecate `.session.json` as source of truth and make `.agents/state/` the canonical root using nested folders, event-sourcing events.jsonl, and a State Aggregator to write dashboard.json]

## 3. Business Problem
- **Problem**: Trạng thái hệ thống đang phân mảnh, một số Skill đọc ghi trực tiếp `.session.json`, một số khác viết vào các tệp phân mảnh trong `.agents/state/` dẫn đến sai lệch trạng thái (State Divergence). Khiến Agent đề xuất sai Skill tiếp theo (ví dụ: khuyên Release trong khi Implementation chưa xong).
- **Why it matters**: Làm suy giảm độ tin cậy của AI Engineering Workflow, tăng khả năng Agent nhảy bước nhảy phase sai lệch, làm hỏng hoặc mất code của người dùng.
- **Who is affected**: Developer sử dụng AIWF, AI Agents thực thi workflow, và hệ thống Visualizer Extension hiển thị dashboard.
- **Expected outcome**: Nhất quán hóa nguồn trạng thái canonical duy nhất tại `.agents/state/`, hỗ trợ lưu vết sự kiện qua Event Sourcing và cung cấp Aggregator tự động tạo snapshot tương thích ngược.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Định nghĩa cấu trúc thư mục con chuẩn hóa tại `.agents/state/` (`project/`, `workflow/`, `runtime/`, `context/`, `recovery/`, `events/`).
  - FR-02: Triển khai luồng ghi log sự kiện append-only vào `.agents/state/events/events.jsonl` khi có thay đổi trạng thái.
  - FR-03: Xây dựng bộ reducer xử lý các sự kiện lõi (như `WorkflowInitialized`, `SkillStarted`, `SkillCompleted`) để cập nhật các tệp trạng thái con.
  - FR-04: Triển khai State Aggregator đọc trạng thái canonical để tạo ra `dashboard.json` phục vụ Visualizer Extension.
  - FR-05: Đóng gói snapshot `.session.json` tự động với đánh dấu `@deprecated` để đảm bảo tương thích ngược với các skill cũ.
- **Non-functional Requirements**:
  - NFR-01: **Tính nguyên tử (Atomicity)**: Mọi thao tác ghi tệp JSON phải là atomic (ghi ra tệp `.tmp` rồi đổi tên) để tránh hỏng dữ liệu khi mất điện hoặc dừng đột ngột.
  - NFR-02: **Độ trễ thấp**: Thao tác ghi event và chạy reducer phải diễn ra dưới 50ms để không ảnh hưởng đến tốc độ chung của Agent.
- **Technical Constraints**:
  - TC-01: Không được xóa bỏ đột ngột tệp `.session.json` cũ để tránh bẻ gãy các trình đọc cũ chưa nâng cấp. Hỗ trợ cờ cấu hình `state.generate_legacy_session_json`.

## 5. Requirement Traceability Matrix
| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Nested canonical state directory layout | Directory Layout | test_directory_structure | Folder structure created under `.agents/state/` |
| FR-02 | Must | Append-only event log events.jsonl | Event Sourcing | test_event_appender | Valid events written to events.jsonl |
| FR-03 | Must | Reducer for core events | Event Reducer | test_reducer_processing | Events successfully update sub-state JSON files |
| FR-04 | Must | Aggregator builds dashboard.json | Aggregator | test_dashboard_aggregation | dashboard.json contains computed next skill |
| FR-05 | Must | Backward compatibility session.json | Compatibility | test_legacy_snapshot | session.json marked deprecated is written |
| NFR-01| Must | Atomic JSON writes (temp+rename) | Write Reliability | test_atomic_write_fail_recovery | No corrupted JSON left on disk on write interruption |

## 6. Stakeholder Analysis
| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Developer | Primary | High | High | Workflow ổn định, giao diện hiển thị trạng thái chính xác |
| AI Agent | Primary | High | High | Quyết định Skill tiếp theo chuẩn xác theo đúng trạng thái thực tế |
| Visualizer Extension | Secondary | Medium | High | Đọc thông tin dashboard thống nhất từ dashboard.json |

## 7. Scope Boundary
- **In Scope**:
  - Thiết kế cấu trúc thư mục con và tệp trạng thái mới.
  - Viết bộ Event Logger, Reducer và State Aggregator trong `workflow_runtime.py` và `session.py`.
  - Nâng cấp các CLI command: `state migrate`, `state aggregate`, `state validate`, `state emit`, `state doctor`, `state snapshot`, `state recover`.
  - Cập nhật tất cả các Skill hiện tại để sử dụng CLI commands thay vị trực tiếp ghi đè `.session.json`.
- **Out of Scope**:
  - Không thay đổi hành vi nghiệp vụ của các Skill khác ngoài việc thay đổi cách đọc ghi trạng thái.

## 8. Dependency Graph Preview
- State Path Resolver & Atomic Writer (Must)
  └── Event Logger & Reducers (Must)
      └── State Aggregator & CLI command implementations (Must)
          └── Skill/Script Migrations (Must)
              └── Visualizer Extension read target update (Should)

## 9. Data Flow Preview
- Event Emitted (e.g. SkillStarted)
  └── appended to ──> events.jsonl
      └── processed by Reducer ──> updates project/workflow/runtime/*.json
          └── read by Aggregator ──> generates dashboard.json & .session.json
              └── read by ──> Visualizer UI & AI Skills

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| db.py | `skills/workflow-runtime/scripts/db.py` | Extend | Bổ sung lưu trữ thông tin log process và token diff |
| session.py | `skills/workflow-runtime/scripts/session.py` | Refactor | Chuyển sang đọc trạng thái canonical và tạo snapshot |
| workflow_runtime.py | `skills/workflow-runtime/scripts/workflow_runtime.py` | Extend | Bổ sung các CLI command `state` mới |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: workflow-runtime, initialize-workflow, software-development-workflow, blueprint-to-implementation, v.v.
- **Affected Modules/Components**: Visualizer Extension, CLI Runtime.
- **Impact Level**: High (Đây là thay đổi nền tảng về kiến trúc quản lý trạng thái).

## 12. Migration Strategy
- **Backward Compatibility**: snapshot `.session.json` vẫn được sinh ra nhưng chứa metadata chỉ thị đây là tệp tin tự động sinh ra và đã bị phản đối (`_deprecated: true`).
- **Adapter Strategy**: Khi các skill hoặc Visualizer cố gắng đọc `.session.json`, họ sẽ nhận được cảnh báo hoặc tự động fallback sang dashboard.json.

## 13. Architecture Principles
- **State Canonicalization**: Trạng thái phân mảnh là nguồn sự thật duy nhất.
- **Event Sourcing (Audit Trail)**: Mọi thay đổi đều bắt nguồn từ một sự kiện được lưu vết.
- **Atomic Writes**: Không bao giờ ghi trực tiếp lên tệp đang có, luôn dùng tệp tạm để tránh hỏng dữ liệu.

## 14. Non Goals
- Không tích hợp cơ sở dữ liệu phân tán phức tạp ngoài SQLite và tệp JSON phẳng.

## 15. ROI Analysis
- **Estimated Implementation Cost**: Trung bình (Thay đổi phần lõi runtime).
- **Runtime Savings**: Tránh lãng phí Token do Agent chạy sai hoặc lặp lại Skill.
- **Expected Break-Even**: Ngay lập tức sau khi giảm thiểu được các bug trôi trạng thái.

## 16. Success Metrics
- **State Validation Errors**: 0 lỗi được phát hiện bởi `state validate`.
- **Latency of Aggregation**: < 100ms.

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Lỗi ghi file đồng thời trên Windows | High | Medium | Sử dụng cơ chế khóa file và thử lại tự động | Coder |
| Extension cũ không đọc được trạng thái | Medium | Low | Duy trì snapshot tương thích ngược | Architect |

## 18. Technical Questions
- Liệu có nên nén (compact) tệp tin events.jsonl khi số lượng dòng vượt quá một ngưỡng nhất định (ví dụ: 1000 dòng) không?

## 19. Open Decision Register
| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Cơ chế nén sự kiện | Pending | Sẽ nghiên cứu thêm trong Phase 4 |

## 20. ADR Detection
- **ADR Required**: Yes
- **Rationale & Focus**: Ghi nhận cấu trúc Split State và Event Sourcing của AIWF Runtime.

## 21. Knowledge Update Impact
- **project-summary**: Yes (Mô tả cấu trúc tệp trạng thái mới)
- **architecture**: Yes (Mô tả cơ chế event sourcing & aggregation)

## 22. Test Strategy Preview
- **Unit Tests**: Kiểm tra chuyển đổi trạng thái của reducer, kiểm tra ghi atomic.
- **Integration Tests**: Mô phỏng sự kiện chạy workflow và xác thực dashboard.json đầu ra.

## 23. Extension Impact
- **Extension UI Changes**: Cập nhật tệp hiển thị để ưu tiên đọc từ dashboard.json.

## 24. Complexity Estimation
- **Implementation Complexity**: Medium
- **Estimated Refactoring Percentage**: 35% trên phần session/state hiện tại.

## 25. Roadmap Alignment
- **Roadmap Phase**: Phase 1 of Workflow Hardening.

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Có cần duy trì .session.json vĩnh viễn không? | Chỉ duy trì dạng snapshot tương thích ngược cho đến khi toàn bộ Skill và Extension được di trú hoàn toàn. |

## 27. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 28. Existing Project Context
- Đã có nền tảng phân rã tệp trạng thái sơ khởi tại `.agents/state/*.json`. FEAT-050 sẽ tổ chức lại thành thư mục lồng nhau và tích hợp cơ chế event sourcing.

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| session.py | `skills/workflow-runtime/scripts/session.py` | Runtime | load_session, save_session_atomic | 50% | 50% | Medium | Nạp và ghi trạng thái |
| workflow_runtime.py | `skills/workflow-runtime/scripts/workflow_runtime.py` | Runtime | do_init, do_state_action | 80% | 20% | Low | Tích hợp lệnh CLI |

## 30. Solution Options Evaluated

### Option A: Reducer-driven Nested Folders (Recommended)
- **Overview**: Cập nhật thông qua cơ chế Event Sourcing. Emitting Event ➔ Reducer cập nhật tệp phân mảnh ➔ Aggregator tổng hợp `dashboard.json`.
- **Advantages**: Rất sạch, có lịch sử vết (Audit trail), dễ dàng khôi phục trạng thái cũ.
- **Disadvantages**: Đòi hỏi viết thêm code quản lý event và reducer.

### Option B: Direct Split Writing (No Events)
- **Overview**: Tách nhỏ tệp tin và các skill tự cập nhật file con tương ứng trực tiếp.
- **Advantages**: Cài đặt nhanh, đơn giản.
- **Disadvantages**: Không có lịch sử thay đổi, dễ mất đồng bộ chéo giữa các tệp tin nếu một skill ghi lỗi nửa chừng.

## 31. Solution Comparison Table
| Criteria | Option A (Event-sourced) | Option B (Direct Write) |
|---|---|---|
| Complexity | Medium | Low |
| Risk | Low | Medium |
| Performance | High (Ghi nhanh) | High |
| Maintainability | High | Medium |
| Compatibility | High | High |
| Future Scalability | High | Low |
| Development Cost | Medium | Low |

## 32. Selected Solution
- **Choice**: Option A.
- **Why Selected**: Đảm bảo an toàn giao dịch trạng thái cao nhất, tạo ra audit trail hữu dụng cho việc khôi phục lỗi và nâng cấp tính năng chạy song song sau này.

## 33. Risks & Assumptions
- **Risks**: Trục trặc đồng bộ file trên HĐH Windows do cơ chế khóa tệp tin. (Sẽ xử lý bằng retry backoff).

## 34. Acceptance Criteria
- [ ] AC-01: Thư mục `.agents/state/` chứa các thư mục con có cấu trúc nested chuẩn.
- [ ] AC-02: Tệp tin `events.jsonl` được ghi nhận đầy đủ sau mỗi thao tác cập nhật CLI.
- [ ] AC-03: `dashboard.json` và `.session.json` (deprecated snapshot) được sinh ra chính xác.

## 35. Final Planning Prompt
- Hãy chuẩn bị kế hoạch di trú trạng thái từ `.session.json` sang Split State lồng nhau và tích hợp Event Sourcing. Cài đặt các API reducer và bộ aggregator, đồng thời kiểm thử việc tạo snapshot tương thích ngược.
