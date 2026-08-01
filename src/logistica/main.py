"""
Pipeline de execução da etapa de Logística: gera a base sintética
(armazéns, clientes, produtos, funcionários, vendas) e calcula a rota
otimizada de entrega para cada armazém, em cada data de saída.
"""

import os

import pandas as pd
from dotenv import load_dotenv

from src.shared import (
    carrega_municipios,
    carrega_lat_long,
    montar_armazens,
    montar_produtos,
    montar_clientes,
    monta_funcionarios,
    montar_vendas,
)

from src.logistica import (
    atribui_armazem, 
    calcular_melhor_rota,
    calcula_distancias_clientes
)

# ---------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------

load_dotenv()
api_key = os.getenv('ORS_API_KEY')

# período em que as vendas serão sorteadas, e quantidade de vendas a gerar
datas = pd.date_range(start="2026-01-01", end="2026-07-30")
n = 2000

# mostra todas as linhas ao exibir DataFrames grandes (sem truncar com "...")
pd.set_option('display.max_rows', None)


def main():
    # -------------------------------------------------------------
    # 1. Geração das entidades base
    # -------------------------------------------------------------

    # municípios e coordenadas são carregados uma única vez e reaproveitados
    # por montar_armazens() e montar_clientes(), evitando repetir chamadas de API
    df_municipios = carrega_municipios()
    df_lat_long = carrega_lat_long()

    df_armazem = montar_armazens(df_municipios, df_lat_long)
    df_produtos = montar_produtos()
    df_clientes = montar_clientes(df_municipios, df_lat_long)
    df_funcionarios = monta_funcionarios()
    df_vendas = montar_vendas(df_produtos, df_clientes, df_funcionarios, datas, n)

    # atribui a cada cliente o armazém mais próximo (distância real via OpenRouteService)
    df_entrega = atribui_armazem(df_armazem, df_clientes, api_key)

    # -------------------------------------------------------------
    # 2. Junta entregas com vendas para descobrir a data de saída de cada rota
    # -------------------------------------------------------------

    # cada venda gera uma entrega no dia seguinte à compra
    df_entrega_completo = df_entrega.merge(
        df_vendas,
        how='inner',
        on=['id_cliente'],
    )
    df_entrega_completo['data_saida'] = df_entrega_completo['data_venda'] + pd.Timedelta(days=1)

    # -------------------------------------------------------------
    # 3. Roteirização: ordem de visita dos clientes por armazém + data
    # -------------------------------------------------------------

    # distância entre cada par de clientes, usada para montar a rota depois
    # da primeira entrega (o caminho segue de cliente em cliente, não volta
    # ao armazém a cada parada)
    df_dist_clientes = calcula_distancias_clientes(df_clientes, api_key)

    # calcula a melhor rota (vizinho mais próximo) separadamente para cada
    # combinação de armazém + data de saída
    rotas_por_grupo = []
    for (id_armazem, data_saida), grupo in df_entrega_completo.groupby(['id_armazem', 'data_saida']):
        rota = calcular_melhor_rota(grupo, df_dist_clientes)
        rota['id_armazem'] = id_armazem
        rota['data_saida'] = data_saida
        rotas_por_grupo.append(rota)

    df_rotas_otimizadas = pd.concat(rotas_por_grupo, ignore_index=True)

    # ordena o resultado final: por data, depois por armazém, depois pela
    # sequência de entrega dentro de cada rota
    df_rotas = df_rotas_otimizadas.sort_values(['data_saida', 'id_armazem', 'ordem_entrega'])

    return df_rotas


if __name__ == "__main__":
    df_rotas = main()
    print(df_rotas)
