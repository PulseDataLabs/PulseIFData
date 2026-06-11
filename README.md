# PulseIFData

**Inteligência do Sistema Financeiro Nacional** — dados do IFData/BACEN estruturados, normalizados e entregues para uso institucional.

[![Coleta e Atualizacao IFData](https://github.com/PulseDataLabs/PulseIFData/actions/workflows/main.yml/badge.svg)](https://github.com/PulseDataLabs/PulseIFData/actions/workflows/main.yml)

---

## O problema

O IFData do BACEN é **público**, mas a experiência de uso é terrível:

- A API OData exige queries manuais por **relatório** × **trimestre** × **tipo de instituição**
- Sem série histórica consolidada — cada query retorna um trimestre isolado
- Paginação necessária para relatórios com muitos registros
- Quebras de série no plano COSIF (ex: mar/2025) que quebram comparações históricas
- Endpoint `IfDataCadastro` retorna HTTP 500 — cadastro de IFs está indisponível via API

O PulseIFData resolve isso: coleta, normaliza e entrega tudo em schema fixo.

## Posicionamento no portfólio PulseDataLabs

| Produto | Cobre | Gap |
|---------|-------|-----|
| **PulseFlat** | Macro e mercado (taxas, câmbio, fundos, índices) | Não cobre instituições financeiras individuais |
| **PulseRatings** | Risco de crédito externo (S&P, Moody's, Fitch) | Não cobre o SFN doméstico |
| **PulseIFData** | Inteligência competitiva do SFN | **Complementar** — inadimplência, market share, crescimento por IF |

Cruzamento exclusivo: PulseIFData + PulseFlat (SELIC, CDI) → **NIM ajustado ao ciclo de juros**.

## Arquitetura

```
PulseIFData/
├── scrapers/
│   ├── utils/
│   │   ├── base.py             # BaseScraper (herdado do ecossistema)
│   │   └── odata.py            # Paginação OData, checkpointing, períodos
│   ├── bacen_ifdata.py         # Scraper financeiro (11 relatórios × 3 tipos)
│   └── bacen_ifdata_cadastro.py # Scraper de cadastro (fallback CodInst)
├── scripts/
│   ├── normalizer.py           # Pivot semântico + indicadores + join cadastro
│   ├── derivadas.py            # Market share, HHI, rankings, variações QoQ/YoY
│   ├── enriquecer_cadastro.py  # Enriquecimento de cadastro com fallback
│   ├── generate_catalog.py     # Gera datasets.json
│   └── utils/ux.py             # Terminal UX colorida
├── utils/base.py               # salvar_csv, monkey-patch HTTP, helpers
├── config/
│   ├── settings.yaml           # Endpoints OData, relatórios, range temporal
│   ├── cosif_semantic_mapping.csv  # 35 contas COSIF mapeadas semanticamente
│   └── cosif_de_para.csv       # Equivalências para quebra COSIF 2025
├── data/
│   ├── raw/                    # CSVs trimestrais brutos (checkpoint)
│   ├── processed/              # Série consolidada pivoted + indicadores
│   ├── cadastro_ifs.csv        # Cadastro enriquecido de IFs
│   ├── datasets.json           # Catálogo de datasets
│   └── pipeline_status.json    # Status da última execução
├── .github/workflows/main.yml  # GitHub Actions (cron trimestral + Pages)
├── run_all.py                  # Orquestrador do pipeline
├── index.html                  # Dashboard estático (GitHub Pages)
└── tests/                      # Testes unitários
```

### Pipeline

```mermaid
flowchart LR
    A[API OData olinda.bcb.gov.br] --> B[scrapers/bacen_ifdata.py]
    B --> C[data/raw/ checkpoints]
    C --> D[scripts/normalizer.py]
    C --> E[scripts/enriquecer_cadastro.py]
    D --> F[data/processed/ifdata_historical_10y.csv]
    D --> G[scripts/derivadas.py]
    G --> H[data/derivadas_*.csv]
    E --> I[data/cadastro_ifs.csv]
    F --> J[index.html (dashboard)]
    H --> J
    I --> J
```

**Fluxo:**

1. **Detecção**: pipeline cron do GitHub Actions verifica periodicamente novo trimestre
2. **Extração**: itera por ano → trimestre → relatório → tipo de IF, com paginação `$top`/`$skip` e checkpointing em `data/raw/`
3. **Normalização**: pivota COSIF accounts → colunas semânticas, calcula ROE/ROA/NIM, join cadastro
4. **Derivadas**: market share, HHI (0–10000), rankings, variações QoQ + YoY
5. **Publicação**: CSVs versionados no git, dashboard via GitHub Pages

### Relatórios disponíveis

| # | Relatório | Categoria |
|---|-----------|-----------|
| 1 | Resumo | Balanço |
| 2 | Ativo | Balanço |
| 3 | Passivo | Balanço |
| 4 | Demonstração de Resultado | Balanço |
| 5 | Informações de Capital | Balanço |
| 6 | Segmentação | Cadastro |
| 7 | Carteira de Crédito por indexador | Crédito |
| 8 | Carteira de Crédito por nível de risco | Crédito |
| 9 | Carteira de Crédito por região geográfica | Crédito |
| 11 | Carteira de Crédito PF — modalidade e prazo | Crédito |
| 13 | Carteira de Crédito PJ — modalidade e prazo | Crédito |

Série histórica desde **2014** (10+ anos), atualização trimestral.

### Datasets gerados

| Dataset | Descrição | Categoria |
|---------|-----------|-----------|
| `cadastro_ifs.csv` | Cadastro de IFs (CodInst + nomes conhecidos) | cadastro |
| `ifdata_historical_10y.csv` | Série consolidada pivoted com indicadores | balanco |
| `derivadas_market_share.csv` | Participação de mercado por IF (%) | derivadas |
| `derivadas_hhi.csv` | HHI de concentração (0–10000) | derivadas |
| `derivadas_rankings.csv` | Rankings por ativo total e carteira | derivadas |
| `derivadas_var.csv` | Variações QoQ e YoY | derivadas |

### Limitações conhecidas

- **IfDataCadastro** (endpoint de cadastro de IFs) retorna HTTP 500 para todos os períodos testados. O pipeline usa fallback extraindo CodInst dos dados financeiros + mapeamento manual das maiores IFs.
- **Relatórios de crédito** (7–13) retornam vazios para tipo 1 (conglomerados prudenciais).
- **COSIF** sofreu quebra de série em março/2025 — `config/cosif_de_para.csv` mantém as equivalências.

## Instalação

```bash
# Clone
git clone https://github.com/PulseDataLabs/PulseIFData.git
cd PulseIFData

# Dependências
pip install -r requirements.txt

# Pipeline completo (extração + normalização + derivadas + catálogo)
python run_all.py

# Apenas extração
python run_all.py --scraper-only

# Apenas normalização
python run_all.py --normalize-only

# Apenas derivadas
python run_all.py --derivadas-only

# Regenerar catálogo
python run_all.py --generate-catalog
```

## Consumo dos dados

```python
import pandas as pd

# Série histórica consolidada
url = "https://raw.githubusercontent.com/PulseDataLabs/PulseIFData/main/data/processed/ifdata_historical_10y.csv"
df = pd.read_csv(url)

# Dataset específico
url_ranking = "https://raw.githubusercontent.com/PulseDataLabs/PulseIFData/main/data/derivadas_rankings.csv"
df_rank = pd.read_csv(url_ranking)
```

Os CSVs seguem o padrão: **UTF-8, separador vírgula, decimal ponto, datas YYYY-MM-DD**.

## Licença

Dados públicos do [IFData/BACEN](https://www3.bcb.gov.br/ifdata/) — ODbL.
Código sob licença MIT.
