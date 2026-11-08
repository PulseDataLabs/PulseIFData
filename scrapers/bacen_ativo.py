#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Ativo (Relatório 2 IFData) → data/bacen_ativo.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenAtivoScraper(IfdataRelatorioBaseScraper):
    name = "bacen_ativo"
    relatorio_id = "2"
    relatorio_nome = "Ativo"
    title = "BACEN — Ativo (Relatório 2 IFData)"
    description = (
        "Série histórica do Relatório 2 (Ativo) do IFData/BACEN: disponibilidades, "
        "aplicações interfinanceiras de liquidez, TVM e derivativos, operações de "
        "crédito, arrendamento mercantil, outros créditos e ativo total."
    )
    icon = "🏦"
    tags = ["IFData", "BACEN", "ativo", "disponibilidades", "TVM", "crédito"]


if __name__ == "__main__":
    BacenAtivoScraper().run()

