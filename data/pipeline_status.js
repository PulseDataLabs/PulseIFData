window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-09-01T13:10:24.248588",
  "elapsed_seconds": 29.924558639526367,
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
      "elapsed_seconds": 28.117491722106934,
      "error": null,
      "timestamp": "2026-09-01T13:10:24.248684"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 29.922178983688354,
      "error": null,
      "timestamp": "2026-09-01T13:10:24.248684"
    },
    "bacen_conglomerados": {
      "status": "error",
      "elapsed_seconds": 0.8284709453582764,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 138, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 50, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_conglomerados.py\", line 69, in fetch\n    print_warn(f\"{yyyymm}CONGLOMERADO.zip não disponível\", elapsed=time.time() - t0)\n    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nTypeError: print_warn() got an unexpected keyword argument 'elapsed'\n",
      "timestamp": "2026-09-01T13:10:24.248684"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 6.91986346244812,
      "error": null,
      "timestamp": "2026-09-01T13:10:24.248684"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "success",
      "elapsed_seconds": 4.170573711395264,
      "error": null,
      "timestamp": "2026-09-01T13:10:24.248684"
    }
  },
  "drifts": {}
};
