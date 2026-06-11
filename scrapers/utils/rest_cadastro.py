import sys
import time
from pathlib import Path

import requests
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from utils.base import get_logger, nova_session

log = get_logger("rest_cadastro")

REST_BASE = "https://www3.bcb.gov.br/ifdata/rest"
CATALOGO_ENDPOINT = f"{REST_BASE}/relatorios"
ARQUIVO_ENDPOINT = f"{REST_BASE}/arquivos"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www3.bcb.gov.br/ifdata/",
    "Accept": "application/json",
}

RELA_CADASTRO_TIPO = {
    1005: "conglomerados_financeiros",
    1006: "instituicoes_individuais",
    1009: "conglomerados_prudenciais",
}

COLUNAS_CADASTRO = {
    "c0": "CodInst",
    "c1": "Data",
    "c2": "NomeInstituicao",
    "c3": "TCB",
    "c4": "TD",
    "c5": "TC",
    "c6": "TI",
    "c7": "UF",
    "c8": "Cidade",
    "c9": "Segmento",
    "c10": "TI_Desc",
    "c11": "CodConglomeradoFinanceiro",
    "c12": "CodConglomeradoPrudencial",
    "c13": "NumeroAgencias",
    "c14": "NumeroPostos",
    "c15": "NomeConglomeradoPrudencial",
    "c16": "NomeConglomeradoFinanceiro",
    "c17": "Situacao",
    "c18": "Ativo",
    "c19": "TotalAssets",
}


def listar_periodos() -> list[dict]:
    r = requests.get(CATALOGO_ENDPOINT, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def _path_cadastro(periodo: int, tipo_id: int) -> str:
    prefixo = f"ifdata_2025_2030/{periodo}" if periodo >= 202500 else str(periodo)
    return f"{prefixo}/cadastro{periodo}_{tipo_id}.json"


def baixar_cadastro_tipo(periodo: int, tipo_id: int) -> pd.DataFrame | None:
    nome_tipo = RELA_CADASTRO_TIPO.get(tipo_id, str(tipo_id))
    path = _path_cadastro(periodo, tipo_id)
    url = f"{ARQUIVO_ENDPOINT}?nomeArquivo={path}"

    r = requests.get(url, headers=HEADERS, timeout=60)
    if r.status_code != 200 or len(r.text) < 100:
        log.warning(f"Cadastro {periodo} tipo {tipo_id} ({nome_tipo}): HTTP {r.status_code} ({len(r.text)} bytes)")
        return None

    registros = r.json()
    if not registros:
        log.warning(f"Cadastro {periodo} tipo {tipo_id}: vazio")
        return None

    df = pd.DataFrame(registros)
    df.rename(columns=COLUNAS_CADASTRO, inplace=True)

    cols_presentes = [c for c in COLUNAS_CADASTRO.values() if c in df.columns]

    if "Data" in df.columns:
        df["AnoMes"] = df["Data"].astype(str).str[:6]
    else:
        df["AnoMes"] = str(periodo)

    df["TipoCadastro"] = nome_tipo
    df["TipoCadastroId"] = tipo_id

    log.info(f"Cadastro {periodo} tipo {tipo_id} ({nome_tipo}): {len(df)} IFs")
    return df[cols_presentes + ["AnoMes", "TipoCadastro", "TipoCadastroId"]]


def baixar_cadastro_completo(periodo: int) -> pd.DataFrame:
    frames = []
    for tipo_id in [1005, 1006, 1009]:
        df = baixar_cadastro_tipo(periodo, tipo_id)
        if df is not None and not df.empty:
            frames.append(df)
        time.sleep(0.5)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def baixar_todos_periodos() -> pd.DataFrame:
    catalogo = listar_periodos()
    log.info(f"Catálogo: {len(catalogo)} períodos disponíveis")
    frames = []
    for item in catalogo:
        periodo = item["dt"]
        df = baixar_cadastro_completo(periodo)
        if not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def baixar_cadastro_unico_mais_recente() -> pd.DataFrame:
    catalogo = listar_periodos()
    if not catalogo:
        return pd.DataFrame()
    ultimo = catalogo[-1]["dt"]
    log.info(f"Baixando cadastro mais recente: {ultimo}")
    return baixar_cadastro_completo(ultimo)
