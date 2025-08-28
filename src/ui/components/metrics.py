import streamlit as st

def render_metrics(numeric_summary: dict):
    """숫자 요약 메트릭 렌더링"""
    st.subheader("📊 Numeric Summary")
    # 숫자 컬럼별 sum/mean/min/max 요약을 작은 표로
    for col, stats in numeric_summary.items():
        col1, col2, col3, col4 = st.columns(4)
        with col1: 
            st.metric(f"{col} sum", f"{stats.get('sum',0):,.2f}")
        with col2: 
            st.metric(f"{col} mean", f"{stats.get('mean',0):,.2f}")
        with col3: 
            st.metric(f"{col} min", f"{stats.get('min',0):,.2f}")
        with col4: 
            st.metric(f"{col} max", f"{stats.get('max',0):,.2f}")
