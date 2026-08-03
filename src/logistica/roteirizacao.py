"""
Atribuição do armazém mais próximo a cada cliente (com prazo de entrega
estimado), e cálculo da ordem de entrega otimizada (heurística do
vizinho mais próximo). Exclusivo da etapa de Logística.
"""

import pandas as pd

from src.logistica.distancias import calcula_distancias

def atribui_armazem(df_armazem, df_clientes, api_key):
    """
    Para cada cliente, encontra o armazém mais próximo.

    Faz o cross join armazém × cliente, junta com as distâncias calculadas
    e mantém, por cliente, apenas a linha com a menor distância.
    """
    perto = 500
    medio = 800

    REGIOES_PERMITIDAS = {
        'Norte': ['Norte', 'Nordeste'],
        'Nordeste': ['Nordeste', 'Norte'],
        'Centro-Oeste': ['Centro-Oeste', 'Sudeste'],
        'Sudeste': ['Sudeste', 'Sul'],
        'Sul': ['Sul', 'Sudeste'],
    }

    df_distancias = calcula_distancias(df_armazem, df_clientes, api_key)

    df = df_armazem.merge(df_clientes, how='cross', suffixes=('_armazem', '_cliente'))

    df = df[df.apply(
        lambda linha: linha['regiao_armazem'] in REGIOES_PERMITIDAS[linha['regiao_cliente']],
        axis=1
    )]

    df = df.merge(
        df_distancias,
        on=['id_armazem', 'id_cliente'],
    ).drop(
        columns=[
            'codigo', 'cidade_armazem', 'latitude_armazem', 'longitude_armazem',
            'name', 'endereco_entrega', 'cidade_cliente', 'uf_cliente',
            'latitude_cliente', 'longitude_cliente', 'email', 'telefone',
            'regiao_armazem', 'regiao_cliente',
        ]
    ).reset_index(drop=True)

    df['distancia_km'] = (df['distancia_metros'] / 1000).round(2)
    df = df.drop(columns=['distancia_metros'])

    # remove linhas sem distância válida antes de calcular o mínimo
    df_validas = df.dropna(subset=['distancia_km'])

    # define o prazo de entrega com base na distância
    # até 500 km → 1 dia
    # de 500 a 800 km → 2 dias
    # acima de 800 km → 3 dias
    df['prazo'] = 3

    df.loc[df['distancia_km'] <= perto, 'prazo'] = 1

    df.loc[
        (df['distancia_km'] > perto) &
        (df['distancia_km'] <= medio),
        'prazo'
    ] = 2

    indice_menor_distancia = df_validas.groupby('id_cliente')['distancia_km'].idxmin()
    return df_validas.loc[indice_menor_distancia].reset_index(drop=True)


def calcular_melhor_rota(df_entregas_grupo, df_dist_clientes):
    """
    Ordena as entregas de um grupo (um armazém + uma data de saída) usando
    a heurística do vizinho mais próximo: parte do cliente mais perto do
    armazém e, a cada passo, segue para o cliente não visitado mais
    próximo do ponto atual.

    Não é a rota matematicamente ótima (isso seria um problema de TSP),
    mas é uma aproximação simples e rápida de calcular.

    Parâmetros
    ----------
    df_entregas_grupo : DataFrame
        Linhas de UM armazém + UMA data, com colunas id_cliente e
        distancia_km (armazém -> cliente).

    df_dist_clientes : DataFrame
        Resultado de calcula_distancias_clientes(), com a distância
        entre cada par de clientes.

    Retorno
    -------
    DataFrame com id_cliente, ordem_entrega (1, 2, 3...) e
    distancia_percorrida (distância do ponto anterior até aquela parada
    — não é acumulada).
    """

    # um cliente pode ter mais de uma venda no mesmo dia, mas só é
    # visitado uma vez fisicamente
    df_entregas_grupo = (
        df_entregas_grupo
        .dropna(subset=['id_cliente'])
        .drop_duplicates(subset=['id_cliente'])
    )

    clientes_restantes = df_entregas_grupo['id_cliente'].tolist()

    if not clientes_restantes:
        return pd.DataFrame()

    # ponto de partida: cliente mais próximo do armazém
    primeira_linha = df_entregas_grupo.sort_values('distancia_km').iloc[0]
    cliente_atual = primeira_linha['id_cliente']

    ordem = [cliente_atual]
    distancias = [primeira_linha['distancia_km']]
    duracoes = [primeira_linha['duracao_min']]

    clientes_restantes.remove(cliente_atual)

    # a cada passo, vai para o cliente restante mais próximo do atual
    while clientes_restantes:
        candidatos = df_dist_clientes[
            (df_dist_clientes['id_cliente_origem'] == cliente_atual) &
            (df_dist_clientes['id_cliente_destino'].isin(clientes_restantes))
        ].dropna(subset=['distancia_km'])

        # se não houver conexão válida, interrompe a rota
        if candidatos.empty:
            print(f"Sem rota encontrada para cliente {cliente_atual}")
            break

        proxima_linha = candidatos.sort_values('distancia_km').iloc[0]

        proximo_cliente = proxima_linha['id_cliente_destino']

        # segurança contra NaN
        if pd.isna(proximo_cliente):
            break

        ordem.append(proximo_cliente)
        distancias.append(proxima_linha['distancia_km'])
        duracoes.append(proxima_linha['duracao_min'])

        clientes_restantes.remove(proximo_cliente)
        cliente_atual = proximo_cliente

    return pd.DataFrame({
        'id_cliente': ordem,
        'ordem_entrega': range(1, len(ordem) + 1),
        'distancia_percorrida_km': distancias,
        'duracao_percorrida_min': duracoes,
    })
