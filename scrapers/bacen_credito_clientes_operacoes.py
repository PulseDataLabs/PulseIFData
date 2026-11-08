#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Carteira de crédito ativa - quantidade de clientes e de operações (Relatório 10 IFData) → data/bacen_credito_clientes_operacoes.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenCreditoClientesOperacoesScraper(IfdataRelatorioBaseScraper):
    name = "bacen_credito_clientes_operacoes"
    relatorio_id = "10"
    relatorio_nome = "Carteira de crédito ativa - quantidade de clientes e de operações"
    title = "BACEN — Carteira de Crédito: Quantidade de Clientes e Operações (Relatório 10 IFData)"
    description = (
        "Série histórica do Relatório 10 do IFData/BACEN: quantidade de clientes "
        "e quantidade de operações da carteira de crédito ativa por instituição financeira."
    )
    icon = "👥"
    tags = ["IFData", "BACEN", "crédito", "clientes", "operações"]


if __name__ == "__main__":
    BacenCreditoClientesOperacoesScraper().run()

