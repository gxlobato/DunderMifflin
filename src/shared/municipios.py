"""
Funções compartilhadas para carregar municípios brasileiros e suas
coordenadas geográficas. Usadas por qualquer área do negócio que
precise de localização (hoje: logística; no futuro: outras áreas
que também dependam de endereço de cliente/armazém).
"""

import io

import pandas as pd

from src.shared.api_client import get_json, get_text

URL_IBGE = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
URL_LAT_LONG = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"


def carrega_municipios():
    """
    Busca todos os municípios do Brasil na API do IBGE e retorna um
    DataFrame já achatado (sem colunas aninhadas), com o nome, UF,
    código da UF e região de cada um.
    """
    # 1. chama a API do IBGE e converte a resposta em JSON
    dados_json = get_json(URL_IBGE)

    # 2. achata a estrutura aninhada do JSON (município -> microrregião -> UF)
    df = pd.json_normalize(dados_json)

    # 3. mantém só as colunas relevantes e renomeia para nomes mais simples
    df = df[[
        "id",
        "nome",
        "microrregiao.mesorregiao.UF.sigla",
        "microrregiao.mesorregiao.UF.id",
        "microrregiao.mesorregiao.UF.regiao.nome",
    ]]
    df.columns = ["codigo_ibge", "nome_cidade", "uf", "sigla_id", "regiao"]
    return df


def carrega_lat_long():
    """
    Baixa o CSV com latitude/longitude de todos os municípios brasileiros
    (fonte: kelvins/municipios-brasileiros) e retorna só as colunas
    necessárias para geolocalização.

    Usa um User-Agent customizado porque o GitHub às vezes bloqueia (403)
    requisições sem esse cabeçalho.
    """
    # 1. baixa o CSV como texto puro, para poder enviar o header de
    #    User-Agent e evitar bloqueio 403
    texto_csv = get_text(URL_LAT_LONG, headers={'User-Agent': 'Mozilla/5.0'})

    # 2. lê o conteúdo baixado como se fosse um arquivo (io.StringIO)
    df = pd.read_csv(io.StringIO(texto_csv))

    # 3. mantém só as colunas necessárias
    return df[['nome', 'codigo_uf', 'latitude', 'longitude']]


def buscar_lat_long(df_lat_long, codigo_ibge):
    """
    Retorna (latitude, longitude) de uma cidade específica, buscando
    pelo código IBGE — mais robusto que buscar por nome, já que evita
    divergências de acentuação/grafia entre fontes de dados diferentes
    (ex: API do IBGE vs CSV do kelvins/municipios-brasileiros).
    """
    linha = df_lat_long[df_lat_long['codigo_ibge'] == codigo_ibge].head(1)

    if linha.empty:
        raise ValueError(f"Código IBGE não encontrado em df_lat_long: {codigo_ibge}")

    return linha['latitude'].values[0], linha['longitude'].values[0]
