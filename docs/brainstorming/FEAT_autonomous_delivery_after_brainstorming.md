<!-- docs/brainstorming/FEAT_autonomous_delivery_after_brainstorming.md -->

---
feature_id: FEAT-116
feature_name: Autonomous Delivery After Brainstorming
status: draft
stage: brainstorming
created_at: 2026-07-12
updated_at: 2026-07-12
previous_artifact: None
next_artifact: ../plans/FEAT-116_autonomous_delivery_after_brainstorming_plan.md
---

# Master Requirement Document – Autonomous Delivery After Brainstorming (FEAT-116)

## 1. Executive Summary

Tài liệu thiết kế ý tưởng này trình bày giải pháp cho phép phân phối tự động (Autonomous Delivery) toàn bộ vòng đời phát triển phần mềm (SDLC) sau giai đoạn Brainstorming mà không cần sự can thiệp thủ công của Ba tại các bước trung gian. 

Hệ thống AIWF Runtime hiện tại đòi hỏi nhiều cổng phê duyệt thủ công (Manual Approval Gates) giữa các giai đoạn (Planning -> Blueprint -> Implementation -> Verification -> Release). Điều này làm tăng độ trễ và giảm tính tự động hóa khi chạy các tác vụ dài (ví dụ: chạy qua đêm). 

Mục tiêu của tính năng này là thiết lập cơ chế **Autonomous Delivery** (Phân phối Tự động). Ba chỉ cần tham gia vào giai đoạn **Brainstorming** ban đầu. Sau khi thống nhất yêu cầu (Requirements) đạt điểm số sẵn sàng (Readiness Score) theo yêu cầu, hệ thống Resident Orchestrator sẽ tự động điều phối toàn bộ các giai đoạn từ Lập kế hoạch (Planning), Thiết kế (Blueprint), Triển khai (Implementation), Gỡ lỗi (Debug), Kiểm thử (Testing) cho đến Kiểm chứng (Verification) và Đánh giá độc lập (Independent Review) mà không ngắt quãng Ba. Ba chỉ được liên hệ trong các trường hợp đặc biệt quan trạng (Blockers, Privileged operations) và xác nhận cuối cùng (Final Review & Release).

---

## 2. Current Limitations

Hệ thống AIWF v1 hiện tại có các hạn chế sau đối với tính tự động hóa:
1. **Quá nhiều cổng phê duyệt trung gian**: Agent dừng lại yêu cầu phản hồi sau mỗi bước tạo Plan, Blueprint hoặc trước khi bắt đầu Coder. Điều này cản trở khả năng tự động hóa hoàn toàn khi thực hiện các tác vụ dài (ví dụ: chạy qua đêm).
2. **Thiếu mô hình định lượng độ sẵn sàng của yêu cầu (Requirement Readiness)**: Không có cách khoa học để biết khi nào yêu cầu đủ rõ ràng để chuyển sang tự động hóa và khi nào cần hỏi làm rõ (clarification).
3. **Subagent tương tác trực tiếp với người dùng**: Gây nhiễu thông tin khi nhiều Subagent cùng đặt câu hỏi không đồng bộ, vi phạm nguyên tắc giao tiếp qua kênh tập trung.
4. **Không hỗ trợ chạy luồng nền dài**: Khó thực hiện các tác vụ autonomous qua đêm mà không bị dừng do chờ duyệt trung gian.

---

## 3. Proposed Workflow

Resident Orchestrator sẽ điều phối luồng công việc tự động theo sơ đồ sau:

- **Brainstorming Phase**: Orchestrator nhận yêu cầu từ Ba, phân tích và tính toán điểm sẵn sàng (Requirement Readiness Score - RRS).
- **Clarification Loop (nếu RRS < 85)**: Hỏi câu hỏi làm rõ tập trung.
- **Autonomous Execution Loop (nếu RRS >= 85)**: 
  - **Planning** (Tự động chuyển đổi spec thành kế hoạch chi tiết).
  - **Blueprint** (Tự động thiết kế kiến trúc kỹ thuật).
  - **Architecture Validation** (Tự động kiểm tra tĩnh bằng các công cụ phân tích cấu trúc).
  - **Implementation** (Coder viết mã nguồn).
  - **Debug & Testing** (Tự động chạy pytest, debug lỗi biên dịch và logic).
  - **Verification & Independent Review** (Chạy visual validation và các chốt bảo vệ tự động).
- **Final Review & Release Gate**: Ba phê duyệt cuối cùng để phát hành (Release).

---

## 4. Requirement Readiness Model & Readiness Score

Hệ thống sử dụng mô hình đánh giá độ sẵn sàng của yêu cầu (Requirement Readiness Model) với công thức tính điểm (Readiness Score):

$$Readiness\ Score = (W_{scope} \times S_{scope}) + (W_{deps} \times S_{deps}) + (W_{data} \times S_{data}) + (W_{risk} \times S_{risk})$$

Trong đó:
- **Scope Clarity ($S_{scope}$ - 40%)**: Mục tiêu, phạm vi thay đổi file và các chức năng cần thiết được xác định rõ ràng.
- **Dependency Map ($S_{deps}$ - 20%)**: Xác định rõ các thư viện, module bị ảnh hưởng và giao diện API liên quan.
- **Data & State Impact ($S_{data}$ - 20%)**: Định nghĩa rõ cấu trúc dữ liệu, các thay đổi đối với tệp trạng thái hoặc cơ sở dữ liệu.
- **Risk Assessment ($S_{risk}$ - 20%)**: Xác định các nguy cơ xung đột đồng thời (concurrency), OOM hoặc ảnh hưởng bảo mật.

### Ngưỡng kích hoạt tự động (Autonomous Delivery Trigger):
- **Score >= 85/100**: Đạt chuẩn để kích hoạt tự động chạy tiếp.
- **Score < 85/100**: Kích hoạt **Clarification Strategy**.

---

## 5. Human Interaction Policy

Chính sách tương tác nhằm đảm bảo Ba chỉ bị làm phiền trong các trường hợp tối thiểu và chí mạng:

1. **Không hỏi trung gian**: Sau khi qua giai đoạn Brainstorming và đạt điểm kích hoạt, hệ thống sẽ tự động thực thi tất cả các bước tiếp theo mà không dừng lại chờ phê duyệt.
2. **Các trường hợp ngoại lệ duy nhất được phép ngắt quãng Ba**:
   - **Missing critical requirements**: Phát hiện thiếu tham số cấu hình hoặc API key bí mật mà không có mặc định khả dụng.
   - **Unrecoverable blockers**: Lỗi hệ thống, xung đột môi trường không thể tự khắc phục qua 3 lần retry sửa lỗi tự động.
   - **Out-of-scope requests**: Ba gửi thêm yêu cầu làm thay đổi lớn cấu trúc hiện tại giữa chừng.
   - **Privileged operations**: Các lệnh yêu cầu quyền Administrator/Root, truy cập mạng ngoài danh sách an toàn, hoặc thao tác tệp nhạy cảm nằm ngoài workspace.
   - **Final Review**: Báo cáo kết quả và chạy walkthrough kiểm chứng.
   - **Release approval**: Đẩy mã nguồn lên Production hoặc xuất bản gói.
3. **Subagent Isolation**: Tất cả Subagent không được phép gọi trực tiếp các tool giao tiếp hoặc đặt câu hỏi với Ba. Mọi câu hỏi phải được gửi ngược về cho Resident Orchestrator để lọc và định dạng lại trước khi gửi cho Ba.

---

## 6. Autonomous Delivery Policy

Chính sách thực thi tự động hóa bao gồm:
1. **Dynamic Agent Team Planning**: Orchestrator tự động tuyển dụng và sắp xếp các Specialist Agents (Coder, Reviewer, DBA, API Architect) dựa trên phân tích tác động (Blast Radius) của Blueprint.
2. **Parallel Execution**: Cho phép thực thi song song các nhánh độc lập trong task graph (ví dụ: triển khai backend và frontend độc lập cùng lúc), sử dụng cơ chế khóa tài nguyên (`locks.json`) để tránh xung đột.
3. **Tự sửa lỗi (Self-healing)**: Cho phép tự động lặp lại quy trình sửa lỗi tối đa 5 lần cho một tác vụ bị lỗi (pytest fail hoặc compiler error) thông qua sự kết hợp của Coder và Debugger trước khi báo cáo blocker.

---

## 7. Runtime Integration

Cơ chế điều phối tự động sẽ được tích hợp vào `session.py` và `workflow_runtime.py` thông qua các điểm:
1. **Cấu hình Session**: Bổ sung trường `"autonomous_delivery": true` vào trạng thái session để báo hiệu cho runtime bỏ qua các gate phê duyệt thủ công trung gian.
2. **Cập nhật Trạng thái**: Ghi nhận tiến trình chi tiết từng phase vào `.agents/state/context.json` để Visualizer (`webview.html`) hiển thị thanh tiến trình động tương ứng từ 0% đến 100% của toàn bộ luồng lớn.
3. **Cơ chế Circuit Breaker tự động**: Nếu vòng lặp debug vượt quá 5 lần hoặc tài nguyên (CPU/RAM) vượt quá ngưỡng an toàn (>90%), Orchestrator sẽ tự động ngắt mạch, lưu trạng thái phục hồi (`recovery.json`) và gửi thông báo khẩn cấp cho Ba.

---

## 8. Risks

| Rủi ro | Mức độ | Biện pháp giảm thiểu |
| :--- | :--- | :--- |
| **Agent đi sai hướng thiết kế** | Cao | Thực hiện kiểm tra tĩnh (Static compliance checklist) giữa Kế hoạch và Blueprint tự động trước khi triển khai code. |
| **Vòng lặp Debug vô hạn (Infinite Loop)** | Trung bình | Đặt giới hạn cứng tối đa 5 lần lặp Debug cho một lỗi. Nếu vượt quá, chuyển trạng thái blocker và thông báo cho Ba. |
| **Tràn bộ nhớ / CPU khi chạy ngầm** | Cao | Tích hợp chặt chẽ với bộ giám sát tài nguyên của TestCoordinator và hệ thống Circuit Breaker để ngắt mạch lập tức khi tài nguyên > 90%. |

---

## 9. Migration Strategy

1. **Phase 1: Shadow Mode**: Triển khai Orchestrator ghi nhận điểm số sẵn sàng (Readiness Score) và dự đoán hành động tiếp theo nhưng vẫn yêu cầu Ba click "Proceed" để kiểm chứng độ chính xác của mô hình chấm điểm.
2. **Phase 2: Opt-in Mode**: Bổ sung cờ `--autonomous` trong CLI để Ba kích hoạt thủ công cho các task xác định.
3. **Phase 3: Default Active**: Tự động kích hoạt khi điểm số spec đạt chuẩn.

---

## 10. Success Criteria

- Ba chỉ cần tương tác 2 lần: Lúc Brainstorming ban đầu và lúc Final Review/Release cuối cùng đối với 90% các tính năng nhỏ (Quick Features).
- Tỷ lệ hoàn thành tự động không lỗi đạt trên 85%.
- Không có hiện tượng rò rỉ hoặc treo tiến trình nền khi tự động chuyển giao giữa các phase.

---

## 11. Recommendation

Recommendation: READY FOR PLANNING
