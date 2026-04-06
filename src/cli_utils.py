import argparse
import os
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.core.llm_provider import LLMProvider
from src.telemetry.metrics import tracker
from src.tools.demo_tools import build_demo_tools


@dataclass
class RuntimeConfig:
    provider: str
    model: str
    local_model_path: str
    max_steps: int = 5


def load_runtime_config(provider_override: Optional[str] = None, model_override: Optional[str] = None) -> RuntimeConfig:
    load_dotenv()
    provider = (provider_override or os.getenv("DEFAULT_PROVIDER", "openai")).strip().lower()
    model = model_override or os.getenv("DEFAULT_MODEL", "gpt-4o")
    local_model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
    return RuntimeConfig(provider=provider, model=model, local_model_path=local_model_path)


def build_provider(config: RuntimeConfig) -> LLMProvider:
    if config.provider == "openai":
        from src.core.openai_provider import OpenAIProvider

        return OpenAIProvider(model_name=config.model, api_key=os.getenv("OPENAI_API_KEY"))
    if config.provider in {"google", "gemini"}:
        from src.core.gemini_provider import GeminiProvider

        return GeminiProvider(model_name=config.model, api_key=os.getenv("GEMINI_API_KEY"))
    if config.provider == "local":
        from src.core.local_provider import LocalProvider

        return LocalProvider(model_path=config.local_model_path)
    raise ValueError(f"Unsupported provider: {config.provider}")


def build_agent(provider: LLMProvider, max_steps: int = 5) -> ReActAgent:
    return ReActAgent(provider, build_demo_tools(), max_steps=max_steps)


def run_chatbot(provider: LLMProvider, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
    direct_prompt = prompt.strip()
    result = provider.generate(
        direct_prompt,
        system_prompt=system_prompt or "You are a helpful chatbot. Answer directly and do not use tools.",
    )
    tracker.track_request(
        provider=result.get("provider", "unknown"),
        model=provider.model_name,
        usage=result.get("usage", {}),
        latency_ms=result.get("latency_ms", 0),
    )
    return result


def run_agent(provider: LLMProvider, prompt: str, max_steps: int = 5) -> Dict[str, Any]:
    agent = build_agent(provider, max_steps=max_steps)
    start = time.time()
    answer = agent.run(prompt)
    latency_ms = int((time.time() - start) * 1000)
    return {
        "content": answer,
        "latency_ms": latency_ms,
        "steps": agent.last_run.get("steps", 0),
        "provider": provider.model_name,
    }


def print_result_block(title: str, content: str, latency_ms: Optional[int] = None, steps: Optional[int] = None) -> None:
    print(f"\n=== {title} ===")
    if latency_ms is not None:
        print(f"Latency: {latency_ms} ms")
    if steps is not None:
        print(f"Steps: {steps}")
    print(content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lab 3 entry points for chatbot and ReAct agent demos.")
    parser.add_argument("--provider", choices=["openai", "google", "gemini", "local"], help="Override DEFAULT_PROVIDER from .env")
    parser.add_argument("--model", help="Override DEFAULT_MODEL from .env")
    parser.add_argument("--prompt", help="Single prompt to run non-interactively")
    parser.add_argument("--max-steps", type=int, default=5, help="Maximum ReAct steps before stopping")
    parser.add_argument("--interactive", action="store_true", help="Start an interactive prompt loop")
    return parser.parse_args()


def interactive_loop(mode: str, provider: LLMProvider, max_steps: int) -> None:
    print(f"Running {mode} demo. Type 'exit' to quit.")
    while True:
        prompt = input("You: ").strip()
        if prompt.lower() in {"exit", "quit"}:
            break

        if mode == "chatbot":
            result = run_chatbot(provider, prompt)
            print_result_block("Chatbot", result["content"], latency_ms=result.get("latency_ms"))
        else:
            result = run_agent(provider, prompt, max_steps=max_steps)
            print_result_block("Agent", result["content"], latency_ms=result.get("latency_ms"), steps=result.get("steps"))