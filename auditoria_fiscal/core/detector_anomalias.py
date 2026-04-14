"""
Detector de Anomalias Fiscais.

Identifica padrões suspeitos que fogem do comportamento esperado nas NFe.
Complementa o motor de validação com análises estatísticas e de padrão.

Anomalias detectadas:
    A01 — Notas de alto valor (> 3x média do emitente)
    A02 — Sequência numérica com saltos (possíveis notas não declaradas)
    A03 — Mesmo CNPJ emitindo em múltiplas UFs
    A04 — CFOP de devolução sem nota original referenciada
    A05 — NCM incomum (produtos muito distintos do padrão do emitente)
    A06 — Concentração excessiva em um fornecedor (> 40% do total)
    A07 — Notas emitidas fora do horário comercial (22h–6h)

Exemplo de uso:
    df_itens = extrair_itens_lote(lista_arquivos)
    df_anomalias = detectar_anomalias(df_itens)
"""

import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)

# CFOPs de devolução que exigem referência à nota original
CFOPS_DEVOLUCAO = {"1201", "1202", "1203", "2201", "2202", "5201", "5202", "6201", "6202"}

# Limite para concentração de fornecedor
LIMITE_CONCENTRACAO = 0.40  # 40%


def _nova_anomalia(
    ch_nfe: str, n_nf: str, n_item: str, arquivo: str,
    codigo: str, descricao: str,
    valor_observado: str, valor_referencia: str,
    emit_cnpj: str = "", emit_nome: str = "",
    severidade: str = "ALERTA",
) -> dict:
    return {
        "chNFe": ch_nfe,
        "nNF": n_nf,
        "item": n_item,
        "arquivo": arquivo,
        "emit_CNPJ": emit_cnpj,
        "emit_xNome": emit_nome,
        "codigo_anomalia": codigo,
        "descricao": descricao,
        "valor_observado": valor_observado,
        "valor_referencia": valor_referencia,
        "severidade": severidade,
    }


def _a01_alto_valor(df: pd.DataFrame, anomalias: list) -> None:
    """A01 — Notas com valor total > 3x a média do emitente no período."""
    if "emit_CNPJ" not in df.columns or "tot_vNF" not in df.columns:
        return

    # Uma linha por nota
    df_notas = df.drop_duplicates(subset="chNFe")[["chNFe", "nNF", "arquivo", "emit_CNPJ", "emit_xNome", "tot_vNF"]].copy()
    df_notas["tot_vNF"] = pd.to_numeric(df_notas["tot_vNF"], errors="coerce").fillna(0)

    media_emit = df_notas.groupby("emit_CNPJ")["tot_vNF"].transform("mean")
    limite = media_emit * 3

    suspeitas = df_notas[df_notas["tot_vNF"] > limite]
    for _, row in suspeitas.iterrows():
        media = float(media_emit[row.name])
        if media == 0:
            continue
        anomalias.append(_nova_anomalia(
            ch_nfe=str(row["chNFe"]), n_nf=str(row["nNF"]),
            n_item="—", arquivo=str(row["arquivo"]),
            codigo="A01",
            descricao=f"Nota com valor R$ {row['tot_vNF']:.2f} é {row['tot_vNF']/media:.1f}x a média do emitente (R$ {media:.2f})",
            valor_observado=f"R$ {row['tot_vNF']:.2f}",
            valor_referencia=f"Média: R$ {media:.2f} | Limite: R$ {media*3:.2f}",
            emit_cnpj=str(row["emit_CNPJ"]), emit_nome=str(row["emit_xNome"]),
            severidade="ALERTA",
        ))


def _a02_salto_numeracao(df: pd.DataFrame, anomalias: list) -> None:
    """A02 — Saltos na sequência numérica das notas por emitente."""
    if "emit_CNPJ" not in df.columns or "nNF" not in df.columns:
        return

    df_notas = df.drop_duplicates(subset="chNFe")[["chNFe", "nNF", "arquivo", "emit_CNPJ", "emit_xNome", "serie"]].copy()

    for (cnpj, serie), grupo in df_notas.groupby(["emit_CNPJ", "serie"]):
        numeros = pd.to_numeric(grupo["nNF"], errors="coerce").dropna().astype(int).sort_values()
        if len(numeros) < 2:
            continue

        for i in range(len(numeros) - 1):
            gap = numeros.iloc[i + 1] - numeros.iloc[i]
            if gap > 1:
                row = grupo[grupo["nNF"] == str(numeros.iloc[i])].iloc[0] if str(numeros.iloc[i]) in grupo["nNF"].values else grupo.iloc[0]
                anomalias.append(_nova_anomalia(
                    ch_nfe=str(row["chNFe"]), n_nf=str(numeros.iloc[i]),
                    n_item="—", arquivo=str(row["arquivo"]),
                    codigo="A02",
                    descricao=f"Salto de {gap-1} nota(s) na série {serie}: NF {numeros.iloc[i]} → NF {numeros.iloc[i+1]}",
                    valor_observado=f"NF {numeros.iloc[i]} → NF {numeros.iloc[i+1]} (gap={gap-1})",
                    valor_referencia="Sequência numérica contínua esperada",
                    emit_cnpj=str(cnpj), emit_nome=str(row.get("emit_xNome", "")),
                    severidade="INFORMATIVO",
                ))


def _a03_cnpj_multi_estado(df: pd.DataFrame, anomalias: list) -> None:
    """A03 — Mesmo CNPJ emitindo notas em múltiplas UFs diferentes."""
    if "emit_CNPJ" not in df.columns or "emit_UF" not in df.columns:
        return

    df_notas = df.drop_duplicates(subset="chNFe")[["chNFe", "nNF", "arquivo", "emit_CNPJ", "emit_xNome", "emit_UF"]].copy()
    ufs_por_cnpj = df_notas.groupby("emit_CNPJ")["emit_UF"].nunique()
    cnpjs_multi = ufs_por_cnpj[ufs_por_cnpj > 1].index

    for cnpj in cnpjs_multi:
        ufs = df_notas[df_notas["emit_CNPJ"] == cnpj]["emit_UF"].unique()
        row = df_notas[df_notas["emit_CNPJ"] == cnpj].iloc[0]
        anomalias.append(_nova_anomalia(
            ch_nfe="—", n_nf="—", n_item="—", arquivo=str(row["arquivo"]),
            codigo="A03",
            descricao=f"CNPJ {cnpj} emite notas em {len(ufs)} UFs diferentes: {', '.join(sorted(ufs))}",
            valor_observado=f"UFs: {', '.join(sorted(ufs))}",
            valor_referencia="Emissão em UF única (ou com IE em cada estado)",
            emit_cnpj=str(cnpj), emit_nome=str(row.get("emit_xNome", "")),
            severidade="ALERTA",
        ))


def _a04_devolucao_sem_referencia(df: pd.DataFrame, anomalias: list) -> None:
    """A04 — CFOP de devolução sem referência à nota original no lote."""
    if "CFOP" not in df.columns:
        return

    df_dev = df[df["CFOP"].isin(CFOPS_DEVOLUCAO)].copy()
    # Verifica se chNFe aparece em refNFe de alguma outra nota (não disponível sem parse adicional)
    # Por ora, sinaliza todas as devoluções para verificação manual
    for _, row in df_dev.iterrows():
        anomalias.append(_nova_anomalia(
            ch_nfe=str(row.get("chNFe", "")), n_nf=str(row.get("nNF", "")),
            n_item=str(row.get("nItem", "")), arquivo=str(row.get("arquivo", "")),
            codigo="A04",
            descricao=f"CFOP {row.get('CFOP')} é de devolução — verificar se nota original está referenciada no XML (refNFe)",
            valor_observado=f"CFOP {row.get('CFOP')}",
            valor_referencia="Campo refNFe obrigatório em devoluções",
            emit_cnpj=str(row.get("emit_CNPJ", "")), emit_nome=str(row.get("emit_xNome", "")),
            severidade="INFORMATIVO",
        ))


def _a05_ncm_incomum(df: pd.DataFrame, anomalias: list) -> None:
    """A05 — Produtos com NCM muito distinto do padrão do emitente."""
    if "emit_CNPJ" not in df.columns or "NCM" not in df.columns:
        return

    # Detecta NCM cuja classe (primeiros 2 dígitos) difere da moda do emitente
    df_ncm = df[["emit_CNPJ", "emit_xNome", "chNFe", "nNF", "nItem", "arquivo", "NCM", "xProd"]].copy()
    df_ncm["ncm_classe"] = df_ncm["NCM"].str[:2]

    for cnpj, grupo in df_ncm.groupby("emit_CNPJ"):
        if len(grupo) < 3:
            continue
        moda = grupo["ncm_classe"].mode()
        if moda.empty:
            continue
        classe_dominante = moda.iloc[0]
        incomuns = grupo[grupo["ncm_classe"] != classe_dominante]
        for _, row in incomuns.iterrows():
            anomalias.append(_nova_anomalia(
                ch_nfe=str(row["chNFe"]), n_nf=str(row["nNF"]),
                n_item=str(row["nItem"]), arquivo=str(row["arquivo"]),
                codigo="A05",
                descricao=f"NCM {row['NCM']} ({row['xProd']}) difere do padrão do emitente (classe NCM mais comum: {classe_dominante}xx)",
                valor_observado=f"NCM {row['NCM']}",
                valor_referencia=f"Classe dominante: {classe_dominante}xx",
                emit_cnpj=str(cnpj), emit_nome=str(row.get("emit_xNome", "")),
                severidade="INFORMATIVO",
            ))


def _a06_concentracao_fornecedor(df: pd.DataFrame, anomalias: list) -> None:
    """A06 — Fornecedor com > 40% do total de compras do período."""
    if "tpNF" not in df.columns or "vProd" not in df.columns:
        return

    df_entrada = df[df["tpNF"] == "0"].copy()
    if df_entrada.empty:
        return

    df_entrada["vProd"] = pd.to_numeric(df_entrada["vProd"], errors="coerce").fillna(0)
    total = float(df_entrada["vProd"].sum())
    if total == 0:
        return

    por_emit = df_entrada.groupby(["emit_CNPJ", "emit_xNome"])["vProd"].sum().reset_index()
    por_emit["pct"] = por_emit["vProd"] / total

    concentrados = por_emit[por_emit["pct"] > LIMITE_CONCENTRACAO]
    for _, row in concentrados.iterrows():
        anomalias.append(_nova_anomalia(
            ch_nfe="—", n_nf="—", n_item="—", arquivo="—",
            codigo="A06",
            descricao=f"Fornecedor {row['emit_xNome']} representa {row['pct']:.1%} do total de compras do período",
            valor_observado=f"{row['pct']:.1%} (R$ {row['vProd']:.2f})",
            valor_referencia=f"Limite: {LIMITE_CONCENTRACAO:.0%} | Total: R$ {total:.2f}",
            emit_cnpj=str(row["emit_CNPJ"]), emit_nome=str(row["emit_xNome"]),
            severidade="ALERTA",
        ))


def _a07_horario_suspeito(df: pd.DataFrame, anomalias: list) -> None:
    """A07 — Notas emitidas fora do horário comercial (22h–6h) para consumidor final."""
    if "dhEmi" not in df.columns:
        return

    # Foca em notas para consumidor final (indFinal=1 ou dest sem CNPJ)
    df_notas = df.drop_duplicates(subset="chNFe")[["chNFe", "nNF", "arquivo", "dhEmi", "emit_CNPJ", "emit_xNome", "dest_CNPJ"]].copy()

    for _, row in df_notas.iterrows():
        dh_str = str(row.get("dhEmi", "")).strip()
        if not dh_str:
            continue
        try:
            dh = datetime.fromisoformat(dh_str)
            hora = dh.hour
            if hora >= 22 or hora < 6:
                # Prioriza notas para pessoa física (sem CNPJ do destinatário)
                dest_cnpj = str(row.get("dest_CNPJ", "")).strip()
                if not dest_cnpj:
                    anomalias.append(_nova_anomalia(
                        ch_nfe=str(row["chNFe"]), n_nf=str(row["nNF"]),
                        n_item="—", arquivo=str(row["arquivo"]),
                        codigo="A07",
                        descricao=f"Nota emitida fora do horário comercial às {dh.strftime('%H:%M')} para consumidor final",
                        valor_observado=f"{dh.strftime('%d/%m/%Y %H:%M')}",
                        valor_referencia="Horário comercial: 06h–22h",
                        emit_cnpj=str(row["emit_CNPJ"]), emit_nome=str(row.get("emit_xNome", "")),
                        severidade="INFORMATIVO",
                    ))
        except Exception:
            pass


# ── Função principal ──────────────────────────────────────────────────────────

def detectar_anomalias(df_itens: pd.DataFrame) -> pd.DataFrame:
    """
    Executa todos os detectores de anomalias (A01–A07) no DataFrame de itens.

    Parâmetros:
        df_itens: DataFrame retornado por extrair_itens_lote() enriquecido com
                  colunas de totais (tot_vNF, tot_vProd, etc.) quando disponíveis.

    Retorna:
        pd.DataFrame com colunas:
            chNFe, nNF, item, arquivo, emit_CNPJ, emit_xNome,
            codigo_anomalia, descricao, valor_observado, valor_referencia, severidade

    Exemplo:
        df_anomalias = detectar_anomalias(df_itens)
        print(df_anomalias[df_anomalias["severidade"] == "ALERTA"])
    """
    if df_itens.empty:
        return pd.DataFrame()

    anomalias: list = []

    _a01_alto_valor(df_itens, anomalias)
    _a02_salto_numeracao(df_itens, anomalias)
    _a03_cnpj_multi_estado(df_itens, anomalias)
    _a04_devolucao_sem_referencia(df_itens, anomalias)
    _a05_ncm_incomum(df_itens, anomalias)
    _a06_concentracao_fornecedor(df_itens, anomalias)
    _a07_horario_suspeito(df_itens, anomalias)

    df_result = pd.DataFrame(anomalias)
    if not df_result.empty:
        ordem = {"ALERTA": 0, "INFORMATIVO": 1}
        df_result["_ord"] = df_result["severidade"].map(ordem).fillna(2)
        df_result = df_result.sort_values("_ord").drop(columns="_ord").reset_index(drop=True)

    logger.info(f"Detecção de anomalias: {len(anomalias)} anomalia(s) encontrada(s).")
    return df_result
