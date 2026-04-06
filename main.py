from src.cli_utils import (
    build_provider,
    interactive_loop,
    load_runtime_config,
    parse_args,
    print_result_block,
    run_agent,
    run_chatbot,
)


def main() -> None:
    args = parse_args()
    config = load_runtime_config(args.provider, args.model)
    config.max_steps = args.max_steps
    provider = build_provider(config)

    if args.interactive or not args.prompt:
        interactive_loop("agent", provider, config.max_steps)
        return

    result = run_agent(provider, args.prompt, max_steps=config.max_steps)
    print_result_block("Agent", result["content"], latency_ms=result.get("latency_ms"), steps=result.get("steps"))


if __name__ == "__main__":
    main()