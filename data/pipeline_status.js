window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-07-02T09:51:03.491928",
  "elapsed_seconds": 31.606131076812744,
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
      "elapsed_seconds": 31.603660106658936,
      "error": null,
      "timestamp": "2026-07-02T09:51:03.492071"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 30.598845958709717,
      "error": null,
      "timestamp": "2026-07-02T09:51:03.492071"
    },
    "bacen_conglomerados": {
      "status": "error",
      "elapsed_seconds": 0.8531618118286133,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 136, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 48, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_conglomerados.py\", line 69, in fetch\n    print_warn(f\"{yyyymm}CONGLOMERADO.zip não disponível\", elapsed=time.time() - t0)\n    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nTypeError: print_warn() got an unexpected keyword argument 'elapsed'\n",
      "timestamp": "2026-07-02T09:51:03.492071"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 6.2876060009002686,
      "error": null,
      "timestamp": "2026-07-02T09:51:03.492071"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "success",
      "elapsed_seconds": 6.561091661453247,
      "error": null,
      "timestamp": "2026-07-02T09:51:03.492071"
    }
  },
  "drifts": {}
};
