window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-08-03T11:05:22.662183",
  "elapsed_seconds": 34.42536234855652,
  "status": "error",
  "summary": {
    "total": 5,
    "success": 4,
    "failed": 1,
    "drifts": 0
  },
  "scrapers": {
    "bacen_ifdata": {
      "status": "success",
      "elapsed_seconds": 34.42291975021362,
      "error": null,
      "timestamp": "2026-08-03T11:05:22.662365"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 32.23583722114563,
      "error": null,
      "timestamp": "2026-08-03T11:05:22.662365"
    },
    "bacen_conglomerados": {
      "status": "error",
      "elapsed_seconds": 1.0797264575958252,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 138, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 50, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_conglomerados.py\", line 69, in fetch\n    print_warn(f\"{yyyymm}CONGLOMERADO.zip não disponível\", elapsed=time.time() - t0)\n    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nTypeError: print_warn() got an unexpected keyword argument 'elapsed'\n",
      "timestamp": "2026-08-03T11:05:22.662365"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 7.850302219390869,
      "error": null,
      "timestamp": "2026-08-03T11:05:22.662365"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "success",
      "elapsed_seconds": 4.678127288818359,
      "error": null,
      "timestamp": "2026-08-03T11:05:22.662365"
    }
  },
  "drifts": {}
};
