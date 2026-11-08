#!/usr/bin/env python
# coding: utf-8
"""
Validador de qualidade e integridade dos datasets do PulseIFData.

Verifica:
  1. Cadastro (data/cadastro_ifs.csv): chaves únicas, preenchimento e integridade.
  2. Relatórios IFData (data/bacen_*.csv.gz):
     - Presença das colunas essenciais (AnoMes, CodInst, TipoInstituicao, Conta, Saldo).
     - Unicidade da chave (AnoMes, CodInst, TipoInstituicao, Conta).
     - Ausência de nulos em chaves primárias.
     - Validação de saldo (conversão numérica sem perda).
     - Cobertura temporal e regras de transição regulatória (Res. 2.682 vs 4.966, câmbio, etc.).
  3. Atualização de pipeline_status.json com métricas de Data Quality.
"""
import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import tipos_validos_para_relatorio
from scripts.utils.ux import (
    b_green,
    b_red,
    b_yellow,
    bold,
    cyan,
    dim,
    green,
    red,
    section,
    white,
    yellow,
)
from utils.base import get_logger

log = get_logger("validar_datasets")

RELATORIOS_MAP = {
    "bacen_resumo": "1",
    "bacen_ativo": "2",
    "bacen_passivo": "3",
    "bacen_dre": "4",
    "bacen_informacoes_capital": "5",
    "bacen_segmentacao": "6",
    "bacen_credito_indexador": "7",
    "bacen_credito_nivel_risco": "8",
    "bacen_credito_regiao": "9",
    "bacen_credito_clientes_operacoes": "10",
    "bacen_credito_pf_modalidade_prazo": "11",
    "bacen_credito_pj_cnae": "12",
    "bacen_credito_pj_modalidade_prazo": "13",
    "bacen_credito_pj_porte": "14",
    "bacen_cambio_trimestre": "15",
    "bacen_credito_instrumentos_financeiros": "16",
}


def validar_cadastro(csv_path: Path) -> dict[str, Any]:
    resultado = {
        "dataset": csv_path.name,
        "status": "success",
        "total_linhas": 0,
        "erros": [],
        "avisos": [],
    }

    if not csv_path.exists():
        resultado["status"] = "error"
        resultado["erros"].append(f"Arquivo {csv_path.name} não encontrado.")
        return resultado

    try:
        df = pl.read_csv(csv_path, infer_schema_length=10000)
    except Exception as e:
        resultado["status"] = "error"
        resultado["erros"].append(f"Falha ao ler {csv_path.name}: {e}")
        return resultado

    resultado["total_linhas"] = len(df)
    if len(df) == 0:
        resultado["status"] = "error"
        resultado["erros"].append("Arquivo de cadastro está vazio.")
        return resultado

    # Colunas esperadas
    cols_esperadas = {"CodInst", "NomeInstituicao"}
    cols_faltantes = cols_esperadas - set(df.columns)
    if cols_faltantes:
        resultado["status"] = "error"
        resultado["erros"].append(f"Colunas ausentes no cadastro: {cols_faltantes}")
        return resultado

    col_data = "Data" if "Data" in df.columns else ("AnoMes" if "AnoMes" in df.columns else None)
    if not col_data:
        resultado["status"] = "error"
        resultado["erros"].append("Coluna de período ('Data' ou 'AnoMes') ausente no cadastro.")
        return resultado

    # Nulos em colunas chave
    nulos_cod = df.filter(pl.col("CodInst").is_null() | (pl.col("CodInst").cast(pl.String) == "")).shape[0]
    if nulos_cod > 0:
        resultado["status"] = "error"
        resultado["erros"].append(f"{nulos_cod} registros com CodInst nulo/vazio.")

    # Duplicatas em (CodInst, Data)
    dups = len(df) - len(df.unique(subset=["CodInst", col_data]))
    if dups > 0:
        resultado["status"] = "warning"
        resultado["avisos"].append(f"{dups} registros duplicados na chave (CodInst, {col_data}).")

    return resultado


def validar_relatorio(
    csv_gz_path: Path,
    relatorio_id: str,
    strict_periods: bool = True,
) -> dict[str, Any]:
    resultado = {
        "dataset": csv_gz_path.name,
        "relatorio_id": relatorio_id,
        "status": "success",
        "total_linhas": 0,
        "min_periodo": None,
        "max_periodo": None,
        "periodos_count": 0,
        "erros": [],
        "avisos": [],
    }

    if not csv_gz_path.exists():
        resultado["status"] = "error"
        resultado["erros"].append(f"Arquivo {csv_gz_path.name} não encontrado.")
        return resultado

    try:
        df = pl.read_csv(csv_gz_path, infer_schema_length=0)
    except Exception as e:
        resultado["status"] = "error"
        resultado["erros"].append(f"Falha ao ler {csv_gz_path.name}: {e}")
        return resultado

    resultado["total_linhas"] = len(df)
    if len(df) == 0:
        resultado["status"] = "error"
        resultado["erros"].append("Dataset está vazio.")
        return resultado

    cols_necessarias = {"AnoMes", "TipoInstituicao", "Conta", "Saldo"}
    cols_faltantes = cols_necessarias - set(df.columns)
    if cols_faltantes:
        resultado["status"] = "error"
        resultado["erros"].append(f"Colunas obrigatórias ausentes: {cols_faltantes}")
        return resultado

    # Identificar linhas de instituições vs agregados do sistema (onde CodInst vem vazio do BACEN)
    df_inst = df.filter((pl.col("CodInst").is_not_null()) & (pl.col("CodInst") != ""))
    df_agregados = df.filter(pl.col("CodInst").is_null() | (pl.col("CodInst") == ""))

    # Nulos em campos de chave primária nas instituições
    nulos_chave_inst = df_inst.filter(
        pl.col("AnoMes").is_null()
        | pl.col("TipoInstituicao").is_null()
        | pl.col("Conta").is_null()
    ).shape[0]
    if nulos_chave_inst > 0:
        resultado["status"] = "error"
        resultado["erros"].append(f"{nulos_chave_inst} linhas de instituições com nulos na chave primária.")

    # Unicidade da chave primária das instituições
    dups_inst = len(df_inst) - len(df_inst.unique(subset=["AnoMes", "CodInst", "TipoInstituicao", "Conta"]))
    if dups_inst > 0:
        resultado["status"] = "error"
        resultado["erros"].append(
            f"{dups_inst} registros duplicados na chave primária de instituições (AnoMes, CodInst, TipoInstituicao, Conta)."
        )

    # Unicidade das linhas agregadas do sistema
    if len(df_agregados) > 0:
        dups_agr = len(df_agregados) - len(df_agregados.unique(subset=["AnoMes", "TipoInstituicao", "Conta"]))
        if dups_agr > 0:
            resultado["status"] = "error"
            resultado["erros"].append(f"{dups_agr} registros agregados duplicados.")
        resultado["avisos"].append(f"{len(df_agregados)} registros de totais agregados do sistema (CodInst vazio).")

    # Períodos
    try:
        periodos = sorted(int(p) for p in df["AnoMes"].unique().to_list() if str(p).isdigit())
    except Exception:
        periodos = []

    if periodos:
        resultado["min_periodo"] = periodos[0]
        resultado["max_periodo"] = periodos[-1]
        resultado["periodos_count"] = len(periodos)

        # Regras de fronteira regulatória por relatório
        if relatorio_id == "8":
            # Nível de risco deve terminar em 202412
            periodos_invalidos = [p for p in periodos if p >= 202503]
            if periodos_invalidos:
                resultado["status"] = "error"
                resultado["erros"].append(
                    f"Relatório 8 (Res. 2.682) contém períodos a partir de 202503 ({periodos_invalidos})."
                )
        elif relatorio_id == "16":
            # Instrumentos financeiros (Res. 4.966) inicia em 202503
            periodos_invalidos = [p for p in periodos if p < 202503]
            if periodos_invalidos:
                resultado["status"] = "error"
                resultado["erros"].append(
                    f"Relatório 16 (Res. 4.966) contém períodos antes de 202503 ({periodos_invalidos})."
                )
        elif relatorio_id == "15":
            # Câmbio tipo 4 encerrou em 202306
            periodos_invalidos = [p for p in periodos if p > 202306]
            if periodos_invalidos:
                resultado["avisos"].append(
                    f"Relatório 15 contém períodos posteriores a 202306 ({periodos_invalidos})."
                )
        elif relatorio_id == "6":
            # Segmentação começa em 201703
            periodos_invalidos = [p for p in periodos if p < 201703]
            if periodos_invalidos:
                resultado["status"] = "error"
                resultado["erros"].append(
                    f"Relatório 6 (Segmentação) contém períodos anteriores a 201703 ({periodos_invalidos})."
                )

    # Validar formato de Saldo (amostra de 1000 linhas)
    sample_df = df.head(1000)
    saldo_str = sample_df["Saldo"].fill_null("").str.strip_chars()
    # Filtra saldos não vazios para checar se convertem para número
    saldos_preenchidos = saldo_str.filter(saldo_str != "")
    if len(saldos_preenchidos) > 0:
        saldo_num = (
            saldos_preenchidos
            .str.replace_all(".", "", literal=True)
            .str.replace_all(",", ".", literal=True)
            .cast(pl.Float64, strict=False)
        )
        if saldo_num.null_count() > 0:
            resultado["status"] = "error"
            resultado["erros"].append("Valores corrompidos de Saldo detectados na amostra.")

    if resultado["erros"]:
        resultado["status"] = "error"
    elif resultado["avisos"]:
        resultado["status"] = "warning"

    return resultado


def validar_todos_datasets(
    data_dir: Path | None = None,
    atualizar_status: bool = True,
) -> dict[str, Any]:
    if data_dir is None:
        data_dir = Path(__file__).resolve().parents[1] / "data"

    section("Auditoria e Validação de Qualidade de Dados (Data Quality)")
    resultados = {
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "total_datasets": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "datasets": {},
    }

    # 1. Cadastro
    cad_path = data_dir / "cadastro_ifs.csv"
    res_cad = validar_cadastro(cad_path)
    resultados["datasets"][cad_path.name] = res_cad
    resultados["total_datasets"] += 1
    if res_cad["status"] == "error":
        resultados["failed"] += 1
        print(f"  {b_red('✖')} {cad_path.name}: {res_cad['erros']}")
    elif res_cad["status"] == "warning":
        resultados["warnings"] += 1
        print(f"  {b_yellow('⚠')} {cad_path.name}: {res_cad['avisos']}")
    else:
        resultados["passed"] += 1
        print(f"  {green('✔')} {cad_path.name} ({res_cad['total_linhas']:,} linhas)")

    # 2. Relatórios 1 a 16
    for dataset_id, rel_id in RELATORIOS_MAP.items():
        rel_file = data_dir / f"{dataset_id}.csv.gz"
        if not rel_file.exists():
            continue

        res_rel = validar_relatorio(rel_file, rel_id)
        resultados["datasets"][rel_file.name] = res_rel
        resultados["total_datasets"] += 1

        if res_rel["status"] == "error":
            resultados["failed"] += 1
            print(f"  {b_red('✖')} Relatório {rel_id} ({rel_file.name}): {res_rel['erros']}")
        elif res_rel["status"] == "warning":
            resultados["warnings"] += 1
            print(f"  {b_yellow('⚠')} Relatório {rel_id} ({rel_file.name}): {res_rel['avisos']}")
        else:
            resultados["passed"] += 1
            per_info = f"{res_rel['min_periodo']} → {res_rel['max_periodo']} ({res_rel['periodos_count']} trimestres)"
            print(f"  {green('✔')} Relatório {rel_id:2s} ({rel_file.name}) {dim(per_info)}")

    if resultados["failed"] > 0:
        resultados["status"] = "error"
    elif resultados["warnings"] > 0:
        resultados["status"] = "warning"

    print()
    resumo_cor = b_green if resultados["status"] == "success" else (b_yellow if resultados["status"] == "warning" else b_red)
    print(
        f"  Resultado Data Quality: {resumo_cor(resultados['status'].upper())} — "
        f"{resultados['passed']}/{resultados['total_datasets']} datasets aprovados, "
        f"{resultados['warnings']} avisos, {resultados['failed']} falhas."
    )
    print()

    if atualizar_status:
        _atualizar_pipeline_status(data_dir, resultados)

    return resultados


def _atualizar_pipeline_status(data_dir: Path, data_quality_result: dict[str, Any]) -> None:
    status_path = data_dir / "pipeline_status.json"
    status_js_path = data_dir / "pipeline_status.js"

    status_data = {}
    if status_path.exists():
        try:
            with open(status_path, "r", encoding="utf-8") as f:
                status_data = json.load(f)
        except Exception:
            pass

    status_data["data_quality"] = {
        "status": data_quality_result["status"],
        "timestamp": data_quality_result["timestamp"],
        "total_datasets": data_quality_result["total_datasets"],
        "passed": data_quality_result["passed"],
        "warnings": data_quality_result["warnings"],
        "failed": data_quality_result["failed"],
    }

    try:
        with open(status_path, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
        with open(status_js_path, "w", encoding="utf-8") as f:
            f.write(
                f"window.PULSEIFDATA_PIPELINE_STATUS = "
                f"{json.dumps(status_data, indent=2, ensure_ascii=False)};\n"
            )
        log.info("Status de Data Quality gravado em pipeline_status.json/js")
    except Exception as e:
        log.warning(f"Não foi possível atualizar pipeline_status com Data Quality: {e}")


def main():
    parser = argparse.ArgumentParser(description="Validador de qualidade de dados do PulseIFData")
    parser.add_argument("--fail-on-error", action="store_true", help="Retorna exit code 1 se houver falhas")
    parser.add_argument("--no-status-update", action="store_true", help="Não altera pipeline_status.json")
    args = parser.parse_args()

    resultados = validar_todos_datasets(atualizar_status=not args.no_status_update)

    if args.fail_on_error and resultados["status"] == "error":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
