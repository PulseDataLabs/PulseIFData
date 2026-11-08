import gzip
import hashlib
import io
import tempfile
from pathlib import Path

import polars as pl
import pytest

from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class FakeRelatorioScraper(IfdataRelatorioBaseScraper):
    relatorio_id = "99"
    relatorio_nome = "Fake"
    name = "bacen_fake"
    title = "Fake"
    description = "Fake desc"
    tags = ["fake"]

    def __init__(self, output_file: Path, raw_dir: Path):
        self.output_file = output_file
        self.raw_dir = raw_dir


def test_gzip_deterministico_produz_bytes_identicos():
    df = pl.DataFrame({
        "CodInst": ["C0000001", "C0000002"],
        "AnoMes": ["202403", "202403"],
        "Saldo": ["1000.0", "2000.0"],
    })

    def _escrever_gz():
        buf = io.BytesIO()
        with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
            df.write_csv(gz)
        return buf.getvalue()

    bytes1 = _escrever_gz()
    bytes2 = _escrever_gz()

    assert bytes1 == bytes2
    assert hashlib.sha256(bytes1).hexdigest() == hashlib.sha256(bytes2).hexdigest()


def test_manter_arquivo_existente_detecta_sem_mudancas():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "bacen_fake.csv.gz"
        raw_dir = Path(tmpdir) / "raw"
        raw_dir.mkdir()

        df_existente = pl.DataFrame({
            "data_captura": ["2026-11-01"],
            "AnoMes": ["202403"],
            "CodInst": ["C0000001"],
            "TipoInstituicao": ["1"],
            "Conta": ["1000"],
            "Saldo": ["100.0"],
        })
        with open(out_file, "wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
            df_existente.write_csv(gz)

        scraper = FakeRelatorioScraper(output_file=out_file, raw_dir=raw_dir)

        # Mesmo conteúdo, apenas data_captura mais recente
        df_novo = pl.DataFrame({
            "data_captura": ["2026-11-08"],
            "AnoMes": ["202403"],
            "CodInst": ["C0000001"],
            "TipoInstituicao": ["1"],
            "Conta": ["1000"],
            "Saldo": ["100.0"],
        })

        # Deve identificar que não houve mudança real e manter o arquivo existente
        assert scraper._manter_arquivo_existente(df_novo) is True


def test_manter_arquivo_existente_rejeita_perda_de_periodo_inicial():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "bacen_fake.csv.gz"
        raw_dir = Path(tmpdir) / "raw"
        raw_dir.mkdir()

        df_existente = pl.DataFrame({
            "data_captura": ["2026-11-01", "2026-11-01"],
            "AnoMes": ["201403", "202403"],
            "CodInst": ["C0000001", "C0000001"],
            "TipoInstituicao": ["1", "1"],
            "Conta": ["1000", "1000"],
            "Saldo": ["100.0", "150.0"],
        })
        with open(out_file, "wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
            df_existente.write_csv(gz)

        scraper = FakeRelatorioScraper(output_file=out_file, raw_dir=raw_dir)

        # Novo dataset começa apenas em 202403 (perdeu o histórico de 201403)
        df_novo = pl.DataFrame({
            "data_captura": ["2026-11-08"],
            "AnoMes": ["202403"],
            "CodInst": ["C0000001"],
            "TipoInstituicao": ["1"],
            "Conta": ["1000"],
            "Saldo": ["150.0"],
        })

        with pytest.raises(RuntimeError, match="Sobrescrita abortada"):
            scraper._manter_arquivo_existente(df_novo)


def test_manter_arquivo_existente_rejeita_shrink():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_file = Path(tmpdir) / "bacen_fake.csv.gz"
        raw_dir = Path(tmpdir) / "raw"
        raw_dir.mkdir()

        # 100 linhas existentes
        linhas = [
            {
                "data_captura": "2026-11-01",
                "AnoMes": "202403",
                "CodInst": f"C{i:07d}",
                "TipoInstituicao": "1",
                "Conta": "1000",
                "Saldo": "10.0",
            }
            for i in range(100)
        ]
        df_existente = pl.DataFrame(linhas)
        with open(out_file, "wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
            df_existente.write_csv(gz)

        scraper = FakeRelatorioScraper(output_file=out_file, raw_dir=raw_dir)

        # Novo dataset com apenas 50 linhas (< 0.98 * 100)
        df_novo = pl.DataFrame(linhas[:50])

        with pytest.raises(RuntimeError, match="Sobrescrita abortada"):
            scraper._manter_arquivo_existente(df_novo)

