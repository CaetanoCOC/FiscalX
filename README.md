Cole o conteúdo abaixo direto no README.md do GitHub
========================================================

---

<div align="center">

<img src="auditoria_fiscal/static/fiscalx_logo_new.png" width="120" height="120" style="border-radius:20px"/>

# FiscalX — Auditoria Fiscal Automatizada de NFe

**Transforme XMLs de Notas Fiscais em relatórios de auditoria tributária em segundos.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-00CDCD?style=for-the-badge)](LICENSE)

[![Acessar App](https://img.shields.io/badge/🚀_ACESSAR_APP_ONLINE-00CDCD?style=for-the-badge&logoColor=white)](https://fiscalx.streamlit.app)

[📋 Funcionalidades](#-funcionalidades) • [📦 Como Executar](#-como-executar) • [👤 Autor](#-autor)

</div>

---

## 🧾 O que é o FiscalX?

O **FiscalX** é um sistema profissional de auditoria fiscal desenvolvido em Python com interface Streamlit. Ele lê XMLs de **Notas Fiscais Eletrônicas (NFe layout 4.0)**, valida a tributação declarada, detecta inconsistências, apura impostos por período e gera relatórios exportáveis — tudo automaticamente.

> 💼 Desenvolvido como **portfólio técnico** para vagas de **Auditor Fiscal** e **Analista Fiscal**, demonstrando domínio de legislação tributária aliado a desenvolvimento de software.

---

## ✨ Funcionalidades

### 🔍 Auditoria Tributária — 12 Validações Automáticas

| Código | Validação | Severidade |
|--------|-----------|------------|
| V01 | CFOP vs tipo de operação (entrada/saída) | 🔴 CRÍTICO |
| V02 | CFOP vs destino (interna/interestadual/exterior) | 🔴 CRÍTICO |
| V03 | Alíquota ICMS declarada vs esperada | 🔴 CRÍTICO |
| V04 | Base de cálculo ICMS | 🟡 ALERTA |
| V05 | Valor ICMS calculado vs declarado | 🔴 CRÍTICO |
| V06 | CST vs regime tributário (CRT=1→CSOSN / CRT=3→CST) | 🔴 CRÍTICO |
| V07 | CFOP vs CST PIS/COFINS | 🟡 ALERTA |
| V08 | Alíquota PIS/COFINS por regime (cumulativo/não-cumulativo) | 🟡 ALERTA |
| V09 | NCM vs alíquota IPI (TIPI) | 🟡 ALERTA |
| V10 | Duplicidade de chave de acesso | 🔴 CRÍTICO |
| V11 | Nota fora do prazo de emissão (> 24h) | 🔵 INFORMATIVO |
| V12 | Soma dos itens vs total da nota | 🔴 CRÍTICO |

### 🚨 Detector de Anomalias — 7 Detectores

| Código | Anomalia |
|--------|----------|
| A01 | Nota de alto valor (outlier estatístico) |
| A02 | Salto numérico na sequência de NFs |
| A03 | CNPJ emitindo de múltiplos estados |
| A04 | Devolução sem nota de origem |
| A05 | NCM incongruente com a descrição do produto |
| A06 | Concentração de fornecedor > 40% do volume |
| A07 | Emissão fora do horário comercial |

### 🔗 Conciliação DE PARA — Novo!

Cruza os dados das NFes com o **cadastro interno da empresa (ERP)**:

- **V13** — Fornecedor na NFe não mapeado no cadastro interno
- **V14** — NCM declarado diverge do NCM esperado no cadastro
- **V15** — CFOP diverge do CFOP padrão para o produto

### 📊 Apuração de Impostos

- Apuração de **ICMS** (débitos, créditos e saldo) por CFOP
- Apuração de **PIS e COFINS** separados por regime
- Apuração de **ISS** por município com verificação de retenção
- Simulação de **DARF** para pagamento
- Comparativo entre períodos

### 📄 Relatórios

- Exportação em **Excel (.xlsx)** e **CSV**
- Relatório consolidado de inconsistências
- Relatório de divergências DE PARA

---

## 🖥️ Interface

```
📊 Dashboard          → KPIs gerais, gráfico de severidades, status de alíquotas
📂 Upload NFe         → Upload de XMLs avulsos ou .zip com múltiplas notas
📈 Dashboard Fiscal   → Evolução mensal, heatmap por UF, treemap CFOP, top fornecedores
🔎 Auditoria Detalhada → Tabela completa de inconsistências com filtros e anomalias
🧾 Apuração Impostos  → Cards débito/crédito/saldo, comparativo entre períodos
📄 Relatório & Exportar → Preview e download em Excel/CSV
🔗 Conciliação DE PARA → Upload do cadastro interno e cruzamento com as NFes
```

---

## 🗂️ Estrutura do Projeto

```
FiscalX/
├── requirements.txt              ← dependências para deploy
├── packages.txt                  ← libs de sistema (lxml no Linux)
├── NFe_ficticio.zip              ← 20 NFes fictícias para demo
├── NFe_depara_teste.zip          ← 5 NFes para testar o DE PARA
├── DEPARA.zip                    ← planilhas de cadastro interno (DE PARA)
├── nfe_teste_unica.xml           ← 1 NFe isolada para teste rápido
└── auditoria_fiscal/
    ├── app.py                    ← roteador principal (Streamlit)
    ├── home.py                   ← página Dashboard
    ├── requirements.txt
    ├── config/                   ← tabelas tributárias (ICMS, ISS, NCM, CFOP, CST)
    ├── core/
    │   ├── parser_nfe.py         ← leitura de XML NFe 4.0
    │   ├── motor_validacao.py    ← 12 validações tributárias
    │   ├── detector_anomalias.py ← 7 detectores de anomalias
    │   ├── apuracao.py           ← apuração ICMS/PIS/COFINS/ISS
    │   ├── conciliador_cadastro.py ← conciliação DE PARA (V13-V15)
    │   └── atualizador_aliquotas.py
    ├── pages/                    ← 6 páginas da aplicação
    ├── utils/                    ← constantes, tema, formatadores
    └── tests/                    ← testes unitários + XMLs de exemplo
```

---

## ⚙️ Regras Tributárias Implementadas

- **ICMS Interestadual:** 4% (importados) · 7% (Sul/SE → N/NE/CO) · 12% (demais pares)
- **DIFAL (EC 87/2015):** operações para consumidor final não contribuinte
- **FCP:** adicional 2% nos estados configurados
- **Simples Nacional (CRT=1):** CSOSN obrigatório; sem destaque de ICMS
- **PIS/COFINS Cumulativo:** 0,65% / 3,00% (Lucro Presumido)
- **PIS/COFINS Não-cumulativo:** 1,65% / 7,60% (Lucro Real)
- **ISS:** 2% mínimo · 5% máximo (LC 116/2003)

---

## 🚀 Como Executar

### Requisitos

- Python 3.10+
- Ambiente virtual (Conda ou venv)

### Instalação

```bash
# Clone o repositório
git clone https://github.com/CaetanoCOC/FiscalX.git
cd FiscalX

# Crie e ative o ambiente
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Instale as dependências
pip install -r requirements.txt

# Execute
streamlit run auditoria_fiscal/app.py
```

Acesse: **http://localhost:8501**

### Testando rapidamente

1. Vá em **Upload NFe**
2. Faça upload do `NFe_ficticio.zip` (20 notas fictícias)
3. Clique em **Iniciar Auditoria**
4. Explore os resultados nas demais páginas

---

## 🌐 Deploy

A aplicação está disponível online via **Streamlit Community Cloud**:

> 🔗 **[fiscalx.streamlit.app](https://fiscalx.streamlit.app)**

---

## 🛠️ Stack Tecnológica

| Tecnologia | Uso |
|-----------|-----|
| **Python 3.10+** | Linguagem principal |
| **Streamlit** | Interface web |
| **Pandas** | Manipulação de dados |
| **lxml** | Parsing de XML NFe |
| **Plotly** | Gráficos interativos |
| **openpyxl** | Exportação Excel |
| **ReportLab** | Geração de PDF |
| **Pydantic** | Validação de dados |

---

## 📌 Sobre o Projeto

Este projeto foi desenvolvido para demonstrar como a **automação fiscal com Python** pode:

- Reduzir drasticamente o tempo de revisão de escrituração
- Eliminar erros humanos na conferência de alíquotas e CFOPs
- Dar ao profissional fiscal uma ferramenta de análise que antes só existia em ERPs caros
- Conciliar o cadastro interno com os dados declarados pelos fornecedores

> *"Conciliar a área tributária com desenvolvimento pode reduzir horas de trabalho."*
> — Feedback recebido no LinkedIn ✅

---

## 👤 Autor

**Bruno Caetano**
Analista Fiscal | Python Developer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/bcaetano-datascience/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/CaetanoCOC)
[![FiscalX App](https://img.shields.io/badge/🔗_App_Online-FF4B4B?style=for-the-badge)](https://fiscalx.streamlit.app)

---

<div align="center">

**⭐ Se este projeto foi útil, deixe uma estrela no repositório!**

</div>
