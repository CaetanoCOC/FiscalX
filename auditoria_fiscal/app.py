"""
FiscalX — Roteador principal.
set_page_config, CSS e sidebar ficam aqui e são compartilhados automaticamente
com todas as páginas via st.navigation().
"""

import sys
import base64
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

from utils.constants import APP_TITLE, APP_ICON, COR_TEXTO, COR_TEXTO_SEC
from utils.theme import css_global

def _logo_b64() -> str:
    logo = Path(__file__).parent / "static" / "fiscalx_logo_new.png"
    return base64.b64encode(logo.read_bytes()).decode()

# ── Configuração global (uma única vez) ───────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=str(Path(__file__).parent / "static" / "fiscalx_logo_new.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS injetado antes de qualquer renderização de página
st.markdown(css_global(), unsafe_allow_html=True)

# ── Definição das páginas ─────────────────────────────────────────────────────
pg_home      = st.Page("home.py",                          title="Dashboard",            icon="📊", default=True)
pg_upload    = st.Page("pages/01_upload_nfe.py",           title="Upload NFe",           icon="📂")
pg_dashboard = st.Page("pages/02_dashboard_fiscal.py",     title="Dashboard Fiscal",     icon="📈")
pg_auditoria = st.Page("pages/03_auditoria_detalhada.py",  title="Auditoria Detalhada",  icon="🔎")
pg_apuracao  = st.Page("pages/04_apuracao_impostos.py",    title="Apuração de Impostos", icon="🧾")
pg_relatorio = st.Page("pages/05_relatorio_exportar.py",   title="Relatório & Exportar", icon="📄")
pg_de_para   = st.Page("pages/06_de_para.py",              title="Conciliação DE PARA",  icon="🔗")

pg = st.navigation(
    [pg_home, pg_upload, pg_dashboard, pg_auditoria, pg_apuracao, pg_relatorio, pg_de_para],
    position="hidden",   # desabilita o nav automático do Streamlit completamente
)

# ── Sidebar compartilhada (aparece em TODAS as páginas automaticamente) ───────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:20px 0 24px 0;">
        <img src="data:image/png;base64,{_logo_b64()}"
             style="width:120px; height:120px; object-fit:contain; border-radius:16px; margin-bottom:4px;" />
    </div>
    <div style="color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase;
                letter-spacing:0.1em; padding:0 8px 6px 8px;">Menu</div>
    """, unsafe_allow_html=True)

    st.page_link(pg_home,      label="Dashboard",            icon="📊")
    st.page_link(pg_upload,    label="Upload NFe",           icon="📂")
    st.page_link(pg_dashboard, label="Dashboard Fiscal",     icon="📈")
    st.page_link(pg_auditoria, label="Auditoria Detalhada",  icon="🔎")
    st.page_link(pg_apuracao,  label="Apuração de Impostos", icon="🧾")
    st.page_link(pg_relatorio, label="Relatório & Exportar", icon="📄")
    st.page_link(pg_de_para,  label="Conciliação DE PARA",  icon="🔗")

    st.divider()
    st.markdown(
        f"<div style='color:{COR_TEXTO_SEC}; font-size:0.68em; text-align:center;'>"
        f"v1.0.0 · Python · Streamlit</div>",
        unsafe_allow_html=True,
    )

# ── Executa a página selecionada ──────────────────────────────────────────────
pg.run()
