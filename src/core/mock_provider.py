import json
import time
from typing import Any, Dict, Generator, Optional

from src.agent.parser import extract_city, extract_coupon, extract_quantity
from src.core.llm_provider import LLMProvider
from src.core.text import normalize_text
from src.services import seed_data


class MockProvider(LLMProvider):
    """Deterministic provider for local development, offline demos, and benchmarking."""

    def __init__(self, model_name: str = "mock-llm"):
        super().__init__(model_name=model_name, api_key=None, provider_name="mock")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        started_at = time.time()
        if system_prompt and (
            "Your output must follow this format EXACTLY" in system_prompt or "Action Input" in system_prompt
        ):
            content = self._generate_react_response(prompt)
        else:
            content = self._generate_chat_response(prompt)

        latency_ms = int((time.time() - started_at) * 1000)
        usage = self._estimate_usage(prompt, content)
        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "mock",
            "model": self.model_name,
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        yield self.generate(prompt, system_prompt)["content"]

    def _estimate_usage(self, prompt: str, content: str) -> Dict[str, int]:
        prompt_tokens = max(len(prompt.split()), 1)
        completion_tokens = max(len(content.split()), 1)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    def _generate_chat_response(self, prompt: str) -> str:
        faq = self._match_faq(prompt)
        if faq:
            return faq["answer"]

        product = self._match_product(prompt)
        if product:
            return (
                f"{product['name']} hiện có giá {product['price']:,} VND và tồn kho khoảng {product['stock']} sản phẩm. "
                "Nếu bạn muốn tính tổng tiền, coupon hoặc phí ship, hãy dùng version v2."
            )

        return (
            "Tôi là mock provider cho môi trường local. "
            "Bạn vui lòng nêu rõ tên sản phẩm, số lượng và thành phố để tôi hỗ trợ tốt hơn."
        )

    def _generate_react_response(self, prompt: str) -> str:
        user_query = self._extract_user_query(prompt)
        faq = self._match_faq(user_query)
        if faq:
            return f"Thought: Đây là câu hỏi FAQ đơn giản.\nFinal Answer: {faq['answer']}"

        product = self._match_product(user_query)
        if not product:
            return (
                "Thought: Tôi chưa xác định được sản phẩm cụ thể.\n"
                "Final Answer: Bạn vui lòng cho biết rõ tên sản phẩm, số lượng và thành phố giao hàng."
            )

        quantity = max(extract_quantity(user_query), 1)
        coupon_code = extract_coupon(user_query)
        destination_city = extract_city(user_query)
        observations = self._collect_observations(prompt)

        if "get_product_price" not in observations:
            return (
                "Thought: Tôi cần lấy đơn giá sản phẩm trước.\n"
                f"Action: get_product_price\nAction Input: {json.dumps({'product_name': product['name']}, ensure_ascii=False)}"
            )

        if "check_stock" not in observations:
            return (
                "Thought: Tôi cần kiểm tra tồn kho cho số lượng khách yêu cầu.\n"
                f"Action: check_stock\nAction Input: {json.dumps({'product_name': product['name'], 'quantity': quantity}, ensure_ascii=False)}"
            )

        unit_price = int(observations.get("get_product_price", {}).get("unit_price", product["price"]))
        subtotal = unit_price * quantity

        if coupon_code and "get_coupon_discount" not in observations:
            return (
                "Thought: Tôi cần kiểm tra mã giảm giá trên đơn hàng này.\n"
                f"Action: get_coupon_discount\nAction Input: {json.dumps({'coupon_code': coupon_code, 'order_subtotal': subtotal}, ensure_ascii=False)}"
            )

        if destination_city and "calc_shipping" not in observations:
            total_weight_kg = round(float(product.get("weight_kg", 0.5)) * quantity, 2)
            return (
                "Thought: Tôi cần tính phí ship theo thành phố giao hàng.\n"
                f"Action: calc_shipping\nAction Input: {json.dumps({'destination_city': destination_city, 'total_weight_kg': total_weight_kg}, ensure_ascii=False)}"
            )

        stock_observation = observations.get("check_stock", {})
        in_stock = bool(stock_observation.get("in_stock", True))
        available_quantity = int(stock_observation.get("available_quantity", product.get("stock", 0)))

        discount_amount = 0
        coupon_note = None
        coupon_observation = observations.get("get_coupon_discount")
        if isinstance(coupon_observation, dict):
            discount_amount = int(coupon_observation.get("discount_amount", 0))
            coupon_note = f"Mã {coupon_code} giảm {discount_amount:,} VND."
        elif coupon_code:
            coupon_note = f"Mã {coupon_code} không hợp lệ hoặc không đủ điều kiện áp dụng."

        shipping_fee = 0
        shipping_note = None
        shipping_observation = observations.get("calc_shipping")
        if isinstance(shipping_observation, dict):
            shipping_fee = int(shipping_observation.get("shipping_fee", 0))
            estimated_days = shipping_observation.get("estimated_days")
            shipping_note = f"Phí ship tới {destination_city}: {shipping_fee:,} VND"
            if estimated_days is not None:
                shipping_note += f" (dự kiến {estimated_days} ngày)"
            shipping_note += "."
        elif destination_city:
            shipping_note = f"Chưa có rule ship cho {destination_city}."

        total = subtotal - discount_amount + shipping_fee
        summary_parts = [
            f"{product['name']} {'còn hàng' if in_stock else 'không đủ hàng'} cho số lượng {quantity} (hiện có {available_quantity}).",
            f"Đơn giá: {unit_price:,} VND.",
            f"Tạm tính: {subtotal:,} VND.",
        ]
        if coupon_note:
            summary_parts.append(coupon_note)
        if shipping_note:
            summary_parts.append(shipping_note)
        if in_stock:
            summary_parts.append(f"Tổng thanh toán dự kiến: {total:,} VND.")
        else:
            summary_parts.append("Bạn vui lòng giảm số lượng hoặc chọn sản phẩm khác.")

        return "Thought: Tôi đã đủ dữ liệu từ các tools để trả lời.\nFinal Answer: " + " ".join(summary_parts)

    def _extract_user_query(self, prompt: str) -> str:
        for line in prompt.splitlines():
            if line.startswith("User:"):
                return line.split("User:", 1)[1].strip()
        return prompt.strip()

    def _match_product(self, text: str) -> Dict[str, Any] | None:
        normalized_text = normalize_text(text)
        for product in seed_data.PRODUCTS:
            if normalize_text(product["name"]) in normalized_text:
                return product
        return None

    def _match_faq(self, text: str) -> Dict[str, Any] | None:
        normalized_text = normalize_text(text)
        for faq in seed_data.FAQS:
            if normalize_text(faq["question"]) in normalized_text or normalize_text(faq["topic"].replace("_", " ")) in normalized_text:
                return faq
        if "doi tra" in normalized_text:
            return next((faq for faq in seed_data.FAQS if faq["topic"] == "return_policy"), None)
        if "giao hang" in normalized_text or "cuoi tuan" in normalized_text:
            return next((faq for faq in seed_data.FAQS if faq["topic"] == "weekend_shipping"), None)
        return None

    def _collect_observations(self, prompt: str) -> Dict[str, Any]:
        observations: Dict[str, Any] = {}
        current_action: str | None = None

        for raw_line in prompt.splitlines():
            line = raw_line.strip()
            if line.startswith("Action:"):
                current_action = line.split("Action:", 1)[1].strip()
            elif line.startswith("Observation:") and current_action:
                raw_observation = line.split("Observation:", 1)[1].strip()
                try:
                    observations[current_action] = json.loads(raw_observation)
                except json.JSONDecodeError:
                    observations[current_action] = raw_observation

        return observations
