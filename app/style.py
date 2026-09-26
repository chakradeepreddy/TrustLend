from contextlib import contextmanager

import streamlit as st

PAPER = "#ECE8DF"
SHEET = "#F8F6F1"
INK = "#16181B"
RULE = "#CFC9BC"
RULE2 = "#DDD8CC"
ORANGE = "#E8691C"
ORANGE_TXT = "#B34A0B"
GREEN = "#17784A"
RED = "#B3261E"
MUTED = "#6B6E73"
MUTED2 = "#4A4D52"

VERDICT_COLORS = {"APPROVE": GREEN, "DENY": RED, "REVIEW": ORANGE}
VERDICT_WORD = {"APPROVE": "APPROVED", "DENY": "DENIED", "REVIEW": "REFERRED"}


def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

        html, body, [class*="css"] {{ font-family: 'Chakra Petch', system-ui, sans-serif; }}
        code, pre {{ font-family: 'JetBrains Mono', monospace; }}

        [data-testid="stAppViewContainer"] {{
            background-color: {PAPER};
            background-image: linear-gradient(rgba(22,24,27,0.05) 1px, transparent 1px),
                               linear-gradient(90deg, rgba(22,24,27,0.05) 1px, transparent 1px);
            background-size: 24px 24px;
        }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stAppDeployButton"], [data-testid="stMainMenu"],
        [data-testid="stStatusWidget"], [data-testid="stDecoration"] {{ display: none !important; }}
        [data-testid="stMainBlockContainer"] {{ padding-top: 2.5rem; }}

        div[class*="st-key-card_"] {{
            border: 1.5px solid {INK} !important;
            border-radius: 0 !important;
            background: {SHEET} !important;
            margin-bottom: 20px;
        }}
        .tl-card-head {{
            display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 4px 12px;
            padding: 12px 18px; margin: -1rem -1rem 1rem; border-bottom: 1.5px solid {INK};
        }}
        .tl-card-head h2 {{ margin: 0; flex: 1 1 auto; min-width: 0; font-size: 15px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }}
        .tl-card-head span {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {MUTED}; white-space: nowrap; }}

        section[data-testid="stSidebar"] {{
            background: {INK};
            color: {SHEET};
        }}
        section[data-testid="stSidebar"] * {{ color: {SHEET} !important; }}
        
        [data-testid="stLogo"] {{
            height: 40px !important;
        }}
        [data-testid="stLogo"] img {{
            max-height: 100% !important;
            height: 40px !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"],
        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
            border-radius: 0 !important;
            border-bottom: 1px solid #34373B;
            font-weight: 500;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}
        section[data-testid="stSidebar"] [aria-current="page"] {{
            background: {PAPER} !important;
        }}
        section[data-testid="stSidebar"] [aria-current="page"] * {{ color: {INK} !important; }}
        section[data-testid="stSidebar"] hr {{ border-color: #34373B; }}

        h1, h2, h3 {{ font-family: 'Chakra Petch', system-ui, sans-serif; letter-spacing: -0.01em; }}

        div.stButton > button, div.stDownloadButton > button, div.stFormSubmitButton > button {{
            border-radius: 0;
            border: 1.5px solid {INK};
            background: {SHEET};
            color: {INK};
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        div.stFormSubmitButton > button {{
            width: 100%;
            height: 56px;
            background: {INK};
            color: {SHEET};
            border: none;
            font-size: 16px;
            letter-spacing: 0.14em;
        }}

        [class*="st-key-preset_active"] button {{
            background: {INK} !important;
            color: {SHEET} !important;
            border-color: {INK} !important;
        }}
        [class*="st-key-approve_"] button {{
            background: {GREEN} !important;
            color: {SHEET} !important;
            border-color: {GREEN} !important;
        }}
        [class*="st-key-deny_"] button {{
            background: transparent !important;
            color: {RED} !important;
            border: 2px solid {RED} !important;
        }}

        div[data-testid="stTextInput"] input, div[data-testid="stNumberInput"] input {{
            border: none;
            border-radius: 0;
            border-bottom: 1.5px solid {INK};
            background: transparent;
            font-family: 'JetBrains Mono', monospace;
            font-size: 17px;
            color: {INK};
        }}
        div[data-testid="stTextArea"] textarea {{
            border: none;
            border-radius: 0;
            border-bottom: 1.5px solid {INK};
            font-family: 'Chakra Petch', system-ui, sans-serif;
            font-size: 15px;
            line-height: 26px;
            background-color: #FFFFFF;
            background-image: repeating-linear-gradient(180deg, transparent 0 25px, {RULE2} 25px 26px);
        }}
        div[data-testid="stExpander"] {{
            border: 1.5px solid {INK};
            border-radius: 0;
            background: {SHEET};
        }}
        div[data-testid="stMetric"] {{
            background: {SHEET};
            border: 1px solid {RULE};
            border-radius: 0;
            padding: 10px 14px;
        }}
        [data-testid="stDataFrame"] {{ border: 1.5px solid {INK}; border-radius: 0; }}

        .tl-sheet {{ border: 1.5px solid {INK}; background: {SHEET}; margin-bottom: 20px; }}
        .tl-sheet-head {{
            padding: 12px 18px; border-bottom: 1.5px solid {INK};
            display: flex; justify-content: space-between; align-items: center;
        }}
        .tl-sheet-head h2 {{ margin: 0; font-size: 15px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; }}
        .tl-sheet-meta {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {MUTED}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def sheet_header(kicker, title, subtitle, meta):
    """meta: list of (label, value) shown as boxes to the right of the title."""
    cols_html = "".join(
        f'<div style="padding:18px 16px; border-left:1px solid {INK}; display:flex; flex-direction:column; '
        f'justify-content:space-between; min-width:120px">'
        f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:10px; letter-spacing:0.14em; color:{MUTED}">{label}</span>'
        f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:20px; font-weight:700">{value}</span></div>'
        for label, value in meta
    )
    st.markdown(
        f'<div style="display:flex; border:1.5px solid {INK}; background:{SHEET}; margin-bottom:20px">'
        f'<div style="flex-grow:1; padding:18px 22px; border-right:1px solid {INK}; display:flex; flex-direction:column; gap:8px">'
        f'<div style="font-family:\'JetBrains Mono\',monospace; font-size:11px; letter-spacing:0.12em; color:{MUTED}">{kicker}</div>'
        f'<h1 style="margin:0; font-size:44px; line-height:0.95; font-weight:700; letter-spacing:-0.01em; text-transform:uppercase">{title}</h1>'
        f'<p style="margin:0; font-size:15px; color:{MUTED2}">{subtitle}</p></div>'
        f'{cols_html}</div>',
        unsafe_allow_html=True,
    )


@contextmanager
def card(key, title, meta=""):
    """A bordered card that real widgets can live inside (unlike sheet_start/sheet_end,
    which draw an empty HTML box that widgets render outside of). Use as:
        with card("demo", "A · Demo applicants"):
            st.button(...)
    """
    with st.container(border=True, key=f"card_{key}"):
        st.markdown(
            f'<div class="tl-card-head"><h2>{title}</h2><span>{meta}</span></div>',
            unsafe_allow_html=True,
        )
        yield


def sheet_start(title, meta=""):
    st.markdown(
        f'<div class="tl-sheet"><div class="tl-sheet-head"><h2>{title}</h2>'
        f'<span class="tl-sheet-meta">{meta}</span></div><div style="padding:18px 20px">',
        unsafe_allow_html=True,
    )


def sheet_end():
    st.markdown("</div></div>", unsafe_allow_html=True)


def stamp(decision, sub, size=52):
    color = VERDICT_COLORS[decision]
    word = VERDICT_WORD[decision]
    st.markdown(
        f'<div style="transform:rotate(-5deg); padding:10px 20px 8px; display:inline-flex; flex-direction:column; '
        f'align-items:center; gap:4px; border:5px double {color}; color:{color}">'
        f'<span style="font-size:{size}px; line-height:1; font-weight:700; letter-spacing:0.06em">{word}</span>'
        f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:11px; font-weight:700; letter-spacing:0.16em">{sub}</span></div>',
        unsafe_allow_html=True,
    )


def tag(text, kind):
    """kind: 'pass', 'fired', 'approve', 'deny'"""
    styles = {
        "pass": f"border:1.5px solid {GREEN}; color:{GREEN}; background:transparent",
        "fired": f"border:1.5px solid {ORANGE}; color:{INK}; background:{ORANGE}",
        "approve": f"border:1.5px solid {GREEN}; color:{GREEN}; background:transparent",
        "deny": f"border:1.5px solid {RED}; color:{RED}; background:transparent",
    }
    return (
        f'<span style="padding:3px 8px; font-family:\'JetBrains Mono\',monospace; font-size:11px; '
        f'font-weight:700; letter-spacing:0.12em; {styles[kind]}">{text}</span>'
    )


def field_box(label, value, flag=None):
    border = ORANGE if flag else INK
    bg = "rgba(232,105,28,0.16)" if flag else "transparent"
    hint = f'<div style="font-size:11px; font-weight:600; color:{ORANGE_TXT}">{flag}</div>' if flag else ""
    st.markdown(
        f'<div style="display:flex; flex-direction:column; gap:4px; margin-bottom:10px">'
        f'<span style="font-size:12px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; color:{MUTED2}">{label}</span>'
        f'<span style="height:36px; box-sizing:border-box; padding:0 4px; display:flex; align-items:center; '
        f'border-bottom:1.5px solid {border}; background:{bg}; font-family:\'JetBrains Mono\',monospace; font-size:16px">{value}</span>'
        f"{hint}</div>",
        unsafe_allow_html=True,
    )


def check_ruler(marker_value, scale_max, zone_start, zone_end, cutoff, cutoff_label, marker_fmt, fired, unit=""):
    """A horizontal number-line: tick marks, a hatched 'fired' zone, and a triangle marker at marker_value."""
    color = ORANGE if fired else GREEN
    text_color = ORANGE_TXT if fired else GREEN
    over = marker_value > scale_max
    m_val = min(marker_value, scale_max * 0.985)
    m_frac = max(min(m_val / scale_max, 0.985), 0.015)
    z0 = max(min(zone_start / scale_max, 1), 0) * 100
    z1 = max(min(zone_end / scale_max, 1), 0) * 100
    c_frac = max(min(cutoff / scale_max, 1), 0) * 100
    label = (marker_fmt.format(marker_value)) + (" →" if over else "")

    def pos(frac_pct):
        if frac_pct <= 2:
            return "left:0"
        if frac_pct >= 98:
            return "right:0"
        return f"left:{frac_pct:.2f}%; transform:translateX(-50%)"

    st.markdown(
        f'<div style="position:relative; height:64px; margin:6px 0 4px">'
        f'<div style="position:absolute; top:0; {pos(m_frac*100)}; font-family:\'JetBrains Mono\',monospace; '
        f'font-size:12px; font-weight:700; color:{text_color}">{label}</div>'
        f'<div style="position:absolute; top:18px; left:{m_frac*100:.2f}%; margin-left:-7px; width:0; height:0; '
        f'border-left:7px solid transparent; border-right:7px solid transparent; border-top:10px solid {color}"></div>'
        f'<div style="position:absolute; left:{z0:.2f}%; width:{max(z1-z0,0):.2f}%; top:30px; height:10px; box-sizing:border-box; '
        f'border:1px solid {ORANGE}; border-bottom:none; background:repeating-linear-gradient(135deg, rgba(232,105,28,0.6) 0 2px, transparent 2px 5px)"></div>'
        f'<div style="position:absolute; left:0; right:0; top:40px; height:2px; background:{INK}"></div>'
        f'<div style="position:absolute; left:{c_frac:.2f}%; top:26px; width:2px; height:26px; margin-left:-1px; background:{INK}"></div>'
        f'<div style="position:absolute; top:52px; left:0; font-family:\'JetBrains Mono\',monospace; font-size:10px; color:{MUTED}">0</div>'
        f'<div style="position:absolute; top:52px; {pos(c_frac)}; font-family:\'JetBrains Mono\',monospace; font-size:10px; font-weight:700">{cutoff_label}</div>'
        f'<div style="position:absolute; top:52px; right:0; font-family:\'JetBrains Mono\',monospace; font-size:10px; color:{MUTED}">{scale_max:g}{unit}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def zone_ruler(scale_max, zone_start, zone_end, cutoff, cutoff_label, zone_word="ZONE", unit=""):
    """The check-ruler mechanism (zone + cut-off) without a specific-applicant marker."""
    z0 = max(min(zone_start / scale_max, 1), 0) * 100
    z1 = max(min(zone_end / scale_max, 1), 0) * 100
    c_frac = max(min(cutoff / scale_max, 1), 0) * 100

    def pos(frac_pct):
        if frac_pct <= 2:
            return "left:0"
        if frac_pct >= 98:
            return "right:0"
        return f"left:{frac_pct:.2f}%; transform:translateX(-50%)"

    st.markdown(
        f'<div style="position:relative; height:78px; margin:6px 0 4px">'
        f'<div style="position:absolute; left:{z0:.2f}%; width:{max(z1-z0,0):.2f}%; top:12px; height:12px; box-sizing:border-box; '
        f'border:1px solid {ORANGE}; border-bottom:none; background:repeating-linear-gradient(135deg, rgba(232,105,28,0.6) 0 2px, transparent 2px 5px)"></div>'
        f'<div style="position:absolute; left:0; right:0; top:24px; height:2px; background:{INK}"></div>'
        f'<div style="position:absolute; left:{c_frac:.2f}%; top:10px; width:2px; height:30px; margin-left:-1px; background:{INK}"></div>'
        f'<div style="position:absolute; top:38px; left:0; font-family:\'JetBrains Mono\',monospace; font-size:11px; color:{MUTED}">0</div>'
        f'<div style="position:absolute; top:38px; {pos(c_frac)}; font-family:\'JetBrains Mono\',monospace; font-size:11px; font-weight:700">{cutoff_label}</div>'
        f'<div style="position:absolute; top:38px; right:0; font-family:\'JetBrains Mono\',monospace; font-size:11px; color:{MUTED}">{scale_max:g}{unit}</div>'
        f'<div style="position:absolute; top:56px; left:{z0:.2f}%; width:{max(z1-z0,0):.2f}%; display:flex; align-items:center; gap:6px; '
        f'font-family:\'JetBrains Mono\',monospace; font-size:10px; color:{ORANGE_TXT}">'
        f'<span style="flex-grow:1; height:1px; background:{ORANGE}"></span>{zone_word}<span style="flex-grow:1; height:1px; background:{ORANGE}"></span></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def stat_strip(cells):
    """cells: list of (label, value, highlight:bool)"""
    n = len(cells)
    parts = []
    for i, (label, value, hi) in enumerate(cells):
        border = "" if i == n - 1 else f"border-right:1px solid {RULE};"
        bg = f"background:{ORANGE};" if hi else ""
        weight = "700" if hi else "600"
        color = MUTED2 if not hi else INK
        parts.append(
            f'<div style="padding:14px 20px; {border} {bg} display:flex; justify-content:space-between; align-items:baseline">'
            f'<span style="font-size:14px; font-weight:{weight}; letter-spacing:0.08em; text-transform:uppercase; color:{color}">{label}</span>'
            f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:26px; font-weight:700">{value}</span></div>'
        )
    st.markdown(
        f'<div style="display:grid; grid-template-columns:repeat({n}, minmax(0,1fr)); border:1.5px solid {INK}; '
        f'background:{SHEET}; margin-bottom:20px">'
        + "".join(parts) + "</div>",
        unsafe_allow_html=True,
    )
