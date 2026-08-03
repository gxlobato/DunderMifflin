"""
Cálculo de distâncias e tempos de viagem reais (armazém-cliente e
cliente-cliente) usando a API de Matrix do OpenRouteService.
Exclusivo da etapa de Logística.
"""

import pandas as pd
import requests

from src.shared.api_client import post_json

URL_MATRIX = "https://api.openrouteservice.org/v2/matrix/driving-car"


def calcula_distancias(df_armazem, df_clientes, api_key):
    """
    Calcula a distância rodoviária entre cada armazém e cada cliente
    via OpenRouteService Matrix API, em uma única chamada.

    Usa "sources"/"destinations" para pedir apenas a matriz armazém→cliente,
    evitando gastar cota da API com pares armazém↔armazém ou cliente↔cliente.
    """

    locations_armazem = df_armazem[['longitude', 'latitude']].values.tolist()
    locations_cliente = df_clientes[['longitude', 'latitude']].values.tolist()
    locations = locations_armazem + locations_cliente

    n_armazens = len(locations_armazem)
    n_clientes = len(locations_cliente)

    url_matrix = "https://api.openrouteservice.org/v2/matrix/driving-car"

    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json',
    }

    body = {
        "locations": locations,
        "sources": list(range(n_armazens)),
        "destinations": list(range(n_armazens, n_armazens + n_clientes)),
        "metrics": ["distance", "duration"],
    }

    response = requests.post(url_matrix, json=body, headers=headers)
    response.raise_for_status()

    dados = response.json()

    if 'distances' not in dados:
        raise RuntimeError(f"Erro na API do OpenRouteService: {dados}")

    registros_distancia = []

    for i in range(n_armazens):
        for j in range(n_clientes):
            duracao_s = dados['durations'][i][j] if 'durations' in dados else None

            registros_distancia.append({
                'id_armazem': df_armazem.iloc[i]['id'],
                'id_cliente': df_clientes.iloc[j]['id'],
                'distancia_metros': dados['distances'][i][j],
                'duracao_min': round(duracao_s / 60) if duracao_s is not None else None,
            })

    return pd.DataFrame(registros_distancia)


def calcula_distancias_clientes(df_clientes, df_entrega, api_key):
    """
    Calcula a distância e duração rodoviária entre cada par de clientes,
    separadamente para cada armazém — usando só os clientes atribuídos
    a ele (matriz cliente × cliente por grupo, excluindo a diagonal
    onde origem == destino).

    Evita calcular distância entre clientes que nunca estarão na mesma
    rota (ex: cliente do armazém de Belém x cliente do armazém de
    Curitiba), reduzindo bastante o número de pares em relação a uma
    matriz global de todos contra todos.

    Necessário para a roteirização: depois da primeira entrega, o
    caminho segue de cliente em cliente, não volta ao armazém.
    """
    url_matrix = "https://api.openrouteservice.org/v2/matrix/driving-car"

    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json',
    }

    registros = []

    for id_armazem, grupo in df_entrega.groupby('id_armazem'):
        ids_clientes = grupo['id_cliente'].unique()

        # filtra só os clientes desse armazém, e remove quem não tem
        # coordenadas válidas
        df = df_clientes[df_clientes['id'].isin(ids_clientes)]
        df = df.dropna(subset=['latitude', 'longitude']).reset_index(drop=True)

        # se sobrar 1 ou 0 clientes válidos nesse armazém, não há par
        # possível para calcular — pula para o próximo grupo
        if len(df) < 2:
            continue

        locations = df[['longitude', 'latitude']].values.tolist()

        body = {
            "locations": locations,
            "metrics": ["distance", "duration"],
        }

        response = requests.post(url_matrix, json=body, headers=headers)
        response.raise_for_status()

        dados = response.json()

        if 'distances' not in dados or 'durations' not in dados:
            raise RuntimeError(f"Erro na API: {dados}")

        for i, origem in df.iterrows():
            for j, destino in df.iterrows():
                if i == j:
                    continue

                distancia = dados['distances'][i][j]
                duracao = dados['durations'][i][j]

                registros.append({
                    'id_cliente_origem': origem['id'],
                    'id_cliente_destino': destino['id'],
                    'distancia_km': round(distancia / 1000, 2) if distancia is not None else None,
                    'duracao_min': round(duracao / 60) if duracao is not None else None,
                })

    return pd.DataFrame(registros)
