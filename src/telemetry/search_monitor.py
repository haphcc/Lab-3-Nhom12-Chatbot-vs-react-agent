from datetime import datetime
from typing import Any, Dict, List, Optional

from src.telemetry.logger import logger


class SearchMonitor:
    """Centralized telemetry helper for information-search workflows."""

    def log_search_query(
        self,
        user_query: str,
        search_query: str,
        step: int,
        tool_name: str = "search",
        category: Optional[str] = None,
    ) -> None:
        logger.log_event(
            "SEARCH_QUERY",
            {
                "user_query": user_query,
                "search_query": search_query,
                "step": step,
                "tool": tool_name,
                "category": category,
            },
        )

    def log_search_results(
        self,
        search_query: str,
        results_count: int,
        relevant_count: Optional[int] = None,
        sources: Optional[List[str]] = None,
        latency_ms: Optional[int] = None,
    ) -> None:
        relevance_score = None
        if relevant_count is not None and results_count > 0:
            relevance_score = relevant_count / float(results_count)

        logger.log_event(
            "SEARCH_RESULTS",
            {
                "search_query": search_query,
                "results_count": results_count,
                "relevant_count": relevant_count,
                "relevance_score": relevance_score,
                "sources": sources or [],
                "source_diversity": len(set(sources or [])),
                "latency_ms": latency_ms,
            },
        )

    def log_multi_hop_start(self, user_query: str, planned_hops: Optional[int] = None) -> None:
        logger.log_event(
            "MULTI_HOP_START",
            {
                "user_query": user_query,
                "planned_hops": planned_hops,
                "started_at": datetime.utcnow().isoformat(),
            },
        )

    def log_info_synthesis(
        self,
        user_query: str,
        sources_used: List[str],
        completeness_score: Optional[float] = None,
        confidence_score: Optional[float] = None,
    ) -> None:
        logger.log_event(
            "INFO_SYNTHESIS",
            {
                "user_query": user_query,
                "sources_used": sources_used,
                "source_diversity": len(set(sources_used)),
                "completeness_score": completeness_score,
                "confidence_score": confidence_score,
            },
        )

    def log_query_refinement(
        self,
        original_query: str,
        refined_query: str,
        reason: str,
        improved: Optional[bool] = None,
        previous_results: Optional[int] = None,
        refined_results: Optional[int] = None,
    ) -> None:
        logger.log_event(
            "QUERY_REFINEMENT",
            {
                "original_query": original_query,
                "refined_query": refined_query,
                "reason": reason,
                "improved": improved,
                "previous_results": previous_results,
                "refined_results": refined_results,
            },
        )

    def log_search_failure(
        self,
        failure_type: str,
        query: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        logger.log_event(
            "SEARCH_FAILURE",
            {
                "failure_type": failure_type,
                "query": query,
                "details": details or {},
            },
        )


search_monitor = SearchMonitor()
