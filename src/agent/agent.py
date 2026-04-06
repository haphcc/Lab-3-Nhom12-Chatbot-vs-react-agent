import re
from typing import List, Dict, Any, Optional

from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []
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
        You are an intelligent assistant with tool-use capabilities.
        Your primary goal is to produce a high-quality final answer, not just intermediate reasoning.

        Available tools:
        {tool_descriptions}

        Required format:
        Thought: brief reasoning for the next step.
        Action: tool_name("single string argument")
        Observation: result of the tool call (provided by system)
        ... repeat if needed ...
        Final Answer: complete response for the user.

        Rules:
        - Use at most one tool per step.
        - If a tool is needed, wait for Observation before next action.
        - Keep Action on one line.
        - Prefer evidence-based answers from observations when available.
        - Final Answer should be clear, specific, and useful (not one short vague sentence).
        - Match the user's language.
        """

    def _build_synthesis_prompt(self) -> str:
        return (
            "You are a careful assistant that writes the final user-facing answer from ReAct traces. "
            "Use the provided observations when possible, avoid exposing chain-of-thought, and avoid tool syntax. "
            "Answer directly and clearly with enough detail to be useful. "
            "If information is uncertain or missing, explicitly say what is uncertain. "
            "Match the user's language."
        )

    def _synthesize_final_answer(self, user_input: str, scratchpad: str, latest_response: str) -> str:
        synthesis_input = (
            f"User question: {user_input}\n\n"
            f"ReAct trace:\n{scratchpad}\n"
            f"Latest model response:\n{latest_response}\n\n"
            "Write only the final answer for the user."
        )
        result = self.llm.generate(synthesis_input, system_prompt=self._build_synthesis_prompt())
        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=self.llm.model_name,
            usage=result.get("usage", {}),
            latency_ms=result.get("latency_ms", 0),
        )
        return result.get("content", "").strip()

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
            if "response" in locals() and response:
                synthesized = self._synthesize_final_answer(user_input, scratchpad, response)
                final_answer = synthesized or response
            else:
                final_answer = "I could not produce a final answer within the step limit."

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

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Execute a tool by name and return the result.
        """
        for tool in self.tools:
            if tool["name"] == tool_name:
                tool_callable = tool.get("callable") or tool.get("function") or tool.get("handler")
                if callable(tool_callable):
                    parsed_args = args.strip()
                    if parsed_args.startswith('"') and parsed_args.endswith('"'):
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
