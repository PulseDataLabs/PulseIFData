import csv
import json
import logging
import sys
import time
from base64 import b64encode
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import urllib3
import urllib3.response
from urllib3.exceptions import InvalidChunkLength

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _patched_update_chunk_length(self):
    if self.chunk_left is not None:
        return
    if not self._fp or not hasattr(self._fp, "fp") or not self._fp.fp:
        self.chunk_left = 0
        return
    try:
        line = self._fp.fp.readline()
        line = line.split(b";", 1)[0]
    except Exception:
        self.chunk_left = 0
        return
    try:
        self.chunk_left = int(line, 16)
    except ValueError:
        if not line or line.strip() == b"":
            self.chunk_left = 0
        else:
            self.close()
            raise InvalidChunkLength(self, line)

urllib3.response.HTTPResponse._update_chunk_length = _patched_update_chunk_length

_orig_request = requests.Session.request

def _patched_request(self, method, url, *args, **kwargs):
    kwargs["verify"] = False
    timeout = kwargs.get("timeout")
    if timeout is None:
        kwargs["timeout"] = (10, 30)
    elif isinstance(timeout, (int, float)):
        conn = min(timeout, 10)
        read = min(timeout, 30)
        kwargs["timeout"] = (conn, read)
    elif isinstance(timeout, tuple):
        conn, read = timeout
        conn_val = min(conn, 10) if conn is not None else 10
        read_val = min(read, 30) if read is not None else 30
        kwargs["timeout"] = (conn_val, read_val)
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        try:
            resp = _orig_request(self, method, url, *args, **kwargs)
            if resp.status_code in (502, 503, 504) and attempt < max_attempts:
                time.sleep(1.0)
                continue
            return resp
        except requests.exceptions.ConnectTimeout as e:
            raise e
        except requests.RequestException as e:
            if attempt == max_attempts:
                raise e
            time.sleep(1.0)

requests.Session.request = _patched_request

DRIFTS = []
FUSO = ZoneInfo("America/Sao_Paulo")

HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept":  "application/json, text/plain, */*",
    "Referer": "https://www.bcb.gov.br/",
    "Origin":  "https://www.bcb.gov.br",
}

def get_logger(name: str) -> logging.Logger:
    try:
        from scripts.utils.ux import ColorLogger
        return ColorLogger(name)
    except Exception:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        return logging.getLogger(name)

def agora_brt() -> tuple[str, str]:
    now = datetime.now(FUSO)
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

def limpar(valor) -> str:
    if valor is None:
        return ""
    return str(valor).strip()

def nova_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS_HTTP)
    return s

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

def _salvar_csv_logger():
    from scripts.utils.ux import ColorLogger
    return ColorLogger("utils.salvar_csv")

def salvar_csv(
    arquivo: Path,
    registros: list[dict],
    cabecalho: list[str],
    chaves_dedup: list[str] | None = None,
    acumular: bool = True,
) -> None:
    log = _salvar_csv_logger()
    if not registros:
        log.warning("Nenhum registro para salvar — abortando.")
        sys.exit(1)
    try:
        schemas_path = arquivo.parent / "schemas.json"
        if schemas_path.exists() and registros:
            with schemas_path.open("r", encoding="utf-8") as sf:
                schemas = json.load(sf)
            filtered_cols = [c for c in cabecalho if c not in ("conjunto", "arquivo_origem", "registro_hash", "dt_captura")]
            import re
            for s in schemas:
                files_declared = [f.strip() for f in re.split(r'·| e ', s.get("files", ""))]
                if arquivo.name in files_declared:
                    existing_cols = [f["name"] for f in s.get("fields", [])]
                    added = [c for c in filtered_cols if c not in existing_cols]
                    removed = []
                    if len(files_declared) == 1:
                        removed = [c for c in existing_cols if c not in filtered_cols]
                    if added or removed:
                        drift_info = {
                            "file": arquivo.name,
                            "added": added,
                            "removed": removed,
                            "timestamp": datetime.now().isoformat()
                        }
                        DRIFTS.append(drift_info)
                        log.warning(f"SCHEMA DRIFT detectado em {arquivo.name}: Adicionadas: {added} | Removidas: {removed}")
                    break
    except Exception as e:
        log.warning(f"Erro ao detectar schema drift para {arquivo.name}: {e}")

    arquivo.parent.mkdir(parents=True, exist_ok=True)

    if acumular and arquivo.exists():
        header_existente = read_existing_header(arquivo)
        merged = []
        for col in header_existente + cabecalho:
            if col and col not in merged:
                merged.append(col)
        cabecalho = merged

    datas_novas = {r.get("data_captura") for r in registros}
    chaves_novas: set[tuple] | None = None
    if chaves_dedup:
        chaves_novas = {
            tuple(r.get(c, "") for c in chaves_dedup)
            for r in registros
        }

    linhas_anteriores: list[dict] = []
    substituidas = 0

    if acumular and arquivo.exists():
        with arquivo.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for linha in reader:
                if chaves_novas is not None:
                    chave = tuple(linha.get(c, "") for c in chaves_dedup)
                    if chave in chaves_novas:
                        substituidas += 1
                        continue
                else:
                    if linha.get("data_captura") in datas_novas:
                        substituidas += 1
                        continue
                linhas_anteriores.append(linha)

    todas = linhas_anteriores + registros

    with arquivo.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cabecalho, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(todas)

    try:
        last_updates_path = arquivo.parent / "last_updates.json"
        last_updates = {}
        if last_updates_path.exists():
            try:
                with last_updates_path.open("r", encoding="utf-8") as lf:
                    last_updates = json.load(lf)
            except Exception:
                pass
        if registros:
            date_col = None
            for candidate in ["data_captura", "data_base", "AnoMes", "data"]:
                if candidate in cabecalho:
                    date_col = candidate
                    break
            if date_col:
                datas = [r.get(date_col) for r in todas if r.get(date_col)]
                if datas:
                    last_updates[arquivo.name] = {
                        "min": min(datas),
                        "max": max(datas)
                    }
                    with last_updates_path.open("w", encoding="utf-8") as lf:
                        json.dump(last_updates, lf, indent=2, ensure_ascii=False)
                    last_updates_js_path = arquivo.parent / "last_updates.js"
                    with last_updates_js_path.open("w", encoding="utf-8") as lf:
                        lf.write(f"window.PULSEIFDATA_LAST_UPDATES = {json.dumps(last_updates, indent=2, ensure_ascii=False)};\n")
    except Exception as e:
        log.warning(f"Não foi possível atualizar last_updates.json/js: {e}")

    try:
        import re
        schemas_path = arquivo.parent / "schemas.json"
        schemas = []
        if schemas_path.exists():
            try:
                with schemas_path.open("r", encoding="utf-8") as sf:
                    schemas = json.load(sf)
            except Exception:
                pass

        def get_type_badge(col_name):
            col_name = col_name.lower()
            if "data" in col_name or "date" in col_name or col_name.startswith("dt_"):
                return "date"
            if any(k in col_name for k in ("saldo", "valor", "pct", "taxa", "indice", "preco", "vl_", "vr_")):
                return "float"
            if any(k in col_name for k in ("qt_", "nr_", "quantidade", "numero", "ranking")):
                return "int"
            return "str"

        filtered_cols = [c for c in cabecalho if c not in ("conjunto", "arquivo_origem", "registro_hash", "dt_captura")]
        first_reg = registros[0] if registros else {}
        fields = []
        for c in filtered_cols:
            t_badge = get_type_badge(c)
            ex_val = str(first_reg.get(c, ""))
            if ex_val in ("nan", "None"):
                ex_val = ""
            fields.append({"name": c, "type": t_badge, "example": ex_val})

        found = False
        for s in schemas:
            files_declared = [f.strip() for f in re.split(r'·| e ', s.get("files", ""))]
            if arquivo.name in files_declared:
                if len(files_declared) > 1:
                    new_names = {f["name"] for f in fields}
                    merged_fields = fields.copy()
                    for existing_field in s.get("fields", []):
                        if existing_field["name"] not in new_names:
                            merged_fields.append(existing_field)
                    s["fields"] = merged_fields
                else:
                    s["fields"] = fields
                found = True
                break

        if not found:
            guessed_title = arquivo.name.replace(".csv", "").replace("_", " ").title()
            schemas.append({
                "title": guessed_title,
                "files": arquivo.name,
                "source": "bacen",
                "fields": fields
            })

        with schemas_path.open("w", encoding="utf-8") as sf:
            json.dump(schemas, sf, indent=2, ensure_ascii=False)
    except Exception as e:
        log.warning(f"Não foi possível atualizar schemas.json: {e}")

    log.info(
        f"CSV atualizado → {arquivo} | "
        f"{len(registros)} novos registros salvos"
        + (f" | {substituidas} linha(s) antigas substituídas" if substituidas else "")
    )
