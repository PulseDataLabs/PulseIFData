#!/usr/bin/env python
# coding: utf-8
"""
PulseIFData – Orquestrador de pipeline

Uso:
  python run_all.py                           # extração + normalização + derivadas
  python run_all.py --scraper-only            # só extração
  python run_all.py --normalize-only          # só normalização
  python run_all.py --derivadas-only          # só métricas derivadas
  python run_all.py --generate-catalog        # só datasets.json
  python run_all.py --sequential              # execução sequencial
"""

import argparse
import importlib
import json
import logging
import sys
import traceback
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("run_all")
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

from scripts.utils.ux import (
    USE_COLOR,
    bold, dim, green, yellow, red, cyan, white,
    b_green, b_yellow, b_red,
    _line, _progress_bar,
    GROUP_ICON, GROUP_COLOR,
    print_done,
)


def _banner() -> None:
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    print()
    print(_line("═"))
    print(
        bold(white("  🏦 PulseIFData")) +
        dim("  Pipeline de Dados do Sistema Financeiro Nacional")
    )
    print(dim(f"  {now}"))
    print(_line("═"))
    print()


def _section(title: str, icon: str = "▶") -> None:
    print()
    print(_line())
    print(f"  {icon}  {bold(title)}")
    print(_line())


def discover_scrapers() -> dict[str, dict]:
    scrapers: dict[str, dict] = {}
    scrapers_dir = Path(__file__).resolve().parent / "scrapers"
    for file_path in sorted(scrapers_dir.glob("*.py")):
        module_name = file_path.stem
        if module_name in ("__init__",):
            continue
        try:
            mod = importlib.import_module(f"scrapers.{module_name}")
            class_name = "".join(w.capitalize() for w in module_name.split("_")) + "Scraper"
            if hasattr(mod, class_name):
                cls = getattr(mod, class_name)
                scrapers[module_name] = {
                    "group":   getattr(cls, "group", "bacen"),
                    "enabled": getattr(cls, "enabled", True),
                    "phase":   getattr(cls, "phase", 1),
                    "class_name": class_name,
                    "title":   getattr(cls, "title", module_name.replace("_", " ").title()),
                }
        except Exception as e:
            logger.warning(yellow(f"  ⚠  Não foi possível carregar metadados de {module_name}: {e}"))
    return scrapers


def run_scraper(module_name: str) -> tuple[bool, float, Optional[str]]:
    t0 = time.time()
    try:
        mod = importlib.import_module(f"scrapers.{module_name}")
        class_name = "".join(w.capitalize() for w in module_name.split("_")) + "Scraper"
        if hasattr(mod, class_name):
            getattr(mod, class_name)().run()
        else:
            msg = f"Módulo {module_name} não possui classe {class_name}"
            return False, time.time() - t0, msg
        return True, time.time() - t0, None
    except Exception:
        return False, time.time() - t0, traceback.format_exc()


def save_pipeline_status(
    results: dict[str, tuple[bool, float, Optional[str]]],
    total_elapsed: float,
) -> None:
    from utils.base import DRIFTS
    root_dir = Path(__file__).resolve().parent
    status_path = root_dir / "data" / "pipeline_status.json"
    status_js_path = root_dir / "data" / "pipeline_status.js"

    status_data: dict = {
        "timestamp": datetime.now().isoformat(),
        "elapsed_seconds": total_elapsed,
        "status": "success",
        "summary": {"total": 0, "success": 0, "failed": 0, "drifts": 0},
        "scrapers": {},
        "drifts": {},
    }

    if status_path.exists():
        try:
            with status_path.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded.get("scrapers"), dict):
                status_data["scrapers"] = loaded["scrapers"]
            if isinstance(loaded.get("drifts"), dict):
                status_data["drifts"] = loaded["drifts"]
        except Exception:
            pass

    now_iso = datetime.now().isoformat()
    for name, (success, elapsed, err) in results.items():
        status_data["scrapers"][name] = {
            "status": "success" if success else "error",
            "elapsed_seconds": elapsed,
            "error": err,
            "timestamp": now_iso,
        }

    processed_files = {f"{n}.csv" for n in results}
    for filename in list(status_data["drifts"].keys()):
        if filename in processed_files:
            del status_data["drifts"][filename]
    for d in DRIFTS:
        status_data["drifts"][d["file"]] = {
            "added": d["added"],
            "removed": d["removed"],
            "timestamp": d["timestamp"],
        }

    scrapers_registry = discover_scrapers()
    active_scrapers = {k: v for k, v in scrapers_registry.items() if v["enabled"]}
    for name in active_scrapers:
        if name not in status_data["scrapers"]:
            status_data["scrapers"][name] = {
                "status": "unknown", "elapsed_seconds": 0.0,
                "error": None, "timestamp": None,
            }

    ok_cnt = sum(1 for s in status_data["scrapers"].values() if s["status"] == "success")
    fail_cnt = sum(1 for s in status_data["scrapers"].values() if s["status"] == "error")
    status_data["summary"] = {
        "total": len(active_scrapers),
        "success": ok_cnt,
        "failed": fail_cnt,
        "drifts": len(status_data["drifts"]),
    }
    status_data["status"] = (
        "error" if fail_cnt > 0 else
        "warning" if status_data["drifts"] else "success"
    )

    try:
        status_path.parent.mkdir(parents=True, exist_ok=True)
        with status_path.open("w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
        with status_js_path.open("w", encoding="utf-8") as f:
            f.write(
                f"window.PULSEIFDATA_PIPELINE_STATUS = "
                f"{json.dumps(status_data, indent=2, ensure_ascii=False)};\n"
            )
        print(f"  {dim('📄 pipeline_status.json atualizado')}")
    except Exception as e:
        logger.error(red(f"  ✖  Erro ao salvar status do pipeline: {e}"))


def main(
    scraper_only: bool = False,
    normalize_only: bool = False,
    derivadas_only: bool = False,
    sequential: bool = False,
) -> None:
    _banner()

    if not normalize_only and not derivadas_only:
        t0 = time.time()
        registry = discover_scrapers()
        targets = {n: info for n, info in registry.items() if info["enabled"]}

        if not targets:
            print(b_red("  ✖  Nenhum scraper encontrado."))
            sys.exit(1)

        total = len(targets)
        _section(f"Extração — {total} scraper{'s' if total > 1 else ''}", "📥")

        results: dict[str, tuple[bool, float, Optional[str]]] = {}

        if sequential:
            for idx, (name, info) in enumerate(targets.items(), 1):
                group = info.get("group", "bacen")
                icon = GROUP_ICON.get(group, "⬜")
                color = GROUP_COLOR.get(group, dim)
                print(f"  {dim(f'{idx}/{total}')}  {icon}  {color(name):<40} {dim('iniciando…')}")
                success, elapsed, err = run_scraper(name)
                if success:
                    print(f"\033[1A\033[2K", end="") if USE_COLOR else None
                    print(f"  {dim(f'{idx}/{total}')}  {icon}  {color(name):<40} {b_green('✔')} {dim(f'{elapsed:.1f}s')}")
                else:
                    print(f"\033[1A\033[2K", end="") if USE_COLOR else None
                    print(f"  {dim(f'{idx}/{total}')}  {icon}  {b_red(name):<40} {b_red('✖')} {dim(f'{elapsed:.1f}s')}")
                results[name] = (success, elapsed, err)
        else:
            with ThreadPoolExecutor(max_workers=4) as ex:
                future_map = {ex.submit(run_scraper, n): n for n in targets}
                done_count = 0
                for future in as_completed(future_map):
                    name = future_map[future]
                    group = targets[name]["group"]
                    icon = GROUP_ICON.get(group, "⬜")
                    color = GROUP_COLOR.get(group, dim)
                    done_count += 1
                    try:
                        success, elapsed, err = future.result()
                    except Exception:
                        success, elapsed, err = False, 0.0, traceback.format_exc()
                    if success:
                        print(f"  {dim(f'{done_count}/{total}')}  {icon}  {color(name):<40} {b_green('✔')} {dim(f'{elapsed:.1f}s')}")
                    else:
                        print(f"  {dim(f'{done_count}/{total}')}  {icon}  {b_red(name):<40} {b_red('✖')} {dim(f'{elapsed:.1f}s')}")
                    results[name] = (success, elapsed, err)
                    print(f"  {_progress_bar(done_count, total)}", end="\r" if done_count < total else "\n")

        total_elapsed = time.time() - t0
        save_pipeline_status(results, total_elapsed)

        ok = sum(1 for r in results.values() if r[0])
        fail = sum(1 for r in results.values() if not r[0])
        print()
        print(f"  {bold('Extração')}: {b_green(f'✔ {ok} ok')}  {'│' if fail else ''}  {b_red(f'✖ {fail} erro(s)') if fail else ''}  │  {cyan(f'⏱ {total_elapsed:.1f}s')}")

    if scraper_only:
        return

    root_dir = Path(__file__).resolve().parent

    if not derivadas_only:
        _section("Normalização: raw/ → processed/ (pivot semântico)", "🔄")
        try:
            import yaml
            import pandas as pd
            from scripts.normalizer import normalizar as run_normalizer

            with open(root_dir / "config" / "settings.yaml", "r", encoding="utf-8") as f:
                settings = yaml.safe_load(f)
            norm_cfg = settings.get("normalization", {})

            raw_dir = root_dir / "data" / "raw"
            output_rel = norm_cfg.get("output", {})
            output_path = root_dir / output_rel.get("dir", "data/processed") / output_rel.get("filename", "ifdata_historical_10y.csv")

            mapping_path = root_dir / "config" / "cosif_semantic_mapping.csv"
            mapping = {}
            if mapping_path.exists():
                df_map = pd.read_csv(mapping_path, dtype=str)
                for _, row in df_map.iterrows():
                    conta = str(row.get("conta_cosif", "")).strip()
                    if conta:
                        mapping[conta] = {
                            "campo": row.get("campo_semantico", "").strip(),
                            "relatorio": row.get("relatorio", "").strip(),
                            "nome_coluna": row.get("nome_coluna", "").strip(),
                        }

            cadastro_path = root_dir / "data" / "cadastro_ifs.csv"
            df = run_normalizer(raw_dir, output_path, mapping, cadastro_path)
            if not df.empty:
                print_done(f"Consolidado: {output_path} ({len(df)} linhas)")
        except Exception as e:
            logger.error(red(f"  ✖  Erro na normalização: {e}"))

    if not normalize_only:
        _section("Métricas Derivadas", "📊")
        try:
            from scripts.derivadas import gerar_tudo
            data_processed = root_dir / "data" / "processed"
            data_dir = root_dir / "data"
            resultados = gerar_tudo(data_processed, data_dir)
            if resultados:
                print_done(f"{len(resultados)} métricas geradas: {', '.join(resultados.keys())}")
        except Exception as e:
            logger.error(red(f"  ✖  Erro nas métricas derivadas: {e}"))

    _section("Catálogo", "📦")
    try:
        from scripts.generate_catalog import generate
        generate()
    except Exception as e:
        logger.error(red(f"  ✖  Erro ao gerar catálogo: {e}"))

    print()
    print(_line("═"))
    print(f"  {bold('Pipeline concluído')}  {green('✔')}")
    print(_line("═"))
    print()


if __name__ == "__main__":
    registry_on_startup = {}
    try:
        registry_on_startup = discover_scrapers()
    except Exception:
        pass
    available_scrapers = sorted(registry_on_startup.keys())

    parser = argparse.ArgumentParser(
        description="🏦 PulseIFData – Orquestrador de pipeline",
    )
    parser.add_argument("--scraper-only", action="store_true", help="Apenas extração")
    parser.add_argument("--normalize-only", action="store_true", help="Apenas normalização")
    parser.add_argument("--derivadas-only", action="store_true", help="Apenas métricas derivadas")
    parser.add_argument("--sequential", action="store_true", help="Execução sequencial")
    parser.add_argument("--generate-catalog", action="store_true", help="Regenera datasets.json e sai")

    args = parser.parse_args()

    if args.generate_catalog:
        _banner()
        _section("Gerando catálogo de datasets", "📦")
        from scripts.generate_catalog import generate
        generate()
        print(b_green("\n  ✔  datasets.json atualizado.\n"))
        sys.exit(0)

    main(
        scraper_only=args.scraper_only,
        normalize_only=args.normalize_only,
        derivadas_only=args.derivadas_only,
        sequential=args.sequential,
    )
