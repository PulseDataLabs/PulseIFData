import polars as pl
import pytest
from pathlib import Path
import tempfile

from scripts.normalizer import (
    _calcular_indicadores_pl,
    _join_cadastro_pl,
    _pivotar_por_conta_pl,
)


def test_pivotar_por_conta_pl_converte_saldo_formatado_pt_br():
    df_raw = pl.DataFrame({
        "CodInst": ["C0000001", "C0000001"],
        "AnoMes": ["202403", "202403"],
        "TipoInstituicao": [1, 1],
        "Conta": ["1000", "2000"],
        "Saldo": ["1.234.567,89", "-500,25"],
    })
    mapping = {
        "1000": {"campo": "ativo_total"},
        "2000": {"campo": "passivo_circulante"},
    }

    pivoted = _pivotar_por_conta_pl(df_raw, mapping)

    assert "ativo_total" in pivoted.columns
    assert "passivo_circulante" in pivoted.columns
    assert len(pivoted) == 1
    assert pytest.approx(pivoted["ativo_total"][0], 0.01) == 1234567.89
    assert pytest.approx(pivoted["passivo_circulante"][0], 0.01) == -500.25


def test_pivotar_por_conta_pl_campos_ausentes_nao_quebram():
    df_raw = pl.DataFrame({"OutraColuna": [1, 2]})
    res = _pivotar_por_conta_pl(df_raw, {})
    assert res.columns == ["OutraColuna"]


def test_calcular_indicadores_pl_roe_e_roa():
    df = pl.DataFrame({
        "patrimonio_liquido": [1000.0, 0.0],
        "lucro_liquido": [50.0, 10.0],
        "ativo_total": [5000.0, 0.0],
        "resultado_operacional": [80.0, 5.0],
    })

    res = _calcular_indicadores_pl(df)

    assert "roe_anualizado" in res.columns
    assert "roa_anualizado" in res.columns
    assert "nim_margem_financeira" in res.columns

    # Linha 1: 50 / 1000 * 4 = 0.20
    assert pytest.approx(res["roe_anualizado"][0], 0.001) == 0.20
    # Linha 1: 50 / 5000 * 4 = 0.04
    assert pytest.approx(res["roa_anualizado"][0], 0.001) == 0.04
    # Linha 1: 80 / 5000 * 4 = 0.064
    assert pytest.approx(res["nim_margem_financeira"][0], 0.001) == 0.064

    # Linha 2 com divisão por zero deve retornar 0.0
    assert res["roe_anualizado"][1] == 0.0
    assert res["roa_anualizado"][1] == 0.0
    assert res["nim_margem_financeira"][1] == 0.0


def test_join_cadastro_pl_estrito():
    with tempfile.TemporaryDirectory() as tmpdir:
        cad_path = Path(tmpdir) / "cadastro_ifs.csv"
        cad_df = pl.DataFrame({
            "CodInst": ["C0000001", "C0000002"],
            "AnoMes": ["202403", "202403"],
            "NomeInstituicao": ["BANCO TESTE A", "BANCO TESTE B"],
            "Segmento": ["S1", "S2"],
            "UF": ["SP", "RJ"],
        })
        cad_df.write_csv(cad_path)

        rel_df = pl.DataFrame({
            "CodInst": ["C0000001", "C9999999"],
            "AnoMes": ["202403", "202403"],
            "Saldo": [100.0, 200.0],
        })

        merged = _join_cadastro_pl(rel_df, cad_path, modo="estrito")

        assert len(merged) == 2
        assert "NomeInstituicao" in merged.columns
        assert "Segmento" in merged.columns

        row_a = merged.filter(pl.col("CodInst") == "C0000001")
        assert row_a["NomeInstituicao"][0] == "BANCO TESTE A"
        assert row_a["Segmento"][0] == "S1"

        row_not_found = merged.filter(pl.col("CodInst") == "C9999999")
        assert row_not_found["NomeInstituicao"][0] is None

