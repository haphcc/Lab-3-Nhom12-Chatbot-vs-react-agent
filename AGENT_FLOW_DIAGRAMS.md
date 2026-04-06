# 🔄 ReAct Agent Architecture & Flow Diagrams

## 1. Main Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER QUESTION INPUT                              │
│                    "Compare Vietnam and Thailand"                        │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ReActAgent.run()                                    │
│                                                                          │
│  ✓ Initialize conversation context                                      │
│  ✓ Reset tracking variables (search_history, tool_call_count)           │
│  ✓ Set error counter to 0                                               │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              🔄 REACT LOOP (while steps < max_steps)                     │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
    Step 1              Step 2              Step 3+
                               │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│  THOUGHT         │  │  ACTION          │  │  OBSERVATION    │
│                  │  │                  │  │                 │
│ LLM generates    │  │ Parse & Extract  │  │ Execute tool &  │
│ reasoning step   │  │ tool + arguments │  │ get results     │
│                  │  │                  │  │                 │
│ Input: prev      │  │ Input: LLM       │  │ Input: tool call│
│ conversation     │  │ response         │  │                 │
│                  │  │                  │  │ Output: result  │
│ Output: thought  │  │ Output: action   │  │                 │
│ text             │  │ dict (tool,args) │  │ Cache result    │
└────────┬─────────┘  └────────┬─────────┘  └────────┬────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │                     │
                    ▼                     ▼
              Has Final     No Final
              Answer?        Answer?
                    │                     │
                    │YES                 │NO
                    │                     │
                    ▼                     ▼
           ┌─────────────────┐   ┌──────────────────┐
           │ Extract Answer  │   │ Append Observation
           │                 │   │ to Conversation
           │ Log AGENT_END   │   │
           │ with metrics    │   │ Increment step
           │                 │   │
           │ Calculate:      │   │ Loop Again
           │ - confidence    │   │
           │ - search chain  │   │
           │ - redundancy    │   │
           │                 │   │
           │ RETURN ANSWER   │   │
           └─────────────────┘   └──────────────────┘
```

---

## 2. Tool Execution Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│               PARSE ACTION FROM LLM RESPONSE                             │
│                                                                          │
│  Input: "Action: search(\"Vietnam GDP 2024\")"                          │
│                                                                          │
│  Process:                                                                │
│  1. Extract tool name: "search"                                          │
│  2. Extract arguments: "Vietnam GDP 2024"                                │
│  3. Create action dict: {"tool": "search", "args": "Vietnam GDP 2024"}  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               TRACK TOOL USAGE STATISTICS                                │
│                                                                          │
│  ✓ Increment tool call count: tool_call_count["search"] += 1            │
│  ✓ Add to search history: search_history.append("Vietnam GDP 2024")     │
│  ✓ Check for redundancy: Compare with previous searches                 │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               EXECUTE TOOL: _execute_tool()                              │
│                                                                          │
│  1. Find tool in registry:                                               │
│     for tool in self.tools:                                              │
│        if tool['name'] == tool_name:                                     │
│           tool_func = tool.get('function')                               │
│                                                                          │
│  2. If tool not found:                                                   │
│     return "ERROR: Tool '{tool_name}' not found"                         │
│                                                                          │
│  3. Execute tool with error handling:                                    │
│     try:                                                                 │
│        result = tool_func(args)                                          │
│     except Exception as e:                                               │
│        return f"ERROR executing tool: {str(e)}"                          │
│                                                                          │
│  4. Log event:                                                           │
│     logger.log_event("TOOL_EXECUTION", {...})                            │
│                                                                          │
│  Output: "Vietnam's GDP in 2024 is approximately $430 billion..."       │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               APPEND OBSERVATION TO CONTEXT                              │
│                                                                          │
│  Before:                                                                 │
│  conversation = "Question: Compare Vietnam and Thailand GDP?\n..."      │
│                                                                          │
│  Process:                                                                │
│  conversation += f"\n{response}\n"                                       │
│  conversation += f"Observation: {observation}\n"                        │
│                                                                          │
│  After:                                                                  │
│  conversation = "Question: Compare Vietnam and Thailand GDP?\n          │
│                 ...\n                                                    │
│                 Thought: I need Vietnam's GDP\n                          │
│                 Action: search(\"Vietnam GDP 2024\")\n                   │
│                 Observation: Vietnam's GDP is $430 billion\n"            │
│                                                                          │
│  Result: Enhanced context for next LLM call                              │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │                     │
                    ▼                     ▼
               Final Answer?          Loop (step+1)
                    │                     │
                    ▼                     ▼
               RETURN                NEXT ITERATION
```

---

## 3. Multi-hop Reasoning Flow

```
┌─────────────────────────────────────────────────────┐
│  INCOMING QUESTION                                   │
│  "Compare Vietnam and Thailand economies"            │
└──────────────────────────────┬──────────────────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                              │
        ▼                                              ▼
   ┌────────────────┐                        ┌──────────────────┐
   │ STEP 1: Search │                        │ STEP 2: Search   │
   │                │                        │                  │
   │ Query: Vietnam │                        │ Query: Thailand  │
   │ GDP 2024       │                        │ GDP 2024         │
   │                │                        │                  │
   │ Result:        │                        │ Result:          │
   │ $430B,         │                        │ $380B,           │
   │ growth 6.5%    │                        │ growth 3%        │
   └────────┬───────┘                        └────────┬─────────┘
            │                                         │
            └──────────────────┬──────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ MULTI-HOP ANALYSIS   │
                    │                      │
                    │ ✓ 2 searches done    │
                    │ ✓ Multi-hop = true   │
                    │ ✓ Overlap score: 71% │
                    │ ✓ Tool diversity: 1  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │ INFORMATION SYNTHESIS    │
                    │                          │
                    │ Source 1: Vietnam data   │
                    │ Source 2: Thailand data  │
                    │                          │
                    │ Comparison:              │
                    │ "Vietnam ($430B) >       │
                    │  Thailand ($380B)"       │
                    │                          │
                    │ Growth:                  │
                    │ "Vietnam (6.5%) >        │
                    │  Thailand (3%)"          │
                    └──────────┬───────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │ CONFIDENCE ASSESSMENT    │
                    │                          │
                    │ Base score: 0.50         │
                    │ + Sources:   0.15        │
                    │ + Multi-hop: 0.15        │
                    │ + Diversity: 0.10        │
                    │ - Errors:    0.00        │
                    │ ──────────────────       │
                    │ TOTAL: 0.90 ✓ HIGH      │
                    └──────────┬───────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │ FINAL ANSWER             │
                    │                          │
                    │ "Vietnam's economy is    │
                    │  larger and growing      │
                    │  faster than Thailand's" │
                    │                          │
                    │ Confidence: 0.90/1.0     │
                    └──────────────────────────┘
```

---

## 4. Error Recovery Flow

```
┌────────────────────────────────────────────────────┐
│  POTENTIAL ERROR ENCOUNTERED                        │
└──────────────────────┬───────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    CASE 1        CASE 2         CASE 3
    LLM Error     Parsing        Tool Error
                  Error
        │              │              │
        ▼              ▼              ▼
    
CASE 1: LLM Error
├─ Error: API timeout, rate limit, auth fail
├─ Action: Log AGENT_END with error status
├─ Result: Return "ERROR: Failed to get LLM response"
└─ Return immediately (no retry)

CASE 2: Parsing Error
├─ Error: Action not found in LLM response
├─ Action:
│  ├─ Increment error_count
│  ├─ Log PARSING_ERROR
│  ├─ Append error feedback: "You did not provide valid Action"
│  └─ Continue loop (retry)
├─ Retry condition: error_count < max_errors (3)
└─ On max errors: Give up, call AGENT_END

CASE 3: Tool Error
├─ Sub-case 3a: Tool not found
│  ├─ Error: Tool name doesn't exist in registry
│  ├─ Action: Return error message
│  └─ Observation: "ERROR: Tool 'xxx' not found"
│
├─ Sub-case 3b: Tool execution fails
│  ├─ Error: Exception during tool_func(args)
│  ├─ Action: Catch exception, return error
│  └─ Observation: "ERROR executing tool 'xxx': ..."
│
└─ Continue loop with error observation
   (LLM learns from error and tries different approach)
```

---

## 5. System Prompt Selection Flow

```
┌─────────────────────────────────────┐
│  INCOMING QUESTION ANALYSIS         │
└──────────────────────┬──────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Simple?        Complex?       Unknown?
        │              │              │
        ▼              ▼              ▼
      YES            YES             NO
        │              │              │
        │       ┌──────┴────────┐     │
        │      │Requires        │     │
        │   Multi-step   Single-step  │
        │   comparison   answer       │
        │       │           │         │
        │       │           │         ▼
        │       │           │      DEFAULT V1
        │       │           │
        ▼       ▼           ▼
    USE V2  USE V2      USE V1
    
┌─────────────────────────────────────────────────────────────┐
│  SYSTEM PROMPT V1: Basic ReAct Format                        │
│  ≈ 750 tokens                                                │
│  - ReAct format explanation                                  │
│  - Tool listing                                              │
│  - 3 examples                                                │
│  - Do's and Don'ts                                           │
│                                                              │
│  Best for: "What is the capital of France?"                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  SYSTEM PROMPT V2: Advanced Strategies                       │
│  ≈ 1800 tokens                                               │
│  - Everything from V1 +                                      │
│  - Query decomposition strategy                              │
│  - Multi-hop search guidance                                 │
│  - Confidence indicators                                     │
│  - Information synthesis framework                           │
│  - Error recovery strategies                                 │
│  - Advanced examples with explanations                       │
│                                                              │
│  Best for: "Compare Vietnam & Thailand economies"            │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Confidence Scoring Calculation

```
┌──────────────────────────────────────┐
│  CONFIDENCE SCORE CALCULATION         │
│                                       │
│  score = 0.5  (base)                 │
└──────────────────┬────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    
    Factor 1:           Factor 2:            Factor 3:
    Number of           Multi-hop            Tool
    Sources             Reasoning            Diversity
        │                   │                   │
        ▼                   ▼                   ▼
    
    If 1 source: +0.10  If 2+ searches: +0.15  If 2+ tools: +0.15
    If 2 sources: +0.15 Else: +0.00           Else: +0.00
    If 3+ sources: +0.20
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌─────────────────────┐
                    │  Factor 4:          │
                    │  Errors Encountered │
                    │                     │
                    │  0 errors: -0.00    │
                    │  1 error:  -0.10    │
                    │  2 errors: -0.20    │
                    │  3 errors: -0.30    │
                    └─────────┬───────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │  SUM ALL FACTORS │
                        │                  │
                        │  Score = sum(+)  │
                        │  - sum(-)        │
                        │                  │
                        │  Bound: [0, 1]   │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌────────────────────┐
                        │  CONFIDENCE SCORE  │
                        │                    │
                        │  0.0-0.3:🔴 Very Low
                        │  0.3-0.5: 🟡 Low    
                        │  0.5-0.7: 🟡 Medium
                        │  0.7-0.9: 🟢 High   
                        │  0.9-1.0: 🟢🟢 Very High
                        └────────────────────┘
```

---

## 7. Redundancy Detection Flow

```
┌────────────────────────────────────────┐
│  SEARCH HISTORY                         │
│                                         │
│  Search 1: "Vietnam GDP 2024"           │
│  Search 2: "Thailand GDP 2024"          │
│  Search 3: "Vietnam population data"    │
│  Search 4: "Thailand population"        │
└──────────────────┬─────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
       
   For each      For each    Calculate
   search 1      search 2    overlap
       │          │          │
       ▼          ▼          ▼
   
   "Vietnam     "Thailand    Terms in S1:
    GDP         GDP          {vietnam, gdp, 2024}
    2024"       2024"
                           Terms in S2:
                           {thailand, gdp, 2024}
                           
                           Overlap: {gdp, 2024}
                           Score = 2/5 = 0.40
       │          │          │
       └──────────┼──────────┘
                  │
                  ▼
           ┌──────────────────┐
           │  Check: overlap  │
           │  > 0.50 ?        │
           └────────┬─────────┘
                    │
            ┌───────┴────────┐
            │                │
           NO               YES
            │                │
            ▼                ▼
         Continue      ADD TO REDUNDANT
                       ├─ Search 1: "Vietnam..."
                       ├─ Search 2: "Thailand..."
                       ├─ Overlap: 0.40
                       └─ Step diff: 2
                       
           ...continue
           with all pairs...
           
                    │
                    ▼
           ┌────────────────────────┐
           │  REDUNDANCY REPORT      │
           │                         │
           │  Total search pairs: 6  │
           │  Redundant pairs: 2     │
           │                         │
           │  Suggestions:           │
           │  - Vary search queries  │
           │  - Use different tools  │
           │  - Refine after first   │
           │    search failure       │
           └────────────────────────┘
```

---

## 8. Query Refinement Strategy

```
┌──────────────────────────────────────────┐
│  ORIGINAL QUERY (that failed or is long)  │
│                                           │
│  "What are the characteristics and       │
│   features and properties and aspects    │
│   of Vietnam economy?"                    │
└──────────────────┬───────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
    
    STRATEGY 1:         STRATEGY 2:
    Remove Noise        Simplify
        │                   │
        ▼                   ▼
    
    Split on spaces:    Keep first 3-4
    Filter length       important terms
    < 3 chars           
        │                   │
        ▼                   ▼
    
    Remove: "and"      "What are the
    Keep: "characteristics characteristics"
          "features"         vs
          "properties"    "Vietnam economy"
          "aspects"       
          "Vietnam"           │
          "economy"
        │
        ▼
    
    REFINED QUERY:      REFINED QUERY:
    "What are the       "What are the
     characteristics    characteristics
     features           of Vietnam"
     properties
     aspects of
     Vietnam economy"
    
     (removed short
      words)
    
                   │
                   ▼
        ┌──────────────────────┐
        │  TRACK REFINEMENT    │
        │                      │
        │  {                   │
        │    "original": "...",│
        │    "refined": "...", │
        │    "reason": "..."   │
        │  }                   │
        │                      │
        │  Logged for analysis │
        └──────────────────────┘
```

---

## 9. Complete Session Flow (End-to-End)

```
┌────────────────────────────────────────────────────────────┐
│  SESSION START                                              │
│                                                              │
│  1️⃣  User: "Compare Vietnam and Thailand economies"        │
└──────────────────┬─────────────────────────────────────────┘
                   │
                   ▼
        ┌─────────────────────────┐
        │  Initialize Agent       │
        │  - Reset search_history │
        │  - Reset tool_call_count│
        │  - Set error_count = 0  │
        └──────────┬──────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  ITERATION 1 (Step=1)    │
        ├──────────────────────────┤
        │  LLM: "I need to search  │
        │        for both GDP"     │
        │  Action: search(Vietnam) │
        │  Observation: $430B, 6.5%│
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  ITERATION 2 (Step=2)    │
        ├──────────────────────────┤
        │  LLM: "Now search        │
        │        Thailand"         │
        │  Action: search(Thailand)│
        │  Observation: $380B, 3%  │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  ITERATION 3 (Step=3)    │
        ├──────────────────────────┤
        │  LLM: "I have all info"  │
        │  Final Answer: "Vietnam  │
        │  is larger and faster    │
        │  growing"               │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  ANALYSIS POST-PROCESS   │
        ├──────────────────────────┤
        │  Search chain: [2]       │
        │  Multi-hop: true         │
        │  Redundancy: 1           │
        │  Confidence: 0.92        │
        │  Synthesis summary: [...] │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  LOGGING                 │
        ├──────────────────────────┤
        │  Event: AGENT_END        │
        │  Steps: 3                │
        │  Status: success         │
        │  Answer: "Vietnam..."    │
        │  Metrics: {...}          │
        └──────────┬───────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────┐
│  SESSION END & RETURN                                       │
│                                                              │
│  Answer: "Vietnam's economy is larger and growing faster"  │
│  Confidence: 0.92/1.0                                       │
│  Tests passed: 3/3 ✅                                       │
└────────────────────────────────────────────────────────────┘
```

---

## Summary: Key Flows

| Flow | Purpose | Time | Status |
|------|---------|------|--------|
| Main Execution | Core ReAct loop | 2-30s | ✅ Complete |
| Tool Execution | Tool lookup & execution | <1s | ✅ Complete |
| Multi-hop | Search chain analysis | <1s | ✅ Enhanced |
| Error Recovery | Handle failures gracefully | Variable | ✅ Complete |
| Prompt Selection | Choose v1 or v2 | <1s | ✅ Available |
| Confidence Scoring | Assess answer quality | <1s | ✅ Enhanced |
| Redundancy Detection | Find wasted searches | <1s | ✅ New |
| Query Refinement | Improve search queries | <1s | ✅ New |

---

## Navigation

- **[Main Documentation](AGENT_CORE_DOCUMENTATION.md)** - Full technical reference
- **[Test Results](PROGRESS_PERSON1.md)** - Test execution records
- **Test Files:** `test_react_loop.py`, `test_multihop_reasoning.py`
