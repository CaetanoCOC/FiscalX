"""Página 1 — Upload de NFe"""

import io, zipfile, tempfile, os
import streamlit as st
import pandas as pd

from core.parser_nfe import parse_xml, extrair_itens
from core.motor_validacao import validar_nfe
from core.detector_anomalias import detectar_anomalias
from utils.formatters import fmt_moeda, fmt_data, fmt_cnpj
from utils.constants import (
    COR_TEXTO, COR_TEXTO_SEC, COR_CIANO, COR_BORDA,
    COR_CARD, COR_CARD_ALT, COR_CRITICO, COR_ALERTA, COR_INFORMATIVO, COR_VERDE,
)

st.markdown("<h1>📂 Upload de NFe</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='color:{COR_TEXTO_SEC}; margin-top:-8px;'>Carregue XMLs de Notas Fiscais Eletrônicas para iniciar a auditoria</p>", unsafe_allow_html=True)
st.divider()

col_up, col_info = st.columns([2, 1])

with col_up:
    with st.container(border=True):
        st.markdown(f"<p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:10px;'>Selecione XMLs ou um arquivo .zip com múltiplos XMLs</p>", unsafe_allow_html=True)
        arquivos = st.file_uploader(
            "upload", type=["xml", "zip"],
            accept_multiple_files=True, label_visibility="collapsed",
        )

with col_info:
    st.markdown(f"""
    <div class='fiscal-card'>
        <p style='font-weight:600; color:{COR_TEXTO}; margin-bottom:10px;'>Formatos aceitos</p>
        <div style='color:{COR_TEXTO_SEC}; font-size:0.88em; line-height:2em;'>
            <span style='color:{COR_CIANO};'>✓</span> XML de NFe (layout 4.0)<br>
            <span style='color:{COR_CIANO};'>✓</span> Múltiplos XMLs simultâneos<br>
            <span style='color:{COR_CIANO};'>✓</span> Arquivo .zip com XMLs<br>
            <span style='color:{COR_TEXTO_SEC};'>ℹ</span> Dados ficam apenas na sessão
        </div>
    </div>
    """, unsafe_allow_html=True)

if not arquivos:
    st.info("Aguardando upload de arquivos...")
    st.stop()

@st.cache_data(show_spinner=False)
def processar_uploads(arquivos_bytes: list) -> tuple:
    notas_raw, itens_raw, erros = [], [], []
    with tempfile.TemporaryDirectory() as tmpdir:
        for nome, conteudo in arquivos_bytes:
            if nome.endswith(".zip"):
                try:
                    with zipfile.ZipFile(io.BytesIO(conteudo)) as z:
                        for membro in z.namelist():
                            if membro.lower().endswith(".xml"):
                                dados = z.read(membro)
                                tmp_path = os.path.join(tmpdir, os.path.basename(membro))
                                with open(tmp_path, "wb") as f: f.write(dados)
                                nfe = parse_xml(tmp_path)
                                if nfe.get("status") == "ok":
                                    notas_raw.append(nfe); itens_raw.append(extrair_itens(nfe))
                                else: erros.append(f"{membro}: {nfe.get('erro')}")
                except Exception as e: erros.append(f"{nome}: {e}")
            else:
                tmp_path = os.path.join(tmpdir, nome)
                with open(tmp_path, "wb") as f: f.write(conteudo)
                nfe = parse_xml(tmp_path)
                if nfe.get("status") == "ok":
                    notas_raw.append(nfe); itens_raw.append(extrair_itens(nfe))
                else: erros.append(f"{nome}: {nfe.get('erro')}")

    df_notas = pd.DataFrame([{
        "chNFe": n["cabecalho"]["chNFe"], "nNF": n["cabecalho"]["nNF"],
        "serie": n["cabecalho"]["serie"], "dhEmi": n["cabecalho"]["dhEmi"],
        "tpNF": n["cabecalho"]["tpNF"],
        "emit_CNPJ": n["emitente"]["CNPJ"], "emit_xNome": n["emitente"]["xNome"],
        "emit_UF": n["emitente"]["UF"], "emit_CRT": n["emitente"]["CRT"],
        "dest_xNome": n["destinatario"]["xNome"], "dest_UF": n["destinatario"]["UF"],
        "tot_vNF": n["totais"]["vNF"], "tot_vICMS": n["totais"]["vICMS"],
        "tot_vPIS": n["totais"]["vPIS"], "tot_vCOFINS": n["totais"]["vCOFINS"],
        "arquivo": n["cabecalho"]["arquivo"],
    } for n in notas_raw]) if notas_raw else pd.DataFrame()

    df_itens = pd.concat(itens_raw, ignore_index=True) if itens_raw else pd.DataFrame()

    if not df_itens.empty and not df_notas.empty:
        df_prod = pd.DataFrame([{"chNFe": n["cabecalho"]["chNFe"], "tot_vProd": n["totais"]["vProd"]} for n in notas_raw])
        df_itens = df_itens.merge(df_prod, on="chNFe", how="left")

    return df_notas, df_itens, erros

arquivos_bytes = [(a.name, a.read()) for a in arquivos]
with st.spinner("Lendo arquivos..."):
    df_notas, df_itens, erros = processar_uploads(arquivos_bytes)

for e in erros: st.error(f"Erro: {e}")

if not df_notas.empty:
    st.markdown(f"<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Notas carregadas", len(df_notas))
    col2.metric("Valor total", fmt_moeda(df_notas["tot_vNF"].sum()))
    col3.metric("Emitentes distintos", df_notas["emit_CNPJ"].nunique())

    st.markdown("<br>", unsafe_allow_html=True)

    # Filtros
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        tp_filtro = st.selectbox("Tipo", ["Todos", "Entrada (0)", "Saída (1)"])
    with col_f2:
        uf_opcoes = ["Todos"] + sorted(df_notas["emit_UF"].dropna().unique().tolist())
        uf_filtro = st.selectbox("UF Emitente", uf_opcoes)
    with col_f3:
        emit_opcoes = ["Todos"] + sorted(df_notas["emit_xNome"].dropna().unique().tolist())
        emit_filtro = st.selectbox("Emitente", emit_opcoes)

    df_exib = df_notas.copy()
    if tp_filtro != "Todos":
        df_exib = df_exib[df_exib["tpNF"] == ("0" if "Entrada" in tp_filtro else "1")]
    if uf_filtro != "Todos":
        df_exib = df_exib[df_exib["emit_UF"] == uf_filtro]
    if emit_filtro != "Todos":
        df_exib = df_exib[df_exib["emit_xNome"] == emit_filtro]

    linhas_nf = ""
    for i, row in df_exib.iterrows():
        tipo     = {"0": "Entrada", "1": "Saída"}.get(str(row.get("tpNF","")), "—")
        cor_tipo = COR_CIANO if tipo == "Entrada" else COR_VERDE
        bg       = COR_CARD_ALT if i % 2 == 0 else COR_CARD
        linhas_nf += f"""
        <tr style='background:{bg};'>
            <td style='padding:9px 12px; color:{COR_TEXTO}; font-weight:600;'>{row.get("nNF","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO_SEC};'>{row.get("serie","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO_SEC};'>{fmt_data(row.get("dhEmi",""))}</td>
            <td style='padding:9px 12px; text-align:center;'><span style='background:{cor_tipo}22; color:{cor_tipo}; padding:2px 8px; border-radius:4px; font-size:0.78em; font-weight:700;'>{tipo}</span></td>
            <td style='padding:9px 12px; color:{COR_TEXTO};'>{row.get("emit_xNome","")}</td>
            <td style='padding:9px 12px; color:{COR_CIANO}; font-weight:600; text-align:center;'>{row.get("emit_UF","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO_SEC};'>{row.get("dest_xNome","")}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO_SEC}; text-align:center;'>{row.get("dest_UF","")}</td>
            <td style='padding:9px 12px; color:{COR_VERDE}; font-weight:700; text-align:right;'>{fmt_moeda(row.get("tot_vNF",0))}</td>
            <td style='padding:9px 12px; color:{COR_TEXTO_SEC}; font-size:0.78em;'>{row.get("arquivo","")}</td>
        </tr>"""

    st.markdown(f"""
    <div class='fiscal-card' style='padding:0; overflow:auto; max-height:320px;'>
        <table style='width:100%; border-collapse:collapse; font-size:0.85em;'>
            <thead style='position:sticky; top:0; z-index:1;'>
                <tr style='background:{COR_CARD}; border-bottom:2px solid {COR_BORDA};'>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>NF</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Série</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Emissão</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center;'>Tipo</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Emitente</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center;'>UF Emit</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Destinatário</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:center;'>UF Dest</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:right;'>Valor NF</th>
                    <th style='padding:10px 12px; color:{COR_TEXTO_SEC}; font-size:0.72em; text-transform:uppercase; letter-spacing:0.06em; text-align:left;'>Arquivo</th>
                </tr>
            </thead>
            <tbody>{linhas_nf}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn, col_txt = st.columns([1, 2])
    with col_btn:
        iniciar = st.button("🔍 Iniciar Auditoria", use_container_width=True)
    with col_txt:
        st.markdown(f"<p style='color:{COR_TEXTO_SEC}; padding-top:10px;'>12 validações tributárias + 7 detectores de anomalias em {len(df_itens)} itens.</p>", unsafe_allow_html=True)

    if iniciar:
        prog = st.progress(0, text="Iniciando auditoria...")
        prog.progress(20, text="Executando validações tributárias...")
        df_validacoes = validar_nfe(df_itens)
        prog.progress(65, text="Detectando anomalias...")
        df_anomalias  = detectar_anomalias(df_itens)
        prog.progress(100, text="Concluído!")
        prog.empty()

        st.session_state["df_itens"]      = df_itens
        st.session_state["df_notas"]      = df_notas
        st.session_state["df_validacoes"] = df_validacoes
        st.session_state["df_anomalias"]  = df_anomalias

        criticos     = len(df_validacoes[df_validacoes["severidade"] == "CRÍTICO"])    if not df_validacoes.empty else 0
        alertas      = len(df_validacoes[df_validacoes["severidade"] == "ALERTA"])     if not df_validacoes.empty else 0
        informativos = len(df_validacoes[df_validacoes["severidade"] == "INFORMATIVO"])if not df_validacoes.empty else 0

        st.success(f"Auditoria concluída — {len(df_validacoes)} inconsistências encontradas.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Críticos",     criticos)
        c2.metric("Alertas",      alertas)
        c3.metric("Informativos", informativos)

    elif "df_validacoes" in st.session_state:
        st.success("Auditoria já executada. Navegue para **Auditoria Detalhada** para ver os resultados.")
