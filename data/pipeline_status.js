window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-08-07T08:54:01.103552",
  "elapsed_seconds": 27.71119213104248,
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
      "elapsed_seconds": 24.043384075164795,
      "error": null,
      "timestamp": "2026-08-07T08:54:01.103782"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 27.708603382110596,
      "error": null,
      "timestamp": "2026-08-07T08:54:01.103782"
    },
    "bacen_conglomerados": {
      "status": "error",
      "elapsed_seconds": 0.8778564929962158,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 138, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 50, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_conglomerados.py\", line 69, in fetch\n    print_warn(f\"{yyyymm}CONGLOMERADO.zip não disponível\", elapsed=time.time() - t0)\n    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nTypeError: print_warn() got an unexpected keyword argument 'elapsed'\n",
      "timestamp": "2026-08-07T08:54:01.103782"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 11.709532260894775,
      "error": null,
      "timestamp": "2026-08-07T08:54:01.103782"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "success",
      "elapsed_seconds": 6.055580139160156,
      "error": null,
      "timestamp": "2026-08-07T08:54:01.103782"
    }
  },
  "drifts": {}
};
