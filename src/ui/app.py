import os
import json
import time
import streamlit as st
from pathlib import Path

# Router 엔트리포인트
from src.agent.router.graph import ask as router_ask

from src.ui.utils.session import init_session, append_history
from src.ui.components.chat_message import render_user, render_assistant
from src.ui.components.citations import render_citations
from src.ui.components.metrics import render_metrics

st.set_page_config(page_title="FinOps RAG Agent", page_icon="💬", layout="wide")

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Settings")
    # 숨겨진 설정들 (기본값 사용)
    month = "latest"
    show_sql = True
    debug = False
    
    # 표시 토글들
    show_table = st.checkbox("Show table (결과 표 표시)", value=True)
    show_metrics = st.checkbox("Show metrics (숫자 요약 표시)", value=True)
    show_citations = st.checkbox("Show citations (참고문헌 표시)", value=True)
    
    st.caption("LangSmith tracing is enabled via environment if configured.")

init_session()

st.title("🤖 FinOps AI 어시스턴트")
st.markdown("""
**AWS SageMaker 비용 최적화를 위한 AI 어시스턴트입니다.**

💡 **무엇을 도와드릴까요?**
- 📊 **비용 분석**: "이번 달 SageMaker 비용이 얼마나 나왔어요?"
- 🔍 **사용량 조회**: "Endpoint 사용량이 가장 많은 서비스는?"
- 📚 **설정 가이드**: "SageMaker 설정 방법을 알려주세요"
- 💰 **최적화 팁**: "비용을 줄이는 방법이 있을까요?"

자연어로 질문하시면 AI가 자동으로 분석하여 답변해드립니다.
""")

# 기존 히스토리 렌더 (먼저 표시)
if "history" in st.session_state and st.session_state["history"]:
    for msg in st.session_state["history"]:
        if msg["role"] == "user":
            render_user(msg["content"])
        else:
            # 저장된 assistant 레코드에는 전체 result dict가 들어있을 수 있음
            res = msg["content"]
            if isinstance(res, dict):
                render_assistant(res.get("answer") or res.get("message","(no content)"),
                                 intent=res.get("intent","general"),
                                 extra={"elapsed_ms": res.get("elapsed_ms"),
                                        "trace_id": res.get("trace_id")})
            else:
                render_assistant(str(res))

# --- Chat input ---
question = st.chat_input("메시지를 입력하세요…")
if question:
    # 새로운 사용자 메시지 렌더
    render_user(question)
    start = time.time()

    # Router 호출 (month 파라미터를 NL2SQL에서 사용하려면 질문에 주입 or 내부 처리)
    result = router_ask(question)  # 내부 에이전트들이 month를 쓸 수 있게 이미 구성돼 있다고 가정
    elapsed = int((time.time() - start) * 1000)

    # 세션 히스토리 저장
    append_history({"role": "user", "content": question})
    append_history({"role": "assistant", "content": result})

    # --- 응답 렌더링 ---
    intent = result.get("intent", "general")
    answer = result.get("answer") or result.get("message") or "(no content)"
    extra = {
        "elapsed_ms": result.get("elapsed_ms", elapsed),
        "trace_id": result.get("trace_id")
    }
    render_assistant(answer, intent=intent, extra=extra)

    # Intent별 부가정보
    if intent == "sql":
        if show_sql and result.get("sql"):
            st.code(result["sql"], language="sql")
        if show_metrics and result.get("numeric_summary"):
            render_metrics(result["numeric_summary"])
        if show_table and result.get("sample_rows"):
            import pandas as pd
            df = pd.DataFrame(result["sample_rows"])
            st.dataframe(df, width='stretch')
    elif intent == "docs":
        if show_citations and result.get("citations"):
            render_citations(result["citations"])

    if debug:
        with st.expander("Debug JSON"):
            st.json(result)
