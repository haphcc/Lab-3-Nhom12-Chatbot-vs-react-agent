import argparse
import csv
import glob
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from statistics import mean
from typing import Any, Dict, List, Optional


@dataclass
class SessionMetrics:
    session_id: int
    user_query: str = ""
    category: str = "unknown"
    search_count: int = 0
    results_count_total: int = 0
    zero_result_count: int = 0
    failures: int = 0
    refinements: int = 0
    refinement_improved: int = 0
    refinement_total_known: int = 0
    multi_hop: bool = False
    relevance_scores: List[float] = field(default_factory=list)
    completeness_scores: List[float] = field(default_factory=list)
    source_diversity_values: List[int] = field(default_factory=list)
    tools_used: Counter = field(default_factory=Counter)

    def to_row(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_query": self.user_query,
            "category": self.category,
            "search_count": self.search_count,
            "avg_relevance": _safe_mean(self.relevance_scores),
            "avg_completeness": _safe_mean(self.completeness_scores),
            "avg_source_diversity": _safe_mean(self.source_diversity_values),
            "failed_search_rate": (
                self.zero_result_count / self.search_count if self.search_count else 0.0
            ),
            "multi_hop": self.multi_hop,
            "refinements": self.refinements,
            "refinement_success_rate": (
                self.refinement_improved / self.refinement_total_known
                if self.refinement_total_known
                else None
            ),
        }


def _safe_mean(values: List[float]) -> Optional[float]:
    return mean(values) if values else None


def _read_log_events(log_dir: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    log_paths = [log_dir] if os.path.isfile(log_dir) else sorted(glob.glob(os.path.join(log_dir, "*.log")))
    for path in log_paths:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "event" in payload:
                    events.append(payload)
    return events


def _ensure_session(sessions: Dict[int, SessionMetrics], session_id: int) -> SessionMetrics:
    if session_id not in sessions:
        sessions[session_id] = SessionMetrics(session_id=session_id)
    return sessions[session_id]


def _append_failure_case(
    failure_cases: List[Dict[str, Any]],
    seen_failures: set,
    session_id: int,
    failure_type: str,
    query: str,
    details: Optional[Dict[str, Any]] = None,
    source: str = "derived",
) -> None:
    key = (session_id, failure_type, query)
    if key in seen_failures:
        return

    seen_failures.add(key)
    failure_cases.append(
        {
            "session_id": session_id,
            "failure_type": failure_type,
            "query": query,
            "source": source,
            "details": details or {},
            "root_cause": _infer_root_cause(failure_type, details or {}),
            "recommended_action": _recommended_action(failure_type),
        }
    )


def _infer_root_cause(failure_type: str, details: Dict[str, Any]) -> str:
    if failure_type == "no_results":
        search_mode = details.get("search_mode")
        if search_mode == "mock":
            return "Mock dataset does not cover the query wording or topic."
        return "Search query returned no matching results from the selected provider."
    if failure_type == "low_relevance":
        return "Returned results only weakly matched the user intent."
    if failure_type == "low_source_diversity":
        return "Answer depended on too few unique sources, increasing bias risk."
    if failure_type == "incomplete_reasoning":
        return "The search flow stopped before collecting enough evidence to answer all parts of the question."
    if failure_type == "tool_selection_error":
        return "The workflow appears to have relied on the wrong retrieval path for the question type."
    if failure_type == "ineffective_refinement":
        return "Query reformulation did not improve retrieval quality or result count."
    return "Search workflow degradation detected from telemetry signals."


def _recommended_action(failure_type: str) -> str:
    recommendations = {
        "no_results": "Broaden the query, normalize wording, or expand indexed data sources.",
        "low_relevance": "Tighten query intent extraction and add stronger query rewriting.",
        "low_source_diversity": "Pull results from additional domains before synthesis.",
        "incomplete_reasoning": "Trigger an extra search hop when completeness stays low.",
        "tool_selection_error": "Improve tool-routing rules for current-event versus encyclopedia queries.",
        "ineffective_refinement": "Add query rewrite templates and compare before/after retrieval quality.",
    }
    return recommendations.get(failure_type, "Review the session and add a targeted recovery step.")


def _build_failure_summary(failure_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_type = Counter(case["failure_type"] for case in failure_cases)
    return {
        "total_failure_cases": len(failure_cases),
        "failure_type_breakdown": dict(by_type),
        "sessions_with_failures": sorted({case["session_id"] for case in failure_cases}),
        "cases": failure_cases,
    }


def _build_multi_hop_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    multi_hop_rows = [row for row in rows if row.get("multi_hop")]
    single_hop_rows = [row for row in rows if not row.get("multi_hop")]
    return {
        "multi_hop_session_count": len(multi_hop_rows),
        "single_hop_session_count": len(single_hop_rows),
        "avg_searches_multi_hop": _safe_mean([row["search_count"] for row in multi_hop_rows]),
        "avg_searches_single_hop": _safe_mean([row["search_count"] for row in single_hop_rows]),
        "avg_completeness_multi_hop": _safe_mean(
            [row["avg_completeness"] for row in multi_hop_rows if row["avg_completeness"] is not None]
        ),
        "avg_completeness_single_hop": _safe_mean(
            [row["avg_completeness"] for row in single_hop_rows if row["avg_completeness"] is not None]
        ),
    }


def analyze_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    sessions: Dict[int, SessionMetrics] = {}
    current_session_id = 0
    category_tool_usage: Dict[str, Counter] = defaultdict(Counter)
    failure_cases: List[Dict[str, Any]] = []
    refinement_details: List[Dict[str, Any]] = []
    seen_failures = set()

    for event in events:
        event_type = event.get("event")
        data = event.get("data", {}) or {}

        if event_type == "AGENT_START":
            current_session_id += 1
            session = _ensure_session(sessions, current_session_id)
            session.user_query = data.get("input", "")
            continue

        if current_session_id == 0:
            current_session_id = 1

        session = _ensure_session(sessions, current_session_id)

        if event_type == "MULTI_HOP_START":
            session.multi_hop = True

        elif event_type == "SEARCH_QUERY":
            session.search_count += 1
            tool_name = data.get("tool", "search")
            session.tools_used[tool_name] += 1
            category = data.get("category") or session.category
            session.category = category if category else "unknown"
            category_tool_usage[session.category][tool_name] += 1

        elif event_type == "SEARCH_RESULTS":
            results_count = int(data.get("results_count") or 0)
            session.results_count_total += results_count
            if results_count == 0:
                session.zero_result_count += 1
                _append_failure_case(
                    failure_cases,
                    seen_failures,
                    session.session_id,
                    "no_results",
                    data.get("search_query", session.user_query),
                    {
                        "results_count": results_count,
                        "source_diversity": data.get("source_diversity", 0),
                    },
                )

            relevance_score = data.get("relevance_score")
            if relevance_score is None:
                relevant_count = data.get("relevant_count")
                if relevant_count is not None and results_count > 0:
                    relevance_score = float(relevant_count) / float(results_count)
            if relevance_score is not None:
                session.relevance_scores.append(float(relevance_score))
                if float(relevance_score) < 0.5:
                    _append_failure_case(
                        failure_cases,
                        seen_failures,
                        session.session_id,
                        "low_relevance",
                        data.get("search_query", session.user_query),
                        {
                            "relevance_score": float(relevance_score),
                            "results_count": results_count,
                        },
                    )

            source_diversity = data.get("source_diversity")
            if source_diversity is None:
                sources = data.get("sources") or []
                source_diversity = len(set(sources))
            session.source_diversity_values.append(int(source_diversity))
            if results_count > 0 and int(source_diversity) <= 1:
                _append_failure_case(
                    failure_cases,
                    seen_failures,
                    session.session_id,
                    "low_source_diversity",
                    data.get("search_query", session.user_query),
                    {
                        "source_diversity": int(source_diversity),
                        "results_count": results_count,
                    },
                )

        elif event_type == "INFO_SYNTHESIS":
            completeness = data.get("completeness_score")
            if completeness is not None:
                session.completeness_scores.append(float(completeness))
                if float(completeness) < 0.7:
                    _append_failure_case(
                        failure_cases,
                        seen_failures,
                        session.session_id,
                        "incomplete_reasoning",
                        data.get("user_query", session.user_query),
                        {
                            "completeness_score": float(completeness),
                            "source_diversity": data.get("source_diversity"),
                        },
                    )
            source_diversity = data.get("source_diversity")
            if source_diversity is not None:
                session.source_diversity_values.append(int(source_diversity))

        elif event_type == "QUERY_REFINEMENT":
            session.refinements += 1
            improved = data.get("improved")
            if improved is not None:
                session.refinement_total_known += 1
                if bool(improved):
                    session.refinement_improved += 1
                else:
                    _append_failure_case(
                        failure_cases,
                        seen_failures,
                        session.session_id,
                        "ineffective_refinement",
                        data.get("original_query", session.user_query),
                        {
                            "previous_results": data.get("previous_results"),
                            "refined_results": data.get("refined_results"),
                            "refined_query": data.get("refined_query"),
                        },
                    )
            refinement_details.append(
                {
                    "session_id": session.session_id,
                    "original_query": data.get("original_query"),
                    "refined_query": data.get("refined_query"),
                    "reason": data.get("reason"),
                    "improved": improved,
                    "previous_results": data.get("previous_results"),
                    "refined_results": data.get("refined_results"),
                }
            )

        elif event_type == "SEARCH_FAILURE":
            session.failures += 1
            _append_failure_case(
                failure_cases,
                seen_failures,
                session.session_id,
                data.get("failure_type", "unknown"),
                data.get("query", ""),
                data.get("details", {}),
                source="explicit",
            )

    rows = [s.to_row() for s in sessions.values()]

    all_searches = sum(row["search_count"] for row in rows)
    all_zero = sum(
        sessions[row["session_id"]].zero_result_count for row in rows
    )
    refinement_known = sum(
        sessions[row["session_id"]].refinement_total_known for row in rows
    )
    refinement_improved = sum(
        sessions[row["session_id"]].refinement_improved for row in rows
    )

    overall = {
        "total_sessions": len(rows),
        "search_efficiency_avg_searches_per_question": _safe_mean(
            [row["search_count"] for row in rows]
        ),
        "relevance_score_avg": _safe_mean(
            [row["avg_relevance"] for row in rows if row["avg_relevance"] is not None]
        ),
        "answer_completeness_avg": _safe_mean(
            [
                row["avg_completeness"]
                for row in rows
                if row["avg_completeness"] is not None
            ]
        ),
        "source_diversity_avg": _safe_mean(
            [
                row["avg_source_diversity"]
                for row in rows
                if row["avg_source_diversity"] is not None
            ]
        ),
        "failed_search_rate": (all_zero / all_searches) if all_searches else 0.0,
        "explicit_failure_count": sum(1 for case in failure_cases if case.get("source") == "explicit"),
        "total_failure_cases": len(failure_cases),
        "multi_hop_rate": (
            sum(1 for row in rows if row["multi_hop"]) / len(rows) if rows else 0.0
        ),
        "query_refinement_success_rate": (
            refinement_improved / refinement_known if refinement_known else None
        ),
        "query_refinement_total": sum(row.get("refinements", 0) for row in rows),
        "query_refinement_flagged_improved": refinement_improved,
        "query_refinement_flagged_total": refinement_known,
        "analyzer_version": "1.0.0",
    }

    failure_summary = _build_failure_summary(failure_cases)
    multi_hop_summary = _build_multi_hop_summary(rows)

    return {
        "overall": overall,
        "sessions": rows,
        "category_tool_usage": {
            category: dict(counter) for category, counter in category_tool_usage.items()
        },
        "failure_cases": failure_cases,
        "failure_summary": failure_summary,
        "multi_hop_summary": multi_hop_summary,
        "query_refinement_report": refinement_details,
    }


def _write_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def _write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write("")
        return

    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_tool_usage_matrix(path: str, category_tool_usage: Dict[str, Dict[str, int]]) -> None:
    categories = sorted(category_tool_usage.keys())
    tools = sorted(
        {
            tool
            for usage in category_tool_usage.values()
            for tool in usage.keys()
        }
    )

    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["category"] + tools)
        for category in categories:
            row = [category]
            for tool in tools:
                row.append(category_tool_usage.get(category, {}).get(tool, 0))
            writer.writerow(row)


def run_analysis(log_dir: str, output_dir: str) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    events = _read_log_events(log_dir)
    report = analyze_events(events)

    _write_json(os.path.join(output_dir, "search_metrics_summary.json"), report["overall"])
    _write_csv(os.path.join(output_dir, "session_metrics.csv"), report["sessions"])
    _write_tool_usage_matrix(
        os.path.join(output_dir, "tool_usage_matrix.csv"), report["category_tool_usage"]
    )
    _write_json(os.path.join(output_dir, "failure_cases.json"), {"cases": report["failure_cases"]})
    _write_json(os.path.join(output_dir, "search_failure_summary.json"), report["failure_summary"])
    _write_json(os.path.join(output_dir, "multi_hop_analysis.json"), report["multi_hop_summary"])
    _write_json(
        os.path.join(output_dir, "query_refinement_report.json"),
        {"items": report["query_refinement_report"]},
    )

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze search telemetry logs.")
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory containing JSONL log files, or a single .log file path",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join("analysis", "output"),
        help="Directory where analysis artifacts are generated",
    )
    args = parser.parse_args()

    report = run_analysis(args.log_dir, args.output_dir)
    print("=== Search Quality Summary ===")
    for key, value in report["overall"].items():
        print(f"{key}: {value}")
    print(f"Artifacts saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
