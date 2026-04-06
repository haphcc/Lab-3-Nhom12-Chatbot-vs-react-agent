import ast
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []
<<<<<<< Updated upstream
        self.last_run: Dict[str, Any] = {}

    def get_system_prompt(self) -> str:
        """
        Build the system prompt that instructs the agent to follow ReAct.
        The tools are expected to accept a single string argument.
        """
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )
        return f"""
        You are an intelligent assistant. You have access to the following tools:
        {tool_descriptions}

        Use the following format:
        Thought: your line of reasoning.
        Action: tool_name("single string argument")
        Observation: result of the tool call.
        ... (repeat Thought/Action/Observation if needed)
        Final Answer: your final response.

        Rules:
        - Use a tool only when it is needed.
        - If you call a tool, wait for the Observation before deciding the next step.
        - Keep the Action on one line.
        - If you can answer directly, respond with Final Answer.
        """

    def run(self, user_input: str) -> str:
        """
        Run the ReAct loop until a final answer is produced or max_steps is reached.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        scratchpad = f"Question: {user_input}\n"
        steps = 0
        final_answer = ""

        while steps < self.max_steps:
            result = self.llm.generate(scratchpad, system_prompt=self.get_system_prompt())
            tracker.track_request(
                provider=result.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=result.get("usage", {}),
                latency_ms=result.get("latency_ms", 0),
            )

            response = result.get("content", "").strip()
            logger.log_event(
                "AGENT_STEP",
                {
                    "step": steps + 1,
                    "response": response,
                },
            )

            final_answer = self._extract_final_answer(response)
            if final_answer:
                break

            action = self._extract_action(response)
            if action:
                tool_name, tool_args = action
                observation = self._execute_tool(tool_name, tool_args)
                logger.log_event(
                    "TOOL_EXECUTION",
                    {
                        "tool": tool_name,
                        "args": tool_args,
                        "observation": observation,
                    },
                )
                scratchpad += f"{response}\nObservation: {observation}\n"
            else:
                scratchpad += f"{response}\n"

            steps += 1

        if not final_answer:
            final_answer = response if "response" in locals() and response else "I could not produce a final answer within the step limit."

        self.last_run = {
            "input": user_input,
            "steps": steps,
            "final_answer": final_answer,
        }
            
        logger.log_event("AGENT_END", {"steps": steps, "final_answer": final_answer})
        return final_answer

    def _extract_final_answer(self, response: str) -> str:
        match = re.search(r"Final Answer:\s*(.+)", response, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_action(self, response: str) -> Optional[tuple[str, str]]:
        match = re.search(r"Action:\s*([A-Za-z_][\w]*)\((.*?)\)", response, re.IGNORECASE | re.DOTALL)
        if not match:
            return None

        tool_name = match.group(1).strip()
        tool_args = match.group(2).strip()
        return tool_name, tool_args
=======
        
        # Multi-hop tracking
        self.search_history = []  # Track all searches to avoid redundant queries
        self.tool_call_count = {}  # Count calls per tool
        self.synthesis_steps = []  # Track information synthesis steps
        self.search_results_cache = {}  # Cache results to avoid redundant searches
        
        # Error tracking
        self.error_count = 0
        self.max_errors = 3  # Maximum consecutive errors before giving up
        
        # Reasoning quality tracking
        self.query_refinements = []  # Track query improvements made during reasoning
        self.confidence_scores = []  # Track confidence scores for answers

    def get_system_prompt(self) -> str:
        """
        System prompt that instructs the agent to follow ReAct format for search tasks.
        
        Returns:
            str: Complete system prompt with tool descriptions and format instructions
        """
        # Build tool descriptions
        tool_descriptions = []
        for tool in self.tools:
            desc = f"- **{tool['name']}**: {tool['description']}"
            if 'input_format' in tool:
                desc += f" | Input: {tool['input_format']}"
            if 'example' in tool:
                desc += f" | Example: {tool['example']}"
            tool_descriptions.append(desc)
        
        tools_text = "\n".join(tool_descriptions)
        
        # Complete system prompt
        return f"""You are an intelligent AI Research Assistant. Your job is to answer user questions by using the available tools.

## AVAILABLE TOOLS:
{tools_text}

## HOW TO WORK:

You MUST follow the ReAct (Reason + Act) format:

1. **Thought**: Think about what to do next
2. **Action**: Call a tool using the syntax: tool_name(arguments)
3. **Observation**: The system will provide the result (YOU do NOT write this)
4. Repeat Thought → Action → Observation until you have enough information
5. **Final Answer**: When you have all the info, provide the final answer

## EXAMPLES:

**Example 1: Simple question**
Question: What is the capital of Vietnam?
Thought: This is a basic geography question, I need to search for information
Action: search("capital of Vietnam")
Observation: Hanoi is the capital of Vietnam since 1976...
Thought: I have the information needed
Final Answer: The capital of Vietnam is Hanoi.

**Example 2: Question requiring calculation**
Question: Compare the population of Vietnam and Thailand, which country has more people?
Thought: I need to find the population of both countries to compare
Action: search("Vietnam population 2024")
Observation: Vietnam's population in 2024 is approximately 98.5 million
Thought: Now I need Thailand's population
Action: search("Thailand population 2024")
Observation: Thailand's population in 2024 is approximately 71.8 million
Thought: I have both numbers, I can compare now
Action: calculate("98.5 - 71.8")
Observation: 26.7
Thought: I have all the information to answer
Final Answer: Vietnam has a larger population than Thailand. Vietnam has 98.5 million people while Thailand has 71.8 million people, a difference of 26.7 million.

**Example 3: Multi-step reasoning**
Question: If Vietnam's GDP in 2023 was 430 billion USD and it grows 6.5% in 2024, what will be the GDP in 2024?
Thought: I need to calculate the growth
Action: calculate("430 * (1 + 0.065)")
Observation: 457.95
Thought: I have the result
Final Answer: Vietnam's GDP in 2024 will be approximately 457.95 billion USD.

## IMPORTANT RULES:

1. ✓ Call ONLY ONE tool per step
2. ✓ ALWAYS start with "Thought:" before taking action
3. ✓ Action must follow the format: tool_name(arguments)
4. ✓ DO NOT create your own Observation - the system provides it
5. ✓ Only use "Final Answer:" when you have ENOUGH information
6. ✗ DO NOT guess or make up information - if you don't know, search for it
7. ✗ DO NOT call tools that don't exist
8. ✗ DO NOT create fake results for Observation

Begin!"""

    def run(self, user_input: str) -> str:
        """
        Run the ReAct agent to answer a user question.
        
        Flow:
        1. User input → LLM
        2. Parse response → Thought + Action
        3. Execute tool → Observation
        4. Append observation to context
        5. Repeat until Final Answer or max_steps
        
        Args:
            user_input: The user's question
            
        Returns:
            str: The final answer or error message
        """
        from src.agent.parser import parse_thought, parse_action, parse_final_answer, has_final_answer
        
        logger.log_event("AGENT_START", {
            "input": user_input,
            "model": self.llm.model_name,
            "max_steps": self.max_steps
        })
        
        # Reset multi-hop tracking for new run
        self.search_history = []
        self.tool_call_count = {}
        self.error_count = 0
        
        # Initialize conversation history
        conversation = f"Question: {user_input}\n"
        steps = 0
        
        while steps < self.max_steps:
            steps += 1
            logger.log_event("LOOP_ITERATION", {"step": steps})
            
            # 1. Generate LLM response
            try:
                result = self.llm.generate(
                    prompt=conversation,
                    system_prompt=self.get_system_prompt()
                )
                response = result['content']
                
                logger.log_event("LLM_RESPONSE", {
                    "step": steps,
                    "response": response,
                    "tokens": result['usage'],
                    "latency_ms": result['latency_ms']
                })
                
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                return f"ERROR: Failed to get LLM response: {str(e)}"
            
            # 2. Check for Final Answer
            if has_final_answer(response):
                final_ans = parse_final_answer(response)
                
                # Calculate enhanced metrics for multi-hop reasoning
                search_analysis = self.get_search_chain_analysis()
                confidence = self.calculate_confidence_score(final_ans, num_sources=len(self.search_history))
                
                logger.log_event("AGENT_END", {
                    "steps": steps,
                    "status": "success",
                    "answer": final_ans,
                    "total_tool_calls": sum(self.tool_call_count.values()),
                    "tool_usage": self.tool_call_count,
                    "search_count": len(self.search_history),
                    "is_multi_hop": len(self.search_history) > 1,
                    # New multi-hop metrics
                    "search_chain_analysis": search_analysis,
                    "confidence_score": confidence,
                    "tool_diversity": len(self.tool_call_count),
                    "query_refinements_count": len(self.query_refinements),
                    "redundant_searches": len(self._find_redundant_searches())
                })
                return final_ans
            
            # 3. Parse Thought and Action
            thought = parse_thought(response)
            action = parse_action(response)
            
            if thought:
                logger.log_event("THOUGHT", {"step": steps, "content": thought})
            
            if action is None:
                # No valid action found - LLM not following format
                self.error_count += 1
                
                logger.log_event("PARSING_ERROR", {
                    "step": steps,
                    "response": response[:200],
                    "error": "No valid action found",
                    "consecutive_errors": self.error_count
                })
                
                # Check if too many errors
                if self.error_count >= self.max_errors:
                    logger.log_event("AGENT_END", {
                        "steps": steps,
                        "status": "too_many_errors",
                        "error_count": self.error_count
                    })
                    return f"ERROR: Agent failed after {self.error_count} consecutive parsing errors. The LLM is not following the ReAct format correctly."
                
                # Append error feedback to conversation
                conversation += f"\n{response}\n"
                conversation += "Observation: ERROR - You did not provide a valid Action. Please use the format: Action: tool_name(arguments)\n"
                continue
            
            # Reset error count on successful parse
            self.error_count = 0
            
            # 4. Execute tool
            tool_name = action['tool']
            tool_args = action['args']
            
            # Track tool usage
            self.tool_call_count[tool_name] = self.tool_call_count.get(tool_name, 0) + 1
            
            # Track searches for multi-hop analysis
            if tool_name == 'search':
                self.search_history.append(tool_args)
            
            logger.log_event("ACTION", {
                "step": steps,
                "tool": tool_name,
                "args": tool_args,
                "tool_call_number": self.tool_call_count[tool_name]
            })
            
            observation = self._execute_tool(tool_name, tool_args)
            
            # Check if tool execution resulted in error
            if "ERROR" in observation:
                self.error_count += 1
                logger.log_event("TOOL_ERROR_IN_OBSERVATION", {
                    "step": steps,
                    "tool": tool_name,
                    "error": observation[:200]
                })
            else:
                # Reset error count on successful tool execution
                self.error_count = 0
            
            logger.log_event("OBSERVATION", {
                "step": steps,
                "tool": tool_name,
                "result": observation[:200]  # Log first 200 chars
            })
            
            # 5. Append to conversation
            conversation += f"\n{response}\n"
            conversation += f"Observation: {observation}\n"
        
        # Reached max_steps without Final Answer
        logger.log_event("AGENT_END", {
            "steps": steps,
            "status": "max_steps_reached",
            "final_conversation": conversation[:500],
            "tool_usage": self.tool_call_count,
            "search_count": len(self.search_history)
        })
        
        return f"ERROR: Reached maximum {self.max_steps} steps without a final answer. The agent may be stuck in a loop or needs more steps to complete the task."
>>>>>>> Stashed changes

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Execute a tool by name and return the result.
        
        Args:
            tool_name: Name of the tool to execute
            args: Arguments for the tool (string)
            
        Returns:
            str: Result from the tool or error message
        """
        # Find the tool in registry
        tool_func = None
        for tool in self.tools:
            if tool['name'] == tool_name:
<<<<<<< Updated upstream
                tool_callable = tool.get("callable") or tool.get("function") or tool.get("handler")
                if callable(tool_callable):
                    parsed_args = args.strip()
                    if parsed_args.startswith("\"") and parsed_args.endswith("\""):
                        parsed_args = parsed_args[1:-1]
                    elif parsed_args.startswith("'") and parsed_args.endswith("'"):
                        parsed_args = parsed_args[1:-1]

                    try:
                        result = tool_callable(parsed_args)
                    except Exception as exc:
                        return f"Tool {tool_name} failed: {exc}"

                    return str(result)
                return f"Tool {tool_name} has no callable handler."
        return f"Tool {tool_name} not found."
=======
                tool_func = tool.get('function')
                break
        
        if tool_func is None:
            error_msg = f"ERROR: Tool '{tool_name}' not found. Available tools: {[t['name'] for t in self.tools]}"
            logger.log_event("TOOL_ERROR", {
                "error": "tool_not_found",
                "tool_name": tool_name,
                "available_tools": [t['name'] for t in self.tools]
            })
            return error_msg
        
        # Execute the tool
        try:
            logger.log_event("TOOL_CALL", {
                "tool": tool_name,
                "args": args
            })
            
            result = tool_func(args)
            
            logger.log_event("TOOL_SUCCESS", {
                "tool": tool_name,
                "result_length": len(str(result))
            })
            
            return str(result)
            
        except Exception as e:
            error_msg = f"ERROR executing tool '{tool_name}': {str(e)}"
            logger.log_event("TOOL_EXECUTION_ERROR", {
                "tool": tool_name,
                "error": str(e)
            })
            return error_msg

    def get_search_chain_analysis(self) -> Dict[str, Any]:
        """
        Analyze the search chain to understand multi-hop reasoning.
        
        Returns:
            Dict with analysis of the search chain
        """
        analysis = {
            "total_searches": len(self.search_history),
            "is_multi_hop": len(self.search_history) > 1,
            "search_chain": self.search_history,
            "search_topics": self._extract_search_topics(),
            "redundant_searches": self._find_redundant_searches(),
            "search_efficiency": len(self.search_history) / max(1, sum(self.tool_call_count.values())),
            "tool_diversity": len(self.tool_call_count)
        }
        return analysis
    
    def _extract_search_topics(self) -> List[str]:
        """Extract main topics from search queries."""
        topics = []
        for query in self.search_history:
            # Simple topic extraction: split by key words and extract main nouns
            words = query.lower().split()
            topics.extend(words)
        return list(set(topics))  # Remove duplicates
    
    def _find_redundant_searches(self) -> List[Dict[str, Any]]:
        """
        Identify potentially redundant searches.
        Two searches are potentially redundant if they have high term overlap.
        
        Returns:
            List of redundant search pairs
        """
        redundant = []
        for i, search1 in enumerate(self.search_history):
            for j, search2 in enumerate(self.search_history[i+1:], i+1):
                # Calculate term overlap
                terms1 = set(search1.lower().split())
                terms2 = set(search2.lower().split())
                overlap = len(terms1 & terms2) / max(len(terms1 | terms2), 1)
                
                if overlap > 0.5:  # More than 50% overlap
                    redundant.append({
                        "search1": search1,
                        "search2": search2,
                        "overlap_score": overlap,
                        "step_diff": j - i
                    })
        return redundant
    
    def calculate_confidence_score(self, final_answer: str, num_sources: int = 1) -> float:
        """
        Calculate confidence score for the final answer based on:
        - Number of sources used
        - Number of search steps
        - Tool diversity
        
        Args:
            final_answer: The final answer provided
            num_sources: Number of sources cited in the answer
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        score = 0.5  # Base score
        
        # Increase score based on number of sources
        score += min(0.2, num_sources * 0.1)
        
        # Increase score for multi-hop reasoning
        if len(self.search_history) > 1:
            score += 0.15
        
        # Increase score for tool diversity
        score += min(0.15, len(self.tool_call_count) * 0.075)
        
        # Decrease score if there were errors
        score -= self.error_count * 0.1
        
        # Cap score between 0.0 and 1.0
        return max(0.0, min(1.0, score))
    
    def suggest_query_refinement(self, original_query: str, failed_searches: List[str] = None) -> Optional[str]:
        """
        Suggest a refined version of a search query if the original didn't yield good results.
        
        Args:
            original_query: The original search query
            failed_searches: List of searches that didn't yield results
            
        Returns:
            str: Suggested refined query, or None if no refinement needed
        """
        # Simple heuristic: if query has uncommon terms, suggest removing them
        terms = original_query.lower().split()
        
        # Remove very short terms (< 3 chars) as they might be noise
        filtered = [t for t in terms if len(t) >= 3]
        
        if len(filtered) < len(terms):
            refined = " ".join(filtered)
            self.query_refinements.append({
                "original": original_query,
                "refined": refined,
                "reason": "Removed short terms (noise)"
            })
            return refined
        
        # If original query has many terms, try simplifying to top 3-4 terms
        if len(terms) > 4:
            # Keep first and last important terms
            simplified = " ".join(terms[:3] + terms[-1:])
            self.query_refinements.append({
                "original": original_query,
                "refined": simplified,
                "reason": "Simplified to key terms"
            })
            return simplified
        
        return None
    
    def get_synthesis_summary(self) -> str:
        """
        Generate a summary of how the final answer was synthesized from multiple sources.
        
        Returns:
            str: Summary of the reasoning process
        """
        summary_lines = []
        
        if len(self.search_history) > 1:
            summary_lines.append(f"🔍 Information Synthesis Chain:")
            for i, search in enumerate(self.search_history, 1):
                summary_lines.append(f"  Step {i}: Searched for '{search}'")
        
        if self.tool_call_count:
            summary_lines.append(f"\n🛠️  Tools Used:")
            for tool, count in self.tool_call_count.items():
                summary_lines.append(f"  - {tool}: {count} call(s)")
        
        if self.query_refinements:
            summary_lines.append(f"\n✨ Query Refinements:")
            for refinement in self.query_refinements:
                summary_lines.append(f"  - Original: '{refinement['original']}'")
                summary_lines.append(f"    Refined:  '{refinement['refined']}'")
        
        return "\n".join(summary_lines)
>>>>>>> Stashed changes
