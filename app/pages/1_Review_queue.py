import sys
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "app")]
from audit import log, LOG
from sidebar import queue_badge

st.logo(str(ROOT / "app" / "logo.svg"))
queue_badge()
queue = st.session_state.get("queue", [])
st.title(f"Review queue ({len(queue)})" if queue else "Review queue")

if not queue:
    st.info("Nothing waiting. Send an applicant from the Home page first.")

for i, case in enumerate(list(queue)):
    r = case["result"]
    with st.expander(f"{case['name']}: AI said {r['model_says']} at {r['p_default']:.1%} risk", expanded=True):
        for reason in r["reasons"]:
            st.write("- " + reason)
        st.dataframe(pd.DataFrame(r["neighbours"]), hide_index=True)
        note = st.text_input("Reviewer note", key=f"note_{i}")
        a, b = st.columns(2)
        if a.button("Approve", key=f"approve_{i}", use_container_width=True):
            log(case["name"], r, "APPROVE", "human reviewer", note)
            queue.pop(i)
            st.rerun()
        if b.button("Deny", key=f"deny_{i}", use_container_width=True):
            log(case["name"], r, "DENY", "human reviewer", note)
            queue.pop(i)
            st.rerun()

st.subheader("Audit log")
if Path(LOG).exists():
    st.dataframe(pd.read_csv(LOG).iloc[::-1], hide_index=True)
    st.download_button(
        "Download audit log (CSV)",
        data=Path(LOG).read_bytes(),
        file_name="trustlend_audit_log.csv",
        mime="text/csv",
    )
else:
    st.caption("No decisions logged yet.")
