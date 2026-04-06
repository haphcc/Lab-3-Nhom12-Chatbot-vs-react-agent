# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: NHOM12
- **Team Members**: NHOM12 members
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

This project implements an Information Search Agent using a ReAct loop and deterministic mock tools (`search`, `wikipedia`, `calculate`, `fact_check`) and compares it against a direct chatbot baseline.

- **Success Rate**: 3/3 demo tasks completed in smoke runs for search workflows (single-hop retrieval, chatbot-vs-agent comparison, multi-hop trace run).
- **Key Outcome**: In the same question on gold price in Vietnam, chatbot baseline refused due to no browsing access while the ReAct agent returned a grounded answer using tool output from mock search data.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
The core loop is implemented in `src/agent/agent.py` with this cycle:
1. Build prompt with scratchpad (`Question -> Thought -> Action -> Observation`).
2. Call LLM provider (`OpenAIProvider`, `GeminiProvider`, or `LocalProvider`).
3. Parse either `Action: tool(args)` or `Final Answer:`.
4. Execute tool and append observation back to scratchpad.
5. Stop on final answer or max steps.

Architecture visualization is provided in `SEARCH_ARCHITECTURE_FLOWCHART.md`.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `search` | `string` query | Retrieve top search snippets from deterministic mock dataset. |
| `wikipedia` | `string` topic | Return concise background article from mock encyclopedia dataset. |
| `calculate` | arithmetic expression string | Compute numeric values for simple quantitative questions. |
| `fact_check` | claim string | Cross-check claim consistency across mock sources. |

### 2.3 LLM Providers Used
- **Primary**: OpenAI `gpt-4o`
- **Secondary (Backup)**: Gemini provider path is available in code (`src/core/gemini_provider.py`)
- **Optional Local**: `llama-cpp` local provider (`src/core/local_provider.py`)

---

## 3. Telemetry & Performance Dashboard

Telemetry is logged in JSONL format and includes request latency, token usage, and cost estimate events (`LLM_METRIC`) in `logs/2026-04-06.log`.

Summary computed from the current log snapshot:
- **Average Latency (P50)**: **2047 ms**
- **Max Latency (P99)**: **5389 ms**
- **Average Tokens per Task**: **406.04 tokens**
- **Total Cost of Test Suite**: **$0.10557**
- **Average Agent Steps (AGENT_END)**: **0.77**

Notes:
- The metrics include all logged runs in the day snapshot, including iterative debugging/demo executions.
- Cost is a lab-side estimate from tracker logic, not a billing export.

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Multi-hop Instruction Not Reliably Enforced by Parser
- **Input**: `Gia vang hom nay o Viet Nam la bao nhieu va thong tin nay co nhat quan giua cac nguon khong?`
- **Expected**: At least 3 explicit tool calls in sequence (per `MultiHopSearchAgent` prompt constraint).
- **Observed**:
  - Agent trace only recorded 1 tool call in `Reasoning Chain`.
  - LLM output packed additional `Action/Observation/Final Answer` text in one generation block, but parser accepted final answer early.
- **Root Cause**:
  - Current parser extracts one actionable pattern per step and is vulnerable when model emits multiple pseudo-steps in a single response.
  - This causes mismatch between textual reasoning and actual executed tool trace.
- **Fix Direction**:
  - Enforce strict output schema (single action per turn).
  - Reject generations containing both `Final Answer` and unexecuted actions.
  - Add parser validation + retry with correction prompt.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Chatbot Baseline vs ReAct Agent (Search Query)
- **Prompt**: `Gia vang hom nay o Viet Nam la bao nhieu?`
- **Result**:
  - Chatbot: refused/uncertain (no tool access).
  - Agent: returned `~90,000,000 VND/luong` grounded by `search` tool observation.
- **Conclusion**: Tool-enabled ReAct is materially better for retrieval-style questions than direct chatbot response.

### Experiment 2: Standard Search Agent vs Multi-hop Prompting Variant
- **Diff**: MultiHop variant adds explicit instruction: minimum 3 tool calls before final answer.
- **Observed**: Model attempted to describe multiple steps in one generation, but executed trace still showed only 1 real call due to parser behavior.
- **Conclusion**: Prompt-only control is insufficient; parser and execution policy must enforce workflow constraints.

---

## 6. Production Readiness Review

- **Security**:
  - Keep API keys in `.env` only; rotate leaked keys immediately.
  - Avoid logging sensitive inputs in plaintext for production.
- **Guardrails**:
  - Current `max_steps` loop cap prevents infinite loops.
  - Need stricter action format validation and retry policy for malformed responses.
- **Scaling**:
  - Move from regex parsing to structured tool-calling protocol.
  - Introduce a reproducible benchmark suite (`tests/test_cases.json`) for regression checks.
  - Add richer search telemetry events (`SEARCH_QUERY`, `SEARCH_RESULTS`, `MULTI_HOP_START/END`) for clearer RCA.

---

## 7. Evidence Snapshot

- Implemented demos:
  - `search_demo.py`
  - `compare_search.py`
  - `multi_hop_demo.py`
- Setup guide:
  - `SETUP_SEARCH.md`
- Architecture artifact:
  - `SEARCH_ARCHITECTURE_FLOWCHART.md`

These artifacts support rubric categories: Agent v1/v2 evolution, Trace Quality, Evaluation & Analysis, Flowchart & Insight, and Extra Tools (Search).
