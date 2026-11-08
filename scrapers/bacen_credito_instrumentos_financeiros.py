#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Carteira de crédito ativa - por carteiras de instrumentos financeiros (Relatório 16 IFData) → data/bacen_credito_instrumentos_financeiros.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenCreditoInstrumentosFinanceirosScraper(IfdataRelatorioBaseScraper):
    name = "bacen_credito_instrumentos_financeiros"
    relatorio_id = "16"
    relatorio_nome = "Carteira de crédito ativa - por carteiras de instrumentos financeiros"
    title = "BACEN — Carteira de Crédito por Instrumentos Financeiros (Relatório 16 IFData)"
    description = (
        "Série histórica do Relatório 16 do IFData/BACEN (Resolução CMN 4.966): "
        "carteira de crédito ativa classificada por carteiras de instrumentos financeiros "
        "(C1 a C5) e estágios de risco de crédito."
    )
    icon = "📑"
    tags = ["IFData", "BACEN", "crédito", "instrumentos financeiros", "Resolução 4966", "estágios"]


if __name__ == "__main__":
    BacenCreditoInstrumentosFinanceirosScraper().run()

