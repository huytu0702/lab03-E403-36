import math
from typing import Any, Dict

from sqlalchemy.orm import Session

from src.repositories.pricing_repo import pricing_repo
from src.services.product_service import product_service


class QuoteService:
    def get_price(self, db: Session, product_name: str) -> Dict[str, Any]:
        product = product_service.get_product(db, product_name)
        if not product:
            raise ValueError("PRODUCT_NOT_FOUND")
        return {"product_name": product["name"], "unit_price": product["price"], "currency": "VND"}

    def check_stock(self, db: Session, product_name: str, quantity: int) -> Dict[str, Any]:
        product = product_service.get_product(db, product_name)
        if not product:
            raise ValueError("PRODUCT_NOT_FOUND")
        return {
            "product_name": product["name"],
            "requested_quantity": quantity,
            "available_quantity": product["stock"],
            "in_stock": product["stock"] >= quantity,
        }

    def get_coupon_discount(self, db: Session, coupon_code: str, order_subtotal: int) -> Dict[str, Any]:
        coupon = pricing_repo.get_coupon(db, coupon_code)
        if not coupon or not coupon.is_active:
            raise ValueError("COUPON_NOT_FOUND")
        if order_subtotal < int(coupon.min_order_value):
            raise ValueError("COUPON_INVALID")

        if coupon.discount_type == "percent":
            discount_amount = int(order_subtotal * float(coupon.discount_value) / 100)
        else:
            discount_amount = int(float(coupon.discount_value))

        if coupon.max_discount is not None:
            discount_amount = min(discount_amount, int(coupon.max_discount))

        return {
            "coupon_code": coupon.code,
            "is_valid": True,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value),
            "discount_amount": discount_amount,
        }

    def calc_shipping(self, db: Session, destination_city: str, total_weight_kg: float) -> Dict[str, Any]:
        rule = pricing_repo.get_shipping_rule(db, destination_city)
        if not rule:
            raise ValueError("SHIPPING_RULE_NOT_FOUND")
        shipping_fee = int(float(rule.base_fee) + math.ceil(total_weight_kg) * float(rule.fee_per_kg))
        return {
            "destination_city": rule.city,
            "shipping_fee": shipping_fee,
            "estimated_days": int(rule.estimated_days),
        }


quote_service = QuoteService()
