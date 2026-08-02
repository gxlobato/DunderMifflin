import os
import pandas as pd


def salvar_parquet(df, caminho):
    """Salva um DataFrame em Parquet no caminho informado, com timestamps
    em microssegundos (Spark não lê timestamps em nanossegundos)."""
    df.to_parquet(caminho, index=False, coerce_timestamps='us', allow_truncated_timestamps=True)


def carregar_parquet(caminho):
    """Carrega um DataFrame salvo em Parquet, ou None se o arquivo não existir."""
    if not os.path.exists(caminho):
        return None
    return pd.read_parquet(caminho)


def carregar_ou_gerar(caminho, funcao_geradora, forcar_atualizacao=False):
    """
    Carrega um DataFrame do cache (Parquet), se existir; caso contrário
    (ou se forcar_atualizacao=True), executa `funcao_geradora`, salva o
    resultado em disco e retorna.
    """
    if not forcar_atualizacao:
        df_em_cache = carregar_parquet(caminho)
        if df_em_cache is not None:
            return df_em_cache

    df = funcao_geradora()
    salvar_parquet(df, caminho)
    return df
