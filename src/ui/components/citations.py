import streamlit as st

def render_citations(citations):
    """참고문헌 카드 렌더링"""
    st.subheader("🔎 References")
    for c in citations:
        title = c.get("title") or "Untitled"
        section = c.get("section") or ""
        url = c.get("url") or ""
        ver = c.get("version_date") or ""
        with st.container(border=True):
            st.markdown(f"**{title}** — {section}")
            if url:
                st.markdown(f"[{url}]({url})")
            if ver:
                st.caption(f"version: {ver}")
