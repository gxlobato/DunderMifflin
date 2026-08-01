"""
Wrapper genérico para chamadas a APIs externas (OpenRouteService, IBGE,
GitHub, etc.). Centraliza o tratamento de erro de rede/API, para que os
módulos de cada área do negócio não precisem repetir essa lógica.
"""

import requests


def post_json(url, body, headers=None, chave_esperada=None):
    """
    Faz uma requisição POST esperando uma resposta em JSON.

    Parâmetros
    ----------
    url : str
        Endpoint da API.
    body : dict
        Corpo da requisição, enviado como JSON.
    headers : dict, opcional
        Cabeçalhos da requisição (ex: Authorization, Content-Type).
    chave_esperada : str, opcional
        Se informado, valida se essa chave existe na resposta (ex:
        "distances" para a API de matrix do OpenRouteService).
        Se a chave não existir, levanta um erro com a resposta completa
        da API — mais claro do que deixar um KeyError genérico estourar
        mais adiante no código.

    Retorno
    -------
    dict com a resposta da API já convertida de JSON.
    """
    response = requests.post(url, json=body, headers=headers)
    dados = response.json()

    if chave_esperada is not None and chave_esperada not in dados:
        raise RuntimeError(f"Erro na chamada a {url}: {dados}")

    return dados


def get_json(url, headers=None, params=None):
    """
    Faz uma requisição GET esperando uma resposta em JSON.

    Usa raise_for_status() para lançar um erro claro em caso de falha
    HTTP (ex: 403, 404, 500), em vez de seguir adiante com uma resposta
    inválida.
    """
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def get_text(url, headers=None):
    """
    Faz uma requisição GET esperando uma resposta em texto puro
    (ex: conteúdo de um CSV baixado diretamente de uma URL).
    """
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text
