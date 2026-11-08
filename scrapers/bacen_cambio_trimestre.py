#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Movimentação de Câmbio no Trimestre (Relatório 15 IFData) → data/bacen_cambio_trimestre.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenCambioTrimestreScraper(IfdataRelatorioBaseScraper):
    name = "bacen_cambio_trimestre"
    relatorio_id = "15"
    relatorio_nome = "Movimentação de Câmbio no Trimestre"
    title = "BACEN — Movimentação de Câmbio no Trimestre (Relatório 15 IFData)"
    description = (
        "Série histórica do Relatório 15 do IFData/BACEN: movimentação de câmbio no trimestre "
        "(operações comerciais, financeiras, mercado primário e interbancário)."
    )
    icon = "💱"
    tags = ["IFData", "BACEN", "câmbio", "exportação", "importação", "mercado interbancário"]


if __name__ == "__main__":
    BacenCambioTrimestreScraper().run()

