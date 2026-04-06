import time
import json
from typing import Any, Dict, List, Optional

from src.agent.parser import extract_city, extract_coupon, extract_faq, extract_product, extract_quantity, parse_react_response
from src.agent.prompts import build_react_system_prompt
from src.agent.tools_registry import get_tools, preview_result, render_tool_descriptions
from src.core.config import get_settings
from src.core.llm_provider import LLMProvider
from src.core.provider_factory import build_provider
from src.telemetry.logger import logger
from src.telemetry.metrics import build_llm_metrics, tracker
from src.telemetry.trace_store import trace_store


class ReActAgent:
    """Runnable standard ReAct-style agent using LLM for tool selection and planning."""

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
        scratchpad = f"User: {user_input}\n"
        system_prompt = self.get_system_prompt()
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        llm_calls = 0
        llm_latency_ms = 0
        observed_tools: Dict[str, Dict[str, Any]] = {}
        required_tools = self._infer_required_tools(user_input)

        while steps < self.max_steps:
            steps += 1
            logger.log_event("AGENT_STEP_STARTED", {"trace_id": trace["trace_id"], "step": steps})

            try:
                response = self.llm.generate(prompt=scratchpad, system_prompt=system_prompt)
                text = response["content"]
                usage = response.get("usage", {})
                llm_calls += 1
                llm_latency_ms += int(response.get("latency_ms", 0))
                total_usage["prompt_tokens"] += int(usage.get("prompt_tokens", 0))
                total_usage["completion_tokens"] += int(usage.get("completion_tokens", 0))
                total_usage["total_tokens"] += int(usage.get("total_tokens", 0))
                tracker.track_request(
                    response.get("provider", self.llm.provider_name),
                    response.get("model", self.llm.model_name),
                    usage,
                    int(response.get("latency_ms", 0)),
                )

                step_payload: Dict[str, Any] = {
                    "step": steps,
                    "provider": response.get("provider", self.llm.provider_name),
                    "model": response.get("model", self.llm.model_name),
                    "usage": usage,
                    "latency_ms": int(response.get("latency_ms", 0)),
                    "raw_model_output": text,
                }

                try:
                    parsed = parse_react_response(text)
                except Exception as exc:
                    observation = (
                        f"System Error parsing your response: {str(exc)}. "
                        "Please strictly use valid JSON in 'Action Input'."
                    )
                    scratchpad += f"{text}\nObservation: {observation}\n"
                    step_payload.update(
                        {
                            "thought": text,
                            "action": None,
                            "observation": observation,
                            "status": "parse_error",
                        }
                    )
                    trace_store.append_step(trace, step_payload)
                    continue

                thought = parsed.get("thought")
                action = parsed.get("action")
                final_answer = parsed.get("final_answer")
                step_payload["thought"] = thought

                if action:
                    tool_name, args = action
                    missing_tools = self._missing_required_tools(required_tools, observed_tools)
                    if tool_name in observed_tools and observed_tools[tool_name].get("ok") and missing_tools:
                        forced_call = self._next_missing_tool_call(user_input, missing_tools, observed_tools)
                        if forced_call:
                            tool_name, args = forced_call
                            step_payload["planner_note"] = (
                                f"Model repeated `{parsed['action'][0]}`. "
                                f"Forced next missing tool `{tool_name}` to keep grounding complete."
                            )
                    args = self._prepare_tool_args(user_input, tool_name, args)
                    has_error = False
                    try:
                        result = self._execute_tool(tool_name, args)
                        observation = preview_result(result)
                        observed_tools[tool_name] = {"ok": True, "args": args, "result": result}
                    except Exception as exc:
                        result = f"Error executing tool {tool_name}: {str(exc)}"
                        observation = result
                        has_error = True
                        observed_tools[tool_name] = {"ok": False, "args": args, "error": str(exc)}

                    step_payload.update(
                        {
                            "action": {"tool": tool_name, "args": args},
                            "observation": result,
                            "status": "tool_error" if has_error else "tool_success",
                        }
                    )
                    if parsed.get("has_mixed_output"):
                        step_payload["parser_note"] = "Ignored Final Answer because the model still emitted an Action."
                    trace_store.append_step(trace, step_payload)

                    if not has_error:
                        tool_calls.append({"tool": tool_name, "args": args, "result_preview": observation})

                    if self._has_required_grounding(required_tools, observed_tools):
                        grounded_answer = self._build_grounded_answer(user_input, observed_tools)
                        trace_store.append_step(
                            trace,
                            {
                                "step": steps + 0.1,
                                "thought": "Đã đủ dữ liệu từ tools, tổng hợp câu trả lời trực tiếp từ observation.",
                                "action": None,
                                "observation": grounded_answer,
                                "status": "auto_final_answer",
                            },
                        )
                        return self._finalize(
                            trace=trace,
                            answer=grounded_answer,
                            started_at=started_at,
                            steps=len(trace["steps"]),
                            tool_calls=tool_calls,
                            status="success",
                            error_code=None,
                            total_usage=total_usage,
                            llm_calls=llm_calls,
                            llm_latency_ms=llm_latency_ms,
                        )

                    scratchpad += f"{self._render_action_step(thought, tool_name, args)}\nObservation: {observation}\n"
                    continue

                if final_answer:
                    missing_tools = self._missing_required_tools(required_tools, observed_tools)
                    if missing_tools:
                        observation = (
                            "Bạn chưa được phép kết luận. "
                            f"Hãy gọi thêm các tool còn thiếu trước khi trả lời cuối cùng: {', '.join(missing_tools)}."
                        )
                        step_payload.update(
                            {
                                "action": None,
                                "observation": observation,
                                "status": "insufficient_grounding",
                                "missing_tools": missing_tools,
                            }
                        )
                        trace_store.append_step(trace, step_payload)
                        scratchpad += f"{text}\nObservation: {observation}\n"
                        continue

                    step_payload.update({"action": None, "observation": final_answer, "status": "final_answer"})
                    trace_store.append_step(trace, step_payload)
                    return self._finalize(
                        trace=trace,
                        answer=final_answer,
                        started_at=started_at,
                        steps=steps,
                        tool_calls=tool_calls,
                        status="success",
                        error_code=None,
                        total_usage=total_usage,
                        llm_calls=llm_calls,
                        llm_latency_ms=llm_latency_ms,
                    )

                observation = "Error parsing action, you must provide 'Action' and 'Action Input', or 'Final Answer'."
                scratchpad += f"{text}\nObservation: {observation}\n"
                step_payload.update({"action": None, "observation": observation, "status": "invalid_step"})
                trace_store.append_step(trace, step_payload)

            except Exception as exc:
                logger.log_event("AGENT_STEP_ERROR", {"trace_id": trace["trace_id"], "step": steps, "error": str(exc)})
                answer = "Hệ thống đang gặp trục trặc khi suy luận, vui lòng thử lại sau."
                trace_store.append_step(
                    trace,
                    {
                        "step": steps,
                        "thought": "Provider call failed.",
                        "action": None,
                        "observation": str(exc),
                        "status": "provider_error",
                    },
                )
                return self._finalize(
                    trace=trace,
                    answer=answer,
                    started_at=started_at,
                    steps=steps,
                    tool_calls=tool_calls,
                    status="error",
                    error_code="PROVIDER_ERROR",
                    total_usage=total_usage,
                    llm_calls=llm_calls,
                    llm_latency_ms=llm_latency_ms,
                )

        answer = "Tôi đã suy nghĩ quá giới hạn số bước nhưng chưa tìm được câu trả lời."
        trace_store.append_step(
            trace,
            {
                "step": steps + 1,
                "thought": "Đã chạm max_steps.",
                "action": None,
                "observation": answer,
                "status": "max_steps_reached",
            },
        )
        return self._finalize(
            trace=trace,
            answer=answer,
            started_at=started_at,
            steps=len(trace["steps"]),
            tool_calls=tool_calls,
            status="error",
            error_code="MAX_STEPS_REACHED",
            total_usage=total_usage,
            llm_calls=llm_calls,
            llm_latency_ms=llm_latency_ms,
        )

    def _finalize(
        self,
        *,
        trace: Dict[str, Any],
        answer: str,
        started_at: float,
        steps: int,
        tool_calls: List[Dict[str, Any]],
        status: str,
        error_code: str | None,
        total_usage: Dict[str, int],
        llm_calls: int,
        llm_latency_ms: int,
    ) -> Dict[str, Any]:
        latency_ms = int((time.time() - started_at) * 1000)
        llm_metrics = build_llm_metrics(
            provider=self.llm.provider_name,
            model=self.llm.model_name,
            usage=total_usage,
            llm_calls=llm_calls,
            latency_ms=llm_latency_ms,
        )
        trace = trace_store.finalize_trace(
            trace,
            final_answer=answer,
            status=status,
            metrics={
                "latency_ms": latency_ms,
                "tool_calls_count": len(tool_calls),
                "steps": steps,
                **llm_metrics,
            },
            error_code=error_code,
        )
        logger.log_event(
            "AGENT_FINAL",
            {"trace_id": trace["trace_id"], "latency_ms": latency_ms, "steps": steps, "status": status},
        )
        return {
            "version": "v2",
            "answer": answer,
            "latency_ms": latency_ms,
            "steps": steps,
            "tool_calls": tool_calls,
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

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        for tool in self.tools:
            if tool["name"] == tool_name:
                logger.log_event("TOOL_EXECUTION_STARTED", {"tool": tool_name, "args": args})
                result = tool["handler"](**args)
                logger.log_event("TOOL_EXECUTED", {"tool": tool_name, "args": args, "result": result})
                return result
        raise ValueError(f"Tool {tool_name} not found.")

    def _render_action_step(self, thought: str | None, tool_name: str, args: Dict[str, Any]) -> str:
        rendered_thought = thought or "Need tool-grounded information."
        return (
            f"Thought: {rendered_thought}\n"
            f"Action: {tool_name}\n"
            f"Action Input: {json.dumps(args, ensure_ascii=False)}"
        )

    def _prepare_tool_args(self, user_input: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        prepared = dict(args)
        product = extract_product(user_input)
        quantity = extract_quantity(user_input)

        if tool_name == "calc_shipping" and product:
            prepared["total_weight_kg"] = round(float(product.get("weight_kg", 0.0)) * quantity, 2)
        if tool_name == "get_coupon_discount" and product:
            prepared["order_subtotal"] = int(product.get("price", 0)) * quantity
        return prepared

    def _next_missing_tool_call(
        self,
        user_input: str,
        missing_tools: List[str],
        observed_tools: Dict[str, Dict[str, Any]],
    ) -> tuple[str, Dict[str, Any]] | None:
        product = extract_product(user_input)
        quantity = extract_quantity(user_input)
        coupon = extract_coupon(user_input)
        city = extract_city(user_input)

        for tool_name in missing_tools:
            if tool_name == "get_faq_answer":
                return tool_name, {"user_message": user_input}
            if tool_name == "get_product_price" and product:
                return tool_name, {"product_name": product["name"]}
            if tool_name == "check_stock" and product:
                return tool_name, {"product_name": product["name"], "quantity": quantity}
            if tool_name == "get_coupon_discount" and product and coupon:
                subtotal = int(product["price"]) * quantity
                return tool_name, {"coupon_code": coupon, "order_subtotal": subtotal}
            if tool_name == "calc_shipping" and product and city:
                total_weight_kg = round(float(product.get("weight_kg", 0.0)) * quantity, 2)
                return tool_name, {"destination_city": city, "total_weight_kg": total_weight_kg}
        return None

    def _infer_required_tools(self, user_input: str) -> List[str]:
        faq = extract_faq(user_input)
        if faq:
            return ["get_faq_answer"]

        product = extract_product(user_input)
        city = extract_city(user_input)
        coupon = extract_coupon(user_input)
        quantity = extract_quantity(user_input)
        lowered = user_input.lower()

        required_tools: List[str] = []
        if product:
            need_price = any(token in lowered for token in ("giá", "gia", "bao nhiêu", "bao nhieu", "tổng", "tong", "mua"))
            need_stock = quantity > 1 or any(token in lowered for token in ("còn hàng", "con hang", "mua", "stock"))
            if need_price:
                required_tools.append("get_product_price")
            if need_stock:
                required_tools.append("check_stock")
        if coupon:
            required_tools.append("get_coupon_discount")
        if city:
            required_tools.append("calc_shipping")
        return required_tools

    def _missing_required_tools(
        self, required_tools: List[str], observed_tools: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        return [tool_name for tool_name in required_tools if tool_name not in observed_tools]

    def _has_required_grounding(self, required_tools: List[str], observed_tools: Dict[str, Dict[str, Any]]) -> bool:
        return not self._missing_required_tools(required_tools, observed_tools)

    def _build_grounded_answer(self, user_input: str, observed_tools: Dict[str, Dict[str, Any]]) -> str:
        faq_result = observed_tools.get("get_faq_answer", {})
        if faq_result.get("ok"):
            return str(faq_result["result"]["answer"])

        quantity = extract_quantity(user_input)
        city = extract_city(user_input)
        coupon = extract_coupon(user_input)

        price_result = observed_tools.get("get_product_price", {}).get("result", {})
        stock_result = observed_tools.get("check_stock", {}).get("result", {})
        coupon_obs = observed_tools.get("get_coupon_discount", {})
        shipping_obs = observed_tools.get("calc_shipping", {})

        product = extract_product(user_input)
        product_name = price_result.get("product_name") or stock_result.get("product_name") or (product or {}).get("name")
        unit_price = int(price_result.get("unit_price", 0))
        subtotal = unit_price * quantity if unit_price else 0

        parts: List[str] = []
        if product_name and unit_price:
            parts.append(f"{product_name} có đơn giá {unit_price:,} VND.")
        if subtotal:
            parts.append(f"Subtotal cho {quantity} sản phẩm là {subtotal:,} VND.")
        if stock_result:
            parts.append(
                f"Tồn kho hiện tại: {stock_result.get('available_quantity', 0)}. "
                f"Đủ hàng cho yêu cầu: {'có' if stock_result.get('in_stock') else 'không'}."
            )

        discount_amount = 0
        if coupon:
            if coupon_obs.get("ok"):
                coupon_result = coupon_obs.get("result", {})
                discount_amount = int(coupon_result.get("discount_amount", 0))
                parts.append(f"Mã {coupon} hợp lệ, giảm {discount_amount:,} VND.")
            elif coupon_obs:
                parts.append(f"Mã {coupon} không hợp lệ hoặc không tồn tại.")

        shipping_fee = 0
        if city:
            if shipping_obs.get("ok"):
                shipping_result = shipping_obs.get("result", {})
                shipping_fee = int(shipping_result.get("shipping_fee", 0))
                parts.append(
                    f"Phí ship đến {city}: {shipping_fee:,} VND, "
                    f"dự kiến {shipping_result.get('estimated_days', '?')} ngày."
                )
            elif shipping_obs:
                parts.append(f"Không tính được phí ship cho {city}.")

        if subtotal:
            total = subtotal - discount_amount + shipping_fee
            parts.append(f"Tổng thanh toán dự kiến: {total:,} VND.")

        return " ".join(parts).strip() or "Tôi chưa có đủ dữ liệu grounded để trả lời."


settings = get_settings()
agent = ReActAgent(max_steps=settings.max_agent_steps)
