from __future__ import annotations

from typing import Any, Dict, List

from src.agent.agent import ReActAgent
from src.cli_utils import build_provider, load_runtime_config, parse_args
from src.tools import TOOLS


def _build_agent_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "callable": tool["func"],
        }
        for tool in TOOLS
    ]


def _run_once(agent: ReActAgent, question: str) -> str:
    answer = agent.run(question)
    print("\n=== Final Answer ===")
    print(answer)
    return answer


def main() -> None:
    args = parse_args()
    config = load_runtime_config(args.provider, args.model)
    provider = build_provider(config)

    agent = ReActAgent(provider, _build_agent_tools(), max_steps=args.max_steps)

    if args.prompt:
        _run_once(agent, args.prompt)
        return

    print("Search demo (ReAct). Type 'exit' to quit.")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        _run_once(agent, question)


if __name__ == "__main__":
    main()
