"""
Atribuição do armazém mais próximo a cada cliente (com prazo de entrega
estimado), e cálculo da ordem de entrega otimizada (heurística do
vizinho mais próximo). Exclusivo da etapa de Logística.
"""

import pandas as pd

from src.logistica.distancias import calcula_distancias

# faixas de distância (em km) usadas para estimar o prazo de entrega
DISTANCIA_PERTO_KM = 500
DISTANCIA_MEDIO_KM = 800


def atribui_armazem(df_armazem, df_clientes, api_key):
    """
    Para cada cliente, encontra o armazém mais próximo e estima um
    prazo de entrega com base na distância.

    Faz o cross join armazém x cliente, junta com as distâncias calculadas
    e mantém, por cliente, apenas a linha com a menor distância.

    Regra de prazo:
        até 500 km      -> 1 dia
        de 500 a 800 km  -> 2 dias
        acima de 800 km  -> 3 dias
    """
    df_distancias = calcula_distancias(df_armazem, df_clientes, api_key)

    # 1. cross join: gera todas as combinações possíveis de armazém x cliente
    df = df_armazem.merge(
        df_clientes,
        how='cross',
        suffixes=('_armazem', '_cliente'),
    )

    # 2. junta com as distâncias/durações reais calculadas via API, e remove
    #    colunas que não são necessárias para essa análise (endereço, contato, etc.)
    df = df.merge(
        df_distancias,
        on=['id_armazem', 'id_cliente'],
    ).drop(
        columns=[
            'codigo', 'cidade_armazem', 'latitude_armazem', 'longitude_armazem',
            'name', 'endereco_entrega', 'cidade_cliente', 'uf_cliente',
            'latitude_cliente', 'longitude_cliente', 'email', 'telefone',
        ]
    ).reset_index(drop=True)

    df['distancia_km'] = (df['distancia_metros'] / 1000).round(2)
    df = df.drop(columns=['distancia_metros'])

    # 3. define o prazo de entrega com base em faixas de distância
    df['prazo'] = 3
    df.loc[df['distancia_km'] <= DISTANCIA_PERTO_KM, 'prazo'] = 1
    df.loc[
        (df['distancia_km'] > DISTANCIA_PERTO_KM) &
        (df['distancia_km'] <= DISTANCIA_MEDIO_KM),
        'prazo'
    ] = 2

    # 4. para cada cliente, mantém só a linha com a menor distância
    #    (ou seja, o armazém mais próximo dele)
    indice_menor_distancia = df.groupby('id_cliente')['distancia_km'].idxmin()
    return df.loc[indice_menor_distancia].reset_index(drop=True)


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
        Linhas de UM armazém + UMA data, com colunas id_cliente,
        distancia_km e duracao_min (armazém -> cliente).
    df_dist_clientes : DataFrame
        Resultado de calcula_distancias_clientes(), com a distância e
        duração entre cada par de clientes.

    Retorno
    -------
    DataFrame com id_cliente, ordem_entrega (1, 2, 3...),
    distancia_percorrida_km e duracao_percorrida_min (referentes ao
    trecho do ponto anterior até aquela parada — não são acumuladas).
    Retorna DataFrame vazio se o grupo não tiver nenhum cliente válido.
    """
    # remove linhas sem id_cliente e clientes duplicados (um cliente pode
    # ter mais de uma venda no mesmo dia, mas só é visitado uma vez fisicamente)
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

        # se não houver nenhuma conexão válida para os clientes restantes,
        # interrompe a rota nesse ponto em vez de quebrar com erro
        if candidatos.empty:
            print(f"Sem rota encontrada para cliente {cliente_atual}")
            break

        proxima_linha = candidatos.sort_values('distancia_km').iloc[0]
        proximo_cliente = proxima_linha['id_cliente_destino']

        # segurança extra contra valores nulos vindos da matriz de distâncias
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
