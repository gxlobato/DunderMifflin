# 📄 Dunder Mifflin

> *"I am running away from my responsibilities. And it feels good."* — Michael Scott

Um projeto de dados sintéticos inspirado na Dunder Mifflin, a empresa de papéis da sitcom **The Office** (versão americana). A intenção não é só a homenagem — é usar o universo da série como pano de fundo para simular, de forma incremental, as diferentes áreas de uma empresa real: logística, vendas, qualidade, RH e contabilidade.

A ideia é que cada etapa seja construída (e documentada) separadamente, começando pela logística — a primeira parte do negócio implementada até agora — e crescendo aos poucos para as demais áreas.

---

## 🎬 A homenagem

Todo o projeto é ambientado no universo de *The Office*:

- **Funcionários** são os personagens da série (Jim Halpert, Dwight Schrute, Michael Scott, Pam, Kevin, Creed, e por aí vai), cada um em uma área da empresa (Vendas, Gerência, Administrativo, Contabilidade, Armazém, RH) — um espelho dos papéis que eles tinham na Dunder Mifflin.
- **Produtos** são variações de papel (Kraft, Sulfite, Couché, Fotográfico...), referência direta ao ramo da empresa na série.
- **Municípios brasileiros** entram como pano de fundo geográfico — os armazéns e clientes são espalhados por cidades reais do Brasil, dando realismo às distâncias e rotas calculadas.

---

## 🗂️ Etapas do projeto

O projeto é dividido pelas áreas de negócio de uma empresa. Cada uma tem seu próprio nível de maturidade — algumas já implementadas, outras ainda por vir.

### 📦 Logística — *implementado*

A primeira etapa construída. Cobre a geração de armazéns e clientes, o cálculo de distâncias e tempos de viagem reais, a atribuição do armazém mais próximo a cada cliente, a estimativa de prazo de entrega e a roteirização otimizada das entregas.

📄 Detalhamento completo (lógicas aplicadas, escolhas técnicas, bugs encontrados e próximos passos): [`src/logistica/README.md`](src/logistica/README.md)

---

### 💰 Vendas — *ainda a ser implementado*

Hoje as vendas existem apenas como uma tabela de apoio para a logística (gerada de forma simples e aleatória, para alimentar as datas de saída das rotas). O plano é evoluir isso para uma área própria, com métricas de performance por vendedor, metas, sazonalidade e funil de vendas.

### ✅ Qualidade do produto — *ainda a ser implementado*

Simular controle de qualidade sobre os produtos (papéis) — taxa de defeito, devoluções, avaliações de cliente — e como isso se conecta com fornecedores e reposição de estoque.

### 👥 Recursos Humanos — *ainda a ser implementado*

Hoje o quadro de funcionários só tem nome, área e data de contratação. O plano é ir além: turnover, avaliação de desempenho, folha de pagamento, plano de carreira.

### 📊 Contabilidade — *ainda a ser implementado*

Consolidar os dados de vendas, frete e folha de pagamento em uma visão financeira: receita, custos operacionais (incluindo o custo de frete já mapeado por UF na logística), margem por produto e por rota.

---

## 🗂️ Estrutura do projeto

O projeto é organizado para crescer junto com as etapas descritas acima: entidades compartilhadas (funcionários, produtos, clientes) ficam centralizadas em `shared/`, e cada área de negócio ganha seu próprio módulo, seguindo sempre o mesmo padrão.

```
dunder-mifflin/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── src/
│   ├── shared/                      # entidades centrais, usadas por todas as áreas
│   │   ├── __init__.py
│   │   ├── municipios.py            # carrega_municipios, carrega_lat_long, buscar_lat_long
│   │   ├── entidades.py             # montar_armazens, montar_produtos, montar_clientes, monta_funcionarios
│   │   └── api_client.py            # wrapper genérico pra chamadas de API externa (ORS, IBGE)
│   │
│   ├── logistica/                   # etapa implementada
│   │   ├── __init__.py
│   │   ├── distancias.py            # calcula_distancias, calcula_distancias_clientes
│   │   ├── roteirizacao.py          # atribui_armazem, calcular_melhor_rota
│   │   └── main.py                  # pipeline de execução dessa etapa
│   │
│   ├── vendas/                      # a implementar — mesmo padrão de logistica/
│   ├── qualidade/                   # a implementar
│   ├── rh/                          # a implementar
│   └── contabilidade/               # a implementar
│
├── tests/
│   ├── test_logistica.py
│   └── ...
│
└── notebooks/                       # exploração/experimentação (Databricks exports, etc.)
    └── logistica_exploracao.ipynb
```

**Por que essa divisão:**

- **`shared/`** evita duplicar código entre áreas. Clientes e funcionários, por exemplo, não são exclusivos da logística — vendas e contabilidade também vão precisar deles, então centralizar evita reimplementação.
- **Uma pasta por área de negócio** (`logistica/`, `vendas/`, etc.) espelha a divisão por etapas deste README — cada módulo cresce de forma isolada, sem bagunçar o que já existe.
- **Um `main.py` por módulo**, em vez de um único arquivo geral na raiz — cada área terá seu próprio pipeline de execução. Um `main.py` na raiz do projeto pode futuramente orquestrar todos os módulos juntos.
- **`.env.example`** documenta as variáveis de ambiente necessárias (ex: `ORS_API_KEY=`) sem expor nenhuma chave real — importante já que chaves de API sensíveis apareceram acidentalmente em versões anteriores do projeto.
- **`tests/`** antecipa o item de testes automatizados já previsto no roadmap da logística.
- **Um README por módulo.** Cada pasta de área de negócio (`logistica/`, e futuramente `vendas/`, `qualidade/`, `rh/`, `contabilidade/`) tem seu próprio `README.md` com o detalhamento técnico daquela etapa — lógicas aplicadas, escolhas de design, bugs encontrados e próximos passos. Este README na raiz mantém só um resumo de cada etapa e um link para o detalhamento.

---

## 🌱 Visão de longo prazo

A meta é que cada área (Logística, Vendas, Qualidade, RH, Contabilidade) tenha suas próprias funções de geração de dados e suas próprias análises, todas conectadas pelas mesmas entidades centrais (funcionários, produtos, clientes) — formando uma base de dados sintética completa o suficiente para simular, estudar e demonstrar competências em diferentes frentes de engenharia e análise de dados, não só logística.
