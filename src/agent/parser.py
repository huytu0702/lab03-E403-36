import re
from typing import Any, Dict

from src.core.text import normalize_text
from src.services.product_service import product_service


def extract_quantity(message: str) -> int:
    match = re.search(r"(\d+)", message)
    return int(match.group(1)) if match else 1


def extract_coupon(message: str) -> str | None:
    match = re.search(r"\b([A-Z0-9]{4,12})\b", message)
    return match.group(1) if match else None


def extract_city(message: str) -> str | None:
    normalized_message = normalize_text(message)
    for city in ("Hà Nội", "TP.HCM", "Đà Nẵng"):
        if normalize_text(city) in normalized_message:
            return city
    return None


def extract_product(message: str) -> Dict[str, Any] | None:
    return product_service.detect_product_in_text(message)
