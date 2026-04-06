import time
from typing import Any, Dict

from src.core.provider_factory import build_provider
from src.services.faq_service import faq_service
from src.services.product_service import product_service
from src.telemetry.logger import logger
from src.telemetry.trace_store import trace_store


class BaselineChatbot:
    def __init__(self):
        self.llm = build_provider()

    def run(self, user_input: str, session_id: str | None = None) -> Dict[str, Any]:
        started_at = time.time()
        trace = trace_store.create_trace(version="v1", user_query=user_input, session_id=session_id)
        logger.log_event("CHATBOT_REQUEST_RECEIVED", {"trace_id": trace["trace_id"], "input": user_input})

        faq = faq_service.match(user_input)
        if faq:
            trace_store.append_step(
                trace,
                {
                    "step": 1,
                    "context_sources": [f"faq:{faq['topic']}"],
                    "llm_mode": "single_pass",
                },
            )
            answer = faq["answer"]
        else:
            product = product_service.detect_product_in_text(user_input)
            trace_store.append_step(
                trace,
                {
                    "step": 1,
                    "context_sources": [f"product:{product['name']}" if product else "none"],
                    "llm_mode": "single_pass",
                },
            )
            if product:
                answer = (
                    f"{product['name']} hiện có giá niêm yết {product['price']:,} VND. "
                    "Nếu bạn cần kiểm tra tồn kho, mã giảm giá hoặc phí ship, hãy chạy version v2."
                )
            else:
                generated = self.llm.generate(user_input, system_prompt="You are a concise Vietnamese shopping assistant.")
                answer = generated["content"]

        latency_ms = int((time.time() - started_at) * 1000)
        trace = trace_store.finalize_trace(
            trace,
            final_answer=answer,
            status="success",
            metrics={"latency_ms": latency_ms, "tool_calls_count": 0, "steps": 1},
        )
        logger.log_event("CHATBOT_FINAL", {"trace_id": trace["trace_id"], "latency_ms": latency_ms})
        return {
            "version": "v1",
            "answer": answer,
            "latency_ms": latency_ms,
            "steps": 1,
            "tool_calls": [],
            "trace_id": trace["trace_id"],
            "status": "success",
            "error_code": None,
        }


chatbot = BaselineChatbot()
