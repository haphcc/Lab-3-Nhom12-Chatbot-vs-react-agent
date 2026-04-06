# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- Student Name: Nguyễn Tiến Thành
- Student ID: 2A202600487
- Date: 06/04/2026

## I. Technical Contribution (15 Points)

My assigned role in the updated plan was Member 4: Telemetry and Monitoring for the Information Search Agent. I focused only on the monitoring scope and completed the search-specific logging, analysis pipeline, and dashboard generation flow.

- Modules Implemented:
  - `src/telemetry/search_monitor.py`
  - `analysis/search_analyzer.py`
  - `analysis/search_dashboard.py`
- Supporting integration related to my scope:
  - `src/telemetry/logger.py`
  - `src/tools/search_tool.py`
  - `logs/sample.log`

- Code Highlights:
  - In `src/telemetry/search_monitor.py`, I created a centralized `SearchMonitor` class to log the five search-specific event types required by the work plan: `SEARCH_QUERY`, `SEARCH_RESULTS`, `MULTI_HOP_START`, `INFO_SYNTHESIS`, `QUERY_REFINEMENT`, and also `SEARCH_FAILURE` for root-cause analysis.
  - In `analysis/search_analyzer.py`, I implemented a full log-processing pipeline that reads JSONL log files from `logs/`, groups events by session, and computes the search quality metrics required by the project: search efficiency, relevance score, answer completeness, source diversity, failed search rate, multi-hop rate, and query refinement effectiveness.
  - In `analysis/search_dashboard.py`, I built a dashboard generator that converts analyzer outputs into visual artifacts, including search count distribution, average searches by category, tool usage heatmap, relevance-vs-completeness scatter plot, and query refinement effectiveness chart.
  - In `src/tools/search_tool.py`, I integrated telemetry calls directly into the search execution flow so the search tool automatically records query, result quality, source diversity, latency, and failure events.
  - In `src/telemetry/logger.py`, I supported stable log-file handling so telemetry can be written consistently to file and reused by the analyzer and dashboard scripts.

- Documentation / Interaction with the ReAct loop:
  - My code does not change the reasoning logic itself. Instead, it provides observability around the reasoning process.
  - During a ReAct-style workflow, when the agent or tool issues a search, the telemetry layer records what query was sent, what results came back, whether the search failed, whether a refinement happened, and whether the answer required multi-hop reasoning.
  - These logs are then consumed by the analyzer to produce quantitative metrics, and by the dashboard script to generate visual summaries for evaluation and debugging.

## II. Debugging Case Study (10 Points)

- Problem Description:
  - A search session failed for the research-oriented query `search engine citation best practices` and returned zero results. This is a realistic failure case because the agent/tool had to operate on limited mock search data and the original query wording did not match available indexed entries.

- Log Source:
  - `logs/sample.log`
  - Relevant events observed in the log:
    - `SEARCH_QUERY` for `search engine citation best practices`
    - `SEARCH_RESULTS` with `results_count = 0`
    - `SEARCH_FAILURE` with `failure_type = no_results`
    - `QUERY_REFINEMENT` to `nghien cuu ve citation trong academic search`, but still not improved

- Diagnosis:
  - The failure was mainly caused by data coverage and query mismatch, not by the logger itself.
  - The query was valid semantically, but the mock dataset used by the search tool did not contain matching entries for that research phrase.
  - This case is important because without search telemetry, the system would only appear to “not answer well”; with telemetry, I could isolate the exact point of failure: the search layer produced zero results, and the refinement still failed to recover.

- Solution:
  - I added explicit `SEARCH_FAILURE` logging to capture no-result scenarios.
  - I added `QUERY_REFINEMENT` tracking so the team can measure whether reformulated queries actually improve retrieval.
  - I implemented `analysis/search_analyzer.py` to export failure cases and refinement outcomes into machine-readable reports.
  - From the generated metrics, this failure appears in `analysis/output/failure_cases.json`, while refinement behavior appears in `analysis/output/query_refinement_report.json`.
  - This gives a concrete basis for future fixes such as improving mock search coverage, adding better query normalization, or routing certain queries to other tools like Wikipedia or fact-checking.

## III. Personal Insights: Chatbot vs ReAct (10 Points)

- Reasoning:
  - A direct chatbot can produce a fluent answer quickly, but it does not expose how it reached the answer.
  - With a ReAct-style agent plus telemetry, the `Thought -> Action -> Observation` pattern becomes inspectable. Even if the internal Thought text is not fully logged, the search-related actions and observations are visible through telemetry events. This makes reasoning quality easier to analyze.

- Reliability:
  - The agent can perform worse than a direct chatbot when tool results are sparse, irrelevant, or missing. In those cases, the extra reasoning steps do not help unless the search quality is good.
  - My telemetry results showed that the system had a `failed_search_rate` of `0.2` on the sample dataset, which means search quality directly affects the final answer quality.

- Observation:
  - Environment feedback is the main advantage of the agent design. When the system sees `SEARCH_RESULTS` with zero results or weak coverage, it can trigger `QUERY_REFINEMENT` or another search hop.
  - In the multi-hop weather example, the refinement from `thoi tiet ha noi` to `thoi tiet ha noi chat luong khong khi` improved completeness by covering the second part of the user question, which is exactly the type of behavior that a basic chatbot usually does not perform explicitly.

## IV. Future Improvements (5 Points)

- Scalability:
  - Store telemetry in a structured analytics backend instead of plain log files, for example PostgreSQL, Elasticsearch, or a data warehouse.
  - Add session IDs generated at runtime so events can be grouped more reliably across concurrent users.

- Safety:
  - Add a telemetry rule to detect suspicious behavior such as repeated failed searches, irrelevant tool usage, or answer synthesis without enough supporting sources.
  - Add automatic alerts when failed search rate or low source diversity crosses a threshold.

- Performance:
  - Track latency per tool and per search provider more explicitly, then optimize slow steps.
  - Add richer dashboard filters by category, provider, and failure type.
  - Extend the dashboard to compare multiple log files over time so the team can measure whether changes improve search quality.

## Summary

My contribution as Member 4 was to make the Information Search Agent observable and measurable. I implemented search-specific logging, analysis scripts, and a dashboard pipeline so the team can move from subjective debugging to evidence-based evaluation. This work supports both technical diagnosis and project scoring because it quantifies how well the search workflow performs under realistic cases.

## Artifacts & How I validated (commands I ran)

- Generated demo logs (created `logs/sample.log`) and confirmed events were written by `search_monitor` and `logger`.
  ```bash
  python analysis/generate_demo_search_logs.py --output logs/sample.log
  ```
- Ran the analyzer over the demo log and produced analysis artifacts in `analysis/output/`:
  ```bash
  python analysis/search_analyzer.py --log-dir logs/sample.log --output-dir analysis/output
  ```
- Built dashboard images and `dashboard.md`:
  ```bash
  python analysis/search_dashboard.py --analysis-dir analysis/output
  ```
- Optional: open the Streamlit UI and use the `Search Monitoring` tab to run these steps interactively:

  ```bash
  streamlit run web_app.py
  ```

- Key analyzer outputs I verified (example values from running the demo):
  - `analysis/output/search_metrics_summary.json`: total_sessions = 8, failed_search_rate ≈ 0.11, relevance_score_avg ≈ 0.82, answer_completeness_avg ≈ 0.73
  - `analysis/output/search_failure_summary.json`: total_failure_cases = 10 with breakdown by type (no_results, low_relevance, low_source_diversity, incomplete_reasoning, tool_selection_error)
  - `analysis/output/multi_hop_analysis.json`: shows multi-hop vs single-hop comparisons and average completeness values

These artifacts (CSV, JSON, PNG, and `dashboard.md`) provide evidence that the telemetry pipeline captures search events end-to-end and that the analyzer/dashboard produce actionable KPIs and RCA for the team.
