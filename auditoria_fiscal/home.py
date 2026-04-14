"""Dashboard principal — conteúdo da home page."""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from utils.constants import (
    COR_FUNDO, COR_CARD, COR_BORDA,
    COR_TEXTO, COR_TEXTO_SEC,
    COR_CIANO, COR_AZUL, COR_VERDE, COR_VERMELHO, COR_AMARELO,
    COR_CRITICO, COR_ALERTA, COR_INFORMATIVO,
)
from utils.theme import plotly_layout
from utils.formatters import fmt_moeda
from core.atualizador_aliquotas import status_aliquotas

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("<h1>📊 Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{COR_TEXTO_SEC}; margin-top:-8px;'>Visão geral da auditoria fiscal</p>", unsafe_allow_html=True)
st.divider()

df_itens      = st.session_state.get("df_itens",      pd.DataFrame())
df_validacoes = st.session_state.get("df_validacoes", pd.DataFrame())
df_notas      = st.session_state.get("df_notas",      pd.DataFrame())
tem_dados     = not df_itens.empty

# ── KPIs ──────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

if tem_dados:
    total_notas     = df_itens["chNFe"].nunique() if "chNFe" in df_itens.columns else 0
    valor_total     = df_notas["tot_vNF"].sum()   if "tot_vNF" in df_notas.columns else 0
    total_inconsist = len(df_validacoes)          if not df_validacoes.empty else 0
    criticos        = len(df_validacoes[df_validacoes["severidade"] == "CRÍTICO"]) if not df_validacoes.empty else 0
    impacto         = float(df_validacoes["divergencia"].sum()) if not df_validacoes.empty and "divergencia" in df_validacoes.columns else 0
else:
    total_notas = valor_total = total_inconsist = criticos = impacto = 0

col1.metric("Notas Auditadas",  f"{total_notas:,}")
col2.metric("Valor Auditado",   fmt_moeda(float(valor_total)))
col3.metric("Inconsistências",  f"{total_inconsist:,}",
            delta=f"{criticos} críticos" if criticos else None, delta_color="inverse")
col4.metric("Impacto Estimado", fmt_moeda(impacto))

st.markdown("<br>", unsafe_allow_html=True)

# ── Gráficos ──────────────────────────────────────────────────────────────────
if tem_dados and not df_validacoes.empty:
    col_g1, col_g2 = st.columns([1, 2])

    with col_g1:
        with st.container(border=True):
            st.markdown(f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:12px;'>Distribuição por Severidade</p>", unsafe_allow_html=True)

            contagem = df_validacoes["severidade"].value_counts().reset_index()
            contagem.columns = ["severidade", "count"]
            cores_pizza = [{"CRÍTICO": COR_CRITICO, "ALERTA": COR_ALERTA, "INFORMATIVO": COR_INFORMATIVO}.get(s, COR_BORDA)
                           for s in contagem["severidade"]]

            # Texto escuro em fatias claras (amarelo), branco nas escuras
            texto_cores = ["#1A1A1A" if c == COR_ALERTA else "#FFFFFF" for c in cores_pizza]

            fig_pizza = go.Figure(go.Pie(
                labels=contagem["severidade"], values=contagem["count"],
                hole=0.62,
                marker=dict(colors=cores_pizza, line=dict(color=COR_FUNDO, width=3)),
                textinfo="label+percent",
                textfont=dict(color=texto_cores, size=11),
                textposition="auto",
                automargin=True,
                hovertemplate="<b>%{label}</b><br>%{value} inconsistências<extra></extra>",
            ))
            layout_pizza = plotly_layout(260, dict(t=24, b=24, l=24, r=24))
            layout_pizza["showlegend"] = False
            fig_pizza.update_layout(**layout_pizza)
            st.plotly_chart(fig_pizza, use_container_width=True)

    with col_g2:
        with st.container(border=True):
            st.markdown(f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:12px;'>Inconsistências por Tipo de Validação</p>", unsafe_allow_html=True)

            por_cod = df_validacoes.groupby("codigo_validacao").agg(
                count=("codigo_validacao", "count"),
                sev=("severidade", lambda x: x.mode().iloc[0])
            ).reset_index().sort_values("count", ascending=True)

            cor_map  = {"CRÍTICO": COR_CRITICO, "ALERTA": COR_ALERTA, "INFORMATIVO": COR_INFORMATIVO}
            cores_bar = [cor_map.get(s, COR_BORDA) for s in por_cod["sev"]]

            fig_bar = go.Figure(go.Bar(
                x=por_cod["count"], y=por_cod["codigo_validacao"],
                orientation="h",
                marker=dict(color=cores_bar, line=dict(color="rgba(0,0,0,0)")),
                hovertemplate="<b>%{y}</b>: %{x} ocorrências<extra></extra>",
            ))
            layout_bar = plotly_layout(260, dict(t=8, b=8, l=8, r=8))
            layout_bar["xaxis"]["showgrid"] = True
            layout_bar["yaxis"]["showgrid"] = False
            layout_bar["bargap"] = 0.38
            fig_bar.update_layout(**layout_bar)
            st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.markdown(f"""
    <div class='fiscal-card' style='text-align:center; padding:52px 24px; border:2px dashed {COR_BORDA};'>
        <div style='font-size:2.8em; margin-bottom:14px;'>📂</div>
        <div style='font-size:1.15em; font-weight:700; color:{COR_TEXTO}; margin-bottom:8px;'>
            Nenhuma nota fiscal carregada
        </div>
        <div style='color:{COR_TEXTO_SEC}; margin-bottom:28px; font-size:0.92em;'>
            Acesse <strong style='color:{COR_CIANO};'>Upload NFe</strong> para carregar XMLs e iniciar a auditoria.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Ir para Upload de NFe"):
        st.switch_page("pages/01_upload_nfe.py")

# ── Status das Alíquotas ──────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### Status das Alíquotas")

status = status_aliquotas()
col_s1, col_s2, col_s3, col_s4 = st.columns(4)


def _card_status(col, icone, titulo, vigencia, detalhe, cor=COR_CIANO):
    with col:
        st.markdown(f"""
        <div class='fiscal-card' style='padding:16px; border-left:3px solid {cor};'>
            <div style='display:flex; align-items:center; gap:8px; margin-bottom:10px;'>
                <span style='font-size:1.1em;'>{icone}</span>
                <span style='font-weight:700; color:{COR_TEXTO}; font-size:0.95em;'>{titulo}</span>
            </div>
            <div style='color:{cor}; font-size:0.78em; margin-bottom:4px;'>Vigência: {vigencia}</div>
            <div style='color:{COR_TEXTO_SEC}; font-size:0.78em; line-height:1.5;'>{detalhe}</div>
        </div>
        """, unsafe_allow_html=True)


_card_status(col_s1, "🏛️", "ICMS",       status["icms"]["vigencia"],
             f"{status['icms']['estados_internos']} estados · {status['icms']['tabela_interestadual']} pares interestaduais", COR_CIANO)
_card_status(col_s2, "🏙️", "ISS",        status["iss"]["vigencia"],
             f"{status['iss']['municipios_mapeados']} municípios · {status['iss']['minimo_legal']}%–{status['iss']['maximo_legal']}%", COR_AZUL)
_card_status(col_s3, "🏭", "IPI (TIPI)", status["ipi"]["vigencia"],
             f"{status['ipi']['ncms_mapeados']} NCMs mapeados", COR_AMARELO)
_card_status(col_s4, "📋", "PIS/COFINS", "Vigente",
             "Cumulativo: 0,65%/3,00%<br>Não-cumulativo: 1,65%/7,60%", COR_VERDE)
