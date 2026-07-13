---
feature_id: FEAT-051
feature_name: Harden AIWF Implementation Flow and Release Gate
status: draft
stage: brainstorming
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: None
next_artifact: ../plans/FEAT-051_harden_implementation_phases_and_release_gate_plan.md
---

# Master Requirement Document – Harden AIWF Implementation Flow and Release Gate

## 1. Feature ID & Name
- **Feature ID**: FEAT-051
- **Feature Name**: Harden AIWF Implementation Flow and Release Gate

## 2. Original Idea
[Prompt: Harden AIWF Implementation Flow to Prevent Code Loss, Premature Release, and Phase Skipping. Stop premature debug/release suggestions, implement implementation-ledger.json, only recommend release after verify passes, and support partial releases with user confirmation.]

## 3. Business Problem
- **Problem**: Đề xuất `/release` hoặc `/debug` quá sớm ngay sau khi hoàn thành Phase 1 của blueprint nhiều Phase. Không có cơ chế phân biệt rõ ràng giữa hoàn thành Phase và hoàn thành toàn bộ Feature.
- **Why it matters**: Làm tăng rủi ro Agent bỏ sót code chưa phát triển ở các Phase tiếp theo, hoặc commit phát hành code chưa chạy thử nghiệm.
- **Who is affected**: Developer và AI Coder thực hiện implement các blueprint phức tạp nhiều Phase.
- **Expected outcome**: Quản lý chặt chẽ ranh giới các Phase thực thi, tiếp tục triển khai Phase N+1 cho đến khi hoàn tất 100% Phase trong blueprint rồi mới chuyển trạng thái đề xuất sang Debug ➔ Verify ➔ Release.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Triển khai tệp sổ cái `implementation-ledger.json` ghi nhận cấu trúc Phase, Task và trạng thái thực tế của từng phần.
  - FR-02: Khi kết thúc Phase N, nếu còn Phase N+1, hệ thống bắt buộc đề xuất tiếp tục chạy `/implement --phase <Phase N+1>` hoặc đưa ra menu lựa chọn (tiếp tục, debug cục bộ, pause, partial release).
  - FR-03: Nếu người dùng yêu cầu tiếp tục, tự động tìm Phase chưa hoàn thành kế tiếp trong ledger để tiếp tục thực thi.
  - FR-04: Xây dựng Release Gate kiểm tra nghiêm ngặt: toàn bộ Phase/Task hoàn thành, không có tiến trình worker chạy ngầm, đã pass debug & verify mới cho phép Release.
  - FR-05: Hỗ trợ quy trình Partial Release (phát hành một phần) khi người dùng phê duyệt rõ ràng bằng văn bản và ghi chú cụ thể.
- **Non-functional Requirements**:
  - NFR-01: **Bảo vệ mã nguồn**: Tuyệt đối không cho phép tạo commit phát hành tự động nếu các cổng kiểm tra an toàn bị từ chối.
- **Technical Constraints**:
  - TC-01: Tương thích ngược với các blueprint cũ không có cấu trúc Phase (coi toàn bộ task là 1 Phase duy nhất).

## 5. Requirement Traceability Matrix
| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | implementation-ledger.json file | Ledger | test_ledger_creation | Ledger correctly records phase/task statuses |
| FR-02 | Must | Continue next phase recommendation | Phase Boundary | test_phase_boundary_suggest | Suggest next phase when incomplete phases exist |
| FR-03 | Must | Resume next incomplete phase on request | Phase Resume | test_resume_next_phase | CLI resumes at Phase N+1 on next phase command |
| FR-04 | Must | Release gate blocks prematurely | Release Gate | test_release_blocked_premature | Release fails if incomplete phases remain |
| FR-05 | Must | Partial release approval gate | Release Gate | test_partial_release_approval | Partial release notes written on explicit approval |

## 6. Stakeholder Analysis
| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Project Owner / Ba | Primary | High | High | Code phát hành được kiểm duyệt kỹ càng, không bị mất code giữa các Phase |
| Coder Agent | Primary | High | High | Nhận đúng chỉ thị triển khai Phase tiếp theo, tránh nhảy cóc |

## 7. Scope Boundary
- **In Scope**:
  - Thiết kế và triển khai `implementation-ledger.json` và logic xử lý nó trong `workflow_runtime.py`.
  - Cập nhật logic đề xuất next skill trong State Aggregator.
  - Cập nhật Skill `/release` để kiểm tra Release Gate trước khi chạy.
- **Out of Scope**:
  - Không tự động viết code thực thi các tệp tin nghiệp vụ của user.

## 8. Dependency Graph Preview
- State Aggregator & split state structures (FEAT-050) (Must)
  └── Implementation Ledger & Phase Boundary logic (Must)
      └── Release Gate validations (Must)
          └── Skill/CLI Integration (Must)

## 9. Data Flow Preview
- Phase N completed
  └── Aggregator scans ledger ──> detects Phase N+1 incomplete
      └── sets suggested_next_skill = blueprint-to-implementation
          └── blocks release_allowed = false

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| workflow_runtime.py | `skills/workflow-runtime/scripts/workflow_runtime.py` | Extend | Quản lý logic kiểm tra release gate và cập nhật ledger |
| software-development-workflow | `skills/software-development-workflow/SKILL.md` | Refactor | Cập nhật hướng dẫn luồng di chuyển phase |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: blueprint-to-implementation, implementation-to-release.
- **Affected Docs**: Cấu trúc tệp tin thiết kế blueprint.
- **Impact Level**: High (Thay đổi luồng đi của SDLC).

## 12. Migration Strategy
- **Backward Compatibility**: Các blueprint không chia phase sẽ tự động được coi như có 1 Phase duy nhất để giữ nguyên tính tương thích.

## 13. Architecture Principles
- **Monotonic Phase Progression**: Luồng di chuyển phase chỉ đi một chiều tiến lên, không nhảy cóc hoặc đảo lộn.
- **Strict Release Gating**: Release là hành động cuối cùng sau khi đã được xác thực an toàn tuyệt đối.

## 14. Non Goals
- Không hỗ trợ tự động giải quyết xung đột code trong Git (Merge conflict resolution).

## 15. ROI Analysis
- **Estimated Implementation Cost**: Thấp - Trung bình.
- **Runtime Savings**: Loại bỏ hoàn toàn lỗi trôi lệch trạng thái làm mất thời gian sửa chữa thủ công.

## 16. Success Metrics
- **Premature Releases Blocked**: 100% các lần phát hành thử nghiệm sớm bị chặn đứng.
- **Correct Next Skill Recommendation**: 100% chuyển sang Phase kế tiếp.

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Agent bị kẹt vòng lặp vô hạn ở Phase boundary | High | Low | Cung cấp menu lựa chọn rõ ràng cho người dùng | Architect |

## 18. Technical Questions
- Menu lựa chọn khi hoàn tất Phase có nên hiển thị dưới dạng câu hỏi tương tác đa lựa chọn CLI không? (Nên, dùng interactive choice).

## 19. Open Decision Register
| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Cách hiển thị lựa chọn | Resolved | Dùng CLI choice protocol |

## 20. ADR Detection
- **ADR Required**: Yes
- **Rationale & Focus**: Cơ chế Release Gate và quản lý Phase của AIWF.

## 21. Knowledge Update Impact
- **lessons**: Yes (Ghi lại bài học chặn release sớm)
- **ADR**: Yes (Ghi nhận ADR về Release Gate)

## 22. Test Strategy Preview
- **Unit Tests**: Kiểm tra ledger ghi nhận đúng trạng thái, kiểm tra release gate chặn thành công.
- **Integration Tests**: Chạy thử luồng thực thi blueprint 3 phase giả lập.

## 23. Extension Impact
- **Extension UI Changes**: Hiển thị rõ ràng danh sách Phase và Phase hiện tại đang thực thi.

## 24. Complexity Estimation
- **Implementation Complexity**: Medium
- **Estimated Refactoring Percentage**: 20% trên luồng workflow.

## 25. Roadmap Alignment
- **Roadmap Phase**: Phase 2 of Workflow Hardening.

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| Làm sao để kích hoạt Partial Release? | Người dùng phải phê duyệt bằng cú pháp văn bản rõ ràng: "Approve partial release for Phase X". |

## 27. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 28. Existing Project Context
- Đang kế thừa cơ chế lưu vết của `.agents/state/approvals.json` để kiểm soát các mốc phê duyệt của người dùng.

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| workflow_runtime.py | `skills/workflow-runtime/scripts/workflow_runtime.py` | Runtime | do_state_action, do_init | 85% | 15% | Low | Quản lý lệnh kiểm thử |

## 30. Solution Options Evaluated

### Option A: Ledger-backed Phase Controller (Recommended)
- **Overview**: Lưu trữ trạng thái Phase và Task chi tiết trong `implementation-ledger.json`. Cập nhật trạng thái monotone.
- **Advantages**: Cực kỳ tin cậy, chống trôi lệch trạng thái hoàn toàn, hỗ trợ resume từ bất kỳ lỗi nào.
- **Disadvantages**: Cần duy trì tệp dữ liệu trạng thái phụ.

### Option B: Checkpoint-only tracking
- **Overview**: Dựa hoàn toàn vào số hiệu checkpoint (ví dụ: Checkpoint 3.1, 3.2) ghi nhận trong session để kiểm soát.
- **Advantages**: Đơn giản, không cần tệp ledger mới.
- **Disadvantages**: Không lưu trữ chi tiết tệp ghi đè (write_set) hoặc thông tin tiến trình con, rủi ro mất code chạy song song cao.

## 31. Solution Comparison Table
| Criteria | Option A (Ledger-backed) | Option B (Checkpoint-only) |
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
- **Why Selected**: Ràng buộc cứng tiến trình của Agent, bảo đảm an toàn dữ liệu đầu ra và khả năng kiểm soát chặt chẽ của người dùng trước khi phát hành.

## 33. Risks & Assumptions
- Giả định rằng toàn bộ các tệp blueprint thiết kế đều tuân thủ đúng định dạng phân phase.

## 34. Acceptance Criteria
- [ ] AC-01: `implementation-ledger.json` được ghi nhận chuẩn xác.
- [ ] AC-02: Đề xuất skill tiếp theo chuyển sang Phase kế tiếp thay vì Debug/Release nếu chưa hoàn thành 100% Phase.
- [ ] AC-03: Lệnh `/release` bị từ chối nếu chưa chạy `/verify` thành công.

## 35. Final Planning Prompt
- Hãy thiết lập cơ chế kiểm soát Phase và chốt Release Gate dựa trên implementation-ledger.json. Viết logic chuyển dịch phase tự động và xử lý tương tác lựa chọn khi hoàn tất mỗi Phase.
