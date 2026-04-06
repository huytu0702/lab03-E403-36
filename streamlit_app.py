import streamlit as st
import requests

from src.core.config import get_settings


settings = get_settings()
API_URL = f"http://{settings.api_host}:{settings.api_port}/api/v1/chat"

st.set_page_config(page_title=settings.app_name, layout="wide")
st.title("Smart E-commerce Assistant")
st.caption("MVP compare mode: chatbot v1 vs ReAct agent v2")

version = st.selectbox("Version", ["v1", "v2"], index=0 if settings.version == "v1" else 1)
message = st.text_area("Message", value="Tôi muốn mua 2 iPhone 15 dùng mã WINNER10 ship Hà Nội")

if st.button("Send", type="primary"):
    response = requests.post(API_URL, json={"message": message, "version": version, "session_id": "streamlit-demo"}, timeout=30)
    data = response.json()
    st.subheader("Answer")
    st.write(data.get("answer", "No answer"))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Status", data.get("status", "unknown"))
    col2.metric("Latency", f"{data.get('latency_ms', 0)} ms")
    col3.metric("Steps", data.get("steps", 0))
    col4.metric("Trace ID", data.get("trace_id", "-"))

    st.subheader("Tool Calls")
    st.json(data.get("tool_calls", []))
