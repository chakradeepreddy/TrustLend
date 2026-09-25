import json
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "app")]
from audit import log, LOG
from sidebar import render_sidebar
from style import inject_css, sheet_header, sheet_start, sheet_end, stamp, tag, stat_strip, field_box, MUTED, MUTED2, INK

st.set_page_config(page_title="Review queue", layout="wide")
inject_css()
st.logo(str(ROOT / "app" / "logo.svg"))
T = json.load(open(ROOT / "artifacts" / "thresholds.json"))
render_sidebar(T)

FIELD_LABELS = {
    "age": "Age", "MonthlyIncome": "Monthly income", "DebtRatio": "Debt ratio",
    "RevolvingUtilizationOfUnsecuredLines": "Credit card use",
    "NumberOfOpenCreditLinesAndLoans": "Open loans + cards", "NumberRealEstateLoansOrLines": "Home loans",
    "NumberOfDependents": "Dependents", "NumberOfTime30-59DaysPastDueNotWorse": "30-59 days late",
    "NumberOfTime60-89DaysPastDueNotWorse": "60-89 days late", "NumberOfTimes90DaysLate": "90+ days late",
}

queue = st.session_state.get("queue", [])
sent_c1 = sum(1 for c in queue if c["result"]["unsure"])
sent_c2 = sum(1 for c in queue if c["result"]["unfamiliar"])
logged = 0
if Path(LOG).exists():
    logged = len(pd.read_csv(LOG))

sheet_header(
    "HUMAN REVIEW · FORM TL-3", "Review queue",
    "Files the AI didn't decide alone. Read the reasons, stamp a decision, leave a note. Every stamp is logged.",
    [],
)
stat_strip([
    ("Waiting", f"{len(queue):02d}", True),
    ("Sent by C1", f"{sent_c1:02d}", False),
    ("Sent by C2", f"{sent_c2:02d}", False),
    ("Logged", f"{logged:02d}", False),
])

st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace; font-size:11px; font-weight:700; '
            f'letter-spacing:0.14em; color:{MUTED2}; margin-bottom:10px">OPEN FILES · OLDEST LAST</div>',
            unsafe_allow_html=True)

if not queue:
    st.info("Nothing waiting. Send an applicant from the Home page first.")

for i, case in enumerate(list(queue)):
    r, applicant = case["result"], case["applicant"]
    file_no = case.get("file", "TL-????")
    time = case.get("time", "")
    st.markdown(
        f'<div style="display:inline-flex; align-items:center; gap:10px; padding:7px 14px; background:#F8F6F1; '
        f'border:1.5px solid {INK}; border-bottom:none; position:relative; top:1.5px">'
        f'<span style="width:8px; height:8px; background:#E8691C"></span>'
        f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:13px; font-weight:700">FILE {file_no}</span>'
        f'<span style="font-size:13px; color:{MUTED2}">{case["name"]} specimen · {time}</span></div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        colL, colR = st.columns([1.6, 1])
        with colL:
            a, b = st.columns([1, 3])
            with a:
                stamp(r["decision"], "TO A HUMAN REVIEWER", size=28)
            with b:
                why = r["reasons"][0] if r["reasons"] else "Sent to a human reviewer."
                st.markdown(f'<p style="font-size:17px; line-height:1.4; font-weight:600">{why}</p>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown(
                    f'<div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-top:1.5px solid {INK}">'
                    f'<span style="font-size:13px; font-weight:700">C1 · Too close?</span>'
                    f'{tag("FIRED" if r["unsure"] else "PASS", "fired" if r["unsure"] else "pass")}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"{r['p_default']:.1%} risk")
            with c2:
                st.markdown(
                    f'<div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-top:1.5px solid {INK}">'
                    f'<span style="font-size:13px; font-weight:700">C2 · Seen before?</span>'
                    f'{tag("FIRED" if r["unfamiliar"] else "PASS", "fired" if r["unfamiliar"] else "pass")}</div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"distance {r['familiarity_distance']:.2f}")

            for n, reason in enumerate(r["reasons"], start=1):
                st.markdown(
                    f'<div style="display:flex; gap:12px; padding:8px 0; border-bottom:1px solid #DDD8CC; font-size:15px">'
                    f'<span style="width:24px; height:20px; flex-shrink:0; display:flex; align-items:center; justify-content:center; '
                    f'font-family:\'JetBrains Mono\',monospace; font-size:11px; font-weight:700; border:1.5px solid {INK}">{n:02d}</span>'
                    f'<span>{reason}</span></div>', unsafe_allow_html=True,
                )
            st.dataframe(pd.DataFrame(r["neighbours"]), hide_index=True, height=180)

        with colR:
            st.markdown(f'<div style="font-family:\'JetBrains Mono\',monospace; font-size:10px; font-weight:700; '
                        f'letter-spacing:0.14em; color:{MUTED}; padding-bottom:6px">APPLICANT DATA</div>', unsafe_allow_html=True)
            for col, label in FIELD_LABELS.items():
                field_box(label, f"{applicant[col]:g}")

        note = st.text_area("Officer's note for the log", key=f"note_{i}", height=90,
                             placeholder="e.g. Called the applicant: age is 42. Re-running with the corrected value.")
        a, b = st.columns(2)
        with a:
            with st.container(key=f"approve_{i}"):
                if st.button("Stamp approved", key=f"approve_btn_{i}", width="stretch"):
                    log(case["name"], r, "APPROVE", "human reviewer", note)
                    queue.pop(i)
                    st.rerun()
        with b:
            with st.container(key=f"deny_{i}"):
                if st.button("Stamp denied", key=f"deny_btn_{i}", width="stretch"):
                    log(case["name"], r, "DENY", "human reviewer", note)
                    queue.pop(i)
                    st.rerun()
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

sheet_start("Audit ledger", meta="NEWEST FIRST · AUTOMATIC + HUMAN")
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
sheet_end()
