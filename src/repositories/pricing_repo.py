from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db import models


class PricingRepository:
    def get_coupon(self, db: Session, coupon_code: str) -> models.Coupon | None:
        return (
            db.execute(
                select(models.Coupon).where(models.Coupon.code.ilike(coupon_code.strip())).limit(1)
            )
            .scalars()
            .first()
        )

    def get_shipping_rule(self, db: Session, destination_city: str) -> models.ShippingRule | None:
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

    def coupon_to_dict(self, coupon: models.Coupon) -> Dict[str, Any]:
        return {
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value),
            "min_order_value": int(Decimal(coupon.min_order_value)),
            "max_discount": int(Decimal(coupon.max_discount)) if coupon.max_discount is not None else None,
            "is_active": bool(coupon.is_active),
            "expires_at": coupon.expires_at.isoformat() if coupon.expires_at else None,
        }


pricing_repo = PricingRepository()

