import json
import unicodedata
from pathlib import Path


MOCK_WIKIPEDIA_PATH = Path(__file__).resolve().parent / "mock_data" / "wikipedia_articles.json"


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    without_accents = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_accents.lower().strip()


def wikipedia_lookup(topic: str) -> str:
    """Tra cuu bai viet Wikipedia mock theo topic."""
    try:
        with MOCK_WIKIPEDIA_PATH.open("r", encoding="utf-8") as file:
            mock_articles = json.load(file)
    except Exception as exc:
        return f"Loi doc mock wikipedia data: {exc}"

    normalized_topic = _normalize_text(topic)
    for key, value in mock_articles.items():
        if _normalize_text(key) == normalized_topic:
            return str(value)

    for key, value in mock_articles.items():
        normalized_key = _normalize_text(key)
        if normalized_key in normalized_topic or normalized_topic in normalized_key:
            return str(value)

    return "Khong tim thay bai viet Wikipedia phu hop cho chu de nay."
