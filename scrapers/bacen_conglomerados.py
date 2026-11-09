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


def _try_download(session: requests.Session, ref_date: datetime.date) -> tuple[bytes | None, str]:
    """
    Tenta baixar o arquivo ZIP de conglomerados testando os formatos de nomenclatura do BACEN:
    - MMYYYYCONGLOMERADO.zip (formato adotado a partir de 102026)
    - YYYYMMCONGLOMERADO.zip (formato histórico anterior)
    Retorna (content, nome_arquivo_encontrado) ou (None, "").
    """
    mmyyyy = ref_date.strftime("%m%Y")
    yyyymm = ref_date.strftime("%Y%m")
    
    nomes_candidatos = [
        f"{mmyyyy}CONGLOMERADO.zip",
        f"{yyyymm}CONGLOMERADO.zip",
    ]
    
    for file_name in nomes_candidatos:
        url = f"https://www.bcb.gov.br/content/estabilidadefinanceira/relacao_instituicoes_funcionamento/Conglomerados/{file_name}"
        try:
            resp = session.get(url, timeout=120)
            if resp.status_code == 200 and len(resp.content) > 1000:
                return resp.content, file_name
        except Exception:
            continue
    return None, ""


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
        arquivo_baixado = ""
        for meses_atras in (0, 1, 2, 3):
            ref = hoje - relativedelta(months=meses_atras)
            t0 = time.time()
            c, nome_arq = _try_download(session, ref)
            if c:
                print_done(f"encontrado {nome_arq}", elapsed=time.time() - t0)
                content = c
                arquivo_baixado = nome_arq
                break
            print_warn(f"{ref.strftime('%m/%Y')} não disponível", elapsed=time.time() - t0)
        if not content:
            raise RuntimeError("Nenhum arquivo de conglomerados disponível nos últimos 4 meses.")

        # Extrai XLSX do ZIP em memória
        with zipfile.ZipFile(BytesIO(content)) as zf:
            xlsx_names = [n for n in zf.namelist() if n.endswith(".xlsx")]
            if not xlsx_names:
                raise RuntimeError("Nenhum XLSX encontrado no arquivo ZIP.")
            xlsx_bytes = zf.read(xlsx_names[0])

        df = pd.read_excel(BytesIO(xlsx_bytes), skiprows=9, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        df = df[df["CNPJ PARTICIPANTE"].notna()]
        
        # Insere data de referência (primeiro dia do mês correspondente)
        df.insert(0, "data_referencia", ref.replace(day=1).strftime("%Y-%m-%d"))
        return df


if __name__ == "__main__":
    BacenConglomeradosScraper().run()
