from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Tuple

from src.agent.agent import ReActAgent
from src.cli_utils import build_provider, load_runtime_config, parse_args
from src.core.llm_provider import LLMProvider
from src.tools import TOOLS


def _wrap_tools_for_counting(tools: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    calls: List[Dict[str, Any]] = []
    wrapped: List[Dict[str, Any]] = []

    for tool in tools:
        func = tool["func"]

        def make_wrapper(name: str, inner: Callable[[str], str]):
            def wrapper(arg: str) -> str:
                observation = inner(arg)
                calls.append({"tool": name, "arg": arg, "observation": observation})
                return observation

            return wrapper

        wrapped.append(
            {
                "name": tool["name"],
                "description": tool["description"],
                "callable": make_wrapper(tool["name"], func),
            }
        )

    return wrapped, calls


def _run_chatbot(provider: LLMProvider, question: str) -> Dict[str, Any]:
    return provider.generate(
        question,
        system_prompt=(
            "You are a helpful chatbot. Answer directly using your internal knowledge only. "
            "Do not claim to browse the web or call tools. If you are unsure, say so."
        ),
    )


def _print_block(title: str, content: str, latency_ms: int | None = None) -> None:
    print(f"\n=== {title} ===")
    if latency_ms is not None:
        print(f"Latency: {latency_ms} ms")
    print(content)


def main() -> None:
    args = parse_args()
    config = load_runtime_config(args.provider, args.model)
    provider = build_provider(config)
    question = args.prompt or input("Enter a search question: ").strip()

    chatbot_start = time.time()
    chatbot_result = _run_chatbot(provider, question)
    chatbot_ms = chatbot_result.get("latency_ms", int((time.time() - chatbot_start) * 1000))

    agent_tools, tool_calls = _wrap_tools_for_counting(TOOLS)
    agent = ReActAgent(provider, agent_tools, max_steps=args.max_steps)
    agent_start = time.time()
    agent_answer = agent.run(question)
    agent_ms = int((time.time() - agent_start) * 1000)

    _print_block("Chatbot", chatbot_result.get("content", ""), latency_ms=chatbot_ms)
    _print_block("Agent", agent_answer, latency_ms=agent_ms)

    print("\n=== Side-by-side Notes ===")
    print(f"Tool calls: {len(tool_calls)}")
    for idx, call in enumerate(tool_calls, start=1):
        observation_line = call["observation"].splitlines()[0] if call["observation"] else ""
        print(f"{idx}. {call['tool']}({call['arg']}) -> {observation_line}")


if __name__ == "__main__":
    main()
