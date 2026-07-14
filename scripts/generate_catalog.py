import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.base import get_logger
from scripts.utils.ux import print_done

log = get_logger("generate_catalog")

CATALOGO_BASE = [
    {
        "id": "cadastro_ifs",
        "name": "cadastro_ifs.csv",
        "desc": "Cadastro de IFs autorizadas, segmento S1–S5, UF e conglomerado",
        "freq": "Trimestral",
        "fonte": "BACEN",
        "cat": "cadastro",
    },
    {
        "id": "ifdata_historical_10y",
        "name": "ifdata_historical.csv.gz",
        "desc": "Série histórica consolidada (pivot): ativo, PL, lucro, carteira, Basileia por IF/trimestre",
        "freq": "Trimestral",
        "fonte": "BACEN",
        "cat": "balanco",
    },
    {
        "id": "derivadas_market_share",
        "name": "derivadas_market_share.csv.gz",
        "desc": "Participação de mercado por IF em cada trimestre (%)",
        "freq": "Trimestral",
        "fonte": "Pulse",
        "cat": "derivadas",
    },
    {
        "id": "derivadas_hhi",
        "name": "derivadas_hhi.csv",
        "desc": "HHI de concentração por trimestre (escala 0–10000)",
        "freq": "Trimestral",
        "fonte": "Pulse",
        "cat": "derivadas",
    },
    {
        "id": "derivadas_rankings",
        "name": "derivadas_rankings.csv.gz",
        "desc": "Ranking das IFs por ativo total em cada trimestre",
        "freq": "Trimestral",
        "fonte": "Pulse",
        "cat": "derivadas",
    },
    {
        "id": "derivadas_var",
        "name": "derivadas_var.csv.gz",
        "desc": "Variação QoQ e YoY da carteira de crédito por IF",
        "freq": "Trimestral",
        "fonte": "Pulse",
        "cat": "derivadas",
    },
]


def generate() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    data_dir = root_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    output_path = data_dir / "datasets.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(CATALOGO_BASE, f, indent=2, ensure_ascii=False)

    js_path = data_dir / "datasets.js"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(
            f"window.PULSEIFDATA_DATASETS = "
            f"{json.dumps(CATALOGO_BASE, indent=2, ensure_ascii=False)};\n"
        )

    log.info(f"Catálogo gerado: {len(CATALOGO_BASE)} datasets → {output_path}")


if __name__ == "__main__":
    generate()
