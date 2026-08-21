window.PULSEIFDATA_PIPELINE_STATUS = {
  "timestamp": "2026-08-21T09:22:09.304755",
  "elapsed_seconds": 4234.493877410889,
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
      "elapsed_seconds": 4234.4902629852295,
      "error": null,
      "timestamp": "2026-08-21T09:22:09.304886"
    },
    "bacen_ifdata_cadastro": {
      "status": "success",
      "elapsed_seconds": 23.730546951293945,
      "error": null,
      "timestamp": "2026-08-21T09:22:09.304886"
    },
    "bacen_conglomerados": {
      "status": "success",
      "elapsed_seconds": 1.465754508972168,
      "error": null,
      "timestamp": "2026-08-21T09:22:09.304886"
    },
    "bacen_balancetes_bancos": {
      "status": "success",
      "elapsed_seconds": 7.594408750534058,
      "error": null,
      "timestamp": "2026-08-21T09:22:09.304886"
    },
    "bacen_parcelas_capital_basileia": {
      "status": "error",
      "elapsed_seconds": 2.4459285736083984,
      "error": "Traceback (most recent call last):\n  File \"/home/runner/work/PulseIFData/PulseIFData/run_all.py\", line 92, in run_scraper\n    getattr(mod, class_name)().run()\n    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 138, in run\n    raise e\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/utils/base.py\", line 50, in run\n    df = self.fetch()\n  File \"/home/runner/work/PulseIFData/PulseIFData/scrapers/bacen_parcelas_capital_basileia.py\", line 152, in fetch\n    raise RuntimeError(\n    ...<2 lines>...\n    )\nRuntimeError: Nenhum dado retornado da API OData do BCB (IFData). Verifique se a API está disponível.\n",
      "timestamp": "2026-08-21T09:22:09.304886"
    }
  },
  "drifts": {}
};
