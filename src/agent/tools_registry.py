import json
from typing import Any, Callable, Dict, List

from src.services.quote_service import quote_service


def _tool_spec(name: str, description: str, handler: Callable[..., Dict[str, Any]]) -> Dict[str, Any]:
    return {"name": name, "description": description, "handler": handler}


def get_tools() -> List[Dict[str, Any]]:
    return [
        _tool_spec(
            "get_product_price",
            "Get the unit price for a product. Args: product_name.",
            lambda product_name: quote_service.get_price(product_name),
        ),
        _tool_spec(
            "check_stock",
            "Check whether a requested quantity is available. Args: product_name, quantity.",
            lambda product_name, quantity: quote_service.check_stock(product_name, int(quantity)),
        ),
        _tool_spec(
            "get_coupon_discount",
            "Validate a coupon and compute discount amount. Args: coupon_code, order_subtotal.",
            lambda coupon_code, order_subtotal: quote_service.get_coupon_discount(coupon_code, int(order_subtotal)),
        ),
        _tool_spec(
            "calc_shipping",
            "Calculate shipping fee by city and weight. Args: destination_city, total_weight_kg.",
            lambda destination_city, total_weight_kg: quote_service.calc_shipping(destination_city, float(total_weight_kg)),
        ),
    ]


def render_tool_descriptions(tools: List[Dict[str, Any]]) -> str:
    return "\n".join(f"- {tool['name']}: {tool['description']}" for tool in tools)


def preview_result(result: Dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False)
