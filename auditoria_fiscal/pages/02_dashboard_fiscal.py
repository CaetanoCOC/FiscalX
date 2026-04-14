"""Página 2 — Dashboard Fiscal"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from utils.formatters import fmt_moeda, fmt_cnpj
from utils.constants import (
    COR_FUNDO, COR_CARD, COR_CARD_ALT, COR_BORDA,
    COR_TEXTO, COR_TEXTO_SEC,
    COR_CIANO, COR_AZUL, COR_VERDE, COR_VERMELHO, COR_AMARELO,
    PALETA_GRAFICOS, SEVERIDADE_CORES,
)
from utils.theme import plotly_layout

st.markdown("<h1>📈 Dashboard Fiscal</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{COR_TEXTO_SEC}; margin-top:-8px;'>Análise visual das operações auditadas</p>", unsafe_allow_html=True)
st.divider()

df_itens      = st.session_state.get("df_itens",      pd.DataFrame())
df_notas      = st.session_state.get("df_notas",      pd.DataFrame())
df_validacoes = st.session_state.get("df_validacoes", pd.DataFrame())

if df_notas.empty:
    st.warning("Nenhum dado carregado. Acesse **Upload NFe** primeiro.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Notas Auditadas",   f"{len(df_notas):,}")
col2.metric("Valor Total",       fmt_moeda(float(df_notas["tot_vNF"].sum())))
col3.metric("Inconsistências",   f"{len(df_validacoes):,}")
impacto = float(df_validacoes["divergencia"].sum()) if not df_validacoes.empty and "divergencia" in df_validacoes.columns else 0
col4.metric("Impacto Estimado",  fmt_moeda(impacto))

st.markdown("<br>", unsafe_allow_html=True)

# ── Linha mensal + Donut tipo de operação ────────────────────────────────────
col_g1, col_g2 = st.columns([2, 1])

with col_g1:
    with st.container(border=True):
        st.markdown(f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:4px;'>Evolução Mensal — Valor Auditado</p>", unsafe_allow_html=True)
        df_c = df_notas.copy()
        df_c["mes"] = pd.to_datetime(df_c["dhEmi"].str[:7], format="%Y-%m", errors="coerce")
        mensal = df_c.groupby("mes")["tot_vNF"].sum().reset_index().dropna(subset=["mes"]).sort_values("mes")

        if not mensal.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=mensal["mes"], y=mensal["tot_vNF"],
                mode="lines+markers",
                line=dict(color=COR_CIANO, width=2.5),
                marker=dict(color=COR_CIANO, size=7, line=dict(color=COR_FUNDO, width=2)),
                fill="tozeroy", fillcolor="rgba(0,205,205,0.08)",
                hovertemplate="<b>%{x|%b %Y}</b><br>R$ %{y:,.2f}<extra></extra>",
            ))
            fig.update_layout(**plotly_layout(270))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para gráfico mensal.")

with col_g2:
    with st.container(border=True):
        st.markdown(f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:4px;'>Tipo de Operação</p>", unsafe_allow_html=True)
        tipo_count = df_notas["tpNF"].map({"0": "Entrada", "1": "Saída"}).value_counts()
        fig_d = go.Figure(go.Pie(
            labels=tipo_count.index, values=tipo_count.values, hole=0.62,
            marker=dict(colors=[COR_AZUL, COR_CIANO], line=dict(color=COR_FUNDO, width=3)),
            textinfo="label+percent",
            textfont=dict(color=COR_TEXTO, size=11),
            textposition="auto",
            automargin=True,
        ))
        layout_d = plotly_layout(270, dict(t=24, b=24, l=24, r=24))
        layout_d["showlegend"] = False
        fig_d.update_layout(**layout_d)
        st.plotly_chart(fig_d, use_container_width=True)

# ── Valor por UF + Treemap CFOP ───────────────────────────────────────────────
col_g3, col_g4 = st.columns(2)

with col_g3:
    with st.container(border=True):
        st.markdown(f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:4px;'>Valor por UF de Destino</p>", unsafe_allow_html=True)
        if "dest_UF" in df_notas.columns:
            por_uf = df_notas.groupby("dest_UF")["tot_vNF"].sum().reset_index().sort_values("tot_vNF", ascending=False).head(15)
            fig_uf = go.Figure(go.Bar(
                x=por_uf["dest_UF"], y=por_uf["tot_vNF"],
                marker=dict(
                    color=por_uf["tot_vNF"],
                    colorscale=[[0, COR_CARD], [1, COR_CIANO]],
                    line=dict(color="rgba(0,0,0,0)"),
                ),
                hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>",
            ))
            layout_uf = plotly_layout(270)
            layout_uf["yaxis"]["showgrid"] = True
            layout_uf["xaxis"]["showgrid"] = False
            fig_uf.update_layout(**layout_uf)
            st.plotly_chart(fig_uf, use_container_width=True)

with col_g4:
    with st.container(border=True):
        st.markdown(f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:4px;'>Distribuição por CFOP</p>", unsafe_allow_html=True)
        if not df_itens.empty and "CFOP" in df_itens.columns:
            por_cfop = df_itens.groupby("CFOP")["vProd"].sum().reset_index()
            por_cfop = por_cfop[por_cfop["vProd"] > 0].sort_values("vProd", ascending=False).head(12)
            if not por_cfop.empty:
                fig_tree = px.treemap(
                    por_cfop, path=["CFOP"], values="vProd",
                    color="vProd",
                    color_continuous_scale=[[0, "#111827"], [1, COR_CIANO]],
                )
                fig_tree.update_traces(
                    textfont=dict(color=COR_TEXTO),
                    hovertemplate="<b>CFOP %{label}</b><br>R$ %{value:,.2f}<extra></extra>",
                    marker=dict(line=dict(color=COR_FUNDO, width=2)),
                )
                fig_tree.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=8,b=8,l=8,r=8), height=270,
                    coloraxis_showscale=False,
                    font=dict(color=COR_TEXTO),
                )
                st.plotly_chart(fig_tree, use_container_width=True)

# ── Top 10 Fornecedores ───────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
top = (df_notas.groupby(["emit_CNPJ","emit_xNome","emit_UF"])
       .agg(total=("tot_vNF","sum"), notas=("chNFe","count"))
       .reset_index().sort_values("total", ascending=False).head(10))

if not top.empty:
    total_geral = top["total"].sum()
    linhas = ""
    for i, row in top.iterrows():
        pct = f"{row['total']/total_geral*100:.1f}%" if total_geral else "—"
        bg = COR_CARD_ALT if i % 2 == 0 else COR_CARD
        linhas += f"""
        <tr style='background:{bg};'>
            <td style='padding:10px 14px; color:{COR_TEXTO_SEC}; font-family:monospace; font-size:0.82em;'>{fmt_cnpj(row['emit_CNPJ'])}</td>
            <td style='padding:10px 14px; color:{COR_TEXTO}; font-weight:600;'>{row['emit_xNome']}</td>
            <td style='padding:10px 14px; color:{COR_CIANO}; font-weight:600; text-align:center;'>{row['emit_UF']}</td>
            <td style='padding:10px 14px; color:{COR_VERDE}; font-weight:700; text-align:right;'>{fmt_moeda(row['total'])}</td>
            <td style='padding:10px 14px; color:{COR_TEXTO}; text-align:center;'>{int(row['notas'])}</td>
            <td style='padding:10px 14px; color:{COR_AMARELO}; text-align:right;'>{pct}</td>
        </tr>"""

    st.markdown(f"""
    <div class='fiscal-card' style='padding:0; overflow:hidden;'>
        <div style='padding:16px 20px 12px; border-bottom:1px solid {COR_BORDA};'>
            <span style='font-weight:600; color:{COR_TEXTO};'>Top 10 Fornecedores por Valor</span>
        </div>
        <table style='width:100%; border-collapse:collapse; font-size:0.88em;'>
            <thead>
                <tr style='border-bottom:1px solid {COR_BORDA};'>
                    <th style='padding:10px 14px; color:{COR_TEXTO_SEC}; font-size:0.75em; text-transform:uppercase; letter-spacing:0.06em; text-align:left; font-weight:600;'>CNPJ</th>
                    <th style='padding:10px 14px; color:{COR_TEXTO_SEC}; font-size:0.75em; text-transform:uppercase; letter-spacing:0.06em; text-align:left; font-weight:600;'>Razão Social</th>
                    <th style='padding:10px 14px; color:{COR_TEXTO_SEC}; font-size:0.75em; text-transform:uppercase; letter-spacing:0.06em; text-align:center; font-weight:600;'>UF</th>
                    <th style='padding:10px 14px; color:{COR_TEXTO_SEC}; font-size:0.75em; text-transform:uppercase; letter-spacing:0.06em; text-align:right; font-weight:600;'>Total</th>
                    <th style='padding:10px 14px; color:{COR_TEXTO_SEC}; font-size:0.75em; text-transform:uppercase; letter-spacing:0.06em; text-align:center; font-weight:600;'>Notas</th>
                    <th style='padding:10px 14px; color:{COR_TEXTO_SEC}; font-size:0.75em; text-transform:uppercase; letter-spacing:0.06em; text-align:right; font-weight:600;'>% Total</th>
                </tr>
            </thead>
            <tbody>{linhas}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
