import json
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "app")]
from sidebar import queue_badge

st.logo(str(ROOT / "app" / "logo.svg"))
queue_badge()
st.title("Does it work?")
path = ROOT / "artifacts" / "results.json"

if not path.exists():
    st.info("Run python -m src.evaluate first to generate results.")
    st.stop()

res = json.load(open(path))
st.subheader("Results on applicants the AI never trained on")
st.dataframe(pd.DataFrame(res["table"]), hide_index=True)

st.subheader("Cost of the automatic decisions, by how many go to a human")
curve = pd.DataFrame(res["curve"]).melt("budget", ["random", "check1_only", "trustlend"], var_name="method", value_name="cost")
curve["budget"] *= 100

fig = px.line(
    curve, x="budget", y="cost", color="method", markers=True,
    labels={"budget": "% sent to a human", "cost": "average cost per automatic decision"}
)
st.plotly_chart(fig, use_container_width=True)
