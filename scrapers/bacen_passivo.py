#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Passivo (Relatório 3 IFData) → data/bacen_passivo.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenPassivoScraper(IfdataRelatorioBaseScraper):
    name = "bacen_passivo"
    relatorio_id = "3"
    relatorio_nome = "Passivo"
    title = "BACEN — Passivo (Relatório 3 IFData)"
    description = (
        "Série histórica do Relatório 3 (Passivo) do IFData/BACEN: depósitos, "
        "captações, obrigações por empréstimos e repasses, instrumentos derivativos, "
        "dívida elegível a capital e patrimônio líquido."
    )
    icon = "📑"
    tags = ["IFData", "BACEN", "passivo", "depósitos", "captações", "patrimônio líquido"]


if __name__ == "__main__":
    BacenPassivoScraper().run()
