#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Carteira de crédito ativa Pessoa Jurídica - por atividade econômica (CNAE) (Relatório 12 IFData) → data/bacen_credito_pj_cnae.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenCreditoPjCnaeScraper(IfdataRelatorioBaseScraper):
    name = "bacen_credito_pj_cnae"
    relatorio_id = "12"
    relatorio_nome = "Carteira de crédito ativa Pessoa Jurídica - por atividade econômica (CNAE)"
    title = "BACEN — Carteira de Crédito PJ por Atividade Econômica CNAE (Relatório 12 IFData)"
    description = (
        "Série histórica do Relatório 12 do IFData/BACEN: carteira de crédito ativa "
        "Pessoa Jurídica segmentada por setor de atividade econômica (CNAE) e faixa de vencimento."
    )
    icon = "🏭"
    tags = ["IFData", "BACEN", "crédito", "PJ", "CNAE", "setor econômico"]


if __name__ == "__main__":
    BacenCreditoPjCnaeScraper().run()

