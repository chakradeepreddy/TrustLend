import json
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "app")]
from src.model import CUTOFF
from sidebar import render_sidebar
from style import inject_css, sheet_header, sheet_start, sheet_end, tag, zone_ruler, MUTED, MUTED2, INK, ORANGE

st.set_page_config(page_title="How it works", layout="wide")
inject_css()
st.logo(str(ROOT / "app" / "logo.svg"))
T = json.load(open(ROOT / "artifacts" / "thresholds.json"))
render_sidebar(T)

sheet_header(
    "TECHNICAL NOTE · FORM TL-2", "How TrustLend decides",
    "One AI model and two independent checks. If either check fires, a person reviews the case instead of the AI deciding alone.",
    [("CHECKS", "C1 + C2")],
)

sheet_start("A · The route every applicant takes")
steps = [
    ("01", "Applicant", "10 numbers: income, age, debt ratio, credit card use, late payments."),
    ("02", "The model", f"Turns them into one risk %. Above {CUTOFF:.1%} the plain answer is Deny; below, Approve."),
]
cols = st.columns(5)
for c, (n, title, text) in zip(cols[:2], steps):
    with c:
        st.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:26px; font-weight:700; color:#CFC9BC">{n}</span>',
                    unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:18px; font-weight:700; text-transform:uppercase">{title}</div>', unsafe_allow_html=True)
        st.caption(text)
for c, tagname, title, text in [
    (cols[2], "C1", "Too close to call?", f"Is the risk % within {T['band']:.0%} of the {CUTOFF:.1%} line? Then the model itself isn't sure."),
    (cols[3], "C2", "Seen anyone like this?", f"How far is this applicant from the people the model trained on? Past {T['fam_threshold']:.2f}, it's guessing."),
]:
    with c:
        st.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:26px; font-weight:700; color:{ORANGE}">{tagname}</span>',
                    unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:18px; font-weight:700; text-transform:uppercase">{title}</div>', unsafe_allow_html=True)
        st.caption(text)
with cols[4]:
    st.markdown('<span style="font-family:\'JetBrains Mono\',monospace; font-size:26px; font-weight:700; color:#CFC9BC">03</span>',
                unsafe_allow_html=True)
    st.markdown('<div style="font-size:18px; font-weight:700; text-transform:uppercase">Stamp</div>', unsafe_allow_html=True)
    st.caption("Both pass: the AI decides. Either fires: a person reviews it, with the reasons.")
    st.markdown(
        tag("APPROVED", "pass") + " " + tag("DENIED", "deny") + " " + tag("REFERRED", "fired"),
        unsafe_allow_html=True,
    )
sheet_end()

c1, c2 = st.columns(2)
with c1:
    sheet_start("B · Check C1 reads the risk number", meta="0-40%")
    st.write(f"The hatched zone runs {T['band']:.0%} either side of the {CUTOFF:.1%} line. "
             "A risk % inside it means the model can barely tell Approve from Deny.")
    scale = max(0.40, (CUTOFF + T["band"]) * 1.6)
    zone_ruler(scale, CUTOFF - T["band"], CUTOFF + T["band"], CUTOFF, f"{CUTOFF:.1%}", zone_word="ZONE")
    a, b = st.columns(2)
    with a:
        st.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:10px; font-weight:700; '
                    f'letter-spacing:0.14em; color:#17784A">CATCHES</span>', unsafe_allow_html=True)
        st.caption("Close calls the model is unsure about")
    with b:
        st.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:10px; font-weight:700; '
                    f'letter-spacing:0.14em; color:#B3261E">MISSES</span>', unsafe_allow_html=True)
        st.caption("Confident answers about unfamiliar people")
    sheet_end()
with c2:
    sheet_start("C · Check C2 reads the applicant", meta="DISTANCE")
    st.write(f"A distance score from this applicant to the nearest people in the training data. "
             f"Past the {T['fam_threshold']:.2f} cut-off, the model is guessing, however sure it sounds.")
    scale = T["fam_threshold"] * 2.5
    zone_ruler(scale, T["fam_threshold"], scale, T["fam_threshold"], f"{T['fam_threshold']:.2f}", zone_word="UNFAMILIAR")
    a, b = st.columns(2)
    with a:
        st.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:10px; font-weight:700; '
                    f'letter-spacing:0.14em; color:#17784A">CATCHES</span>', unsafe_allow_html=True)
        st.caption("Strangers and typos, even at low risk")
    with b:
        st.markdown(f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:10px; font-weight:700; '
                    f'letter-spacing:0.14em; color:#B3261E">MISSES</span>', unsafe_allow_html=True)
        st.caption("Familiar people with a close call (C1 has those)")
    sheet_end()

d1, d2 = st.columns([1.2, 1])
with d1:
    sheet_start("D · Why two checks, not one")
    st.markdown('<p style="font-size:22px; line-height:1.3; font-weight:700; margin:0 0 10px">'
                "A model can be very confident and still be wrong about someone unlike anyone it has seen.</p>",
                unsafe_allow_html=True)
    st.write("C1 only trusts the model's own number, so it can't see that. C2 doesn't ask the model at all; "
             "it looks at the applicant. Each covers the other's blind spot.")
    sheet_end()
with d2:
    st.markdown(
        f'<div style="background:{INK}; color:#F8F6F1; padding:20px 22px; display:flex; flex-direction:column; gap:12px">'
        f'<div style="font-family:\'JetBrains Mono\',monospace; font-size:11px; letter-spacing:0.14em; color:{ORANGE}">E · FIELD TEST</div>'
        f'<div style="font-size:22px; font-weight:700; letter-spacing:0.03em; text-transform:uppercase">Try it in 10 seconds</div>'
        f'<ol style="margin:0; padding-left:20px; display:flex; flex-direction:column; gap:6px; font-size:15px; line-height:1.5; color:#D9D6CE">'
        f'<li>On Home, load specimen <strong style="color:#F8F6F1">Typo</strong> (age typed as 420).</li>'
        f'<li>Risk reads very low: the plain model got <em>more</em> sure, not less.</li>'
        f'<li>C1 passes. Only C2 fires, and the file is referred to a human.</li></ol></div>',
        unsafe_allow_html=True,
    )
