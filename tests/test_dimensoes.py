import gzip
import tempfile
from pathlib import Path

import polars as pl

from scripts.gerar_dimensoes import gerar_depara_conglomerados, gerar_dim_conta


def test_gerar_dim_conta_estrutura_e_agrupamento():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        rel1_path = tmp_path / "bacen_resumo.csv.gz"

        df = pl.DataFrame({
            "NumeroRelatorio": ["1", "1", "1"],
            "NomeRelatorio": ["Resumo", "Resumo", "Resumo"],
            "Conta": ["1000", "1000", "2000"],
            "NomeColuna": ["Ativo Total", "Ativo Total", "Passivo"],
            "DescricaoColuna": ["Soma de ativos", "Soma de ativos", "Passivo total"],
            "AnoMes": ["202303", "202403", "202403"],
        })
        with open(rel1_path, "wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
            df.write_csv(gz)

        dim_df = gerar_dim_conta(tmp_path)

        assert not dim_df.is_empty()
        assert len(dim_df) == 2
        assert "min_periodo" in dim_df.columns
        assert "max_periodo" in dim_df.columns

        conta_1000 = dim_df.filter(pl.col("Conta") == "1000")
        assert conta_1000["min_periodo"][0] == 202303
        assert conta_1000["max_periodo"][0] == 202403
        assert conta_1000["total_ocorrencias"][0] == 2


def test_gerar_depara_conglomerados_identifica_tipos():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        cad_path = tmp_path / "cadastro_ifs.csv"

        df = pl.DataFrame({
            "Data": ["202403", "202403", "202403"],
            "CodInst": ["C0000001", "C0000002", "C0000003"],
            "NomeInstituicao": ["BANCO AMBOS", "BANCO APENAS FIN", "BANCO APENAS PRUD"],
            "CodConglomeradoFinanceiro": ["C001", "C002", ""],
            "CodConglomeradoPrudencial": ["C008", "", "C009"],
            "CnpjInstituicaoLider": ["12345678", "23456789", "34567890"],
            "Segmento": ["S1", "S2", "S3"],
        })
        df.write_csv(cad_path)

        depara_df = gerar_depara_conglomerados(tmp_path)

        assert not depara_df.is_empty()
        assert len(depara_df) == 3

        ambos = depara_df.filter(pl.col("cod_fin") == "C001")
        assert ambos["tipo_associacao"][0] == "financeiro_e_prudencial"
        assert ambos["ativo_atualmente"][0] is True

        apenas_fin = depara_df.filter(pl.col("cod_fin") == "C002")
        assert apenas_fin["tipo_associacao"][0] == "apenas_financeiro"

        apenas_prud = depara_df.filter(pl.col("cod_prud") == "C009")
        assert apenas_prud["tipo_associacao"][0] == "apenas_prudencial"
