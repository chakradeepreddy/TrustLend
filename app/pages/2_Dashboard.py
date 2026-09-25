import json
import sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "app")]
from sidebar import render_sidebar
from style import inject_css, sheet_header, sheet_start, sheet_end, INK, ORANGE, MUTED, MUTED2

st.set_page_config(page_title="Dashboard", layout="wide")
inject_css()
st.logo(str(ROOT / "app" / "logo.svg"))
T = json.load(open(ROOT / "artifacts" / "thresholds.json"))
render_sidebar(T)

path = ROOT / "artifacts" / "results.json"
sheet_header(
    "EVALUATION REPORT · FORM TL-4", "Does it work?",
    "Tested on applicants the AI never trained on. Cost = average loss per decision the AI makes alone. Lower is better.",
    [("TEST SETS", str(len(json.load(open(path))["table"])) if path.exists() else "0")],
)

if not path.exists():
    st.info("Run `python -m src.evaluate` first to generate results.")
    st.stop()

res = json.load(open(path))
table = res["table"]
changes = [(row["TrustLend cost"] - row["plain model cost"]) / row["plain model cost"] for row in table]
worst_i = max(range(len(changes)), key=lambda i: abs(changes[i]))

tiles = st.columns(len(table))
for i, (col, row, pct) in enumerate(zip(tiles, table, changes)):
    hi = i == worst_i
    with col:
        st.markdown(
            f'<div style="padding:16px 18px; {"background:" + ORANGE + ";" if hi else ""} border:1.5px solid {INK}; '
            f'{"border-left:none;" if i else ""} display:flex; flex-direction:column; gap:4px; min-height:130px">'
            f'<span style="font-size:13px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase">{row["test set"]}</span>'
            f'<span style="font-size:44px; line-height:0.95; font-weight:700; letter-spacing:-0.02em">{pct:+.0%}</span>'
            f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:11px; {"" if hi else "color:" + MUTED2}">'
            f'COST {row["plain model cost"]:.3f} → {row["TrustLend cost"]:.3f} · {row["deferral rate"]} REFERRED</span></div>',
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

barcol, readcol = st.columns([1.8, 1])
with barcol:
    sheet_start("A · Cost per automatic decision")
    st.markdown(
        f'<div style="display:flex; gap:16px; font-family:\'JetBrains Mono\',monospace; font-size:11px; '
        f'font-weight:700; letter-spacing:0.08em; margin-bottom:10px">'
        f'<span style="display:flex; align-items:center; gap:6px"><span style="width:14px; height:10px; '
        f'box-sizing:border-box; border:1px solid {INK}; background:repeating-linear-gradient(135deg, {INK} 0 1px, transparent 1px 4px)"></span>PLAIN AI</span>'
        f'<span style="display:flex; align-items:center; gap:6px"><span style="width:14px; height:10px; background:{ORANGE}"></span>TRUSTLEND</span></div>',
        unsafe_allow_html=True,
    )
    max_cost = max(row["plain model cost"] for row in table) * 1.05
    for row in table:
        plain_w = row["plain model cost"] / max_cost * 100
        tl_w = row["TrustLend cost"] / max_cost * 100
        st.markdown(
            f'<div style="display:flex; gap:16px; align-items:center; margin-bottom:14px; font-family:\'JetBrains Mono\',monospace">'
            f'<div style="width:120px; flex-shrink:0; font-family:\'Chakra Petch\',sans-serif; font-size:15px; font-weight:700; text-transform:uppercase">{row["test set"]}</div>'
            f'<div style="flex-grow:1; display:flex; flex-direction:column; gap:4px; border-left:1.5px solid {INK}">'
            f'<div style="display:flex; align-items:center; gap:10px"><div style="height:16px; width:{plain_w:.1f}%; box-sizing:border-box; '
            f'border:1px solid {INK}; border-left:none; background:repeating-linear-gradient(135deg, {INK} 0 1px, transparent 1px 5px)"></div>'
            f'<span style="font-size:12px">{row["plain model cost"]:.3f}</span></div>'
            f'<div style="display:flex; align-items:center; gap:10px"><div style="height:16px; width:{tl_w:.1f}%; background:{ORANGE}"></div>'
            f'<span style="font-size:12px; font-weight:700">{row["TrustLend cost"]:.3f}</span></div></div></div>',
            unsafe_allow_html=True,
        )
    sheet_end()
with readcol:
    st.markdown(
        f'<div style="background:{INK}; color:#F8F6F1; padding:18px 22px; height:100%; box-sizing:border-box; '
        f'display:flex; flex-direction:column; gap:12px">'
        f'<div style="font-family:\'JetBrains Mono\',monospace; font-size:11px; font-weight:700; letter-spacing:0.14em; color:{ORANGE}">B · HOW TO READ THIS</div>'
        f'<p style="margin:0; font-size:15px; line-height:1.5; color:#D9D6CE"><strong style="color:#F8F6F1">Cost</strong> counts only the decisions the AI still makes alone.</p>'
        f'<p style="margin:0; font-size:15px; line-height:1.5; color:#D9D6CE"><strong style="color:#F8F6F1">Referred</strong> files leave the AI\'s pile and go to the review queue.</p>'
        f'<p style="margin:0; font-size:15px; line-height:1.5; color:#D9D6CE">The set with the biggest deferral share is where bad or unusual data gets caught instead of stamped automatically.</p></div>',
        unsafe_allow_html=True,
    )

sheet_start("C · Results by test set", meta="UNSEEN APPLICANTS ONLY")
st.dataframe(pd.DataFrame(table), hide_index=True)
sheet_end()

sheet_start("D · Cost as more files go to a human", meta="Y: AVG COST PER AUTO DECISION · X: % REFERRED")
curve = pd.DataFrame(res["curve"])
curve["budget"] = curve["budget"] * 100

fig = go.Figure()
fig.add_trace(go.Scatter(x=curve["budget"], y=curve["random"], name="Random · no gain",
                          mode="lines", line=dict(color=MUTED, width=1.5, dash="dot")))
fig.add_trace(go.Scatter(x=curve["budget"], y=curve["check1_only"], name="C1 only",
                          mode="lines", line=dict(color=INK, width=2, dash="dash")))
fig.add_trace(go.Scatter(x=curve["budget"], y=curve["trustlend"], name="TrustLend",
                          mode="lines+markers", line=dict(color=ORANGE, width=3.5),
                          marker=dict(symbol="square", size=9, color=ORANGE, line=dict(color=INK, width=1.5))))
fig.update_layout(
    height=380, margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font={"family": "JetBrains Mono, monospace", "color": INK},
    xaxis=dict(ticksuffix="%", gridcolor=MUTED, zeroline=False),
    yaxis=dict(gridcolor="#DDD8CC", zeroline=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig)
st.caption("Referring files at random doesn't lower cost. TrustLend tracks C1 alone closely on this set, "
           "so adding C2 costs almost nothing; its payoff is on strangers and typos above, where confident "
           "mistakes slip past C1.")
sheet_end()
