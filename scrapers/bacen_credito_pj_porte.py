#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Carteira de crédito ativa Pessoa Jurídica - por porte do tomador (Relatório 14 IFData) → data/bacen_credito_pj_porte.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenCreditoPjPorteScraper(IfdataRelatorioBaseScraper):
    name = "bacen_credito_pj_porte"
    relatorio_id = "14"
    relatorio_nome = "Carteira de crédito ativa Pessoa Jurídica - por porte do tomador"
    title = "BACEN — Carteira de Crédito PJ por Porte do Tomador (Relatório 14 IFData)"
    description = (
        "Série histórica do Relatório 14 do IFData/BACEN: carteira de crédito ativa "
        "Pessoa Jurídica classificada pelo porte da empresa tomadora (micro, pequena, média e grande)."
    )
    icon = "📊"
    tags = ["IFData", "BACEN", "crédito", "PJ", "porte", "MPME", "grande porte"]


if __name__ == "__main__":
    BacenCreditoPjPorteScraper().run()

