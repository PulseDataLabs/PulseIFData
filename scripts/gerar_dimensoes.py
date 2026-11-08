#!/usr/bin/env python
# coding: utf-8
"""
Gera tabelas dimensionais mestres do PulseIFData:
  1. data/dim_conta.csv:
     Dicionário de dados oficial de todas as contas contábeis dos 16 relatórios
     do IFData (COSIF, Res. 2.682, Res. 4.966), com vigência (min/max_periodo)
     e descrições sanitizadas.
  2. data/depara_conglomerados.csv:
     Tabela de equivalência entre Conglomerados Financeiros (Tipo 2, vigentes até 202412)
     e Conglomerados Prudenciais (Tipo 1, vigentes a partir de 202503), garantindo
     continuidade de séries temporais de 2014 a 2026+.
"""
import argparse
import sys
import time
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.utils.ux import (
    b_green,
    bold,
    cyan,
    dim,
    green,
    section,
    white,
    yellow,
)
from utils.base import get_logger

log = get_logger("gerar_dimensoes")


def gerar_dim_conta(data_dir: Path) -> pl.DataFrame:
    """
    Gera data/dim_conta.csv a partir de todos os relatórios bacen_*.csv.gz.
    """
    arquivos = sorted(data_dir.glob("bacen_*.csv.gz"))
    if not arquivos:
        log.warning("Nenhum arquivo bacen_*.csv.gz encontrado para gerar dim_conta.")
        return pl.DataFrame()

    t0 = time.time()
    frames = []
    cols_necessarias = ["NumeroRelatorio", "NomeRelatorio", "Conta", "NomeColuna", "DescricaoColuna", "AnoMes"]

    for arq in arquivos:
        try:
            df = pl.read_csv(arq, infer_schema_length=0)
            if not all(c in df.columns for c in cols_necessarias):
                continue

            # Sanitizar textos
            df_clean = (
                df.filter(pl.col("Conta").is_not_null() & (pl.col("Conta") != ""))
                .with_columns([
                    pl.col("NumeroRelatorio").cast(pl.String).str.strip_chars().alias("NumeroRelatorio"),
                    pl.col("NomeRelatorio").cast(pl.String).str.strip_chars().alias("NomeRelatorio"),
                    pl.col("Conta").cast(pl.String).str.strip_chars().alias("Conta"),
                    pl.col("NomeColuna").cast(pl.String).fill_null("").str.replace_all(r"[\r\n]+", " ").str.strip_chars().alias("NomeColuna"),
                    pl.col("DescricaoColuna").cast(pl.String).fill_null("").str.replace_all(r"[\r\n]+", " ").str.strip_chars().alias("DescricaoColuna"),
                    pl.col("AnoMes").cast(pl.Int64, strict=False).alias("periodo"),
                ])
            )

            agg = (
                df_clean.group_by(["NumeroRelatorio", "NomeRelatorio", "Conta", "NomeColuna", "DescricaoColuna"])
                .agg([
                    pl.col("periodo").min().alias("min_periodo"),
                    pl.col("periodo").max().alias("max_periodo"),
                    pl.len().alias("total_ocorrencias"),
                ])
            )
            frames.append(agg)
        except Exception as e:
            log.warning(f"Erro ao processar {arq.name} para dim_conta: {e}")

    if not frames:
        return pl.DataFrame()

    dim_df = (
        pl.concat(frames, how="vertical")
        .with_columns(pl.col("NumeroRelatorio").cast(pl.Int64, strict=False).alias("num_rel_int"))
        .sort(["num_rel_int", "Conta", "min_periodo"])
        .drop("num_rel_int")
    )

    out_path = data_dir / "dim_conta.csv"
    dim_df.write_csv(out_path)
    elapsed = time.time() - t0
    log.info(f"dim_conta.csv gerado com sucesso: {len(dim_df)} contas mapeadas ({elapsed:.2f}s)")
    return dim_df


def gerar_depara_conglomerados(data_dir: Path) -> pl.DataFrame:
    """
    Gera data/depara_conglomerados.csv a partir de data/cadastro_ifs.csv.
    """
    cad_path = data_dir / "cadastro_ifs.csv"
    if not cad_path.exists():
        log.warning(f"Cadastro {cad_path.name} não encontrado para gerar de-para de conglomerados.")
        return pl.DataFrame()

    t0 = time.time()
    df = pl.read_csv(cad_path, infer_schema_length=5000)

    col_periodo = "Data" if "Data" in df.columns else ("AnoMes" if "AnoMes" in df.columns else None)
    if not col_periodo:
        log.warning("Coluna de período não encontrada no cadastro.")
        return pl.DataFrame()

    # Normalizar campos de conglomerado e CNPJ líder
    df_norm = (
        df.filter(
            (pl.col("CodConglomeradoFinanceiro").is_not_null() & (pl.col("CodConglomeradoFinanceiro") != ""))
            | (pl.col("CodConglomeradoPrudencial").is_not_null() & (pl.col("CodConglomeradoPrudencial") != ""))
        )
        .with_columns([
            pl.col(col_periodo).cast(pl.Int64).alias("periodo"),
            pl.col("CodConglomeradoFinanceiro").fill_null("").cast(pl.String).str.strip_chars().alias("cod_fin"),
            pl.col("CodConglomeradoPrudencial").fill_null("").cast(pl.String).str.strip_chars().alias("cod_prud"),
            pl.col("CnpjInstituicaoLider").fill_null("").cast(pl.String).str.strip_chars().str.zfill(8).alias("cnpj_lider"),
            pl.col("NomeInstituicao").fill_null("").cast(pl.String).str.strip_chars().alias("nome_inst"),
            pl.col("Segmento").fill_null("").cast(pl.String).str.strip_chars().alias("segmento"),
        ])
    )

    max_periodo_global = int(df_norm["periodo"].max())

    # Agrupar por par de conglomerados (cod_fin, cod_prud)
    agg_pairs = (
        df_norm.sort(["periodo", "nome_inst"], descending=[True, False])
        .group_by(["cod_fin", "cod_prud"])
        .agg([
            pl.col("cnpj_lider").filter(pl.col("cnpj_lider") != "00000000").first().fill_null("").alias("cnpj_lider"),
            pl.col("nome_inst").first().alias("nome_conglomerado"),
            pl.col("segmento").filter(pl.col("segmento") != "").first().fill_null("").alias("segmento"),
            pl.col("periodo").min().alias("min_periodo"),
            pl.col("periodo").max().alias("max_periodo"),
            pl.len().alias("total_registros_cadastro"),
        ])
    )

    depara_df = (
        agg_pairs.with_columns([
            (pl.col("max_periodo") == max_periodo_global).alias("ativo_atualmente"),
            pl.when((pl.col("cod_fin") != "") & (pl.col("cod_prud") != ""))
            .then(pl.lit("financeiro_e_prudencial"))
            .when(pl.col("cod_fin") != "")
            .then(pl.lit("apenas_financeiro"))
            .otherwise(pl.lit("apenas_prudencial"))
            .alias("tipo_associacao"),
        ])
        .sort(["tipo_associacao", "nome_conglomerado", "min_periodo"])
    )

    out_path = data_dir / "depara_conglomerados.csv"
    depara_df.write_csv(out_path)
    elapsed = time.time() - t0
    log.info(f"depara_conglomerados.csv gerado com sucesso: {len(depara_df)} conglomerados mapeados ({elapsed:.2f}s)")
    return depara_df


def gerar_todas_dimensoes(data_dir: Path | None = None) -> None:
    if data_dir is None:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    section("Geração de Tabelas Dimensionais (Dim_Conta e De-Para de Conglomerados)")

    print(f"  {dim('Processando dimensão de contas...')}")
    df_contas = gerar_dim_conta(data_dir)
    if not df_contas.is_empty():
        print(f"  {green('✔')} data/dim_conta.csv ({len(df_contas)} contas únicas)")
    else:
        print(f"  {yellow('⚠')} data/dim_conta.csv não gerado")

    print(f"  {dim('Processando de-para de conglomerados...')}")
    df_depara = gerar_depara_conglomerados(data_dir)
    if not df_depara.is_empty():
        pares_completos = df_depara.filter(pl.col("tipo_associacao") == "financeiro_e_prudencial").shape[0]
        print(
            f"  {green('✔')} data/depara_conglomerados.csv ({len(df_depara)} mapeamentos, "
            f"{pares_completos} pontes completas Financeiro ↔ Prudencial)"
        )
    else:
        print(f"  {yellow('⚠')} data/depara_conglomerados.csv não gerado")
    print()


def main():
    parser = argparse.ArgumentParser(description="Gera tabelas dimensionais mestres do PulseIFData")
    parser.parse_args()
    gerar_todas_dimensoes()


if __name__ == "__main__":
    main()
