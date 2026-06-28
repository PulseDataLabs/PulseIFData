#!/usr/bin/env python
# coding: utf-8
"""
Faz o upload dos arquivos CSV auxiliares e de configuração para o Oracle Database.
"""

import sys
from pathlib import Path
import pandas as pd

# Adiciona o diretório do projeto ao path para importar utils
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.base import get_logger
from utils.db import upload_dataframe
from scripts.utils.ux import banner, print_done

log = get_logger("upload_meta_csvs")

# Mapeamento de arquivos CSV para suas respectivas tabelas no Oracle
CSV_TABLES_MAPPING = {
    # Arquivos de dados auxiliares
    "data/bacen_balancetes_bancos.csv": "BACEN_BALANCETES_BANCOS",
    "data/bacen_conglomerados.csv": "BACEN_CONGLOMERADOS",
    "data/bacen_ifdata_cadastro.csv": "BACEN_IFDATA_CADASTRO",
    "data/bacen_parcelas_capital_basileia.csv": "BACEN_PARCELAS_CAPITAL_BASILEIA",
    # Arquivos de configuração/mapeamento
    "config/cosif_de_para.csv": "COSIF_DE_PARA",
    "config/cosif_semantic_mapping.csv": "COSIF_SEMANTIC_MAPPING"
}

def upload_all_csvs():
    banner("Upload de CSVs Auxiliares e Configurações")
    
    root_dir = Path(__file__).resolve().parents[1]
    
    uploaded_count = 0
    for rel_path, table_name in CSV_TABLES_MAPPING.items():
        file_path = root_dir / rel_path
        if not file_path.exists():
            log.warning(f"Arquivo {rel_path} não encontrado — pulando upload para {table_name}")
            continue
            
        log.info(f"Lendo {rel_path}...")
        try:
            # Ler CSV com tipagem segura para chaves e códigos
            df = pd.read_csv(file_path, dtype=str)
            
            # Converter colunas numéricas de volta para floats se possível (para preservar tipos no Oracle)
            for col in df.columns:
                # Se a coluna parecer numérica e não for um código/CNPJ, tentar converter
                if col.lower() not in ("cnpj", "cnpj_base", "codinst", "conta", "conta_antiga", "conta_nova", "anomes", "data_base"):
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except (ValueError, TypeError):
                        pass
            
            log.info(f"Carregando {len(df)} linhas de {rel_path} na tabela {table_name}...")
            if upload_dataframe(df, table_name):
                uploaded_count += 1
                
        except Exception as e:
            log.error(f"Erro ao carregar {rel_path} na tabela {table_name}: {e}")

    print_done(f"Upload concluído: {uploaded_count} tabelas atualizadas com sucesso no Oracle.")

if __name__ == "__main__":
    upload_all_csvs()
