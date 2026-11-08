# Databricks notebook source
# MAGIC %md
# MAGIC # 📊 PulseIFData - Exportador para Delta Lake & Unity Catalog
# MAGIC
# MAGIC Varre os datasets gerados em `data/` e `data/processed/` (16 relatórios IFData, cadastro,
# MAGIC série histórica e derivadas) e os grava como tabelas **Delta** no Unity Catalog.
# MAGIC
# MAGIC **Atenção:** os datasets são históricos completos e reescritos a cada execução, por isso o modo
# MAGIC padrão é `overwrite` (evita duplicar linhas). Colunas identificadoras (`CodInst`, `Conta`, CNPJs...)
# MAGIC são lidas como **string** para preservar zeros à esquerda (ex.: `00068987`).

# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Catálogo e Schema de Destino

# COMMAND ----------
try:
    _ = dbutils  # noqa: F821
except NameError:
    from pyspark.dbutils import DBUtils
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.getOrCreate()
    dbutils = DBUtils(spark)

dbutils.widgets.text("catalog", "pulsedatalabs", "Catálogo (Unity Catalog)")
dbutils.widgets.text("database", "ifdata", "Schema")
dbutils.widgets.dropdown("write_mode", "overwrite", ["overwrite", "append"], "Modo de Escrita")
dbutils.widgets.dropdown("include_processed", "true", ["true", "false"], "Incluir data/processed/")

catalog = str(dbutils.widgets.get("catalog") or "").strip()
database = str(dbutils.widgets.get("database") or "ifdata").strip()
write_mode = str(dbutils.widgets.get("write_mode") or "overwrite").strip()
include_processed = dbutils.widgets.get("include_processed") == "true"

use_unity_catalog = bool(catalog and catalog.lower() not in ("hive_metastore", "", "none"))
target_schema = f"{catalog}.{database}" if use_unity_catalog else database

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {target_schema}")
print(f"Alvo configurado: {target_schema} (Unity Catalog: {use_unity_catalog}) | modo: {write_mode}")

# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Ingestão dos Datasets para Tabelas Delta

# COMMAND ----------
import os
from pathlib import Path

from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

NOTEBOOK_DIR = Path(os.getcwd())
REPO_ROOT = NOTEBOOK_DIR.parent.parent
DATA_DIR = REPO_ROOT / "data"

# Colunas identificadoras que NUNCA devem ser inferidas como número (zeros à esquerda).
STRING_COLS = {
    "CodInst", "Conta", "Grupo", "Data", "DataInicioAtividade", "Tcb", "Td", "Tc",
    "CnpjInstituicaoLider", "CodConglomeradoFinanceiro", "CodConglomeradoPrudencial",
    "Conglomerado", "cnpj", "cod_inst",
}

search_dirs = [DATA_DIR] + ([DATA_DIR / "processed"] if include_processed else [])
data_files = []
for d in search_dirs:
    for ext in ("*.csv.gz", "*.csv"):
        data_files.extend(d.glob(ext))
data_files = sorted(set(data_files), key=lambda f: f.name)

print(f"{len(data_files)} arquivos encontrados")


def table_name_for(path: Path) -> str:
    name = path.name
    for ext in (".csv.gz", ".csv"):
        if name.endswith(ext):
            name = name[: -len(ext)]
            break
    return name.lower().replace("-", "_").replace(" ", "_")


def read_csv_typed(path: Path):
    """Infere o schema e força STRING_COLS para string antes da leitura final."""
    inferred = (
        spark.read.format("csv")  # noqa: F821
        .option("header", "true")
        .option("inferSchema", "true")
        .load(str(path))
        .schema
    )
    fields = [
        StructField(f.name, StringType(), True) if f.name in STRING_COLS else f
        for f in inferred.fields
    ]
    return (
        spark.read.format("csv")  # noqa: F821
        .option("header", "true")
        .schema(StructType(fields))
        .load(str(path))
    )


total_ok, total_err = 0, 0
for dfile in data_files:
    target_table = f"{target_schema}.{table_name_for(dfile)}"
    try:
        df = read_csv_typed(dfile).withColumn("_ingested_at", F.current_timestamp())
        (
            df.write.format("delta")
            .mode(write_mode)
            .option("overwriteSchema", "true" if write_mode == "overwrite" else "false")
            .option("mergeSchema", "true" if write_mode == "append" else "false")
            .saveAsTable(target_table)
        )
        n = spark.table(target_table).count()  # noqa: F821
        print(f"✓ {target_table} ({n:,} registros)")
        total_ok += 1
    except Exception as e:
        print(f"✗ Erro ao carregar {dfile.name} em {target_table}: {e}")
        total_err += 1

print(f"\nConcluído! {total_ok} tabelas Delta sincronizadas, {total_err} erro(s).")
