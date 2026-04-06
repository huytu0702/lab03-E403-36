import math
from typing import Any, Dict

from src.services.product_service import product_service
from src.services.seed_data import COUPONS, SHIPPING_RULES


class QuoteService:
    def get_price(self, product_name: str) -> Dict[str, Any]:
        product = product_service.get_product(product_name)
        if not product:
            raise ValueError("PRODUCT_NOT_FOUND")
        return {"product_name": product["name"], "unit_price": product["price"], "currency": "VND"}

    def check_stock(self, product_name: str, quantity: int) -> Dict[str, Any]:
        product = product_service.get_product(product_name)
        if not product:
            raise ValueError("PRODUCT_NOT_FOUND")
        return {
            "product_name": product["name"],
            "requested_quantity": quantity,
            "available_quantity": product["stock"],
            "in_stock": product["stock"] >= quantity,
        }

    def get_coupon_discount(self, coupon_code: str, order_subtotal: int) -> Dict[str, Any]:
        coupon = next((item for item in COUPONS if item["code"].lower() == coupon_code.lower()), None)
        if not coupon or not coupon["is_active"]:
            raise ValueError("COUPON_NOT_FOUND")
        if order_subtotal < coupon["min_order_value"]:
            raise ValueError("COUPON_INVALID")

        if coupon["discount_type"] == "percent":
            discount_amount = int(order_subtotal * coupon["discount_value"] / 100)
        else:
            discount_amount = int(coupon["discount_value"])

        max_discount = coupon.get("max_discount")
        if max_discount:
            discount_amount = min(discount_amount, int(max_discount))

        return {
            "coupon_code": coupon["code"],
            "is_valid": True,
            "discount_type": coupon["discount_type"],
            "discount_value": coupon["discount_value"],
            "discount_amount": discount_amount,
        }

    def calc_shipping(self, destination_city: str, total_weight_kg: float) -> Dict[str, Any]:
        rule = next((item for item in SHIPPING_RULES if item["city"].lower() == destination_city.lower()), None)
        if not rule:
            raise ValueError("SHIPPING_RULE_NOT_FOUND")
        shipping_fee = int(rule["base_fee"] + math.ceil(total_weight_kg) * rule["fee_per_kg"])
        return {
            "destination_city": rule["city"],
            "shipping_fee": shipping_fee,
            "estimated_days": rule["estimated_days"],
        }


quote_service = QuoteService()
