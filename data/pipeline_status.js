window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-08-26T09:02:54.169170",
  "elapsed_seconds": 2859.4234240055084,
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
      "elapsed_seconds": 2859.420006752014,
      "error": null,
      "timestamp": "2026-08-26T09:02:54.169320"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 26.709397554397583,
      "error": null,
      "timestamp": "2026-08-26T09:02:54.169320"
    },
    "bacen_conglomerados": {
      "status": "success",
      "elapsed_seconds": 0.7313010692596436,
      "error": null,
      "timestamp": "2026-08-26T09:02:54.169320"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 7.447477579116821,
      "error": null,
      "timestamp": "2026-08-26T09:02:54.169320"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "error",
      "elapsed_seconds": 2.4337587356567383,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 138, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 50, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_parcelas_capital_basileia.py\", line 152, in fetch\n    raise RuntimeError(\n    ...<2 lines>...\n    )\nRuntimeError: Nenhum dado retornado da API OData do BCB (IFData). Verifique se a API está disponível.\n",
      "timestamp": "2026-08-26T09:02:54.169320"
    }
  },
  "drifts": {}
};
