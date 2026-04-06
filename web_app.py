import os
import sys
import time
from typing import Dict, Any, List

import streamlit as st
from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.cli_utils import RuntimeConfig, build_provider
from src.tools import TOOLS


def _build_agent_tools() -> List[Dict[str, Any]]:
    mapped_tools: List[Dict[str, Any]] = []
    for tool in TOOLS:
        mapped_tools.append(
            {
                "name": tool["name"],
                "description": tool["description"],
                "callable": tool["func"],
            }
        )
    return mapped_tools


def _build_runtime_config(provider_name: str, model_name: str, max_steps: int) -> RuntimeConfig:
    local_model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
    return RuntimeConfig(provider=provider_name, model=model_name, local_model_path=local_model_path, max_steps=max_steps)


def run_chatbot_answer(provider, prompt: str) -> Dict[str, Any]:
    response = provider.generate(
        prompt.strip(),
        system_prompt="You are a helpful chatbot. Answer directly and clearly.",
    )
    return {
        "content": response.get("content", ""),
        "latency_ms": response.get("latency_ms", 0),
    }


def run_agent_answer(provider, prompt: str, max_steps: int) -> Dict[str, Any]:
    agent = ReActAgent(provider, _build_agent_tools(), max_steps=max_steps)
    start = time.time()
    content = agent.run(prompt)
    latency_ms = int((time.time() - start) * 1000)
    return {
        "content": content,
        "latency_ms": latency_ms,
        "steps": agent.last_run.get("steps", 0),
    }


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Chatbot vs ReAct Agent", page_icon="🤖", layout="wide")
    st.title("Chatbot vs ReAct Agent")
    st.caption("Simple UI to compare direct chatbot answers and tool-using ReAct agent.")

    with st.sidebar:
        st.header("Settings")
        provider_name = st.selectbox("Provider", ["openai", "google", "gemini", "local"], index=0)
        default_model = os.getenv("DEFAULT_MODEL", "gpt-4o")
        model_name = st.text_input("Model", value=default_model)
        max_steps = st.slider("Max agent steps", min_value=1, max_value=10, value=5)
        mode = st.radio("Mode", ["Agent", "Chatbot", "Compare"], index=0)
        st.checkbox("Use search API (if configured)", key="search_api")

    os.environ["SEARCH_USE_API"] = "true" if st.session_state.get("search_api") else "false"

    prompt = st.text_area("Your question", height=120, placeholder="Vi du: Gia vang hom nay la bao nhieu?")
    run_clicked = st.button("Run", type="primary")

    if not run_clicked:
        st.info("Nhap cau hoi va bam Run.")
        return

    if not prompt.strip():
        st.warning("Hay nhap cau hoi truoc khi chay.")
        return

    try:
        config = _build_runtime_config(provider_name, model_name, max_steps)
        provider = build_provider(config)
    except Exception as exc:
        st.error(f"Khong the khoi tao provider: {exc}")
        return

    if mode in {"Chatbot", "Compare"}:
        with st.spinner("Chatbot dang tra loi..."):
            chatbot_result = run_chatbot_answer(provider, prompt)
        st.subheader("Chatbot")
        st.write(chatbot_result["content"])
        st.caption(f"Latency: {chatbot_result['latency_ms']} ms")

    if mode in {"Agent", "Compare"}:
        with st.spinner("Agent dang suy luan va goi tools..."):
            agent_result = run_agent_answer(provider, prompt, max_steps=max_steps)
        st.subheader("ReAct Agent")
        st.write(agent_result["content"])
        st.caption(f"Latency: {agent_result['latency_ms']} ms | Steps: {agent_result['steps']}")


def _running_inside_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx() is not None
    except Exception:
        return False


def _launch_streamlit_app() -> None:
    from streamlit.web import cli as stcli

    app_path = os.path.abspath(__file__)
    sys.argv = ["streamlit", "run", app_path]
    raise SystemExit(stcli.main())


if __name__ == "__main__":
    if _running_inside_streamlit():
        main()
    else:
        _launch_streamlit_app()
