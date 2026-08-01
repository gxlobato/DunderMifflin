"""
Cálculo de distâncias rodoviárias reais (armazém-cliente e
cliente-cliente) usando a API de Matrix do OpenRouteService.
Exclusivo da etapa de Logística.
"""

import pandas as pd

from src.shared.api_client import post_json

URL_MATRIX = "https://api.openrouteservice.org/v2/matrix/driving-car"


def calcula_distancias(df_armazem, df_clientes, api_key):
    """
    Calcula a distância rodoviária entre cada armazém e cada cliente
    via OpenRouteService Matrix API, em uma única chamada.

    Usa "sources"/"destinations" para pedir apenas a matriz armazém->cliente,
    evitando gastar cota da API com pares armazém-armazém ou cliente-cliente.
    """
    # 1. monta uma única lista de coordenadas: primeiro os armazéns, depois os clientes
    #    (a API espera [longitude, latitude], não [latitude, longitude])
    locations_armazem = df_armazem[['longitude', 'latitude']].values.tolist()
    locations_cliente = df_clientes[['longitude', 'latitude']].values.tolist()
    locations = locations_armazem + locations_cliente

    n_armazens = len(locations_armazem)
    n_clientes = len(locations_cliente)

    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json',
    }

    # 2. sources = índices dos armazéns na lista; destinations = índices dos clientes
    #    isso restringe a matriz retornada só ao que interessa (armazém -> cliente)
    body = {
        "locations": locations,
        "sources": list(range(n_armazens)),
        "destinations": list(range(n_armazens, n_armazens + n_clientes)),
        "metrics": ["distance"],
    }

    # chave_esperada="distances" garante um erro claro se a API responder
    # com algo diferente do esperado (ex: erro de rate limit ou parâmetro)
    dados = post_json(URL_MATRIX, body, headers=headers, chave_esperada="distances")

    # 3. converte a matriz de distâncias (linhas=armazéns, colunas=clientes)
    #    em uma tabela no formato "longo" (uma linha por par armazém-cliente)
    registros_distancia = []
    for i in range(n_armazens):
        for j in range(n_clientes):
            registros_distancia.append({
                'id_armazem': df_armazem.iloc[i]['id'],
                'id_cliente': df_clientes.iloc[j]['id'],
                'distancia_metros': dados['distances'][i][j],
            })
    return pd.DataFrame(registros_distancia)


def calcula_distancias_clientes(df_clientes, api_key):
    """
    Calcula a distância rodoviária entre cada par de clientes
    (matriz cliente x cliente completa, excluindo a diagonal
    onde origem == destino).

    Necessário para a roteirização: depois da primeira entrega, o
    caminho segue de cliente em cliente, não volta ao armazém.
    """
    locations = df_clientes[['longitude', 'latitude']].values.tolist()
    n = len(locations)

    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json',
    }
    body = {
        "locations": locations,
        "metrics": ["distance"],
    }

    dados = post_json(URL_MATRIX, body, headers=headers, chave_esperada="distances")

    # monta uma linha por par (cliente_origem, cliente_destino), pulando
    # a diagonal (i == j), já que a distância de um cliente até ele mesmo
    # não faz sentido para o problema de roteirização
    registros = []
    for i in range(n):
        for j in range(n):
            if i != j:
                registros.append({
                    'id_cliente_origem': df_clientes.iloc[i]['id'],
                    'id_cliente_destino': df_clientes.iloc[j]['id'],
                    'distancia_km': dados['distances'][i][j] / 1000,
                })
    return pd.DataFrame(registros)
