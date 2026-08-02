# 📦 Logística

Primeira etapa de negócio implementada no projeto **Dunder Mifflin**. Cobre a geração de armazéns e clientes, o cálculo de distâncias/tempos de viagem reais, a atribuição do armazém mais próximo a cada cliente (respeitando uma regra de cobertura regional) e a roteirização otimizada das entregas, com estimativa de horário e sinalização de risco de atraso.

> Para o contexto geral do projeto (a homenagem a *The Office*, a visão de longo prazo com as demais áreas do negócio), veja o [README na raiz](../../README.md). Para o histórico detalhado de decisões e bugs resolvidos ao longo do desenvolvimento, veja o [CHANGELOG](CHANGELOG.md).

---

## O que foi feito

1. Geração de uma base sintética de armazéns, clientes, produtos, funcionários e vendas.
2. Atribuição do armazém mais próximo a cada cliente, respeitando uma **regra de cobertura regional** (nem todo armazém pode atender qualquer região do país) — distância real calculada via OpenRouteService.
3. Estimativa de **prazo de entrega** por faixa de distância, e cálculo do **horário estimado de saída/chegada** em cada parada, sinalizando risco de atraso frente ao prazo prometido.
4. **Roteirização otimizada** por armazém + data de saída, usando a heurística do vizinho mais próximo.
5. **Persistência em cache (Parquet)**, organizada em camadas (dado bruto, entidade compartilhada, cache técnico, resultado de negócio), evitando reprocessar dados e recalcular distâncias via API a cada execução.

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
├── __init__.py          # reexporta as funções principais do pacote
├── distancias.py         # calcula_distancias, calcula_distancias_clientes
├── roteirizacao.py        # atribui_armazem, calcular_melhor_rota
├── previsao.py             # calcular_horarios_estimados, sinalizar_risco_atraso
└── main.py                 # orquestra as funções acima (lógica pura, sem gerar arquivos)
```

Depende de `src/shared/`, onde ficam as entidades centrais (armazéns, clientes, produtos, funcionários, vendas), o wrapper genérico de chamadas de API (`api_client.py`) e as funções de persistência em Parquet (`storage.py`), reaproveitáveis pelas demais áreas do negócio no futuro.

> **Scripts vs. notebooks:** os arquivos em `src/` contêm apenas a lógica (funções puras de geração, cálculo e roteirização) — nenhum deles gera arquivo Parquet por conta própria. A geração e persistência dos dados (chamadas a `carregar_ou_gerar`/`salvar_parquet`, apontando para os Volumes) acontece nos **notebooks** do Databricks, que importam essas funções e orquestram a execução. Isso mantém `src/` testável e reutilizável independente de onde os dados são salvos.

### Persistência dos dados

Os dados são cacheados em Parquet (hoje: Volumes do Unity Catalog no Databricks), em quatro camadas com propósitos diferentes:

- **`raw`** — dado externo cru, estável (municípios, lat/long).
- **`source`** — entidades de negócio geradas, reutilizáveis por qualquer área futura (clientes, produtos, funcionários...).
- **`cache`** — resultado caro de obter via API, sem valor analítico isolado (matriz de distâncias entre clientes).
- **`logistica`** — fatos exclusivos dessa etapa (entrega, rotas otimizadas).

Essa persistência é orquestrada pelo **notebook** de execução (não pelos arquivos em `src/`), que importa as funções deste módulo e as combina com `carregar_ou_gerar()`/`salvar_parquet()`, apontando para os caminhos dos Volumes.

Detalhamento completo dessa divisão no [CHANGELOG](CHANGELOG.md#persistência-dos-dados-parquet).

---

## Escolhas técnicas

- **Distância real via API**, não linha reta — mais realista para um cenário de logística.
- **Chamadas em lote**, usando o endpoint `matrix` do OpenRouteService, em vez de uma chamada por par — evita rate limit e economiza cota de API.
- **Heurística do vizinho mais próximo** para roteirização, em vez de resolver o TSP de forma exata — mais simples, boa aproximação.
- **Cobertura regional como regra de negócio**: cada armazém só atende clientes de certas regiões, mesmo que outro armazém esteja geograficamente mais perto.
- **Reprodutibilidade via seed** (`Faker.seed`, `random.seed`), e **chave de API via variável de ambiente**, nunca hardcoded.

Justificativas detalhadas de cada escolha no [CHANGELOG](CHANGELOG.md#escolhas-técnicas).

---

## Problemas encontrados pelo caminho

Bugs e ajustes recorrentes ao integrar múltiplas APIs externas: parâmetros de coordenadas invertidos, ambiguidade de nomes de cidade, rate limit da API, migração para fora do ambiente Databricks (`dbutils`), clientes duplicados quebrando a rota, e limite de pares por chamada ao escalar o número de clientes.

Descrição completa de cada bug e como foi resolvido no [CHANGELOG](CHANGELOG.md#problemas-encontrados-pelo-caminho).

---

## Próximos passos

- [ ] `FORCAR_ATUALIZACAO` por camada, não global.
- [ ] Horário de saída configurável por armazém.
- [ ] Cobertura regional mais flexível (configurável, não hardcoded).
- [ ] TSP de verdade (ex: OR-Tools), em vez da heurística do vizinho mais próximo.
- [ ] Custo de frete considerando o preço do combustível por UF.
- [ ] Capacidade de carga por veículo.
- [ ] Dashboard de visualização das rotas, com destaque para risco de atraso.
- [ ] Testes automatizados.
