<<<<<<< HEAD
=======
from __future__ import annotations

from typing import Any, Dict, List

>>>>>>> 0c73add2950a3b23caf39caf4f34c4c2ea735a72
import requests
import streamlit as st

from src.core.config import get_settings
from src.evaluation.benchmark_cases import BENCHMARK_CASES


settings = get_settings()
<<<<<<< HEAD
BASE_API_URL = f"http://{settings.api_host}:{settings.api_port}/api/v1"
CHAT_API_URL = f"{BASE_API_URL}/chat"
HEALTH_API_URL = f"{BASE_API_URL}/health"
METRICS_API_URL = f"{BASE_API_URL}/metrics/summary"

DEFAULT_PROMPTS = {
    "FAQ đổi trả": "Chính sách đổi trả là gì?",
    "FAQ cuối tuần": "Shop có giao hàng cuối tuần không?",
    "Quote nhiều bước": "Tôi muốn mua 2 iPhone 15, dùng mã WINNER10 và ship Hà Nội. Tổng bao nhiêu?",
    "Kiểm tra hàng": "MacBook Air M3 còn hàng không? Nếu mua 1 cái ship TP.HCM thì hết bao nhiêu?",
    "Edge case coupon": "Mua 3 AirPods Pro 2 dùng mã SAVE999 ship Đà Nẵng.",
}


st.set_page_config(page_title=settings.app_name, layout="wide")
st.title("Smart E-commerce Assistant")
st.caption("Compare mode cho chatbot `v1` và ReAct agent `v2`")

if "history" not in st.session_state:
    st.session_state.history = []
if "message" not in st.session_state:
    st.session_state.message = DEFAULT_PROMPTS["Quote nhiều bước"]


def fetch_json(url: str):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        return {"error": str(exc)}


def send_chat(version: str, message: str, session_id: str):
    try:
        response = requests.post(
            CHAT_API_URL,
            json={"message": message, "version": version, "session_id": session_id},
            timeout=30,
        )
        data = response.json()
        if response.status_code >= 400:
            data.setdefault("status", "error")
        return data
    except requests.RequestException as exc:
        return {
            "version": version,
            "answer": "Không gọi được backend. Hãy kiểm tra FastAPI đã chạy chưa.",
            "latency_ms": 0,
            "steps": 0,
            "tool_calls": [],
            "trace_id": "",
            "status": "error",
            "error_code": str(exc),
        }


def render_result(title: str, data: dict):
    st.subheader(title)
    st.write(data.get("answer", "No answer"))
=======
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
>>>>>>> 0c73add2950a3b23caf39caf4f34c4c2ea735a72

if st.session_state["chat_history"]:
    current = st.session_state["chat_history"][0]
    st.markdown("## Current Result")
    st.caption(f"Mode: `{current['mode']}`")
    if current["mode"] == "compare":
        _render_compare_result(current["response"])
    else:
        _render_single_result(current["mode"], current["response"])

<<<<<<< HEAD
    st.caption(f"Error code: {data.get('error_code') or 'None'}")
    st.json(data.get("tool_calls", []))


with st.sidebar:
    st.header("Demo controls")
    selected_prompt = st.selectbox("Prompt mẫu", list(DEFAULT_PROMPTS.keys()))
    if st.button("Nạp prompt", use_container_width=True):
        st.session_state.message = DEFAULT_PROMPTS[selected_prompt]

    st.divider()
    st.subheader("Health check")
    health = fetch_json(HEALTH_API_URL)
    if "error" in health:
        st.error(health["error"])
    else:
        st.success(f"API: {health.get('status', 'unknown')}")
        db_info = health.get("database", {})
        st.write(f"DB mode: `{db_info.get('mode', 'unknown')}`")

    st.divider()
    st.subheader("Metrics summary")
    metrics = fetch_json(METRICS_API_URL)
    if "error" in metrics:
        st.warning("Chưa lấy được metrics summary.")
    else:
        st.metric("Total traces", metrics.get("total_traces", 0))
        for version_name, summary in metrics.get("by_version", {}).items():
            st.write(
                f"**{version_name}** — success `{summary.get('success_rate', 0):.0%}`, "
                f"avg latency `{summary.get('avg_latency_ms', 0)} ms`, avg steps `{summary.get('avg_steps', 0)}`"
            )

mode = st.radio("Chế độ demo", ["Single version", "Compare v1 vs v2"], horizontal=True)
version = st.selectbox("Version", ["v1", "v2"], index=0 if settings.version == "v1" else 1, disabled=mode == "Compare v1 vs v2")
session_id = st.text_input("Session ID", value="streamlit-demo")
message = st.text_area("Message", key="message", height=120)

if st.button("Send", type="primary"):
    if not message.strip():
        st.warning("Bạn hãy nhập câu hỏi trước.")
    elif mode == "Compare v1 vs v2":
        result_v1 = send_chat("v1", message, session_id)
        result_v2 = send_chat("v2", message, session_id)

        col_left, col_right = st.columns(2)
        with col_left:
            render_result("Kết quả `v1`", result_v1)
        with col_right:
            render_result("Kết quả `v2`", result_v2)

        st.session_state.history.insert(0, {"question": message, "mode": "compare", "results": {"v1": result_v1, "v2": result_v2}})
    else:
        result = send_chat(version, message, session_id)
        render_result(f"Kết quả `{version}`", result)
        st.session_state.history.insert(0, {"question": message, "mode": version, "results": {version: result}})

if st.session_state.history:
    st.divider()
    st.subheader("Recent chat history")
    for index, item in enumerate(st.session_state.history[:5], start=1):
        with st.expander(f"#{index} — {item['question'][:80]}"):
            st.write(f"Mode: `{item['mode']}`")
            for version_name, result in item["results"].items():
                st.markdown(f"**{version_name}**")
                st.write(result.get("answer", ""))
                st.caption(
                    f"status={result.get('status')} | latency={result.get('latency_ms', 0)} ms | "
                    f"steps={result.get('steps', 0)} | trace_id={result.get('trace_id', '-') }"
                )
=======
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
>>>>>>> 0c73add2950a3b23caf39caf4f34c4c2ea735a72
