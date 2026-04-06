import requests
import streamlit as st

from src.core.config import get_settings


settings = get_settings()
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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Status", data.get("status", "unknown"))
    col2.metric("Latency", f"{data.get('latency_ms', 0)} ms")
    col3.metric("Steps", data.get("steps", 0))
    col4.metric("Trace ID", data.get("trace_id", "-"))

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
