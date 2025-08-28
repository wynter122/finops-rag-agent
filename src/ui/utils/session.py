import streamlit as st

def init_session():
    """세션 상태 초기화"""
    if "history" not in st.session_state:
        st.session_state["history"] = []

def append_history(item):
    """히스토리에 메시지 추가"""
    st.session_state["history"].append(item)
