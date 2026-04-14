"""Página 6 — Conciliação DE PARA"""

import io
import zipfile
import streamlit as st
import pandas as pd

from core.conciliador_cadastro import (
    conciliar,
    gerar_template_fornecedores,
    gerar_template_produtos,
)
from utils.constants import (
    COR_CARD, COR_CARD_ALT, COR_BORDA,
    COR_TEXTO, COR_TEXTO_SEC,
    COR_CIANO, COR_VERDE, COR_VERMELHO, COR_AMARELO, COR_AZUL,
    COR_CRITICO, COR_ALERTA,
)

st.markdown("<h1>🔗 Conciliação DE PARA</h1>", unsafe_allow_html=True)
st.markdown(
    f"<p style='color:{COR_TEXTO_SEC}; margin-top:-8px;'>"
    "Cruze os dados das NFes com o cadastro interno — valide fornecedores, NCM e CFOP"
    "</p>",
    unsafe_allow_html=True,
)
st.divider()

SEV_ICON  = {"CRÍTICO": "🔴", "ALERTA": "🟡", "INFORMATIVO": "🔵"}
SEV_COLOR = {"CRÍTICO": COR_CRITICO, "ALERTA": COR_ALERTA}

df_notas = st.session_state.get("df_notas", pd.DataFrame())
df_itens = st.session_state.get("df_itens", pd.DataFrame())

if df_notas.empty:
    st.warning("Nenhuma NFe auditada. Acesse **Upload NFe** para carregar e auditar primeiro.")
    st.stop()

# ── Helpers ───────────────────────────────────────────────────────────────────
def _ler_df(conteudo: bytes, nome: str) -> pd.DataFrame:
    if nome.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(conteudo), dtype=str).fillna("")
    return pd.read_excel(io.BytesIO(conteudo), dtype=str).fillna("")

def _e_forn(nome: str, df: pd.DataFrame) -> bool:
    n = nome.lower()
    tem_nome = any(p in n for p in ("forn", "fornecedor", "supplier"))
    tem_col  = "cnpj_fornecedor" in df.columns and "cProd" not in df.columns
    return tem_nome or tem_col

def _e_prod(nome: str, df: pd.DataFrame) -> bool:
    n = nome.lower()
    tem_nome = any(p in n for p in ("prod", "produto", "product", "item"))
    tem_col  = "cProd" in df.columns
    return tem_nome or tem_col

# ── Seção de upload + templates ───────────────────────────────────────────────
with st.expander("ℹ️ O que é o DE PARA?", expanded=False):
    st.markdown(f"""
    <div style='color:{COR_TEXTO}; font-size:0.9em; line-height:1.8em;'>
        Mapeia CNPJs e códigos de produto das NFes para o cadastro interno (ERP).<br>
        <span style='color:{COR_TEXTO_SEC};'>
        • Detecta fornecedores não cadastrados ou inativos (V13)<br>
        • Aponta NCM divergente do cadastro tributário interno (V14)<br>
        • Identifica CFOP errado que afeta apuração de créditos/débitos (V15)
        </span>
    </div>
    """, unsafe_allow_html=True)

col_up, col_tmpl = st.columns([3, 1])

with col_tmpl:
    st.markdown(f"<p style='color:{COR_TEXTO_SEC}; font-size:0.82em; margin-bottom:6px;'>Baixar templates</p>", unsafe_allow_html=True)
    buf_tf = io.BytesIO()
    gerar_template_fornecedores().to_excel(buf_tf, index=False, engine="openpyxl")
    st.download_button("⬇ Fornecedores", buf_tf.getvalue(),
                       "template_fornecedores.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True, key="tmpl_forn")
    buf_tp = io.BytesIO()
    gerar_template_produtos().to_excel(buf_tp, index=False, engine="openpyxl")
    st.download_button("⬇ Produtos", buf_tp.getvalue(),
                       "template_produtos.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True, key="tmpl_prod")

with col_up:
    with st.container(border=True):
        st.markdown(
            f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:4px;'>Upload do DE PARA</p>"
            f"<p style='color:{COR_TEXTO_SEC}; font-size:0.83em; margin-bottom:10px;'>"
            "Aceita <strong>DEPARA.zip</strong> (com as duas planilhas), ou cada planilha separadamente (CSV / XLSX)</p>",
            unsafe_allow_html=True,
        )
        arq = st.file_uploader(
            "depara_upload", type=["zip", "csv", "xlsx"],
            accept_multiple_files=True,
            label_visibility="collapsed", key="upload_depara",
        )

# Processa uploads
if arq:
    for f in arq:
        nome = f.name
        conteudo = f.read()
        if nome.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
                    membros = [m for m in zf.namelist()
                               if m.lower().endswith((".csv", ".xlsx")) and not m.startswith("__")]
                    for membro in membros:
                        nome_base = membro.split("/")[-1]
                        try:
                            df_tmp = _ler_df(zf.read(membro), nome_base)
                        except Exception:
                            continue
                        if _e_forn(nome_base, df_tmp):
                            st.session_state["df_de_para_forn"] = df_tmp
                        elif _e_prod(nome_base, df_tmp):
                            st.session_state["df_de_para_prod"] = df_tmp
            except Exception as e:
                st.error(f"Erro ao abrir ZIP: {e}")
        else:
            try:
                df_tmp = _ler_df(conteudo, nome)
                if _e_forn(nome, df_tmp):
                    st.session_state["df_de_para_forn"] = df_tmp
                elif _e_prod(nome, df_tmp):
                    st.session_state["df_de_para_prod"] = df_tmp
                else:
                    st.warning(f"Não foi possível identificar o tipo de '{nome}'. Verifique as colunas.")
            except Exception as e:
                st.error(f"Erro ao ler '{nome}': {e}")

# Status do que está carregado
df_dp_forn = st.session_state.get("df_de_para_forn", pd.DataFrame())
df_dp_prod = st.session_state.get("df_de_para_prod", pd.DataFrame())

if not df_dp_forn.empty or not df_dp_prod.empty:
    badges = []
    if not df_dp_forn.empty:
        badges.append(f"<span style='background:{COR_VERDE}22; color:{COR_VERDE}; padding:3px 10px; border-radius:4px; font-size:0.8em; font-weight:700;'>✓ Fornecedores: {len(df_dp_forn)} registros</span>")
    if not df_dp_prod.empty:
        badges.append(f"<span style='background:{COR_VERDE}22; color:{COR_VERDE}; padding:3px 10px; border-radius:4px; font-size:0.8em; font-weight:700;'>✓ Produtos: {len(df_dp_prod)} registros</span>")
    st.markdown(
        f"<div style='margin-top:10px; display:flex; gap:10px;'>{''.join(badges)}</div>",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Abas — apenas visualização e resultado ────────────────────────────────────
tab_forn, tab_prod, tab_resultado = st.tabs([
    "🏢 Fornecedores carregados",
    "📦 Produtos carregados",
    "📋 Resultado da Conciliação",
])

# ── TAB 1 — preview fornecedores ──────────────────────────────────────────────
with tab_forn:
    if df_dp_forn.empty:
        st.info("Nenhum DE PARA de fornecedores carregado. Faça o upload acima.")
    else:
        st.markdown(f"<p style='color:{COR_TEXTO_SEC}; font-size:0.85em;'>{len(df_dp_forn)} registro(s)</p>", unsafe_allow_html=True)
        linhas = ""
        for i, row in df_dp_forn.iterrows():
            ativo = str(row.get("ativo", "S")).upper()
            cor_a = COR_VERDE if ativo == "S" else COR_VERMELHO
            bg    = COR_CARD_ALT if i % 2 == 0 else COR_CARD
            linhas += f"""
            <tr style='background:{bg};'>
                <td style='padding:8px 12px; color:{COR_CIANO}; font-size:0.82em;'>{row.get("cnpj_fornecedor","")}</td>
                <td style='padding:8px 12px; color:{COR_TEXTO}; font-size:0.82em; font-weight:600;'>{row.get("cod_interno","")}</td>
                <td style='padding:8px 12px; color:{COR_TEXTO}; font-size:0.82em;'>{row.get("nome_interno","")}</td>
                <td style='padding:8px 12px; text-align:center;'>
                    <span style='background:{cor_a}22; color:{cor_a}; padding:2px 8px; border-radius:4px; font-size:0.78em; font-weight:700;'>{ativo}</span>
                </td>
            </tr>"""
        st.markdown(f"""
        <div class='fiscal-card' style='padding:0; overflow:auto; max-height:340px;'>
            <table style='width:100%; border-collapse:collapse;'>
                <thead style='position:sticky; top:0; z-index:1;'>
                    <tr style='background:{COR_CARD}; border-bottom:2px solid {COR_BORDA};'>
                        <th style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>CNPJ Fornecedor</th>
                        <th style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Cód. Interno</th>
                        <th style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Nome Interno</th>
                        <th style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center;'>Ativo</th>
                    </tr>
                </thead>
                <tbody>{linhas}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 2 — preview produtos ──────────────────────────────────────────────────
with tab_prod:
    if df_dp_prod.empty:
        st.info("Nenhum DE PARA de produtos carregado. Faça o upload acima.")
    else:
        st.markdown(f"<p style='color:{COR_TEXTO_SEC}; font-size:0.85em;'>{len(df_dp_prod)} registro(s)</p>", unsafe_allow_html=True)
        linhas2 = ""
        for i, row in df_dp_prod.iterrows():
            bg = COR_CARD_ALT if i % 2 == 0 else COR_CARD
            linhas2 += f"""
            <tr style='background:{bg};'>
                <td style='padding:8px 12px; color:{COR_CIANO}; font-size:0.82em;'>{row.get("cnpj_fornecedor","")}</td>
                <td style='padding:8px 12px; color:{COR_TEXTO}; font-size:0.82em; font-weight:600;'>{row.get("cProd","")}</td>
                <td style='padding:8px 12px; color:{COR_TEXTO}; font-size:0.82em;'>{row.get("cod_interno","")}</td>
                <td style='padding:8px 12px; color:{COR_TEXTO_SEC}; font-size:0.82em;'>{row.get("desc_interna","")}</td>
                <td style='padding:8px 12px; color:{COR_AMARELO}; font-size:0.82em; font-weight:600;'>{row.get("ncm_esperado","")}</td>
                <td style='padding:8px 12px; color:{COR_AZUL}; font-size:0.82em; font-weight:600;'>{row.get("cfop_esperado","")}</td>
            </tr>"""
        st.markdown(f"""
        <div class='fiscal-card' style='padding:0; overflow:auto; max-height:340px;'>
            <table style='width:100%; border-collapse:collapse;'>
                <thead style='position:sticky; top:0; z-index:1;'>
                    <tr style='background:{COR_CARD}; border-bottom:2px solid {COR_BORDA};'>
                        <th style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>CNPJ Fornecedor</th>
                        <th style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Cód. Produto</th>
                        <th style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Cód. Interno</th>
                        <th style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Descrição</th>
                        <th style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>NCM Esperado</th>
                        <th style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>CFOP Esperado</th>
                    </tr>
                </thead>
                <tbody>{linhas2}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

# ── TAB 3 — resultado ─────────────────────────────────────────────────────────
with tab_resultado:
    if df_dp_forn.empty and df_dp_prod.empty:
        st.info("Carregue o DEPARA.zip para executar a conciliação.")
        st.stop()

    col_btn, col_status = st.columns([1, 2])
    with col_btn:
        executar = st.button("🔗 Executar Conciliação", use_container_width=True)
    with col_status:
        partes = []
        if not df_dp_forn.empty: partes.append(f"{len(df_dp_forn)} fornecedor(es)")
        if not df_dp_prod.empty: partes.append(f"{len(df_dp_prod)} produto(s)")
        st.markdown(
            f"<p style='color:{COR_TEXTO_SEC}; padding-top:10px;'>"
            f"{' · '.join(partes)} contra {len(df_notas)} NFe(s).</p>",
            unsafe_allow_html=True,
        )

    if executar:
        with st.spinner("Executando conciliação..."):
            df_result = conciliar(
                df_notas, df_itens,
                df_dp_forn if not df_dp_forn.empty else None,
                df_dp_prod if not df_dp_prod.empty else None,
            )
        st.session_state["df_de_para_result"] = df_result

    df_result = st.session_state.get("df_de_para_result", None)
    if df_result is None:
        st.stop()

    if isinstance(df_result, pd.DataFrame) and df_result.empty:
        st.success("Nenhuma divergência encontrada.")
        st.stop()

    # KPIs
    criticos = len(df_result[df_result["severidade"] == "CRÍTICO"])
    alertas  = len(df_result[df_result["severidade"] == "ALERTA"])
    v13 = len(df_result[df_result["codigo_validacao"] == "V13"])
    v14 = len(df_result[df_result["codigo_validacao"] == "V14"])
    v15 = len(df_result[df_result["codigo_validacao"] == "V15"])

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total",                    len(df_result))
    c2.metric("Críticos",                 criticos)
    c3.metric("Alertas",                  alertas)
    c4.metric("Fornec. s/ cadastro (V13)",v13)
    c5.metric("NCM / CFOP errado",        v14 + v15)
    st.markdown("<br>", unsafe_allow_html=True)

    # Filtros
    with st.container(border=True):
        cf1, cf2, cf3 = st.columns(3)
        with cf1:
            sev_f = st.multiselect("Severidade", ["CRÍTICO", "ALERTA"], default=["CRÍTICO", "ALERTA"])
        with cf2:
            cod_opts = sorted(df_result["codigo_validacao"].unique().tolist())
            cod_f    = st.multiselect("Validação", cod_opts, default=cod_opts)
        with cf3:
            busca_f = st.text_input("Buscar", placeholder="fornecedor, NCM, CFOP…")

    df_filt = df_result.copy()
    if sev_f:   df_filt = df_filt[df_filt["severidade"].isin(sev_f)]
    if cod_f:   df_filt = df_filt[df_filt["codigo_validacao"].isin(cod_f)]
    if busca_f: df_filt = df_filt[df_filt["descricao"].str.contains(busca_f, case=False, na=False)]

    st.markdown(
        f"<p style='color:{COR_TEXTO_SEC}; font-size:0.85em; margin-top:4px;'>{len(df_filt)} divergência(s)</p>",
        unsafe_allow_html=True,
    )

    if df_filt.empty:
        st.info("Nenhuma divergência com os filtros aplicados.")
        st.stop()

    linhas_r = ""
    for i, row in df_filt.iterrows():
        sev  = row.get("severidade", "")
        cor  = SEV_COLOR.get(sev, COR_BORDA)
        icon = SEV_ICON.get(sev, "⚪")
        cod  = row.get("codigo_validacao", "")
        bg   = COR_CARD_ALT if i % 2 == 0 else COR_CARD
        cod_cor = {"V13": COR_ALERTA, "V14": COR_CRITICO, "V15": COR_CRITICO}.get(cod, COR_TEXTO_SEC)
        linhas_r += f"""
        <tr style='background:{bg}; border-left:3px solid {cor};'>
            <td style='padding:9px 10px; text-align:center;'>{icon}</td>
            <td style='padding:9px 12px; color:{cod_cor}; font-weight:700; font-size:0.82em;'>{cod}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO}; font-size:0.82em;'>{row.get("nNF","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO_SEC}; text-align:center; font-size:0.82em;'>{row.get("item","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO}; font-size:0.82em;'>{row.get("emit_xNome","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.82em; max-width:280px;'>{row.get("descricao","")}</td>
            <td style='padding:9px 12px; color:{COR_VERMELHO}; font-size:0.82em; text-align:right;'>{row.get("valor_declarado","")}</td>
            <td style='padding:9px 12px; color:{COR_CIANO}; font-size:0.82em; text-align:right;'>{row.get("valor_esperado","")}</td>
        </tr>"""

    st.markdown(f"""
    <div class='fiscal-card' style='padding:0; overflow:auto; max-height:500px;'>
        <table style='width:100%; border-collapse:collapse; font-size:0.88em;'>
            <thead style='position:sticky; top:0; z-index:1;'>
                <tr style='background:{COR_CARD}; border-bottom:2px solid {COR_BORDA};'>
                    <th style='padding:10px 10px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center; width:36px;'>Sev</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Cód.</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>NF</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center;'>Item</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Emitente</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em;'>Divergência</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>Declarado (NFe)</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>Esperado (Cadastro)</th>
                </tr>
            </thead>
            <tbody>{linhas_r}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "⬇ Exportar CSV", df_filt.to_csv(index=False).encode("utf-8"),
            "de_para_divergencias.csv", "text/csv", use_container_width=True,
        )
    with col_dl2:
        buf_xl = io.BytesIO()
        df_filt.to_excel(buf_xl, index=False, engine="openpyxl")
        st.download_button(
            "⬇ Exportar Excel", buf_xl.getvalue(),
            "de_para_divergencias.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
