import streamlit as st

from src.model import CUTOFF


def render_sidebar(T):
    st.sidebar.markdown(
        '<div style="font-family:\'JetBrains Mono\',monospace; font-size:10px; letter-spacing:0.12em; '
        'color:#9A9C9F; margin:-8px 0 14px">LOAN AI · HUMAN REFERRAL</div>',
        unsafe_allow_html=True,
    )

    n = len(st.session_state.get("queue", []))
    badge = f'<span style="padding:2px 7px; background:#E8691C; color:#16181B; font-family:\'JetBrains Mono\',monospace; font-size:11px; font-weight:700">{n}</span>' if n else ""
    st.sidebar.markdown(
        f'<div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; '
        f'border-top:1px solid #34373B; border-bottom:1px solid #34373B; font-size:13px; font-weight:700; '
        f'letter-spacing:0.06em; text-transform:uppercase">Review queue {badge}</div>',
        unsafe_allow_html=True,
    )

    band = T["band"]
    fam_t = T["fam_threshold"]
    rows = [
        ("Risk line", f"{CUTOFF:.1%}"),
        ("Zone", f"{(CUTOFF - band):.1%}–{(CUTOFF + band):.1%}"),
        ("Cut-off", f"{fam_t:.2f}"),
    ]
    rows_html = "".join(
        f'<div style="display:flex; justify-content:space-between; padding:8px 0; border-top:1px solid #34373B">'
        f'<span style="color:#B9BBBE; font-size:12px">{label}</span>'
        f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:12px">{value}</span></div>'
        for label, value in rows
    )
    st.sidebar.markdown(
        f'<div style="margin-top:18px; font-family:\'JetBrains Mono\',monospace">'
        f'<div style="font-size:10px; letter-spacing:0.14em; color:#9A9C9F; padding-bottom:4px">THRESHOLDS</div>'
        f'{rows_html}</div>',
        unsafe_allow_html=True,
    )
