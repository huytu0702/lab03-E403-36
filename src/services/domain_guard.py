from __future__ import annotations

import re
from typing import Final

import src.db.session as db_session
from src.core.text import normalize_text
from src.services.faq_service import faq_service
from src.services.product_service import product_service


DOMAIN_KEYWORDS: Final[tuple[str, ...]] = (
    "mua",
    "dat hang",
    "don hang",
    "san pham",
    "dien thoai",
    "laptop",
    "tai nghe",
    "bao nhieu",
    "ton kho",
    "con hang",
    "coupon",
    "ma giam gia",
    "giam gia",
    "khuyen mai",
    "ship",
    "giao hang",
    "phi ship",
    "van chuyen",
    "doi tra",
    "bao hanh",
    "thanh toan",
)

ASSISTANT_KEYWORDS: Final[tuple[str, ...]] = (
    "ban la ai",
    "ban lam duoc gi",
    "ban ho tro gi",
    "huong dan su dung",
    "tro giup",
    "help",
)


class DomainGuard:
    def _contains_keyword(self, normalized: str, keyword: str) -> bool:
        return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", normalized) is not None

    def is_in_domain(self, message: str) -> bool:
        normalized = normalize_text(message)
        if not normalized:
            return False

        if any(self._contains_keyword(normalized, keyword) for keyword in ASSISTANT_KEYWORDS):
            return True

        db = db_session.SessionLocal()
        try:
            if faq_service.match(db, message):
                return True
            if product_service.detect_product_in_text(db, message):
                return True
        finally:
            db.close()

        return any(self._contains_keyword(normalized, keyword) for keyword in DOMAIN_KEYWORDS)

    def rejection_message(self) -> str:
        return (
            "Tôi chỉ hỗ trợ câu hỏi liên quan đến cửa hàng điện tử trong bài lab này, "
            "ví dụ sản phẩm, giá, tồn kho, mã giảm giá, giao hàng, đổi trả hoặc bảo hành."
        )


domain_guard = DomainGuard()
