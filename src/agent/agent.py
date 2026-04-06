import time
from typing import Any, Dict, List, Optional

from src.agent.parser import extract_city, extract_coupon, extract_product, extract_quantity
from src.agent.prompts import build_react_system_prompt
from src.agent.tools_registry import get_tools, preview_result, render_tool_descriptions
from src.core.config import get_settings
from src.core.llm_provider import LLMProvider
from src.core.provider_factory import build_provider
from src.telemetry.logger import logger
from src.telemetry.trace_store import trace_store


class ReActAgent:
    """Runnable skeleton of a ReAct-style agent using deterministic tool selection."""

    def __init__(self, llm: Optional[LLMProvider] = None, tools: Optional[List[Dict[str, Any]]] = None, max_steps: int = 5):
        self.llm = llm or build_provider()
        self.tools = tools or get_tools()
        self.max_steps = max_steps

    def get_system_prompt(self) -> str:
        return build_react_system_prompt(render_tool_descriptions(self.tools), self.max_steps)

    def run(self, user_input: str, session_id: str | None = None) -> Dict[str, Any]:
        started_at = time.time()
        trace = trace_store.create_trace(version="v2", user_query=user_input, session_id=session_id)
        logger.log_event("AGENT_REQUEST_RECEIVED", {"trace_id": trace["trace_id"], "input": user_input, "model": self.llm.model_name})

        tool_calls: List[Dict[str, Any]] = []
        steps = 0
        subtotal = 0
        discount_amount = 0
        shipping_fee = 0

        product = extract_product(user_input)
        quantity = extract_quantity(user_input)
        coupon_code = extract_coupon(user_input)
        city = extract_city(user_input)

        if not product:
            answer = "Tôi chưa xác định được sản phẩm trong yêu cầu. Hãy nhập đúng tên sản phẩm trong catalog."
            latency_ms = int((time.time() - started_at) * 1000)
            trace = trace_store.finalize_trace(
                trace,
                final_answer=answer,
                status="error",
                metrics={"latency_ms": latency_ms, "tool_calls_count": 0, "steps": 0},
                error_code="PRODUCT_NOT_FOUND",
            )
            return {
                "version": "v2",
                "answer": answer,
                "latency_ms": latency_ms,
                "steps": 0,
                "tool_calls": [],
                "trace_id": trace["trace_id"],
                "status": "error",
                "error_code": "PRODUCT_NOT_FOUND",
            }

        plan = [
            ("get_product_price", {"product_name": product["name"]}, "Tôi cần lấy đơn giá sản phẩm."),
            ("check_stock", {"product_name": product["name"], "quantity": quantity}, "Tôi cần kiểm tra tồn kho theo số lượng yêu cầu."),
        ]
        if coupon_code:
            plan.append(("get_coupon_discount", {"coupon_code": coupon_code, "order_subtotal": product["price"] * quantity}, "Tôi cần xác thực mã giảm giá."))
        if city:
            plan.append(("calc_shipping", {"destination_city": city, "total_weight_kg": product["weight_kg"] * quantity}, "Tôi cần tính phí vận chuyển."))

        for tool_name, args, thought in plan[: self.max_steps]:
            steps += 1
            logger.log_event("AGENT_STEP_STARTED", {"trace_id": trace["trace_id"], "step": steps, "tool": tool_name})
            try:
                result = self._execute_tool(tool_name, args)
            except ValueError as exc:
                error_code = str(exc)
                answer = f"Không thể hoàn tất yêu cầu vì lỗi: {error_code}."
                return self._finalize(trace, answer, started_at, steps - 1, tool_calls, "error", error_code)
            trace_store.append_step(
                trace,
                {
                    "step": steps,
                    "thought": thought,
                    "action": {"tool": tool_name, "args": args},
                    "observation": result,
                },
            )
            tool_calls.append({"tool": tool_name, "args": args, "result_preview": preview_result(result)})

            if tool_name == "get_product_price":
                subtotal = int(result["unit_price"]) * quantity
            elif tool_name == "check_stock" and not result["in_stock"]:
                answer = (
                    f"{product['name']} hiện không đủ hàng. "
                    f"Yêu cầu {quantity}, tồn kho còn {result['available_quantity']}."
                )
                return self._finalize(trace, answer, started_at, steps, tool_calls, "error", "INSUFFICIENT_STOCK")
            elif tool_name == "get_coupon_discount":
                discount_amount = int(result["discount_amount"])
            elif tool_name == "calc_shipping":
                shipping_fee = int(result["shipping_fee"])

        total_amount = subtotal - discount_amount + shipping_fee
        answer = (
            f"{product['name']} x {quantity}: subtotal {subtotal:,} VND. "
            f"Giảm giá: {discount_amount:,} VND. "
            f"Phí ship: {shipping_fee:,} VND. "
            f"Tổng cộng: {total_amount:,} VND."
        )
        return self._finalize(trace, answer, started_at, steps, tool_calls, "success", None)

    def _finalize(
        self,
        trace: Dict[str, Any],
        answer: str,
        started_at: float,
        steps: int,
        tool_calls: List[Dict[str, Any]],
        status: str,
        error_code: str | None,
    ) -> Dict[str, Any]:
        latency_ms = int((time.time() - started_at) * 1000)
        trace = trace_store.finalize_trace(
            trace,
            final_answer=answer,
            status=status,
            metrics={"latency_ms": latency_ms, "tool_calls_count": len(tool_calls), "steps": steps},
            error_code=error_code,
        )
        logger.log_event("AGENT_FINAL", {"trace_id": trace["trace_id"], "latency_ms": latency_ms, "steps": steps, "status": status})
        return {
            "version": "v2",
            "answer": answer,
            "latency_ms": latency_ms,
            "steps": steps,
            "tool_calls": tool_calls,
            "trace_id": trace["trace_id"],
            "status": status,
            "error_code": error_code,
        }

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        for tool in self.tools:
            if tool["name"] == tool_name:
                logger.log_event("TOOL_EXECUTION_STARTED", {"tool": tool_name, "args": args})
                result = tool["handler"](**args)
                logger.log_event("TOOL_EXECUTED", {"tool": tool_name, "args": args, "result": result})
                return result
        raise ValueError(f"Tool {tool_name} not found.")


settings = get_settings()
agent = ReActAgent(max_steps=settings.max_agent_steps)
