window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-08-20T08:48:45.738515",
  "elapsed_seconds": 2162.812745332718,
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
      "elapsed_seconds": 2162.8105731010437,
      "error": null,
      "timestamp": "2026-08-20T08:48:45.738638"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 31.569448709487915,
      "error": null,
      "timestamp": "2026-08-20T08:48:45.738638"
    },
    "bacen_conglomerados": {
      "status": "success",
      "elapsed_seconds": 1.3957457542419434,
      "error": null,
      "timestamp": "2026-08-20T08:48:45.738638"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 6.567000389099121,
      "error": null,
      "timestamp": "2026-08-20T08:48:45.738638"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "error",
      "elapsed_seconds": 2.447204351425171,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 138, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 50, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_parcelas_capital_basileia.py\", line 152, in fetch\n    raise RuntimeError(\n    ...<2 lines>...\n    )\nRuntimeError: Nenhum dado retornado da API OData do BCB (IFData). Verifique se a API está disponível.\n",
      "timestamp": "2026-08-20T08:48:45.738638"
    }
  },
  "drifts": {}
};
