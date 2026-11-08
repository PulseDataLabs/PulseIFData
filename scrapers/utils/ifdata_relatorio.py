#!/usr/bin/env python
# coding: utf-8
"""
Classe base compartilhada para os 16 scrapers de relatórios do IFData (API OData Olinda).
Cada subclasse define `relatorio_id`, `name`, `title`, `description` e `tags`,
baixando os checkpoints Parquet em `data/raw/ifdata_rel{id}_{periodo}_tipo{tipo}.parquet`
e consolidando a série histórica completa em `data/{name}.csv.gz` via Polars.
"""
import gzip
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

import pandas as pd
import polars as pl
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scrapers.utils.base import BaseScraper
from scrapers.utils.odata import baixar_com_checkpoint, gerar_periodos
from scripts.utils.ux import print_done, print_skip, print_warn, section
from utils.base import agora_brt, get_logger, nova_session

TIPO_LABELS = {
    "1": "conglomerados_prudenciais",
    "2": "conglomerados_financeiros",
    "3": "instituicoes_individuais",
    "4": "instituicoes_cambio",
}


def carregar_settings() -> dict:
    settings_path = Path(__file__).resolve().parents[2] / "config" / "settings.yaml"
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def tipos_validos_para_relatorio(rel_id: str, periodo: int) -> list[tuple[int, str]]:
    """
    Retorna os tipos de instituição que possuem dados publicados na API Olinda
    para cada relatório e período (evitando requisições sabidamente vazias):
      - Relatórios 1, 2, 3, 4: tipos 1, 2 e 3 em todos os períodos.
      - Relatório 5 (Capital): tipo 2 em 2014; tipo 1 a partir de 201503.
      - Relatório 6 (Segmentação): tipo 1 a partir de 201703.
      - Relatórios 7, 9, 10, 11, 12, 13, 14 (Carteira de Crédito):
        tipo 2 até 202412; tipo 1 a partir de 202503.
      - Relatório 8 (Nível de risco): tipo 2 até 202412 (substituído pelo Rel 16 em 202503).
      - Relatório 15 (Câmbio): tipo 4 até 202306; tipo 1 a partir de 202309 (se houver).
      - Relatório 16 (Instrumentos financeiros - Res. 4.966): tipo 1 a partir de 202503.
    """
    rel_id = str(rel_id)
    if rel_id in ("1", "2", "3", "4"):
        cods = [1, 2, 3]
    elif rel_id == "5":
        cods = [2] if periodo <= 201412 else [1]
    elif rel_id == "6":
        if periodo < 201703:
            return []
        cods = [1]
    elif rel_id in ("7", "9", "10", "11", "12", "13", "14"):
        cods = [2] if periodo <= 202412 else [1]
    elif rel_id == "8":
        if periodo >= 202503:
            return []
        cods = [2]
    elif rel_id == "15":
        if periodo > 202306:
            return []
        cods = [4]
    elif rel_id == "16":
        if periodo < 202503:
            return []
        cods = [1]
    else:
        cods = [1, 2, 3]

    return [(c, TIPO_LABELS[str(c)]) for c in cods]


def atualizar_metadados_csv(
    arquivo: Path,
    title: str,
    df_sample: dict,
    min_per: str,
    max_per: str,
    cols: list[str],
    log,
) -> None:
    try:
        last_updates_path = arquivo.parent / "last_updates.json"
        last_updates = {}
        if last_updates_path.exists():
            try:
                with last_updates_path.open("r", encoding="utf-8") as lf:
                    last_updates = json.load(lf)
            except Exception:
                pass

        if min_per and max_per:
            last_updates[arquivo.name] = {"min": str(min_per), "max": str(max_per)}
            with last_updates_path.open("w", encoding="utf-8") as lf:
                json.dump(last_updates, lf, indent=2, ensure_ascii=False)
            last_updates_js_path = arquivo.parent / "last_updates.js"
            with last_updates_js_path.open("w", encoding="utf-8") as lf:
                lf.write(
                    f"window.PULSEIFDATA_LAST_UPDATES = "
                    f"{json.dumps(last_updates, indent=2, ensure_ascii=False)};\n"
                )
    except Exception as e:
        log.warning(f"Não foi possível atualizar last_updates.json/js: {e}")

    try:
        schemas_path = arquivo.parent / "schemas.json"
        schemas = []
        if schemas_path.exists():
            try:
                with schemas_path.open("r", encoding="utf-8") as sf:
                    schemas = json.load(sf)
            except Exception:
                pass

        def get_type_badge(col_name: str) -> str:
            c_low = col_name.lower()
            if "data" in c_low or "date" in c_low or c_low.startswith("dt_"):
                return "date"
            if any(k in c_low for k in ("saldo", "valor", "pct", "taxa", "indice", "preco", "vl_", "vr_")):
                return "float"
            if any(k in c_low for k in ("qt_", "nr_", "quantidade", "numero", "ranking")):
                return "int"
            return "str"

        fields = []
        for c in cols:
            val = str(df_sample.get(c, "") or "")
            if val in ("nan", "None"):
                val = ""
            fields.append({"name": c, "type": get_type_badge(c), "example": val})

        found = False
        for s in schemas:
            files_declared = [f.strip() for f in re.split(r"·| e ", s.get("files", ""))]
            if arquivo.name in files_declared:
                s["fields"] = fields
                found = True
                break

        if not found:
            schemas.append({
                "title": title,
                "files": arquivo.name,
                "source": "bacen",
                "fields": fields,
            })

        with schemas_path.open("w", encoding="utf-8") as sf:
            json.dump(schemas, sf, indent=2, ensure_ascii=False)
    except Exception as e:
        log.warning(f"Não foi possível atualizar schemas.json: {e}")


class IfdataRelatorioBaseScraper(BaseScraper):
    relatorio_id: str = ""
    relatorio_nome: str = ""
    group = "bacen"
    enabled = True
    phase = 1
    accumulate = False
    save_csv = False
    compress = True
    chaves_dedup = ["AnoMes", "CodInst", "TipoInstituicao", "Conta"]
    icon = "🏦"
    icon_class = "icon-bacen"
    badge = "Trimestral"
    badge_class = "badge-quarterly"
    source = "BACEN · IFData · Olinda"

    def __init__(self):
        super().__init__()
        settings = carregar_settings()
        self.extraction = settings.get("extraction", {})
        self.odata_cfg = settings.get("odata", {})
        root_dir = Path(__file__).resolve().parents[2]
        self.raw_dir = root_dir / "data" / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.log = get_logger(self.name)

    def ConsolidateParquets(self) -> None:
        arquivos = sorted(self.raw_dir.glob(f"ifdata_rel{self.relatorio_id}_*.parquet"))
        if not arquivos:
            raise RuntimeError(
                f"Nenhum arquivo Parquet do Relatório {self.relatorio_id} ({self.relatorio_nome}) encontrado."
            )

        self.log.info(
            f"Consolidando {len(arquivos)} arquivos Parquet do Relatório {self.relatorio_id} via Polars..."
        )
        t_cons = time.time()
        df_pl = pl.read_parquet(arquivos)

        if df_pl.is_empty():
            raise RuntimeError(f"Dados consolidados do Relatório {self.relatorio_id} estão vazios.")

        data_captura, _ = agora_brt()

        clean_exprs = [
            pl.lit(data_captura).alias("data_captura"),
            pl.col("TipoInstituicao")
            .cast(pl.String)
            .replace_strict(TIPO_LABELS, default=pl.col("TipoInstituicao").cast(pl.String))
            .alias("tipo_instituicao_label"),
        ]

        for text_col in ("NomeRelatorio", "Grupo", "NomeColuna", "DescricaoColuna"):
            if text_col in df_pl.columns:
                clean_exprs.append(
                    pl.col(text_col)
                    .cast(pl.String)
                    .fill_null("")
                    .str.replace_all(r"[\r\n]+", " ")
                    .str.strip_chars()
                    .alias(text_col)
                )

        if "Saldo" in df_pl.columns:
            clean_exprs.append(
                pl.col("Saldo")
                .cast(pl.String)
                .fill_null("")
                .str.strip_chars()
                .str.replace_all(",", ".", literal=True)
                .alias("Saldo")
            )

        df_pl = df_pl.with_columns(clean_exprs)

        cols_ordem = [
            "data_captura",
            "TipoInstituicao",
            "CodInst",
            "AnoMes",
            "NomeRelatorio",
            "NumeroRelatorio",
            "Grupo",
            "Conta",
            "NomeColuna",
            "DescricaoColuna",
            "Saldo",
            "tipo_instituicao_label",
        ]
        cols_presentes = [c for c in cols_ordem if c in df_pl.columns]
        cols_restantes = [c for c in df_pl.columns if c not in cols_ordem]
        final_cols = cols_presentes + cols_restantes

        df_pl = (
            df_pl.select(final_cols)
            .unique(subset=["AnoMes", "CodInst", "TipoInstituicao", "Conta"], keep="first")
            .sort(["AnoMes", "TipoInstituicao", "CodInst", "Conta"], descending=[True, False, False, False])
        )

        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(self.output_file, "wb") as gz_out:
            df_pl.write_csv(gz_out)

        min_per = df_pl["AnoMes"].min() if "AnoMes" in df_pl.columns else ""
        max_per = df_pl["AnoMes"].max() if "AnoMes" in df_pl.columns else ""
        first_row = df_pl.head(1).to_dicts()[0] if len(df_pl) > 0 else {}
        atualizar_metadados_csv(
            self.output_file,
            self.title,
            first_row,
            str(min_per),
            str(max_per),
            final_cols,
            self.log,
        )

        print_done(
            f"Relatório {self.relatorio_id} ({self.relatorio_nome}): "
            f"{len(df_pl)} linhas ({min_per}–{max_per}) → {self.output_file.name}",
            elapsed=time.time() - t_cons,
        )

    def fetch(self) -> pd.DataFrame:
        odata = self.odata_cfg
        extr = self.extraction

        base_url = odata["base_url"].rstrip("/")
        valores_endpoint = odata["endpoints"]["valores"]

        top = extr.get("pagination", {}).get("top", 5000)
        max_retries = extr.get("pagination", {}).get("max_retries", 3)
        retry_delay = extr.get("pagination", {}).get("retry_delay", 5)

        time_range = extr.get("time_range", {})
        start_year = time_range.get("start_year", 2014)
        start_month = time_range.get("start_month", 3)
        quarters = time_range.get("quarters", [3, 6, 9, 12])

        existing_parquets = list(self.raw_dir.glob(f"ifdata_rel{self.relatorio_id}_*.parquet"))
        if os.getenv("SCRAPE_LATEST_ONLY") == "1" and existing_parquets:
            self.log.info(f"Modo SCRAPE_LATEST_ONLY ativo para Relatório {self.relatorio_id}.")
            start_year = date.today().year - 1
            start_month = 1

        periodos = gerar_periodos(start_year, start_month, quarters)
        force_refresh = os.getenv("REFRESH_IFDATA_REL") == "1" or (
            self.relatorio_id == "3" and os.getenv("REFRESH_PASSIVO") == "1"
        )

        section(f"IFData Relatório {self.relatorio_id} — {self.relatorio_nome}")

        tarefas = []
        checkpoints_pulados = 0

        for periodo in periodos:
            for tipo_codigo, tipo_label in tipos_validos_para_relatorio(self.relatorio_id, periodo):
                raw_filename = f"ifdata_rel{self.relatorio_id}_{periodo}_tipo{tipo_codigo}.parquet"
                raw_path = self.raw_dir / raw_filename

                if force_refresh and raw_path.exists():
                    raw_path.unlink()

                if raw_path.exists() and raw_path.stat().st_size > 0:
                    checkpoints_pulados += 1
                    continue

                tarefas.append((periodo, tipo_codigo, tipo_label, raw_path, raw_filename))

        if checkpoints_pulados:
            print_skip(
                f"{checkpoints_pulados} checkpoints do Relatório {self.relatorio_id} já existentes em data/raw/"
            )

        url = f"{base_url}/{valores_endpoint}"

        def _baixar_item(item: tuple) -> tuple[str, int, float]:
            periodo, tipo_codigo, tipo_label, raw_path, raw_filename = item
            session = nova_session()
            params = {
                "@AnoMes": str(periodo),
                "@TipoInstituicao": str(tipo_codigo),
                "@Relatorio": f"'{self.relatorio_id}'",
                "$format": "json",
            }
            t0 = time.time()
            df = baixar_com_checkpoint(
                session,
                url,
                params,
                raw_path,
                top=top,
                max_retries=max_retries,
                retry_delay=retry_delay,
                headers={"Accept": "application/json;odata.metadata=minimal"},
            )
            elapsed = time.time() - t0
            rows = len(df) if df is not None and not df.empty else 0
            return raw_filename, rows, elapsed

        if tarefas:
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = {pool.submit(_baixar_item, t): t for t in tarefas}
                for fut in as_completed(futures):
                    periodo, tipo_codigo, tipo_label, _, raw_filename = futures[fut]
                    try:
                        fname, rows, elapsed = fut.result()
                        if rows > 0:
                            print_done(f"{fname} — {rows} registros", elapsed=elapsed)
                        else:
                            print_warn(
                                f"Sem dados: rel={self.relatorio_id} tipo={tipo_codigo} período={periodo}"
                            )
                    except Exception as e:
                        self.log.warning(f"Erro em {raw_filename}: {e}")

        self.ConsolidateParquets()
        return pd.DataFrame()

