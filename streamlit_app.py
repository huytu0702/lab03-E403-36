from __future__ import annotations

from typing import Any, Dict, List

import requests
import streamlit as st

from src.core.config import get_settings
from src.evaluation.benchmark_cases import BENCHMARK_CASES


settings = get_settings()
BASE_URL = f"http://{settings.api_host}:{settings.api_port}/api/v1"
CHAT_URL = f"{BASE_URL}/chat"
METRICS_URL = f"{BASE_URL}/metrics/summary"

st.set_page_config(page_title=settings.app_name, layout="wide")
st.title("Smart E-commerce Assistant")
st.caption("Compare `v1` chatbot và `v2` ReAct agent trên cùng input, kèm reasoning log từng bước.")


def _post_chat(message: str, version: str) -> Dict[str, Any]:
    response = requests.post(
        CHAT_URL,
        json={"message": message, "version": version, "session_id": "streamlit-demo"},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def _get_metrics() -> Dict[str, Any]:
    response = requests.get(METRICS_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def _render_reasoning_steps(steps: List[Dict[str, Any]]) -> None:
    if not steps:
        st.caption("Không có reasoning log.")
        return

    for step in steps:
        header = f"Step {step.get('step', '?')} • {step.get('phase') or step.get('status', 'detail')}"
        with st.expander(header, expanded=False):
            for key, value in step.items():
                if key == "step":
                    continue
                st.markdown(f"**{key}**")
                st.json(value) if isinstance(value, (dict, list)) else st.write(value)


def _render_single_result(title: str, result: Dict[str, Any]) -> None:
    st.subheader(title)
    st.write(result.get("answer", "No answer"))

    col1, col2, col3 = st.columns(3)
    col1.metric("Status", result.get("status", "unknown"))
    col2.metric("Latency", f"{result.get('latency_ms', 0)} ms")
    col3.metric("Steps", result.get("steps", 0))

    col4, col5, col6 = st.columns(3)
    col4.metric("LLM Calls", result.get("llm_calls", 0))
    col5.metric("Total Tokens", result.get("token_usage", {}).get("total_tokens", 0))
    col6.metric("Cost", f"{result.get('cost_estimate', 0.0):.4f}")

    st.caption(
        f"Provider: `{result.get('provider') or '-'}` | Model: `{result.get('model') or '-'}` | Trace: `{result.get('trace_id') or '-'}`"
    )

    st.markdown("**Tool Calls**")
    st.json(result.get("tool_calls", []))
    st.markdown("**Reasoning Steps**")
    _render_reasoning_steps(result.get("reasoning_steps", []))


def _render_compare_result(result: Dict[str, Any]) -> None:
    compare_results = result.get("compare_results") or {}
    col_left, col_right = st.columns(2)
    with col_left:
        _render_single_result("v1", compare_results.get("v1", {}))
    with col_right:
        _render_single_result("v2", compare_results.get("v2", {}))


def _run_benchmark() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for case in BENCHMARK_CASES:
        result = _post_chat(case["message"], "compare")
        compare_results = result.get("compare_results", {})
        v1 = compare_results.get("v1", {})
        v2 = compare_results.get("v2", {})
        rows.append(
            {
                "case": case["title"],
                "expected_winner": case["expected_winner"],
                "v1_status": v1.get("status"),
                "v1_latency_ms": v1.get("latency_ms"),
                "v1_steps": v1.get("steps"),
                "v1_trace_id": v1.get("trace_id"),
                "v2_status": v2.get("status"),
                "v2_latency_ms": v2.get("latency_ms"),
                "v2_steps": v2.get("steps"),
                "v2_trace_id": v2.get("trace_id"),
            }
        )
    return rows


st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("benchmark_rows", [])

with st.sidebar:
    st.header("Controls")
    query_mode = st.radio("Query mode", ["compare", "v1", "v2"], index=0)
    if st.button("Refresh metrics", use_container_width=True):
        try:
            st.session_state["metrics_summary"] = _get_metrics()
        except Exception as exc:
            st.session_state["metrics_error"] = str(exc)
    if st.button("Run 5-case benchmark", use_container_width=True):
        try:
            st.session_state["benchmark_rows"] = _run_benchmark()
            st.session_state.pop("benchmark_error", None)
        except Exception as exc:
            st.session_state["benchmark_error"] = str(exc)

    st.divider()
    st.subheader("Metrics Summary")
    try:
        metrics_summary = st.session_state.get("metrics_summary") or _get_metrics()
        st.json(metrics_summary)
    except Exception as exc:
        st.warning(f"Không đọc được metrics: {exc}")

message = st.text_area(
    "Message",
    value="Tôi muốn mua 2 iPhone 15 dùng mã WINNER10 ship Hà Nội",
    height=120,
)

if st.button("Send", type="primary"):
    try:
        data = _post_chat(message, query_mode)
        st.session_state["chat_history"].insert(0, {"message": message, "mode": query_mode, "response": data})
    except Exception as exc:
        st.error(f"Request failed: {exc}")

if st.session_state["chat_history"]:
    current = st.session_state["chat_history"][0]
    st.markdown("## Current Result")
    st.caption(f"Mode: `{current['mode']}`")
    if current["mode"] == "compare":
        _render_compare_result(current["response"])
    else:
        _render_single_result(current["mode"], current["response"])

if st.session_state["benchmark_rows"]:
    st.markdown("## Benchmark 5 Cases")
    st.dataframe(st.session_state["benchmark_rows"], use_container_width=True)
elif st.session_state.get("benchmark_error"):
    st.warning(f"Không chạy được benchmark: {st.session_state['benchmark_error']}")

if st.session_state["chat_history"]:
    st.markdown("## Chat History")
    for item in st.session_state["chat_history"][1:]:
        with st.expander(f"{item['mode']} • {item['message'][:80]}", expanded=False):
            if item["mode"] == "compare":
                _render_compare_result(item["response"])
            else:
                _render_single_result(item["mode"], item["response"])
