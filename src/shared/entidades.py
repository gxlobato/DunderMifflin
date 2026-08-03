
import pandas as pd
from src.shared import buscar_lat_long
from faker import Faker
import random

def montar_armazens(df_municipios, df_lat_long):
    """
    Monta os armazéns fixos da transportadora, um em cada cidade da lista
    abaixo, com código, localização e coordenadas.

    Recebe df_municipios e df_lat_long como parâmetros (em vez de buscar
    internamente) para evitar repetir chamadas de API desnecessárias
    quando montar_clientes() também precisar dos mesmos dados.
    """
    #Adição do armazém de Goiania - 03/08/26
    armazem_cidades = ['São Paulo', 'Curitiba', 'Recife', 'Belém','Goiânia']
    armazem_codigo = ['A1', 'A2', 'A3', 'A4','A5']

    armazens = []

    for i, cidade in enumerate(armazem_cidades):
        linha = df_municipios[df_municipios['nome_cidade'] == cidade].head(1)

        if linha.empty:
            raise ValueError(f"Cidade não encontrada em df_municipios: {cidade}")

        codigo_ibge = linha['codigo_ibge'].values[0]
        uf = linha['uf'].values[0]
        regiao = linha['regiao'].values[0]

        latitude, longitude = buscar_lat_long(df_lat_long, codigo_ibge)

        armazens.append({
            'id': i + 1,
            'codigo': armazem_codigo[i],
            'cidade': cidade,
            'uf': uf,
            'regiao': regiao,
            'latitude': latitude,
            'longitude': longitude,
        })

    return pd.DataFrame(armazens)


def montar_produtos():
    """Catálogo fixo de produtos (papelaria) com peso e valor unitário."""

    produtos = [
        [1, 'Papel Kraft', 3, 80],
        [2, 'Papel-Cartão', 20, 250],
        [3, 'Papel Supremo', 20, 220],
        [4, 'Papel Sulfite', 23, 300],
        [5, 'Papel Couché', 6, 200],
        [6, 'Papel Pólen', 13, 220],
        [7, 'Papel Color Plus', 2.8, 100],
        [8, 'Papel Vegetal', 2, 80],
        [9, 'Papel Fotográfico', 1.2, 40],
    ]

    return pd.DataFrame(
        produtos,
        columns=['id', 'produto', 'peso', 'valor_unitario']
    )


def montar_clientes(df_municipios, df_lat_long, quantidade=50):
    """
    Sorteia `quantidade` municípios aleatórios e gera um cliente fictício
    (empresa) para cada um, com dados de contato via Faker.
    """
    clientes = []

    for x in range(quantidade):
        linha_aleatoria = df_municipios.sample(n=1)

        nome_cidade = linha_aleatoria['nome_cidade'].values[0]
        codigo_ibge = linha_aleatoria['codigo_ibge'].values[0]
        regiao = linha_aleatoria['regiao'].values[0]
        uf = linha_aleatoria['uf'].values[0]

        latitude, longitude = buscar_lat_long(df_lat_long, codigo_ibge)

        clientes.append({
            'id': x + 1,
            'name': fake.company(),
            'endereco_entrega': fake.street_address(),
            'cidade': nome_cidade,
            'uf': uf,
            'regiao': regiao,
            'latitude': latitude,
            'longitude': longitude,
            'email': fake.ascii_company_email(),
            'telefone': fake.phone_number(),
        })

    return pd.DataFrame(clientes)


def monta_funcionarios():
    """Quadro fixo de funcionários, cada um com uma área e data de contratação aleatória."""

    funcionarios = [
        [2, 'Jim Halpert', 'Vendas'],
        [1, 'Dwight Schrute', 'Vendas'],
        [3, 'Stanley Hudson', 'Vendas'],
        [4, 'Phyllis Vance', 'Vendas'],
        [5, 'Andy Bernard', 'Vendas'],
        [6, 'Ryan Howard', 'Vendas'],
        [7, 'Michael Scott', 'Gerencia'],
        [8, 'Pamela Halpert', 'Administrativo'],
        [9, 'Angela Martin', 'Contabilidade'],
        [10, 'Oscar Martinez', 'Contabilidade'],
        [11, 'Kevin Malone', 'Contabilidade'],
        [12, 'Kelly Kapoor', 'Administrativo'],
        [13, 'Creed Bratton', 'Administrativo'],
        [14, 'Meredith Palmer', 'Administrativo'],
        [15, 'Darryl Philbin', 'Armazém'],
        [16, 'Lonny Smith', 'Armazém'],
        [17, 'Madge Parker', 'Armazém'],
        [18, 'Glenn Godwin', 'Armazém'],
        [19, 'Hide Lee', 'Armazém'],
        [20, 'Toby Flenderson', 'Recursos Humanos'],
    ]

    datas_possiveis = pd.date_range(
        start="2020-01-01",
        end="2022-05-10"
    )

    registros = []

    for id_func, nome, area in funcionarios:
        registros.append({
            'id': id_func,
            'Nome': nome,
            'Area': area,
            'Data_Contratacao': random.choice(datas_possiveis),
        })

    return pd.DataFrame(registros)


def montar_vendas(df_produtos, df_clientes, df_funcionarios, datas, n):
    """
    Gera `n` vendas sintéticas, sorteando produto, cliente, vendedor
    (apenas funcionários da área "Vendas") e data.
    """

    # calculado uma única vez fora do loop, já que não muda a cada venda
    vendedores = df_funcionarios[
        df_funcionarios['Area'] == 'Vendas'
    ]['id'].tolist()

    vendas = []

    for x in range(n):
        produto = df_produtos.sample(n=1).iloc[0]
        qtd = random.randint(1, 30)

        vendas.append({
            'id_venda': x + 1,
            'data_venda': random.choice(datas),
            'id_cliente': random.choice(df_clientes['id']),
            'id_vendedor': random.choice(vendedores),
            'produto_id': produto['id'],
            'quantidade': qtd,
            'valor_total': qtd * produto['valor_unitario'],
        })

    return pd.DataFrame(vendas)