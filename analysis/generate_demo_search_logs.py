import argparse
import os
import sys
from pathlib import Path
from typing import List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.telemetry.logger import logger
from src.telemetry.search_monitor import search_monitor
from src.tools.search_tool import web_search


def _extract_sources(formatted_results: str) -> List[str]:
    sources: List[str] = []
    for line in formatted_results.splitlines():
        if "| Source:" not in line:
            continue
        source = line.split("| Source:", maxsplit=1)[-1].strip()
        if source:
            sources.append(source)
    return sources


def _start_session(query: str) -> None:
    logger.log_event("AGENT_START", {"input": query, "mode": "demo"})


def _log_manual_search_case(
    user_query: str,
    search_query: str,
    category: str,
    results_count: int,
    relevant_count: int,
    sources: List[str],
    completeness_score: float,
    confidence_score: float,
    failure_type: str = "",
    failure_details: dict | None = None,
) -> None:
    search_monitor.log_search_query(
        user_query=user_query,
        search_query=search_query,
        step=1,
        tool_name="search",
        category=category,
    )
    search_monitor.log_search_results(
        search_query=search_query,
        results_count=results_count,
        relevant_count=relevant_count,
        sources=sources,
        latency_ms=12,
    )
    search_monitor.log_info_synthesis(
        user_query=user_query,
        sources_used=sources,
        completeness_score=completeness_score,
        confidence_score=confidence_score,
    )
    if failure_type:
        search_monitor.log_search_failure(
            failure_type=failure_type,
            query=search_query,
            details=failure_details or {},
        )


def generate_demo_logs(output_path: str) -> str:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    logger.use_log_file(output_path, append=False)
    os.environ["SEARCH_USE_API"] = "false"

    _start_session("Gia vang hom nay la bao nhieu?")
    first_results = web_search("gia vang hom nay")
    search_monitor.log_info_synthesis(
        user_query="Gia vang hom nay la bao nhieu?",
        sources_used=_extract_sources(first_results),
        completeness_score=0.95,
        confidence_score=0.92,
    )

    _start_session("Thoi tiet Ha Noi hom nay va chat luong khong khi the nao?")
    search_monitor.log_multi_hop_start(
        user_query="Thoi tiet Ha Noi hom nay va chat luong khong khi the nao?",
        planned_hops=2,
    )
    weather_results = web_search("thoi tiet ha noi")
    search_monitor.log_query_refinement(
        original_query="thoi tiet ha noi",
        refined_query="thoi tiet ha noi chat luong khong khi",
        reason="bo sung yeu to chat luong khong khi de tang do day du",
        improved=True,
        previous_results=3,
        refined_results=3,
    )
    refined_results = web_search("thoi tiet ha noi chat luong khong khi")
    search_monitor.log_info_synthesis(
        user_query="Thoi tiet Ha Noi hom nay va chat luong khong khi the nao?",
        sources_used=_extract_sources(weather_results) + _extract_sources(refined_results),
        completeness_score=0.88,
        confidence_score=0.85,
    )

    _start_session("Cho toi tai lieu ve search engine citation best practices.")
    no_result_query = "search engine citation best practices"
    web_search(no_result_query)
    search_monitor.log_query_refinement(
        original_query=no_result_query,
        refined_query="nghien cuu ve citation trong academic search",
        reason="mo rong query ve academic citation",
        improved=False,
        previous_results=0,
        refined_results=0,
    )

    _start_session("Thu tuong Nhat Ban hien tai la ai?")
    leader_results = web_search("thu tuong nhat ban hien tai")
    search_monitor.log_info_synthesis(
        user_query="Thu tuong Nhat Ban hien tai la ai?",
        sources_used=_extract_sources(leader_results),
        completeness_score=0.9,
        confidence_score=0.89,
    )

    _start_session("Tong hop nhanh tin AI tu mot nguon duy nhat.")
    _log_manual_search_case(
        user_query="Tong hop nhanh tin AI tu mot nguon duy nhat.",
        search_query="tin tuc ai moi nhat",
        category="general",
        results_count=3,
        relevant_count=3,
        sources=["news.example.com", "news.example.com", "news.example.com"],
        completeness_score=0.74,
        confidence_score=0.71,
        failure_type="low_source_diversity",
        failure_details={"source_diversity": 1},
    )

    _start_session("Tim tong quan ve startup AI nhung ket qua chua sat cau hoi.")
    _log_manual_search_case(
        user_query="Tim tong quan ve startup AI nhung ket qua chua sat cau hoi.",
        search_query="ai startup funding headline",
        category="general",
        results_count=4,
        relevant_count=1,
        sources=["techcrunch.com", "forbes.com", "blog.example.com", "news.example.com"],
        completeness_score=0.62,
        confidence_score=0.58,
        failure_type="low_relevance",
        failure_details={"relevance_score": 0.25},
    )

    _start_session("So sanh hai chi so kinh te can nhieu buoc nhung agent dung som.")
    search_monitor.log_multi_hop_start(
        user_query="So sanh hai chi so kinh te can nhieu buoc nhung agent dung som.",
        planned_hops=3,
    )
    _log_manual_search_case(
        user_query="So sanh hai chi so kinh te can nhieu buoc nhung agent dung som.",
        search_query="chi so kinh te quy 1 vietnam",
        category="finance",
        results_count=2,
        relevant_count=2,
        sources=["gso.gov.vn", "cafef.vn"],
        completeness_score=0.45,
        confidence_score=0.5,
        failure_type="incomplete_reasoning",
        failure_details={"planned_hops": 3, "completed_hops": 1},
    )

    _start_session("Hoi ve tin moi nhung workflow lai dua vao nguon khong phu hop.")
    _log_manual_search_case(
        user_query="Hoi ve tin moi nhung workflow lai dua vao nguon khong phu hop.",
        search_query="thu tuong nhat ban hom nay wikipedia",
        category="politics",
        results_count=2,
        relevant_count=1,
        sources=["wikipedia.org", "wikipedia.org"],
        completeness_score=0.55,
        confidence_score=0.52,
        failure_type="tool_selection_error",
        failure_details={"selected_tool": "wikipedia", "expected_tool": "search"},
    )

    logger.log_event("DEMO_LOG_GENERATED", {"output_path": output_path})
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sample search telemetry logs.")
    parser.add_argument(
        "--output",
        default=os.path.join("logs", "sample.log"),
        help="Target log file path for generated demo telemetry",
    )
    args = parser.parse_args()
    path = generate_demo_logs(args.output)
    print(f"Demo telemetry log created at: {path}")


if __name__ == "__main__":
    main()