import streamlit as st

def render_user(text: str):
    """사용자 메시지 렌더링"""
    with st.chat_message("user"):
        st.markdown(text)

def render_assistant(text: str, intent: str = "general", extra: dict = None):
    """어시스턴트 메시지 렌더링"""
    icon = {"sql": "🧮", "docs": "📚", "general": "💬"}.get(intent, "💬")
    with st.chat_message("assistant"):
        st.markdown(f"{icon} **{intent.upper()}**\n\n{text}")
        if extra:
            meta = []
            if extra.get("elapsed_ms") is not None:
                meta.append(f"⏱ {extra['elapsed_ms']} ms")
            if extra.get("trace_id"):
                meta.append(f"🧵 trace: `{extra['trace_id']}`")
            if meta:
                st.caption(" · ".join(meta))
