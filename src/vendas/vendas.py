def montar_vendas(df_produtos, df_clientes, df_funcionarios, datas, n):
    """
    Gera `n` vendas sintéticas, sorteando produto, cliente, vendedor
    (todos os funcionários podem vender, com pesos diferentes) e data.
    """
    func = df_funcionarios['id'].tolist()
    area_por_id = df_funcionarios.set_index('id')['Area'].to_dict()

    # Jim e Dwight são os principais vendedores na Dunder Mifflin
    # eles recebem peso maior no sorteio pra aparecerem mais como vendedores
    top_vendedores = [1,2]

    peso =[]
    for x in func:
        if x in top_vendedores:
            peso.append(10)
        elif area_por_id[x] == 'Vendas':
            peso.append(7)
        else:
            peso.append(1)
    cargos = df_funcionarios.set_index('id')['Cargo'].to_dict()
    
    vendas = []
    for x in range(n):
        produto = df_produtos.sample(n=1).iloc[0]
        qtd = random.randint(1, 30)
        id_vendedor = random.choices(func, weights = peso, k=1)[0]
        
        valor_total = round(produto['valor_unitario'] * qtd, 2)

        # regra de desconto: depende do valor da venda, da área e do cargo do vendedor
        # quanto maior a venda e maior o cargo, maior o desconto máximo permitido
        desconto_pct = 0
        if valor_total > 1000:
            if area_por_id[id_vendedor] == 'Administrativo' and cargos[id_vendedor] in ['Gerente','Sub-Gerente']:
                desconto_pct = random.uniform(0,0.2)
            elif area_por_id[id_vendedor] == 'Vendas' and cargos[id_vendedor] =='Sênior':
                desconto_pct = random.uniform(0,0.15)
            elif area_por_id[id_vendedor] == 'Vendas' and cargos[id_vendedor] =='Pleno':
                desconto_pct = random.uniform(0,0.1)
            else: desconto_pct = random.uniform(0,0.05)
        elif valor_total > 800 and valor_total < 1000:
            if area_por_id[id_vendedor] == 'Administrativo' and cargos[id_vendedor] in ['Gerente','Sub-Gerente']:
                desconto_pct = random.uniform(0,0.15)
            elif area_por_id[id_vendedor] == 'Vendas' and cargos[id_vendedor] =='Sênior':
                desconto_pct = random.uniform(0,0.1)
            elif area_por_id[id_vendedor] == 'Vendas' and cargos[id_vendedor] =='Pleno':
                desconto_pct = random.uniform(0,0.05)
            else: desconto_pct = random.uniform(0,0.02)
        
        valor_desconto = round(valor_total * desconto_pct, 2)
        valor_final = round(valor_total - valor_desconto, 2)

        vendas.append({
            'id_venda': x + 1,
            'data_venda': random.choice(datas),
            'id_cliente': random.choice(df_clientes['id']),
            'id_vendedor': id_vendedor,
            'produto_id': produto['id'],
            'quantidade': qtd,
            'valor_total': valor_total,
            'valor_custo_total': round(qtd * produto['valor_custo'],2),
            'valor_desconto': valor_desconto,
            'valor_final': round(valor_final,4),
            'desconto_pct': round(desconto_pct,2),
        })

    return pd.DataFrame(vendas)