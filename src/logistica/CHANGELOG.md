# 📦 Logística — Changelog e detalhamento técnico

Histórico detalhado de decisões, escolhas técnicas e bugs resolvidos durante o desenvolvimento da etapa de Logística. Para uma visão resumida, veja o [README deste módulo](README.md); para o contexto geral do projeto, veja o [README na raiz](../../README.md).

---

## O que foi feito

1. Geração de uma base sintética de armazéns, clientes, produtos, funcionários e vendas.
2. Para cada cliente, descoberta de **qual armazém é o mais próximo** (distância rodoviária real, não linha reta).
3. Cruzamento de vendas com entregas para descobrir **quando cada rota deve sair**.
4. Para cada combinação de armazém + data de saída, cálculo de uma **ordem de visita otimizada** aos clientes daquela rota (heurística do vizinho mais próximo), incluindo a distância e o tempo de viagem estimado entre cada parada.
5. Estimativa de **prazo de entrega** por cliente, com base em faixas de distância até o armazém responsável (até 500 km: 1 dia; de 500 a 800 km: 2 dias; acima de 800 km: 3 dias).
6. Cálculo do **horário estimado de saída e chegada** em cada parada da rota (considerando duração de viagem acumulada + tempo fixo de parada por entrega), e sinalização de **risco de atraso** quando a chegada estimada ultrapassa o prazo prometido.
7. **Persistência em cache (Parquet)** de todas as entidades geradas e do resultado final, evitando reprocessar dados sintéticos e recalcular distâncias via API a cada execução.
8. **Regra de cobertura regional**: cada armazém só pode atender clientes de determinadas regiões do Brasil (ex: um cliente do Sul só é atendido pelo armazém do Sul ou do Sudeste), mesmo que geograficamente outro armazém esteja mais perto — simula uma área de cobertura de negócio, não só a menor distância possível.
9. **Matriz de distância cliente-cliente calculada por armazém**, não globalmente — como cada cliente já está vinculado a um armazém (e a rota nunca cruza entre armazéns diferentes), calcular a distância entre clientes de armazéns distintos era desperdício de chamadas de API.

---

## Fontes de dados externas usadas

| Fonte | Uso |
|---|---|
| [API do IBGE](https://servicodados.ibge.gov.br/) | Lista de municípios brasileiros, UF e região |
| [kelvins/municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros) | Latitude/longitude de cada município |
| [OpenRouteService](https://openrouteservice.org/) | Distância e duração rodoviária real entre dois pontos (Matrix API) |
| [Faker](https://faker.readthedocs.io/) | Geração de dados fictícios (nome de empresa, e-mail, endereço) |

---

## Estrutura de arquivos

```
src/logistica/
├── __init__.py         # reexporta as funções principais do pacote
├── distancias.py        # calcula_distancias, calcula_distancias_clientes
├── roteirizacao.py       # atribui_armazem, calcular_melhor_rota
├── previsao.py            # calcular_horarios_estimados, sinalizar_risco_atraso
└── main.py                # pipeline de execução dessa etapa (com cache em Parquet)
```

Esse módulo depende de `src/shared/`, onde ficam as entidades centrais (armazéns, clientes, produtos, funcionários, vendas), o wrapper genérico de chamadas de API (`api_client.py`) e as funções de persistência em Parquet (`storage.py`), reaproveitáveis pelas demais áreas do negócio no futuro.

### Persistência dos dados (Parquet)

Os dados gerados e calculados por essa etapa são cacheados em disco (hoje: Volumes do Unity Catalog no Databricks), organizados em quatro camadas com propósitos diferentes:

```
raw/                              # dado externo, cru, estável
├── municipios.parquet
└── lat_long.parquet

source/                           # entidades de negócio geradas, reutilizáveis por qualquer área futura
├── armazens.parquet
├── clientes.parquet
├── funcionarios.parquet
├── produtos.parquet
└── vendas.parquet

cache/                            # resultado caro de recalcular, sem valor analítico isolado
└── distancias_cliente_cliente.parquet

logistica/                        # fatos reais e exclusivos dessa etapa de negócio
├── entrega.parquet               # atribuição de armazém + prazo por cliente
└── rotas_otimizadas.parquet      # resultado final, com horário estimado e risco de atraso
```

A lógica de cada camada:

- **`raw`** — dado que vem de fora, sem nenhum processamento (municípios, lat/long). Muda raramente; não há motivo pra buscar de novo a cada execução.
- **`source`** — entidades de negócio (dimensões) reutilizáveis por qualquer área futura do projeto, não só logística — `clientes`, `produtos` e `funcionarios`, por exemplo, também serão usados por Vendas, RH e Contabilidade quando essas etapas forem implementadas.
- **`cache`** — resultado caro de obter (chamada de API sujeita a rate limit), mas que não é, em si, uma tabela de negócio consultável isoladamente — é puramente uma otimização técnica. Diferente de `raw`/`source`/`logistica`, essa camada pode ser livremente apagada e regenerada sem perda de informação de negócio.
- **`logistica`** — fatos exclusivos dessa etapa: o resultado da análise em si (quem entrega pra quem, quando, e o risco de atraso).

Esses diretórios **não são versionados no Git** (estão no `.gitignore`) — os dados são reproduzíveis via código, então versionar os arquivos gerados só infla o repositório e cria risco de inconsistência entre código e dados salvos. Quem clonar o repositório e rodar `main.py` gera a própria base localmente.

`main.py` usa `carregar_ou_gerar()` (de `src/shared/storage.py`) para cada etapa: se o `.parquet` já existe, carrega dele; senão, gera e salva. A constante `FORCAR_ATUALIZACAO`, no topo do arquivo, permite ignorar o cache e regenerar tudo do zero quando necessário (ex: depois de alterar a lógica de geração). Como essa flag hoje força todas as camadas de uma vez, vale ter cuidado: forçar `raw` sem necessidade reintroduz o risco de bloqueio 403/rate limit em APIs externas estáveis que não precisavam ser buscadas de novo.

---

## Escolhas técnicas

- **Distância real, não linha reta.** Em vez de usar a fórmula de haversine (linha reta entre dois pontos), o projeto usa a API do OpenRouteService, que calcula a distância seguindo as rodovias de verdade — mais realista para um cenário de logística.
- **Matriz de distâncias em lote, não par a par.** As distâncias (armazém-cliente e cliente-cliente) são pedidas em **uma única chamada de API** por conjunto, usando o endpoint `matrix` com `sources`/`destinations`, em vez de uma chamada por par. Isso evita estourar o rate limit e economiza cota da API.
- **Distância e duração calculadas juntas.** As chamadas à Matrix API pedem `["distance", "duration"]` de uma vez (em vez de só distância), aproveitando a mesma requisição para trazer o tempo de viagem estimado — evita uma segunda chamada de API só para isso.
- **Prazo de entrega por faixa de distância.** Em vez de usar o tempo de viagem bruto da API (que reflete só a duração da rodagem, não o tempo real de operação logística), o prazo de entrega usa faixas de distância simples (até 500 km, 500-800 km, acima de 800 km) como uma primeira aproximação de SLA — mais fácil de comunicar e ajustar do que uma fórmula baseada em duração de viagem.
- **Heurística do vizinho mais próximo para roteirização.** O problema de "melhor ordem para visitar N clientes" é um caso do Problema do Caixeiro Viajante (TSP), computacionalmente caro de resolver de forma exata. Optamos por uma heurística simples — começar do cliente mais próximo do armazém e sempre seguir para o cliente não visitado mais próximo — que dá uma rota boa (embora não necessariamente ótima) com pouquíssimo código.
- **Uma entrega por cliente, mesmo com várias vendas no mesmo dia.** Se um cliente comprou mais de um produto na mesma data, isso gera múltiplas linhas de venda, mas apenas **uma parada física** na rota (`drop_duplicates` por `id_cliente` antes de rotear).
- **Reprodutibilidade via seed.** `Faker.seed(42)` e `random.seed(42)` fixam a semente de geração aleatória, para que a base sintética seja a mesma a cada execução — importante para comparar resultados e depurar problemas.
- **Chave de API via variável de ambiente.** A `api_key` do OpenRouteService nunca fica hardcoded no código — é lida de uma variável de ambiente (`.env` + `python-dotenv`), para poder subir o projeto no Git com segurança.
- **Tempo fixo de parada por entrega.** O cálculo de horário estimado soma um tempo fixo (`TEMPO_PARADA_MIN`, hoje 15 min) a cada parada, além do tempo de viagem — sem isso, a rota assumiria que o caminhão nunca para para descarregar, subestimando o horário real de chegada nas paradas seguintes.
- **Risco de atraso por comparação de data-limite, não por duração bruta.** Em vez de comparar apenas a duração de viagem com algum limite arbitrário, a lógica calcula uma data-limite real (`data_saida + prazo`, até 23:59) e compara com o horário de chegada estimado — mais alinhado com a forma como um prazo de entrega é comunicado ao cliente.
- **Persistência em Parquet, não CSV.** Os dados gerados/calculados são cacheados em `data/`, usando Parquet em vez de CSV, porque preserva tipos (datas, inteiros, decimais) sem ambiguidade na releitura, além de ocupar menos espaço em disco.
- **Cache não versionado no Git.** A pasta `data/` fica no `.gitignore` — os dados são reproduzíveis via código (com seed fixa), então versioná-los só infla o repositório sem agregar valor.
- **Busca de coordenadas por código IBGE, não por nome de cidade.** `df_municipios` (API do IBGE) e `df_lat_long` (CSV do kelvins) nem sempre concordam na grafia/acentuação do nome de um município (ex: "São Vicente Férrer" vs "São Vicente Ferrer"). Casar as duas fontes pelo `codigo_ibge` — um identificador numérico único e estável — elimina esse tipo de divergência por completo.
- **Cobertura regional simulando regra de negócio, não só distância mínima.** Cada armazém só pode atender clientes de um conjunto definido de regiões (ex: Sul só é atendido pelos armazéns do Sul ou Sudeste), mesmo que geograficamente outro armazém esteja mais próximo. Isso simula uma área de cobertura real de uma transportadora, em vez de assumir que a distância bruta é o único critério de decisão.
- **Matriz de distância cliente-cliente calculada por armazém, não globalmente.** Depois que a cobertura regional entra em vigor, cada cliente já pertence a um único armazém, e a rota nunca cruza entre armazéns diferentes. Calcular a matriz completa entre todos os clientes do país geraria pares inúteis (nunca usados na roteirização) e aumentaria desnecessariamente o número de pares por chamada — o que, no plano gratuito do OpenRouteService (limite de 3.500 pares por requisição), limitava o projeto a no máximo ~59 clientes numa única matriz global. Calculando por armazém, o limite passa a valer por grupo, não pelo total.
- **Timestamps em microssegundos ao salvar Parquet.** O pandas grava colunas de data por padrão com precisão de nanossegundos, formato que o Spark (usado pelo Databricks para ler Parquet) não suporta. `salvar_parquet()` força `coerce_timestamps='us'` para evitar o erro `PARQUET_TYPE_ILLEGAL` ao ler os arquivos via Spark/SQL.

---

## Problemas encontrados pelo caminho

O desenvolvimento dessa etapa passou por bastante debugging — parte natural de um projeto que integra várias APIs externas. Os principais:

- **Ordem das coordenadas invertida.** A API do OpenRouteService espera `[longitude, latitude]`, e não `[latitude, longitude]` como seria mais intuitivo. Inverter isso silenciosamente jogava as coordenadas para o meio do oceano, e a API retornava `None` em vez de erro — o bug mais difícil de perceber do projeto.
- **Ambiguidade de nomes de cidade.** Existem municípios homônimos em estados diferentes (ex: "Belém" existe no Pará, em Minas Gerais e em Alagoas). Filtrar só pelo nome da cidade, sem considerar a UF, causava associações erradas de latitude/longitude.
- **Rate limit da API.** Fazer uma chamada de API por par armazém-cliente (em vez de uma chamada em lote) estourava o limite de requisições por minuto do plano gratuito do OpenRouteService, retornando `Rate Limit Exceeded` no meio do processamento. A solução foi consolidar tudo em uma única chamada por matriz, usando `sources`/`destinations`.
- **Bloqueio 403 do GitHub.** Requisições sem cabeçalho `User-Agent` eram ocasionalmente bloqueadas pelo GitHub ao baixar o CSV de coordenadas — resolvido adicionando um `User-Agent` customizado.
- **`dbutils` fora do Databricks.** O projeto foi originalmente desenvolvido em notebooks do Databricks, onde `dbutils.widgets.get("api_key")` era usado para acessar a chave da API sem expô-la no código. Como a intenção é manter o projeto versionado no GitHub — com histórico de commits, estrutura de módulos e facilidade de leitura para quem for avaliar o portfólio —, o código foi migrado para scripts `.py` independentes, fora do ambiente do notebook. Isso exigiu remover a dependência de `dbutils` (que só existe dentro do Databricks) e ajustar todas as funções para receber a `api_key` como parâmetro, carregada localmente a partir de um arquivo `.env` (via `python-dotenv`) — mantendo os dados sigilosos fora do código-fonte e fora do próprio Git (`.env` incluído no `.gitignore`).
- **Clientes duplicados quebrando a rota.** Quando um cliente tinha mais de uma venda no mesmo dia, ele aparecia duplicado no grupo de entrega — e a heurística de roteirização, ao tentar achar "a distância de um cliente até ele mesmo" (que não existe na matriz), quebrava com `IndexError`. Resolvido removendo duplicatas de `id_cliente` antes de calcular a rota.
- **Estado perdido ao reconectar o cluster (Databricks).** Cada reconexão do cluster limpa toda a memória — os dados sintéticos e as distâncias calculadas via API são recriados do zero, o que pode gerar resultados diferentes entre sessões se a seed não estiver completamente fixada (Faker *e* `random`).
- **Clientes ou trechos sem distância válida.** Em alguns casos, um cliente pode não ter coordenadas completas, ou a matriz de distâncias pode não retornar uma conexão válida entre dois pontos específicos (retornando `None`). Isso poderia quebrar a rota no meio do cálculo. Resolvido filtrando clientes sem coordenadas antes de montar a matriz, e interrompendo a rota de forma controlada (com aviso no console) quando não há candidato válido para o próximo trecho, em vez de lançar um erro não tratado.
- **Divergência de nomes entre fontes de dados.** Ao aumentar o número de clientes sintéticos, cidades com grafia/acentuação divergente entre a API do IBGE e o CSV do kelvins (ex: "São Vicente Férrer") passaram a causar `ValueError: Cidade não encontrada`. Resolvido casando as duas fontes pelo `codigo_ibge` em vez do nome do município.
- **Limite de pares da Matrix API estourado ao escalar o número de clientes.** Com uma matriz cliente-cliente global (todos contra todos), o limite de 3.500 pares por requisição do plano gratuito do OpenRouteService restringia o projeto a, no máximo, ~59 clientes numa única chamada. Resolvido calculando a matriz separadamente por armazém — como cada cliente já pertence a um único armazém e a rota nunca cruza entre armazéns, isso reduz drasticamente o número de pares por chamada e elimina o teto artificial de clientes.
- **`PARQUET_TYPE_ILLEGAL` ao ler os arquivos via Spark.** O Databricks (Spark) não conseguia ler colunas de data salvas pelo pandas em Parquet, por causa da diferença de precisão de timestamp (nanossegundos no pandas vs. microssegundos suportados pelo Spark). Resolvido forçando `coerce_timestamps='us'` na função `salvar_parquet()`.
- **Migração de DBFS local para Volumes do Unity Catalog.** Ao migrar a persistência de um caminho de disco local (`data/raw`, `data/logistica`) para os Volumes do Databricks (`/Volumes/workspace/dundermiffin/...`), a função `salvar_parquet()` precisou deixar de tentar criar subpastas automaticamente (`os.makedirs`), já que Volumes exigem que a estrutura de pastas já exista previamente (criada manualmente ou via `dbutils.fs.mkdirs`).

---

## Investigação: rotas com duração inviável e novo armazém em Goiânia

Uma análise de rotas (`notebooks/1. Analysis - Rotas.ipynb`) identificou entregas com duração total fisicamente impossível para um único dia — algumas rotas somavam mais de 80h de viagem. A investigação seguiu este caminho:

1. **Sintoma:** query agregando `SUM(duracao_percorrida_min)` por armazém/data revelou centenas de rotas acima de 10h (jornada de trabalho de referência).
2. **Primeira hipótese descartada:** volume de entregas por rota. Rotas com **1 única entrega** já apresentavam 30,6% de inviabilidade — o problema não era acúmulo de paradas, era a distância de trechos individuais.
3. **Causa raiz confirmada:** a regra de cobertura regional (`REGIOES_PERMITIDAS`) permitia que clientes do Centro-Oeste fossem atendidos pelo armazém de Recife (Nordeste) — distâncias de milhares de km.
4. **Comparação de cenários** (`exploracao/cenarios_centro_oeste.md`), calculando a distância real de cada cliente até armazéns candidatos (os 4 atuais + Goiânia):

   | Cenário | Distância média (km) | Clientes acima de 800 km |
   |---|---|---|
   | A — corrige a regra (CO → Sudeste+Sul), sem novo armazém | 817,7 | 17 |
   | B — realoca Recife → Goiânia | 999,2 | 21 |
   | **C — mantém os 4 armazéns e adiciona Goiânia** | **719,4** | **12** |

5. **Decisão:** Cenário C. Resultou em `montar_armazens()` ganhando um 5º armazém (Goiânia, código A5) e `REGIOES_PERMITIDAS` sendo ajustado para que o Centro-Oeste passe a ser atendido por Centro-Oeste/Sudeste, em vez de Nordeste.

**Pendência identificada, fora do escopo dessa mudança:** em todos os 3 cenários testados, um cliente da região Norte (atendido por Belém) manteve distância de ~4.100 km, já que nenhum cenário alterava a cobertura do Norte. Sugere que a região Norte tem um problema de cobertura equivalente ao do Centro-Oeste, ainda não investigado.

---

## Próximos passos

- [ ] **Cobertura da região Norte.** Identificado durante a investigação do Centro-Oeste: um cliente do Norte permanece a ~4.100 km do armazém de Belém em todos os cenários testados. Avaliar se precisa de um segundo armazém na região (ex: Manaus) ou de uma regra de SLA/frete diferenciada para clientes muito remotos.
- [x] ~~Cálculo de tempo de entrega.~~ A API já retorna a duração de viagem (`duracao_min`/`duracao_percorrida_min`) para cada trecho, e o prazo de entrega por cliente é estimado por faixa de distância.
- [x] ~~Horário estimado de chegada por parada.~~ `calcular_horarios_estimados()` soma a duração acumulada da rota + tempo de parada por entrega a partir de um horário de saída fixo, e `sinalizar_risco_atraso()` compara isso com o prazo prometido.
- [x] ~~Persistência dos dados gerados.~~ Todas as entidades e o resultado final da rota são cacheados em Parquet, organizados em 4 camadas (`raw`/`source`/`cache`/`logistica`) nos Volumes do Databricks, evitando reprocessar tudo (e recalcular distâncias via API) a cada execução.
- [ ] **`FORCAR_ATUALIZACAO` por camada, não global.** Hoje uma única flag força a regeneração de tudo (raw, source, cache, logística) de uma vez. Separar em `FORCAR_RAW`, `FORCAR_SOURCE`, `FORCAR_CACHE`, `FORCAR_LOGISTICA` evitaria reforçar dados estáveis (municípios, lat/long) sem necessidade — e o risco de bloqueio 403/rate limit que isso reintroduz.
- [ ] **Horário de saída configurável por armazém.** Hoje `HORARIO_SAIDA` é único e fixo para todos os armazéns; o próximo passo natural é permitir horários diferentes por armazém (ou por dia da semana).
- [ ] **Cobertura regional mais flexível.** Hoje o mapa de regiões permitidas (`REGIOES_PERMITIDAS`) é fixo no código; poderia evoluir para considerar também a distância real como critério de desempate entre múltiplos armazéns candidatos de regiões diferentes, ou virar uma tabela de configuração em vez de um dicionário hardcoded.
- [ ] **TSP de verdade.** Substituir a heurística do vizinho mais próximo por uma solução mais precisa usando uma biblioteca de otimização (ex: [OR-Tools](https://developers.google.com/optimization) do Google), para encontrar rotas mais próximas do ótimo, não apenas uma boa aproximação.
- [ ] **Custo de frete considerando o preço do combustível por UF.** Já existe uma integração inicial com uma API de preços de diesel por estado; a ideia é usá-la de forma consistente para calcular o custo real de cada rota, não só a distância.
- [ ] **Capacidade de carga por veículo.** Hoje a rota assume que todas as entregas de um dia cabem em um único veículo. Um próximo passo natural é considerar peso/volume dos produtos e limite de carga, dividindo entregas entre múltiplos veículos quando necessário.
- [ ] **Dashboard de visualização.** Mapa interativo mostrando as rotas otimizadas por armazém e data, com destaque visual para as entregas em risco de atraso.
- [ ] **Testes automatizados.** Cobrir as funções mais sensíveis a erro (parsing de coordenadas, geração de rota, cálculo de horário) com testes unitários.