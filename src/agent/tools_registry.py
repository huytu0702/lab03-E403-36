import json
from typing import Any, Callable, Dict, List

from src.db.session import SessionLocal
from src.services.faq_service import faq_service
from src.services.quote_service import quote_service


def _tool_spec(name: str, description: str, handler: Callable[..., Dict[str, Any]]) -> Dict[str, Any]:
    return {"name": name, "description": description, "handler": handler}


def get_tools() -> List[Dict[str, Any]]:
    return [
        _tool_spec(
            "get_faq_answer",
            "Get a grounded FAQ answer from the knowledge base. Args: user_message.",
            lambda user_message: _with_db(lambda db: _faq_answer(db, user_message)),
        ),
        _tool_spec(
            "get_product_price",
            "Get the unit price for a product. Args: product_name.",
            lambda product_name: _with_db(lambda db: quote_service.get_price(db, product_name)),
        ),
        _tool_spec(
            "check_stock",
            "Check whether a requested quantity is available. Args: product_name, quantity.",
            lambda product_name, quantity: _with_db(lambda db: quote_service.check_stock(db, product_name, int(quantity))),
        ),
        _tool_spec(
            "get_coupon_discount",
            "Validate a coupon and compute discount amount. Args: coupon_code, order_subtotal.",
            lambda coupon_code, order_subtotal: _with_db(
                lambda db: quote_service.get_coupon_discount(db, coupon_code, int(order_subtotal))
            ),
        ),
        _tool_spec(
            "calc_shipping",
            "Calculate shipping fee by city and weight. Args: destination_city, total_weight_kg.",
            lambda destination_city, total_weight_kg: _with_db(
                lambda db: quote_service.calc_shipping(db, destination_city, float(total_weight_kg))
            ),
        ),
    ]


def _with_db(fn: Callable[[Any], Dict[str, Any]]) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        return fn(db)
    finally:
        db.close()


def _faq_answer(db: Any, user_message: str) -> Dict[str, Any]:
    faq = faq_service.match(db, user_message)
    if not faq:
        raise ValueError("FAQ_NOT_FOUND")
    return {"topic": faq["topic"], "question": faq["question"], "answer": faq["answer"]}


def render_tool_descriptions(tools: List[Dict[str, Any]]) -> str:
    return "\n".join(f"- {tool['name']}: {tool['description']}" for tool in tools)


def preview_result(result: Dict[str, Any]) -> str:
    return json.dumps(result, ensure_ascii=False)
