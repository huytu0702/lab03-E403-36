from __future__ import annotations

from typing import Any, Dict, List

import requests
import streamlit as st

from src.core.config import get_settings
from src.evaluation.benchmark_cases import BENCHMARK_CASES


settings = get_settings()
BASE_URL = f"http://{settings.api_host}:{settings.api_port}/api/v1"
CHAT_URL = f"{BASE_URL}/chat"
HEALTH_URL = f"{BASE_URL}/health"
METRICS_URL = f"{BASE_URL}/metrics/summary"

DEFAULT_PROMPTS = {
    "FAQ đổi trả": "Chính sách đổi trả là gì?",
    "FAQ cuối tuần": "Shop có giao hàng cuối tuần không?",
    "Quote nhiều bước": "Tôi muốn mua 2 iPhone 15, dùng mã WINNER10 và ship Hà Nội. Tổng bao nhiêu?",
    "Kiểm tra hàng": "MacBook Air M3 còn hàng không? Nếu mua 1 cái ship TP.HCM thì hết bao nhiêu?",
    "Edge case coupon": "Mua 3 AirPods Pro 2 dùng mã SAVE999 ship Đà Nẵng.",
}


st.set_page_config(page_title=settings.app_name, layout="wide")
st.title("Smart E-commerce Assistant")
st.caption("Compare `v1` chatbot và `v2` ReAct agent trên cùng input, kèm reasoning log từng bước.")


def _get_json(url: str, timeout: int = 30) -> Dict[str, Any]:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _post_chat(message: str, version: str, session_id: str) -> Dict[str, Any]:
    response = requests.post(
        CHAT_URL,
        json={"message": message, "version": version, "session_id": session_id},
        timeout=60,
    )
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
                if isinstance(value, (dict, list)):
                    st.json(value)
                else:
                    st.write(value)


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
        f"Provider: `{result.get('provider') or '-'}` | "
        f"Model: `{result.get('model') or '-'}` | "
        f"Trace: `{result.get('trace_id') or '-'}` | "
        f"Error: `{result.get('error_code') or '-'}'"
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


def _run_benchmark(session_id_prefix: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for case in BENCHMARK_CASES:
        result = _post_chat(case["message"], "compare", f"{session_id_prefix}-{case['id']}")
        compare_results = result.get("compare_results") or {}
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
st.session_state.setdefault("message", DEFAULT_PROMPTS["Quote nhiều bước"])
st.session_state.setdefault("session_id", "streamlit-demo")

with st.sidebar:
    st.header("Controls")
    query_mode = st.radio("Query mode", ["compare", "v1", "v2"], index=0)
    selected_prompt = st.selectbox("Prompt mẫu", list(DEFAULT_PROMPTS.keys()))
    if st.button("Nạp prompt", use_container_width=True):
        st.session_state["message"] = DEFAULT_PROMPTS[selected_prompt]

    session_id = st.text_input("Session ID", key="session_id")

    if st.button("Refresh metrics", use_container_width=True):
        try:
            st.session_state["metrics_summary"] = _get_json(METRICS_URL)
            st.session_state.pop("metrics_error", None)
        except Exception as exc:
            st.session_state["metrics_error"] = str(exc)

    if st.button("Run 5-case benchmark", use_container_width=True):
        try:
            st.session_state["benchmark_rows"] = _run_benchmark(session_id)
            st.session_state.pop("benchmark_error", None)
        except Exception as exc:
            st.session_state["benchmark_error"] = str(exc)

    st.divider()
    st.subheader("Health check")
    try:
        health = _get_json(HEALTH_URL, timeout=10)
        st.success(f"API: {health.get('status', 'unknown')}")
        db_info = health.get("database", {})
        st.write(f"DB mode: `{db_info.get('mode', 'unknown')}`")
        st.write(f"DB available: `{db_info.get('available', False)}`")
    except Exception as exc:
        st.error(f"Không đọc được health check: {exc}")

    st.divider()
    st.subheader("Metrics Summary")
    try:
        metrics_summary = st.session_state.get("metrics_summary") or _get_json(METRICS_URL)
        st.json(metrics_summary)
    except Exception as exc:
        st.warning(f"Không đọc được metrics: {exc}")

message = st.text_area("Message", key="message", height=120)

if st.button("Send", type="primary"):
    if not message.strip():
        st.warning("Bạn hãy nhập câu hỏi trước.")
    else:
        try:
            data = _post_chat(message, query_mode, st.session_state["session_id"])
            st.session_state["chat_history"].insert(
                0,
                {"message": message, "mode": query_mode, "session_id": st.session_state["session_id"], "response": data},
            )
        except Exception as exc:
            st.error(f"Request failed: {exc}")

if st.session_state["chat_history"]:
    current = st.session_state["chat_history"][0]
    st.markdown("## Current Result")
    st.caption(f"Mode: `{current['mode']}` | Session ID: `{current['session_id']}`")
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
            st.caption(f"Session ID: `{item['session_id']}`")
            if item["mode"] == "compare":
                _render_compare_result(item["response"])
            else:
                _render_single_result(item["mode"], item["response"])
