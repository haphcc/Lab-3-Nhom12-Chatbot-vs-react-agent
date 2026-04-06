import json
import os
import time
import unicodedata
from pathlib import Path
from typing import List, Dict, Any

import requests

from src.telemetry.search_monitor import search_monitor


MOCK_SEARCH_PATH = Path(__file__).resolve().parent / "mock_data" / "search_results.json"


def _infer_search_category(query: str) -> str:
    normalized = _normalize_text(query)
    if any(token in normalized for token in ["gia", "vang", "usd", "co phieu", "thi truong"]):
        return "finance"
    if any(token in normalized for token in ["thoi tiet", "nhiet do", "mua", "aqi"]):
        return "weather"
    if any(token in normalized for token in ["thu tuong", "tong thong", "lanh dao", "chinh tri"]):
        return "politics"
    if any(token in normalized for token in ["nghien cuu", "study", "citation", "paper", "tai lieu"]):
        return "research"
    return "general"


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


def _search_serpapi(query: str, timeout_sec: int = 10) -> List[Dict[str, str]]:
    api_key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not api_key:
        return []

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": 5,
    }
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=timeout_sec)
    response.raise_for_status()
    payload = response.json()

    results = []
    for item in payload.get("organic_results", [])[:5]:
        results.append(
            {
                "title": str(item.get("title", "Khong co tieu de")),
                "snippet": str(item.get("snippet", "Khong co mo ta ngan")),
                "source": str(item.get("displayed_link", item.get("link", "serpapi"))),
            }
        )
    return results


def _search_duckduckgo(query: str, timeout_sec: int = 10) -> List[Dict[str, str]]:
    # DuckDuckGo Instant Answer API is free and does not require API key.
    params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
    response = requests.get("https://api.duckduckgo.com/", params=params, timeout=timeout_sec)
    response.raise_for_status()
    payload = response.json()

    results = []
    abstract_text = str(payload.get("AbstractText", "")).strip()
    abstract_source = str(payload.get("AbstractSource", "")).strip()
    if abstract_text:
        results.append(
            {
                "title": str(payload.get("Heading", "DuckDuckGo Instant Answer")).strip() or "DuckDuckGo Instant Answer",
                "snippet": abstract_text,
                "source": abstract_source or "duckduckgo.com",
            }
        )

    for topic in payload.get("RelatedTopics", []):
        if len(results) >= 5:
            break
        if isinstance(topic, dict) and "Text" in topic:
            results.append(
                {
                    "title": "Related Topic",
                    "snippet": str(topic.get("Text", "")),
                    "source": str(topic.get("FirstURL", "duckduckgo.com")),
                }
            )
        elif isinstance(topic, dict) and "Topics" in topic:
            for nested in topic.get("Topics", []):
                if len(results) >= 5:
                    break
                if isinstance(nested, dict) and "Text" in nested:
                    results.append(
                        {
                            "title": "Related Topic",
                            "snippet": str(nested.get("Text", "")),
                            "source": str(nested.get("FirstURL", "duckduckgo.com")),
                        }
                    )
    return results


def _search_api(query: str) -> List[Dict[str, str]]:
    # Priority: SerpAPI (if key exists) -> DuckDuckGo.
    try:
        serpapi_results = _search_serpapi(query)
        if serpapi_results:
            return serpapi_results
    except Exception:
        pass

    try:
        ddg_results = _search_duckduckgo(query)
        if ddg_results:
            return ddg_results
    except Exception:
        pass

    return []


def _search_mock(query: str) -> List[Dict[str, str]]:
    try:
        with MOCK_SEARCH_PATH.open("r", encoding="utf-8") as file:
            mock_db = json.load(file)
    except Exception as exc:
        return [
            {
                "title": "Mock data error",
                "snippet": f"Loi doc mock search data: {exc}",
                "source": "local-mock-db",
            }
        ]

    normalized_query = _normalize_text(query)
    for key, value in mock_db.items():
        if _normalize_text(key) in normalized_query:
            if isinstance(value, list):
                return value
            return [{"title": key, "snippet": str(value), "source": "mock-db"}]
    return []


def web_search(query: str) -> str:
    """
    Tra cuu web search voi che do uu tien API that (optional), fallback mock data.
    Output duoc dinh dang string de phu hop ReAct parser don gian.
    """
    use_api = os.getenv("SEARCH_USE_API", "false").lower() in {"1", "true", "yes"}
    category = _infer_search_category(query)
    start = time.time()
    search_monitor.log_search_query(
        user_query=query,
        search_query=query,
        step=1,
        tool_name="search",
        category=category,
    )

    results: List[Dict[str, str]] = []
    if use_api:
        results = _search_api(query)

    if not results:
        results = _search_mock(query)

    latency_ms = int((time.time() - start) * 1000)
    sources = [str(item.get("source", "unknown-source")) for item in results]
    search_monitor.log_search_results(
        search_query=query,
        results_count=len(results),
        relevant_count=len(results),
        sources=sources,
        latency_ms=latency_ms,
    )

    if not results:
        search_monitor.log_search_failure(
            failure_type="no_results",
            query=query,
            details={"category": category, "search_mode": "api" if use_api else "mock"},
        )

    return _format_results(results)
