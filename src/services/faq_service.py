from typing import Any, Dict, List

from src.core.text import normalize_text
from src.services.seed_data import FAQS


class FAQService:
    def list_faqs(self) -> List[Dict[str, Any]]:
        return FAQS

    def match(self, message: str) -> Dict[str, Any] | None:
        text = normalize_text(message)
        for faq in FAQS:
            question = normalize_text(faq["question"])
            topic = normalize_text(faq["topic"].replace("_", " "))
            if question in text or topic in text:
                return faq
        if "doi tra" in text:
            return FAQS[0]
        if "cuoi tuan" in text or "giao hang" in text:
            return FAQS[1]
        if "bao hanh" in text:
            return FAQS[2]
        return None


faq_service = FAQService()
