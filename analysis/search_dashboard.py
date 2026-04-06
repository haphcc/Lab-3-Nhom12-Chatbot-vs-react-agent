import argparse
import csv
import json
import os
from collections import defaultdict
from typing import Dict, List

import matplotlib.pyplot as plt


def _read_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _to_float(value: str, default: float = 0.0) -> float:
    if value in (None, "", "None"):
        return default
    return float(value)


def _plot_search_count_distribution(session_rows: List[Dict[str, str]], output_dir: str) -> str:
    values = [int(_to_float(row.get("search_count", "0"))) for row in session_rows]
    if not values:
        values = [0]

    plt.figure(figsize=(8, 5))
    plt.hist(values, bins=min(10, max(1, len(set(values)))), color="#1f77b4", edgecolor="white")
    plt.title("Search Count Distribution")
    plt.xlabel("Searches per Question")
    plt.ylabel("Frequency")
    plt.tight_layout()

    out_path = os.path.join(output_dir, "search_count_distribution.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def _plot_avg_searches_by_category(session_rows: List[Dict[str, str]], output_dir: str) -> str:
    grouped: Dict[str, List[int]] = defaultdict(list)
    for row in session_rows:
        category = row.get("category", "unknown") or "unknown"
        grouped[category].append(int(_to_float(row.get("search_count", "0"))))

    categories = sorted(grouped.keys()) or ["unknown"]
    averages = [sum(grouped[c]) / len(grouped[c]) for c in categories] if grouped else [0.0]

    plt.figure(figsize=(9, 5))
    plt.bar(categories, averages, color="#2ca02c")
    plt.title("Average Searches per Category")
    plt.xlabel("Category")
    plt.ylabel("Avg Searches")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    out_path = os.path.join(output_dir, "avg_searches_by_category.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def _plot_tool_usage_heatmap(matrix_rows: List[Dict[str, str]], output_dir: str) -> str:
    if not matrix_rows:
        matrix_rows = [{"category": "unknown", "search": "0"}]

    tools = [key for key in matrix_rows[0].keys() if key != "category"]
    categories = [row["category"] for row in matrix_rows]
    matrix = []
    for row in matrix_rows:
        matrix.append([_to_float(row.get(tool, "0")) for tool in tools])

    plt.figure(figsize=(max(6, len(tools) * 1.1), max(4, len(categories) * 0.8)))
    im = plt.imshow(matrix, cmap="YlGnBu", aspect="auto")
    plt.colorbar(im, label="Usage Count")
    plt.xticks(range(len(tools)), tools, rotation=35, ha="right")
    plt.yticks(range(len(categories)), categories)
    plt.title("Tool Usage Heatmap")
    plt.tight_layout()

    out_path = os.path.join(output_dir, "tool_usage_heatmap.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def _plot_quality_scatter(session_rows: List[Dict[str, str]], output_dir: str) -> str:
    relevance = [_to_float(row.get("avg_relevance", "0")) for row in session_rows]
    completeness = [_to_float(row.get("avg_completeness", "0")) for row in session_rows]
    searches = [_to_float(row.get("search_count", "0")) for row in session_rows]

    if not relevance:
        relevance = [0.0]
        completeness = [0.0]
        searches = [1.0]

    plt.figure(figsize=(8, 5))
    plt.scatter(relevance, completeness, s=[40 + (s * 15) for s in searches], alpha=0.7)
    plt.title("Relevance vs Completeness")
    plt.xlabel("Average Relevance")
    plt.ylabel("Average Completeness")
    plt.xlim(0, 1.05)
    plt.ylim(0, 1.05)
    plt.grid(alpha=0.3)
    plt.tight_layout()

    out_path = os.path.join(output_dir, "quality_scatter.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def _plot_refinement_effectiveness(refinement_items: List[Dict], output_dir: str) -> str:
    improved = sum(1 for item in refinement_items if item.get("improved") is True)
    not_improved = sum(1 for item in refinement_items if item.get("improved") is False)
    unknown = sum(1 for item in refinement_items if item.get("improved") is None)

    values = [improved, not_improved, unknown]
    labels = ["Improved", "Not Improved", "Unknown"]

    if sum(values) == 0:
        values = [1, 0, 0]

    plt.figure(figsize=(7, 5))
    plt.pie(values, labels=labels, autopct="%1.0f%%", startangle=90)
    plt.title("Query Refinement Effectiveness")
    plt.tight_layout()

    out_path = os.path.join(output_dir, "query_refinement_effectiveness.png")
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def build_dashboard(analysis_dir: str) -> Dict[str, str]:
    summary_path = os.path.join(analysis_dir, "search_metrics_summary.json")
    session_csv = os.path.join(analysis_dir, "session_metrics.csv")
    matrix_csv = os.path.join(analysis_dir, "tool_usage_matrix.csv")
    refinement_json = os.path.join(analysis_dir, "query_refinement_report.json")

    summary = _read_json(summary_path) if os.path.exists(summary_path) else {}
    session_rows = _read_csv(session_csv)
    matrix_rows = _read_csv(matrix_csv)
    refinement = _read_json(refinement_json).get("items", []) if os.path.exists(refinement_json) else []

    charts = {
        "search_count_distribution": _plot_search_count_distribution(session_rows, analysis_dir),
        "avg_searches_by_category": _plot_avg_searches_by_category(session_rows, analysis_dir),
        "tool_usage_heatmap": _plot_tool_usage_heatmap(matrix_rows, analysis_dir),
        "quality_scatter": _plot_quality_scatter(session_rows, analysis_dir),
        "query_refinement_effectiveness": _plot_refinement_effectiveness(refinement, analysis_dir),
    }

    dashboard_md = os.path.join(analysis_dir, "dashboard.md")
    with open(dashboard_md, "w", encoding="utf-8") as handle:
        handle.write("# Search Metrics Dashboard\n\n")
        handle.write("## KPI Summary\n\n")
        if summary:
            for key, value in summary.items():
                handle.write(f"- **{key}**: {value}\n")
        else:
            handle.write("- No summary data found.\n")
        handle.write("\n## Visualizations\n\n")
        handle.write("### Search Count Distribution\n\n")
        handle.write("![Search Count Distribution](search_count_distribution.png)\n\n")
        handle.write("### Average Searches by Category\n\n")
        handle.write("![Average Searches by Category](avg_searches_by_category.png)\n\n")
        handle.write("### Tool Usage Heatmap\n\n")
        handle.write("![Tool Usage Heatmap](tool_usage_heatmap.png)\n\n")
        handle.write("### Relevance vs Completeness\n\n")
        handle.write("![Relevance vs Completeness](quality_scatter.png)\n\n")
        handle.write("### Query Refinement Effectiveness\n\n")
        handle.write("![Query Refinement Effectiveness](query_refinement_effectiveness.png)\n")

    charts["dashboard_markdown"] = dashboard_md
    return charts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate visual dashboard for search telemetry.")
    parser.add_argument(
        "--analysis-dir",
        default=os.path.join("analysis", "output"),
        help="Directory containing analyzer artifacts",
    )
    args = parser.parse_args()

    os.makedirs(args.analysis_dir, exist_ok=True)
    outputs = build_dashboard(args.analysis_dir)

    print("Dashboard generated:")
    for key, path in outputs.items():
        print(f"- {key}: {path}")


if __name__ == "__main__":
    main()
