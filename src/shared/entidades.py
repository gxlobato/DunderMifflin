
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


#Adição da coluna de custo de compra do produto
def montar_produtos():
    """Catálogo fixo de produtos (papelaria) com peso e valor unitário."""

    produtos = [
        [1, 'Papel Kraft', 3,60,80],
        [2, 'Papel-Cartão', 20,200,250],
        [3, 'Papel Supremo', 20,180,220],
        [4, 'Papel Sulfite', 23,200,300],
        [5, 'Papel Couché', 6,120,200],
        [6, 'Papel Pólen', 13,100,220],
        [7, 'Papel Color Plus', 2.8,90,100],
        [8, 'Papel Vegetal', 2,75,80],
        [9, 'Papel Fotográfico', 1.2,35,40],
    ]

    return pd.DataFrame(
        produtos,
        columns=['id', 'produto', 'peso', 'valor_custo','valor_unitario']
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

#Adicao do cargo de cada funcionario
def monta_funcionarios():
    """Quadro fixo de funcionários, cada um com uma área e data de contratação aleatória."""

    funcionarios = [
        [1, 'Dwight Schrute', 'Vendas','Sênior'],
		[2, 'Jim Halpert', 'Vendas','Sub-Gerente'],
        [3, 'Stanley Hudson', 'Vendas','Sênior'],
        [4, 'Phyllis Vance', 'Vendas','Pleno'],
        [5, 'Andy Bernard', 'Vendas','Pleno'],
        [6, 'Ryan Howard', 'Vendas','Junior'],
        [7, 'Michael Scott', 'Administrativo','Gerente'],
        [8, 'Pamela Halpert', 'Administrativo','Junior'],
        [9, 'Angela Martin', 'Contabilidade','Sênior'],
        [10, 'Oscar Martinez', 'Contabilidade','Sênior'],
        [11, 'Kevin Malone', 'Contabilidade','Junior'],
        [12, 'Kelly Kapoor', 'Administrativo','Pleno'],
        [13, 'Creed Bratton', 'Administrativo','Pleno'],
        [14, 'Meredith Palmer', 'Administrativo','Pleno'],
        [15, 'Darryl Philbin', 'Armazém','Sênior'],
        [16, 'Lonny Smith', 'Armazém','Pleno'],
        [17, 'Madge Parker', 'Armazém','Pleno'],
        [18, 'Glenn Godwin', 'Armazém','Junior'],
        [19, 'Hide Lee', 'Armazém','Junior'],
        [20, 'Toby Flenderson', 'Recursos Humanos','Sênior'],
    ]

    datas_possiveis = pd.date_range(
        start="2020-01-01",
        end="2022-05-10"
    )

    registros = []

    for id_func, nome, area,cargo in funcionarios:
        registros.append({
            'id': id_func,
            'Nome': nome,
            'Area': area,
            'Cargo': cargo,
            'Data_Contratacao': random.choice(datas_possiveis),
        })

    return pd.DataFrame(registros)



def monta_comissao():
    df_funcionarios = monta_funcionarios()

    comissionamento = []
    for y,x in df_funcionarios.iterrows():
        if x['Cargo'] in (['Sênior','Gerente','Sub-Gerente']):
            Comissao_minima = 0.15 
            Comissao_maxima = 0.2
        elif x['Cargo'] == 'Pleno':
            Comissao_minima = 0.05
            Comissao_maxima = 0.08
        else:
            Comissao_minima = 0.02 
            Comissao_maxima = 0.05
        
        comissionamento.append({
            'id_funcionario': x['id'],
            'Comissao_minima': Comissao_minima,
            'Comissao_maxima': Comissao_maxima
        })

    return pd.DataFrame(comissionamento)