import time
from typing import Any, Dict

from src.core.provider_factory import build_provider
from src.db.session import SessionLocal
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

        db = SessionLocal()
        try:
            faq = faq_service.match(db, user_input)
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
                product = product_service.detect_product_in_text(db, user_input)
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
                        f"Thông tin {product['name']}:\n"
                        f"- Giá: {product['price']:,} VND\n"
                        f"- Tồn kho (ước tính): {product['stock']}\n"
                        f"- Mô tả: {product.get('description') or 'N/A'}\n\n"
                        "Nếu bạn cần kiểm tra mã giảm giá hoặc tính phí ship theo thành phố, hãy chọn version v2."
                    )
                else:
                    generated = self.llm.generate(
                        user_input,
                        system_prompt=(
                            "Bạn là trợ lý mua sắm tiếng Việt cho cửa hàng điện tử. "
                            "Hãy trả lời ngắn gọn, lịch sự, không bịa dữ liệu. "
                            "Nếu câu hỏi mơ hồ hoặc thiếu tên sản phẩm/thành phố/số lượng, "
                            "hãy hỏi lại 1-2 câu để làm rõ thay vì suy đoán."
                        ),
                    )
                    answer = generated["content"]
        finally:
            db.close()

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
