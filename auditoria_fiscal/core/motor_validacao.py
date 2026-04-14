"""
Motor de Validação Tributária de NFe.

Executa 12 validações (V01-V12) cruzando dados da NFe com regras tributárias
e retorna um DataFrame de inconsistências classificadas por severidade.

Severidades:
    CRÍTICO    — Impacto financeiro alto, possível autuação
    ALERTA     — Inconsistência relevante para análise
    INFORMATIVO — Divergência pequena ou questão de conformidade

Exemplo de uso:
    df_itens = extrair_itens_lote(["nfe_01_ok.xml", "nfe_02_aliquota_errada.xml"])
    df_result = validar_nfe(df_itens)
    print(df_result[df_result["severidade"] == "CRÍTICO"])
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent / "config"

# ── Carregamento de configurações ─────────────────────────────────────────────

def _carregar_json(nome_arquivo: str) -> dict:
    caminho = CONFIG_DIR / nome_arquivo
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config não encontrada: {caminho}")
        return {}


_ICMS_CONFIG: dict = {}
_CFOP_TABLE: dict = {}
_CST_ICMS: dict = {}
_CST_PIS_COFINS: dict = {}
_NCM_ALIQUOTAS: dict = {}


def _get_icms_config() -> dict:
    global _ICMS_CONFIG
    if not _ICMS_CONFIG:
        _ICMS_CONFIG = _carregar_json("aliquotas_icms.json")
    return _ICMS_CONFIG


def _get_cfop_table() -> dict:
    global _CFOP_TABLE
    if not _CFOP_TABLE:
        _CFOP_TABLE = _carregar_json("cfop_table.json")
    return _CFOP_TABLE


def _get_cst_icms() -> dict:
    global _CST_ICMS
    if not _CST_ICMS:
        _CST_ICMS = _carregar_json("cst_icms.json")
    return _CST_ICMS


def _get_cst_pis_cofins() -> dict:
    global _CST_PIS_COFINS
    if not _CST_PIS_COFINS:
        _CST_PIS_COFINS = _carregar_json("cst_pis_cofins.json")
    return _CST_PIS_COFINS


def _get_ncm_aliquotas() -> dict:
    global _NCM_ALIQUOTAS
    if not _NCM_ALIQUOTAS:
        _NCM_ALIQUOTAS = _carregar_json("ncm_aliquotas.json")
    return _NCM_ALIQUOTAS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _aliquota_icms_esperada(uf_emitente: str, uf_dest: str, tp_nf: str, id_dest: str) -> Optional[float]:
    """Retorna a alíquota ICMS esperada conforme CONFAZ."""
    cfg = _get_icms_config()
    if not cfg:
        return None

    # Operação interna
    if id_dest == "1":
        return cfg.get("internas", {}).get(uf_emitente)

    # Operação interestadual
    if id_dest == "2":
        chave = f"{uf_emitente}_{uf_dest}"
        tabela = cfg.get("interestaduais", {}).get("tabela", {})
        if chave in tabela:
            return tabela[chave]
        # Regra geral: Sul/SE → N/NE/CO/ES = 7%, demais = 12%
        origem_7 = cfg.get("interestaduais", {}).get("origem_7", [])
        destino_7 = cfg.get("interestaduais", {}).get("destino_7", [])
        if uf_emitente in origem_7 and uf_dest in destino_7:
            return 7.0
        return 12.0

    # Exterior (CFOP 3xxx/7xxx) — ICMS não incide nas exportações
    if id_dest == "3":
        return 0.0

    return None


def _nova_inconsistencia(
    ch_nfe: str, n_nf: str, n_item: str, arquivo: str,
    codigo: str, descricao: str,
    valor_declarado: str, valor_esperado: str,
    divergencia: float, severidade: str,
    emit_cnpj: str = "", emit_nome: str = ""
) -> dict:
    return {
        "chNFe": ch_nfe,
        "nNF": n_nf,
        "item": n_item,
        "arquivo": arquivo,
        "emit_CNPJ": emit_cnpj,
        "emit_xNome": emit_nome,
        "codigo_validacao": codigo,
        "descricao": descricao,
        "valor_declarado": valor_declarado,
        "valor_esperado": valor_esperado,
        "divergencia": divergencia,
        "severidade": severidade,
    }


# ── Validações ────────────────────────────────────────────────────────────────

def _v01_cfop_vs_tipo_operacao(row: pd.Series, inconsistencias: list) -> None:
    """V01 — CFOP deve ser compatível com o tipo da nota (entrada/saída)."""
    cfop = str(row.get("CFOP", "")).strip()
    tp_nf = str(row.get("tpNF", "")).strip()
    if not cfop or not tp_nf:
        return

    primeiro_digito = cfop[0] if cfop else ""
    # tpNF=0 (Entrada) → CFOP 1xxx/2xxx/3xxx
    # tpNF=1 (Saída)   → CFOP 5xxx/6xxx/7xxx
    cfop_entrada = primeiro_digito in ("1", "2", "3")
    cfop_saida = primeiro_digito in ("5", "6", "7")

    if tp_nf == "0" and not cfop_entrada:
        inconsistencias.append(_nova_inconsistencia(
            ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
            n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
            codigo="V01", descricao=f"CFOP {cfop} é de saída em nota de ENTRADA (tpNF=0)",
            valor_declarado=f"CFOP {cfop}", valor_esperado="CFOP iniciado em 1, 2 ou 3",
            divergencia=0.0, severidade="CRÍTICO",
            emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
        ))
    elif tp_nf == "1" and not cfop_saida:
        inconsistencias.append(_nova_inconsistencia(
            ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
            n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
            codigo="V01", descricao=f"CFOP {cfop} é de entrada em nota de SAÍDA (tpNF=1)",
            valor_declarado=f"CFOP {cfop}", valor_esperado="CFOP iniciado em 5, 6 ou 7",
            divergencia=0.0, severidade="CRÍTICO",
            emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
        ))


def _v02_cfop_vs_destino(row: pd.Series, inconsistencias: list) -> None:
    """V02 — CFOP deve ser compatível com idDest (interna/interestadual/exterior)."""
    cfop = str(row.get("CFOP", "")).strip()
    id_dest = str(row.get("idDest", "")).strip()
    tp_nf = str(row.get("tpNF", "")).strip()
    if not cfop or not id_dest:
        return

    primeiro_digito = cfop[0]

    mapa_entrada = {"1": "1", "2": "2", "3": "3"}  # CFOP → idDest esperado
    mapa_saida   = {"5": "1", "6": "2", "7": "3"}

    mapa = mapa_entrada if tp_nf == "0" else mapa_saida
    id_dest_esperado = mapa.get(primeiro_digito)

    if id_dest_esperado and id_dest != id_dest_esperado:
        labels = {"1": "Interna", "2": "Interestadual", "3": "Exterior"}
        inconsistencias.append(_nova_inconsistencia(
            ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
            n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
            codigo="V02",
            descricao=f"CFOP {cfop} indica operação {labels.get(id_dest_esperado,'?')} mas idDest={id_dest} ({labels.get(id_dest,'?')})",
            valor_declarado=f"idDest={id_dest} ({labels.get(id_dest,'?')})",
            valor_esperado=f"idDest={id_dest_esperado} ({labels.get(id_dest_esperado,'?')})",
            divergencia=0.0, severidade="CRÍTICO",
            emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
        ))


def _v03_aliquota_icms(row: pd.Series, inconsistencias: list) -> None:
    """V03 — Alíquota ICMS declarada vs esperada (CONFAZ)."""
    p_icms = float(row.get("icms_pICMS", 0) or 0)
    uf_emit = str(row.get("emit_UF", "")).strip()
    uf_dest = str(row.get("dest_UF", "")).strip()
    tp_nf = str(row.get("tpNF", "")).strip()
    id_dest = str(row.get("idDest", "")).strip()
    cst = str(row.get("icms_CST", "")).strip()
    csosn = str(row.get("icms_CSOSN", "")).strip()

    # Não validar CSTs sem tributação
    cst_sem_tributacao = {"40", "41", "50", "51", "60"}
    csosn_sem_tributacao = {"102", "103", "300", "400", "500"}

    if cst in cst_sem_tributacao or csosn in csosn_sem_tributacao:
        return
    if p_icms == 0.0:
        return

    esperada = _aliquota_icms_esperada(uf_emit, uf_dest, tp_nf, id_dest)
    if esperada is None:
        return

    diff = abs(p_icms - esperada)
    if diff <= 0.01:
        return

    severidade = "CRÍTICO" if diff > 1.0 else "ALERTA"
    inconsistencias.append(_nova_inconsistencia(
        ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
        n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
        codigo="V03",
        descricao=f"Alíquota ICMS declarada {p_icms}% difere da esperada {esperada}% para {uf_emit}→{uf_dest}",
        valor_declarado=f"{p_icms}%",
        valor_esperado=f"{esperada}%",
        divergencia=round(diff, 4), severidade=severidade,
        emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
    ))


def _v04_base_calculo_icms(row: pd.Series, inconsistencias: list) -> None:
    """V04 — Verifica se vBC do ICMS é compatível com vProd + vFrete - vDesc."""
    mod_bc = str(row.get("icms_modBC", "")).strip()
    if mod_bc == "3":  # Pauta — não valida automaticamente
        return

    v_bc_declarado = float(row.get("icms_vBC", 0) or 0)
    v_prod = float(row.get("vProd", 0) or 0)
    v_frete = float(row.get("vFrete", 0) or 0)
    v_desc = float(row.get("vDesc", 0) or 0)

    if v_bc_declarado == 0:
        return

    v_bc_esperado = v_prod + v_frete - v_desc
    diff = abs(v_bc_declarado - v_bc_esperado)

    if diff > 1.00:
        inconsistencias.append(_nova_inconsistencia(
            ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
            n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
            codigo="V04",
            descricao=f"Base de cálculo ICMS divergente. Declarado R$ {v_bc_declarado:.2f}, calculado R$ {v_bc_esperado:.2f}",
            valor_declarado=f"R$ {v_bc_declarado:.2f}",
            valor_esperado=f"R$ {v_bc_esperado:.2f}",
            divergencia=round(diff, 2), severidade="ALERTA",
            emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
        ))


def _v05_valor_icms(row: pd.Series, inconsistencias: list) -> None:
    """V05 — Valor do ICMS calculado vs declarado."""
    v_bc = float(row.get("icms_vBC", 0) or 0)
    p_icms = float(row.get("icms_pICMS", 0) or 0)
    v_icms_declarado = float(row.get("icms_vICMS", 0) or 0)

    if v_bc == 0 or p_icms == 0:
        return

    v_icms_calculado = round(v_bc * p_icms / 100, 2)
    diff = abs(v_icms_declarado - v_icms_calculado)

    if diff > 1.00:
        inconsistencias.append(_nova_inconsistencia(
            ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
            n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
            codigo="V05",
            descricao=f"Valor ICMS declarado R$ {v_icms_declarado:.2f} difere do calculado R$ {v_icms_calculado:.2f} (BC={v_bc:.2f} x {p_icms}%)",
            valor_declarado=f"R$ {v_icms_declarado:.2f}",
            valor_esperado=f"R$ {v_icms_calculado:.2f}",
            divergencia=round(diff, 2), severidade="CRÍTICO",
            emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
        ))


def _v06_cst_vs_regime(row: pd.Series, inconsistencias: list) -> None:
    """V06 — CST deve ser compatível com o CRT do emitente."""
    crt = str(row.get("emit_CRT", "")).strip()
    cst = str(row.get("icms_CST", "")).strip()
    csosn = str(row.get("icms_CSOSN", "")).strip()

    if crt == "1":  # Simples Nacional — deve usar CSOSN
        if cst and not csosn:
            inconsistencias.append(_nova_inconsistencia(
                ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
                n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
                codigo="V06",
                descricao=f"Emitente no Simples Nacional (CRT=1) usa CST {cst} em vez de CSOSN (1xx)",
                valor_declarado=f"CST {cst}",
                valor_esperado="CSOSN (101/102/201/202/203/300/400/500/900)",
                divergencia=0.0, severidade="CRÍTICO",
                emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
            ))
    elif crt in ("2", "3"):  # Regime Normal — deve usar CST
        if csosn and not cst:
            inconsistencias.append(_nova_inconsistencia(
                ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
                n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
                codigo="V06",
                descricao=f"Emitente no Regime Normal (CRT={crt}) usa CSOSN {csosn} em vez de CST",
                valor_declarado=f"CSOSN {csosn}",
                valor_esperado="CST (00/10/20/30/40/41/50/51/60/70/90)",
                divergencia=0.0, severidade="CRÍTICO",
                emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
            ))


def _v07_cfop_vs_cst_pis_cofins(row: pd.Series, inconsistencias: list) -> None:
    """V07 — Verifica compatibilidade entre CFOP e CST de PIS/COFINS."""
    cfop = str(row.get("CFOP", "")).strip()
    pis_cst = str(row.get("pis_CST", "")).strip()
    cfop_table = _get_cfop_table()

    if not cfop or not pis_cst or cfop not in cfop_table:
        return

    cfop_info = cfop_table[cfop]
    # CFOPs de revenda + CST 50 = possível crédito indevido
    cfop_revenda = cfop_info.get("operacao", "") in ("venda_mercadoria", "venda_producao")
    if cfop_revenda and pis_cst == "50":
        inconsistencias.append(_nova_inconsistencia(
            ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
            n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
            codigo="V07",
            descricao=f"CFOP {cfop} (saída/revenda) com CST PIS/COFINS 50 (entrada com crédito) — possível crédito indevido",
            valor_declarado=f"CST {pis_cst}",
            valor_esperado="CST compatível com saída (01/02/06/07/08/49)",
            divergencia=0.0, severidade="ALERTA",
            emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
        ))


def _v08_aliquota_pis_cofins(row: pd.Series, inconsistencias: list) -> None:
    """V08 — Alíquota PIS/COFINS vs regime tributário do emitente."""
    crt = str(row.get("emit_CRT", "")).strip()
    pis_cst = str(row.get("pis_CST", "")).strip()
    p_pis = float(row.get("pis_pPIS", 0) or 0)
    p_cofins = float(row.get("cofins_pCOFINS", 0) or 0)

    # Simples Nacional não destaca PIS/COFINS — CST 07/08/09 esperados
    if crt == "1":
        if pis_cst in ("01", "02") and (p_pis > 0 or p_cofins > 0):
            inconsistencias.append(_nova_inconsistencia(
                ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
                n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
                codigo="V08",
                descricao="Simples Nacional (CRT=1) não deve destacar PIS/COFINS com CST tributado",
                valor_declarado=f"PIS {p_pis}% / COFINS {p_cofins}%",
                valor_esperado="CST 07/08/09 sem destaque",
                divergencia=0.0, severidade="ALERTA",
                emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
            ))
        return

    # Regime Normal (CRT=2 ou 3)
    if pis_cst not in ("01", "02"):
        return  # CSTs não tributados — não valida alíquota

    # CRT=3 pressupõe Lucro Real (não-cumulativo): PIS 1,65% / COFINS 7,60%
    # CRT=2 pode ser cumulativo: PIS 0,65% / COFINS 3,00%
    if crt == "3":
        pis_esperado, cofins_esperado = 1.65, 7.60
    else:
        return  # CRT=2: ambos os regimes possíveis, não valida automaticamente

    diff_pis = abs(p_pis - pis_esperado)
    diff_cofins = abs(p_cofins - cofins_esperado)

    if diff_pis > 0.01:
        inconsistencias.append(_nova_inconsistencia(
            ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
            n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
            codigo="V08",
            descricao=f"Alíquota PIS {p_pis}% diverge do esperado {pis_esperado}% para Lucro Real (CRT=3)",
            valor_declarado=f"PIS {p_pis}%",
            valor_esperado=f"PIS {pis_esperado}%",
            divergencia=round(diff_pis, 4), severidade="ALERTA",
            emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
        ))
    if diff_cofins > 0.01:
        inconsistencias.append(_nova_inconsistencia(
            ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
            n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
            codigo="V08",
            descricao=f"Alíquota COFINS {p_cofins}% diverge do esperado {cofins_esperado}% para Lucro Real (CRT=3)",
            valor_declarado=f"COFINS {p_cofins}%",
            valor_esperado=f"COFINS {cofins_esperado}%",
            divergencia=round(diff_cofins, 4), severidade="ALERTA",
            emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
        ))


def _v09_ncm_vs_ipi(row: pd.Series, inconsistencias: list) -> None:
    """V09 — NCM vs alíquota IPI (TIPI)."""
    ncm = str(row.get("NCM", "")).strip()
    p_ipi = float(row.get("ipi_pIPI", 0) or 0)
    v_ipi = float(row.get("ipi_vIPI", 0) or 0)

    if not ncm or (p_ipi == 0 and v_ipi == 0):
        return

    ncm_cfg = _get_ncm_aliquotas().get("aliquotas", {})
    if ncm not in ncm_cfg:
        return

    ipi_esperado = float(ncm_cfg[ncm].get("ipi", 0))
    diff = abs(p_ipi - ipi_esperado)

    if diff > 0.01:
        inconsistencias.append(_nova_inconsistencia(
            ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
            n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
            codigo="V09",
            descricao=f"Alíquota IPI {p_ipi}% para NCM {ncm} difere da TIPI {ipi_esperado}%",
            valor_declarado=f"{p_ipi}%",
            valor_esperado=f"{ipi_esperado}%",
            divergencia=round(diff, 4), severidade="ALERTA",
            emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
        ))


def _v11_prazo_emissao(row: pd.Series, inconsistencias: list) -> None:
    """V11 — Nota fora do prazo (dhEmi vs dhSaiEnt > 24h)."""
    dh_emi_str = str(row.get("dhEmi", "")).strip()
    dh_sai_str = str(row.get("dhSaiEnt", "")).strip()

    if not dh_emi_str or not dh_sai_str:
        return

    try:
        fmt = "%Y-%m-%dT%H:%M:%S%z"
        dh_emi = datetime.fromisoformat(dh_emi_str)
        dh_sai = datetime.fromisoformat(dh_sai_str)
        diff_horas = abs((dh_sai - dh_emi).total_seconds()) / 3600

        if diff_horas > 24:
            inconsistencias.append(_nova_inconsistencia(
                ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
                n_item="—", arquivo=str(row.get("arquivo", "")),
                codigo="V11",
                descricao=f"Diferença entre emissão e saída/entrada é de {diff_horas:.1f}h (limite: 24h)",
                valor_declarado=f"dhEmi={dh_emi_str[:19]} / dhSaiEnt={dh_sai_str[:19]}",
                valor_esperado="Diferença <= 24h",
                divergencia=round(diff_horas, 1), severidade="INFORMATIVO",
                emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", ""))
            ))
    except Exception:
        pass


# ── Validações em nível de lote (não por item) ────────────────────────────────

def _v10_duplicidade_chave(df: pd.DataFrame, inconsistencias: list) -> None:
    """V10 — Chave de acesso duplicada no lote."""
    if "chNFe" not in df.columns:
        return
    # Obtém uma linha representativa por chNFe
    df_cab = df.drop_duplicates(subset="chNFe")
    duplicadas = df_cab[df_cab.duplicated(subset="chNFe", keep=False)]["chNFe"].unique()

    for ch in duplicadas:
        subset = df_cab[df_cab["chNFe"] == ch].iloc[0]
        inconsistencias.append(_nova_inconsistencia(
            ch_nfe=ch, n_nf=str(subset.get("nNF", "")),
            n_item="—", arquivo=str(subset.get("arquivo", "")),
            codigo="V10",
            descricao=f"Chave de acesso {ch} aparece duplicada no lote de XMLs",
            valor_declarado=f"chNFe: {ch}",
            valor_esperado="Chave única por nota",
            divergencia=0.0, severidade="CRÍTICO",
            emit_cnpj=str(subset.get("emit_CNPJ", "")), emit_nome=str(subset.get("emit_xNome", ""))
        ))


def _v12_soma_itens_vs_total(df: pd.DataFrame, inconsistencias: list) -> None:
    """V12 — Soma de vProd dos itens vs total declarado na nota."""
    if "chNFe" not in df.columns or "vProd" not in df.columns:
        return

    # Precisa de coluna tot_vProd no df (populada por parse_multiplos_xml)
    if "tot_vProd" not in df.columns:
        return

    df_ch = df.groupby("chNFe").agg(
        soma_itens=("vProd", "sum"),
        total_declarado=("tot_vProd", "first"),
        nNF=("nNF", "first"),
        arquivo=("arquivo", "first"),
        emit_CNPJ=("emit_CNPJ", "first"),
        emit_xNome=("emit_xNome", "first"),
    ).reset_index()

    for _, r in df_ch.iterrows():
        diff = abs(float(r["soma_itens"]) - float(r["total_declarado"]))
        if diff > 0.02:
            inconsistencias.append(_nova_inconsistencia(
                ch_nfe=str(r["chNFe"]), n_nf=str(r["nNF"]),
                n_item="—", arquivo=str(r["arquivo"]),
                codigo="V12",
                descricao=f"Soma dos itens R$ {r['soma_itens']:.2f} difere do total declarado R$ {r['total_declarado']:.2f}",
                valor_declarado=f"R$ {r['total_declarado']:.2f}",
                valor_esperado=f"R$ {r['soma_itens']:.2f}",
                divergencia=round(diff, 2), severidade="CRÍTICO",
                emit_cnpj=str(r["emit_CNPJ"]), emit_nome=str(r["emit_xNome"])
            ))


# ── Função principal ──────────────────────────────────────────────────────────

def validar_nfe(df_itens: pd.DataFrame) -> pd.DataFrame:
    """
    Executa todas as validações tributárias (V01–V12) no DataFrame de itens.

    Parâmetros:
        df_itens: DataFrame retornado por extrair_itens_lote() ou extrair_itens().

    Retorna:
        pd.DataFrame com colunas:
            chNFe, nNF, item, arquivo, emit_CNPJ, emit_xNome,
            codigo_validacao, descricao, valor_declarado, valor_esperado,
            divergencia, severidade

    Exemplo:
        df_itens = extrair_itens_lote(["nfe_01_ok.xml", "nfe_02_aliquota_errada.xml"])
        df_result = validar_nfe(df_itens)
        criticos = df_result[df_result["severidade"] == "CRÍTICO"]
    """
    if df_itens.empty:
        return pd.DataFrame()

    inconsistencias: list = []

    # Validações por item
    for _, row in df_itens.iterrows():
        _v01_cfop_vs_tipo_operacao(row, inconsistencias)
        _v02_cfop_vs_destino(row, inconsistencias)
        _v03_aliquota_icms(row, inconsistencias)
        _v04_base_calculo_icms(row, inconsistencias)
        _v05_valor_icms(row, inconsistencias)
        _v06_cst_vs_regime(row, inconsistencias)
        _v07_cfop_vs_cst_pis_cofins(row, inconsistencias)
        _v08_aliquota_pis_cofins(row, inconsistencias)
        _v09_ncm_vs_ipi(row, inconsistencias)
        _v11_prazo_emissao(row, inconsistencias)

    # Validações em nível de lote
    _v10_duplicidade_chave(df_itens, inconsistencias)
    _v12_soma_itens_vs_total(df_itens, inconsistencias)

    df_result = pd.DataFrame(inconsistencias)
    if not df_result.empty:
        ordem_severidade = {"CRÍTICO": 0, "ALERTA": 1, "INFORMATIVO": 2}
        df_result["_ord"] = df_result["severidade"].map(ordem_severidade)
        df_result = df_result.sort_values(["_ord", "chNFe", "nNF"]).drop(columns="_ord")
        df_result = df_result.reset_index(drop=True)

    logger.info(f"Validação concluída: {len(inconsistencias)} inconsistência(s) encontrada(s).")
    return df_result
