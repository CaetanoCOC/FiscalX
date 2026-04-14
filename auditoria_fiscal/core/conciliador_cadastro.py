"""
Conciliador de Cadastro — Módulo DE PARA.

Cruza os dados extraídos das NFes com tabelas de mapeamento fornecidas
pelo usuário (DE PARA de Fornecedores e DE PARA de Produtos), detectando
divergências de cadastro e escrituração.

Validações produzidas:
    V13 — Fornecedor não mapeado no DE PARA (CNPJ ausente do cadastro interno)
    V14 — NCM do item diverge do NCM esperado no cadastro interno
    V15 — CFOP do item diverge do CFOP esperado no cadastro interno

Exemplo de uso:
    df_forn = pd.read_csv("de_para_fornecedores.csv")
    df_prod = pd.read_csv("de_para_produtos.csv")
    df_result = conciliar(df_notas, df_itens, df_forn, df_prod)
"""

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ── Templates ─────────────────────────────────────────────────────────────────

def gerar_template_fornecedores() -> pd.DataFrame:
    """
    Retorna DataFrame-modelo do DE PARA de fornecedores para download.

    Colunas:
        cnpj_fornecedor  — CNPJ conforme consta na NFe (com ou sem máscara)
        cod_interno      — Código do fornecedor no ERP/sistema interno
        nome_interno     — Nome do fornecedor no cadastro interno
        ativo            — S/N — se o fornecedor está ativo no cadastro
    """
    return pd.DataFrame([
        {
            "cnpj_fornecedor": "12.345.678/0001-90",
            "cod_interno":     "FORN-001",
            "nome_interno":    "Distribuidora Exemplo LTDA",
            "ativo":           "S",
        },
        {
            "cnpj_fornecedor": "98.765.432/0001-10",
            "cod_interno":     "FORN-002",
            "nome_interno":    "Indústria Modelo S.A.",
            "ativo":           "S",
        },
    ])


def gerar_template_produtos() -> pd.DataFrame:
    """
    Retorna DataFrame-modelo do DE PARA de produtos para download.

    Colunas:
        cnpj_fornecedor   — CNPJ do fornecedor (vincula o produto ao fornecedor)
        cProd             — Código do produto conforme consta na NFe
        cod_interno       — Código interno do produto no ERP
        desc_interna      — Descrição interna do produto
        ncm_esperado      — NCM correto conforme cadastro tributário interno
        cfop_esperado     — CFOP correto para este produto/fornecedor
    """
    return pd.DataFrame([
        {
            "cnpj_fornecedor": "12.345.678/0001-90",
            "cProd":           "PROD-ABC",
            "cod_interno":     "INT-0001",
            "desc_interna":    "Produto Exemplo A",
            "ncm_esperado":    "8471.30.12",
            "cfop_esperado":   "1102",
        },
        {
            "cnpj_fornecedor": "98.765.432/0001-10",
            "cProd":           "MAT-XYZ",
            "cod_interno":     "INT-0002",
            "desc_interna":    "Material Exemplo B",
            "ncm_esperado":    "3926.90.90",
            "cfop_esperado":   "1556",
        },
    ])


# ── Normalização ──────────────────────────────────────────────────────────────

def _normalizar_cnpj(cnpj: str) -> str:
    """Remove máscara do CNPJ, retornando apenas os 14 dígitos."""
    if not isinstance(cnpj, str):
        return ""
    return "".join(c for c in cnpj if c.isdigit())


def _normalizar_ncm(ncm: str) -> str:
    """Remove pontos e espaços do NCM."""
    if not isinstance(ncm, str):
        return ""
    return ncm.replace(".", "").replace(" ", "").strip()


# ── Validações ────────────────────────────────────────────────────────────────

def validar_fornecedores(
    df_notas: pd.DataFrame,
    df_de_para: pd.DataFrame,
) -> pd.DataFrame:
    """
    V13 — Cruza CNPJs das NFes com o DE PARA de fornecedores.

    Retorna DataFrame de divergências com colunas compatíveis com o
    padrão do motor_validacao.py.

    Parâmetros:
        df_notas   — DataFrame de notas (saída de parse_multiplos_xml)
        df_de_para — DataFrame do DE PARA de fornecedores (template acima)
    """
    if df_notas.empty or df_de_para.empty:
        return pd.DataFrame()

    resultados = []

    # Normaliza CNPJs do DE PARA para lookup rápido
    mapa = {
        _normalizar_cnpj(row["cnpj_fornecedor"]): row
        for _, row in df_de_para.iterrows()
        if pd.notna(row.get("cnpj_fornecedor"))
    }

    for _, nota in df_notas.iterrows():
        cnpj_nfe = _normalizar_cnpj(str(nota.get("emit_CNPJ", "")))
        if not cnpj_nfe:
            continue

        if cnpj_nfe not in mapa:
            resultados.append({
                "chNFe":             nota.get("chNFe", ""),
                "nNF":               nota.get("nNF", ""),
                "item":              "—",
                "emit_xNome":        nota.get("emit_xNome", ""),
                "codigo_validacao":  "V13",
                "descricao":         (
                    f"Fornecedor '{nota.get('emit_xNome','')}' "
                    f"(CNPJ {nota.get('emit_CNPJ','')}) não encontrado no DE PARA. "
                    "Verifique o cadastro interno."
                ),
                "valor_declarado":   nota.get("emit_CNPJ", ""),
                "valor_esperado":    "Não mapeado",
                "divergencia":       0.0,
                "severidade":        "ALERTA",
            })
        else:
            cadastro = mapa[cnpj_nfe]
            if str(cadastro.get("ativo", "S")).upper() == "N":
                resultados.append({
                    "chNFe":             nota.get("chNFe", ""),
                    "nNF":               nota.get("nNF", ""),
                    "item":              "—",
                    "emit_xNome":        nota.get("emit_xNome", ""),
                    "codigo_validacao":  "V13",
                    "descricao":         (
                        f"Fornecedor '{nota.get('emit_xNome','')}' está marcado como "
                        f"INATIVO no cadastro interno (cód. {cadastro.get('cod_interno','')})."
                    ),
                    "valor_declarado":   nota.get("emit_CNPJ", ""),
                    "valor_esperado":    f"Inativo: {cadastro.get('cod_interno','')}",
                    "divergencia":       0.0,
                    "severidade":        "CRÍTICO",
                })

    return pd.DataFrame(resultados) if resultados else pd.DataFrame()


def validar_produtos(
    df_itens: pd.DataFrame,
    df_de_para: pd.DataFrame,
) -> pd.DataFrame:
    """
    V14/V15 — Cruza produtos das NFes com o DE PARA de produtos.

    V14 — NCM declarado na NFe diverge do NCM esperado no cadastro.
    V15 — CFOP declarado na NFe diverge do CFOP esperado no cadastro.

    Parâmetros:
        df_itens   — DataFrame de itens (saída de extrair_itens_lote)
        df_de_para — DataFrame do DE PARA de produtos (template acima)
    """
    if df_itens.empty or df_de_para.empty:
        return pd.DataFrame()

    resultados = []

    # Monta índice composto (cnpj_normalizado, cProd) → linha do DE PARA
    mapa = {}
    for _, row in df_de_para.iterrows():
        cnpj = _normalizar_cnpj(str(row.get("cnpj_fornecedor", "")))
        cprod = str(row.get("cProd", "")).strip()
        if cnpj and cprod:
            mapa[(cnpj, cprod)] = row

    for _, item in df_itens.iterrows():
        cnpj_item  = _normalizar_cnpj(str(item.get("emit_CNPJ", "")))
        cprod_item = str(item.get("cProd", "")).strip()
        chave      = (cnpj_item, cprod_item)

        if chave not in mapa:
            continue  # produto não mapeado — não é erro, apenas não há DE PARA para ele

        cadastro = mapa[chave]

        # V14 — NCM
        ncm_nfe      = _normalizar_ncm(str(item.get("NCM", "")))
        ncm_esperado = _normalizar_ncm(str(cadastro.get("ncm_esperado", "")))
        if ncm_esperado and ncm_nfe != ncm_esperado:
            resultados.append({
                "chNFe":            item.get("chNFe", ""),
                "nNF":              item.get("nNF", ""),
                "item":             item.get("nItem", ""),
                "emit_xNome":       item.get("emit_xNome", ""),
                "codigo_validacao": "V14",
                "descricao":        (
                    f"NCM do produto '{item.get('xProd','')}' (cód. {cprod_item}) "
                    f"diverge do cadastro interno. "
                    f"Risco de classificação fiscal incorreta."
                ),
                "valor_declarado":  item.get("NCM", ""),
                "valor_esperado":   cadastro.get("ncm_esperado", ""),
                "divergencia":      0.0,
                "severidade":       "CRÍTICO",
            })

        # V15 — CFOP
        cfop_nfe      = str(item.get("CFOP", "")).strip()
        cfop_esperado = str(cadastro.get("cfop_esperado", "")).strip()
        if cfop_esperado and cfop_nfe != cfop_esperado:
            resultados.append({
                "chNFe":            item.get("chNFe", ""),
                "nNF":              item.get("nNF", ""),
                "item":             item.get("nItem", ""),
                "emit_xNome":       item.get("emit_xNome", ""),
                "codigo_validacao": "V15",
                "descricao":        (
                    f"CFOP do produto '{item.get('xProd','')}' (cód. {cprod_item}) "
                    f"diverge do cadastro interno — impacto direto na apuração de créditos/débitos."
                ),
                "valor_declarado":  cfop_nfe,
                "valor_esperado":   cfop_esperado,
                "divergencia":      0.0,
                "severidade":       "CRÍTICO",
            })

    return pd.DataFrame(resultados) if resultados else pd.DataFrame()


# ── Ponto de entrada unificado ────────────────────────────────────────────────

def conciliar(
    df_notas: pd.DataFrame,
    df_itens: pd.DataFrame,
    df_de_para_forn: Optional[pd.DataFrame] = None,
    df_de_para_prod: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Executa todas as conciliações DE PARA disponíveis e retorna um
    DataFrame consolidado de divergências no padrão do motor_validacao.

    Parâmetros:
        df_notas         — DataFrame de notas carregadas
        df_itens         — DataFrame de itens das notas
        df_de_para_forn  — DE PARA de fornecedores (opcional)
        df_de_para_prod  — DE PARA de produtos (opcional)

    Retorna:
        pd.DataFrame com colunas:
            chNFe, nNF, item, emit_xNome, codigo_validacao,
            descricao, valor_declarado, valor_esperado, divergencia, severidade
    """
    partes = []

    if df_de_para_forn is not None and not df_de_para_forn.empty:
        partes.append(validar_fornecedores(df_notas, df_de_para_forn))

    if df_de_para_prod is not None and not df_de_para_prod.empty:
        partes.append(validar_produtos(df_itens, df_de_para_prod))

    partes = [p for p in partes if not p.empty]
    if not partes:
        return pd.DataFrame()

    return pd.concat(partes, ignore_index=True)
