# 💰 Vendas

Módulo responsável por simular as vendas da Dunder Mifflin, conectando funcionários, produtos e clientes já existentes em `shared/`. Cobre o sorteio de cada venda (produto, cliente, vendedor e data), o cálculo de custo e faturamento, e uma regra de desconto escalonada por valor da venda, área e cargo do vendedor.

---

## 📌 O que foi adicionado às entidades compartilhadas

Antes de chegar em vendas, duas entidades de `shared/entidades.py` ganharam colunas novas, necessárias para as regras descritas abaixo:

- **`monta_funcionarios`**: coluna `Cargo` (Junior, Pleno, Sênior, Sub-Gerente, Gerente), usada para definir quem pode dar quanto de desconto.
- **`montar_produtos`**: coluna `valor_custo`, o custo de aquisição/produção de cada produto — separado de `valor_unitario`, que é o preço de venda.

---

## 🧮 `montar_vendas`

Gera `n` vendas sintéticas. Para cada venda, sorteia produto, quantidade, cliente, vendedor e data, e calcula os valores financeiros derivados.

### Quem pode vender (sorteio ponderado)

Diferente da primeira versão (restrita a funcionários da área "Vendas"), agora **qualquer funcionário pode aparecer como vendedor** — mas com pesos diferentes:

| Grupo | Peso |
|---|---|
| Dwight Schrute e Jim Halpert | 10 |
| Demais funcionários da área Vendas | 7 |
| Funcionários de outras áreas | 1 |

O sorteio usa `random.choices(func, weights=peso, k=1)`, que respeita esses pesos sem excluir ninguém — é uma homenagem à rivalidade (e talento) dos dois personagens como os melhores vendedores da série, mantendo realismo (outras áreas vendem pouco, mas vendem).

### Cálculo de valores

- `valor_total` = `valor_unitario` do produto × quantidade (valor bruto, sem desconto)
- `valor_custo_total` = `valor_custo` do produto × quantidade (para futura análise de margem na Contabilidade)
- `valor_desconto` = `valor_total` × `desconto_pct`
- `valor_final` = `valor_total` − `valor_desconto` (valor líquido, o que de fato "entra")

`valor_total` e `valor_final` são mantidos separados de propósito — perder o valor bruto significaria perder rastreabilidade de quanto desconto foi de fato concedido em cada venda.

### Regra de desconto

O desconto máximo permitido depende de **três fatores**: o valor da venda, a área do vendedor e o cargo. Cargos mais altos podem dar descontos maiores, e vendas maiores destravam faixas de desconto mais altas:

| Valor da venda | Administrativo (Gerente/Sub-Gerente) | Vendas (Sênior) | Vendas (Pleno) | Demais |
|---|---|---|---|---|
| > 1000 | até 20% | até 15% | até 10% | até 5% |
| 800 – 1000 | até 15% | até 10% | até 5% | até 2% |
| ≤ 800 | — | — | — | sem desconto |

Dentro de cada faixa, o percentual exato é sorteado com `random.uniform(0, limite)` — ou seja, o desconto varia venda a venda, não é sempre o teto da faixa.

**Ponto em aberto:** vendas com valor ≤ 800 nunca têm desconto, independente de quem vendeu. Isso foi uma decisão consciente ao montar a regra, mas pode ser revisitado se fizer sentido ter uma faixa mínima de desconto também para vendas menores.

---

## 🔜 Próximos passos

- Conectar `monta_comissao` a `montar_vendas`, decidindo a base de cálculo (bruto vs. líquido).
- Avaliar se vale adicionar `forma_pagamento`, `status_venda` (concluída/cancelada/devolvida) e `desconto` como campos formais de negócio, hoje ausentes.
- Persistir `montar_vendas` como Parquet em `data/vendas/`, seguindo o mesmo padrão de cache já usado na logística.