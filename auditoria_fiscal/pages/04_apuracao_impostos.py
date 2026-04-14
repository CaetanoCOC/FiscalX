"""Página 4 — Apuração de Impostos"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from core.apuracao import apurar_icms, apurar_pis_cofins, apuracao_comparativa
from utils.formatters import fmt_moeda
from utils.constants import (
    COR_FUNDO, COR_CARD, COR_CARD_ALT, COR_BORDA,
    COR_TEXTO, COR_TEXTO_SEC,
    COR_CIANO, COR_AZUL, COR_VERDE, COR_VERMELHO, COR_AMARELO,
)
from utils.theme import plotly_layout

st.markdown("<h1>🧾 Apuração de Impostos</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{COR_TEXTO_SEC}; margin-top:-8px;'>Débitos, créditos e saldo a recolher por período fiscal</p>", unsafe_allow_html=True)
st.divider()

df_itens = st.session_state.get("df_itens", pd.DataFrame())
if df_itens.empty:
    st.warning("Nenhum dado carregado. Acesse **Upload NFe** primeiro.")
    st.stop()

# ── Seletor de período e imposto ──────────────────────────────────────────────
col_s1, col_s2, _ = st.columns([1, 1, 2])
with col_s1:
    periodos = []
    if "dhEmi" in df_itens.columns:
        try:
            df_itens["_mes"] = pd.to_datetime(df_itens["dhEmi"].str[:7], format="%Y-%m", errors="coerce")
            periodos = sorted(df_itens["_mes"].dt.to_period("M").dropna().unique().astype(str).tolist())
        except Exception: pass
    if not periodos: periodos = [datetime.now().strftime("%Y-%m")]
    periodo = st.selectbox("Período", periodos)
with col_s2:
    imposto_sel = st.selectbox("Imposto", ["Todos", "ICMS", "PIS/COFINS"])

icms = apurar_icms(df_itens, periodo)
pc   = apurar_pis_cofins(df_itens, periodo)

# ── Cards de apuração ─────────────────────────────────────────────────────────
def _card(col, titulo, debitos, creditos, saldo_dev, saldo_cred, cor):
    sinal = "a Recolher" if saldo_dev > 0 else "Credor"
    valor = saldo_dev if saldo_dev > 0 else saldo_cred
    cor_s = COR_VERMELHO if saldo_dev > 0 else COR_CIANO
    with col:
        st.markdown(f"""
        <div class='fiscal-card' style='border-top: 3px solid {cor};'>
            <div style='font-weight:700; color:{cor}; font-size:0.95em;
                        margin-bottom:16px; padding-bottom:10px; border-bottom:1px solid {COR_BORDA};'>
                {titulo}
            </div>
            <div style='display:grid; gap:10px;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span style='color:{COR_TEXTO_SEC}; font-size:0.85em;'>Débitos</span>
                    <span style='color:{COR_VERMELHO}; font-weight:700;'>{fmt_moeda(debitos)}</span>
                </div>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span style='color:{COR_TEXTO_SEC}; font-size:0.85em;'>Créditos</span>
                    <span style='color:{COR_CIANO}; font-weight:700;'>{fmt_moeda(creditos)}</span>
                </div>
                <div style='display:flex; justify-content:space-between; align-items:center;
                            border-top:1px solid {COR_BORDA}; padding-top:10px; margin-top:2px;'>
                    <span style='color:{COR_TEXTO}; font-weight:700;'>Saldo {sinal}</span>
                    <span style='color:{cor_s}; font-weight:700; font-size:1.15em;'>{fmt_moeda(valor)}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

if imposto_sel in ("Todos", "ICMS"):
    cols = st.columns(3)
    _card(cols[0], "ICMS",   icms["debitos"], icms["creditos"], icms["saldo_devedor"], icms["saldo_credor"], COR_AMARELO)
    if imposto_sel == "Todos":
        _card(cols[1], "PIS",   pc["pis"]["debitos"],   pc["pis"]["creditos"],   pc["pis"]["saldo_devedor"],   pc["pis"]["saldo_credor"],   COR_AZUL)
        _card(cols[2], "COFINS",pc["cofins"]["debitos"],pc["cofins"]["creditos"],pc["cofins"]["saldo_devedor"],pc["cofins"]["saldo_credor"],COR_CIANO)
elif imposto_sel == "PIS/COFINS":
    cols = st.columns(3)
    _card(cols[0], "PIS",   pc["pis"]["debitos"],   pc["pis"]["creditos"],   pc["pis"]["saldo_devedor"],   pc["pis"]["saldo_credor"],   COR_AZUL)
    _card(cols[1], "COFINS",pc["cofins"]["debitos"],pc["cofins"]["creditos"],pc["cofins"]["saldo_devedor"],pc["cofins"]["saldo_credor"],COR_CIANO)

# ── Gráfico comparativo ───────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown(f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:4px;'>Comparativo — Todos os Períodos</p>", unsafe_allow_html=True)

    df_comp = apuracao_comparativa(df_itens, periodos)

    fig = go.Figure()
    fig.add_trace(go.Bar(name="ICMS Débitos",  x=df_comp["periodo"], y=df_comp["icms_debitos"],  marker_color=COR_VERMELHO, opacity=0.85))
    fig.add_trace(go.Bar(name="ICMS Créditos", x=df_comp["periodo"], y=df_comp["icms_creditos"], marker_color=COR_CIANO,   opacity=0.85))
    fig.add_trace(go.Scatter(name="Saldo ICMS", x=df_comp["periodo"], y=df_comp["icms_saldo"],
                              mode="lines+markers", line=dict(color=COR_AMARELO, width=2.5),
                              marker=dict(size=7, color=COR_AMARELO, line=dict(color=COR_FUNDO, width=2)), yaxis="y2"))

    layout = plotly_layout(320, dict(t=16,b=12,l=12,r=12))
    layout.update(dict(
        barmode="group", bargap=0.25,
        legend=dict(orientation="h", y=1.08, font=dict(color=COR_TEXTO, size=11), bgcolor="rgba(0,0,0,0)"),
        yaxis2=dict(overlaying="y", side="right", color=COR_AMARELO,
                    tickfont=dict(color=COR_AMARELO), showgrid=False),
    ))
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)

# ── Detalhamento ──────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
tab_icms, tab_pc = st.tabs(["Detalhamento ICMS", "Detalhamento PIS/COFINS"])

def _tabela_icms(df: pd.DataFrame, cor_valor: str) -> str:
    if df.empty:
        return ""
    linhas = ""
    for i, row in df.iterrows():
        bg = COR_CARD_ALT if i % 2 == 0 else COR_CARD
        linhas += f"""
        <tr style='background:{bg};'>
            <td style='padding:8px 10px; color:{COR_TEXTO}; font-weight:600; font-size:0.82em;'>{row.get("nNF","")}</td>
            <td style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.82em; text-align:center;'>{row.get("nItem","")}</td>
            <td style='padding:8px 10px; color:{COR_CIANO}; font-weight:600; font-size:0.82em;'>{row.get("CFOP","")}</td>
            <td style='padding:8px 10px; color:{COR_TEXTO}; font-size:0.82em;'>{row.get("emit_xNome","")}</td>
            <td style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.82em; text-align:right;'>R$ {float(row.get("icms_vBC",0)):,.2f}</td>
            <td style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.82em; text-align:center;'>{float(row.get("icms_pICMS",0)):.1f}%</td>
            <td style='padding:8px 10px; color:{cor_valor}; font-weight:700; font-size:0.82em; text-align:right;'>R$ {float(row.get("icms_vICMS",0)):,.2f}</td>
        </tr>"""
    return f"""
    <div class='fiscal-card' style='padding:0; overflow:auto; max-height:260px;'>
        <table style='width:100%; border-collapse:collapse;'>
            <thead style='position:sticky; top:0; z-index:1;'>
                <tr style='background:{COR_CARD}; border-bottom:2px solid {COR_BORDA};'>
                    <th style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>NF</th>
                    <th style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center;'>Item</th>
                    <th style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>CFOP</th>
                    <th style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Emitente</th>
                    <th style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>Base ICMS</th>
                    <th style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center;'>Alíq.</th>
                    <th style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>ICMS</th>
                </tr>
            </thead>
            <tbody>{linhas}</tbody>
        </table>
    </div>"""

with tab_icms:
    c1, c2 = st.columns(2)
    df_deb  = icms.get("detalhamento_debitos",  pd.DataFrame())
    df_cred = icms.get("detalhamento_creditos", pd.DataFrame())
    with c1:
        st.markdown(f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:8px;'>Débitos ({len(df_deb)} itens)</p>", unsafe_allow_html=True)
        if not df_deb.empty:
            st.markdown(_tabela_icms(df_deb, COR_VERMELHO), unsafe_allow_html=True)
        else:
            st.info("Sem débitos.")
    with c2:
        st.markdown(f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:8px;'>Créditos ({len(df_cred)} itens)</p>", unsafe_allow_html=True)
        if not df_cred.empty:
            st.markdown(_tabela_icms(df_cred, COR_CIANO), unsafe_allow_html=True)
        else:
            st.info("Sem créditos.")

with tab_pc:
    df_det = pc.get("detalhamento", pd.DataFrame())
    if not df_det.empty:
        linhas_pc = ""
        for i, row in df_det.iterrows():
            bg = COR_CARD_ALT if i % 2 == 0 else COR_CARD
            linhas_pc += f"""
            <tr style='background:{bg};'>
                <td style='padding:8px 10px; color:{COR_TEXTO}; font-weight:600; font-size:0.82em;'>{row.get("nNF","")}</td>
                <td style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.82em; text-align:center;'>{row.get("nItem","")}</td>
                <td style='padding:8px 10px; color:{COR_CIANO}; font-weight:600; font-size:0.82em;'>{row.get("CFOP","")}</td>
                <td style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.82em; text-align:center;'>{row.get("pis_CST","")}</td>
                <td style='padding:8px 10px; color:{COR_AZUL}; font-weight:700; font-size:0.82em; text-align:right;'>R$ {float(row.get("pis_vPIS",0)):,.2f}</td>
                <td style='padding:8px 10px; color:{COR_CIANO}; font-weight:700; font-size:0.82em; text-align:right;'>R$ {float(row.get("cofins_vCOFINS",0)):,.2f}</td>
            </tr>"""
        st.markdown(f"""
        <div class='fiscal-card' style='padding:0; overflow:auto; max-height:300px;'>
            <table style='width:100%; border-collapse:collapse;'>
                <thead style='position:sticky; top:0; z-index:1;'>
                    <tr style='background:{COR_CARD}; border-bottom:2px solid {COR_BORDA};'>
                        <th style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>NF</th>
                        <th style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center;'>Item</th>
                        <th style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>CFOP</th>
                        <th style='padding:8px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center;'>CST PIS</th>
                        <th style='padding:8px 10px; color:{COR_AZUL}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>PIS</th>
                        <th style='padding:8px 10px; color:{COR_CIANO}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>COFINS</th>
                    </tr>
                </thead>
                <tbody>{linhas_pc}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Sem operações tributadas de PIS/COFINS no período.")

# ── Simulação DARF ────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📄 Simulação de DARF"):
    total = icms["saldo_devedor"] + pc["pis"]["saldo_devedor"] + pc["cofins"]["saldo_devedor"]
    st.markdown(f"""
    <div class='fiscal-card' style='border:1px solid {COR_BORDA}; font-family:monospace;'>
        <div style='text-align:center; font-weight:700; font-size:1em; color:{COR_TEXTO};
                    margin-bottom:16px; border-bottom:1px solid {COR_BORDA}; padding-bottom:10px;'>
            DOCUMENTO DE ARRECADAÇÃO DE RECEITAS FEDERAIS — DARF (Simulação)
        </div>
        <div style='display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:0.88em;'>
            <div><span style='color:{COR_TEXTO_SEC};'>Período:</span>
                 <span style='color:{COR_TEXTO}; margin-left:6px;'>{periodo}</span></div>
            <div><span style='color:{COR_TEXTO_SEC};'>Vencimento:</span>
                 <span style='color:{COR_TEXTO}; margin-left:6px;'>Consultar legislação</span></div>
            <div><span style='color:{COR_TEXTO_SEC};'>ICMS a Recolher:</span>
                 <span style='color:{COR_VERMELHO}; font-weight:700; margin-left:6px;'>{fmt_moeda(icms["saldo_devedor"])}</span></div>
            <div><span style='color:{COR_TEXTO_SEC};'>PIS a Recolher:</span>
                 <span style='color:{COR_VERMELHO}; font-weight:700; margin-left:6px;'>{fmt_moeda(pc["pis"]["saldo_devedor"])}</span></div>
            <div><span style='color:{COR_TEXTO_SEC};'>COFINS a Recolher:</span>
                 <span style='color:{COR_VERMELHO}; font-weight:700; margin-left:6px;'>{fmt_moeda(pc["cofins"]["saldo_devedor"])}</span></div>
            <div><span style='color:{COR_TEXTO}; font-weight:700;'>Total a Recolher:</span>
                 <span style='color:{COR_AMARELO}; font-weight:700; font-size:1.1em; margin-left:6px;'>{fmt_moeda(total)}</span></div>
        </div>
        <div style='margin-top:12px; color:{COR_TEXTO_SEC}; font-size:0.72em;'>
            ⚠️ Documento simulado para demonstração. Valores reais devem ser apurados no SPED Fiscal.
        </div>
    </div>
    """, unsafe_allow_html=True)
