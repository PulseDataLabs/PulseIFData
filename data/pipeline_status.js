window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-07-06T11:30:58.581522",
  "elapsed_seconds": 26.22383165359497,
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
      "elapsed_seconds": 25.717636346817017,
      "error": null,
      "timestamp": "2026-07-06T11:30:58.581624"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 26.2208149433136,
      "error": null,
      "timestamp": "2026-07-06T11:30:58.581624"
    },
    "bacen_conglomerados": {
      "status": "error",
      "elapsed_seconds": 0.3200807571411133,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 136, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 48, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_conglomerados.py\", line 69, in fetch\n    print_warn(f\"{yyyymm}CONGLOMERADO.zip não disponível\", elapsed=time.time() - t0)\n    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nTypeError: print_warn() got an unexpected keyword argument 'elapsed'\n",
      "timestamp": "2026-07-06T11:30:58.581624"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 7.971034526824951,
      "error": null,
      "timestamp": "2026-07-06T11:30:58.581624"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "success",
      "elapsed_seconds": 4.387523412704468,
      "error": null,
      "timestamp": "2026-07-06T11:30:58.581624"
    }
  },
  "drifts": {}
};
