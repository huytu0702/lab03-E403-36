import json
import re
from typing import Any, Dict

from src.core.text import normalize_text
from src.db.session import SessionLocal
from src.services.faq_service import faq_service
from src.services.product_service import product_service


def extract_quantity(message: str) -> int:
    patterns = [
        r"\bmua\s+(\d+)\b",
        r"\b(\d+)\s+(?:cái|cai|chiếc|chiec|sản phẩm|san pham|con|item)\b",
        r"\bquantity\s*(\d+)\b",
    ]
    lowered = normalize_text(message)
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            return int(match.group(1))
    return 1


def extract_coupon(message: str) -> str | None:
    match = re.search(r"\b([A-Z0-9]{4,12})\b", message)
    return match.group(1) if match else None


def extract_city(message: str) -> str | None:
    normalized_message = normalize_text(message)
    city_aliases = {
        "Hà Nội": ["ha noi", "hanoi", "h? n?i"],
        "TP.HCM": ["tp.hcm", "tp hcm", "ho chi minh", "hcm", "tp.ho chi minh"],
        "Đà Nẵng": ["da nang", "danang", "?? nang", "?? n?ng"],
    }
    for city, aliases in city_aliases.items():
        if any(alias in normalized_message for alias in aliases):
            return city
    return None


def extract_product(message: str) -> Dict[str, Any] | None:
    db = SessionLocal()
    try:
        return product_service.detect_product_in_text(db, message)
    finally:
        db.close()


def extract_faq(message: str) -> Dict[str, Any] | None:
    db = SessionLocal()
    try:
        return faq_service.match(db, message)
    finally:
        db.close()


def parse_react_response(text: str) -> Dict[str, Any]:
    """
    Parse a single ReAct step.
    Priority:
    - If both Action and Final Answer exist, keep both metadata but let caller decide.
    - Only the first Action block is parsed. Extra blocks are reported via metadata.
    """

    result: Dict[str, Any] = {
        "thought": None,
        "action": None,
        "final_answer": None,
        "has_mixed_output": False,
        "action_count": 0,
    }

    thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)", text, re.DOTALL)
    if thought_match:
        result["thought"] = thought_match.group(1).strip()

    action_matches = list(re.finditer(r"Action:\s*([^\n]+)", text))
    result["action_count"] = len(action_matches)
    final_answer_match = re.search(r"Final Answer:\s*(.*)", text, re.DOTALL)

    if final_answer_match:
        result["final_answer"] = final_answer_match.group(1).strip()

    if action_matches:
        action_match = action_matches[0]
        tool_name = action_match.group(1).strip()

        action_input_match = re.search(
            r"Action Input:\s*(?:```(?:json)?\s*)?(\{.*?\})(?:\s*```)?(?=\s*(?:Observation:|Thought:|Action:|Final Answer:|$))",
            text[action_match.end() :],
            re.DOTALL,
        )
        if not action_input_match:
            raise ValueError("Action found but Action Input is missing or invalid.")

        try:
            args = json.loads(action_input_match.group(1))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Action Input contains invalid JSON: {action_input_match.group(1)}") from exc

        result["action"] = (tool_name, args)

    result["has_mixed_output"] = bool(result["action"] and result["final_answer"])
    return result
