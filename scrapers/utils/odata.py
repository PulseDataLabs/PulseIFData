import time
from datetime import date
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from utils.base import get_logger

log = get_logger("odata")

ODATA_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/csv, */*",
}


def gerar_periodos(
    start_year: int,
    start_month: int,
    quarters: list[int],
    end_year: int | None = None,
) -> list[int]:
    hoje = date.today()
    limite = end_year or hoje.year
    periodos = []
    for ano in range(start_year, limite + 1):
        for q in quarters:
            if ano == limite and q > hoje.month:
                break
            if ano == start_year and q < start_month:
                continue
            periodos.append(ano * 100 + q)
    return sorted(periodos, reverse=True)


def paginar_odata(
    session: requests.Session,
    url: str,
    params: dict,
    top: int = 5000,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> pd.DataFrame:
    todos_registros = []
    skip = 0

    while True:
        params_pag = dict(params)
        params_pag["$top"] = top
        params_pag["$skip"] = skip

        for tentativa in range(1, max_retries + 1):
            try:
                resp = session.get(url, params=params_pag, headers=ODATA_HEADERS, timeout=120)
                if resp.status_code == 404:
                    return pd.DataFrame()
                if resp.status_code == 200:
                    break
                log.warning(f"HTTP {resp.status_code} tentativa {tentativa}/{max_retries}")
            except requests.RequestException as e:
                log.warning(f"Erro tentativa {tentativa}/{max_retries}: {e}")
            if tentativa < max_retries:
                time.sleep(retry_delay)
            else:
                log.error(f"Falha após {max_retries} tentativas para skip={skip}")
                return pd.DataFrame()

        if "$format" in params and params["$format"] == "text/csv":
            content = resp.text.strip()
            if not content or "<!DOCTYPE" in content[:200]:
                break
            try:
                df_page = pd.read_csv(StringIO(content))
            except Exception:
                break
        else:
            try:
                data = resp.json()
            except Exception:
                break
            df_page = pd.DataFrame(data.get("value", []))

        if df_page.empty:
            break

        todos_registros.append(df_page)
        skip += top

    if not todos_registros:
        return pd.DataFrame()

    return pd.concat(todos_registros, ignore_index=True)


def baixar_com_checkpoint(
    session: requests.Session,
    url: str,
    params: dict,
    raw_path: Path,
    top: int = 5000,
    max_retries: int = 3,
    retry_delay: int = 5,
) -> pd.DataFrame | None:
    if raw_path.suffix == ".csv":
        raw_path = raw_path.with_suffix(".parquet")

    if raw_path.exists() and raw_path.stat().st_size > 0:
        try:
            df = pd.read_parquet(raw_path)
            if not df.empty:
                log.info(f"Checkpoint carregado: {raw_path.name} ({len(df)} linhas)")
                return df
        except Exception as e:
            log.warning(f"Checkpoint corrompido, refazendo {raw_path.name}: {e}")

    df = paginar_odata(
        session, url, params,
        top=top, max_retries=max_retries, retry_delay=retry_delay,
    )

    if df.empty:
        return None

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    # Converte para string para manter compatibilidade com o formato de texto original
    df = df.astype(str)
    df.to_parquet(raw_path, index=False)
    log.info(f"Checkpoint salvo: {raw_path.name} ({len(df)} linhas)")
    return df
