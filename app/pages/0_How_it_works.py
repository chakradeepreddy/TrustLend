import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "app")]
from sidebar import queue_badge

st.set_page_config(page_title="How it works", layout="wide")
st.logo(str(ROOT / "app" / "logo.svg"))
queue_badge()
st.title("How TrustLend works")

st.write(
    "Every applicant goes through one AI model and two independent safety checks. "
    "If either check fires, a human reviews the case instead of the AI deciding alone."
)

BOX = """
<div style="flex:1; min-width:180px; border:1px solid #3A4A52; border-radius:10px;
            padding:16px; background:{bg}; text-align:center;">
  <div style="font-size:28px;">{icon}</div>
  <div style="font-weight:600; margin-top:4px;">{title}</div>
  <div style="font-size:13px; color:#C8D0D3; margin-top:6px;">{desc}</div>
</div>
"""
ARROW = """
<div style="display:flex; align-items:center; justify-content:center;
            font-size:24px; color:#FFBF00; padding:0 6px;">→</div>
"""

st.markdown(
    '<div style="display:flex; align-items:stretch; gap:0; flex-wrap:wrap;">'
    + BOX.format(bg="#1E2A30", icon="🧑", title="Applicant",
                 desc="10 numbers: income, age, credit use, late payments...")
    + ARROW
    + BOX.format(bg="#1E2A30", icon="🤖", title="The model",
                 desc="Turns them into one risk %. Above 17% risk, the plain "
                      "answer is Deny; below, Approve.")
    + ARROW
    + BOX.format(bg="#2A2416", icon="⚖️", title="Check 1: too close to call?",
                 desc="Is the risk % right next to the 17% line? If so, the "
                      "model itself isn't confident.")
    + ARROW
    + BOX.format(bg="#2A2416", icon="🧭", title="Check 2: ever seen anyone like this?",
                 desc="How far is this applicant from the people the model "
                      "trained on? Catches confident answers on unfamiliar people.")
    + ARROW
    + BOX.format(bg="#1E2A30", icon="✅ / 🧑‍⚖️", title="Decision",
                 desc="Both checks pass → the AI decides automatically. "
                      "Either fires → a human reviews it, with the reasons.")
    + "</div>",
    unsafe_allow_html=True,
)

st.divider()

left, right = st.columns(2)
with left:
    st.subheader("Why two checks, not one")
    st.write(
        "- **Check 1** looks at the *risk number* — is it borderline?\n"
        "- **Check 2** looks at the *applicant* — is this someone the model has "
        "basically never seen, even if it sounds very sure?\n\n"
        "A model can be very confident and still be wrong about someone unlike "
        "anyone in its training data. Check 2 catches those cases; Check 1 alone "
        "catches none of them."
    )
with right:
    st.subheader("Try it")
    st.write(
        "Go to **Home**, click **Typo** (a normal person with age typed as "
        "420), and press **Decide**. The plain model gets *more* confident, "
        "not less — 0.6% risk. Only Check 2 catches it."
    )
