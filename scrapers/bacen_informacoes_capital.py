#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Informações de Capital (Relatório 5 IFData) → data/bacen_informacoes_capital.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenInformacoesCapitalScraper(IfdataRelatorioBaseScraper):
    name = "bacen_informacoes_capital"
    relatorio_id = "5"
    relatorio_nome = "Informações de Capital"
    title = "BACEN — Informações de Capital (Relatório 5 IFData)"
    description = (
        "Série histórica completa do Relatório 5 (Informações de Capital) do IFData/BACEN: "
        "Capital Principal, Capital Complementar, Patrimônio de Referência (Nível I e II), "
        "RWA (crédito, mercado, operacional), Exposição Total, Índice de Basileia e Razão de Alavancagem."
    )
    icon = "⚖️"
    tags = ["IFData", "BACEN", "capital", "Basileia", "RWA", "alavancagem"]


if __name__ == "__main__":
    BacenInformacoesCapitalScraper().run()

