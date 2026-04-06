import time

from src.cli_utils import build_provider, load_runtime_config, parse_args, print_result_block, run_agent, run_chatbot


def main() -> None:
    args = parse_args()
    config = load_runtime_config(args.provider, args.model)
    provider = build_provider(config)
    prompt = args.prompt or input("Enter a question for comparison: ").strip()

    chatbot_start = time.time()
    chatbot_result = run_chatbot(provider, prompt)
    chatbot_total_ms = int((time.time() - chatbot_start) * 1000)

    agent_start = time.time()
    agent_result = run_agent(provider, prompt, max_steps=args.max_steps)
    agent_total_ms = int((time.time() - agent_start) * 1000)

    print_result_block("Chatbot", chatbot_result["content"], latency_ms=chatbot_result.get("latency_ms", chatbot_total_ms))
    print_result_block(
        "Agent",
        agent_result["content"],
        latency_ms=agent_result.get("latency_ms", agent_total_ms),
        steps=agent_result.get("steps"),
    )

    print("\n=== Comparison Summary ===")
    print(f"Question: {prompt}")
    print(f"Chatbot latency: {chatbot_result.get('latency_ms', chatbot_total_ms)} ms")
    print(f"Agent latency: {agent_result.get('latency_ms', agent_total_ms)} ms")
    print("Difference: agent can use tools and multi-step reasoning; chatbot answers directly.")


if __name__ == "__main__":
    main()