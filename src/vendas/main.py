import pandas as pd

from shared.entidades import monta_funcionarios, montar_produtos, montar_clientes
from vendas.vendas import montar_vendas


def gerar_vendas(n: int, seed: int | None = None) -> pd.DataFrame:
    """
    Orquestra a geração da tabela de vendas, montando (ou recebendo)
    as entidades compartilhadas necessárias e chamando `montar_vendas`.

    Não persiste nada em disco — apenas retorna o DataFrame.
    A gravação em Parquet acontece no notebook de execução.
    """
    if seed is not None:
        import random
        random.seed(seed)

    df_funcionarios = monta_funcionarios()
    df_produtos = montar_produtos()
    df_clientes = montar_clientes()

    # datas possíveis para as vendas — mesmo intervalo usado em monta_funcionarios,
    # mantendo consistência temporal entre as áreas
    datas = pd.date_range(start="2020-01-01", end="2022-05-10")

    df_vendas = montar_vendas(
        df_produtos=df_produtos,
        df_clientes=df_clientes,
        df_funcionarios=df_funcionarios,
        datas=datas,
        n=n,
    )

    return df_vendas