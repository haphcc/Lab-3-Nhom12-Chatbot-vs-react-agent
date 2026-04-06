# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Ha Hung Phuoc
- **Student ID**: 2A202600367
- **Date**: 6 April 2026

---

## I. Technical Contribution (15 Points)

As member 5, I was responsible for implementing the search-specific use case and end-to-end demo infrastructure for the Information Search Agent track.

### Modules Implemented
1. **`search_demo.py`** — Interactive ReAct agent demo using search tools (search, wikipedia, calculate, fact_check) with configurable provider and model selection.
2. **`compare_search.py`** — Side-by-side chatbot baseline vs ReAct agent comparison on search queries, with tool-call tracing and latency metrics.
3. **`multi_hop_demo.py`** — Multi-hop search agent variant with explicit constraint for ≥3 tool calls, plus reasoning-chain visualization.
4. **`SETUP_SEARCH.md`** — Comprehensive setup and troubleshooting guide specific to the search use case with mock data paths and run commands.
5. **`SEARCH_ARCHITECTURE_FLOWCHART.md`** — Mermaid flowchart illustrating the Question → Query Analysis → Multi-hop Search → Synthesis → Answer path.
6. **`src/cli_utils.py` (fix)** — Refactored provider imports to be lazy-loaded, ensuring `--help` and non-interactive runs don't trigger import-time side effects (e.g., deprecated Gemini warning).

### Code Highlights

**search_demo.py** (tool mapping):
```python
def _build_agent_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "callable": tool["func"],
        }
        for tool in TOOLS
    ]
```
Maps the shared tool registry (`src/tools/__init__.py:TOOLS`) into the agent's expected tool schema, ensuring consistency across all demo scripts.

**compare_search.py** (batched telemetry):
```python
def _wrap_tools_for_counting(tools):
    calls: List[Dict[str, Any]] = []
    # ... tool wrapping logic ...
    return wrapped, calls
```
Intercepts tool calls to count and trace usage, enabling side-by-side comparison metrics.

**src/cli_utils.py** (lazy import pattern):
```python
def build_provider(config: RuntimeConfig) -> LLMProvider:
    if config.provider == "openai":
        from src.core.openai_provider import OpenAIProvider
        return OpenAIProvider(model_name=config.model, api_key=os.getenv("OPENAI_API_KEY"))
```
Defers provider import until actually needed, avoiding runtime errors when optional dependencies are missing.

### Documentation
- Each demo script includes `--help` documentation for provider selection (`openai`, `google`, `gemini`, `local`), model override, and interactive/non-interactive modes.
- `SETUP_SEARCH.md` provides a walkthrough from environment setup → mock data locations → example commands.
- The group report and architecture flowchart are integrated with these demos to form a cohesive evidence package for rubric compliance.

---

## II. Debugging Case Study (10 Points)

### Problem Description
During the first run of `compare_search.py`, the `--help` command output was cluttered with a `FutureWarning` from the deprecated `google.generativeai` package:
```
FutureWarning: All support for the `google.generativeai` package has ended...
```
This made the CLI output unprofessional and masked the actual help text. Additionally, calling `--help` should be a lightweight operation that doesn't initialize expensive dependencies.

### Log Source
From terminal run on 2026-04-06 (first attempt):
```
src\core\gemini_provider.py:3: FutureWarning:
  import google.generativeai as genai
```
This occurred because `src/cli_utils.py` was importing `GeminiProvider` at module load time, unconditionally.

### Diagnosis
Root cause: **Eager imports at module level**
- The original code had `from src.core.gemini_provider import GeminiProvider` and `from src.core.openai_provider import OpenAIProvider` at the top of `cli_utils.py`.
- These imports happened whenever any script imported `cli_utils`, even if the user was only asking for `--help` or using a different provider.
- The `gemini_provider.py` module, upon import, immediately executed `import google.generativeai`, triggering the deprecation warning.
- The `openai_provider.py` import was also unnecessary for non-OpenAI runs (e.g., local provider).

### Solution
Refactored `build_provider()` to use **lazy imports**:
```python
def build_provider(config: RuntimeConfig) -> LLMProvider:
    if config.provider == "openai":
        from src.core.openai_provider import OpenAIProvider  # Import only when needed
        return OpenAIProvider(...)
    if config.provider in {"google", "gemini"}:
        from src.core.gemini_provider import GeminiProvider  # Import only when needed
        return GeminiProvider(...)
    if config.provider == "local":
        from src.core.local_provider import LocalProvider
        return LocalProvider(...)
```
Post-fix verification showed `--help` now runs clean with no warnings, and each provider dependency is only loaded when its path is actually executed.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning: The Role of the `Thought` Block
In the `search_demo.py` comparison run (query: "Gia vang hom nay o Viet Nam la bao nhieu?"):
- **Chatbot baseline**: Responds directly: *"Xin lỗi, tôi không thể cung cấp thông tin giá vàng hiện tại..."* (refused due to no browsing capability).
- **ReAct agent**: Generates an explicit `Thought` block: *"Tôi cần tìm thông tin về giá vàng Việt Nam hôm nay."*, then calls `search()` to retrieve real data, returning *"Giá vàng SJC hôm nay tại Việt Nam ghi nhận ở mức khoảng 90.000.000 VND/lượng."*

**Key insight**: The `Thought` block acts as an internal reasoning trace that *commits* the agent to a retrieval strategy before execution. This decouples reasoning from response generation, allowing the agent to ground its answer in tool observations rather than relying on pre-trained knowledge (which may be stale or unavailable).

### 2. Reliability: When the Agent Performs Worse
During multi-hop demo runs, I observed that when the ReAct prompt explicitly requested "at least 3 tool calls," the agent would sometimes:
- Pack multiple `Action/Observation` steps into a single LLM generation.
- Use regex parser only extracted the first action, leaving subsequent actions in the text as "unreachable."
- Result: Fewer actual tool calls than intended, reducing multi-hop effectiveness.

**Insight**: The agent is only as reliable as its **output parsing contract**. If the model doesn't strictly follow single-action-per-turn format, the parser breaks and the agent degrades to a single-step tool caller. This is a fundamental limitation of regex-based parsing without structured outputs (e.g., JSON mode or function-calling APIs).

### 3. Observation: Environmental Feedback Drives Next Steps
In the `compare_search.py` trace, after the first `search()` call returned:
```
1. Gia vang SJC ngay 06/04/2026 | Gia vang SJC duoc ghi nhan o muc 90.000.000 VND/luong. | Source: baochinhphu.vn
```
The agent immediately recognized this as sufficient and generated `Final Answer` in the very next step. **No intermediate `Thought` expansion happened.**

**Insight**: The agent's behavior is highly sensitive to observation **quality and specificity**. Rich, relevant observations (like the one above) satisfy the agent quickly. Vague or irrelevant observations would likely trigger additional `Thought/Action` cycles. This means:
- Mock data design is critical to agent behavior / performance evaluation.
- Real-world tool outputs with noise or ambiguity would require more sophisticated parsing or clarification logic.

---

## IV. Future Improvements (5 Points)

### 1. Scalability: Structured Tool-Calling Protocol
**Current limitation**: Regex parsing is fragile and single-step.

**Proposal**: Replace regex extraction with a structured tool-calling mechanism:
- Adopt OpenAI's `function_calling` or similar JSON-mode responses.
- Each step is a **single, well-formed JSON object**:
  ```json
  {"action": "search", "args": "gold price vietnam"}
  ```
- This would eliminate the "packed-response" problem and allow true multi-step execution.

### 2. Safety: Supervisor LLM for Action Auditing
**Current limitation**: No verification that tool arguments are safe or valid before execution.

**Proposal**: Add a secondary "auditor" LLM call before executing any `Action`:
```python
def execute_tool(tool_name, args):
    # Audit: "Is this a safe call to 'search' with argument 'X'?"
    audit_result = auditor_llm.generate(f"Validate: {tool_name}({args})")
    if audit_result.startswith("UNSAFE"):
        return "Action blocked by safety policy."
    # Proceed with execution
    return tool_registry[tool_name](args)
```
This prevents prompt injection and argument hallucination.

### 3. Performance: Vector DB for Tool Selection
**Current limitation**: Tool selection is done via LLM reasoning; no routing optimization.

**Proposal**: For a system with 50+ tools:
- Embed each tool's description in a vector DB.
- At each step, retrieve the top-K most relevant tools based on the `Thought` embedding.
- Narrow down the action space, reducing model confusion and latency.

### 4. Observability: Structured Telemetry Events
**Current limitation**: Generic `LLM_METRIC` logs; no search-specific insights.

**Proposal**: Add domain-specific telemetry:
- `SEARCH_QUERY_ISSUED`: log query string, provenance.
- `SEARCH_RESULTS_RECEIVED`: log result count, source, relevance score.
- `MULTI_HOP_START` / `MULTI_HOP_END`: log total hops, fallback tool usage.
- This enables finer-grained RCA and A/B testing.

---

## V. Conclusion

This lab reinforced that building a production-grade agentic system requires more than just implementing a ReAct loop. The quality of the agent depends on:
1. **Reliable parsing** (structured outputs over regex).
2. **Thoughtful tool design** (rich, deterministic observations).
3. **Robust engineering** (lazy imports, error handling, telemetry).
4. **Extensive testing** (side-by-side comparisons, edge case tracing).

My deliverables—3 demo scripts, setup guide, architecture flowchart, and the lazy-import fix—form a cohesive foundation for scaling the search agent toward production readiness.
