"""Validações gerais: CNPJ, CPF, chave NFe."""


def validar_cnpj(cnpj: str) -> bool:
    """Valida CNPJ pelo algoritmo de dígitos verificadores."""
    c = "".join(filter(str.isdigit, str(cnpj)))
    if len(c) != 14 or c == c[0] * 14:
        return False

    def calc(digitos, pesos):
        s = sum(int(d) * p for d, p in zip(digitos, pesos))
        r = s % 11
        return 0 if r < 2 else 11 - r

    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    p2 = [6] + p1

    return int(c[12]) == calc(c[:12], p1) and int(c[13]) == calc(c[:13], p2)


def validar_cpf(cpf: str) -> bool:
    """Valida CPF pelo algoritmo de dígitos verificadores."""
    c = "".join(filter(str.isdigit, str(cpf)))
    if len(c) != 11 or c == c[0] * 11:
        return False

    def calc(digitos, n):
        s = sum(int(d) * (n - i) for i, d in enumerate(digitos))
        r = (s * 10) % 11
        return 0 if r >= 10 else r

    return int(c[9]) == calc(c[:9], 10) and int(c[10]) == calc(c[:10], 11)


def validar_chave_nfe(chave: str) -> bool:
    """Valida se a chave NFe tem 44 dígitos numéricos."""
    c = "".join(filter(str.isdigit, str(chave)))
    return len(c) == 44


def validar_ncm(ncm: str) -> bool:
    """Valida se o NCM tem 8 dígitos."""
    return len("".join(filter(str.isdigit, str(ncm)))) == 8


def validar_cfop(cfop: str) -> bool:
    """Valida se o CFOP tem 4 dígitos e começa com 1-7."""
    c = str(cfop).strip()
    return len(c) == 4 and c.isdigit() and c[0] in "1234567"
