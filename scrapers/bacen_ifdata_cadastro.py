import os
import sys
import time
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.base import BaseScraper
from scrapers.utils.odata import baixar_com_checkpoint, gerar_periodos
from scrapers.utils.rest_cadastro import (
    baixar_cadastro_completo,
    baixar_cadastro_unico_mais_recente,
    listar_periodos,
)
from utils.base import nova_session, get_logger
from scripts.utils.ux import print_done, print_warn, print_skip, section

log = get_logger("bacen_ifdata_cadastro")


def _carregar_settings() -> dict:
    settings_path = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalizar_df_cadastro(df: pd.DataFrame, periodo: str | int | None = None) -> pd.DataFrame:
    df = df.copy()
    df = df.fillna("").astype(str).replace({"None": "", "nan": "", "<NA>": ""})

    if "Uf" in df.columns and "UF" not in df.columns:
        df = df.rename(columns={"Uf": "UF"})

    sr = df["Sr"].str.strip() if "Sr" in df.columns else pd.Series("", index=df.index)
    seg_tb = (
        df["SegmentoTb"].str.strip()
        if "SegmentoTb" in df.columns
        else (df["Segmento"].str.strip() if "Segmento" in df.columns else pd.Series("", index=df.index))
    )
    if "SegmentoTb" not in df.columns and "Segmento" in df.columns:
        df["SegmentoTb"] = seg_tb
    df["Segmento"] = sr.where(sr != "", seg_tb)

    if "Municipio" in df.columns and "Cidade" not in df.columns:
        df["Cidade"] = df["Municipio"]
    elif "Cidade" in df.columns and "Municipio" not in df.columns:
        df["Municipio"] = df["Cidade"]

    if "Conglomerado" not in df.columns:
        congl_prud = (
            df["CodConglomeradoPrudencial"].str.strip()
            if "CodConglomeradoPrudencial" in df.columns
            else pd.Series("", index=df.index)
        )
        congl_fin = (
            df["CodConglomeradoFinanceiro"].str.strip()
            if "CodConglomeradoFinanceiro" in df.columns
            else pd.Series("", index=df.index)
        )
        df["Conglomerado"] = congl_prud.where(congl_prud != "", congl_fin)

    if periodo is not None:
        df["AnoMes"] = str(periodo)
    elif "AnoMes" not in df.columns and "Data" in df.columns:
        df["AnoMes"] = df["Data"].str.strip()

    return df


def _extrair_instituicoes_de_valores(raw_dir: Path) -> pd.DataFrame:
    log.info("Fallback: extraindo CodInst de dados financeiros existentes")
    codinsts: set[str] = set()
    for fpath in sorted(raw_dir.glob("ifdata_rel*.parquet")):
        try:
            df = pd.read_parquet(fpath, columns=["CodInst"])
            codinsts.update(df["CodInst"].dropna().unique())
        except Exception:
            continue
    if not codinsts:
        return pd.DataFrame()
    df = pd.DataFrame(sorted(codinsts), columns=["CodInst"])
    log.info(f"Extraídos {len(df)} CodInst únicos dos dados financeiros")
    return df


class BacenIfdataCadastroScraper(BaseScraper):
    name = "bacen_ifdata_cadastro"
    group = "bacen"
    enabled = True
    phase = 1
    accumulate = False

    title = "BACEN — Cadastro de Instituições Financeiras"
    description = "Cadastro de instituições financeiras autorizadas pelo BCB: segmento prudencial (S1–S5), conglomerado, UF, tipo de controle."
    icon = "🏛️"
    icon_class = "icon-bacen"
    badge = "Trimestral"
    badge_class = "badge-quarterly"
    tags = ["IFData", "BACEN", "cadastro", "instituições", "segmento"]
    source = "BACEN · IFData · Olinda + REST"

    def __init__(self):
        super().__init__()
        settings = _carregar_settings()
        self.odata_cfg = settings.get("odata", {})
        self.extraction = settings.get("extraction", {})
        root_dir = Path(__file__).resolve().parent.parent
        self.raw_dir = root_dir / "data" / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self) -> pd.DataFrame:
        session = nova_session()
        odata = self.odata_cfg
        extr = self.extraction
        base_url = odata["base_url"].rstrip("/")
        cadastro_endpoint = odata["endpoints"]["cadastro"]
        time_range = extr.get("time_range", {})
        # O Swagger atual documenta `$top=100` para este recurso. Valores
        # maiores podem fazer o endpoint retornar HTTP 500.
        top = extr.get("pagination", {}).get("cadastro_top", 100)
        max_retries = extr.get("pagination", {}).get("max_retries", 3)
        retry_delay = extr.get("pagination", {}).get("retry_delay", 5)
        start_year = time_range.get("start_year", 2014)
        quarters = time_range.get("quarters", [3, 6, 9, 12])
        # `gerar_periodos` já ordena do mais recente para o mais antigo.
        # Mantemos todos os períodos para reconstruir o histórico do cadastro.
        periodos = gerar_periodos(start_year, quarters[0], quarters)
        force_refresh = os.getenv("REFRESH_CADASTRO") == "1"

        section("Cadastro IFData — OData + REST + Fallback")
        log.info(
            f"Importando {len(periodos)} períodos de cadastro"
            f"{' (reprocessamento forçado)' if force_refresh else ''}"
        )

        frames_cadastro = []
        cadastro_ok = False

        for periodo in periodos:
            raw_filename = f"ifdata_cadastro_{periodo}.parquet"
            raw_path = self.raw_dir / raw_filename
            if force_refresh and raw_path.exists():
                raw_path.unlink()
                log.info(f"Checkpoint de cadastro removido: {raw_filename}")
            url = f"{base_url}/{cadastro_endpoint}"
            params = {"@AnoMes": str(periodo), "$format": "json"}

            t0 = time.time()
            df = baixar_com_checkpoint(
                session, url, params, raw_path,
                top=top, max_retries=max_retries, retry_delay=retry_delay,
                headers={"Accept": "application/json;odata.metadata=minimal"},
            )

            if df is not None and not df.empty:
                df = normalizar_df_cadastro(df, periodo=periodo)
                frames_cadastro.append(df)
                elapsed = time.time() - t0
                print_done(f"Cadastro OData {periodo}: {len(df)} IFs", elapsed=elapsed)
                cadastro_ok = True
            else:
                print_warn(f"Cadastro OData {periodo}: sem dados")

        if frames_cadastro:
            df_cadastro = pd.concat(frames_cadastro, ignore_index=True).drop_duplicates(
                subset=["CodInst", "AnoMes"], keep="first"
            )
            cadastro_ifs_path = self.raw_dir.parent / "cadastro_ifs.csv"
            df_cadastro.to_csv(cadastro_ifs_path, index=False, encoding="utf-8")
            log.info(
                f"Cadastro OData consolidado: {len(df_cadastro)} registros "
                f"({df_cadastro['CodInst'].nunique()} IFs únicas em "
                f"{df_cadastro['AnoMes'].nunique()} períodos) → {cadastro_ifs_path}"
            )
            return df_cadastro

        log.warning("IfDataCadastro OData indisponível — tentando REST API")
        try:
            catalogo = listar_periodos()
            if catalogo:
                df_rest = baixar_cadastro_unico_mais_recente()
                if df_rest is not None and not df_rest.empty:
                    df_rest = df_rest.drop_duplicates(subset=["CodInst"], keep="last")
                    log.info(f"Cadastro REST: {len(df_rest)} IFs únicas")
                    cols = ["CodInst", "NomeInstituicao", "Segmento", "UF", "AnoMes"]
                    cols_presentes = [c for c in cols if c in df_rest.columns]
                    return df_rest[cols_presentes]
        except Exception as e:
            log.warning(f"REST API falhou: {e}")

        log.warning("REST API indisponível — usando fallback CodInst")
        df_fallback = _extrair_instituicoes_de_valores(self.raw_dir)
        return df_fallback


if __name__ == "__main__":
    BacenIfdataCadastroScraper().run()
