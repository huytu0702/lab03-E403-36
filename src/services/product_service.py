from typing import Any, Dict, List

from sqlalchemy.orm import Session

from src.repositories.catalog_repo import catalog_repo


class ProductService:
    def list_products(self, db: Session, query: str | None = None) -> List[Dict[str, Any]]:
        return catalog_repo.list_products(db, query=query)

    def get_product(self, db: Session, product_name: str) -> Dict[str, Any] | None:
        return catalog_repo.get_product_by_name(db, product_name)

    def detect_product_in_text(self, db: Session, text: str) -> Dict[str, Any] | None:
        return catalog_repo.detect_product_in_text(db, text)


product_service = ProductService()
