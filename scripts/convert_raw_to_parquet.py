#!/usr/bin/env python
# coding: utf-8
"""
PulseIFData – Utilitário de migração de banco de dados bruto (CSV -> Parquet)
"""

import sys
import time
from pathlib import Path
import pandas as pd
import polars as pl

def convert_all():
    root_dir = Path(__file__).resolve().parents[1]
    raw_dir = root_dir / "data" / "raw"
    
    if not raw_dir.exists():
        print("Diretório data/raw não existe.")
        return
        
    csv_files = sorted(raw_dir.glob("*.csv"))
    # Filter out any files that are not valid CSV scrapers (like .gitkeep)
    csv_files = [f for f in csv_files if f.name != ".gitkeep"]
    
    if not csv_files:
        print("Nenhum arquivo CSV encontrado em data/raw.")
        return
        
    print(f"Encontrados {len(csv_files)} arquivos CSV para migração.")
    
    total_csv_size = 0
    total_parquet_size = 0
    converted_count = 0
    error_count = 0
    
    t0 = time.time()
    
    for idx, fpath in enumerate(csv_files, 1):
        csv_size = fpath.stat().st_size
        total_csv_size += csv_size
        
        parquet_path = fpath.with_suffix(".parquet")
        
        try:
            # Forçar todas as colunas como string para preservar o comportamento original (dtype=str)
            try:
                df = pl.read_csv(fpath, infer_schema_length=0)
            except Exception:
                # Fallback para pandas se o Polars falhar em algum CSV específico
                pdf = pd.read_csv(fpath, dtype=str, keep_default_na=False)
                df = pl.from_pandas(pdf)
                
            # Salvar como Parquet
            df.write_parquet(parquet_path)
            
            # Validar e deletar original
            if parquet_path.exists() and parquet_path.stat().st_size > 0:
                total_parquet_size += parquet_path.stat().st_size
                fpath.unlink()
                converted_count += 1
            else:
                print(f"Aviso: Parquet de {fpath.name} gerado vazio.")
                error_count += 1
                
        except Exception as e:
            print(f"Erro ao converter {fpath.name}: {e}")
            error_count += 1
            
        if idx % 100 == 0 or idx == len(csv_files):
            print(f"Processados {idx}/{len(csv_files)} arquivos...")
            
    elapsed = time.time() - t0
    print("\n=== Migração Concluída ===")
    print(f"Convertidos com sucesso: {converted_count} arquivos")
    print(f"Erros encontrados: {error_count} arquivos")
    print(f"Tamanho total original (CSV): {total_csv_size / (1024*1024):.2f} MB")
    print(f"Tamanho total novo (Parquet): {total_parquet_size / (1024*1024):.2f} MB")
    if total_csv_size > 0:
        reduction = (1 - total_parquet_size / total_csv_size) * 100
        print(f"Redução de espaço em disco: {reduction:.1f}%")
    print(f"Tempo total gasto: {elapsed:.1f}s")

if __name__ == "__main__":
    convert_all()
