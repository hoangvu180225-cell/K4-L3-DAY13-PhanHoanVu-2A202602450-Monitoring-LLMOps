# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Phan Hoàn Vũ
- **MSSV:** 2A202602450
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/hoangvu180225-cell/K4-L3-DAY13-PhanHoanVu-2A202602450-Monitoring-LLMOps
- **Commit SHA cuối:** 800c406
- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602450`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08a-trace-metadata.png` |
| Generation span | `evidence/08b-generation.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt promote | `evidence/10a-prompt-promote.png` |
| Prompt rollback | `evidence/10b-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Đạt toàn bộ 4 tiêu chí: JSON Schema, Correlation ID, Log Enrichment, PII Scrubbing |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Đầy đủ và hợp lệ cả 6 panel theo chuẩn hợp đồng dashboard.yaml |
| `pytest` | 22 passed | 24 passed | Pass 100% toàn bộ unit tests, đã bổ sung test CCCD và Credit Card |
| Số traces hợp lệ | 0 | 25+ | Có đầy đủ cây phân cấp: lab-agent-run -> retrieval, generation |
| Số PII leak | 0 | 0 | Khử sạch PII (Email, SĐT, CCCD, Thẻ ngân hàng) khỏi log và trace |
| Latency P95 / TTFT P95 | 2,118ms / 50ms | 1,917ms / 51ms | Đạt mục tiêu SLO (P95 <= 3000ms ở trạng thái vận hành bình thường) |
| Retrieval success rate | 100% | 100% | Đạt Guardrail >= 90% |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
  Trong `app/middleware.py`, `CorrelationIdMiddleware` tiếp nhận header `x-request-id` từ client nếu có; nếu không có hoặc rỗng thì tự động sinh mới với định dạng `req-<8-hex>` thông qua `uuid.uuid4().hex[:8]`. Để ngăn ngừa tình trạng rò rỉ biến ngữ cảnh giữa các async task trong ASGI event loop, middleware thực hiện `clear_contextvars()` trước, sau đó gán `bind_contextvars(correlation_id=correlation_id)` và lưu vào `request.state.correlation_id`. Cuối cùng, `correlation_id` và thời gian xử lý `x-response-time-ms` được đính kèm vào response headers trả về cho client.
- **Các metadata được ghi vào structured log:**
  Các trường toàn cục và request context gồm: `ts` (ISO UTC), `level`, `service`, `event`, `correlation_id`, `env`, `user_id_hash`, `session_id`, `feature`, `model`. Khi hoàn thành request, log bổ sung: `latency_ms`, `ttft_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success` và `payload.answer_preview`.
- **Cách bảo đảm PII được scrub trước khi ghi:**
  Trong `app/logging_config.py`, một processor chuyên trách `scrub_event` được xây dựng để duyệt đệ quy qua toàn bộ các giá trị chuỗi trong `payload`, `event` và các trường con. Dữ liệu được so khớp với các mẫu regex trong `app/pii.py` (Email, SĐT Việt Nam, CCCD 12 số, Thẻ thanh toán 16 số, Hộ chiếu) và thay thế thành `[REDACTED_<TYPE>]`. Processor này được đăng ký trong pipeline của `structlog` ngay trước `JsonlFileProcessor` và `JSONRenderer`, bảo đảm không có dữ liệu nhạy cảm thô nào bị lọt xuống đĩa cứng hoặc stream ra console.
- **Cách kiểm chứng kết quả:**
  Chạy `python scripts/validate_logs.py` đạt 100/100; gửi request chứa PII mẫu qua endpoint `/chat` và xác nhận log chỉ ghi nhận các token `[REDACTED_...]`; chạy `pytest tests/test_pii.py` pass 100%.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
  Ứng dụng được cấu hình API keys riêng kết nối trực tiếp đến project `day13-k4-l3b-2A202602450` trên Langfuse Cloud. Trên giao diện web của Langfuse, tên project hiển thị rõ ràng cùng các trace `day13-agent-request` có timestamp trùng khớp với thời điểm thực thi.
- **Cấu trúc root/retrieval/generation observations:**
  Trace gốc có observation cha là `lab-agent-run` (as_type: `agent`). Bên trong gồm 2 child observations được tạo qua `start_as_current_observation`:
  - `retrieval` (as_type: `retriever`): đo thời gian truy xuất tài liệu và ghi nhận số lượng docs.
  - `generation` (as_type: `generation`): ghi nhận model `claude-sonnet-4-5`, liên kết prompt `day13-chat`, token usage chi tiết (input/output) và chi phí ước tính `cost_usd`.
- **Cách nối trace với log:**
  Trường `correlation_id` được truyền từ middleware vào `agent.run()` và ghi thẳng vào metadata của trace Langfuse thông qua `propagate_attributes`. Khi có một `correlation_id` trong log, ta chỉ cần tìm kiếm mã đó trong Langfuse là ra ngay trace tương ứng 1-1.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** Version 1, gán nhãn `baseline` và `production`.
- **Version/label candidate:** Version 2, gán nhãn `candidate` và `latest`.
- **Trace ID của mỗi version:**
  - Trace dùng Prompt Version 1: `689b73174a6b21509ec9737256443483`
  - Trace dùng Prompt Version 2: `1a025ce1d1a87fcddf8324abf4e20964`
- **Cách promote và rollback `production`:**
  Ứng dụng truy xuất prompt động từ Langfuse theo nhãn `production`. Khi cần promote, chuyển nhãn `production` trỏ vào Version 2. Nếu phát hiện version mới gây tăng đột biến latency hoặc chi phí, ta thực hiện rollback tức thời bằng cách gán nhãn `production` quay lại Version 1 trên giao diện Langfuse mà không cần sửa code hay redeploy API.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
  Dashboard thời gian thực được dựng theo đúng chuẩn `config/dashboard.yaml` tại endpoint `/dashboard` gồm 6 panels:
  1. *Latency percentiles and TTFT*: P50, P95, P99 và TTFT P95 (đơn vị: ms, threshold P95 <= 3000ms).
  2. *Request traffic*: Tổng số request và rate/phút (đơn vị: req/min, threshold >= 1).
  3. *Error rate and retrieval success*: Tỷ lệ lỗi % (threshold <= 2%) và tỷ lệ retrieval thành công (threshold >= 90%).
  4. *Cost over time*: Chi phí tích lũy theo phút và tổng chi phí (đơn vị: USD, threshold <= $2.50).
  5. *Input and output tokens*: Thống kê tokens_in, tokens_out và tổng tokens (threshold <= 50,000 tokens).
  6. *Quality proxy*: Điểm chất lượng trung bình theo heuristic (đơn vị: 0 - 1.0, threshold >= 0.75).
- **SLO và lý do chọn:**
  SLO chính: 99.5% requests thành công và có `latency_ms <= 3000ms` trong cửa sổ trượt 28 ngày. Ngưỡng 3000ms được chọn vì đây là giới hạn tối đa người dùng chấp nhận được trong trải nghiệm tương tác với AI Agent trước khi cảm thấy hệ thống bị treo.
- **Cách tính error budget:**
  Với SLO 99.5%, error budget cho phép là $100\% - 99.5\% = 0.5\%$. Ví dụ trong một chu kỳ hệ thống tiếp nhận 10,000 requests, tối đa 50 requests được phép có độ trễ > 3000ms hoặc gặp lỗi 5xx. Khi số request xấu vượt quá 50, error budget bị cạn kiệt (burn rate cao), kích hoạt quy trình đóng băng release và tập trung sửa lỗi độ ổn định.
- **Ba alert và runbook tương ứng:**
  1. `HighLatencyP95` (Warning, 5m): Kích hoạt khi `p95(latency_ms) > 3000ms` liên tục 5 phút. Runbook: Kiểm tra panel latency, lọc log tìm correlation_id chậm, soi trace waterfall xác định retrieval hay LLM bị chậm, rollback prompt nếu vừa update.
  2. `HighErrorRate` (Critical, 5m): Kích hoạt khi `error_rate_pct > 2%` liên tục 5 phút. Runbook: Xem phân loại error_type trên dashboard, lọc log `request_failed` tìm nguyên nhân, kích hoạt circuit breaker chuyển sang fallback response tĩnh.
  3. `LowRetrievalSuccessRate` (Critical, 5m): Kích hoạt khi `tool_success_rate_pct < 90%` trong 5 phút. Runbook: Kiểm tra span `retrieval` trên Langfuse, xác minh trạng thái Vector DB và embedding cluster, tạm chuyển sang zero-shot response.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `2026-09-30 05:23:40Z` đến `2026-09-30 05:24:00Z` (tức 12:23:40 đến 12:24:00 GMT+7)
- **Triệu chứng từ metrics:** Panel Latency trên Dashboard ghi nhận P95 tăng vọt từ mức baseline ~500ms lên `3712.2ms` (đỉnh P99 đạt `5327.5ms`), vượt ngưỡng threshold 3000ms.
- **Log line và correlation ID liên quan:** Lọc log tìm thấy correlation ID `req-ddc0b204` thuộc session `k4-l3b-challenge-s02`, event `response_sent` có `latency_ms = 5471ms` (vượt ngưỡng cảnh báo).
- **Trace ID và span gây ảnh hưởng:** Mở trace `689b73174a6b21509ec9737256443483` có cùng correlation ID `req-ddc0b204` trên Langfuse. Waterfall phân tích cho thấy span cha `lab-agent-run` mất 5.47s, trong đó span con **`retrieval` mất 2.501s** (chiếm phần lớn thời gian), trong khi span con `generation` chỉ mất 0.151s.
- **Root cause:** Component truy xuất tri thức (`retrieval`) bị tắc nghẽn (do sự cố mô phỏng `rag_slow` làm trễ 2.5s ở bước vector store search), làm cho toàn bộ chuỗi thực thi của Agent bị kéo dài bất thường.
- **Fix action:** Thực hiện tắt kịch bản lỗi thông qua API `/incidents/rag_slow/disable`, khôi phục và kiểm tra lại kết nối đến Vector DB.
- **Preventive measure:** Bổ sung cơ chế timeout 1000ms cho bước retrieval kết hợp fallback context tĩnh để không làm gián đoạn request của người dùng; duy trì alert `HighLatencyP95` để phát hiện suy giảm hiệu năng trước khi vi phạm SLO.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
  Tách child observations riêng biệt cho `retrieval` (loại `retriever`) và `generation` (loại `generation`) bên dưới root observation `lab-agent-run`. Quyết định này giúp cô lập ranh giới trách nhiệm: khi có sự cố latency, ta có thể kết luận chính xác bước nào là thủ phạm (do Vector DB hay do Model LLM) mà không phải suy đoán.
- **Một lỗi/blocker đã gặp:**
  Nguy cơ Context Leakage giữa các coroutine trong môi trường FastAPI chạy bất đồng bộ, khiến `correlation_id` của request trước có thể bị dùng nhầm cho request sau.
- **Cách tìm nguyên nhân và xử lý:**
  Gọi `clear_contextvars()` ở đầu `dispatch` của `CorrelationIdMiddleware` trước khi bind bất kỳ biến nào cho request mới, bảo đảm mỗi request có một không gian ngữ cảnh hoàn toàn sạch sẽ.
- **Cách hiểu luồng Metrics → Logs → Traces:**
  Metrics là radar phát hiện triệu chứng diện rộng và khoanh vùng thời gian. Logs dùng correlation ID để định danh chính xác request cá biệt bị ảnh hưởng mà không làm lộ PII. Traces mở chi tiết từng span trong request đó để chỉ ra nguyên nhân gốc rễ (root cause).
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
  Prompt là mã nguồn của logic AI, ảnh hưởng trực tiếp đến token, chi phí và latency. Quản lý prompt version tập trung kèm nhãn `production` cho phép rollback ngay tức thì khi prompt mới gây hồi quy (regression) mà không cần deploy lại code.
- **Điều quan trọng nhất đã học:**
  Kỹ năng xây dựng hệ thống quan sát toàn diện (Observability) và tư duy điều tra sự cố dựa trên bằng chứng dữ liệu có thể kiểm chứng được thay vì phỏng đoán cảm tính.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**
  Hiện tại phần đánh giá chất lượng mới dừng ở mức heuristic chất lượng đơn giản, trong tương lai có thể tích hợp LLM-as-a-judge bất đồng bộ để đánh giá độ chính xác câu trả lời sâu hơn.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
