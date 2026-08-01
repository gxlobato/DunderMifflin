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

A primeira etapa construída. Cobre a geração de armazéns, clientes e o cálculo de rotas de entrega.

**O que foi feito:**
1. Geração de uma base sintética de armazéns, clientes, produtos, funcionários e vendas.
2. Para cada cliente, descoberta de **qual armazém é o mais próximo** (distância rodoviária real, não linha reta).
3. Cruzamento de vendas com entregas para descobrir **quando cada rota deve sair**.
4. Para cada combinação de armazém + data de saída, cálculo de uma **ordem de visita otimizada** aos clientes daquela rota (heurística do vizinho mais próximo).

**Fontes de dados externas usadas:**

| Fonte | Uso |
|---|---|
| [API do IBGE](https://servicodados.ibge.gov.br/) | Lista de municípios brasileiros, UF e região |
| [kelvins/municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros) | Latitude/longitude de cada município |
| [OpenRouteService](https://openrouteservice.org/) | Distância rodoviária real entre dois pontos (Matrix API) |
| [Faker](https://faker.readthedocs.io/) | Geração de dados fictícios (nome de empresa, e-mail, endereço) |

**Escolhas técnicas:**

- **Distância real, não linha reta.** Em vez de usar a fórmula de haversine (linha reta entre dois pontos), o projeto usa a API do OpenRouteService, que calcula a distância seguindo as rodovias de verdade — mais realista para um cenário de logística.
- **Matriz de distâncias em lote, não par a par.** As distâncias (armazém↔cliente e cliente↔cliente) são pedidas em **uma única chamada de API** por conjunto, usando o endpoint `matrix` com `sources`/`destinations`, em vez de uma chamada por par. Isso evita estourar o rate limit e economiza cota da API.
- **Heurística do vizinho mais próximo para roteirização.** O problema de "melhor ordem para visitar N clientes" é um caso do Problema do Caixeiro Viajante (TSP), computacionalmente caro de resolver de forma exata. Optamos por uma heurística simples — começar do cliente mais próximo do armazém e sempre seguir para o cliente não visitado mais próximo — que dá uma rota boa (embora não necessariamente ótima) com pouquíssimo código.
- **Uma entrega por cliente, mesmo com várias vendas no mesmo dia.** Se um cliente comprou mais de um produto na mesma data, isso gera múltiplas linhas de venda, mas apenas **uma parada física** na rota (`drop_duplicates` por `id_cliente` antes de rotear).
- **Reprodutibilidade via seed.** `Faker.seed(42)` e `random.seed(42)` fixam a semente de geração aleatória, para que a base sintética seja a mesma a cada execução — importante para comparar resultados e depurar problemas.
- **Chave de API via variável de ambiente.** A `api_key` do OpenRouteService nunca fica hardcoded no código — é lida de uma variável de ambiente (`.env` + `python-dotenv`), para poder subir o projeto no Git com segurança.

**Problemas encontrados pelo caminho:**

O desenvolvimento dessa etapa passou por bastante debugging — parte natural de um projeto que integra várias APIs externas. Os principais:

- **Ordem das coordenadas invertida.** A API do OpenRouteService espera `[longitude, latitude]`, e não `[latitude, longitude]` como seria mais intuitivo. Inverter isso silenciosamente jogava as coordenadas para o meio do oceano, e a API retornava `None` em vez de erro — o bug mais difícil de perceber do projeto.
- **Ambiguidade de nomes de cidade.** Existem municípios homônimos em estados diferentes (ex: "Belém" existe no Pará, em Minas Gerais e em Alagoas). Filtrar só pelo nome da cidade, sem considerar a UF, causava associações erradas de latitude/longitude.
- **Rate limit da API.** Fazer uma chamada de API por par armazém-cliente (em vez de uma chamada em lote) estourava o limite de requisições por minuto do plano gratuito do OpenRouteService, retornando `Rate Limit Exceeded` no meio do processamento. A solução foi consolidar tudo em uma única chamada por matriz, usando `sources`/`destinations`.
- **Bloqueio 403 do GitHub.** Requisições sem cabeçalho `User-Agent` eram ocasionalmente bloqueadas pelo GitHub ao baixar o CSV de coordenadas — resolvido adicionando um `User-Agent` customizado.
- **`dbutils` fora do Databricks.** A API do Databricks (`dbutils.widgets.get(...)`) não existe em ambientes Python "puros". Como o objetivo final é versionar o projeto no Git e rodá-lo fora do notebook, todas as funções foram ajustadas para receber a `api_key` como parâmetro, em vez de depender do Databricks.
- **Clientes duplicados quebrando a rota.** Quando um cliente tinha mais de uma venda no mesmo dia, ele aparecia duplicado no grupo de entrega — e a heurística de roteirização, ao tentar achar "a distância de um cliente até ele mesmo" (que não existe na matriz), quebrava com `IndexError`. Resolvido removendo duplicatas de `id_cliente` antes de calcular a rota.

**Próximos passos da logística:**

- [ ] **TSP de verdade.** Substituir a heurística do vizinho mais próximo por uma solução mais precisa usando uma biblioteca de otimização (ex: [OR-Tools](https://developers.google.com/optimization) do Google), para encontrar rotas mais próximas do ótimo, não apenas uma boa aproximação.
- [ ] **Cálculo de tempo de entrega.** Usar a distância acumulada de cada rota junto com uma velocidade média (ou, futuramente, o tempo de viagem real retornado pela própria API) para estimar horário de chegada em cada parada.
- [ ] **Custo de frete considerando o preço do combustível por UF.** Já existe uma integração inicial com uma API de preços de diesel por estado; a ideia é usá-la de forma consistente para calcular o custo real de cada rota, não só a distância.
- [ ] **Persistência dos dados gerados.** Salvar os DataFrames sintéticos (Parquet/CSV) após a primeira geração, para não depender de recalcular tudo (e regastar cota de API) a cada reconexão do cluster ou nova execução.
- [ ] **Capacidade de carga por veículo.** Hoje a rota assume que todas as entregas de um dia cabem em um único veículo. Um próximo passo natural é considerar peso/volume dos produtos e limite de carga, dividindo entregas entre múltiplos veículos quando necessário.
- [ ] **Dashboard de visualização.** Mapa interativo mostrando as rotas otimizadas por armazém e data.
- [ ] **Testes automatizados.** Cobrir as funções mais sensíveis a erro (parsing de coordenadas, geração de rota) com testes unitários.

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

---

## 🌱 Visão de longo prazo

A meta é que cada área (Logística, Vendas, Qualidade, RH, Contabilidade) tenha suas próprias funções de geração de dados e suas próprias análises, todas conectadas pelas mesmas entidades centrais (funcionários, produtos, clientes) — formando uma base de dados sintética completa o suficiente para simular, estudar e demonstrar competências em diferentes frentes de engenharia e análise de dados, não só logística.
