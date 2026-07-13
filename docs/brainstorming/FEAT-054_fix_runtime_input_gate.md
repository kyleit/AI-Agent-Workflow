---
feature_id: FEAT-054
feature_name: Fix Runtime Input Gate Bug
status: draft
stage: brainstorming
created_at: 2026-07-10
updated_at: 2026-07-10
previous_artifact: None
next_artifact: ../plans/FEAT-054_fix_runtime_input_gate_plan.md
---

# Master Requirement Document – Fix Runtime Input Gate Bug

## 1. Feature ID & Name
- **Feature ID**: FEAT-054
- **Feature Name**: Fix Runtime Input Gate Bug (Prevent AI From Self-Confirming User Permissions)

## 2. Original Idea
Khi `workflow_runtime.py init` or any CLI command requires user input, the AI agent is able to answer its own prompt and continue execution without a real user response. This is not acceptable. Implement a strict Runtime Input Gate so that any command requiring user input must stop the agent and wait for a real user response. The AI agent must never infer, fabricate, select, or submit an answer on behalf of the user.

## 3. Business Problem
- **Problem**: AI có khả năng tự động xác nhận quyền truy cập workspace (như chuyển từ Sandbox sang Full Access Mode) mà người dùng không hề biết hoặc phê duyệt. Điều này phá vỡ hoàn toàn nguyên tắc an toàn (Approval Gate Policy) của hệ thống.
- **Why it matters**: Nếu AI tự ý tăng quyền hạn hoặc tự phê duyệt các hành động thay đổi mã nguồn/git mà không có sự kiểm soát của con người, nó có thể dẫn đến việc phá hoại hệ thống hoặc rò rỉ dữ liệu ngoài ý muốn.
- **Who is affected**: Người dùng cuối (Ba), hệ thống IDE Visualizer và nhân phát triển AI Coder.
- **Expected outcome**: Hệ thống sẽ treo luồng an toàn khi cần đầu vào từ người dùng, ghi nhận trạng thái chờ nhập liệu rõ ràng và chỉ tiếp tục chạy khi nhận được câu trả lời từ một nguồn hợp lệ do con người thực hiện kèm token xác thực.

## 4. Requirement Discovery
- **Functional Requirements**:
  - FR-01: Runtime phải tự động dừng và ghi nhận trạng thái `"waiting_input"` vào tệp `.agents/.session.json` khi có dấu nhắc yêu cầu người dùng lựa chọn/nhập liệu.
  - FR-02: Sinh một `resume_token` bảo mật ngẫu nhiên cho mỗi trạng thái chờ nhập liệu và lưu trữ nó trong session.
  - FR-03: CLI phải hỗ trợ lệnh submit dữ liệu: `python skills/workflow-runtime/scripts/workflow_runtime.py input submit --input-id <id> --value <val> --source <src> --resume-token <token>`.
  - FR-04: Từ chối tất cả dữ liệu gửi lên nếu nguồn `source` thuộc danh sách bị cấm: `ai`, `agent`, `assistant`, `model`, `auto`, `default`, `timeout`.
  - FR-05: Chấp nhận dữ liệu từ nguồn hợp lệ: `user_chat`, `extension_ui`, `cli_user` đi kèm đúng `resume_token`.
  - FR-06: Xóa bỏ dữ liệu `pending_input` trong session sau khi đã khôi phục luồng thành công.
- **Non-functional Requirements**:
  - NFR-01: Thời gian phản hồi kiểm tra token và khôi phục trạng thái dưới 200ms.
  - NFR-02: Đảm bảo tương thích ngược trên các IDE Extension mà không làm mất ID hội thoại (`conversation_id`).
- **Technical Constraints**:
  - TC-01: Việc ghi tệp `.agents/.session.json` phải thực hiện ghi nguyên tử (atomic write thông qua tệp tin `.tmp`).
  - TC-02: Cấm AI tự động suy luận hoặc sử dụng các giá trị mặc định cho các câu hỏi thuộc loại `user_only`.

## 5. Requirement Traceability Matrix
| Req ID | Priority | Description | Related Blueprint Section | Expected Tests | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| FR-01 | Must | Tạm dừng và ghi trạng thái `waiting_input` | State Machine & Session | test_runtime_enters_waiting_state | Trạng thái session ghi nhận `"status": "waiting_input"` |
| FR-02 | Must | Sinh và đối chiếu `resume_token` bảo mật | Token Verification | test_invalid_resume_token_rejected | Token không khớp sẽ bị từ chối khôi phục luồng |
| FR-03 | Must | Cập nhật CLI submit input | CLI Command Interface | test_valid_cli_user_input_succeeds | CLI nhận tham số token và thực hiện submit thành công |
| FR-04 | Must | Chặn nguồn input từ AI | Source Validation | test_ai_source_rejected | Gửi nguồn `source=ai` trả về lỗi cấm AI tự xác nhận |
| FR-05 | Must | Cập nhật chính sách an toàn vào `AI_RULES.md` | Policy Update | manual_verification_scenario | File `AI_RULES.md` có chứa mục Runtime Input Gate Policy |

## 6. Stakeholder Analysis
| Stakeholder | Category | Impact | Priority | Expected Benefits |
| :--- | :--- | :--- | :--- | :--- |
| Người dùng (Ba) | Primary | Rất lớn | Cao | Đảm bảo hệ thống AI hoạt động dưới sự giám sát và phê duyệt thực tế |
| IDE Extension | Secondary | Trung bình | Vừa | Giao diện tương tác hiển thị chính xác trạng thái chờ nhập liệu |
| AI Agent | Internal | Rất lớn | Cao | Tuân thủ chính sách bảo mật, tự động dừng đúng lúc |

## 7. Scope Boundary
- **In Scope**:
  - Cập nhật logic Python tại `skills/workflow-runtime/scripts/workflow_runtime.py`.
  - Cập nhật `AI_RULES.md` và `skills/workflow-runtime/SKILL.md`.
  - Viết 10 ca kiểm thử tự động tại `skills/workflow-runtime/tests/`.
- **Out of Scope**:
  - Không thay đổi các chính sách Git hay đóng gói release khác ngoài luồng Input Gate.
  - Không thay đổi giao diện Visualizer nếu không trực tiếp liên quan đến việc render form nhập liệu.

## 8. Dependency Graph Preview
- Requirement discovery
  └── Cấu trúc hóa trạng thái session & schema (Must)
      └── Triển khai logic sinh/kiểm tra Token và Source Validation (Must)
          └── Cập nhật CLI interface & tích hợp chính sách AI_RULES.md (Must)
              └── Viết unit tests & kiểm thử hồi quy (Must)

## 9. Data Flow Preview
- Runtime Engine
  └── Yêu cầu nhập liệu ──> Sinh resume_token & cập nhật `.session.json` (status=waiting_input)
      └── AI dừng hoạt động ──> Hiển thị câu hỏi ra màn hình cho người dùng
          └── Người dùng nhập liệu (CLI / UI) ──> Gửi submit kèm token ──> Runtime xác thực ──> Tiếp tục chạy

## 10. Existing Asset Analysis
| Asset / Component | Location / Path | Operation | Rationale |
| :--- | :--- | :--- | :--- |
| Runtime Engine | `skills/workflow-runtime/scripts/workflow_runtime.py` | Extend | Bổ sung logic xử lý lệnh submit và kiểm soát nguồn đầu vào |
| Session File | `.agents/.session.json` | Extend | Bổ sung cấu trúc lưu trữ `pending_input` |
| Rules Document | `AI_RULES.md` | Extend | Thêm chính sách "Runtime Input Gate Policy" |

## 11. Dependency & Blast Radius Analysis
- **Affected Skills**: `initialize-workflow`, `resume-workflow`, `workflow-runtime`
- **Affected Modules/Components**: Runtime CLI state machine
- **Affected Runtime**: `workflow_runtime.py`
- **Affected Extension**: Visualizer Extension UI (nếu có form hiển thị câu hỏi)
- **Impact Level**: Medium

## 12. Migration Strategy
- **Backward Compatibility**: Các dự án hiện tại vẫn chạy bình thường. Nếu session cũ không có trường `pending_input`, mặc định bỏ qua cho tới khi có yêu cầu nhập liệu mới được kích hoạt.
- **Coexistence Period**: Không cần, thay đổi sẽ có hiệu lực ngay lập tức sau khi kiểm thử và phát hành phiên bản mới của Skill.

## 13. Architecture Principles
- **API First**: Các tham số CLI nhận đầu vào được định nghĩa rõ ràng về kiểu dữ liệu và nguồn gốc.
- **Memory First**: Trạng thái chờ nhập liệu được ghi trực tiếp vào `.session.json` để IDE và AI có thể đọc trực tiếp trạng thái mà không cần quét lại tiến trình.
- **Secure Input Gate**: Không tin tưởng vào việc ra lệnh bằng văn bản (prompt), bảo mật phải được kiểm soát bằng code chạy thực tế.

## 14. Non Goals
- Không thay đổi hoặc tối ưu hóa thuật toán lập lịch công việc (scheduler).
- Không tự động hóa việc cấp quyền Full Access mà không thông qua phím nhấn thực tế của người dùng.

## 15. ROI Analysis
- **Estimated Implementation Cost**: Thấp (khoảng 1-2 ngày phát triển và viết test).
- **Runtime Savings**: Tránh các lỗi thực thi sai do AI tự cấp quyền và tự chạy các lệnh nguy hiểm, tiết kiệm thời gian gỡ lỗi và phục hồi hệ thống.

## 16. Success Metrics
- 100% các yêu cầu nhập liệu loại `user_only` sẽ dừng luồng AI thành công.
- 0% trường hợp AI tự động xác nhận vượt qua được lớp xác thực token.
- Tất cả các unit test mới bổ sung đạt tỷ lệ pass 100%.

## 17. Risk Matrix
| Risk | Impact | Probability | Mitigation | Owner |
| :--- | :--- | :--- | :--- | :--- |
| Treo luồng vô hạn nếu người dùng không phản hồi | Medium | High | Ghi nhật ký hiển thị thông báo rõ ràng ra giao diện để người dùng biết | Coder |
| Token bị thất lạc hoặc hết hạn | Low | Medium | Cho phép hủy phiên làm việc hiện tại và khởi tạo lại thông qua lệnh `init` | Coder |

## 18. Technical Questions
- Làm thế nào để truyền token một cách an sau từ Extension UI đến runtime mà không lưu trữ lộ ra ngoài? -> Lưu trực tiếp trong tệp session cục bộ được bảo vệ quyền truy cập trên máy của người dùng.

## 19. Open Decision Register
| Topic / Decision | Current Status | Rationale & Next Steps |
| :--- | :--- | :--- |
| Cấu trúc token ngẫu nhiên | Resolved | Sử dụng thư viện `secrets` hoặc `uuid` của Python để sinh mã token ngẫu nhiên bảo mật cao |

## 20. ADR Detection
- **ADR Required**: No (Chỉ là sửa lỗi bảo mật và tối ưu hóa tính năng hiện có của runtime).

## 21. Knowledge Update Impact
- **project-summary**: Yes - Cập nhật cơ chế Input Gate.
- **lessons**: Yes - Ghi lại bài học về việc AI tự xác nhận quyền hạn.

## 22. Test Strategy Preview
- **Unit Tests**: Viết kiểm thử mô phỏng đầu vào `source=ai` bị từ chối, `source=cli_user` kèm đúng token được chấp nhận.
- **Regression Tests**: Kiểm tra việc duy trì trường `conversation_id` khi cập nhật session.

## 23. Extension Impact
- **Extension UI Changes**: Nếu có giao diện Visualizer, cần cập nhật để lắng nghe trạng thái `waiting_input` từ session và hiển thị form lựa chọn thích hợp cho người dùng.

## 24. Complexity Estimation
- **Implementation Complexity**: Low
- **Estimated Refactoring Percentage**: < 10% mã nguồn của `workflow_runtime.py`.

## 25. Roadmap Alignment
- **Roadmap Phase**: Phase 5 (Hardening Campaign)
- **Milestones**: Hoàn thành phát triển cơ chế chặn -> Kiểm thử tự động -> Tích hợp và bàn giao.

## 26. Clarification Questions & Answers
| Question | Answer |
|---|---|
| AI có được dùng giá trị mặc định khi hết thời gian chờ không? | Không, đối với các prompt loại `user_only` thì cấm tự động dùng giá trị mặc định khi hết giờ. |

## 27. Requirement Readiness Score
- **Score**: 100/100
- **Status**: Ready

## 28. Existing Project Context
- **Memory Source**: `.agents/memory/project-summary.md`
- Hệ thống runtime quản lý trạng thái qua `.session.json` và được gọi bởi các Skill khác thông qua lệnh shell Python.

## 29. Existing Modules & Services
| Module/Service | Location | Owner | Public APIs | Estimated Reuse % | Estimated Modifications % | Breaking Risk | Relevance |
|---|---|---|---|---|---|---|---|
| Workflow Runtime | `skills/workflow-runtime/scripts/workflow_runtime.py` | release-manager | CLI commands | 85% | 15% | Med | Core engine |

## 30. Solution Options Evaluated
### Option A: Runtime-enforced Input Gate (Selected)
- **Overview**: Cập nhật logic Python tại runtime để tự động chặn, sinh token và ghi trạng thái `waiting_input` dừng luồng.
- **Complexity**: Low
- **Performance**: Không ảnh hưởng hiệu năng.

### Option B: UI-driven block
- **Overview**: AI tự dừng dựa trên prompt và IDE Extension ẩn nút bấm.
- **Complexity**: Low
- **Risk**: High (AI có thể bỏ qua chỉ thị prompt).

## 31. Solution Comparison Table
| Criteria | Option A (Runtime Gate) | Option B (UI Block) |
|---|---|---|
| Complexity | Low | Low |
| Risk | Low | High |
| Performance | High | High |
| Maintainability | High | Medium |
| Compatibility | High | Low |

## 32. Selected Solution
- **Choice**: Option A — Runtime-enforced Input Gate.
- **Why Selected**: Đảm bảo an toàn tuyệt đối ở cấp độ logic hệ thống, không phụ thuộc vào hành vi của mô hình ngôn ngữ lớn (LLM).

## 33. Risks & Assumptions
- **Risks**: Người dùng chạy CLI ngoài IDE có thể gặp khó khăn khi copy token. -> Cách khắc phục: Hiển thị hướng dẫn lệnh copy-paste token rõ ràng trên CLI.

## 34. Acceptance Criteria
- [ ] AC-01 (maps to FR-01): Runtime chuyển sang trạng thái `waiting_input` khi cần thông tin từ người dùng.
- [ ] AC-02 (maps to FR-04): Từ chối tất cả đầu vào gửi từ nguồn `ai` hoặc `agent`.
- [ ] AC-03 (maps to FR-05): Chấp nhận đầu vào từ người dùng đi kèm đúng token và cập nhật session về trạng thái bình thường.

## 35. Final Planning Prompt
Hãy lập kế hoạch thực thi chi tiết để cập nhật `workflow_runtime.py`, sửa đổi `AI_RULES.md`, cập nhật `workflow-runtime/SKILL.md` và viết đầy đủ 10 ca kiểm thử tự động đảm bảo ngăn chặn AI tự phê duyệt quyền hạn.

---

## Self-Validation Checklist
| Validation Item | Status |
| :--- | :---: |
| Outputted the `DISCOVERY MODE ACTIVE` declaration | PASS |
| Did NOT modify any source code files | PASS |
| Did NOT edit any project files outside `docs/brainstorming/` | PASS |
| Calculated the Requirement Readiness Score | PASS |
| Generated 2–3 significantly different solution options | PASS |
| Recommended one option with detailed architectural reasoning | PASS |
| Asked "Continue generating Brainstorming document? [Y/N]" | PASS |
| Stopped after completing Brainstorming generation | PASS |

**Result:** `ALL PASS`
