import calendar
import sys
from pathlib import Path

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


def _parse_periodo(ano_mes: str) -> str:
    try:
        ano = int(ano_mes[:4])
        mes = int(ano_mes[4:])
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        return f"{ano:04d}-{mes:02d}-{ultimo_dia:02d}"
    except (ValueError, IndexError):
        return ano_mes


def _sanitizar_saldo(val) -> float:
    if pd.isna(val) or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(".", "").replace(",", ".").replace(" ", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _pivotar_por_conta(
    df: pd.DataFrame,
    mapping: dict[str, dict],
) -> pd.DataFrame:
    """
    Transforma linhas (IF × período × conta) em colunas (contas viram campos).
    """
    df = df.copy()

    if "Conta" not in df.columns or "Saldo" not in df.columns:
        log.warning("Colunas 'Conta' ou 'Saldo' ausentes — pulando pivot")
        return df

    df["Saldo_num"] = df["Saldo"].apply(_sanitizar_saldo)

    df["campo_semantico"] = df["Conta"].map(
        {k: v["campo"] for k, v in mapping.items()}
    ).fillna(df["Conta"])

    group_cols = [c for c in ["CodInst", "AnoMes", "data_base", "TipoInstituicao",
                               "NomeRelatorio", "NumeroRelatorio"]
                  if c in df.columns]

    pivoted = df.pivot_table(
        index=group_cols,
        columns="campo_semantico",
        values="Saldo_num",
        aggfunc="sum",
    ).reset_index()

    pivoted.columns.name = None
    pivoted = pivoted.fillna(0.0)

    return pivoted


def _calcular_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula ROE, ROA e outros indicadores derivados."""
    df = df.copy()

    if "patrimonio_liquido" in df.columns and "lucro_liquido" in df.columns:
        df["roe_anualizado"] = df.apply(
            lambda r: (r["lucro_liquido"] / r["patrimonio_liquido"] * 4)
            if r["patrimonio_liquido"] != 0 else 0.0,
            axis=1,
        )

    if "ativo_total" in df.columns and "lucro_liquido" in df.columns:
        df["roa_anualizado"] = df.apply(
            lambda r: (r["lucro_liquido"] / r["ativo_total"] * 4)
            if r["ativo_total"] != 0 else 0.0,
            axis=1,
        )

    if "resultado_operacional" in df.columns and "ativo_total" in df.columns:
        df["nim_margem_financeira"] = df.apply(
            lambda r: (r["resultado_operacional"] / r["ativo_total"] * 4)
            if r["ativo_total"] != 0 else 0.0,
            axis=1,
        )

    return df


def _join_cadastro(
    df: pd.DataFrame,
    cadastro_path: Path,
    modo: str = "estrito",
) -> pd.DataFrame:
    """
    Join estrito (A): CodInst + AnoMes.
    Se cadastro_path não existir, retorna df original.
    """
    if not cadastro_path.exists():
        log.warning(f"Cadastro não encontrado: {cadastro_path} — pulando join")
        return df

    df_cad = pd.read_csv(cadastro_path, dtype=str)
    if df_cad.empty:
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

    df_cad = df_cad.rename(columns=rename_map)
    cad_cols = ["CodInst", "NomeInstituicao", "Segmento", "UF", "Municipio", "Conglomerado"]
    cad_cols = [c for c in cad_cols if c in df_cad.columns]

    if modo == "estrito" and "AnoMes" not in df_cad.columns:
        if "Data" in df_cad.columns:
            df_cad["AnoMes"] = df_cad["Data"].astype(str).str[:6]
        else:
            log.warning("Cadastro sem AnoMes — join apenas por CodInst")
            df_merged = df.merge(
                df_cad[cad_cols].drop_duplicates(subset=["CodInst"]),
                on="CodInst", how="left",
            )
            return df_merged

    if modo == "estrito" and "AnoMes" in df_cad.columns:
        join_cols = [c for c in ["CodInst", "AnoMes"] if c in df.columns]
        df_merged = df.merge(df_cad, on=join_cols, how="left", suffixes=("", "_cad"))
    else:
        df_merged = df.merge(
            df_cad[cad_cols].drop_duplicates(subset=["CodInst"]),
            on="CodInst", how="left",
        )

    log.info(f"Join cadastro: {len(df)} → {len(df_merged)} linhas")
    return df_merged


def normalizar(
    raw_dir: Path,
    output_path: Path,
    mapping: dict[str, dict],
    cadastro_path: Path | None = None,
) -> pd.DataFrame:
    section("Normalização: raw → processed (pivot semântico)")

    raw_files = sorted(raw_dir.glob("ifdata_rel*.csv"))
    if not raw_files:
        log.warning(f"Nenhum arquivo bruto em {raw_dir}")
        return pd.DataFrame()

    log.info(f"Lendo {len(raw_files)} arquivos brutos")

    frames = []
    for fpath in raw_files:
        try:
            df = pd.read_csv(fpath, dtype=str, keep_default_na=False)
            if df.empty:
                print_skip(f"{fpath.name} — vazio")
                continue
            if "AnoMes" in df.columns:
                df["data_base"] = df["AnoMes"].apply(_parse_periodo)
            frames.append(df)
        except Exception as e:
            print_warn(f"{fpath.name} — erro: {e}")

    if not frames:
        log.error("Nenhum dado para processar.")
        return pd.DataFrame()

    df_raw = pd.concat(frames, ignore_index=True)
    log.info(f"Raw consolidado: {len(df_raw)} linhas")

    df_pivoted = _pivotar_por_conta(df_raw, mapping)
    log.info(f"Pivoted: {len(df_pivoted)} linhas × {len(df_pivoted.columns)} colunas")

    df_indicadores = _calcular_indicadores(df_pivoted)
    log.info("Indicadores calculados: ROE, ROA, NIM")

    if cadastro_path and cadastro_path.exists():
        df_final = _join_cadastro(df_indicadores, cadastro_path, modo="estrito")
    else:
        df_final = df_indicadores

    cols_ordem = ["data_base", "AnoMes", "CodInst", "TipoInstituicao",
                  "NomeInstituicao", "Segmento", "UF", "Conglomerado",
                  "ativo_total", "carteira_credito", "patrimonio_liquido",
                  "lucro_liquido", "passivo_total", "captacoes",
                  "indice_basileia", "roe_anualizado", "roa_anualizado",
                  "nim_margem_financeira"]
    cols_presentes = [c for c in cols_ordem if c in df_final.columns]
    cols_restantes = [c for c in df_final.columns if c not in cols_ordem]
    df_final = df_final[cols_presentes + cols_restantes]

    df_final = df_final.drop_duplicates().reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(output_path, index=False, encoding="utf-8")

    log.info(
        f"Consolidado: {len(df_final)} linhas × {len(df_final.columns)} colunas"
        f" → {output_path}"
    )

    return df_final


def main():
    banner("Normalizador IFData", "Pivot semântico + join cadastro + indicadores")

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
