import time
from typing import Any, Dict

from src.core.provider_factory import build_provider
from src.db.session import SessionLocal
from src.services.faq_service import faq_service
from src.services.product_service import product_service
from src.telemetry.logger import logger
from src.telemetry.metrics import build_llm_metrics, tracker
from src.telemetry.trace_store import trace_store


class BaselineChatbot:
    def __init__(self):
        self.llm = build_provider()

    def run(self, user_input: str, session_id: str | None = None) -> Dict[str, Any]:
        started_at = time.time()
        trace = trace_store.create_trace(version="v1", user_query=user_input, session_id=session_id)
        logger.log_event("CHATBOT_REQUEST_RECEIVED", {"trace_id": trace["trace_id"], "input": user_input})

        llm_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        llm_calls = 0
        llm_latency_ms = 0
        answer = ""
        status = "success"
        error_code = None

        db = SessionLocal()
        try:
            faq = faq_service.match(db, user_input)
            trace_store.append_step(
                trace,
                {
                    "step": 1,
                    "phase": "faq_lookup",
                    "thought": "Kiểm tra FAQ trước vì đây là đường trả lời rẻ và nhanh nhất của v1.",
                    "context_sources": [f"faq:{faq['topic']}"] if faq else [],
                    "decision": "faq_hit" if faq else "faq_miss",
                },
            )
            if faq:
                answer = faq["answer"]
            else:
                product = product_service.detect_product_in_text(db, user_input)
                trace_store.append_step(
                    trace,
                    {
                        "step": 2,
                        "phase": "product_lookup",
                        "thought": "Không match FAQ, thử tìm sản phẩm trong câu hỏi để trả thông tin catalog cơ bản.",
                        "context_sources": [f"product:{product['name']}"] if product else [],
                        "decision": "product_hit" if product else "product_miss",
                    },
                )
                if product:
                    answer = (
                        f"Thông tin {product['name']}:\n"
                        f"- Giá: {product['price']:,} VND\n"
                        f"- Tồn kho (ước tính): {product['stock']}\n"
                        f"- Mô tả: {product.get('description') or 'N/A'}\n\n"
                        "Nếu bạn cần kiểm tra mã giảm giá hoặc tính phí ship theo thành phố, hãy xem thêm kết quả v2."
                    )
                else:
                    trace_store.append_step(
                        trace,
                        {
                            "step": 3,
                            "phase": "llm_fallback",
                            "thought": "Không có grounding từ FAQ hay product catalog, fallback sang single-pass LLM.",
                            "provider": self.llm.provider_name,
                            "model": self.llm.model_name,
                        },
                    )
                    try:
                        generated = self.llm.generate(
                            user_input,
                            system_prompt=(
                                "Bạn là trợ lý mua sắm tiếng Việt cho cửa hàng điện tử. "
                                "Hãy trả lời ngắn gọn, lịch sự, không bịa dữ liệu. "
                                "Nếu câu hỏi mơ hồ hoặc thiếu tên sản phẩm/thành phố/số lượng, "
                                "hãy hỏi lại 1-2 câu để làm rõ thay vì suy đoán."
                            ),
                        )
                        llm_calls = 1
                        llm_latency_ms = int(generated.get("latency_ms", 0))
                        llm_usage = generated.get("usage", llm_usage)
                        tracker.track_request(
                            generated.get("provider", self.llm.provider_name),
                            generated.get("model", self.llm.model_name),
                            llm_usage,
                            llm_latency_ms,
                        )
                        answer = generated["content"]
                        trace_store.append_step(
                            trace,
                            {
                                "step": 4,
                                "phase": "llm_response",
                                "thought": "LLM đã tạo câu trả lời cuối cùng cho truy vấn chưa có grounding trực tiếp.",
                                "provider": generated.get("provider", self.llm.provider_name),
                                "model": generated.get("model", self.llm.model_name),
                                "usage": llm_usage,
                                "latency_ms": llm_latency_ms,
                                "final_answer_preview": answer[:300],
                            },
                        )
                    except Exception as exc:
                        status = "error"
                        error_code = "PROVIDER_ERROR"
                        answer = "Hệ thống đang gặp lỗi khi gọi provider, vui lòng thử lại sau."
                        trace_store.append_step(
                            trace,
                            {
                                "step": 4,
                                "phase": "llm_response",
                                "thought": "Fallback LLM thất bại.",
                                "provider": self.llm.provider_name,
                                "model": self.llm.model_name,
                                "error": str(exc),
                            },
                        )
        finally:
            db.close()

        latency_ms = int((time.time() - started_at) * 1000)
        llm_metrics = build_llm_metrics(
            provider=self.llm.provider_name,
            model=self.llm.model_name,
            usage=llm_usage,
            llm_calls=llm_calls,
            latency_ms=llm_latency_ms,
        )
        trace = trace_store.finalize_trace(
            trace,
            final_answer=answer,
            status=status,
            metrics={
                "latency_ms": latency_ms,
                "tool_calls_count": 0,
                "steps": len(trace["steps"]),
                **llm_metrics,
            },
            error_code=error_code,
        )
        logger.log_event(
            "CHATBOT_FINAL",
            {"trace_id": trace["trace_id"], "latency_ms": latency_ms, "status": status, "steps": len(trace["steps"])},
        )
        return {
            "version": "v1",
            "answer": answer,
            "latency_ms": latency_ms,
            "steps": len(trace["steps"]),
            "tool_calls": [],
            "reasoning_steps": trace["steps"],
            "trace_id": trace["trace_id"],
            "status": status,
            "error_code": error_code,
            "provider": self.llm.provider_name,
            "model": self.llm.model_name,
            "llm_calls": llm_calls,
            "token_usage": llm_metrics["token_usage"],
            "cost_estimate": llm_metrics["cost_estimate"],
        }


chatbot = BaselineChatbot()
