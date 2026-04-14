"""
Atualizador de Alíquotas — garante que o sistema use alíquotas vigentes.

Fontes:
    - ICMS: tabela hardcoded CONFAZ + arquivo config/aliquotas_icms.json
    - ISS: config/aliquotas_iss.json (100+ municípios por código IBGE)
    - IPI: config/ncm_aliquotas.json (TIPI) com cache em memória
    - PIS/COFINS: alíquotas fixas por regime em config/cst_pis_cofins.json

Exemplo de uso:
    aliq = buscar_aliquota_icms("SP", "MG", id_dest="2")  # 12.0
    iss = buscar_iss_municipio("3550308")  # 5.0 (São Paulo)
    ipi = buscar_aliquota_ipi("84713012")  # 0.0 (notebook)
"""

import json
import logging
from pathlib import Path
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent.parent / "config"

_cache_icms: Optional[dict] = None
_cache_iss: Optional[dict] = None
_cache_ncm: Optional[dict] = None
_cache_pis_cofins: Optional[dict] = None


def _load_json(nome: str) -> dict:
    try:
        with open(CONFIG_DIR / nome, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Arquivo de configuração não encontrado: {nome}")
        return {}


def _icms_cfg() -> dict:
    global _cache_icms
    if _cache_icms is None:
        _cache_icms = _load_json("aliquotas_icms.json")
    return _cache_icms


def _iss_cfg() -> dict:
    global _cache_iss
    if _cache_iss is None:
        _cache_iss = _load_json("aliquotas_iss.json")
    return _cache_iss


def _ncm_cfg() -> dict:
    global _cache_ncm
    if _cache_ncm is None:
        _cache_ncm = _load_json("ncm_aliquotas.json")
    return _cache_ncm


def _pis_cofins_cfg() -> dict:
    global _cache_pis_cofins
    if _cache_pis_cofins is None:
        _cache_pis_cofins = _load_json("cst_pis_cofins.json")
    return _cache_pis_cofins


# ── ICMS ──────────────────────────────────────────────────────────────────────

def buscar_aliquota_icms(
    uf_emitente: str,
    uf_destinatario: str,
    id_dest: str = "1",
    origem_importado: bool = False,
) -> dict:
    """
    Retorna a alíquota ICMS aplicável conforme CONFAZ.

    Parâmetros:
        uf_emitente:      UF do emitente (ex: "SP")
        uf_destinatario:  UF do destinatário (ex: "MG")
        id_dest:          "1"=Interna, "2"=Interestadual, "3"=Exterior
        origem_importado: True se mercadoria importada (aplica 4% - Res. SF 13/2012)

    Retorna:
        dict com: aliquota, tipo, fonte, observacao

    Exemplo:
        buscar_aliquota_icms("SP", "MG", id_dest="2")
        # {"aliquota": 12.0, "tipo": "interestadual", "fonte": "CONFAZ", ...}
    """
    cfg = _icms_cfg()
    if not cfg:
        return {"aliquota": None, "tipo": "desconhecido", "fonte": "config não carregada", "observacao": ""}

    if origem_importado and id_dest == "2":
        aliq = cfg.get("importados", 4.0)
        return {
            "aliquota": aliq,
            "tipo": "importado",
            "fonte": "Resolução SF 13/2012",
            "observacao": "Mercadoria importada — alíquota 4% nas operações interestaduais",
        }

    if id_dest == "1":  # Interna
        aliq = cfg.get("internas", {}).get(uf_emitente)
        return {
            "aliquota": aliq,
            "tipo": "interna",
            "fonte": "CONFAZ",
            "observacao": f"Alíquota interna {uf_emitente}",
        }

    if id_dest == "2":  # Interestadual
        chave = f"{uf_emitente}_{uf_destinatario}"
        tabela = cfg.get("interestaduais", {}).get("tabela", {})
        if chave in tabela:
            aliq = tabela[chave]
        else:
            origem_7 = cfg.get("interestaduais", {}).get("origem_7", [])
            destino_7 = cfg.get("interestaduais", {}).get("destino_7", [])
            aliq = 7.0 if (uf_emitente in origem_7 and uf_destinatario in destino_7) else 12.0

        return {
            "aliquota": aliq,
            "tipo": "interestadual",
            "fonte": "CONFAZ",
            "observacao": f"{uf_emitente} → {uf_destinatario}",
        }

    if id_dest == "3":  # Exterior — exportação não tributada
        return {
            "aliquota": 0.0,
            "tipo": "exportacao",
            "fonte": "CF/88 art. 155 §2º X a",
            "observacao": "Exportações imunes ao ICMS",
        }

    return {"aliquota": None, "tipo": "desconhecido", "fonte": "", "observacao": ""}


def buscar_fcp(uf: str) -> float:
    """
    Retorna o percentual do FCP (Fundo de Combate à Pobreza) para a UF.

    Parâmetros:
        uf: Sigla da UF (ex: "RJ")

    Retorna:
        float — percentual FCP (0.0 se não aplicável)

    Exemplo:
        buscar_fcp("RJ")  # 2.0
        buscar_fcp("SP")  # 0.0
    """
    cfg = _icms_cfg()
    return float(cfg.get("fcp", {}).get(uf, 0.0))


# ── ISS ───────────────────────────────────────────────────────────────────────

def buscar_iss_municipio(codigo_ibge: str) -> dict:
    """
    Retorna a alíquota ISS para o município pelo código IBGE.

    Parâmetros:
        codigo_ibge: Código IBGE do município (7 dígitos, ex: "3550308")

    Retorna:
        dict com: aliquota, municipio, uf, estimativa (bool)

    Exemplo:
        buscar_iss_municipio("3550308")
        # {"aliquota": 5.0, "municipio": "São Paulo", "uf": "SP", "estimativa": False}
    """
    cfg = _iss_cfg()
    municipios = cfg.get("municipios", {})

    if codigo_ibge in municipios:
        info = municipios[codigo_ibge]
        return {
            "aliquota": float(info.get("aliquota", 5.0)),
            "municipio": info.get("municipio", ""),
            "uf": info.get("uf", ""),
            "estimativa": False,
            "fonte": "Legislação municipal",
        }

    # Município não mapeado — retorna alíquota máxima com flag de estimativa
    logger.warning(f"Município {codigo_ibge} não mapeado — usando alíquota estimada de 5%")
    return {
        "aliquota": float(cfg.get("maximo_legal", 5.0)),
        "municipio": f"Município {codigo_ibge}",
        "uf": "?",
        "estimativa": True,
        "fonte": "Estimativa (máximo legal LC 116/2003)",
    }


def listar_municipios_iss() -> list:
    """Retorna lista de municípios mapeados com alíquota ISS."""
    cfg = _iss_cfg()
    municipios = cfg.get("municipios", {})
    return [
        {"codigo_ibge": k, **v}
        for k, v in municipios.items()
    ]


# ── IPI ───────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=512)
def buscar_aliquota_ipi(ncm: str) -> dict:
    """
    Retorna a alíquota IPI para o NCM conforme a TIPI.
    Resultado cacheado em memória para melhor performance.

    Parâmetros:
        ncm: Código NCM de 8 dígitos (ex: "84713012")

    Retorna:
        dict com: aliquota, descricao, encontrado (bool)

    Exemplo:
        buscar_aliquota_ipi("84713012")  # notebook — {"aliquota": 0.0, ...}
        buscar_aliquota_ipi("22030000")  # cerveja — {"aliquota": 30.0, ...}
    """
    cfg = _ncm_cfg()
    aliquotas = cfg.get("aliquotas", {})

    if ncm in aliquotas:
        info = aliquotas[ncm]
        return {
            "aliquota": float(info.get("ipi", 0.0)),
            "descricao": info.get("descricao", ""),
            "encontrado": True,
            "fonte": "TIPI — Decreto 11.158/2022",
        }

    # Tenta NCM com 6 dígitos (posição da TIPI)
    ncm_6 = ncm[:6] if len(ncm) >= 6 else ncm
    for k, v in aliquotas.items():
        if k.startswith(ncm_6):
            return {
                "aliquota": float(v.get("ipi", 0.0)),
                "descricao": v.get("descricao", ""),
                "encontrado": True,
                "fonte": "TIPI (posição aproximada)",
            }

    return {
        "aliquota": 0.0,
        "descricao": f"NCM {ncm} não encontrado na TIPI",
        "encontrado": False,
        "fonte": "Não mapeado",
    }


# ── PIS/COFINS ────────────────────────────────────────────────────────────────

def buscar_aliquotas_pis_cofins(regime: str = "nao_cumulativo") -> dict:
    """
    Retorna alíquotas de PIS e COFINS por regime tributário.

    Parâmetros:
        regime: "cumulativo" (Lucro Presumido) ou "nao_cumulativo" (Lucro Real)

    Retorna:
        dict com: pis, cofins, regime, legislacao, vigencia

    Exemplo:
        buscar_aliquotas_pis_cofins("cumulativo")
        # {"pis": 0.65, "cofins": 3.00, "regime": "Lucro Presumido", ...}
    """
    cfg = _pis_cofins_cfg()
    aliquotas = cfg.get("aliquotas", {})

    if regime in aliquotas:
        info = aliquotas[regime]
        return {
            "pis": float(info.get("pis", 0.0)),
            "cofins": float(info.get("cofins", 0.0)),
            "regime": info.get("regime", regime),
            "legislacao": info.get("legislacao", ""),
            "vigencia": info.get("vigencia", ""),
        }

    return {"pis": 0.0, "cofins": 0.0, "regime": regime, "legislacao": "", "vigencia": ""}


def inferir_regime_pis_cofins(crt: str) -> str:
    """
    Infere o regime de PIS/COFINS pelo CRT do emitente.

    Parâmetros:
        crt: Código de Regime Tributário ("1"=Simples, "2"=SN Excesso, "3"=Normal)

    Retorna:
        "simples" | "cumulativo" | "nao_cumulativo"

    Exemplo:
        inferir_regime_pis_cofins("3")  # "nao_cumulativo"
    """
    if crt == "1":
        return "simples"
    elif crt == "2":
        return "cumulativo"  # Simples excesso — geralmente cumulativo
    elif crt == "3":
        return "nao_cumulativo"  # Lucro Real — presume-se não-cumulativo
    return "desconhecido"


# ── Status geral ──────────────────────────────────────────────────────────────

def status_aliquotas() -> dict:
    """
    Retorna status de vigência de todas as tabelas de alíquotas.

    Retorna:
        dict com vigência e contagem de registros por imposto.

    Exemplo:
        status = status_aliquotas()
        print(status["icms"]["vigencia"])  # "2024-01-01"
    """
    icms = _icms_cfg()
    iss = _iss_cfg()
    ncm = _ncm_cfg()

    return {
        "icms": {
            "vigencia": icms.get("vigencia", "—"),
            "fonte": icms.get("fonte", "—"),
            "estados_internos": len(icms.get("internas", {})),
            "tabela_interestadual": len(icms.get("interestaduais", {}).get("tabela", {})),
        },
        "iss": {
            "vigencia": iss.get("vigencia", "—"),
            "fonte": iss.get("fonte", "—"),
            "municipios_mapeados": len(iss.get("municipios", {})),
            "minimo_legal": iss.get("minimo_legal", 2.0),
            "maximo_legal": iss.get("maximo_legal", 5.0),
        },
        "ipi": {
            "vigencia": ncm.get("vigencia", "—"),
            "fonte": ncm.get("fonte", "—"),
            "ncms_mapeados": len(ncm.get("aliquotas", {})),
        },
        "pis_cofins": {
            "cumulativo": {"pis": 0.65, "cofins": 3.00},
            "nao_cumulativo": {"pis": 1.65, "cofins": 7.60},
            "legislacao": "Lei 10.637/2002 e Lei 10.833/2003",
        },
    }
