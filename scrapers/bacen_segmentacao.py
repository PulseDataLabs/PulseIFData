#!/usr/bin/env python
# coding: utf-8
"""Scraper: BACEN – Segmentação (Relatório 6 IFData) → data/bacen_segmentacao.csv.gz"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.ifdata_relatorio import IfdataRelatorioBaseScraper


class BacenSegmentacaoScraper(IfdataRelatorioBaseScraper):
    name = "bacen_segmentacao"
    relatorio_id = "6"
    relatorio_nome = "Segmentação"
    title = "BACEN — Segmentação (Relatório 6 IFData)"
    description = (
        "Série histórica do Relatório 6 (Segmentação Prudencial) do IFData/BACEN: "
        "enquadramento em segmentos S1–S5, exposição total e porte em relação ao PIB."
    )
    icon = "🏛️"
    tags = ["IFData", "BACEN", "segmentação", "S1", "S2", "S3", "S4", "S5"]


if __name__ == "__main__":
    BacenSegmentacaoScraper().run()

