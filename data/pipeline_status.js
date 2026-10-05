window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-10-05T17:35:21.755410",
  "elapsed_seconds": 31.309563636779785,
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
      "elapsed_seconds": 31.306681632995605,
      "error": null,
      "timestamp": "2026-10-05T17:35:21.755552"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 28.162301063537598,
      "error": null,
      "timestamp": "2026-10-05T17:35:21.755552"
    },
    "bacen_conglomerados": {
      "status": "error",
      "elapsed_seconds": 0.7356843948364258,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 138, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 50, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_conglomerados.py\", line 69, in fetch\n    print_warn(f\"{yyyymm}CONGLOMERADO.zip não disponível\", elapsed=time.time() - t0)\n    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nTypeError: print_warn() got an unexpected keyword argument 'elapsed'\n",
      "timestamp": "2026-10-05T17:35:21.755552"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 6.820737838745117,
      "error": null,
      "timestamp": "2026-10-05T17:35:21.755552"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "success",
      "elapsed_seconds": 3.3460512161254883,
      "error": null,
      "timestamp": "2026-10-05T17:35:21.755552"
    }
  },
  "drifts": {}
};
