from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from src.core.text import normalize_text
from src.db import models


def _product_row_to_dict(row: Any) -> Dict[str, Any]:
    product: models.Product = row[0]
    inventory: models.Inventory | None = row[1]
    stock = int(inventory.quantity_available) if inventory else 0
    return {
        "id": int(product.id),
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "price": int(Decimal(product.price)),
        "weight_kg": float(product.weight_kg),
        "stock": stock,
        "description": product.description,
        "is_active": bool(product.is_active),
    }


class CatalogRepository:
    def list_products(self, db: Session, query: Optional[str] = None) -> List[Dict[str, Any]]:
        stmt: Select = (
            select(models.Product, models.Inventory)
            .join(models.Inventory, models.Inventory.product_id == models.Product.id, isouter=True)
            .where(models.Product.is_active.is_(True))
            .order_by(models.Product.id.asc())
        )
        if query:
            q = f"%{query.strip()}%"
            stmt = stmt.where(func.lower(models.Product.name).like(func.lower(q)))
        rows = db.execute(stmt).all()
        return [_product_row_to_dict(row) for row in rows]

    def get_product_by_name(self, db: Session, product_name: str) -> Dict[str, Any] | None:
        target = normalize_text(product_name)
        stmt = (
            select(models.Product, models.Inventory)
            .join(models.Inventory, models.Inventory.product_id == models.Product.id, isouter=True)
            .where(models.Product.is_active.is_(True))
        )
        for row in db.execute(stmt).all():
            product_dict = _product_row_to_dict(row)
            if normalize_text(product_dict["name"]) == target:
                return product_dict
        return None

    def detect_product_in_text(self, db: Session, text: str) -> Dict[str, Any] | None:
        text_normalized = normalize_text(text)
        stmt = (
            select(models.Product, models.Inventory)
            .join(models.Inventory, models.Inventory.product_id == models.Product.id, isouter=True)
            .where(models.Product.is_active.is_(True))
        )
        for row in db.execute(stmt).all():
            product_dict = _product_row_to_dict(row)
            if normalize_text(product_dict["name"]) in text_normalized:
                return product_dict
        return None

    def list_faqs(self, db: Session) -> List[Dict[str, Any]]:
        faqs = (
            db.execute(
                select(models.FAQ).where(models.FAQ.is_active.is_(True)).order_by(models.FAQ.id.asc())
            )
            .scalars()
            .all()
        )
        return [{"id": int(f.id), "topic": f.topic, "question": f.question, "answer": f.answer} for f in faqs]

    def match_faq(self, db: Session, message: str) -> Dict[str, Any] | None:
        text = normalize_text(message)
        faqs = self.list_faqs(db)
        for faq in faqs:
            question = normalize_text(faq["question"])
            topic = normalize_text(faq["topic"].replace("_", " "))
            if question in text or topic in text:
                return faq
        # Lightweight heuristics for Vietnamese phrasing
        if "doi tra" in text and faqs:
            return next((f for f in faqs if f["topic"] == "return_policy"), faqs[0])
        if ("cuoi tuan" in text or "giao hang" in text) and faqs:
            return next((f for f in faqs if f["topic"] == "weekend_shipping"), faqs[min(1, len(faqs) - 1)])
        if "bao hanh" in text and faqs:
            return next((f for f in faqs if f["topic"] == "warranty"), faqs[min(2, len(faqs) - 1)])
        return None


catalog_repo = CatalogRepository()

