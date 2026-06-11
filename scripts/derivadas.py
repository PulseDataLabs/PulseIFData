import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.base import get_logger
from scripts.utils.ux import (
    banner, print_done, print_warn, section,
)

log = get_logger("derivadas")

COLUNAS_PADRAO = {
    "carteira": "carteira_credito",
    "ativo": "ativo_total",
}


def gerar_market_share(
    df: pd.DataFrame,
    output_path: Path,
    col_valor: str = "carteira_credito",
) -> pd.DataFrame:
    section("Market Share")
    df = df.copy()

    if col_valor not in df.columns:
        log.warning(f"coluna '{col_valor}' não encontrada — pulando market share")
        return pd.DataFrame()

    # Market share por IF dentro de cada AnoMes
    df["total_segmento"] = df.groupby("AnoMes")[col_valor].transform("sum")
    df["market_share_pct"] = df.apply(
        lambda r: (r[col_valor] / r["total_segmento"] * 100)
        if r["total_segmento"] != 0 else 0.0,
        axis=1,
    )

    cols = ["data_base", "AnoMes", "CodInst"]
    if "NomeInstituicao" in df.columns:
        cols.append("NomeInstituicao")
    if "Segmento" in df.columns:
        cols.append("Segmento")
    cols.extend([col_valor, "market_share_pct"])

    result = df[cols].copy()
    result = result.sort_values(["AnoMes", "market_share_pct"], ascending=[True, False])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, encoding="utf-8")
    log.info(f"Market share: {len(result)} linhas → {output_path}")
    return result


def gerar_hhi(
    df: pd.DataFrame,
    output_path: Path,
    col_valor: str = "carteira_credito",
) -> pd.DataFrame:
    section("HHI — Concentração de Mercado")
    df = df.copy()

    if col_valor not in df.columns:
        log.warning(f"coluna '{col_valor}' não encontrada — pulando HHI")
        return pd.DataFrame()

    # Market share por IF dentro de cada AnoMes
    df["total_segmento"] = df.groupby("AnoMes")[col_valor].transform("sum")
    df["share"] = df.apply(
        lambda r: (r[col_valor] / r["total_segmento"]) if r["total_segmento"] != 0 else 0.0,
        axis=1,
    )

    # HHI = sum(share²) * 10000 (escala 0–10000)
    hhi = df.groupby("AnoMes").agg(
        hhi=("share", lambda s: (s ** 2).sum() * 10000),
        total_carteira=(col_valor, "sum"),
        numero_ifs=(col_valor, "count"),
    ).reset_index()

    if "data_base" in df.columns:
        data_map = df[["AnoMes", "data_base"]].drop_duplicates(subset="AnoMes")
        hhi = hhi.merge(data_map, on="AnoMes", how="left")

    hhi = hhi.sort_values("AnoMes")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    hhi.to_csv(output_path, index=False, encoding="utf-8")
    log.info(f"HHI: {len(hhi)} trimestres → {output_path}")
    return hhi


def gerar_rankings(
    df: pd.DataFrame,
    output_path: Path,
    col_valor: str = "ativo_total",
) -> pd.DataFrame:
    section("Rankings")
    df = df.copy()

    if col_valor not in df.columns:
        log.warning(f"coluna '{col_valor}' não encontrada — pulando rankings")
        return pd.DataFrame()

    df["ranking"] = df.groupby("AnoMes")[col_valor].rank(ascending=False, method="min").astype(int)

    cols = ["data_base", "AnoMes", "CodInst"]
    if "NomeInstituicao" in df.columns:
        cols.append("NomeInstituicao")
    cols.extend([col_valor, "ranking"])

    result = df[cols].copy()
    result = result.sort_values(["AnoMes", "ranking"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, encoding="utf-8")
    log.info(f"Rankings: {len(result)} linhas → {output_path}")
    return result


def gerar_variacoes(
    df: pd.DataFrame,
    output_path: Path,
    col_valor: str = "carteira_credito",
) -> pd.DataFrame:
    section("Variações QoQ e YoY")
    df = df.copy()

    if col_valor not in df.columns:
        log.warning(f"coluna '{col_valor}' não encontrada — pulando variações")
        return pd.DataFrame()

    df = df.sort_values(["CodInst", "AnoMes"])

    df["var_qoq_pct"] = df.groupby("CodInst")[col_valor].transform(
        lambda s: s.pct_change(periods=1) * 100
    )
    df["var_yoy_pct"] = df.groupby("CodInst")[col_valor].transform(
        lambda s: s.pct_change(periods=4) * 100
    )

    cols = ["data_base", "AnoMes", "CodInst"]
    if "NomeInstituicao" in df.columns:
        cols.append("NomeInstituicao")
    cols.extend([col_valor, "var_qoq_pct", "var_yoy_pct"])

    result = df[cols].copy()
    result = result.sort_values(["CodInst", "AnoMes"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False, encoding="utf-8")
    log.info(f"Variações: {len(result)} linhas → {output_path}")
    return result


def gerar_tudo(
    data_processed_dir: Path,
    output_dir: Path,
) -> dict[str, pd.DataFrame]:
    banner("Métricas Derivadas")

    input_path = data_processed_dir / "ifdata_historical.csv"
    if not input_path.exists():
        log.warning(f"Arquivo processado não encontrado: {input_path}")
        return {}

    df = pd.read_csv(input_path, dtype={"CodInst": str})
    log.info(f"Lido: {input_path} — {len(df)} linhas")

    resultados = {}

    ms = gerar_market_share(df, output_dir / "derivadas_market_share.csv")
    if not ms.empty:
        resultados["market_share"] = ms

    hhi = gerar_hhi(df, output_dir / "derivadas_hhi.csv")
    if not hhi.empty:
        resultados["hhi"] = hhi

    rank = gerar_rankings(df, output_dir / "derivadas_rankings.csv")
    if not rank.empty:
        resultados["rankings"] = rank

    var = gerar_variacoes(df, output_dir / "derivadas_var.csv")
    if not var.empty:
        resultados["variacoes"] = var

    print_done(f"{len(resultados)} métricas geradas")
    return resultados


def main():
    root_dir = Path(__file__).resolve().parents[1]
    data_processed = root_dir / "data" / "processed"
    output_dir = root_dir / "data"

    gerar_tudo(data_processed, output_dir)


if __name__ == "__main__":
    main()
