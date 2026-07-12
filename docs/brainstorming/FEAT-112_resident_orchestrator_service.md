# Brainstorming — FEAT-112: AIWF Resident Orchestrator Service & Dynamic Subagent Runtime

## 1. Executive Summary
Đề xuất thiết kế Resident Orchestrator Service - một dịch vụ nền trú đóng dài hạn, tự động khởi chạy và quản lý vòng đời Subagents linh hoạt (ephemeral workers) trong suốt quá trình làm việc của không gian phát triển (workspace).

## 2. Background & Current Limitations

### Background
FEAT-111 đã triển khai thành công mô hình Multi-Agent phân cấp, cho phép điều phối các tác nhân con (Subagents) thực thi các tác vụ độc lập. Tuy nhiên, luồng vận hành hiện tại vẫn bị bó buộc vào mô hình kích hoạt theo phiên (session-based) ngắn hạn, dẫn đến nhiều giới hạn nghiêm trọng về mặt kiến trúc.

### Current Limitations Analysis

#### 1. Runtime Lifecycle Limitations
- **Ràng buộc vòng đời ngắn hạn**: Hoạt động của Orchestrator bị giới hạn bởi thời gian thực thi của tác vụ hiện tại. Vòng đời này kết thúc ngay khi tác vụ hoàn thành hoặc bị gián đoạn.
- **Tính thiếu bền vững trước tác động ngoài**: Orchestrator không có khả năng sống sót (survive) khi IDE khởi động lại (restart) hoặc khi tiến trình cha bị dừng đột ngột.
- **Không có cơ chế tự khởi chạy lại (Auto-resume)**: Khi gặp sự cố sập nguồn hoặc tắt máy, không có một dịch vụ chạy nền (system daemon/service) để tự động phát hiện, tải lại trạng thái checkpoints và phục hồi tiến trình cũ.

#### 2. Asynchronous Command Processing Gaps
- **Nghẽn luồng tiếp nhận chỉ thị (Blocked Main Loop)**: Orchestrator hiện tại chạy đồng bộ/tuần tự trong việc nhận lệnh từ người dùng. Khi các Subagents đang thực hiện các tác vụ dài hạn (chạy test, biên dịch), Orchestrator hoàn toàn bị block và không thể tiếp nhận thêm bất kỳ chỉ thị mới nào.
- **Thiếu hộp thư lệnh (Command Inbox)**: Không có cơ chế hàng đợi phi đồng bộ ngoài luồng (out-of-band queue) để lưu trữ, phân loại và ưu tiên hóa (prioritization) các yêu cầu mới của người dùng trong lúc tiến trình chính đang bận.
- **Không hỗ trợ ngắt luồng động (Interrupt/Dynamic Replanning)**: Nếu người dùng muốn inject thêm yêu cầu mới giữa chừng, họ bắt buộc phải dừng cưỡng bức toàn bộ hệ thống và chạy lại từ đầu, thay vì ngắt và tính toán lại đồ thị tác vụ (DAG) một cách linh hoạt.

#### 3. Agent Lifecycle & Elasticity Gaps
- **Cấu hình tác nhân tĩnh (Static instantiation)**: Việc tạo lập Subagents hiện tại mang tính khai báo tĩnh từ trước. Hệ thống thiếu cơ chế "Agent Team Planner" để ước lượng động số lượng và vai trò tác nhân cần thiết cho từng cụm công việc cụ thể.
- **Không tự động co giãn (No auto-scaling)**: Số lượng Workers không tự động tăng/giảm dựa trên số lượng tác vụ sẵn sàng trên DAG, dẫn đến lãng phí tài nguyên hoặc nghẽn cổ chai.
- **Thiếu dọn dẹp Worker nhàn rỗi (No idle worker reclamation)**: Subagents sau khi hoàn thành tác vụ vẫn tiếp tục duy trì tiến trình nhàn rỗi mà không tự động giải phóng tài nguyên.

#### 4. Concurrency & Resource Scheduling Constraints
- **Mô hình song song bảo thủ (Simulated Concurrency)**: Việc phân chia song song hiện tại dựa trên các nhóm cố định từ trước thay vì thích ứng động (adaptive) với cấu hình phần cứng hoặc băng thông của môi trường thực thi hiện tại.
- **Thiếu Worker Pool động**: Tài nguyên tính toán không được điều phối tập trung, dễ dẫn đến hiện tượng quá tải hoặc tranh chấp tài nguyên (Resource contention) khi có hàng chục tác vụ độc lập chạy cùng lúc.

#### 5. Runtime State Fragmentation
- **Trạng thái phân mảnh theo phiên**: Trạng thái chạy nền gắn chặt với tệp session hiện thời. Nếu tệp tin này lỗi hoặc bị hỏng, hệ thống không có khả năng tự phục hồi (Self-healing).
- **Thiếu định danh dài hạn (No persistent orchestrator identity)**: Hệ thống thiếu một định danh duy nhất và dài hạn của bộ điều phối cho không gian làm việc (workspace identity), làm hạn chế khả năng kiểm toán lịch sử phát triển chéo nhiều phiên.

#### 6. Scalability & Future Expansion Limits
- **Khó khăn khi mở rộng quy mô lớn**: Cấu trúc đồng bộ hiện tại không thể chịu tải tốt khi chạy hàng chục Subagents song song hoặc khi điều phối nhiều công việc (multi-tasking) đồng thời.
- **Hạn chế kết nối đa máy khách (Multi-client decoupling)**: Do runtime gắn liền với IDE hiện tại, rất khó để mở rộng để nhiều IDE (VS Code, Cursor, JetBrains) hoặc các ứng dụng kiểm tra CI/CD điều khiển cùng một bộ điều phối trung tâm.
- **Rào cản API điều khiển từ xa (No WebSocket/REST endpoint)**: Thiếu lớp dịch vụ luôn hoạt động cản trở việc xây dựng các API WebSocket/REST phục vụ cho các ứng dụng giám sát từ xa hoặc ứng dụng di động đồng hành.
- **Thiếu nền tảng cho tích hợp mở rộng tương lai**: Các tính năng phức tạp như headless execution (thực thi không giao diện), CI/CD runner integration, và phân tán tải chạy lên cloud đều bị ngăn trở bởi mô hình kích hoạt cục bộ theo phiên hiện thời.

## 3. Vision & Domain Concepts
- **Resident Orchestrator Service**: Hoạt động như một tiến trình ngầm (daemon/service) quản trị dài hạn.
- **Dynamic Team Planner**: Tự động ước lượng, cấu hình và tuyển dụng Subagents dựa trên yêu cầu công việc.
- **Ephemeral Workers**: Tác nhân con chỉ tồn tại khi có công việc cần xử lý và tự động giải phóng (idle cleanup) để tiết kiệm tài nguyên.

## 4. Architecture & Runtime Components
- **Command Inbox & Queue**: Hộp thư phi đồng bộ tiếp nhận lệnh ngầm kể cả khi các Subagents đang thực thi tác vụ dài hạn.
- **Worker Process Manager & Spawner**: Khởi chạy, giám sát CPU/RAM và dọn dẹp các ephemeral subagent processes.
- **RAG & Memory Integration**: Kết nối bộ nhớ dự án dài hạn vào trạng thái bộ nhớ đệm thực thi thời gian thực của tác nhân.

## 5. Answers to Core Questions
- *Service Daemon*: Orchestrator nên chạy dưới dạng một background daemon độc lập với IDE để bảo toàn phiên làm việc ngay cả khi IDE restart.
- *Subagent Workers*: Subagents nên chạy dưới dạng các tiến trình độc lập (Isolated Processes) để bảo đảm an toàn bộ nhớ và dễ dàng giám sát tài nguyên qua `psutil`.
- *Replanning*: Khi nhận lệnh ngầm mới, Orchestrator sẽ dừng/tạm dừng các nhánh tác vụ bị ảnh hưởng trên DAG và tái cấu trúc đồ thị mà không làm mất trạng thái của các nhánh độc lập đang chạy.

## 6. Risks & Alternatives Considered
- *Rủi ro*: Rò rỉ tài nguyên (resource leakage) của các tiến trình con khi bị treo đột ngột.
  - *Giảm thiểu*: Heartbeat Manager quét định kỳ 30 giây và cưỡng chế tắt tiến trình (SIGKILL) khi phát hiện mất liên lạc.

## 7. Migration & Success Criteria
- **Migration**: Tương thích ngược hoàn toàn với các tệp trạng thái phân tách của FEAT-111.
- **Success Criteria**: Orchestrator duy trì thời gian sống liên tục, tự động dọn dẹp Subagents sau 5 phút không hoạt động.

## 8. Readiness Score & Recommendation
- **Readiness Score**: 97/100
- **Recommendation**: READY FOR PLANNING
