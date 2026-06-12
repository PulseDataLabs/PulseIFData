#!/usr/bin/env python
# coding: utf-8
"""
Scraper: BACEN – Conglomerados Financeiros
Fonte:   https://www.bcb.gov.br/content/estabilidadefinanceira/relacao_instituicoes_funcionamento/
Saída:   data/bacen_conglomerados.csv

Baixa o arquivo ZIP mensal (YYYYMMCONGLOMERADO.zip), extrai o XLSX
e retorna o conteúdo normalizado.
"""
import os
import sys
import time
import datetime
import zipfile
from io import BytesIO
from dateutil.relativedelta import relativedelta

import pandas as pd
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.utils.base import BaseScraper


def _try_download(session: requests.Session, yyyymm: str) -> bytes | None:
    file_name = f"{yyyymm}CONGLOMERADO.zip"
    url = f"https://www.bcb.gov.br/content/estabilidadefinanceira/relacao_instituicoes_funcionamento/Conglomerados/{file_name}"
    resp = session.get(url, timeout=120)
    if resp.status_code == 200:
        return resp.content
    return None


class BacenConglomeradosScraper(BaseScraper):
    name = "bacen_conglomerados"
    group = "bacen"
    enabled = True
    phase = 1
    accumulate = False
    chaves_dedup = ["data_referencia", "CNPJ"]

    title = "BACEN — Conglomerados Financeiros"
    description = "Lista e composição dos conglomerados financeiros autorizados pelo Banco Central do Brasil."
    icon = "🏢"
    icon_class = "icon-bacen"
    badge = "Mensal"
    badge_class = "badge-monthly"
    tags = ["conglomerados", "cadastro", "BACEN"]
    source = "BACEN · Relação de Instituições"

    def fetch(self) -> pd.DataFrame:
        from scripts.utils.ux import print_done, print_warn

        session = requests.Session()

        hoje = datetime.date.today()
        content = None
        ref = hoje
        for meses_atras in (1, 2, 3):
            ref = hoje - relativedelta(months=meses_atras)
            yyyymm = ref.strftime("%Y%m")
            t0 = time.time()
            c = _try_download(session, yyyymm)
            if c:
                print_done(f"encontrado {yyyymm}CONGLOMERADO.zip", elapsed=time.time() - t0)
                content = c
                break
            print_warn(f"{yyyymm}CONGLOMERADO.zip não disponível", elapsed=time.time() - t0)
        if not content:
            raise RuntimeError("Nenhum arquivo de conglomerados disponível nos últimos 3 meses.")

        # Extrai XLSX do ZIP em memória
        with zipfile.ZipFile(BytesIO(content)) as zf:
            xlsx_names = [n for n in zf.namelist() if n.endswith(".xlsx")]
            if not xlsx_names:
                raise RuntimeError("Nenhum XLSX encontrado no arquivo ZIP.")
            xlsx_bytes = zf.read(xlsx_names[0])

        df = pd.read_excel(BytesIO(xlsx_bytes), engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        
        # Insere data de referência (primeiro dia do mês correspondente)
        df.insert(0, "data_referencia", ref.replace(day=1).strftime("%Y-%m-%d"))
        return df


if __name__ == "__main__":
    BacenConglomeradosScraper().run()
