# Databricks notebook source
# MAGIC %md
# MAGIC # 🏦 PulseIFData - Orquestrador Interativo (Databricks)
# MAGIC
# MAGIC Executa e depura o pipeline do **PulseIFData** (16 relatórios IFData + cadastro, normalização e derivadas)
# MAGIC diretamente no Databricks. Escolha as etapas pelos widgets no topo da tela.

# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Instalação de Dependências

# COMMAND ----------
# MAGIC %pip install -r ../../requirements.txt --quiet

# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Parâmetros (Widgets)

# COMMAND ----------
try:
    _ = dbutils  # noqa: F821
except NameError:
    from pyspark.dbutils import DBUtils
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    dbutils = DBUtils(spark)

dbutils.widgets.dropdown(
    "etapa",
    "tudo",
    ["tudo", "extracao", "normalizacao", "derivadas"],
    "Etapa do pipeline",
)
dbutils.widgets.dropdown("mode", "parallel", ["parallel", "sequential"], "Modo de Execução")
dbutils.widgets.dropdown("skip_db", "true", ["true", "false"], "Pular carga no Oracle")
dbutils.widgets.text("secret_scope", "pulseifdata", "Databricks Secret Scope")

# COMMAND ----------
# MAGIC %md
# MAGIC ### 3. Ambiente e Segredos

# COMMAND ----------
import os
import sys
from pathlib import Path

NOTEBOOK_DIR = Path(os.getcwd())
REPO_ROOT = NOTEBOOK_DIR.parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
os.chdir(str(REPO_ROOT))

sys.path.insert(0, str(REPO_ROOT / "databricks"))
from run_pulseifdata_job import load_databricks_secrets, setup_oracle_wallet  # noqa: E402

load_databricks_secrets(dbutils.widgets.get("secret_scope"))  # noqa: F821
setup_oracle_wallet()

if dbutils.widgets.get("skip_db") == "true":  # noqa: F821
    os.environ["SKIP_ORACLE_DB"] = "1"

# COMMAND ----------
# MAGIC %md
# MAGIC ### 4. Execução do Pipeline

# COMMAND ----------
import run_all  # noqa: E402

etapa = dbutils.widgets.get("etapa")  # noqa: F821
sequential = dbutils.widgets.get("mode") == "sequential"  # noqa: F821

run_all.main(
    scraper_only=etapa == "extracao",
    normalize_only=etapa == "normalizacao",
    derivadas_only=etapa == "derivadas",
    sequential=sequential,
)
