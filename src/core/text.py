import re
import unicodedata


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.casefold())
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    without_marks = without_marks.replace("đ", "d")
    return re.sub(r"\s+", " ", without_marks).strip()
