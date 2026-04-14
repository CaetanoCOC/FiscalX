"""
Módulo de Apuração de Impostos por Período Fiscal.

Calcula débitos, créditos e saldo a recolher de ICMS, PIS/COFINS e ISS
a partir do DataFrame de itens processados.

Exemplo de uso:
    df = extrair_itens_lote(["nfe_01_ok.xml", "nfe_02_aliquota_errada.xml"])
    resultado = apurar_icms(df, "2024-01")
    print(resultado)  # {debitos, creditos, saldo_devedor, saldo_credor}
"""

import logging
from typing import Optional

import pandas as pd

from core.atualizador_aliquotas import buscar_iss_municipio

logger = logging.getLogger(__name__)

# CFOPs que geram crédito de ICMS (entradas)
CFOPS_CREDITO_ICMS = {
    "1101", "1102", "1111", "1116", "1120", "1121", "1122", "1124", "1125",
    "1201", "1202", "1551",
    "2101", "2102", "2201", "2202", "2551",
}

# CFOPs que geram débito de ICMS (saídas)
CFOPS_DEBITO_ICMS = {
    "5101", "5102", "5111", "5113", "5114", "5115", "5120", "5122",
    "5651", "5652", "5653",
    "6101", "6102",
}

# CSTs de PIS/COFINS que geram débito (saída tributada)
CSTS_DEBITO_PIS_COFINS = {"01", "02", "03"}

# CSTs de PIS/COFINS que geram crédito (entrada com crédito)
CSTS_CREDITO_PIS_COFINS = {"50", "51", "52", "53", "54", "55", "56", "60"}


def _filtrar_periodo(df: pd.DataFrame, periodo: str) -> pd.DataFrame:
    """
    Filtra o DataFrame pelo período no formato 'AAAA-MM'.

    Parâmetros:
        df:      DataFrame com coluna 'dhEmi'.
        periodo: Período no formato "2024-01".

    Retorna:
        DataFrame filtrado.
    """
    if "dhEmi" not in df.columns:
        return df

    try:
        df = df.copy()
        df["_ano_mes"] = pd.to_datetime(
            df["dhEmi"].str[:7], format="%Y-%m", errors="coerce"
        ).dt.to_period("M").astype(str)
        return df[df["_ano_mes"] == periodo].drop(columns="_ano_mes")
    except Exception as e:
        logger.warning(f"Erro ao filtrar período {periodo}: {e}")
        return df


def apurar_icms(df_itens: pd.DataFrame, periodo: str) -> dict:
    """
    Apura ICMS do período: débitos de saídas, créditos de entradas.

    Parâmetros:
        df_itens: DataFrame de itens retornado por extrair_itens_lote().
        periodo:  Período no formato "AAAA-MM" (ex: "2024-01").

    Retorna:
        dict com:
            debitos, creditos, saldo_devedor, saldo_credor,
            notas_debito (int), notas_credito (int),
            detalhamento_debitos (DataFrame), detalhamento_creditos (DataFrame)

    Exemplo:
        resultado = apurar_icms(df, "2024-01")
        print(f"Saldo a recolher: R$ {resultado['saldo_devedor']:.2f}")
    """
    if df_itens.empty:
        return _resultado_vazio_icms()

    df = _filtrar_periodo(df_itens, periodo)
    if df.empty:
        return _resultado_vazio_icms()

    # Débitos: CFOPs de saída com ICMS destacado
    mask_debito = df["CFOP"].isin(CFOPS_DEBITO_ICMS) & (df["icms_vICMS"] > 0)
    df_debitos = df[mask_debito].copy()

    # Créditos: CFOPs de entrada com direito a crédito
    mask_credito = df["CFOP"].isin(CFOPS_CREDITO_ICMS) & (df["icms_vICMS"] > 0)
    df_creditos = df[mask_credito].copy()

    total_debitos = float(df_debitos["icms_vICMS"].sum())
    total_creditos = float(df_creditos["icms_vICMS"].sum())
    saldo = total_debitos - total_creditos

    return {
        "periodo": periodo,
        "imposto": "ICMS",
        "debitos": round(total_debitos, 2),
        "creditos": round(total_creditos, 2),
        "saldo_devedor": round(max(saldo, 0), 2),
        "saldo_credor": round(abs(min(saldo, 0)), 2),
        "notas_debito": df_debitos["chNFe"].nunique(),
        "notas_credito": df_creditos["chNFe"].nunique(),
        "detalhamento_debitos": df_debitos[["chNFe", "nNF", "nItem", "CFOP", "emit_xNome", "icms_vBC", "icms_pICMS", "icms_vICMS"]].copy() if not df_debitos.empty else pd.DataFrame(),
        "detalhamento_creditos": df_creditos[["chNFe", "nNF", "nItem", "CFOP", "emit_xNome", "icms_vBC", "icms_pICMS", "icms_vICMS"]].copy() if not df_creditos.empty else pd.DataFrame(),
    }


def _resultado_vazio_icms() -> dict:
    return {
        "periodo": "—",
        "imposto": "ICMS",
        "debitos": 0.0, "creditos": 0.0,
        "saldo_devedor": 0.0, "saldo_credor": 0.0,
        "notas_debito": 0, "notas_credito": 0,
        "detalhamento_debitos": pd.DataFrame(),
        "detalhamento_creditos": pd.DataFrame(),
    }


def apurar_pis_cofins(df_itens: pd.DataFrame, periodo: str) -> dict:
    """
    Apura PIS e COFINS do período (regime não-cumulativo).

    Parâmetros:
        df_itens: DataFrame de itens retornado por extrair_itens_lote().
        periodo:  Período no formato "AAAA-MM" (ex: "2024-01").

    Retorna:
        dict com:
            pis:    {debitos, creditos, saldo_devedor, saldo_credor}
            cofins: {debitos, creditos, saldo_devedor, saldo_credor}

    Exemplo:
        resultado = apurar_pis_cofins(df, "2024-01")
        print(f"PIS a recolher: R$ {resultado['pis']['saldo_devedor']:.2f}")
    """
    if df_itens.empty:
        return _resultado_vazio_pis_cofins()

    df = _filtrar_periodo(df_itens, periodo)
    if df.empty:
        return _resultado_vazio_pis_cofins()

    # Débitos PIS/COFINS
    mask_debito = df["pis_CST"].isin(CSTS_DEBITO_PIS_COFINS)
    df_debito = df[mask_debito].copy()

    # Créditos PIS/COFINS
    mask_credito = df["pis_CST"].isin(CSTS_CREDITO_PIS_COFINS)
    df_credito = df[mask_credito].copy()

    pis_debito = float(df_debito["pis_vPIS"].sum())
    pis_credito = float(df_credito["pis_vPIS"].sum())
    pis_saldo = pis_debito - pis_credito

    cofins_debito = float(df_debito["cofins_vCOFINS"].sum())
    cofins_credito = float(df_credito["cofins_vCOFINS"].sum())
    cofins_saldo = cofins_debito - cofins_credito

    return {
        "periodo": periodo,
        "pis": {
            "debitos": round(pis_debito, 2),
            "creditos": round(pis_credito, 2),
            "saldo_devedor": round(max(pis_saldo, 0), 2),
            "saldo_credor": round(abs(min(pis_saldo, 0)), 2),
        },
        "cofins": {
            "debitos": round(cofins_debito, 2),
            "creditos": round(cofins_credito, 2),
            "saldo_devedor": round(max(cofins_saldo, 0), 2),
            "saldo_credor": round(abs(min(cofins_saldo, 0)), 2),
        },
        "total_debitos": round(pis_debito + cofins_debito, 2),
        "total_creditos": round(pis_credito + cofins_credito, 2),
        "total_saldo_devedor": round(max(pis_saldo, 0) + max(cofins_saldo, 0), 2),
        "detalhamento": df_debito[["chNFe", "nNF", "nItem", "CFOP", "pis_CST", "pis_vPIS", "cofins_vCOFINS"]].copy() if not df_debito.empty else pd.DataFrame(),
    }


def _resultado_vazio_pis_cofins() -> dict:
    vazio = {"debitos": 0.0, "creditos": 0.0, "saldo_devedor": 0.0, "saldo_credor": 0.0}
    return {
        "periodo": "—",
        "pis": vazio.copy(),
        "cofins": vazio.copy(),
        "total_debitos": 0.0, "total_creditos": 0.0, "total_saldo_devedor": 0.0,
        "detalhamento": pd.DataFrame(),
    }


def apurar_iss(df_servicos: pd.DataFrame, periodo: str) -> dict:
    """
    Apura ISS do período para notas de serviço.

    Parâmetros:
        df_servicos: DataFrame com colunas: chNFe, nNF, cMunFG, vProd (valor do serviço).
        periodo:     Período no formato "AAAA-MM".

    Retorna:
        dict com: total_base, total_iss, detalhamento (DataFrame)

    Exemplo:
        resultado = apurar_iss(df_servicos, "2024-01")
        print(f"ISS a recolher: R$ {resultado['total_iss']:.2f}")
    """
    if df_servicos.empty:
        return {"periodo": periodo, "total_base": 0.0, "total_iss": 0.0, "detalhamento": pd.DataFrame()}

    df = _filtrar_periodo(df_servicos, periodo)
    if df.empty:
        return {"periodo": periodo, "total_base": 0.0, "total_iss": 0.0, "detalhamento": pd.DataFrame()}

    registros = []
    for _, row in df.iterrows():
        codigo_ibge = str(row.get("cMunFG", "")).strip()
        v_servico = float(row.get("vProd", 0) or 0)

        iss_info = buscar_iss_municipio(codigo_ibge)
        aliquota = iss_info["aliquota"]
        v_iss = round(v_servico * aliquota / 100, 2)

        registros.append({
            "chNFe": row.get("chNFe", ""),
            "nNF": row.get("nNF", ""),
            "municipio": iss_info["municipio"],
            "uf": iss_info["uf"],
            "aliquota_iss": aliquota,
            "base_calculo": v_servico,
            "valor_iss": v_iss,
            "estimativa": iss_info["estimativa"],
        })

    df_result = pd.DataFrame(registros)
    return {
        "periodo": periodo,
        "total_base": round(float(df_result["base_calculo"].sum()), 2),
        "total_iss": round(float(df_result["valor_iss"].sum()), 2),
        "detalhamento": df_result,
    }


def apuracao_comparativa(df_itens: pd.DataFrame, periodos: list) -> pd.DataFrame:
    """
    Gera tabela comparativa de apuração de ICMS, PIS e COFINS para múltiplos períodos.

    Parâmetros:
        df_itens: DataFrame de itens.
        periodos: Lista de períodos no formato "AAAA-MM" (ex: ["2024-01", "2024-02"]).

    Retorna:
        pd.DataFrame com uma linha por período contendo todos os totais.

    Exemplo:
        df_comp = apuracao_comparativa(df, ["2024-01", "2024-02", "2024-03"])
    """
    linhas = []
    for periodo in periodos:
        icms = apurar_icms(df_itens, periodo)
        pis_cofins = apurar_pis_cofins(df_itens, periodo)
        linhas.append({
            "periodo": periodo,
            "icms_debitos": icms["debitos"],
            "icms_creditos": icms["creditos"],
            "icms_saldo": icms["saldo_devedor"],
            "pis_debitos": pis_cofins["pis"]["debitos"],
            "pis_creditos": pis_cofins["pis"]["creditos"],
            "pis_saldo": pis_cofins["pis"]["saldo_devedor"],
            "cofins_debitos": pis_cofins["cofins"]["debitos"],
            "cofins_creditos": pis_cofins["cofins"]["creditos"],
            "cofins_saldo": pis_cofins["cofins"]["saldo_devedor"],
            "total_saldo": icms["saldo_devedor"] + pis_cofins["total_saldo_devedor"],
        })
    return pd.DataFrame(linhas)
