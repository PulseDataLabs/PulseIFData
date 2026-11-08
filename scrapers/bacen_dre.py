#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Demonstração de Resultado (Relatório 4 IFData) → data/bacen_dre.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenDreScraper(IfdataRelatorioBaseScraper):
    name = "bacen_dre"
    relatorio_id = "4"
    relatorio_nome = "Demonstração de Resultado"
    title = "BACEN — Demonstração de Resultado (Relatório 4 IFData)"
    description = (
        "Série histórica do Relatório 4 (Demonstração de Resultado - DRE) do IFData/BACEN: "
        "receitas de intermediação financeira, despesas de captação, resultado com perdas "
        "esperadas, rendas de tarifas e prestação de serviços, despesas de pessoal e lucro líquido."
    )
    icon = "📈"
    tags = ["IFData", "BACEN", "DRE", "resultado", "receitas", "despesas", "lucro"]


if __name__ == "__main__":
    BacenDreScraper().run()

