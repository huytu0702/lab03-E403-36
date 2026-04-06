from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.agent.agent import agent
from src.agent.parser import extract_city, extract_quantity
from src.core.llm_provider import LLMProvider


class ScriptedProvider(LLMProvider):
    def __init__(self, responses: List[str]):
        super().__init__(model_name="scripted-test", provider_name="scripted")
        self.responses = responses
        self.index = 0

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if self.index >= len(self.responses):
            content = "Thought: Tôi đã hết script.\nFinal Answer: Script exhausted."
        else:
            content = self.responses[self.index]
        self.index += 1
        return {
            "content": content,
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            "latency_ms": 0,
            "provider": "scripted",
            "model": self.model_name,
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None):
        yield self.generate(prompt, system_prompt)["content"]


def test_agent_requires_faq_tool_before_final_answer(client, monkeypatch):
    provider = ScriptedProvider(
        [
            "Thought: Tôi có thể tự trả lời câu hỏi này.\nFinal Answer: Chính sách đổi trả tùy cửa hàng.",
            'Thought: Tôi cần lấy FAQ đã grounding.\nAction: get_faq_answer\nAction Input: {"user_message": "Chính sách đổi trả là gì?"}',
        ]
    )
    monkeypatch.setattr(agent, "llm", provider)

    response = client.post("/api/v1/chat", json={"message": "Chính sách đổi trả là gì?", "version": "v2"})
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "7 ngày" in data["answer"]
    assert data["tool_calls"][0]["tool"] == "get_faq_answer"
    assert any(step["status"] == "insufficient_grounding" for step in data["reasoning_steps"])


def test_agent_ignores_mixed_final_answer_and_waits_for_missing_tools(client, monkeypatch):
    provider = ScriptedProvider(
        [
            'Thought: Lấy giá trước.\nAction: get_product_price\nAction Input: {"product_name": "iPhone 15"}',
            'Thought: Kiểm tra tồn kho.\nAction: check_stock\nAction Input: {"product_name": "iPhone 15", "quantity": 2}',
            (
                'Thought: Tiếp tục tính coupon và ship.\n'
                'Action: get_coupon_discount\n'
                'Action Input: {"coupon_code": "WINNER10", "order_subtotal": 49980000}\n'
                'Action: calc_shipping\n'
                'Action Input: {"destination_city": "Hà Nội", "total_weight_kg": 1.0}\n'
                'Final Answer: Tổng là 44,932,000 VND.'
            ),
            'Thought: Tính ship.\nAction: calc_shipping\nAction Input: {"destination_city": "Hà Nội", "total_weight_kg": 1.0}',
        ]
    )
    monkeypatch.setattr(agent, "llm", provider)

    response = client.post(
        "/api/v1/chat",
        json={"message": "Tôi muốn mua 2 iPhone 15, dùng mã WINNER10 và ship Hà Nội. Tổng bao nhiêu?", "version": "v2"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "47,020,000 VND" in data["answer"]
    assert [call["tool"] for call in data["tool_calls"]] == [
        "get_product_price",
        "check_stock",
        "get_coupon_discount",
        "calc_shipping",
    ]
    assert any(step.get("parser_note") for step in data["reasoning_steps"])


def test_agent_uses_grounded_coupon_error_instead_of_hallucinating_discount(client, monkeypatch):
    provider = ScriptedProvider(
        [
            'Thought: Lấy giá.\nAction: get_product_price\nAction Input: {"product_name": "AirPods Pro 2"}',
            'Thought: Kiểm kho.\nAction: check_stock\nAction Input: {"product_name": "AirPods Pro 2", "quantity": 3}',
            (
                'Thought: Kiểm coupon trước.\n'
                'Action: get_coupon_discount\n'
                'Action Input: {"coupon_code": "SAVE999", "order_subtotal": 16470000}\n'
                'Final Answer: Coupon hợp lệ và được giảm 1,647,000 VND.'
            ),
            'Thought: Tính ship.\nAction: calc_shipping\nAction Input: {"destination_city": "Đà Nẵng", "total_weight_kg": 0.6}',
        ]
    )
    monkeypatch.setattr(agent, "llm", provider)

    response = client.post(
        "/api/v1/chat",
        json={"message": "Mua 3 AirPods Pro 2 dùng mã SAVE999 ship Đà Nẵng.", "version": "v2"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "SAVE999 không hợp lệ hoặc không tồn tại" in data["answer"]
    assert "16,525,000 VND" in data["answer"]
    assert [call["tool"] for call in data["tool_calls"]] == [
        "get_product_price",
        "check_stock",
        "calc_shipping",
    ]
    shipping_call = next(call for call in data["tool_calls"] if call["tool"] == "calc_shipping")
    assert shipping_call["args"]["total_weight_kg"] == 0.6


def test_extractors_do_not_confuse_model_numbers_with_quantity():
    assert extract_quantity("MacBook Air M3 còn hàng không? Nếu mua 1 cái ship TP.HCM thì hết bao nhiêu?") == 1
    assert extract_quantity("Mua 3 AirPods Pro 2 dùng mã SAVE999 ship Đà Nẵng.") == 3
    assert extract_city("Toi muon mua 2 iPhone 15, dung ma WINNER10 va ship Ha Noi.") == "Hà Nội"
    assert extract_city("Mua 3 AirPods Pro 2 dung ma SAVE999 ship Da Nang.") == "Đà Nẵng"


def test_agent_forces_next_missing_tool_when_model_repeats_successful_tool(client, monkeypatch):
    provider = ScriptedProvider(
        [
            'Thought: Lay gia.\nAction: get_product_price\nAction Input: {"product_name": "iPhone 15"}',
            'Thought: Kiem kho.\nAction: check_stock\nAction Input: {"product_name": "iPhone 15", "quantity": 2}',
            'Thought: Giam gia.\nAction: get_coupon_discount\nAction Input: {"coupon_code": "WINNER10", "order_subtotal": 49980000}',
            'Thought: Toi muon kiem tra lai giam gia.\nAction: get_coupon_discount\nAction Input: {"coupon_code": "WINNER10", "order_subtotal": 49980000}',
        ]
    )
    monkeypatch.setattr(agent, "llm", provider)

    response = client.post(
        "/api/v1/chat",
        json={"message": "Tôi muốn mua 2 iPhone 15, dùng mã WINNER10 và ship Hà Nội. Tổng bao nhiêu?", "version": "v2"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "47,020,000 VND" in data["answer"]
    assert [call["tool"] for call in data["tool_calls"]] == [
        "get_product_price",
        "check_stock",
        "get_coupon_discount",
        "calc_shipping",
    ]
    assert any("Forced next missing tool" in step.get("planner_note", "") for step in data["reasoning_steps"])
