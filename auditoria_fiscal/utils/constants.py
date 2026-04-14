"""Constantes do sistema FiscalX."""

APP_TITLE = "FiscalX — Auditoria Fiscal"
APP_ICON = "🔍"
APP_VERSION = "1.0.0"

# ── Design System — StockPeers (navy dark) ───────────────────────────────────
# Fundo navy profundo, cards azul-noite, linhas de gráfico saturadas e vivas
COR_FUNDO      = "#0B1120"   # navy quase preto (fundo principal)
COR_SIDEBAR    = "#0D1626"   # sidebar ligeiramente mais escura
COR_CARD       = "#111827"   # card/container azul-noite
COR_CARD_ALT   = "#151F35"   # card alternativo (hover, zebra)
COR_BORDA      = "#1E2D45"   # separadores e bordas sutis

# Texto
COR_TEXTO      = "#E8EBF0"   # branco suave — títulos e valores
COR_TEXTO_SEC  = "#6B7FA3"   # cinza-azulado — labels e subtítulos

# Cores de acento (inspiradas nas linhas do gráfico StockPeers)
COR_CIANO      = "#00CDCD"   # linha principal — ciano elétrico
COR_AZUL       = "#4B9FE1"   # azul elétrico
COR_VERDE      = "#00CC77"   # verde
COR_VERMELHO   = "#E05252"   # vermelho/coral
COR_AMARELO    = "#F7C34B"   # dourado
COR_ROSA       = "#E06AA0"   # magenta/rosa
COR_LARANJA    = "#E07A40"   # laranja

# Severidade
COR_CRITICO    = "#E05252"   # vermelho
COR_ALERTA     = "#F7C34B"   # dourado
COR_INFORMATIVO= "#4B9FE1"   # azul

# Paleta para séries de gráficos (ordem das linhas do StockPeers)
PALETA_GRAFICOS = [
    "#E05252",  # vermelho
    "#00CDCD",  # ciano
    "#4B9FE1",  # azul
    "#F7C34B",  # dourado
    "#00CC77",  # verde
    "#E06AA0",  # rosa
    "#E07A40",  # laranja
]

# Severidades
SEVERIDADES = ["CRÍTICO", "ALERTA", "INFORMATIVO"]
SEVERIDADE_CORES = {
    "CRÍTICO": COR_CRITICO,
    "ALERTA": COR_ALERTA,
    "INFORMATIVO": COR_INFORMATIVO,
}

# Regimes tributários
CRT_DESCRICAO = {
    "1": "Simples Nacional",
    "2": "Simples Nacional — Excesso de Sublimite",
    "3": "Regime Normal (Lucro Presumido / Lucro Real)",
}

# Tipos de nota
TP_NF_DESCRICAO = {"0": "Entrada", "1": "Saída"}

# Destinos
ID_DEST_DESCRICAO = {"1": "Interna", "2": "Interestadual", "3": "Exterior"}

# UFs do Brasil
UFS_BRASIL = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]

# Extensões aceitas para upload
EXTENSOES_XML = ["xml", "zip"]

# Tolerâncias
TOLERANCIA_ALIQUOTA = 0.01   # %
TOLERANCIA_VALOR = 0.02      # R$
TOLERANCIA_ICMS = 1.00       # R$
