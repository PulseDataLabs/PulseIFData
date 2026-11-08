#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Carteira de crédito ativa - por nível de risco da operação (Relatório 8 IFData) → data/bacen_credito_nivel_risco.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenCreditoNivelRiscoScraper(IfdataRelatorioBaseScraper):
    name = "bacen_credito_nivel_risco"
    relatorio_id = "8"
    relatorio_nome = "Carteira de crédito ativa - por nível de risco da operação"
    title = "BACEN — Carteira de Crédito Ativa por Nível de Risco (Relatório 8 IFData)"
    description = (
        "Série histórica do Relatório 8 do IFData/BACEN: carteira de crédito ativa "
        "classificada por nível de risco da operação (AA, A, B, C, D, E, F, G, H)."
    )
    icon = "⚠️"
    tags = ["IFData", "BACEN", "crédito", "risco", "rating", "AA-H"]


if __name__ == "__main__":
    BacenCreditoNivelRiscoScraper().run()

