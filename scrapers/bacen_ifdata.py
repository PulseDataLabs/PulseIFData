import sys
import time
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scrapers.utils.base import BaseScraper
from scrapers.utils.odata import baixar_com_checkpoint, gerar_periodos
from utils.base import nova_session, get_logger
from scripts.utils.ux import print_done, print_warn, print_skip

log = get_logger("bacen_ifdata")


def _carregar_settings() -> dict:
    settings_path = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
    if not settings_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {settings_path}")
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class BacenIfdataScraper(BaseScraper):
    name = "bacen_ifdata"
    group = "bacen"
    enabled = True
    phase = 1
    accumulate = False

    title = "BACEN — IFData (todos os relatórios)"
    description = "Dados do IFData/BACEN: balanço, resultado, crédito, cadastro e capital. Coletados via API OData Olinda com paginação e checkpointing trimestral."
    icon = "🏦"
    icon_class = "icon-bacen"
    badge = "Trimestral"
    badge_class = "badge-quarterly"
    tags = ["IFData", "BACEN", "Cosif", "SCR", "balanço", "crédito"]
    source = "BACEN · IFData · Olinda"

    def __init__(self):
        super().__init__()
        settings = _carregar_settings()
        self.extraction = settings.get("extraction", {})
        self.odata_cfg = settings.get("odata", {})

        root_dir = Path(__file__).resolve().parent.parent
        self.raw_dir = root_dir / "data" / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def fetch(self) -> pd.DataFrame:
        session = nova_session()
        odata = self.odata_cfg
        extr = self.extraction

        base_url = odata["base_url"].rstrip("/")
        valores_endpoint = odata["endpoints"]["valores"]

        top = extr.get("pagination", {}).get("top", 5000)
        max_retries = extr.get("pagination", {}).get("max_retries", 3)
        retry_delay = extr.get("pagination", {}).get("retry_delay", 5)
        rate_limit = extr.get("rate_limit", 1.0)

        reports = extr.get("reports", [])
        inst_types = extr.get("institution_types", [])
        time_range = extr.get("time_range", {})

        start_year = time_range.get("start_year", 2014)
        start_month = time_range.get("start_month", 1)
        quarters = time_range.get("quarters", [3, 6, 9, 12])
        periodos = gerar_periodos(start_year, start_month, quarters)

        log.info(
            f"Extraindo {len(reports)} relatórios × {len(inst_types)} tipos de IF "
            f"× {len(periodos)} trimestres ({start_year}-{periodos[0] if periodos else 'N/A'})"
        )

        frames_totais = []
        total = len(reports) * len(inst_types) * len(periodos)
        concluido = 0

        for relatorio in reports:
            rel_id = relatorio["id"]
            rel_name = relatorio.get("name", rel_id)

            for tipo in inst_types:
                tipo_codigo = tipo["codigo"]
                tipo_label = tipo.get("label", str(tipo_codigo))

                for periodo in periodos:
                    concluido += 1
                    self.logger.info(
                        f"[{concluido}/{total}] Rel {rel_id} ({rel_name}) | "
                        f"Tipo {tipo_codigo} ({tipo_label}) | "
                        f"Período {periodo}"
                    )

                    raw_filename = f"ifdata_rel{rel_id}_{periodo}_tipo{tipo_codigo}.csv"
                    raw_path = self.raw_dir / raw_filename

                    if raw_path.exists() and raw_path.stat().st_size > 0:
                        print_skip(f"Checkpoint: {raw_filename}")
                        try:
                            df_existing = pd.read_csv(raw_path)
                            if not df_existing.empty:
                                frames_totais.append(df_existing)
                                continue
                        except Exception:
                            pass

                    url = f"{base_url}/{valores_endpoint}"
                    params = {
                        "@AnoMes": str(periodo),
                        "@TipoInstituicao": str(tipo_codigo),
                        "@Relatorio": f"'{rel_id}'",
                        "$format": "json",
                    }

                    t0 = time.time()
                    df = baixar_com_checkpoint(
                        session, url, params, raw_path,
                        top=top, max_retries=max_retries, retry_delay=retry_delay,
                    )

                    if df is None or df.empty:
                        print_warn(
                            f"Sem dados: rel={rel_id} tipo={tipo_codigo} período={periodo}"
                        )
                        continue

                    df["AnoMes"] = str(periodo)
                    df["TipoInstituicao"] = tipo_codigo
                    df["NomeRelatorio"] = rel_name
                    df["NumeroRelatorio"] = rel_id

                    elapsed = time.time() - t0
                    print_done(f"{raw_filename} — {len(df)} registros", elapsed=elapsed)

                    frames_totais.append(df)
                    time.sleep(rate_limit)

        if not frames_totais:
            raise RuntimeError("Nenhum dado retornado da API IFData.")

        df_final = pd.concat(frames_totais, ignore_index=True)
        log.info(f"Total consolidado: {len(df_final)} registros de {len(frames_totais)} chunks")
        return df_final
