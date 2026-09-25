import json
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "app")]

from src.decide import decide
from audit import log

st.set_page_config(page_title="TrustLend", layout="wide")
st.logo("app/logo.png")
st.title("TrustLend: a loan AI that knows when to ask a human")

FIELDS = {
    "age": ("Age", 35),
    "MonthlyIncome": ("Monthly income", 5000),
    "DebtRatio": ("Debt ratio (monthly debt / income)", 0.3),
    "RevolvingUtilizationOfUnsecuredLines": ("Credit card use (0.3 = 30% of limit)", 0.3),
    "NumberOfOpenCreditLinesAndLoans": ("Open loans and cards", 8),
    "NumberRealEstateLoansOrLines": ("Home loans", 1),
    "NumberOfDependents": ("Dependents", 0),
    "NumberOfTime30-59DaysPastDueNotWorse": ("Times 30-59 days late", 0),
    "NumberOfTime60-89DaysPastDueNotWorse": ("Times 60-89 days late", 0),
    "NumberOfTimes90DaysLate": ("Times 90+ days late", 0)
}

PRESETS = json.load(open(ROOT / "app" / "presets.json"))

for col, (_, default) in FIELDS.items():
    st.session_state.setdefault(col, float(default))
st.session_state.setdefault("queue", [])

def load_preset(name):
    for col, v in PRESETS[name].items():
        st.session_state[col] = float(v) if v is not None else 0.0
    st.session_state["preset_name"] = name

st.write("**Demo applicants:**")
cols = st.columns(len(PRESETS))
for c, name in zip(cols, PRESETS):
    c.button(name, on_click=load_preset, args=(name,), use_container_width=True)

with st.form("applicant"):
    left, right = st.columns(2)
    for i, (col, (label, _)) in enumerate(FIELDS.items()):
        (left if i % 2 == 0 else right).number_input(label, min_value=0.0, key=col)
    submitted = st.form_submit_button("Decide", type="primary")

if submitted:
    applicant = {col: st.session_state[col] for col in FIELDS}
    r = decide(applicant)
    name = st.session_state.get("preset_name", "manual entry")

    if r["decision"] == "REVIEW":
        st.warning(
            f"### Sent to a human reviewer\n"
            f"The plain AI would have said **{r['model_says']}** at {r['p_default']:.1%} risk."
        )
        st.write("**Why:**")
        for reason in r["reasons"]:
            st.write("- " + reason)
        st.session_state.queue.append({"name": name, "applicant": applicant, "result": r})
    else:
        box = st.success if r["decision"] == "APPROVE" else st.error
        box(
            f"### Automatic decision: {r['decision']}\n"
            f"Risk of not repaying: {r['p_default']:.1%}. Both checks passed."
        )
        log(name, r, r["decision"], "AI")

    a, b, c = st.columns(3)
    a.metric("Risk", f"{r['p_default']:.1%}")
    b.metric("Check 1: too close to the line?", "Yes" if r["unsure"] else "No")
    c.metric(
        "Check 2: unfamiliar?",
        "Yes" if r["unfamiliar"] else "No",
        f"distance = {r['familiarity_distance']:.2f}",
        delta_color="off"
    )

    st.write("**The 5 most similar past applicants:**")
    st.dataframe(pd.DataFrame(r["neighbours"]), hide_index=True)
