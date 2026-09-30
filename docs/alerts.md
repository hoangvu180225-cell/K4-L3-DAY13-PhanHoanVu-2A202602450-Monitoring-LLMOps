# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: HighLatencyP95
- Severity: warning
- Duration: 5m
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Latency P95 của `response_sent.latency_ms` (SLO <= 3000ms)
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng phải chờ đợi lâu để nhận câu trả lời, trải nghiệm bị gián đoạn hoặc timeout.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và thời điểm bắt đầu tăng đột biến.
  2. Lọc `data/logs.jsonl` tìm `correlation_id` của các request có latency > 3000ms.
  3. Mở trace trên Langfuse qua `correlation_id` để kiểm tra xem bước `retrieval` hay `generation` bị chậm.
- Mitigation tạm thời: Rollback prompt version nếu vừa cập nhật prompt mới làm tăng token/latency, hoặc khởi động lại worker nếu nghẽn tài nguyên.
- Owner: oncall-llmops

## Alert 2

- Tên: HighErrorRate
- Severity: critical
- Duration: 5m
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `error_rate_pct` (Tỷ lệ `request_failed` / `request_received`, SLO <= 2%)
- Điều kiện và thời gian duy trì: `error_rate_pct > 2%` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận mã lỗi 500 hoặc thông báo lỗi không có câu trả lời từ AI.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors trên dashboard để xác định tỷ lệ lỗi và `error_type` phổ biến.
  2. Lọc các dòng log `request_failed` trong `data/logs.jsonl` để lấy `correlation_id` và thông báo lỗi.
  3. Tra cứu trace ID tương ứng trên Langfuse để xem exception stacktrace xảy ra ở component nào.
- Mitigation tạm thời: Bật circuit breaker hoặc fallback response nếu downstream/upstream bị lỗi, chuyển traffic sang cụm dự phòng.
- Owner: oncall-llmops

## Alert 3

- Tên: LowRetrievalSuccessRate
- Severity: critical
- Duration: 5m
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `tool_success_rate_pct` (Tỷ lệ retrieval thành công, Guardrail >= 90%)
- Điều kiện và thời gian duy trì: `tool_success_rate_pct < 90%` liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Chatbot trả lời sai ngữ cảnh, ảo giác (hallucination) hoặc trả về thông báo lỗi do không truy xuất được tài liệu RAG.
- Ba bước kiểm tra đầu tiên:
  1. Mở panel Errors kiểm tra đồ thị retrieval success rate và tỷ lệ `tool_success == false`.
  2. Lọc log có `tool_name == "retrieval"` và `tool_success == false` để kiểm tra nguyên nhân lỗi (ví dụ: vector store timeout).
  3. Kiểm tra span `retrieval` trên Langfuse trace để xác định query nào gây lỗi vector DB.
- Mitigation tạm thời: Khởi động lại dịch vụ Vector DB / Embedding service, chuyển chế độ RAG sang zero-shot fallback answer tạm thời.
- Owner: oncall-llmops

