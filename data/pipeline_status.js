window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-07-04T10:47:12.495313",
  "elapsed_seconds": 23.060839891433716,
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
      "elapsed_seconds": 22.384207487106323,
      "error": null,
      "timestamp": "2026-07-04T10:47:12.495421"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 23.056637287139893,
      "error": null,
      "timestamp": "2026-07-04T10:47:12.495421"
    },
    "bacen_conglomerados": {
      "status": "error",
      "elapsed_seconds": 0.8814187049865723,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 136, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 48, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_conglomerados.py\", line 69, in fetch\n    print_warn(f\"{yyyymm}CONGLOMERADO.zip não disponível\", elapsed=time.time() - t0)\n    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nTypeError: print_warn() got an unexpected keyword argument 'elapsed'\n",
      "timestamp": "2026-07-04T10:47:12.495421"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 6.257248163223267,
      "error": null,
      "timestamp": "2026-07-04T10:47:12.495421"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "success",
      "elapsed_seconds": 5.050992012023926,
      "error": null,
      "timestamp": "2026-07-04T10:47:12.495421"
    }
  },
  "drifts": {}
};
