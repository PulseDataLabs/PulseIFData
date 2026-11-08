#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Resumo (Relatório 1 IFData) → data/bacen_resumo.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenResumoScraper(IfdataRelatorioBaseScraper):
    name = "bacen_resumo"
    relatorio_id = "1"
    relatorio_nome = "Resumo"
    title = "BACEN — Resumo (Relatório 1 IFData)"
    description = (
        "Série histórica do Relatório 1 (Resumo) do IFData/BACEN: ativo total, "
        "carteira de crédito, títulos e valores mobiliários, passivo exigível, "
        "captações, patrimônio líquido, lucro líquido e índice de Basileia."
    )
    icon = "📊"
    tags = ["IFData", "BACEN", "resumo", "ativo", "crédito", "lucro", "Basileia"]


if __name__ == "__main__":
    BacenResumoScraper().run()

