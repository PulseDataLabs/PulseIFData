#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento (Relatório 13 IFData) → data/bacen_credito_pj_modalidade_prazo.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenCreditoPjModalidadePrazoScraper(IfdataRelatorioBaseScraper):
    name = "bacen_credito_pj_modalidade_prazo"
    relatorio_id = "13"
    relatorio_nome = "Carteira de crédito ativa Pessoa Jurídica - modalidade e prazo de vencimento"
    title = "BACEN — Carteira de Crédito PJ por Modalidade e Prazo (Relatório 13 IFData)"
    description = (
        "Série histórica do Relatório 13 do IFData/BACEN: carteira de crédito ativa "
        "Pessoa Jurídica aberta por modalidade (capital de giro, investimento, comércio exterior, "
        "habitacional, rural, outros) e por faixa de prazo de vencimento e atraso."
    )
    icon = "🏢"
    tags = ["IFData", "BACEN", "crédito", "PJ", "modalidade", "prazo", "capital de giro"]


if __name__ == "__main__":
    BacenCreditoPjModalidadePrazoScraper().run()

