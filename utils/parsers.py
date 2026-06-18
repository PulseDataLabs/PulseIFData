import csv
import json
import zipfile
from datetime import date, datetime, timedelta
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd


def date_ref(ref: str | None = None) -> date:
    hoje = date.today()
    if ref is None or ref == "hoje":
        return hoje
    if ref == "mes_anterior":
        return hoje.replace(day=1) - timedelta(days=1)
    return hoje


def replace_date_vars(template: str, dt: date) -> str:
    return (
        template.replace("YYYY", dt.strftime("%Y"))
        .replace("MM", dt.strftime("%m"))
        .replace("DD", dt.strftime("%d"))
    )


def rows_from_zip(content: bytes) -> list[dict]:
    rows = []
    with zipfile.ZipFile(BytesIO(content)) as zf:
        for name in zf.namelist():
            if name.endswith(".csv"):
                text = zf.read(name).decode("utf-8", errors="replace")
                rows.extend(csv.DictReader(StringIO(text)))
            elif name.endswith((".xls", ".xlsx")):
                df = pd.read_excel(BytesIO(zf.read(name)), engine="openpyxl")
                rows.extend(df.to_dict(orient="records"))
    return rows


def enriquecer(dataset_id: str, rows: list[dict]) -> tuple[list[dict], list[str]]:
    from utils.base import agora_brt
    data_captura, hora_captura = agora_brt()
    enriched = []
    for r in rows:
        r["data_captura"] = data_captura
        enriched.append(r)
    header = list(dict.fromkeys(k for r in enriched for k in r.keys()))
    return enriched, header


def read_existing_header(arquivo: Path) -> list[str]:
    if not arquivo.exists() or arquivo.stat().st_size == 0:
        return []
    try:
        with arquivo.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            return [col.strip() for col in header if col.strip()]
    except Exception:
        return []
