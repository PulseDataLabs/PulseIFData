#!/usr/bin/env python
# coding: utf-8
"""
Gera versão "lite" do ifdata_historical.csv para consumo via web.

Lê o CSV completo (2GB, 381 colunas), extrai apenas as colunas
usadas pelo dashboard e filtra os últimos N anos.
Resultado < 100MB, adequado para GitHub Raw.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.base import get_logger
from scripts.utils.ux import print_done, section

log = get_logger("lite")


COLUNAS_DASHBOARD = [
    "data_base", "AnoMes", "CodInst", "TipoInstituicao",
    "NomeInstituicao", "Segmento", "UF",
    "ativo_total", "carteira_credito", "patrimonio_liquido",
    "lucro_liquido", "passivo_total", "captacoes",
    "indice_basileia", "roe_anualizado", "roa_anualizado",
    "nim_margem_financeira",
]


def gerar_lite(
    full_path: Path,
    output_path: Path,
    anos: int = 3,
) -> None:
    import pandas as pd

    if not full_path.exists():
        log.error(f"Arquivo completo não encontrado: {full_path}")
        return

    section("Gerando versão lite para web")

    cols_existentes = [c for c in COLUNAS_DASHBOARD if c in pd.read_csv(full_path, nrows=0).columns]
    log.info(f"Lendo {len(cols_existentes)} colunas do CSV completo ({full_path})")

    dtype = {c: str for c in cols_existentes if c in ("CodInst", "AnoMes", "Segmento", "UF", "NomeInstituicao", "data_base", "TipoInstituicao")}

    df = pd.read_csv(
        full_path,
        usecols=cols_existentes,
        dtype=dtype,
        low_memory=True,
    )

    # Se o lite anterior existir, mescla com ele para manter a janela deslizante de 3 anos (incremental)
    if output_path.exists():
        log.info(f"Mesclando com o histórico lite existente ({output_path.name}) para preservar os últimos anos...")
        try:
            df_old_lite = pd.read_csv(output_path, dtype=dtype)
            # Concatenar e remover duplicados mantendo a versão mais nova (a da carga atual)
            df = pd.concat([df_old_lite, df], ignore_index=True)
            df = df.drop_duplicates(subset=["AnoMes", "CodInst", "TipoInstituicao"], keep="last")
        except Exception as e:
            log.warning(f"Não foi possível mesclar com o lite anterior: {e}")

    log.info(f"Total lido/mesclado: {len(df)} linhas")

    df["AnoMes_int"] = df["AnoMes"].astype(str).str[:4].astype(int)
    ano_corte = df["AnoMes_int"].max() - anos + 1
    df_lite = df[df["AnoMes_int"] >= ano_corte].copy()
    df_lite.drop(columns=["AnoMes_int"], inplace=True)
    df_lite.reset_index(drop=True, inplace=True)

    for col in ["ativo_total", "carteira_credito", "patrimonio_liquido",
                 "lucro_liquido", "passivo_total", "captacoes",
                 "indice_basileia", "roe_anualizado", "roa_anualizado",
                 "nim_margem_financeira"]:
        if col in df_lite.columns:
            df_lite[col] = pd.to_numeric(df_lite[col], errors="coerce")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_lite.to_csv(output_path, index=False)

    size_mb = output_path.stat().st_size / 1_000_000
    log.info(
        f"Lite: {len(df_lite)} linhas, {len(df_lite.columns)} colunas, "
        f"{size_mb:.1f}MB → {output_path}"
    )
    print_done(
        f"Versão lite ({anos} anos): {output_path.name} "
        f"({len(df_lite)} linhas, {size_mb:.1f}MB)"
    )


def main():
    root_dir = Path(__file__).resolve().parents[1]
    full_path = root_dir / "data" / "processed" / "ifdata_historical.csv.gz"
    output_path = root_dir / "data" / "processed" / "ifdata_historical_lite.csv"
    gerar_lite(full_path, output_path, anos=3)


if __name__ == "__main__":
    main()
