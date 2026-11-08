#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Carteira de crédito ativa - por região geográfica (Relatório 9 IFData) → data/bacen_credito_regiao.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenCreditoRegiaoScraper(IfdataRelatorioBaseScraper):
    name = "bacen_credito_regiao"
    relatorio_id = "9"
    relatorio_nome = "Carteira de crédito ativa - por região geográfica"
    title = "BACEN — Carteira de Crédito Ativa por Região Geográfica (Relatório 9 IFData)"
    description = (
        "Série histórica do Relatório 9 do IFData/BACEN: carteira de crédito ativa "
        "distribuída por região geográfica (Norte, Nordeste, Centro-Oeste, Sudeste, Sul e Exterior)."
    )
    icon = "🗺️"
    tags = ["IFData", "BACEN", "crédito", "região", "geografia"]


if __name__ == "__main__":
    BacenCreditoRegiaoScraper().run()

