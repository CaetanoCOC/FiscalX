"""CSS global do tema FiscalX — navy dark (inspirado no StockPeers)."""

from utils.constants import (
    COR_FUNDO, COR_SIDEBAR, COR_CARD, COR_CARD_ALT, COR_BORDA,
    COR_TEXTO, COR_TEXTO_SEC,
    COR_CIANO, COR_AZUL, COR_VERDE, COR_VERMELHO, COR_AMARELO,
    COR_CRITICO, COR_ALERTA, COR_INFORMATIVO,
)


def css_global() -> str:
    return f"""
<style>
/* ── Fundo e fonte global ──────────────────────────────────────────── */
html, body, .stApp {{
    background-color: {COR_SIDEBAR} !important;
    color: {COR_TEXTO} !important;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}

/* ── Sidebar ────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: {COR_SIDEBAR} !important;
    border-right: 1px solid {COR_BORDA};
    box-shadow: 4px 0 24px 0 rgba(0,0,0,0.55), 2px 0 6px 0 rgba(0,205,205,0.04);
}}
[data-testid="stSidebar"] * {{
    color: {COR_TEXTO} !important;
}}

/* Remove o menu automático gerado pelo Streamlit (nav superior) */
[data-testid="stSidebarNav"] {{
    display: none !important;
}}
section[data-testid="stSidebarNav"] {{
    display: none !important;
}}

[data-testid="stSidebarNavLink"] {{
    border-radius: 6px;
    margin: 2px 0;
}}
[data-testid="stSidebarNavLink"]:hover {{
    background-color: {COR_CARD_ALT} !important;
}}
[data-testid="stSidebarNavLink"][aria-current="page"] {{
    background-color: {COR_CARD} !important;
    border-left: 3px solid {COR_CIANO} !important;
}}

/* ── Métricas / KPIs ────────────────────────────────────────────────── */
[data-testid="stMetric"] {{
    background-color: {COR_CARD} !important;
    border: 1px solid {COR_BORDA};
    border-radius: 10px;
    padding: 18px 20px !important;
}}
[data-testid="stMetricLabel"] {{
    color: {COR_TEXTO_SEC} !important;
    font-size: 0.78em !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}
[data-testid="stMetricValue"] {{
    color: {COR_TEXTO} !important;
    font-size: 1.7em !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.82em !important;
}}

/* ── Headers ────────────────────────────────────────────────────────── */
h1 {{ color: {COR_TEXTO} !important; font-weight: 700; letter-spacing: -0.02em; }}
h2 {{ color: {COR_TEXTO} !important; font-weight: 600; }}
h3 {{ color: {COR_TEXTO_SEC} !important; font-size: 0.78em !important;
      text-transform: uppercase; letter-spacing: 0.08em; }}
p  {{ color: {COR_TEXTO_SEC}; }}

/* ── Divisor ────────────────────────────────────────────────────────── */
hr {{ border-color: {COR_BORDA} !important; margin: 12px 0; }}

/* ── Botões primários ───────────────────────────────────────────────── */
.stButton > button {{
    background-color: {COR_CIANO} !important;
    color: #0A0F1A !important;
    border: none !important;
    border-radius: 7px !important;
    font-weight: 800 !important;
    padding: 0.55rem 1.6rem !important;
    letter-spacing: 0.02em;
    transition: opacity 0.15s;
    text-shadow: none !important;
}}
.stButton > button:hover {{ opacity: 0.85 !important; }}

/* ── Botões de download ─────────────────────────────────────────────── */
.stDownloadButton > button {{
    background-color: transparent !important;
    color: {COR_CIANO} !important;
    border: 1.5px solid {COR_CIANO} !important;
    border-radius: 7px !important;
    font-weight: 600 !important;
    transition: background-color 0.15s, color 0.15s;
}}
.stDownloadButton > button:hover {{
    background-color: {COR_CIANO} !important;
    color: #0D1626 !important;
    opacity: 1 !important;
}}

/* ── Tabs ───────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    background-color: {COR_CARD};
    border-radius: 8px;
    border: 1px solid {COR_BORDA};
    gap: 4px;
    padding: 4px;
}}
.stTabs [data-baseweb="tab"] {{
    color: {COR_TEXTO_SEC} !important;
    border-radius: 6px !important;
    padding: 6px 16px !important;
}}
.stTabs [aria-selected="true"] {{
    background-color: {COR_CARD_ALT} !important;
    color: {COR_CIANO} !important;
}}

/* ── Inputs / Selects ───────────────────────────────────────────────── */
.stSelectbox > div > div,
.stMultiSelect > div > div,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{
    background-color: {COR_CARD} !important;
    color: {COR_TEXTO} !important;
    border-color: {COR_BORDA} !important;
    border-radius: 7px !important;
}}
.stSelectbox label, .stMultiSelect label,
.stTextInput label, .stTextArea label,
.stFileUploader label {{
    color: {COR_TEXTO_SEC} !important;
    font-size: 0.82em;
}}

/* ── File uploader ──────────────────────────────────────────────────── */
[data-testid="stFileUploader"] {{
    background-color: {COR_CARD} !important;
    border: 2px dashed {COR_BORDA} !important;
    border-radius: 10px !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {COR_CIANO} !important;
}}

/* ── DataFrames ─────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border: 1px solid {COR_BORDA};
    border-radius: 8px;
    overflow: hidden;
}}
.dvn-scroller {{ background-color: {COR_CARD} !important; }}

/* ── Alertas / info ─────────────────────────────────────────────────── */
.stAlert {{ background-color: {COR_CARD} !important; border-radius: 8px; }}

/* ── Progress bar ───────────────────────────────────────────────────── */
.stProgress > div > div {{ background-color: {COR_CIANO} !important; }}

/* ── Header / toolbar do Streamlit ─────────────────────────────────── */
[data-testid="stHeader"] {{
    background-color: {COR_SIDEBAR} !important;
    border-bottom: 1px solid {COR_BORDA} !important;
}}
[data-testid="stHeader"] * {{
    color: {COR_TEXTO_SEC} !important;
}}
[data-testid="stDecoration"] {{
    display: none !important;
}}

/* ── Scrollbar ──────────────────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {COR_FUNDO}; }}
::-webkit-scrollbar-thumb {{ background: {COR_BORDA}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {COR_TEXTO_SEC}; }}

/* ── Cards customizados ─────────────────────────────────────────────── */
.fiscal-card {{
    background-color: {COR_CARD};
    border-radius: 10px;
    padding: 20px;
    border: 1px solid {COR_BORDA};
    margin-bottom: 12px;
}}
.fiscal-card:hover {{
    border-color: #2A3F60;
}}

/* ── st.container(border=True) → visual fiscal-card ────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {{
    border: 1px solid {COR_BORDA} !important;
    border-radius: 10px !important;
}}
[data-testid="stVerticalBlockBorderWrapper"]:hover {{
    border-color: #2A3F60 !important;
}}

/* ── Badges de severidade ───────────────────────────────────────────── */
.badge-critico  {{ background:{COR_CRITICO};   color:#fff;     padding:2px 9px; border-radius:4px; font-size:0.75em; font-weight:700; }}
.badge-alerta   {{ background:{COR_ALERTA};    color:#060E1A;  padding:2px 9px; border-radius:4px; font-size:0.75em; font-weight:700; }}
.badge-info     {{ background:{COR_INFORMATIVO};color:#fff;    padding:2px 9px; border-radius:4px; font-size:0.75em; font-weight:700; }}

/* ── Chips/tags de CFOP, UF ─────────────────────────────────────────── */
.chip {{
    display:inline-block;
    background-color: {COR_CARD_ALT};
    border: 1px solid {COR_BORDA};
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 0.78em;
    color: {COR_CIANO};
    font-weight: 600;
    margin: 2px;
}}
</style>
"""


def plotly_layout(height: int = 300, margin: dict | None = None) -> dict:
    """Retorna layout padrão Plotly com o tema navy dark."""
    if margin is None:
        margin = dict(t=16, b=16, l=16, r=16)
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COR_TEXTO, family="Inter, Segoe UI, sans-serif"),
        xaxis=dict(
            gridcolor=COR_BORDA, showgrid=True,
            color=COR_TEXTO_SEC, linecolor=COR_BORDA,
            tickfont=dict(color=COR_TEXTO_SEC, size=11),
        ),
        yaxis=dict(
            gridcolor=COR_BORDA, showgrid=True,
            color=COR_TEXTO_SEC, linecolor=COR_BORDA,
            tickfont=dict(color=COR_TEXTO_SEC, size=11),
        ),
        legend=dict(
            font=dict(color=COR_TEXTO, size=11),
            bgcolor="rgba(0,0,0,0)",
            bordercolor=COR_BORDA,
        ),
        margin=margin,
        height=height,
    )
