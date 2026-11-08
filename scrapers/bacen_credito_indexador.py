#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Carteira de Crédito Ativa - Por indexador (Relatório 7 IFData) → data/bacen_credito_indexador.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenCreditoIndexadorScraper(IfdataRelatorioBaseScraper):
    name = "bacen_credito_indexador"
    relatorio_id = "7"
    relatorio_nome = "Carteira de Crédito Ativa - Por indexador"
    title = "BACEN — Carteira de Crédito Ativa por Indexador (Relatório 7 IFData)"
    description = (
        "Série histórica do Relatório 7 do IFData/BACEN: carteira de crédito ativa "
        "aberta por indexador (prefixado, TR/TBF, TJLP, CDI/Selic, índices de preços, "
        "moeda estrangeira e outros)."
    )
    icon = "💳"
    tags = ["IFData", "BACEN", "crédito", "indexador", "CDI", "prefixado", "IPCA"]


if __name__ == "__main__":
    BacenCreditoIndexadorScraper().run()

