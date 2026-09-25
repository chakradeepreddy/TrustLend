import streamlit as st


def queue_badge():
    n = len(st.session_state.get("queue", []))
    if n:
        st.sidebar.warning(f"🔔 Review queue: {n} pending")
    else:
        st.sidebar.caption("Review queue: empty")
