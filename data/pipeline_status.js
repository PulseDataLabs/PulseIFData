window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-11-05T16:04:18.995651",
  "elapsed_seconds": 40.438488483428955,
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
      "elapsed_seconds": 33.479655265808105,
      "error": null,
      "timestamp": "2026-11-05T16:04:18.995752"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 40.4346399307251,
      "error": null,
      "timestamp": "2026-11-05T16:04:18.995752"
    },
    "bacen_conglomerados": {
      "status": "error",
      "elapsed_seconds": 0.6989233493804932,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 138, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 50, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_conglomerados.py\", line 69, in fetch\n    print_warn(f\"{yyyymm}CONGLOMERADO.zip não disponível\", elapsed=time.time() - t0)\n    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nTypeError: print_warn() got an unexpected keyword argument 'elapsed'\n",
      "timestamp": "2026-11-05T16:04:18.995752"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 7.44153618812561,
      "error": null,
      "timestamp": "2026-11-05T16:04:18.995752"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "success",
      "elapsed_seconds": 4.453164577484131,
      "error": null,
      "timestamp": "2026-11-05T16:04:18.995752"
    }
  },
  "drifts": {}
};
