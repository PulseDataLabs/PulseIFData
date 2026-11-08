"""
PulseIFData - Databricks Entrypoint Job
=======================================
Script para execução via Databricks Workflows (Python script task).

Executa o pipeline do PulseIFData (extração dos 16 relatórios IFData + cadastro,
normalização, derivadas e catálogo) em um cluster Databricks ou Serverless.

Compatível com:
  1. Databricks Git Folders (Repos)
  2. Workspace Files
  3. sys.argv / argparse para passagem de parâmetros do Job
  4. Databricks Secrets com fallback transparente para os.environ
"""

import argparse
import os
import sys
from pathlib import Path

# ── 1. Garantir que a raiz do repositório está no sys.path ────────────────────
CURRENT_FILE = Path(__file__).resolve()
REPO_ROOT = CURRENT_FILE.parent.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# CWD na raiz do repositório para que os caminhos relativos funcionem
os.chdir(str(REPO_ROOT))

SECRET_KEYS = [
    "ORACLE_DB_DSN",
    "ORACLE_DB_USER",
    "ORACLE_DB_PASSWORD",
    "ORACLE_DB_WALLET_PASSWORD",
    "ORACLE_DB_WALLET_BASE64",
]


# ── 2. Carregar segredos do Databricks / .env ─────────────────────────────────
def load_databricks_secrets(scope_name: str = "pulseifdata") -> None:
    """Carrega segredos do .env local ou do Databricks Secret Scope para os.environ."""
    try:
        from dotenv import load_dotenv

        env_file = REPO_ROOT / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    except Exception:
        pass
    try:
        from pyspark.dbutils import DBUtils
        from pyspark.sql import SparkSession

        spark = SparkSession.builder.getOrCreate()
        dbutils = DBUtils(spark)

        for key in SECRET_KEYS:
            if not os.getenv(key):
                try:
                    val = dbutils.secrets.get(scope=scope_name, key=key)
                    if val:
                        os.environ[key] = val
                except Exception:
                    pass
    except Exception:
        pass


# ── 3. Extração de Wallet Oracle se fornecida em base64 ───────────────────────
def setup_oracle_wallet() -> None:
    wallet_b64 = os.getenv("ORACLE_DB_WALLET_BASE64")
    if wallet_b64 and not os.getenv("ORACLE_DB_WALLET_DIR"):
        import base64
        import zipfile
        from io import BytesIO

        wallet_dir = Path("/tmp/oracle_wallet")
        wallet_dir.mkdir(parents=True, exist_ok=True)
        zip_data = base64.b64decode(wallet_b64)
        with zipfile.ZipFile(BytesIO(zip_data)) as z:
            z.extractall(wallet_dir)
        os.environ["ORACLE_DB_WALLET_DIR"] = str(wallet_dir)
        print(f"✓ Oracle Wallet configurada em: {wallet_dir}")


# ── 4. Parâmetros e execução ──────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="🏦 PulseIFData – Databricks Workflow Job Runner")
    parser.add_argument("--scraper-only", action="store_true", help="Apenas extração")
    parser.add_argument("--normalize-only", action="store_true", help="Apenas normalização")
    parser.add_argument("--derivadas-only", action="store_true", help="Apenas métricas derivadas")
    parser.add_argument("--sequential", action="store_true", help="Execução sequencial")
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Pula a carga no Oracle DB (recomendado quando o destino é só o Delta Lake)",
    )
    parser.add_argument(
        "--secret-scope",
        default="pulseifdata",
        help="Nome do Databricks Secret Scope (padrão: pulseifdata)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    load_databricks_secrets(args.secret_scope)
    setup_oracle_wallet()

    if args.skip_db:
        os.environ["SKIP_ORACLE_DB"] = "1"

    import run_all

    run_all.main(
        scraper_only=args.scraper_only,
        normalize_only=args.normalize_only,
        derivadas_only=args.derivadas_only,
        sequential=args.sequential,
    )


if __name__ == "__main__":
    main()
