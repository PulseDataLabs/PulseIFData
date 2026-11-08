import gzip
import tempfile
from pathlib import Path

import polars as pl

from scripts.validar_datasets import validar_cadastro, validar_relatorio


def test_validar_cadastro_ok():
    with tempfile.TemporaryDirectory() as tmpdir:
        cad_path = Path(tmpdir) / "cadastro_ifs.csv"
        df = pl.DataFrame({
            "CodInst": ["C0000001", "C0000002"],
            "Data": ["202403", "202403"],
            "NomeInstituicao": ["BANCO A", "BANCO B"],
        })
        df.write_csv(cad_path)

        res = validar_cadastro(cad_path)
        assert res["status"] == "success"
        assert res["total_linhas"] == 2
        assert len(res["erros"]) == 0


def test_validar_cadastro_arquivo_inexistente():
    res = validar_cadastro(Path("/caminho/inexistente/cadastro.csv"))
    assert res["status"] == "error"
    assert "não encontrado" in res["erros"][0]


def test_validar_cadastro_detecta_codinst_nulo():
    with tempfile.TemporaryDirectory() as tmpdir:
        cad_path = Path(tmpdir) / "cadastro_ifs.csv"
        df = pl.DataFrame({
            "CodInst": ["C0000001", None],
            "Data": ["202403", "202403"],
            "NomeInstituicao": ["BANCO A", "BANCO B"],
        })
        df.write_csv(cad_path)

        res = validar_cadastro(cad_path)
        assert res["status"] == "error"
        assert any("CodInst nulo" in e for e in res["erros"])


def test_validar_relatorio_ok_com_instituicao_e_agregado():
    with tempfile.TemporaryDirectory() as tmpdir:
        rel_path = Path(tmpdir) / "bacen_resumo.csv.gz"
        df = pl.DataFrame({
            "AnoMes": ["202403", "202403"],
            "CodInst": ["C0000001", ""],  # Um de IF e um agregado do BACEN
            "TipoInstituicao": ["1", "1"],
            "Conta": ["1000", "1000"],
            "Saldo": ["123.45", "9999.00"],
        })
        with open(rel_path, "wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
            df.write_csv(gz)

        res = validar_relatorio(rel_path, relatorio_id="1")
        assert res["status"] in ("success", "warning")
        assert res["total_linhas"] == 2
        assert len(res["erros"]) == 0


def test_validar_relatorio_detecta_duplicatas_de_chave():
    with tempfile.TemporaryDirectory() as tmpdir:
        rel_path = Path(tmpdir) / "bacen_ativo.csv.gz"
        # Duas linhas com exatamente a mesma chave primária para a mesma IF
        df = pl.DataFrame({
            "AnoMes": ["202403", "202403"],
            "CodInst": ["C0000001", "C0000001"],
            "TipoInstituicao": ["1", "1"],
            "Conta": ["1000", "1000"],
            "Saldo": ["100.0", "200.0"],
        })
        with open(rel_path, "wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
            df.write_csv(gz)

        res = validar_relatorio(rel_path, relatorio_id="2")
        assert res["status"] == "error"
        assert any("duplicados na chave primária" in e for e in res["erros"])


def test_validar_relatorio_8_rejeita_periodo_pos_2025():
    with tempfile.TemporaryDirectory() as tmpdir:
        rel_path = Path(tmpdir) / "bacen_credito_nivel_risco.csv.gz"
        df = pl.DataFrame({
            "AnoMes": ["202503"],  # Relatório 8 encerrou em 202412
            "CodInst": ["C0000001"],
            "TipoInstituicao": ["2"],
            "Conta": ["1000"],
            "Saldo": ["100.0"],
        })
        with open(rel_path, "wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
            df.write_csv(gz)

        res = validar_relatorio(rel_path, relatorio_id="8")
        assert res["status"] == "error"
        assert any("Res. 2.682" in e for e in res["erros"])


def test_validar_relatorio_16_rejeita_periodo_pre_2025():
    with tempfile.TemporaryDirectory() as tmpdir:
        rel_path = Path(tmpdir) / "bacen_credito_instrumentos_financeiros.csv.gz"
        df = pl.DataFrame({
            "AnoMes": ["202412"],  # Relatório 16 só existe a partir de 202503
            "CodInst": ["C0000001"],
            "TipoInstituicao": ["1"],
            "Conta": ["1000"],
            "Saldo": ["100.0"],
        })
        with open(rel_path, "wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
            df.write_csv(gz)

        res = validar_relatorio(rel_path, relatorio_id="16")
        assert res["status"] == "error"
        assert any("Res. 4.966" in e for e in res["erros"])

