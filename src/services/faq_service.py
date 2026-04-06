from typing import Any, Dict, List

from sqlalchemy.orm import Session

from src.repositories.catalog_repo import catalog_repo


class FAQService:
    def list_faqs(self, db: Session) -> List[Dict[str, Any]]:
        return catalog_repo.list_faqs(db)

    def match(self, db: Session, message: str) -> Dict[str, Any] | None:
        return catalog_repo.match_faq(db, message)


faq_service = FAQService()
