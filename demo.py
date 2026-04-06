from src.cli_utils import build_provider, interactive_loop, load_runtime_config, parse_args


def main() -> None:
    args = parse_args()
    config = load_runtime_config(args.provider, args.model)
    provider = build_provider(config)
    interactive_loop("agent", provider, args.max_steps)


if __name__ == "__main__":
    main()