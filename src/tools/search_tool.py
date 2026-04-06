import json
import unicodedata
from pathlib import Path
from typing import List, Dict, Any


MOCK_SEARCH_PATH = Path(__file__).resolve().parent / "mock_data" / "search_results.json"


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    without_accents = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return without_accents.lower().strip()


def _format_results(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "Khong tim thay thong tin moi nhat cho yeu cau nay."

    lines = []
    top_results = results[:5]
    for idx, item in enumerate(top_results, start=1):
        title = str(item.get("title", "Khong co tieu de"))
        snippet = str(item.get("snippet", "Khong co mo ta ngan"))
        source = str(item.get("source", "unknown-source"))
        lines.append(f"{idx}. {title} | {snippet} | Source: {source}")
    return "\n".join(lines)


def web_search(query: str) -> str:
    """
    Tra cuu mock web search va tra ve top 3-5 ket qua voi title + snippet.
    Output duoc dinh dang string de phu hop ReAct parser don gian.
    """
    try:
        with MOCK_SEARCH_PATH.open("r", encoding="utf-8") as file:
            mock_db = json.load(file)
    except Exception as exc:
        return f"Loi doc mock search data: {exc}"

    normalized_query = _normalize_text(query)
    for key, value in mock_db.items():
        if _normalize_text(key) in normalized_query:
            if isinstance(value, list):
                return _format_results(value)
            return _format_results([{"title": key, "snippet": str(value), "source": "mock-db"}])

    return "Khong tim thay thong tin moi nhat cho yeu cau nay."
