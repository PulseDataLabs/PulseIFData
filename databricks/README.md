# 🏦 PulseIFData no Databricks

Execução do pipeline do **PulseIFData** (16 relatórios IFData + cadastro, normalização, derivadas) em **Databricks Workflows** a partir de um **Git Folder**, com exportação opcional para tabelas **Delta / Unity Catalog**. Mesmo modelo do PulseFlat.

## Arquitetura

```text
Databricks Workspace
├── Git Folder: PulseIFData/ (clonado do GitHub)
│   ├── databricks/
│   │   ├── run_pulseifdata_job.py            <-- Python script task do Job
│   │   └── notebooks/
│   │       ├── 01_orchestrator_notebook.py   <-- execução interativa (widgets)
│   │       └── 02_delta_lake_exporter.py     <-- data/ → tabelas Delta
│   ├── run_all.py, scrapers/, scripts/       <-- reutilizados sem mudanças
└── Workflows (Job)
    ├── Task 1: run_pulseifdata_job.py   (extração + normalização + derivadas)
    └── Task 2: 02_delta_lake_exporter   (depende da Task 1)
```

## Configuração

### 1. Git Folder
**Workspace → Create → Git Folder** com `https://github.com/PulseDataLabs/PulseIFData.git`.

### 2. Segredos (opcional, só se for carregar no Oracle)
```bash
databricks secrets create-scope pulseifdata
databricks secrets put-secret pulseifdata ORACLE_DB_DSN
databricks secrets put-secret pulseifdata ORACLE_DB_USER
databricks secrets put-secret pulseifdata ORACLE_DB_PASSWORD
databricks secrets put-secret pulseifdata ORACLE_DB_WALLET_PASSWORD
databricks secrets put-secret pulseifdata ORACLE_DB_WALLET_BASE64
```
Se o destino for só o Delta Lake, use `--skip-db` e dispense os segredos.

### 3. Job agendado
- **Task 1** `run_pipeline` — tipo *Python script*, path `databricks/run_pulseifdata_job.py`, parâmetros: `["--skip-db"]`. Bibliotecas: as de `requirements.txt`.
- **Task 2** `export_delta` — tipo *Notebook*, path `databricks/notebooks/02_delta_lake_exporter`, dependente da Task 1. Parâmetros: `catalog`, `database`, `write_mode`.
- **Agendamento:** o BACEN divulga cada trimestre ~60–90 dias após o fechamento. Um cron semanal/mensal basta, pois os checkpoints em `data/raw/` evitam reprocessar o que já foi coletado.

Flags do runner: `--scraper-only`, `--normalize-only`, `--derivadas-only`, `--sequential`, `--skip-db`, `--secret-scope`.

## Exportação para Delta Lake

O notebook `02_delta_lake_exporter` grava um tabela por arquivo de `data/` e `data/processed/`. Nome da tabela = nome do arquivo (ex.: `bacen_passivo`, `cadastro_ifs`, `derivadas_rankings`, `ifdata_historical`).

- **`write_mode=overwrite` (padrão):** os datasets são históricos completos e reescritos a cada execução; `append` duplicaria linhas.
- **Zeros à esquerda:** `CodInst`, `Conta`, CNPJs e códigos de conglomerado são lidos como **string** (um `00068987` não vira `68987`).
- **Destino padrão:** `pulsedatalabs.ifdata` (Unity Catalog), ajustável nos widgets.

```sql
SELECT AnoMes, CodInst, Conta, Saldo
FROM pulsedatalabs.ifdata.bacen_passivo
WHERE AnoMes = 202606 AND tipo_instituicao_label = 'conglomerado_prudencial';
```

## Observações
- Os checkpoints `data/raw/*.parquet` ficam no Git Folder. Se o cluster não os preservar entre execuções, o pipeline refaz a coleta histórica (lento). Para persistir, mantenha o Git Folder num workspace com armazenamento durável.
- O Oracle pode continuar em paralelo usando os mesmos segredos.
