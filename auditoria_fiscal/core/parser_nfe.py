"""
Parser de Notas Fiscais Eletrônicas (NFe) — layout 4.0.

Extrai cabeçalho, emitente, destinatário, itens (ICMS, PIS/COFINS, IPI)
e totais de XMLs de NFe, retornando estruturas padronizadas.

Exemplo de uso:
    nfe = parse_xml("tests/sample_nfe/nfe_01_ok.xml")
    df_itens = extrair_itens(nfe)
    df_lote = parse_multiplos_xml(["nfe_01_ok.xml", "nfe_02_aliquota_errada.xml"])
"""

import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

import pandas as pd
from lxml import etree

logger = logging.getLogger(__name__)

# Namespace padrão NFe 4.0
NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


def _txt(element, xpath: str, ns: dict = NS, default: str = "") -> str:
    """Extrai texto de um elemento via xpath, retornando default se não encontrado."""
    result = element.xpath(xpath, namespaces=ns)
    if result:
        return result[0].strip() if isinstance(result[0], str) else result[0].text or default
    return default


def _find(element, xpath: str, ns: dict = NS):
    """Retorna primeiro elemento encontrado ou None."""
    result = element.xpath(xpath, namespaces=ns)
    return result[0] if result else None


def _float(value: str, default: float = 0.0) -> float:
    """Converte string para float com segurança."""
    try:
        return float(value) if value else default
    except (ValueError, TypeError):
        return default


def parse_xml(caminho_arquivo: str) -> dict:
    """
    Lê e parseia um XML de NFe (layout 4.0) retornando dicionário padronizado.

    Parâmetros:
        caminho_arquivo: Caminho absoluto ou relativo ao arquivo XML.

    Retorna:
        dict com chaves: cabecalho, emitente, destinatario, itens, totais, status

    Exemplo:
        nfe = parse_xml("tests/sample_nfe/nfe_01_ok.xml")
        print(nfe["cabecalho"]["nNF"])  # "1"
    """
    caminho = Path(caminho_arquivo)

    if not caminho.exists():
        return {"erro": f"Arquivo não encontrado: {caminho_arquivo}", "status": "erro"}

    try:
        tree = etree.parse(str(caminho))
        root = tree.getroot()
    except etree.XMLSyntaxError as e:
        logger.error(f"XML malformado: {caminho_arquivo} — {e}")
        return {"erro": f"XML malformado: {e}", "arquivo": caminho.name, "status": "erro"}

    # Remove namespace para facilitar xpath se necessário
    # Detecta elemento raiz (pode ser nfeProc ou NFe direto)
    infNFe = _find(root, ".//nfe:infNFe")
    if infNFe is None:
        return {"erro": "Elemento infNFe não encontrado", "arquivo": caminho.name, "status": "erro"}

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    ide = _find(infNFe, "nfe:ide")
    ch_nfe = infNFe.get("Id", "").replace("NFe", "")

    cabecalho = {
        "chNFe":    ch_nfe,
        "nNF":      _txt(ide, "nfe:nNF/text()"),
        "serie":    _txt(ide, "nfe:serie/text()"),
        "dhEmi":    _txt(ide, "nfe:dhEmi/text()"),
        "dhSaiEnt": _txt(ide, "nfe:dhSaiEnt/text()"),
        "natOp":    _txt(ide, "nfe:natOp/text()"),
        "tpNF":     _txt(ide, "nfe:tpNF/text()"),      # 0=Entrada, 1=Saída
        "idDest":   _txt(ide, "nfe:idDest/text()"),    # 1=Interna, 2=Interestadual, 3=Exterior
        "cMunFG":   _txt(ide, "nfe:cMunFG/text()"),
        "mod":      _txt(ide, "nfe:mod/text()"),
        "arquivo":  caminho.name,
    }

    # ── Emitente ───────────────────────────────────────────────────────────────
    emit = _find(infNFe, "nfe:emit")
    ender_emit = _find(emit, "nfe:enderEmit") if emit is not None else None

    emitente = {
        "CNPJ":   _txt(emit, "nfe:CNPJ/text()") if emit is not None else "",
        "CPF":    _txt(emit, "nfe:CPF/text()") if emit is not None else "",
        "xNome":  _txt(emit, "nfe:xNome/text()") if emit is not None else "",
        "UF":     _txt(ender_emit, "nfe:UF/text()") if ender_emit is not None else "",
        "cMun":   _txt(ender_emit, "nfe:cMun/text()") if ender_emit is not None else "",
        "xMun":   _txt(ender_emit, "nfe:xMun/text()") if ender_emit is not None else "",
        "CRT":    _txt(emit, "nfe:CRT/text()") if emit is not None else "",  # 1=Simples, 2=SN Excesso, 3=Normal
    }

    # ── Destinatário ───────────────────────────────────────────────────────────
    dest = _find(infNFe, "nfe:dest")
    ender_dest = _find(dest, "nfe:enderDest") if dest is not None else None

    destinatario = {
        "CNPJ":      _txt(dest, "nfe:CNPJ/text()") if dest is not None else "",
        "CPF":       _txt(dest, "nfe:CPF/text()") if dest is not None else "",
        "xNome":     _txt(dest, "nfe:xNome/text()") if dest is not None else "",
        "UF":        _txt(ender_dest, "nfe:UF/text()") if ender_dest is not None else "",
        "cMun":      _txt(ender_dest, "nfe:cMun/text()") if ender_dest is not None else "",
        "xMun":      _txt(ender_dest, "nfe:xMun/text()") if ender_dest is not None else "",
        "indIEDest": _txt(dest, "nfe:indIEDest/text()") if dest is not None else "",
    }

    # ── Itens ──────────────────────────────────────────────────────────────────
    itens = []
    for det in infNFe.xpath("nfe:det", namespaces=NS):
        n_item = det.get("nItem", "")
        prod = _find(det, "nfe:prod")
        imposto = _find(det, "nfe:imposto")

        item: dict = {
            "nItem":  n_item,
            "cProd":  _txt(prod, "nfe:cProd/text()"),
            "xProd":  _txt(prod, "nfe:xProd/text()"),
            "NCM":    _txt(prod, "nfe:NCM/text()"),
            "CFOP":   _txt(prod, "nfe:CFOP/text()"),
            "uCom":   _txt(prod, "nfe:uCom/text()"),
            "qCom":   _float(_txt(prod, "nfe:qCom/text()")),
            "vUnCom": _float(_txt(prod, "nfe:vUnCom/text()")),
            "vProd":  _float(_txt(prod, "nfe:vProd/text()")),
            "vDesc":  _float(_txt(prod, "nfe:vDesc/text()")),
            "vFrete": _float(_txt(prod, "nfe:vFrete/text()")),
        }

        # ICMS — suporta os grupos mais comuns (00, 10, 20, 30, 40, 41, 50, 51, 60, 70, 90, CSOSN)
        icms_grupos = [
            "ICMS00", "ICMS10", "ICMS20", "ICMS30", "ICMS40",
            "ICMS41", "ICMS50", "ICMS51", "ICMS60", "ICMS70", "ICMS90",
            "ICMSSN101", "ICMSSN102", "ICMSSN201", "ICMSSN202",
            "ICMSSN500", "ICMSSN900",
        ]
        icms_node = None
        for grupo in icms_grupos:
            icms_node = _find(imposto, f"nfe:ICMS/nfe:{grupo}") if imposto is not None else None
            if icms_node is not None:
                break

        item.update({
            "icms_orig":    _txt(icms_node, "nfe:orig/text()") if icms_node is not None else "",
            "icms_CST":     _txt(icms_node, "nfe:CST/text()") if icms_node is not None else "",
            "icms_CSOSN":   _txt(icms_node, "nfe:CSOSN/text()") if icms_node is not None else "",
            "icms_modBC":   _txt(icms_node, "nfe:modBC/text()") if icms_node is not None else "",
            "icms_vBC":     _float(_txt(icms_node, "nfe:vBC/text()")) if icms_node is not None else 0.0,
            "icms_pICMS":   _float(_txt(icms_node, "nfe:pICMS/text()")) if icms_node is not None else 0.0,
            "icms_vICMS":   _float(_txt(icms_node, "nfe:vICMS/text()")) if icms_node is not None else 0.0,
            "icms_pRedBC":  _float(_txt(icms_node, "nfe:pRedBC/text()")) if icms_node is not None else 0.0,
            "icms_vICMSST": _float(_txt(icms_node, "nfe:vICMSST/text()")) if icms_node is not None else 0.0,
            "icms_vBCST":   _float(_txt(icms_node, "nfe:vBCST/text()")) if icms_node is not None else 0.0,
        })

        # PIS
        pis_node = None
        for grupo_pis in ["PISAliq", "PISQtde", "PISNT", "PISOutr"]:
            pis_node = _find(imposto, f"nfe:PIS/nfe:{grupo_pis}") if imposto is not None else None
            if pis_node is not None:
                break

        item.update({
            "pis_CST":  _txt(pis_node, "nfe:CST/text()") if pis_node is not None else "",
            "pis_vBC":  _float(_txt(pis_node, "nfe:vBC/text()")) if pis_node is not None else 0.0,
            "pis_pPIS": _float(_txt(pis_node, "nfe:pPIS/text()")) if pis_node is not None else 0.0,
            "pis_vPIS": _float(_txt(pis_node, "nfe:vPIS/text()")) if pis_node is not None else 0.0,
        })

        # COFINS
        cofins_node = None
        for grupo_cofins in ["COFINSAliq", "COFINSQtde", "COFINSNT", "COFINSOutr"]:
            cofins_node = _find(imposto, f"nfe:COFINS/nfe:{grupo_cofins}") if imposto is not None else None
            if cofins_node is not None:
                break

        item.update({
            "cofins_CST":     _txt(cofins_node, "nfe:CST/text()") if cofins_node is not None else "",
            "cofins_vBC":     _float(_txt(cofins_node, "nfe:vBC/text()")) if cofins_node is not None else 0.0,
            "cofins_pCOFINS": _float(_txt(cofins_node, "nfe:pCOFINS/text()")) if cofins_node is not None else 0.0,
            "cofins_vCOFINS": _float(_txt(cofins_node, "nfe:vCOFINS/text()")) if cofins_node is not None else 0.0,
        })

        # IPI (opcional)
        ipi_node = _find(imposto, "nfe:IPI/nfe:IPITrib") if imposto is not None else None
        item.update({
            "ipi_CST":  _txt(ipi_node, "nfe:CST/text()") if ipi_node is not None else "",
            "ipi_vBC":  _float(_txt(ipi_node, "nfe:vBC/text()")) if ipi_node is not None else 0.0,
            "ipi_pIPI": _float(_txt(ipi_node, "nfe:pIPI/text()")) if ipi_node is not None else 0.0,
            "ipi_vIPI": _float(_txt(ipi_node, "nfe:vIPI/text()")) if ipi_node is not None else 0.0,
        })

        itens.append(item)

    # ── Totais ─────────────────────────────────────────────────────────────────
    icms_tot = _find(infNFe, ".//nfe:ICMSTot")
    totais = {
        "vBC":       _float(_txt(icms_tot, "nfe:vBC/text()")) if icms_tot is not None else 0.0,
        "vICMS":     _float(_txt(icms_tot, "nfe:vICMS/text()")) if icms_tot is not None else 0.0,
        "vICMSDeson":_float(_txt(icms_tot, "nfe:vICMSDeson/text()")) if icms_tot is not None else 0.0,
        "vFCPST":   _float(_txt(icms_tot, "nfe:vFCPST/text()")) if icms_tot is not None else 0.0,
        "vST":       _float(_txt(icms_tot, "nfe:vST/text()")) if icms_tot is not None else 0.0,
        "vProd":     _float(_txt(icms_tot, "nfe:vProd/text()")) if icms_tot is not None else 0.0,
        "vFrete":    _float(_txt(icms_tot, "nfe:vFrete/text()")) if icms_tot is not None else 0.0,
        "vSeg":      _float(_txt(icms_tot, "nfe:vSeg/text()")) if icms_tot is not None else 0.0,
        "vDesc":     _float(_txt(icms_tot, "nfe:vDesc/text()")) if icms_tot is not None else 0.0,
        "vII":       _float(_txt(icms_tot, "nfe:vII/text()")) if icms_tot is not None else 0.0,
        "vIPI":      _float(_txt(icms_tot, "nfe:vIPI/text()")) if icms_tot is not None else 0.0,
        "vPIS":      _float(_txt(icms_tot, "nfe:vPIS/text()")) if icms_tot is not None else 0.0,
        "vCOFINS":   _float(_txt(icms_tot, "nfe:vCOFINS/text()")) if icms_tot is not None else 0.0,
        "vNF":       _float(_txt(icms_tot, "nfe:vNF/text()")) if icms_tot is not None else 0.0,
    }

    logger.info(f"NFe parseada com sucesso: {caminho.name} — NF-e nº {cabecalho['nNF']}")

    return {
        "cabecalho":    cabecalho,
        "emitente":     emitente,
        "destinatario": destinatario,
        "itens":        itens,
        "totais":       totais,
        "status":       "ok",
    }


def parse_multiplos_xml(lista_caminhos: list) -> pd.DataFrame:
    """
    Parseia uma lista de XMLs de NFe e retorna DataFrame com uma linha por nota.

    Parâmetros:
        lista_caminhos: Lista de caminhos para arquivos XML.

    Retorna:
        pd.DataFrame com colunas de cabeçalho, emitente, destinatário e totais.

    Exemplo:
        arquivos = ["nfe_01_ok.xml", "nfe_02_aliquota_errada.xml"]
        df = parse_multiplos_xml(arquivos)
    """
    registros = []
    erros = []

    for caminho in lista_caminhos:
        nfe = parse_xml(caminho)
        if nfe.get("status") == "erro":
            erros.append(nfe)
            logger.warning(f"Erro ao parsear: {caminho} — {nfe.get('erro')}")
            continue

        row = {**nfe["cabecalho"], **{f"emit_{k}": v for k, v in nfe["emitente"].items()},
               **{f"dest_{k}": v for k, v in nfe["destinatario"].items()},
               **{f"tot_{k}": v for k, v in nfe["totais"].items()}}
        registros.append(row)

    if erros:
        logger.warning(f"{len(erros)} arquivo(s) com erro de parse.")

    return pd.DataFrame(registros) if registros else pd.DataFrame()


def extrair_itens(nfe_dict: dict) -> pd.DataFrame:
    """
    Extrai os itens de uma NFe parseada e retorna DataFrame enriquecido
    com dados do cabeçalho e emitente.

    Parâmetros:
        nfe_dict: Dicionário retornado por parse_xml().

    Retorna:
        pd.DataFrame com uma linha por item, incluindo chNFe, nNF, CRT, UF emitente/destinatário.

    Exemplo:
        nfe = parse_xml("nfe_01_ok.xml")
        df = extrair_itens(nfe)
        print(df[["nItem", "xProd", "icms_pICMS", "pis_pPIS"]])
    """
    if nfe_dict.get("status") == "erro" or not nfe_dict.get("itens"):
        return pd.DataFrame()

    cab = nfe_dict["cabecalho"]
    emit = nfe_dict["emitente"]
    dest = nfe_dict["destinatario"]

    itens = []
    for item in nfe_dict["itens"]:
        row = {
            "chNFe":      cab["chNFe"],
            "nNF":        cab["nNF"],
            "serie":      cab["serie"],
            "dhEmi":      cab["dhEmi"],
            "tpNF":       cab["tpNF"],
            "idDest":     cab["idDest"],
            "cMunFG":     cab["cMunFG"],
            "arquivo":    cab["arquivo"],
            "emit_CNPJ":  emit["CNPJ"],
            "emit_xNome": emit["xNome"],
            "emit_UF":    emit["UF"],
            "emit_CRT":   emit["CRT"],
            "dest_CNPJ":  dest["CNPJ"],
            "dest_xNome": dest["xNome"],
            "dest_UF":    dest["UF"],
            **item,
        }
        itens.append(row)

    return pd.DataFrame(itens)


def extrair_itens_lote(lista_caminhos: list) -> pd.DataFrame:
    """
    Parseia múltiplos XMLs e retorna todos os itens em um único DataFrame.

    Parâmetros:
        lista_caminhos: Lista de caminhos para arquivos XML.

    Retorna:
        pd.DataFrame consolidado com todos os itens de todas as notas.

    Exemplo:
        df = extrair_itens_lote(["nfe_01_ok.xml", "nfe_02_aliquota_errada.xml"])
    """
    frames = []
    for caminho in lista_caminhos:
        nfe = parse_xml(caminho)
        if nfe.get("status") == "ok":
            df_itens = extrair_itens(nfe)
            if not df_itens.empty:
                frames.append(df_itens)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
