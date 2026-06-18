import calendar
import sys
from pathlib import Path
import polars as pl
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.base import get_logger
from scripts.utils.ux import banner, print_done, print_warn, print_skip, section

log = get_logger("normalizer")


def _carregar_settings() -> dict:
    settings_path = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _carregar_mapeamento_semantico(mapping_path: Path) -> dict[str, dict]:
    if not mapping_path.exists():
        log.warning(f"Mapeamento semântico não encontrado: {mapping_path}")
        return {}

    df = pd.read_csv(mapping_path, dtype=str)
    mapping = {}
    for _, row in df.iterrows():
        conta = str(row.get("conta_cosif", "")).strip()
        if conta:
            mapping[conta] = {
                "campo": row.get("campo_semantico", "").strip(),
                "relatorio": row.get("relatorio", "").strip(),
                "nome_coluna": row.get("nome_coluna", "").strip(),
            }
    log.info(f"Mapeamento semântico: {len(mapping)} contas COSIF")
    return mapping


def _pivotar_por_conta_pl(df: pl.DataFrame, mapping: dict[str, dict]) -> pl.DataFrame:
    """
    Transforma linhas (IF × período × conta) em colunas (contas viram campos) usando Polars.
    """
    if "Conta" not in df.columns or "Saldo" not in df.columns:
        log.warning("Colunas 'Conta' ou 'Saldo' ausentes — pulando pivot")
        return df

    # Sanitizar e converter Saldo para float em Rust
    saldo_clean = (
        pl.col("Saldo")
        .fill_null("0.0")
        .str.strip_chars()
        .str.replace_all(".", "", literal=True)
        .str.replace_all(",", ".", literal=True)
        .str.replace_all(" ", "", literal=True)
    )
    df = df.with_columns(
        pl.coalesce(
            pl.col("Saldo").cast(pl.Float64, strict=False),
            saldo_clean.cast(pl.Float64, strict=False)
        ).fill_null(0.0).alias("Saldo_num")
    )

    # Substituir Conta pelo campo semântico correspondente
    mapping_dict = {k: v["campo"] for k, v in mapping.items() if v.get("campo")}
    df = df.with_columns(
        pl.col("Conta").replace_strict(mapping_dict, default=pl.col("Conta")).alias("campo_semantico")
    )

    group_cols = [c for c in ["CodInst", "AnoMes", "data_base", "TipoInstituicao",
                               "NomeRelatorio", "NumeroRelatorio"]
                  if c in df.columns]

    # Pivot de alta performance em Polars
    pivoted = df.pivot(
        on="campo_semantico",
        index=group_cols,
        values="Saldo_num",
        aggregate_function="sum"
    )

    return pivoted.fill_null(0.0)


def _calcular_indicadores_pl(df: pl.DataFrame) -> pl.DataFrame:
    """Calcula ROE, ROA e outros indicadores de forma vetorizada com Polars."""
    exprs = []

    if "patrimonio_liquido" in df.columns and "lucro_liquido" in df.columns:
        exprs.append(
            pl.when(pl.col("patrimonio_liquido") != 0)
            .then(pl.col("lucro_liquido") / pl.col("patrimonio_liquido") * 4)
            .otherwise(0.0)
            .alias("roe_anualizado")
        )

    if "ativo_total" in df.columns and "lucro_liquido" in df.columns:
        exprs.append(
            pl.when(pl.col("ativo_total") != 0)
            .then(pl.col("lucro_liquido") / pl.col("ativo_total") * 4)
            .otherwise(0.0)
            .alias("roa_anualizado")
        )

    if "resultado_operacional" in df.columns and "ativo_total" in df.columns:
        exprs.append(
            pl.when(pl.col("ativo_total") != 0)
            .then(pl.col("resultado_operacional") / pl.col("ativo_total") * 4)
            .otherwise(0.0)
            .alias("nim_margem_financeira")
        )

    if exprs:
        df = df.with_columns(exprs)

    return df


def _join_cadastro_pl(
    df: pl.DataFrame,
    cadastro_path: Path,
    modo: str = "estrito",
) -> pl.DataFrame:
    """Realiza junção com a tabela de cadastro utilizando Polars."""
    if not cadastro_path.exists():
        log.warning(f"Cadastro não encontrado: {cadastro_path} — pulando join")
        return df

    df_cad = pl.read_csv(cadastro_path, schema_overrides={"CodInst": pl.String})
    if df_cad.is_empty():
        return df

    rename_map = {}
    for col in df_cad.columns:
        col_lower = col.lower()
        if "codinst" in col_lower or "cod_inst" in col_lower:
            rename_map[col] = "CodInst"
        elif "nomeinst" in col_lower or "nome_inst" in col_lower:
            rename_map[col] = "NomeInstituicao"
        elif "segmento" in col_lower:
            rename_map[col] = "Segmento"
        elif "uf" in col_lower:
            rename_map[col] = "UF"
        elif "municipio" in col_lower:
            rename_map[col] = "Municipio"
        elif "conglomerado" in col_lower:
            rename_map[col] = "Conglomerado"

    df_cad = df_cad.rename(rename_map)
    cad_cols = ["CodInst", "NomeInstituicao", "Segmento", "UF", "Municipio", "Conglomerado"]
    if "AnoMes" in df_cad.columns and modo == "estrito":
        cad_cols.append("AnoMes")

    cad_cols = [c for c in cad_cols if c in df_cad.columns]
    df_cad = df_cad.select(cad_cols).unique()

    if modo == "estrito" and "AnoMes" in df_cad.columns:
        df_merged = df.join(df_cad, on=["CodInst", "AnoMes"], how="left")
    else:
        df_cad_unique = df_cad.select([c for c in cad_cols if c != "AnoMes"]).unique(subset=["CodInst"])
        df_merged = df.join(df_cad_unique, on="CodInst", how="left")

    log.info(f"Join cadastro: {len(df)} → {len(df_merged)} linhas")
    return df_merged


def normalizar(
    raw_dir: Path,
    output_path: Path,
    mapping: dict[str, dict],
    cadastro_path: Path | None = None,
) -> pd.DataFrame:
    section("Normalização: raw → processed (pivot semântico)")

    # Busca arquivos Parquet gerados
    raw_files = sorted(raw_dir.glob("ifdata_rel*.parquet"))

    if not raw_files:
        log.warning(f"Nenhum arquivo bruto Parquet em {raw_dir}")
        log.info("Execute a extração primeiro: python run_all.py --scraper-only")
        return pd.DataFrame()

    log.info(f"Lendo {len(raw_files)} arquivos brutos Parquet...")
    df_raw = pl.read_parquet(raw_files)

    if df_raw.is_empty():
        log.error("Nenhum dado para processar.")
        return pd.DataFrame()

    # Geração vetorizada da data base em Polars
    if "AnoMes" in df_raw.columns:
        df_raw = df_raw.with_columns(
            ano = pl.col("AnoMes").str.slice(0, 4),
            mes = pl.col("AnoMes").str.slice(4, 2)
        )
        df_raw = df_raw.with_columns(
            dia = pl.col("mes").replace_strict(
                {"03": "31", "06": "30", "09": "30", "12": "31", "01": "31", "02": "28"},
                default="30"
            )
        )
        df_raw = df_raw.with_columns(
            data_base = pl.col("ano") + "-" + pl.col("mes") + "-" + pl.col("dia")
        ).drop(["ano", "mes", "dia"])

    log.info(f"Raw consolidado: {len(df_raw)} linhas")

    df_pivoted = _pivotar_por_conta_pl(df_raw, mapping)
    log.info(f"Pivoted: {len(df_pivoted)} linhas × {len(df_pivoted.columns)} colunas")

    df_indicadores = _calcular_indicadores_pl(df_pivoted)
    log.info("Indicadores calculados: ROE, ROA, NIM")

    if cadastro_path and cadastro_path.exists():
        df_final = _join_cadastro_pl(df_indicadores, cadastro_path, modo="estrito")
    else:
        df_final = df_indicadores

    # Ordenar colunas
    cols_ordem = ["data_base", "AnoMes", "CodInst", "TipoInstituicao",
                  "NomeInstituicao", "Segmento", "UF", "Conglomerado",
                  "ativo_total", "carteira_credito", "patrimonio_liquido",
                  "lucro_liquido", "passivo_total", "captacoes",
                  "indice_basileia", "roe_anualizado", "roa_anualizado",
                  "nim_margem_financeira"]
    cols_presentes = [c for c in cols_ordem if c in df_final.columns]
    cols_restantes = [c for c in df_final.columns if c not in cols_ordem]
    df_final = df_final.select(cols_presentes + cols_restantes).unique()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_final.write_csv(output_path)

    log.info(
        f"Consolidado: {len(df_final)} linhas × {len(df_final.columns)} colunas"
        f" → {output_path}"
    )

    # Retorna DataFrame pandas para compatibilidade externa
    return df_final.to_pandas()


def main():
    banner("Normalizador IFData", "Pivot semântico + join cadastro + indicadores (Polars)")

    root_dir = Path(__file__).resolve().parents[1]
    settings = _carregar_settings()
    norm_cfg = settings.get("normalization", {})

    raw_dir = root_dir / "data" / "raw"
    output_rel = norm_cfg.get("output", {})
    output_path = root_dir / output_rel.get("dir", "data/processed") / output_rel.get("filename", "ifdata_historical_10y.csv")

    mapping_path = root_dir / "config" / "cosif_semantic_mapping.csv"
    mapping = _carregar_mapeamento_semantico(mapping_path)

    cadastro_path = root_dir / "data" / "cadastro_ifs.csv"

    df = normalizar(raw_dir, output_path, mapping, cadastro_path)

    if not df.empty:
        print_done(
            f"Consolidado: {output_path} "
            f"({len(df)} linhas, {len(df.columns)} colunas)"
        )


if __name__ == "__main__":
    main()
