import json
import re
from typing import Any, Dict, Generator, Optional

from src.core.llm_provider import LLMProvider


class MockProvider(LLMProvider):
    """Deterministic provider for local development without external APIs."""

    def __init__(self, model_name: str = "mock-llm"):
        super().__init__(model_name=model_name, api_key=None, provider_name="mock")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if system_prompt and "Your output must follow this format EXACTLY" in system_prompt:
            content = self._generate_react_response(prompt)
        else:
            content = self._generate_chat_response(prompt)
        return {
            "content": content,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "latency_ms": 0,
            "provider": "mock",
            "model": self.model_name,
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        yield self.generate(prompt, system_prompt)["content"]

    def _generate_chat_response(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "đổi trả" in lowered or "doi tra" in lowered:
            return "Bạn có thể đổi trả trong vòng 7 ngày nếu sản phẩm còn nguyên hộp và chưa kích hoạt bảo hành điện tử."
        if "cuối tuần" in lowered or "cuoi tuan" in lowered:
            return "Shop vẫn giao hàng cuối tuần tại Hà Nội và TP.HCM. Một số khu vực khác sẽ xử lý vào ngày làm việc tiếp theo."
        return (
            "Đây là phản hồi từ mock provider. "
            "Với câu hỏi cần tính giá, tồn kho, coupon hoặc ship, hãy dùng compare mode để xem thêm kết quả v2."
        )

    def _generate_react_response(self, prompt: str) -> str:
        user_message = self._extract_user_message(prompt)
        observations = self._extract_observations(prompt)
        product_name = self._detect_product(user_message)
        quantity = self._detect_quantity(user_message)
        coupon_code = self._detect_coupon(user_message)
        destination_city = self._detect_city(user_message)

        lowered = user_message.lower()
        if "đổi trả" in lowered or "doi tra" in lowered:
            return (
                "Thought: Câu hỏi này thuộc FAQ nhưng agent hiện không có tool FAQ.\n"
                "Final Answer: Tôi chưa có tool FAQ để xác minh chính sách đổi trả trong chế độ agent. "
                "Bạn có thể xem câu trả lời từ v1 để lấy nội dung FAQ đã grounding."
            )
        if "cuối tuần" in lowered or "cuoi tuan" in lowered:
            return (
                "Thought: Câu hỏi này thuộc FAQ nhưng agent hiện không có tool FAQ.\n"
                "Final Answer: Tôi chưa có tool FAQ để xác minh chính sách giao hàng cuối tuần trong chế độ agent. "
                "Bạn có thể xem câu trả lời từ v1 để lấy nội dung FAQ đã grounding."
            )
        if not product_name:
            return (
                "Thought: Tôi không xác định được sản phẩm cụ thể từ câu hỏi này.\n"
                "Final Answer: Tôi chưa xác định được sản phẩm để tính giá hoặc kiểm tra kho. "
                "Bạn hãy nêu rõ tên sản phẩm như iPhone 15 hoặc MacBook Air M3."
            )

        if "get_product_price" not in observations:
            return (
                "Thought: Tôi cần lấy đơn giá sản phẩm trước.\n"
                f"Action: get_product_price\nAction Input: {json.dumps({'product_name': product_name}, ensure_ascii=False)}"
            )

        if self._needs_stock_check(user_message) and "check_stock" not in observations:
            return (
                "Thought: Tôi cần kiểm tra tồn kho cho số lượng người dùng yêu cầu.\n"
                f"Action: check_stock\nAction Input: {json.dumps({'product_name': product_name, 'quantity': quantity}, ensure_ascii=False)}"
            )

        subtotal = self._get_subtotal(observations, quantity)
        if coupon_code and "get_coupon_discount" not in observations and subtotal is not None:
            return (
                "Thought: Tôi cần kiểm tra coupon trên subtotal hiện tại.\n"
                "Action: get_coupon_discount\n"
                f"Action Input: {json.dumps({'coupon_code': coupon_code, 'order_subtotal': subtotal}, ensure_ascii=False)}"
            )

        if destination_city and "calc_shipping" not in observations:
            weight = self._get_weight(product_name, quantity)
            return (
                "Thought: Tôi cần tính phí vận chuyển theo thành phố và cân nặng.\n"
                "Action: calc_shipping\n"
                f"Action Input: {json.dumps({'destination_city': destination_city, 'total_weight_kg': weight}, ensure_ascii=False)}"
            )

        return (
            "Thought: Tôi đã có đủ dữ liệu từ tools để tổng hợp câu trả lời cuối cùng.\n"
            f"Final Answer: {self._build_final_answer(product_name, quantity, coupon_code, destination_city, observations)}"
        )

    def _extract_user_message(self, prompt: str) -> str:
        match = re.search(r"User:\s*(.*)", prompt)
        return match.group(1).strip() if match else prompt.strip()

    def _extract_observations(self, prompt: str) -> Dict[str, Any]:
        observations: Dict[str, Any] = {}
        action_names = re.findall(r"Action:\s*([^\n]+)", prompt)
        action_inputs = re.findall(r"Action Input:\s*(?:```(?:json)?\s*)?(\{.*?\})(?:\s*```)?", prompt, flags=re.DOTALL)
        observation_values = re.findall(r"Observation:\s*(.*)", prompt)

        for action_name, action_input, observation in zip(action_names, action_inputs, observation_values):
            try:
                parsed_input = json.loads(action_input)
            except json.JSONDecodeError:
                parsed_input = {}
            payload: Any = observation
            if observation.startswith("{") and observation.endswith("}"):
                try:
                    payload = json.loads(observation)
                except json.JSONDecodeError:
                    payload = observation
            observations[action_name.strip()] = {"input": parsed_input, "output": payload}
        return observations

    def _detect_product(self, message: str) -> Optional[str]:
        lowered = message.lower()
        for name in ("iPhone 15", "MacBook Air M3", "AirPods Pro 2", "Samsung S24"):
            if name.lower() in lowered:
                return name
        return None

    def _detect_quantity(self, message: str) -> int:
        match = re.search(r"(\d+)", message)
        return int(match.group(1)) if match else 1

    def _detect_coupon(self, message: str) -> Optional[str]:
        match = re.search(r"\b([A-Z0-9]{4,12})\b", message)
        return match.group(1) if match else None

    def _detect_city(self, message: str) -> Optional[str]:
        lowered = message.lower()
        for city in ("Hà Nội", "TP.HCM", "Đà Nẵng"):
            if city.lower() in lowered:
                return city
        return None

    def _needs_stock_check(self, message: str) -> bool:
        lowered = message.lower()
        return any(keyword in lowered for keyword in ("mua", "còn hàng", "con hang", "tổng", "tong"))

    def _get_subtotal(self, observations: Dict[str, Any], quantity: int) -> Optional[int]:
        price_data = observations.get("get_product_price", {}).get("output")
        if not isinstance(price_data, dict):
            return None
        return int(price_data.get("unit_price", 0)) * quantity

    def _get_weight(self, product_name: str, quantity: int) -> float:
        weights = {
            "iPhone 15": 0.5,
            "Samsung S24": 0.5,
            "MacBook Air M3": 1.3,
            "AirPods Pro 2": 0.2,
        }
        return weights.get(product_name, 0.5) * quantity

    def _build_final_answer(
        self,
        product_name: str,
        quantity: int,
        coupon_code: Optional[str],
        destination_city: Optional[str],
        observations: Dict[str, Any],
    ) -> str:
        price_data = observations.get("get_product_price", {}).get("output", {})
        stock_data = observations.get("check_stock", {}).get("output", {})
        coupon_data = observations.get("get_coupon_discount", {}).get("output")
        shipping_data = observations.get("calc_shipping", {}).get("output", {})

        unit_price = int(price_data.get("unit_price", 0))
        subtotal = unit_price * quantity
        shipping_fee = int(shipping_data.get("shipping_fee", 0))
        discount_amount = 0
        coupon_note = "Không áp dụng coupon."

        if isinstance(coupon_data, dict):
            discount_amount = int(coupon_data.get("discount_amount", 0))
            coupon_note = f"Coupon {coupon_code} giảm {discount_amount:,} VND."
        elif coupon_code:
            coupon_note = f"Coupon {coupon_code} không hợp lệ hoặc không tồn tại."

        stock_note = ""
        if isinstance(stock_data, dict):
            stock_note = (
                f" Tồn kho hiện tại: {stock_data.get('available_quantity', 0)}. "
                f"Khả dụng cho {quantity} sản phẩm: {'có' if stock_data.get('in_stock') else 'không'}."
            )

        shipping_note = ""
        if destination_city and isinstance(shipping_data, dict):
            shipping_note = (
                f" Phí ship đến {destination_city}: {shipping_fee:,} VND, "
                f"dự kiến {shipping_data.get('estimated_days', '?')} ngày."
            )

        total = subtotal - discount_amount + shipping_fee
        return (
            f"{product_name} có đơn giá {unit_price:,} VND. "
            f"Subtotal cho {quantity} sản phẩm là {subtotal:,} VND."
            f"{stock_note} {coupon_note}{shipping_note} "
            f"Tổng thanh toán dự kiến: {total:,} VND."
        )
