from typing import Any, Dict, List

from src.core.text import normalize_text
from src.services.seed_data import PRODUCTS


class ProductService:
    def list_products(self, query: str | None = None) -> List[Dict[str, Any]]:
        if not query:
            return PRODUCTS
        query_lower = query.lower()
        return [product for product in PRODUCTS if query_lower in product["name"].lower()]

    def get_product(self, product_name: str) -> Dict[str, Any] | None:
        target = normalize_text(product_name)
        for product in PRODUCTS:
            if normalize_text(product["name"]) == target:
                return product
        return None

    def detect_product_in_text(self, text: str) -> Dict[str, Any] | None:
        text_normalized = normalize_text(text)
        for product in PRODUCTS:
            if normalize_text(product["name"]) in text_normalized:
                return product
        return None


product_service = ProductService()
