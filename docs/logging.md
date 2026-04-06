# Logging and Trace Design

## Mục tiêu

Lab này cần chứng minh bằng evidence, không chỉ bằng cảm giác. Vì vậy cần có log từng bước cho cả `v1` và `v2`.

Logging phải trả lời được:

- request nào thất bại
- thất bại ở bước nào
- tool nào được gọi
- agent chọn tool có hợp lý không
- `v1` nhanh hơn ở đâu
- `v2` chính xác hơn ở đâu

## Nguyên tắc

- dùng JSON logs
- mỗi request có `trace_id`
- mọi event trong cùng request dùng cùng `trace_id`
- lưu được version `v1` hoặc `v2`
- lưu step index cho agent

## Thư mục log đề xuất

```text
logs/
  app.log
  traces/
    trace_20260406_001.json
    trace_20260406_002.json
```

## Event schema chuẩn

```json
{
  "timestamp": "2026-04-06T15:32:11.123Z",
  "trace_id": "trace_20260406_001",
  "session_id": "demo-session-01",
  "version": "v2",
  "event_type": "TOOL_EXECUTED",
  "step": 2,
  "component": "agent",
  "status": "success",
  "latency_ms": 44,
  "payload": {}
}
```

## Event types cho `v1`

`v1` vẫn phải có trace từng bước, dù ít bước hơn.

- `CHATBOT_REQUEST_RECEIVED`
- `CHATBOT_CONTEXT_FETCH_STARTED`
- `CHATBOT_CONTEXT_FETCH_COMPLETED`
- `CHATBOT_LLM_CALL_STARTED`
- `CHATBOT_LLM_CALL_COMPLETED`
- `CHATBOT_FINAL`
- `CHATBOT_ERROR`

## Event types cho `v2`

- `AGENT_REQUEST_RECEIVED`
- `AGENT_STEP_STARTED`
- `AGENT_THOUGHT_GENERATED`
- `AGENT_ACTION_PARSED`
- `TOOL_EXECUTION_STARTED`
- `TOOL_EXECUTED`
- `AGENT_OBSERVATION_APPENDED`
- `AGENT_FINAL`
- `AGENT_MAX_STEPS_EXCEEDED`
- `AGENT_PARSE_ERROR`
- `AGENT_ERROR`

## Event types dùng chung

- `API_REQUEST_STARTED`
- `API_REQUEST_COMPLETED`
- `DB_QUERY`
- `METRIC_RECORDED`

## Trace file format đề xuất

Một file trace nên gồm:

```json
{
  "trace_id": "trace_20260406_001",
  "version": "v2",
  "user_query": "Mua 2 iPhone 15 với WINNER10 ship Hà Nội",
  "status": "success",
  "steps": [
    {
      "step": 1,
      "thought": "Tôi cần lấy giá sản phẩm trước.",
      "action": {
        "tool": "get_product_price",
        "args": {
          "product_name": "iPhone 15"
        }
      },
      "observation": {
        "unit_price": 24990000
      }
    },
    {
      "step": 2,
      "thought": "Tôi cần kiểm tra tồn kho cho số lượng 2.",
      "action": {
        "tool": "check_stock",
        "args": {
          "product_name": "iPhone 15",
          "quantity": 2
        }
      },
      "observation": {
        "in_stock": true,
        "available_quantity": 12
      }
    }
  ],
  "final_answer": "Tổng đơn hàng là 47,020,000 VND.",
  "metrics": {
    "latency_ms": 2144,
    "tool_calls_count": 4,
    "prompt_tokens": 820,
    "completion_tokens": 310
  }
}
```

## Log tối thiểu cho `v1`

Ví dụ trace `v1`:

```json
{
  "trace_id": "trace_20260406_008",
  "version": "v1",
  "user_query": "Chính sách đổi trả là gì?",
  "steps": [
    {
      "step": 1,
      "context_sources": [
        "faq:return_policy"
      ],
      "llm_mode": "single_pass"
    }
  ],
  "final_answer": "Bạn có thể đổi trả trong 7 ngày ...",
  "metrics": {
    "latency_ms": 740,
    "tool_calls_count": 0
  }
}
```

## Metrics cần ghi

- `latency_ms`
- `steps`
- `tool_calls_count`
- `success`
- `error_code`
- `prompt_tokens`
- `completion_tokens`
- `provider`
- `model`

## Error codes nên chuẩn hóa

- `LLM_PROVIDER_ERROR`
- `CHATBOT_CONTEXT_ERROR`
- `AGENT_PARSE_ERROR`
- `AGENT_MAX_STEPS_EXCEEDED`
- `TOOL_NOT_FOUND`
- `TOOL_ARGUMENT_ERROR`
- `DB_CONNECTION_ERROR`
- `COUPON_INVALID`
- `INSUFFICIENT_STOCK`

## Điểm cần có trong UI

Frontend nên hiển thị:

- `trace_id`
- `version`
- `latency_ms`
- `steps`
- danh sách tool calls
- trạng thái `success` hoặc `error`

## Use cho báo cáo

Logs này phục vụ:

- trace quality
- evaluation and analysis
- debugging case study
- chứng minh nơi agent tạo giá trị
