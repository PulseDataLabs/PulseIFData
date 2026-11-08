#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento (Relatório 11 IFData) → data/bacen_credito_pf_modalidade_prazo.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenCreditoPfModalidadePrazoScraper(IfdataRelatorioBaseScraper):
    name = "bacen_credito_pf_modalidade_prazo"
    relatorio_id = "11"
    relatorio_nome = "Carteira de crédito ativa Pessoa Física - modalidade e prazo de vencimento"
    title = "BACEN — Carteira de Crédito PF por Modalidade e Prazo (Relatório 11 IFData)"
    description = (
        "Série histórica do Relatório 11 do IFData/BACEN: carteira de crédito ativa "
        "Pessoa Física aberta por modalidade (consignado, habitação, veículos, cartão, "
        "rural, outros) e por faixa de prazo de vencimento e atraso."
    )
    icon = "🧑"
    tags = ["IFData", "BACEN", "crédito", "PF", "modalidade", "prazo", "consignado"]


if __name__ == "__main__":
    BacenCreditoPfModalidadePrazoScraper().run()

