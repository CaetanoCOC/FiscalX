"""Formatação de valores monetários, datas e percentuais para exibição."""

from datetime import datetime
from typing import Optional


def fmt_moeda(valor: float, simbolo: bool = True) -> str:
    """Formata valor como moeda brasileira. Ex: 1234.5 → 'R$ 1.234,50'"""
    try:
        v = float(valor)
        formatado = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatado}" if simbolo else formatado
    except (TypeError, ValueError):
        return "R$ 0,00" if simbolo else "0,00"


def fmt_percentual(valor: float, casas: int = 2) -> str:
    """Formata valor como percentual. Ex: 12.5 → '12,50%'"""
    try:
        return f"{float(valor):.{casas}f}".replace(".", ",") + "%"
    except (TypeError, ValueError):
        return "0,00%"


def fmt_data(data_str: str, formato_saida: str = "%d/%m/%Y") -> str:
    """Converte ISO datetime para formato legível. Ex: '2024-01-15T10:00:00-03:00' → '15/01/2024'"""
    if not data_str:
        return "—"
    try:
        dt = datetime.fromisoformat(data_str)
        return dt.strftime(formato_saida)
    except ValueError:
        try:
            return datetime.strptime(data_str[:10], "%Y-%m-%d").strftime(formato_saida)
        except ValueError:
            return data_str[:10]


def fmt_cnpj(cnpj: str) -> str:
    """Formata CNPJ. Ex: '11111111000191' → '11.111.111/0001-91'"""
    c = str(cnpj).strip().zfill(14)
    return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}" if len(c) == 14 else cnpj


def fmt_chave_nfe(chave: str) -> str:
    """Formata chave NFe em blocos de 4. Ex: '3524...' → '3524 1234 ...'"""
    c = str(chave).strip()
    return " ".join(c[i:i+4] for i in range(0, len(c), 4)) if len(c) == 44 else chave


def badge_severidade(severidade: str) -> str:
    """Retorna HTML de badge colorido para a severidade."""
    cores = {
        "CRÍTICO":     ("#E05252", "#FAFAFA"),
        "ALERTA":      ("#F7C34B", "#060E1A"),
        "INFORMATIVO": ("#4B9FE1", "#FAFAFA"),
    }
    bg, txt = cores.get(severidade, ("#6B7FA3", "#FAFAFA"))
    return (
        f'<span style="background:{bg};color:{txt};padding:2px 9px;'
        f'border-radius:4px;font-size:0.75em;font-weight:700;">{severidade}</span>'
    )
