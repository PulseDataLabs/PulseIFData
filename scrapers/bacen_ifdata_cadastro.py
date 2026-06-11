import sys
import time
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.base import BaseScraper
from scrapers.utils.odata import paginar_odata, baixar_com_checkpoint, gerar_periodos
from utils.base import nova_session, get_logger
from scripts.utils.ux import print_done, print_warn, print_skip, section

log = get_logger("bacen_ifdata_cadastro")


def _carregar_settings() -> dict:
    settings_path = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _extrair_instituicoes_de_valores(raw_dir: Path) -> pd.DataFrame:
    """
    Fallback: extrai CodInst únicos dos dados financeiros já baixados.
    Útil quando IfDataCadastro está fora do ar (HTTP 500).
    """
    log.info("Fallback: extraindo CodInst de dados financeiros existentes")
    codinsts: set[str] = set()
    for fpath in sorted(raw_dir.glob("ifdata_rel*.csv")):
        try:
            df = pd.read_csv(fpath, usecols=["CodInst"], dtype=str)
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
    source = "BACEN · IFData · Olinda"

    def __init__(self):
        super().__init__()
        settings = _carregar_settings()
        self.odata_cfg = settings.get("odata", {})
        self.extraction = settings.get("extraction", {})
        root_dir = Path(__file__).resolve().parents[2]
        self.raw_dir = root_dir / "data" / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self) -> pd.DataFrame:
        session = nova_session()
        odata = self.odata_cfg
        extr = self.extraction

        base_url = odata["base_url"].rstrip("/")
        cadastro_endpoint = odata["endpoints"]["cadastro"]
        time_range = extr.get("time_range", {})

        top = extr.get("pagination", {}).get("top", 5000)
        max_retries = extr.get("pagination", {}).get("max_retries", 3)
        retry_delay = extr.get("pagination", {}).get("retry_delay", 5)

        start_year = time_range.get("start_year", 2014)
        quarters = time_range.get("quarters", [3, 6, 9, 12])

        periodos = gerar_periodos(start_year, quarters[0], quarters, end_year=start_year + 1)[:4]
        periodos = [p for p in periodos if p >= 202400]

        section("Cadastro IFData (IfDataCadastro)")

        frames_cadastro = []
        cadastro_ok = False

        for periodo in periodos:
            raw_filename = f"ifdata_cadastro_{periodo}.csv"
            raw_path = self.raw_dir / raw_filename

            url = f"{base_url}/{cadastro_endpoint}"
            params = {
                "@AnoMes": str(periodo),
                "$format": "json",
            }

            t0 = time.time()
            df = baixar_com_checkpoint(
                session, url, params, raw_path,
                top=top, max_retries=max_retries, retry_delay=retry_delay,
            )

            if df is not None and not df.empty:
                df["AnoMes"] = str(periodo)
                frames_cadastro.append(df)
                elapsed = time.time() - t0
                print_done(f"Cadastro {periodo}: {len(df)} IFs", elapsed=elapsed)
                cadastro_ok = True
            else:
                print_warn(f"Cadastro {periodo}: sem dados")

        if frames_cadastro:
            df_cadastro = pd.concat(frames_cadastro, ignore_index=True).drop_duplicates(
                subset=["CodInst"], keep="last"
            )
            log.info(f"Cadastro consolidado: {len(df_cadastro)} IFs únicas")
            return df_cadastro

        if not cadastro_ok:
            log.warning("IfDataCadastro indisponível (500). Usando fallback.")
            df_fallback = _extrair_instituicoes_de_valores(self.raw_dir)
            return df_fallback

        return pd.DataFrame()
