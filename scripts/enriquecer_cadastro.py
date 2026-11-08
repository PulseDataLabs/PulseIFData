import re
import sys
from pathlib import Path

import pandas as pd
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.bacen_ifdata_cadastro import (
    BacenIfdataCadastroScraper,
    normalizar_df_cadastro,
)
from scrapers.utils.rest_cadastro import (
    baixar_cadastro_unico_mais_recente,
    baixar_cadastro_completo,
    listar_periodos,
)
from utils.base import get_logger, nova_session
from scripts.utils.ux import print_done, print_warn, section

log = get_logger("enriquecer_cadastro")

COLUNAS_SAIDA = ["CodInst", "NomeInstituicao", "Segmento", "UF", "AnoMes"]


def carregar_cadastro_odata_raw(raw_dir: Path) -> pd.DataFrame:
    arquivos = sorted(raw_dir.glob("ifdata_cadastro_*.parquet"), reverse=True)
    if not arquivos:
        return pd.DataFrame()

    frames = []
    for fpath in arquivos:
        try:
            m = re.search(r"ifdata_cadastro_(\d{6})\.parquet$", fpath.name)
            periodo = m.group(1) if m else None
            df_p = pd.read_parquet(fpath)
            if not df_p.empty:
                frames.append(normalizar_df_cadastro(df_p, periodo=periodo))
        except Exception as e:
            log.warning(f"Erro ao ler checkpoint {fpath.name}: {e}")

    if not frames:
        return pd.DataFrame()

    df_all = pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["CodInst", "AnoMes"], keep="first"
    )
    return df_all


def extrair_codinst_de_valores(raw_dir: Path) -> pd.DataFrame:
    log.info("Extraindo CodInst de dados financeiros existentes (Polars)")
    parquet_files = sorted(raw_dir.glob("ifdata_rel*.parquet"))
    if not parquet_files:
        log.warning("Nenhum arquivo Parquet encontrado em data/raw")
        return pd.DataFrame()
    try:
        df = pl.read_parquet(parquet_files, columns=["CodInst"])
        unique_cods = df["CodInst"].drop_nulls().unique().sort()
        return unique_cods.to_frame().to_pandas()
    except Exception as e:
        log.warning(f"Erro ao extrair CodInst via Polars: {e}")
        return pd.DataFrame()


def aplicar_cadastro_rest(df: pd.DataFrame, df_cad: pd.DataFrame) -> pd.DataFrame:
    cad = df_cad.copy()
    if "AnoMes" not in cad.columns:
        cad["AnoMes"] = ""

    cad = cad.drop_duplicates(subset=["CodInst"], keep="last")
    renomear = {}
    for col in cad.columns:
        if "NomeInstituicao" in col:
            renomear[col] = "NomeInstituicao"
        elif col == "Segmento":
            renomear[col] = "Segmento"
        elif col == "UF":
            renomear[col] = "UF"
    cad = cad.rename(columns=renomear)

    cad_cols = [c for c in COLUNAS_SAIDA if c in cad.columns]
    df = df.merge(cad[cad_cols], on="CodInst", how="left")
    return df


def preencher_faltantes(df: pd.DataFrame) -> pd.DataFrame:
    df["NomeInstituicao"] = df.get("NomeInstituicao", pd.Series(dtype=str)).fillna(
        df["CodInst"].apply(lambda c: f"IF {c}")
    )
    df["Segmento"] = df.get("Segmento", pd.Series(dtype=str)).fillna("N/D")
    df["UF"] = df.get("UF", pd.Series(dtype=str)).fillna("")
    return df


def enriquecer(raw_dir: Path, output_path: Path | None = None) -> pd.DataFrame:
    section("Enriquecimento de Cadastro — OData + REST API + Fallback")

    df_odata = carregar_cadastro_odata_raw(raw_dir)
    if df_odata.empty:
        log.info("Nenhum checkpoint OData encontrado em data/raw — executando scraper de cadastro OData")
        try:
            df_odata = BacenIfdataCadastroScraper().fetch()
        except Exception as e:
            log.warning(f"Falha ao buscar cadastro via OData: {e}")

    if df_odata is not None and not df_odata.empty:
        df = df_odata
        print_done(
            f"Cadastro OData consolidado: {len(df)} registros "
            f"({df['CodInst'].nunique()} IFs únicas, "
            f"{df['AnoMes'].nunique() if 'AnoMes' in df.columns else 0} períodos, "
            f"{df['Segmento'].replace('', pd.NA).dropna().nunique() if 'Segmento' in df.columns else 0} segmentos)"
        )
    else:
        df = extrair_codinst_de_valores(raw_dir)
        if df.empty:
            log.error("Nenhum dado de cadastro disponível")
            return df

        log.info(f"Fallback inicial: {len(df)} CodInst extraídos de dados financeiros")

        try:
            df_cad = baixar_cadastro_unico_mais_recente()
            if df_cad is not None and not df_cad.empty:
                log.info(f"Cadastro REST: {df_cad['CodInst'].nunique()} IFs únicas em {df_cad.get('AnoMes','').unique()}")
                df = aplicar_cadastro_rest(df, df_cad)
                n_nomeadas = df["NomeInstituicao"].notna().sum()
                log.info(f"Enriquecidas: {n_nomeadas} IFs com nome via REST")
            else:
                log.warning("REST API sem dados — usando fallback CodInst apenas")
        except Exception as e:
            log.warning(f"REST API falhou: {e} — usando fallback CodInst apenas")

        df = preencher_faltantes(df)
        nomeadas = sum(1 for _ in df[df["NomeInstituicao"].str.len() > 10].iterrows())
        print_done(
            f"Cadastro enriquecido: {len(df)} IFs "
            f"({nomeadas} nomeadas, {df['Segmento'].nunique() if 'Segmento' in df else 0} segmentos)"
        )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8")
        log.info(f"Cadastro salvo: {output_path}")

    # Upload para o Oracle DB se configurado
    try:
        from utils.db import upload_dataframe
        upload_dataframe(df, "CADASTRO_IFS")
    except Exception as e:
        log.warning(f"Não foi possível enviar o cadastro de IFs para o Oracle DB: {e}")

    return df


def main():
    root_dir = Path(__file__).resolve().parents[1]
    raw_dir = root_dir / "data" / "raw"
    output_path = root_dir / "data" / "cadastro_ifs.csv"

    df = enriquecer(raw_dir, output_path)
    if not df.empty:
        print_done(f"{output_path} — {len(df)} IFs ({len(df.columns)} colunas)")
        print(f"  Colunas: {list(df.columns)}")


if __name__ == "__main__":
    main()
