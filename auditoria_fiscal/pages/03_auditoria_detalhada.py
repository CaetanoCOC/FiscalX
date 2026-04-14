"""Página 3 — Auditoria Detalhada"""

import streamlit as st
import pandas as pd

from utils.formatters import fmt_moeda
from utils.constants import (
    COR_CARD, COR_CARD_ALT, COR_BORDA,
    COR_TEXTO, COR_TEXTO_SEC,
    COR_CIANO, COR_VERMELHO, COR_AMARELO,
    COR_CRITICO, COR_ALERTA, COR_INFORMATIVO,
    SEVERIDADES, SEVERIDADE_CORES,
)

st.markdown("<h1>🔎 Auditoria Detalhada</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{COR_TEXTO_SEC}; margin-top:-8px;'>Inconsistências tributárias por nota e item</p>", unsafe_allow_html=True)
st.divider()

df_validacoes = st.session_state.get("df_validacoes", pd.DataFrame())
df_anomalias  = st.session_state.get("df_anomalias",  pd.DataFrame())

if df_validacoes.empty:
    st.warning("Nenhuma auditoria executada. Acesse **Upload NFe** para carregar e auditar.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
criticos     = len(df_validacoes[df_validacoes["severidade"] == "CRÍTICO"])
alertas      = len(df_validacoes[df_validacoes["severidade"] == "ALERTA"])
informativos = len(df_validacoes[df_validacoes["severidade"] == "INFORMATIVO"])
impacto      = float(df_validacoes["divergencia"].sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Críticos",         criticos)
c2.metric("Alertas",          alertas)
c3.metric("Informativos",     informativos)
c4.metric("Impacto Estimado", fmt_moeda(impacto))

st.markdown("<br>", unsafe_allow_html=True)

# ── Filtros ───────────────────────────────────────────────────────────────────
with st.container(border=True):
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        sev_filtro = st.multiselect("Severidade", SEVERIDADES, default=SEVERIDADES)
    with col_f2:
        cod_opcoes = sorted(df_validacoes["codigo_validacao"].unique().tolist())
        cod_filtro = st.multiselect("Código", cod_opcoes, default=cod_opcoes)
    with col_f3:
        emit_opcoes = ["Todos"] + sorted(df_validacoes["emit_xNome"].dropna().unique().tolist())
        emit_filtro = st.selectbox("Emitente", emit_opcoes)
    with col_f4:
        busca = st.text_input("Buscar descrição", placeholder="ex: ICMS, CFOP…")

df_filt = df_validacoes.copy()
if sev_filtro:             df_filt = df_filt[df_filt["severidade"].isin(sev_filtro)]
if cod_filtro:             df_filt = df_filt[df_filt["codigo_validacao"].isin(cod_filtro)]
if emit_filtro != "Todos": df_filt = df_filt[df_filt["emit_xNome"] == emit_filtro]
if busca:                  df_filt = df_filt[df_filt["descricao"].str.contains(busca, case=False, na=False)]

st.markdown(f"<p style='color:{COR_TEXTO_SEC}; font-size:0.85em; margin-top:8px;'>{len(df_filt)} inconsistência(s)</p>", unsafe_allow_html=True)

# ── Tabela de inconsistências ─────────────────────────────────────────────────
SEV_ICON  = {"CRÍTICO": "🔴", "ALERTA": "🟡", "INFORMATIVO": "🔵"}
SEV_COLOR = {"CRÍTICO": COR_CRITICO, "ALERTA": COR_ALERTA, "INFORMATIVO": COR_INFORMATIVO}

if not df_filt.empty:
    linhas = ""
    for i, row in df_filt.iterrows():
        sev   = row.get("severidade", "")
        cor   = SEV_COLOR.get(sev, COR_BORDA)
        icon  = SEV_ICON.get(sev, "⚪")
        div   = fmt_moeda(float(row["divergencia"])) if float(row.get("divergencia") or 0) > 0 else "—"
        bg    = COR_CARD_ALT if i % 2 == 0 else COR_CARD
        linhas += f"""
        <tr style='background:{bg}; border-left:3px solid {cor};'>
            <td style='padding:9px 10px; text-align:center; font-size:1em;'>{icon}</td>
            <td style='padding:9px 12px; color:{cor}; font-weight:700; font-size:0.82em;'>{row.get("codigo_validacao","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO}; font-size:0.82em;'>{row.get("nNF","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.82em; text-align:center;'>{row.get("item","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO}; font-size:0.82em;'>{row.get("emit_xNome","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.82em; max-width:260px;'>{row.get("descricao","")}</td>
            <td style='padding:9px 12px; color:{COR_VERMELHO}; font-size:0.82em; text-align:right;'>{row.get("valor_declarado","")}</td>
            <td style='padding:9px 12px; color:{COR_CIANO}; font-size:0.82em; text-align:right;'>{row.get("valor_esperado","")}</td>
            <td style='padding:9px 12px; color:{COR_AMARELO if div != "—" else COR_TEXTO_SEC}; font-weight:700; font-size:0.82em; text-align:right;'>{div}</td>
        </tr>"""

    st.markdown(f"""
    <div class='fiscal-card' style='padding:0; overflow:auto; max-height:520px;'>
        <table style='width:100%; border-collapse:collapse; font-size:0.88em;'>
            <thead style='position:sticky; top:0; z-index:1;'>
                <tr style='background:{COR_CARD}; border-bottom:2px solid {COR_BORDA};'>
                    <th style='padding:10px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center; width:36px;'>Sev</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Cód.</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>NF</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center;'>Item</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Emitente</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Descrição</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>Declarado</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>Esperado</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>Divergência</th>
                </tr>
            </thead>
            <tbody>{linhas}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Nenhuma inconsistência encontrada com os filtros aplicados.")

# ── Exportar ──────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
if not df_filt.empty:
    st.download_button("Exportar CSV", df_filt.to_csv(index=False).encode("utf-8"),
                       "auditoria.csv", "text/csv")

# ── Anomalias ─────────────────────────────────────────────────────────────────
if not df_anomalias.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h2>⚠️ Anomalias Detectadas</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{COR_TEXTO_SEC}; margin-top:-6px;'>{len(df_anomalias)} anomalia(s) por análise de padrão</p>", unsafe_allow_html=True)

    linhas_an = ""
    for i, row in df_anomalias.iterrows():
        sev  = row.get("severidade", "")
        cor  = SEV_COLOR.get(sev, COR_BORDA)
        icon = SEV_ICON.get(sev, "⚪")
        bg   = COR_CARD_ALT if i % 2 == 0 else COR_CARD
        linhas_an += f"""
        <tr style='background:{bg}; border-left:3px solid {cor};'>
            <td style='padding:9px 10px; text-align:center; font-size:1em;'>{icon}</td>
            <td style='padding:9px 12px; color:{cor}; font-weight:700; font-size:0.82em;'>{row.get("codigo_anomalia","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO}; font-size:0.82em;'>{row.get("nNF","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO}; font-size:0.82em;'>{row.get("emit_xNome","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.82em;'>{row.get("descricao","")}</td>
            <td style='padding:9px 12px; color:{COR_VERMELHO}; font-size:0.82em; text-align:right;'>{row.get("valor_observado","")}</td>
            <td style='padding:9px 12px; color:{COR_CIANO}; font-size:0.82em; text-align:right;'>{row.get("valor_referencia","")}</td>
        </tr>"""

    st.markdown(f"""
    <div class='fiscal-card' style='padding:0; overflow:auto; max-height:400px;'>
        <table style='width:100%; border-collapse:collapse; font-size:0.88em;'>
            <thead style='position:sticky; top:0; z-index:1;'>
                <tr style='background:{COR_CARD}; border-bottom:2px solid {COR_BORDA};'>
                    <th style='padding:10px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center; width:36px;'>Sev</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Código</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>NF</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Emitente</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Descrição</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>Observado</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>Referência</th>
                </tr>
            </thead>
            <tbody>{linhas_an}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

# ── Detalhe por nota ──────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("🔍 Detalhe de uma nota específica"):
    nfs = sorted(df_filt["nNF"].dropna().unique().tolist())
    if nfs:
        nf_sel = st.selectbox("Nota Fiscal", nfs)
        for _, row in df_filt[df_filt["nNF"] == nf_sel].iterrows():
            cor = SEVERIDADE_CORES.get(row["severidade"], COR_BORDA)
            txt_badge = "#060E1A" if row["severidade"] == "ALERTA" else COR_TEXTO
            st.markdown(f"""
            <div style='background:{COR_CARD}; border-left:4px solid {cor}; border-radius:7px;
                        padding:14px 18px; margin-bottom:10px;'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                    <span style='font-weight:700; color:{COR_TEXTO}; font-size:0.95em;'>{row.get("codigo_validacao","")}</span>
                    <span style='background:{cor}; color:{txt_badge}; padding:2px 10px;
                                 border-radius:4px; font-size:0.75em; font-weight:700;'>
                        {row.get("severidade","")}
                    </span>
                </div>
                <div style='color:{COR_TEXTO}; margin-bottom:10px; font-size:0.9em;'>{row.get("descricao","")}</div>
                <div style='display:flex; gap:28px; font-size:0.82em;'>
                    <div><span style='color:{COR_TEXTO_SEC};'>Declarado:</span>
                         <span style='color:{COR_VERMELHO}; font-weight:600; margin-left:4px;'>{row.get("valor_declarado","")}</span></div>
                    <div><span style='color:{COR_TEXTO_SEC};'>Esperado:</span>
                         <span style='color:{COR_CIANO}; font-weight:600; margin-left:4px;'>{row.get("valor_esperado","")}</span></div>
                    <div><span style='color:{COR_TEXTO_SEC};'>Item:</span>
                         <span style='color:{COR_TEXTO}; margin-left:4px;'>{row.get("item","")}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhuma inconsistência encontrada com os filtros atuais.")
