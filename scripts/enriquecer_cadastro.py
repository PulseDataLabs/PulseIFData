"""
Enriquece cadastro de IFs: tenta IfDataCadastro, fallback CodInst, 
mapeamento manual para IFs conhecidas.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.base import get_logger, nova_session
from scrapers.utils.odata import baixar_com_checkpoint, gerar_periodos
from scripts.utils.ux import print_done, print_warn, section

log = get_logger("enriquecer_cadastro")

MAPA_CONHECIDO: dict[str, dict] = {
    "60701190": {"nome": "Banco do Brasil S.A.", "segmento": "S1"},
    "00360305": {"nome": "Itaú Unibanco S.A.", "segmento": "S1"},
    "60746948": {"nome": "Caixa Econômica Federal", "segmento": "S1"},
    "90400888": {"nome": "Banco Bradesco S.A.", "segmento": "S1"},
    "33657248": {"nome": "Banco Santander (Brasil) S.A.", "segmento": "S1"},
    "30306294": {"nome": "BNDES", "segmento": "S1"},
    "60872504": {"nome": "Banco BTG Pactual S.A.", "segmento": "S1"},
    "58160789": {"nome": "Banco Safra S.A.", "segmento": "S1"},
    "33479023": {"nome": "Sicoob", "segmento": "S2"},
    "01181521": {"nome": "Banco do Nordeste do Brasil S.A.", "segmento": "S2"},
    "33264668": {"nome": "Bradesco Financiamentos S.A.", "segmento": "S2"},
    "30680829": {"nome": "Citibank N.A.", "segmento": "S2"},
    "02332886": {"nome": "XP Investimentos Corretora de Câmbio Títulos e Valores Mobiliários S.A.", "segmento": "S3"},
    "59588111": {"nome": "Banco Votorantim S.A.", "segmento": "S2"},
    "01425787": {"nome": "Banco ABC Brasil S.A.", "segmento": "S2"},
    "92702067": {"nome": "Banco Daycoval S.A.", "segmento": "S3"},
    "33172537": {"nome": "Banco Pan S.A.", "segmento": "S3"},
    "02038232": {"nome": "Banco BBM S.A.", "segmento": "S3"},
    "01027058": {"nome": "Banco Mercantil do Brasil S.A.", "segmento": "S3"},
    "18236120": {"nome": "Banco Ourinvest S.A.", "segmento": "S3"},
    "01522368": {"nome": "Banco C6 S.A.", "segmento": "S3"},
    "62232889": {"nome": "Banco Inter S.A.", "segmento": "S3"},
    "07707650": {"nome": "Banco Modal S.A.", "segmento": "S3"},
    "31872495": {"nome": "Banco Fibra S.A.", "segmento": "S4"},
    "00416968": {"nome": "Banco da Amazônia S.A.", "segmento": "S2"},
    "10440482": {"nome": "Banco do Estado do Rio Grande do Sul S.A.", "segmento": "S2"},
    "08561701": {"nome": "Banco do Estado do Espírito Santo S.A.", "segmento": "S3"},
    "07237373": {"nome": "Banco do Estado do Pará S.A.", "segmento": "S4"},
    "59285411": {"nome": "Banco do Estado do Amazonas S.A.", "segmento": "S4"},
}


def tentar_ifdata_cadastro(raw_dir: Path, max_periodos: int = 1) -> pd.DataFrame | None:
    """Tenta baixar IfDataCadastro. Falha rápido (1 período, 1 tentativa)."""
    from scrapers.utils.odata import gerar_periodos
    import yaml

    settings_path = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
    if not settings_path.exists():
        return None

    settings = yaml.safe_load(settings_path.read_text())
    odata_cfg = settings.get("odata", {})
    extr = settings.get("extraction", {})

    session = nova_session()
    base_url = odata_cfg["base_url"].rstrip("/")
    cadastro_ep = odata_cfg["endpoints"]["cadastro"]

    periodos = [p for p in gerar_periodos(2024, 3, [3, 6, 9, 12]) if p >= 202400][:max_periodos]

    for periodo in periodos:
        raw_path = raw_dir / f"ifdata_cadastro_{periodo}.csv"
        params = {"@AnoMes": str(periodo), "$format": "json"}
        url = f"{base_url}/{cadastro_ep}"

        r = session.get(url, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            values = data.get("value", [])
            if values:
                df = pd.DataFrame(values)
                df["AnoMes"] = str(periodo)
                log.info(f"Cadastro OK: {periodo} ({len(df)} IFs)")
                return df.drop_duplicates(subset=["CodInst"], keep="last")
        else:
            log.warning(f"IfDataCadastro {periodo}: HTTP {r.status_code} — falha rápida")

    return None


def extrair_codinst_de_valores(raw_dir: Path) -> pd.DataFrame:
    """Fallback: CodInst únicos dos dados financeiros."""
    log.info("Fallback: extraindo CodInst de dados financeiros")
    codinsts: set[str] = set()
    for fpath in sorted(raw_dir.glob("ifdata_rel*.csv")):
        try:
            df = pd.read_csv(fpath, usecols=["CodInst"], dtype=str)
            codinsts.update(df["CodInst"].dropna().unique())
        except Exception:
            continue
    if not codinsts:
        return pd.DataFrame()
    return pd.DataFrame(sorted(codinsts), columns=["CodInst"])


def aplicar_mapa_conhecido(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica mapeamento manual para IFs conhecidas."""
    mapa_df = pd.DataFrame.from_dict(MAPA_CONHECIDO, orient="index")
    mapa_df.index.name = "CodInst"
    mapa_df = mapa_df.reset_index()

    cols_enriquecer = {"nome": "NomeInstituicao", "segmento": "Segmento"}
    for src, dst in cols_enriquecer.items():
        if src in mapa_df.columns:
            merge_cols = ["CodInst", src]
            df = df.merge(mapa_df[merge_cols], on="CodInst", how="left")
            df[dst] = df[src]
            df = df.drop(columns=[src])

    df["NomeInstituicao"] = df.get("NomeInstituicao", pd.Series(dtype=str)).fillna(
        df["CodInst"].apply(lambda c: f"IF {c}")
    )
    df["Segmento"] = df.get("Segmento", pd.Series(dtype=str)).fillna("N/D")
    return df


def enriquecer(raw_dir: Path, output_path: Path | None = None) -> pd.DataFrame:
    """Pipeline de enriquecimento."""
    section("Enriquecimento de Cadastro")

    # 1. Tentar IfDataCadastro
    df = tentar_ifdata_cadastro(raw_dir)
    if df is not None and not df.empty:
        log.info(f"IfDataCadastro OK: {len(df)} IFs")
        print_done(f"IfDataCadastro: {len(df)} IFs enriquecidas")

        mapear_colunas(df)
        df = aplicar_mapa_conhecido(df)

        if output_path:
            salvar(df, output_path)
        return df

    # 2. Fallback: CodInst
    log.warning("IfDataCadastro indisponível — usando fallback CodInst + mapa conhecido")
    df = extrair_codinst_de_valores(raw_dir)

    if df.empty:
        log.error("Nenhum dado de cadastro disponível")
        return df

    log.info(f"Fallback: {len(df)} CodInst extraídos")
    df = aplicar_mapa_conhecido(df)
    print_done(f"Cadastro enriquecido: {len(df)} IFs ({sum(1 for _ in df['NomeInstituicao'].dropna())} nomeadas)")

    if output_path:
        salvar(df, output_path)
    return df


def mapear_colunas(df: pd.DataFrame) -> None:
    """Normaliza colunas do IfDataCadastro."""
    rename = {
        "NomeInstituicao": "NomeInstituicao",
        "SegmentoTb": "Segmento",
        "Uf": "UF",
        "Municipio": "Municipio",
        "CodConglomeradoFinanceiro": "CodConglomerado",
        "CodConglomeradoPrudencial": "CodConglomeradoPrudencial",
        "CnpjInstituicaoLider": "CNPJLider",
        "Situacao": "Situacao",
    }
    df.rename(columns={k: v for k, v in rename.items() if k in df.columns}, inplace=True)


def salvar(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    log.info(f"Cadastro salvo: {output_path}")


def main():
    root_dir = Path(__file__).resolve().parents[1]
    raw_dir = root_dir / "data" / "raw"
    output_path = root_dir / "data" / "cadastro_ifs.csv"

    df = enriquecer(raw_dir, output_path)
    if not df.empty:
        print_done(f"{output_path} — {len(df)} IFs ({len(df.columns)} colunas)")
        print(f"  Colunas: {list(df.columns)}")


if __name__ == "__main__":
    main()
