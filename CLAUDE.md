# CLAUDE.md — FiscalX: Sistema de Auditoria Fiscal Automatizada de NFe

## Visão Geral do Projeto

Sistema profissional de auditoria fiscal em Python com interface Streamlit.
Lê XMLs de Notas Fiscais Eletrônicas (NFe layout 4.0), valida tributação,
detecta inconsistências, apura impostos (ICMS, PIS, COFINS, IPI, ISS) e
gera relatórios de auditoria exportáveis.

**Objetivo:** Portfólio para vagas de Auditor Fiscal / Analista Fiscal.
Deve impressionar demonstrado ao vivo em entrevista técnica.

**Status:** ✅ Totalmente implementado e funcional.

---

## Estrutura de Pastas

```
FiscalX/                          ← raiz do repositório
├── NFe_ficticio.zip              ← 20 NFes fictícias para demo/teste
├── CLAUDE.md
└── auditoria_fiscal/             ← aplicação Streamlit
    ├── app.py                    ← ROTEADOR: set_page_config + CSS + sidebar + st.navigation()
    ├── home.py                   ← conteúdo da página Dashboard (chamado pelo app.py)
    ├── requirements.txt
    ├── static/                   ← assets estáticos (logos)
    │   ├── fiscalx_icon_512.png  ← logo sidebar
    │   └── fiscalx_icon_1024.png ← favicon
    ├── config/
    │   ├── aliquotas_icms.json
    │   ├── aliquotas_iss.json
    │   ├── cfop_table.json
    │   ├── cst_icms.json
    │   ├── cst_pis_cofins.json
    │   └── ncm_aliquotas.json
    ├── core/
    │   ├── __init__.py
    │   ├── parser_nfe.py
    │   ├── motor_validacao.py
    │   ├── apuracao.py
    │   ├── detector_anomalias.py
    │   └── atualizador_aliquotas.py
    ├── data/
    │   ├── uploads/
    │   ├── processados/
    │   └── relatorios/
    ├── pages/                    ← arquivos de conteúdo PURO (sem set_page_config, sem sidebar)
    │   ├── 01_upload_nfe.py
    │   ├── 02_dashboard_fiscal.py
    │   ├── 03_auditoria_detalhada.py
    │   ├── 04_apuracao_impostos.py
    │   └── 05_relatorio_exportar.py
    ├── utils/
    │   ├── constants.py          ← tokens de cor e constantes globais
    │   ├── theme.py              ← css_global() + plotly_layout()
    │   ├── formatters.py
    │   └── validators.py
    └── tests/
        ├── sample_nfe/           ← 5 XMLs de teste unitário
        ├── test_parser.py
        ├── test_validacao.py
        └── test_apuracao.py
```

---

## Arquitetura de Navegação — IMPORTANTE

O projeto usa `st.navigation()` do Streamlit 1.36+ com `position="hidden"`.

**Regra crítica:** `app.py` é o único arquivo que contém:
- `st.set_page_config()` — chamado apenas uma vez
- `st.markdown(css_global())` — CSS global injetado uma vez
- Sidebar (`with st.sidebar`) — compartilhada automaticamente com todas as páginas
- `st.navigation([...], position="hidden")` — desabilita o nav automático do Streamlit

**As páginas em `pages/` e `home.py` NÃO devem conter:**
- `st.set_page_config()`
- `st.markdown(css_global())`
- Nenhum código de sidebar
- `sys.path.insert` (o path já está configurado pelo app.py)

Isso elimina o flash do nav automático do Streamlit na troca de páginas.

---

## Dependências (requirements.txt)

```
streamlit>=1.35.0
pandas>=2.0.0
lxml>=5.0.0
openpyxl>=3.1.0
requests>=2.31.0
python-dotenv>=1.0.0
plotly>=5.18.0
reportlab>=4.1.0
httpx>=0.27.0
pydantic>=2.0.0
streamlit-aggrid>=0.3.4
```

Ambiente Python: `notafiscal/` (Conda, na raiz do repo).
Python em: `notafiscal/python.exe` (NÃO `notafiscal/Scripts/python.exe`).

---

## Módulos Core

### parser_nfe.py
Extrai do XML NFe 4.0: cabeçalho, emitente, destinatário, itens (com ICMS,
PIS/COFINS, IPI) e totais. Funções principais:
- `parse_xml(caminho: str) -> dict`
- `parse_multiplos_xml(lista: list) -> pd.DataFrame`
- `extrair_itens(nfe_dict: dict) -> pd.DataFrame`
- `extrair_itens_lote(lista: list) -> pd.DataFrame`

Namespace XML: `NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}`
Suporta todos os grupos ICMS: ICMS00–ICMS90, ICMSSN101–ICMSSN900.

### motor_validacao.py
12 validações tributárias com severidade CRÍTICO / ALERTA / INFORMATIVO:

| Código | Validação | Severidade |
|--------|-----------|------------|
| V01 | CFOP vs tipo de operação (entrada/saída) | CRÍTICO |
| V02 | CFOP vs destino (interna/interestadual/exterior) | CRÍTICO |
| V03 | Alíquota ICMS declarada vs esperada (tolerância 0,01%) | CRÍTICO |
| V04 | Base de cálculo ICMS | ALERTA |
| V05 | Valor ICMS calculado vs declarado | CRÍTICO |
| V06 | CST vs regime tributário (CRT=1→CSOSN, CRT=3→CST) | CRÍTICO |
| V07 | CFOP vs CST PIS/COFINS | ALERTA |
| V08 | Alíquota PIS/COFINS por regime | ALERTA |
| V09 | NCM vs alíquota IPI (TIPI) | ALERTA |
| V10 | Duplicidade de chave de acesso | CRÍTICO |
| V11 | Nota fora do prazo de emissão (>24h) | INFORMATIVO |
| V12 | Soma dos itens vs total da nota (tolerância R$0,02) | CRÍTICO |

Retorno: `validar_nfe(nfe_df) -> pd.DataFrame` com colunas:
`chNFe, nNF, item, codigo_validacao, descricao, valor_declarado, valor_esperado, divergencia, severidade`

### atualizador_aliquotas.py
- ICMS: tabela CONFAZ (4% importados, 7% Sul/SE→N/NE/CO, 12% demais)
- ISS: JSON por código IBGE (100+ municípios), padrão 5% com flag "estimativa"
- IPI: JSON local baseado na TIPI com cache LRU em memória
- PIS/COFINS: alíquotas fixas por regime com controle de vigência

### apuracao.py
- `apurar_icms(df, periodo) -> dict` → débitos/créditos/saldo por CFOP
- `apurar_pis_cofins(df, periodo) -> dict` → separado por PIS e COFINS
- `apurar_iss(df, periodo) -> dict` → por município, verifica retenção
- `apuracao_comparativa(df_itens, periodos) -> pd.DataFrame`

### detector_anomalias.py
7 detectores: A01 (alto valor), A02 (salto numérico), A03 (CNPJ multi-estado),
A04 (devolução sem nota original), A05 (NCM incongruente), A06 (concentração
fornecedor >40%), A07 (emissão fora horário comercial).

---

## Páginas Streamlit

- **app.py** — Roteador + sidebar (logo base64) + CSS global + favicon (NÃO é uma página de conteúdo)
- **home.py** — Dashboard: KPIs, pizza severidade, barra por validação, status alíquotas
- **01_upload_nfe.py** — Upload multi-XML/zip, preview em tabela HTML com filtros, botão "Iniciar Auditoria"
- **02_dashboard_fiscal.py** — KPIs, linha mensal, heatmap UF, treemap CFOP, Top 10 fornecedores HTML
- **03_auditoria_detalhada.py** — Tabela HTML com ícone de severidade 🔴🟡🔵, scroll interno, filtros, anomalias
- **04_apuracao_impostos.py** — Cards débito/crédito/saldo ICMS+PIS+COFINS, gráfico comparativo, detalhamento HTML, simulação DARF
- **05_relatorio_exportar.py** — Preview do relatório, exportação Excel (.xlsx) e CSV

---

## Design System — Navy Dark

**Cores (utils/constants.py):**

| Token | Valor | Uso |
|-------|-------|-----|
| `COR_FUNDO` | `#0B1120` | Fundo base (não usado na tela — ver abaixo) |
| `COR_SIDEBAR` | `#0D1626` | Sidebar, tela principal e header — cor unificada |
| `COR_CARD` | `#111827` | Cards e containers |
| `COR_CARD_ALT` | `#151F35` | Cards alternativos, zebrado de tabelas |
| `COR_BORDA` | `#1E2D45` | Bordas e separadores |
| `COR_TEXTO` | `#E8EBF0` | Texto primário |
| `COR_TEXTO_SEC` | `#6B7FA3` | Texto secundário e labels |
| `COR_CIANO` | `#00CDCD` | Accent principal, botões |
| `COR_AZUL` | `#4B9FE1` | Accent secundário |
| `COR_VERDE` | `#00CC77` | Positivo |
| `COR_VERMELHO` | `#E05252` | CRÍTICO, negativo |
| `COR_AMARELO` | `#F7C34B` | ALERTA, destaque |

**Nota:** `COR_SIDEBAR` é usada no fundo da tela principal, no header (faixa do deploy)
e na sidebar para criar visual unificado e coeso.

**CSS global (utils/theme.py):**
- `css_global()` — retorna CSS completo como string
- `plotly_layout(height, margin)` — layout padrão Plotly dark
- `[data-testid="stVerticalBlockBorderWrapper"]` — estilizado como fiscal-card (border + radius)
- Sidebar com `box-shadow` duplo para efeito de alto relevo
- Header (`[data-testid="stHeader"]`) cor unificada com a tela (`COR_SIDEBAR`)
- `[data-testid="stSidebarNav"]` oculto (substituído pelo nav do `st.navigation()`)
- Botões primários (`.stButton`): texto `#0A0F1A` (quase preto) + `font-weight:800` sobre ciano
- Botões de download (`.stDownloadButton`): estilo *ghost* — fundo transparente, borda + texto ciano; hover preenche ciano com texto escuro

**Severidade → cor:**
- CRÍTICO → `#E05252` (vermelho)
- ALERTA → `#F7C34B` (amarelo)
- INFORMATIVO → `#4B9FE1` (azul)

---

## XMLs de Teste

### tests/sample_nfe/ — testes unitários (5 arquivos)
| Arquivo | Cenário | Validação Esperada |
|---------|---------|-------------------|
| nfe_01_ok.xml | SP→MG, ICMS 12%, correto | Sem inconsistências |
| nfe_02_aliquota_errada.xml | ICMS 18% em interestadual | V03 CRÍTICO |
| nfe_03_cfop_divergente.xml | CFOP saída em nota entrada | V01 CRÍTICO |
| nfe_04_simples_nacional.xml | CRT=1 com CST em vez de CSOSN | V06 CRÍTICO |
| nfe_05_pis_cofins_errado.xml | PIS 0,65% para Lucro Real | V08 ALERTA |

### NFe_ficticio.zip — demo completa (20 NFes, raiz do repo)
20 notas espalhadas de Jan/2024 a Jul/2024, cobrindo:
- 8 emitentes de diferentes UFs (SP, MG, RJ, PR, BA, GO, SC, PE)
- Operações internas e interestaduais
- Regimes Lucro Real (CRT=3) e Simples Nacional (CRT=1)
- Erros intencionais: V01, V03 (×2), V06, V08 (×2) — para popular os gráficos de auditoria

---

## Regras Tributárias Chave

- **DIFAL (EC 87/2015):** operações interestaduais para consumidor final não contribuinte
- **FCP:** adicional 2% em MG, RJ, CE, MA, PI, AL, RN, SE, TO, AP, RO, AC, AM, PA, RR, MT, MS
- **Simples Nacional (CRT=1):** usa CSOSN (1xx), não CST; sem destaque ICMS
- **PIS/COFINS cumulativo:** PIS 0,65% / COFINS 3,00% (Lucro Presumido)
- **PIS/COFINS não-cumulativo:** PIS 1,65% / COFINS 7,60% (Lucro Real)
- **ISS:** mínimo 2%, máximo 5% (LC 116/2003)
- **ICMS interestadual:** 7% Sul/SE→N/NE/CO; 12% demais pares; 4% mercadoria importada

---

## Armadilhas conhecidas / decisões técnicas

- **NÃO usar `st.dataframe()` para tabelas com dados fiscais** — em Streamlit 1.35+ o componente dataframe não renderiza dentro de `st.container(border=True)` nem em alguns layouts de coluna no dark mode. Solução definitiva: usar tabelas HTML puras via `st.markdown(..., unsafe_allow_html=True)` com `<div class='fiscal-card' style='padding:0; overflow:auto;'>`.
- **NÃO usar padrão open/close div** — `st.markdown("<div class='fiscal-card'>")` seguido de componentes Streamlit e `st.markdown("</div>")` NÃO funciona. O Streamlit isola cada `st.markdown()` e fecha o div imediatamente, criando um card vazio. Para envolver componentes (charts, widgets) usar `with st.container(border=True):`.
- **`st.container(border=True)` + CSS** — estilizado via `[data-testid="stVerticalBlockBorderWrapper"]` no CSS global. NÃO usar `background-color` nesse seletor — interfere no canvas de renderização dos componentes internos.
- **Logo na sidebar via base64** — carregar o PNG com `Path.read_bytes()` + `base64.b64encode()` e embutir em `<img src="data:image/png;base64,...">`. Não depende de servidor de arquivos estático.
- **Gráficos de rosca (Plotly Pie):** usar `automargin=True` + margens ≥ 24px para evitar corte de labels em fatias pequenas. Usar `textfont=dict(color=[lista_por_fatia])` para texto escuro em fatias amarelas.
- **`st.navigation(position="hidden")`** desabilita completamente o nav automático, evitando flash na troca de páginas. Sidebar definida antes de `pg.run()` é compartilhada automaticamente.
- **Vigência das alíquotas nos JSONs** — o campo `"vigencia"` nos arquivos `aliquotas_icms.json`, `aliquotas_iss.json` e `ncm_aliquotas.json` é hardcoded. Atualizar manualmente quando as tabelas tributárias mudarem.
- **Cache de módulo** — `atualizador_aliquotas.py` usa variáveis de módulo (`_cache_icms` etc.) como cache. Mudanças nos JSONs só aparecem após reiniciar o servidor Streamlit.

## Boas Práticas

- Type hints em todas as funções
- Docstrings em português com exemplo de uso
- `@st.cache_data` para XMLs já processados
- `st.session_state` para estado entre páginas
- `data/` no `.gitignore` (nunca commitar XMLs reais)
- Tabelas de dados: sempre HTML puro — nunca `st.dataframe()` neste projeto

---

## Como Executar

```bash
# Streamlit usa o Conda env na raiz
notafiscal\python.exe -m streamlit run auditoria_fiscal\app.py

# Se porta 8501 ocupada (processo anterior ainda ativo):
notafiscal\python.exe -m streamlit run auditoria_fiscal\app.py --server.port 8502
```

Acesse: http://localhost:8501 (ou 8502)

**Para testar:** faça upload do `NFe_ficticio.zip` na página "Upload NFe"
e clique em "Iniciar Auditoria".
