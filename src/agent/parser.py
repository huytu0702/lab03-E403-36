import re
import json
from typing import Any, Dict, Optional, Tuple

from src.core.text import normalize_text
from src.db.session import SessionLocal
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
    db = SessionLocal()
    try:
        return product_service.detect_product_in_text(db, message)
    finally:
        db.close()


def parse_react_response(text: str) -> Dict[str, Any]:
    """
    Parses a ReAct LLM response and extracts Thought, Action (and its JSON args), and Final Answer.
    """
    result: Dict[str, Any] = {
        "thought": None,
        "action": None,
        "final_answer": None
    }
    
    # Extract Thought
    thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)", text, re.DOTALL)
    if thought_match:
        result["thought"] = thought_match.group(1).strip()
        
    # Extract Final Answer
    final_answer_match = re.search(r"Final Answer:\s*(.*)", text, re.DOTALL)
    if final_answer_match:
        result["final_answer"] = final_answer_match.group(1).strip()
        return result
        
    # Extract Action and Action Input
    action_match = re.search(r"Action:\s*([^\n]+)", text)
    action_input_match = re.search(r"Action Input:\s*(?:```(?:json)?\s*)?(\{.*?\})(?:\s*```)?", text, re.DOTALL)
    
    if action_match and action_input_match:
        tool_name = action_match.group(1).strip()
        try:
            json_str = action_input_match.group(1)
            args = json.loads(json_str)
            result["action"] = (tool_name, args)
        except json.JSONDecodeError:
            raise ValueError(f"Action Input contains invalid JSON: {action_input_match.group(1)}")
            
    return result
