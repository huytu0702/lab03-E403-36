from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.core.text import normalize_text
from src.db import models
from src.db.session import is_database_available
from src.services import seed_data


def _as_namespace(data: Dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(**data)


class PricingRepository:
    def get_coupon(self, db: Session, coupon_code: str) -> models.Coupon | SimpleNamespace | None:
        if is_database_available():
            try:
                return (
                    db.execute(
                        select(models.Coupon).where(models.Coupon.code.ilike(coupon_code.strip())).limit(1)
                    )
                    .scalars()
                    .first()
                )
            except SQLAlchemyError:
                pass

        target = coupon_code.strip().lower()
        for coupon in seed_data.COUPONS:
            if coupon["code"].lower() == target:
                return _as_namespace(dict(coupon))
        return None

    def get_shipping_rule(self, db: Session, destination_city: str) -> models.ShippingRule | SimpleNamespace | None:
        if is_database_available():
            try:
                return (
                    db.execute(
                        select(models.ShippingRule)
                        .where(models.ShippingRule.city.ilike(destination_city.strip()))
                        .where(models.ShippingRule.is_active.is_(True))
                        .limit(1)
                    )
                    .scalars()
                    .first()
                )
            except SQLAlchemyError:
                pass

        target = normalize_text(destination_city)
        for rule in seed_data.SHIPPING_RULES:
            if normalize_text(rule["city"]) == target:
                fallback_rule = dict(rule)
                fallback_rule["is_active"] = True
                return _as_namespace(fallback_rule)
        return None

    def coupon_to_dict(self, coupon: models.Coupon | SimpleNamespace | Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(coupon, dict):
            data = coupon
            return {
                "code": data["code"],
                "discount_type": data["discount_type"],
                "discount_value": float(data["discount_value"]),
                "min_order_value": int(Decimal(data["min_order_value"])),
                "max_discount": int(Decimal(data["max_discount"])) if data.get("max_discount") is not None else None,
                "is_active": bool(data.get("is_active", True)),
                "expires_at": data.get("expires_at"),
            }

        return {
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value),
            "min_order_value": int(Decimal(coupon.min_order_value)),
            "max_discount": int(Decimal(coupon.max_discount)) if coupon.max_discount is not None else None,
            "is_active": bool(getattr(coupon, "is_active", True)),
            "expires_at": coupon.expires_at.isoformat() if getattr(coupon, "expires_at", None) else None,
        }


pricing_repo = PricingRepository()

