import os
import sys
import time
from typing import Dict, Any, List

import streamlit as st
from dotenv import load_dotenv

from analysis.generate_demo_search_logs import generate_demo_logs
from analysis.search_analyzer import run_analysis
from analysis.search_dashboard import build_dashboard
from src.agent.agent import ReActAgent
from src.cli_utils import RuntimeConfig, build_provider
from src.telemetry.logger import logger
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


def _render_analysis_outputs(analysis_dir: str) -> None:
    summary_path = os.path.join(analysis_dir, "search_metrics_summary.json")
    dashboard_md_path = os.path.join(analysis_dir, "dashboard.md")

    st.subheader("Search Telemetry Outputs")
    st.caption(f"Log file hien tai: {logger.get_current_log_file()}")

    if os.path.exists(summary_path):
        import json

        with open(summary_path, "r", encoding="utf-8") as handle:
            summary = json.load(handle)
        st.json(summary)
    else:
        st.info("Chua co file summary. Hay chay tao log mau va analyzer truoc.")

    chart_files = [
        "search_count_distribution.png",
        "avg_searches_by_category.png",
        "tool_usage_heatmap.png",
        "quality_scatter.png",
        "query_refinement_effectiveness.png",
        "failure_breakdown.png",
        "multi_hop_comparison.png",
    ]
    for chart_name in chart_files:
        chart_path = os.path.join(analysis_dir, chart_name)
        if os.path.exists(chart_path):
            st.image(chart_path, caption=chart_name, use_container_width=True)

    if os.path.exists(dashboard_md_path):
        with open(dashboard_md_path, "r", encoding="utf-8") as handle:
            st.markdown(handle.read())


def _render_monitoring_tab() -> None:
    st.header("Search Monitoring Workspace")
    st.write("Tao log mau, chay phan tich va xem dashboard ngay trong giao dien hien co.")

    log_path = st.text_input("Telemetry log file", value=os.path.join("logs", "sample.log"))
    analysis_dir = st.text_input("Analysis output dir", value=os.path.join("analysis", "output"))

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("1. Generate Demo Logs", use_container_width=True):
            path = generate_demo_logs(log_path)
            st.success(f"Da tao log demo: {path}")
    with col2:
        if st.button("2. Run Analyzer", use_container_width=True):
            report = run_analysis(log_path, analysis_dir)
            st.success("Da sinh file phan tich.")
            st.json(report.get("overall", {}))
    with col3:
        if st.button("3. Build Dashboard", use_container_width=True):
            outputs = build_dashboard(analysis_dir)
            st.success("Da tao dashboard va bieu do.")
            st.json(outputs)

    st.divider()
    _render_analysis_outputs(analysis_dir)


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Chatbot vs ReAct Agent", page_icon="🤖", layout="wide")
    st.title("Chatbot vs ReAct Agent")
    st.caption("Simple UI to compare direct chatbot answers and tool-using ReAct agent.")

    app_tab, monitor_tab = st.tabs(["Agent Playground", "Search Monitoring"])

    with app_tab:
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
        elif not prompt.strip():
            st.warning("Hay nhap cau hoi truoc khi chay.")
        else:
            try:
                config = _build_runtime_config(provider_name, model_name, max_steps)
                provider = build_provider(config)
            except Exception as exc:
                st.error(f"Khong the khoi tao provider: {exc}")
            else:
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
                    st.caption(f"Telemetry log: {logger.get_current_log_file()}")

    with monitor_tab:
        _render_monitoring_tab()


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
