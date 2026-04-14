"""Página 5 — Relatório e Exportação"""

import io
from datetime import datetime

import streamlit as st
import pandas as pd

from utils.formatters import fmt_moeda, fmt_cnpj
from utils.constants import (
    COR_CARD, COR_BORDA,
    COR_TEXTO, COR_TEXTO_SEC,
    COR_CIANO, COR_AZUL, COR_VERMELHO, COR_AMARELO,
    COR_CRITICO, COR_ALERTA, COR_INFORMATIVO,
)

st.markdown("<h1>📄 Relatório e Exportação</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{COR_TEXTO_SEC}; margin-top:-8px;'>Gere e exporte o relatório completo de auditoria fiscal</p>", unsafe_allow_html=True)
st.divider()

df_notas      = st.session_state.get("df_notas",      pd.DataFrame())
df_validacoes = st.session_state.get("df_validacoes", pd.DataFrame())
df_anomalias  = st.session_state.get("df_anomalias",  pd.DataFrame())
df_itens      = st.session_state.get("df_itens",      pd.DataFrame())

if df_notas.empty:
    st.warning("Nenhum dado carregado. Acesse **Upload NFe** primeiro.")
    st.stop()

# ── Formulário ────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:14px;'>Informações do Relatório</p>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        empresa      = st.text_input("Empresa Auditada",   placeholder="Nome da empresa")
        cnpj_empresa = st.text_input("CNPJ",               placeholder="00.000.000/0001-00")
    with c2:
        responsavel  = st.text_input("Responsável Técnico",placeholder="Nome do auditor")
        periodo_rel  = st.text_input("Período",            placeholder="Ex: Janeiro/2024")
    observacoes = st.text_area("Observações", placeholder="Observações gerais…", height=72)

# ── Dados ─────────────────────────────────────────────────────────────────────
data_ger     = datetime.now().strftime("%d/%m/%Y %H:%M")
total_notas  = len(df_notas)
valor_total  = float(df_notas["tot_vNF"].sum()) if "tot_vNF" in df_notas.columns else 0
criticos     = len(df_validacoes[df_validacoes["severidade"] == "CRÍTICO"])    if not df_validacoes.empty else 0
alertas      = len(df_validacoes[df_validacoes["severidade"] == "ALERTA"])     if not df_validacoes.empty else 0
informativos = len(df_validacoes[df_validacoes["severidade"] == "INFORMATIVO"])if not df_validacoes.empty else 0
impacto      = float(df_validacoes["divergencia"].sum()) if not df_validacoes.empty and "divergencia" in df_validacoes.columns else 0

# ── Preview ───────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<h2>Preview do Relatório</h2>", unsafe_allow_html=True)

st.markdown(f"""
<div class='fiscal-card' style='border:1px solid {COR_CIANO};'>
  <div style='display:flex; justify-content:space-between; align-items:center;
               border-bottom:2px solid {COR_CIANO}; padding-bottom:16px; margin-bottom:20px;'>
    <div>
      <div style='font-size:1.3em; font-weight:700; color:{COR_CIANO}; letter-spacing:-0.01em;'>🔍 FiscalX</div>
      <div style='color:{COR_TEXTO_SEC}; font-size:0.78em; margin-top:2px;'>Sistema de Auditoria Fiscal Automatizada</div>
    </div>
    <div style='color:{COR_TEXTO_SEC}; font-size:0.75em; text-align:right;'>Gerado em:<br>{data_ger}</div>
  </div>

  <div style='display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:20px; font-size:0.88em;'>
    <div><div style='color:{COR_TEXTO_SEC}; font-size:0.75em; text-transform:uppercase; letter-spacing:0.08em;'>Empresa</div>
         <div style='color:{COR_TEXTO}; font-weight:600;'>{empresa or "—"}</div></div>
    <div><div style='color:{COR_TEXTO_SEC}; font-size:0.75em; text-transform:uppercase; letter-spacing:0.08em;'>CNPJ</div>
         <div style='color:{COR_TEXTO}; font-weight:600;'>{cnpj_empresa or "—"}</div></div>
    <div><div style='color:{COR_TEXTO_SEC}; font-size:0.75em; text-transform:uppercase; letter-spacing:0.08em;'>Período</div>
         <div style='color:{COR_TEXTO}; font-weight:600;'>{periodo_rel or "—"}</div></div>
    <div><div style='color:{COR_TEXTO_SEC}; font-size:0.75em; text-transform:uppercase; letter-spacing:0.08em;'>Responsável</div>
         <div style='color:{COR_TEXTO}; font-weight:600;'>{responsavel or "—"}</div></div>
  </div>

  <div style='display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:18px;'>
    <div style='background:#0B1120; border-radius:8px; padding:14px; text-align:center;'>
      <div style='color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Notas</div>
      <div style='color:{COR_TEXTO}; font-size:1.5em; font-weight:700; margin-top:4px;'>{total_notas}</div>
    </div>
    <div style='background:#0B1120; border-radius:8px; padding:14px; text-align:center;'>
      <div style='color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Valor Total</div>
      <div style='color:{COR_CIANO}; font-size:1.1em; font-weight:700; margin-top:4px;'>{fmt_moeda(valor_total)}</div>
    </div>
    <div style='background:#0B1120; border-radius:8px; padding:14px; text-align:center;'>
      <div style='color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Inconsistências</div>
      <div style='color:{COR_VERMELHO}; font-size:1.5em; font-weight:700; margin-top:4px;'>{criticos+alertas+informativos}</div>
    </div>
    <div style='background:#0B1120; border-radius:8px; padding:14px; text-align:center;'>
      <div style='color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Impacto</div>
      <div style='color:{COR_AMARELO}; font-size:1.1em; font-weight:700; margin-top:4px;'>{fmt_moeda(impacto)}</div>
    </div>
  </div>

  <div style='display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:{'16px' if observacoes else '0'};'>
    <div style='background:rgba(224,82,82,0.10); border-left:3px solid {COR_CRITICO}; border-radius:5px; padding:10px 14px;'>
      <div style='color:{COR_CRITICO}; font-weight:700; font-size:1.4em;'>{criticos}</div>
      <div style='color:{COR_TEXTO_SEC}; font-size:0.78em; margin-top:2px;'>Críticos</div>
    </div>
    <div style='background:rgba(247,195,75,0.10); border-left:3px solid {COR_ALERTA}; border-radius:5px; padding:10px 14px;'>
      <div style='color:{COR_ALERTA}; font-weight:700; font-size:1.4em;'>{alertas}</div>
      <div style='color:{COR_TEXTO_SEC}; font-size:0.78em; margin-top:2px;'>Alertas</div>
    </div>
    <div style='background:rgba(75,159,225,0.10); border-left:3px solid {COR_INFORMATIVO}; border-radius:5px; padding:10px 14px;'>
      <div style='color:{COR_INFORMATIVO}; font-weight:700; font-size:1.4em;'>{informativos}</div>
      <div style='color:{COR_TEXTO_SEC}; font-size:0.78em; margin-top:2px;'>Informativos</div>
    </div>
  </div>
  {f'<div style="color:{COR_TEXTO_SEC}; font-size:0.82em; border-top:1px solid {COR_BORDA}; padding-top:12px; margin-top:4px;"><strong style=color:{COR_TEXTO};>Observações:</strong> {observacoes}</div>' if observacoes else ""}
</div>
""", unsafe_allow_html=True)

# ── Exportação ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<h2>Exportar</h2>", unsafe_allow_html=True)

def _gerar_excel() -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame({"Campo": ["Empresa","CNPJ","Período","Responsável","Total Notas",
                                  "Valor Total","Críticos","Alertas","Informativos","Impacto","Gerado em"],
                       "Valor": [empresa,cnpj_empresa,periodo_rel,responsavel,total_notas,
                                  valor_total,criticos,alertas,informativos,impacto,data_ger]
                      }).to_excel(w, sheet_name="Resumo", index=False)
        if not df_notas.empty:      df_notas.to_excel(w, sheet_name="Notas", index=False)
        if not df_validacoes.empty:
            for sev, aba in [("CRÍTICO","Críticos"),("ALERTA","Alertas"),("INFORMATIVO","Informativos")]:
                df_s = df_validacoes[df_validacoes["severidade"] == sev]
                if not df_s.empty: df_s.to_excel(w, sheet_name=aba, index=False)
        if not df_anomalias.empty: df_anomalias.to_excel(w, sheet_name="Anomalias", index=False)
        if not df_itens.empty:     df_itens.to_excel(w, sheet_name="Itens NFe", index=False)
    return buf.getvalue()

col_e1, col_e2, col_e3 = st.columns(3)

with col_e1:
    with st.container(border=True):
        st.markdown(f"<div style='height:3px; background:{COR_CIANO}; border-radius:3px 3px 0 0; margin:-20px -20px 16px -20px;'></div>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-weight:700; color:{COR_TEXTO}; text-align:center;'>Excel (.xlsx)</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{COR_TEXTO_SEC}; font-size:0.82em; text-align:center;'>Resumo · Notas · Críticos · Alertas · Anomalias · Itens</p>", unsafe_allow_html=True)
        st.download_button("Baixar Excel", _gerar_excel(),
                           f"fiscalx_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

with col_e2:
    with st.container(border=True):
        st.markdown(f"<div style='height:3px; background:{COR_AZUL}; border-radius:3px 3px 0 0; margin:-20px -20px 16px -20px;'></div>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-weight:700; color:{COR_TEXTO}; text-align:center;'>CSV — Inconsistências</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{COR_TEXTO_SEC}; font-size:0.82em; text-align:center;'>Dados brutos para importação em outros sistemas</p>", unsafe_allow_html=True)
        csv_i = df_validacoes.to_csv(index=False).encode("utf-8") if not df_validacoes.empty else b""
        st.download_button("Baixar CSV", csv_i,
                           f"inconsistencias_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv",
                           use_container_width=True)

with col_e3:
    with st.container(border=True):
        st.markdown(f"<div style='height:3px; background:{COR_AMARELO}; border-radius:3px 3px 0 0; margin:-20px -20px 16px -20px;'></div>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-weight:700; color:{COR_TEXTO}; text-align:center;'>CSV — Notas Fiscais</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:{COR_TEXTO_SEC}; font-size:0.82em; text-align:center;'>Todas as notas auditadas em formato CSV</p>", unsafe_allow_html=True)
        csv_n = df_notas.to_csv(index=False).encode("utf-8") if not df_notas.empty else b""
        st.download_button("Baixar CSV", csv_n,
                           f"notas_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv",
                           use_container_width=True)
