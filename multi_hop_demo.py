from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Tuple

from src.agent.agent import ReActAgent
from src.cli_utils import build_provider, load_runtime_config, parse_args
from src.tools import TOOLS


class MultiHopSearchAgent(ReActAgent):
    """A ReAct agent variant that is nudged to perform multi-hop search."""

    def get_system_prompt(self) -> str:
        base = super().get_system_prompt()
        return (
            base
            + "\n\n"
            + "Multi-hop requirement:\n"
            + "- Before Final Answer, you MUST perform at least 3 tool calls.\n"
            + "- Prefer calling search() multiple times with refined sub-questions.\n"
            + "- Then optionally use fact_check() to verify.\n"
            + "- In Final Answer, cite sources shown in tool outputs.\n"
        )


def _wrap_tools_for_trace(tools: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    trace: List[Dict[str, Any]] = []
    wrapped: List[Dict[str, Any]] = []

    for tool in tools:
        func = tool["func"]

        def make_wrapper(name: str, inner: Callable[[str], str]):
            def wrapper(arg: str) -> str:
                observation = inner(arg)
                trace.append({"tool": name, "arg": arg, "observation": observation})
                return observation

            return wrapper

        wrapped.append(
            {
                "name": tool["name"],
                "description": tool["description"],
                "callable": make_wrapper(tool["name"], func),
            }
        )

    return wrapped, trace


def main() -> None:
    args = parse_args()
    config = load_runtime_config(args.provider, args.model)
    provider = build_provider(config)

    question = args.prompt or (
        "Gia vang hom nay o Viet Nam la bao nhieu va thong tin nay co nhat quan giua hai nguon khong? "
        "Neu co, hay giai thich ngan gon."
    )

    tools, trace = _wrap_tools_for_trace(TOOLS)
    agent = MultiHopSearchAgent(provider, tools, max_steps=max(args.max_steps, 6))

    start = time.time()
    answer = agent.run(question)
    latency_ms = int((time.time() - start) * 1000)

    print("\n=== Multi-hop Question ===")
    print(question)

    print("\n=== Reasoning Chain (Tool Trace) ===")
    for idx, item in enumerate(trace, start=1):
        first_line = item["observation"].splitlines()[0] if item["observation"] else ""
        print(f"{idx}. {item['tool']}({item['arg']}) -> {first_line}")

    print("\n=== Final Answer ===")
    print(f"Latency: {latency_ms} ms")
    print(answer)


if __name__ == "__main__":
    main()
