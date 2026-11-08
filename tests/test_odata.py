import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import requests_mock

from scrapers.utils.odata import (
    baixar_com_checkpoint,
    gerar_periodos,
    paginar_odata,
)


def test_gerar_periodos_end_year_e_ordem():
    periodos = gerar_periodos(start_year=2023, start_month=3, quarters=[3, 6, 9, 12], end_year=2024)
    # Deve estar em ordem decrescente
    assert periodos == [202412, 202409, 202406, 202403, 202312, 202309, 202306, 202303]


def test_gerar_periodos_ignora_meses_anteriores_ao_start():
    periodos = gerar_periodos(start_year=2023, start_month=9, quarters=[3, 6, 9, 12], end_year=2023)
    assert periodos == [202312, 202309]


def test_paginar_odata_primeira_pagina_sem_top_skip():
    url = "https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata/Teste"
    with requests_mock.Mocker() as m:
        # Página 1 (sem $top nem $skip)
        m.get(
            url,
            additional_matcher=lambda req: "$top" not in req.qs and "$skip" not in req.qs,
            json={"value": [{"CodInst": "00000001", "Saldo": 100}, {"CodInst": "00000002", "Saldo": 200}]},
        )
        # Página 2 (com $top=2 e $skip=2)
        m.get(
            url,
            additional_matcher=lambda req: req.qs.get("$top") == ["2"] and req.qs.get("$skip") == ["2"],
            json={"value": [{"CodInst": "00000003", "Saldo": 300}]},
        )

        session = requests.Session()
        df = paginar_odata(session, url, params={"@AnoMes": "202403"}, top=2)

        assert len(df) == 3
        assert list(df["CodInst"]) == ["00000001", "00000002", "00000003"]


def test_paginar_odata_retorna_vazio_em_404():
    url = "https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata/Inexistente"
    with requests_mock.Mocker() as m:
        m.get(url, status_code=404)
        session = requests.Session()
        df = paginar_odata(session, url, params={})
        assert df.empty


def test_paginar_odata_retry_em_erro_500():
    url = "https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata/Flaky"
    with requests_mock.Mocker() as m:
        # Primeira tentativa falha com 500, segunda responde com 200
        m.register_uri(
            "GET",
            url,
            [
                {"status_code": 500},
                {"status_code": 200, "json": {"value": [{"ok": True}]}},
            ],
        )
        session = requests.Session()
        df = paginar_odata(session, url, params={}, max_retries=2, retry_delay=0)
        assert len(df) == 1
        assert bool(df.iloc[0]["ok"]) is True


def test_baixar_com_checkpoint_reaproveita_parquet_existente():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = Path(tmpdir) / "ifdata_rel1_202403_tipo1.parquet"
        orig_df = pd.DataFrame({"CodInst": ["12345678"], "Valor": [999.0]})
        orig_df.to_parquet(raw_path, index=False)

        session = requests.Session()
        # Não registra mock: se fizesse requisição HTTP, geraria erro de conexão
        df = baixar_com_checkpoint(
            session=session,
            url="https://olinda.bcb.gov.br/fake",
            params={},
            raw_path=raw_path,
        )

        assert df is not None
        assert len(df) == 1
        assert df.iloc[0]["CodInst"] == "12345678"


def test_baixar_com_checkpoint_cria_parquet_se_nao_existir():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = Path(tmpdir) / "ifdata_rel1_202403_tipo1.parquet"
        assert not raw_path.exists()

        url = "https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata/Dados"
        with requests_mock.Mocker() as m:
            m.get(url, json={"value": [{"CodInst": "87654321", "Saldo": 50.0}]})
            session = requests.Session()
            df = baixar_com_checkpoint(
                session=session,
                url=url,
                params={"@AnoMes": "202403"},
                raw_path=raw_path,
            )

            assert df is not None
            assert len(df) == 1
            assert raw_path.exists()
            loaded = pd.read_parquet(raw_path)
            assert len(loaded) == 1
            assert loaded.iloc[0]["CodInst"] == "87654321"
