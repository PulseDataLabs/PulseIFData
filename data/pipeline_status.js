window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-09-03T12:15:43.234199",
  "elapsed_seconds": 35.50940203666687,
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
      "elapsed_seconds": 33.45546770095825,
      "error": null,
      "timestamp": "2026-09-03T12:15:43.234304"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 35.50699329376221,
      "error": null,
      "timestamp": "2026-09-03T12:15:43.234304"
    },
    "bacen_conglomerados": {
      "status": "error",
      "elapsed_seconds": 1.2963032722473145,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 138, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 50, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_conglomerados.py\", line 69, in fetch\n    print_warn(f\"{yyyymm}CONGLOMERADO.zip não disponível\", elapsed=time.time() - t0)\n    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nTypeError: print_warn() got an unexpected keyword argument 'elapsed'\n",
      "timestamp": "2026-09-03T12:15:43.234304"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 10.044957160949707,
      "error": null,
      "timestamp": "2026-09-03T12:15:43.234304"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "success",
      "elapsed_seconds": 4.7135632038116455,
      "error": null,
      "timestamp": "2026-09-03T12:15:43.234304"
    }
  },
  "drifts": {}
};
