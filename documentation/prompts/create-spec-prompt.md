---
description: Prompt para criar uma especificação técnica detalhada com base no PRD e na arquitetura do equiny-server.
---

# Prompt: Criar Spec (equiny-server)

**Objetivo:** Detalhar a implementação técnica de uma feature, fix ou
refatoração no `equiny-server`, atuando como um Tech Lead Sênior. O documento
deve servir como uma ponte estritamente definida entre o PRD e o código, com
nível de detalhe suficiente para que a implementação seja direta e sem
ambiguidades.

## Entrada

- **PRD:** deve existir e estar finalizado antes de iniciar a spec.
- **Esboço da tarefa:** descrição da feature, fix ou refatoração a implementar.
- **Acesso à codebase:** necessário para pesquisa e validação de padrões.

> Se o PRD estiver ausente ou incompleto, não inicie a spec.
> Registre a lacuna em **Pendências / Dúvidas** e use a tool `question`.

---

## Diretrizes de Execução

### 1. Pesquisa e Contextualização

**1.1 Leitura obrigatória antes de escrever:**

- PRD associado à spec (localizado um nível acima na árvore de documentos).
- `documentation/architecture.md` — fluxo de dados, princípios e armadilhas.
- `documentation/rules/rules.md` — índice de regras; leia os docs acionados
  pelas camadas impactadas.

**1.2 Identificação de camadas impactadas**

Com base no PRD e no esboço da tarefa, classifique as camadas envolvidas:

| Camada | Localização | Responsabilidade |
|---|---|---|
| `core` | `src/equiny/core/` | Entidades, DTOs, erros, ports (interfaces), use cases |
| `database` | `src/equiny/database/` | Models SQLAlchemy, mappers, repositórios concretos |
| `rest` | `src/equiny/rest/` | Controllers HTTP finos; valida, adapta e delega |
| `routers` | `src/equiny/routers/` | Composição de rotas por contexto |
| `pipes` | `src/equiny/pipes/` | Providers de DI via `Depends(...)` |
| `validation` | `src/equiny/validation/` | Schemas Pydantic de entrada/saída |
| `providers` | `src/equiny/providers/` | Adaptadores de infraestrutura (jwt, hash, cache, storage, email, push) |
| `pubsub` | `src/equiny/pubsub/` | Jobs Inngest e PubSub Redis (eventos assíncronos) |
| `websocket` | `src/equiny/websocket/` | Channels e canais em tempo real |

**1.3 Mapeamento da codebase**

Use **Serena** para localizar arquivos e implementações similares. Reporte:

- Arquivos e módulos diretamente relacionados à feature (caminhos relativos reais)
- Implementações análogas que devem servir de referência
- Contratos existentes que a feature deve respeitar (interfaces, schemas, DTOs)
- Fluxo de dados atual e onde ele precisa ser estendido ou alterado
- Pontos de atenção: acoplamentos, riscos, arquivos que provavelmente serão impactados
- Lacunas: o que não foi encontrado e seria esperado

**1.4 Síntese e decisões**

Com base na pesquisa, tome as decisões de implementação:

- Defina o que será criado, modificado e removido — com justificativa baseada
  nas evidências coletadas
- Priorize consistência com os padrões identificados na codebase
- Mapeie o fluxo de dados principal da feature:
  `HTTP Request → Middleware → Router → Controller → Pipe/Depends → UseCase → Repository (port) → SQLAlchemy → PostgreSQL → Response JSON`
- Se houver eventos assíncronos: `UseCase → Broker → PubSub (Inngest/Redis) → Job / Canal WebSocket`
- Registre em **Pendências / Dúvidas** (seção 10) tudo que não teve evidência
  suficiente para decidir

---

### 2. Uso de Ferramentas Auxiliares

- **MCP Serena:** use para localizar arquivos e implementações similares na
  codebase. Acione sempre na fase de pesquisa.
- **MCP Context7:** use quando houver dúvida sobre uso correto de uma biblioteca
  específica (ex: `FastAPI`, `SQLAlchemy`, `Pydantic`, `Inngest`, `Redis`). Não
  use para decisões de arquitetura — essas seguem as regras do projeto.
- **Tool `question`:** use quando houver lacunas no PRD, incongruências com a
  codebase ou decisões críticas sem evidência suficiente. Não avance sem
  resposta quando o impacto for alto.

---

### 3. Qualidade e Densidade

- Seja direto; prefira listas e tabelas a blocos longos de texto.
- Use **negrito** para conceitos/decisões e `code` para termos técnicos
  (ex: `FastAPI`, `Depends`, `Session`, `DTO`, `UseCase`, `Pydantic`).
- Escreva em PT-BR; mantenha termos de programação em inglês e em `code`.
- **Nível de detalhe esperado em métodos:** descreva a assinatura Python (nome,
  parâmetros tipados e retorno) e uma linha de responsabilidade. Não escreva
  implementação — a spec define contratos, não código.

  Exemplo: `execute(dto: CreateHorseDto) -> HorseDto` — cria um cavalo e
  retorna o DTO com o ID gerado; lança `HorseAlreadyExistsError` se o nome
  já estiver em uso para o mesmo dono.

---

## Estrutura do Documento (modelo obrigatório)

Use frontmatter e hierarquia de cabeçalhos sem pular níveis.

### Cabeçalho (Frontmatter)

```md
---
title: <Título claro>
prd: <caminho para o PRD referente à spec, localizado um nível acima do diretório da spec>
status: <em_progresso|concluido>
last_updated_at: <YYYY-MM-DD>
---
```

---

# 1. Objetivo (Obrigatório)

[Resumo claro em um parágrafo do que será entregue funcionalmente e tecnicamente.]

---

# 2. Escopo (Obrigatório)

## 2.1 In-scope

[Liste o que está contemplado por esta spec.]

## 2.2 Out-of-scope

[Liste explicitamente o que não será tratado nesta spec.]

---

# 3. Requisitos (Obrigatório)

## 3.1 Funcionais

[Liste os requisitos funcionais relevantes para implementação, resumidos a partir do PRD.]

## 3.2 Não funcionais

[Liste apenas requisitos técnicos verificáveis/mensuráveis, quando aplicável.]

Categorias relevantes para o server (usar apenas se aplicável):

- **Performance:** ex: latência máxima de endpoint, throughput esperado
- **Segurança:** autenticação obrigatória, escopo de permissão
- **Idempotência:** jobs Inngest, operações de escrita
- **Resiliência:** retry, fallback em providers externos
- **Observabilidade:** logs, rastreamento de eventos
- **Compatibilidade retroativa:** mudanças de contrato HTTP ou schema de banco

> Evite requisitos vagos (ex: "ser rápido"). Prefira critérios verificáveis.

---

# 4. Regras de Negócio e Invariantes (Obrigatório)

[Liste as regras e invariantes de domínio que a implementação deve garantir.
Ex: "um cavalo não pode ter dois registros de saúde no mesmo dia".]

---

# 5. O que já existe? (Obrigatório)

[Liste recursos da codebase que serão utilizados ou impactados. Inclua apenas
itens realmente relevantes para implementar a mudança.]

## [Nome da Camada]

- **`NomeDaClasseOuModulo`** (`src/equiny/camada/arquivo.py`) — *[Breve
  descrição do uso (ex: use case a estender, repositório a implementar,
  schema similar).]*

---

# 6. O que deve ser criado? (Depende da tarefa)

[Descreva novos componentes dividindo por camadas. Para cada arquivo novo,
detalhe e marque explicitamente como **novo arquivo**.]

> Se uma camada não se aplicar, **não inclua ela na spec**.

## Camada Core (Entidades / Structures / DTOs)

- **Localização:** `src/equiny/core/<contexto>/` (**novo arquivo** se aplicável)
- **Tipo:** `@entity` | `@structure` | `@dto`
- **Atributos:** propriedades com tipos Python
- **Métodos / factory:** assinatura e responsabilidade

## Camada Core (Erros de Domínio)

- **Localização:** `src/equiny/core/<contexto>/errors/` (**novo arquivo** se aplicável)
- **Classe base:** ex: `DomainError`, `NotFoundError`, `ConflictError`
- **Motivo:** quando deve ser levantado

## Camada Core (Interfaces / Ports)

- **Localização:** `src/equiny/core/<contexto>/interfaces/` (**novo arquivo** se aplicável)
- **Métodos:** assinatura com tipos e responsabilidade

## Camada Core (Use Cases)

- **Localização:** `src/equiny/core/<contexto>/use_cases/` (**novo arquivo** se aplicável)
- **Dependências (ports injetados):** quais interfaces são consumidas
- **Método principal:** `execute(dto: ...) -> ...` — assinatura e responsabilidade
- **Fluxo resumido:** sequência de passos (busca, validação, persistência, evento)

## Camada Database (Models SQLAlchemy)

- **Localização:** `src/equiny/database/<contexto>/models/` (**novo arquivo** se aplicável)
- **Tabela:** nome da tabela no banco
- **Colunas:** nome, tipo SQLAlchemy e constraints relevantes
- **Relacionamentos:** ForeignKey, relações ORM

## Camada Database (Mappers)

- **Localização:** `src/equiny/database/<contexto>/mappers/` (**novo arquivo** se aplicável)
- **Métodos:**
  - `to_entity(model: ...) -> Entity` — assinatura e responsabilidade
  - `to_model(entity: ...) -> Model` — assinatura e responsabilidade

## Camada Database (Repositórios)

- **Localização:** `src/equiny/database/<contexto>/repositories/` (**novo arquivo** se aplicável)
- **Interface implementada:** port do `core`
- **Dependências:** `Session` SQLAlchemy
- **Métodos:** assinatura com tipos e responsabilidade

## Camada Validation (Schemas Pydantic)

- **Localização:** `src/equiny/validation/<contexto>/` (**novo arquivo** se aplicável)
- **Tipo:** `RequestSchema` | `ResponseSchema`
- **Atributos:** campos com tipos Pydantic e validações relevantes
- **Método `to_dto()` (se aplicável):** assinatura e DTO retornado

## Camada REST (Controllers)

- **Localização:** `src/equiny/rest/<contexto>/` (**novo arquivo** se aplicável)
- **Método HTTP e path:** ex: `POST /horses`
- **`status_code`:** código HTTP esperado
- **`response_model`:** schema Pydantic de saída
- **Dependências injetadas via `Depends`:** repositórios, providers, auth
- **Fluxo:** schema de entrada → `to_dto()` → `UseCase.execute()` → resposta

## Camada Routers

- **Localização:** `src/equiny/routers/` (**novo arquivo** se aplicável)
- **Prefixo da rota:** ex: `/horses`
- **Controllers registrados:** lista de controllers que compõem o router

## Camada Pipes

- **Localização:** `src/equiny/pipes/` (**novo arquivo** se aplicável)
- **Método `Depends`:** assinatura e o que provê (ex: repositório concreto)
- **Sessão SQLAlchemy:** se o pipe precisa de sessão, indicar como é obtida

## Camada Providers

- **Localização:** `src/equiny/providers/<nome>/` (**novo arquivo** se aplicável)
- **Interface implementada (port):** do `core`
- **Biblioteca/SDK utilizado:** ex: `boto3`, `firebase-admin`, `redis`
- **Métodos:** assinatura com tipos e responsabilidade

## Camada PubSub (Jobs Inngest)

- **Localização:** `src/equiny/pubsub/inngest/jobs/<contexto>/` (**novo arquivo** se aplicável)
- **Evento consumido:** nome do evento (`Event.NAME`) e payload esperado
- **Dependências:** use cases e repositórios instanciados no job
- **Passos (`step.run`):** sequência de ações do job
- **Idempotência:** como garantir que re-execuções são seguras

## Camada PubSub (Eventos de Domínio)

- **Localização:** `src/equiny/core/<contexto>/events/` (**novo arquivo** se aplicável)
- **`NAME`:** string identificadora do evento (ex: `"profiling/horse_created"`)
- **Payload:** atributos publicados com tipos

## Camada WebSocket (Channels)

- **Localização:** `src/equiny/websocket/channels/` (**novo arquivo** se aplicável)
- **Eventos suportados:** lista de `Event.NAME` que o channel trata
- **Dependências:** use cases e repositórios injetados
- **Fluxo por evento:** payload recebido → schema → `UseCase.execute()` → resposta/emissão

## Migrações Alembic (se aplicável)

- **Localização:** `migrations/versions/`
- **Operações:** tabelas criadas/alteradas, colunas adicionadas/removidas
- **Reversibilidade:** se o `downgrade` é seguro ou tem impacto de dados

---

# 7. O que deve ser modificado? (Depende da tarefa)

[Descreva alterações em código existente.]

## [Nome da Camada]

- **Arquivo:** `src/equiny/camada/arquivo.py`
- **Mudança:** [Descreva a mudança específica]
- **Justificativa:** [Por que a mudança é necessária]

> Se não houver alterações em código existente, escrever: **Não aplicável**.

---

# 8. O que deve ser removido? (Depende da tarefa)

[Descreva remoções de código legado, endpoints obsoletos ou limpeza de
refatoração.]

## [Nome da Camada]

- **Arquivo:** `src/equiny/camada/arquivo.py`
- **Motivo da remoção:** [Por que pode ser removido]
- **Impacto esperado:** [Dependências que precisam ser atualizadas]

> Se não houver remoções, escrever: **Não aplicável**.

---

# 9. Decisões Técnicas e Trade-offs (Obrigatório)

[Registre decisões relevantes para revisão futura.]

Para cada decisão importante:

- **Decisão**
- **Alternativas consideradas**
- **Motivo da escolha**
- **Impactos / trade-offs**

---

# 10. Diagramas e Referências (Obrigatório)

- **Fluxo de dados:** diagrama em notação ASCII mostrando a interação entre
  camadas para o fluxo principal da feature.
- **Fluxo assíncrono (se aplicável):** diagrama separado para eventos Inngest
  ou WebSocket, mostrando publicação → job → efeito.
- **Referências:** caminhos de arquivos similares na codebase para servir de
  exemplo de implementação.

---

# 11. Pendências / Dúvidas (Quando aplicável)

[Liste perguntas em aberto, incongruências e pontos que dependem de
confirmação.]

Para cada item:

- **Descrição da pendência**
- **Impacto na implementação**
- **Ação sugerida:** (ex: usar tool `question`, validar com produto, validar
  com arquitetura)

> Se não houver pendências, escrever: **Sem pendências**.

---

## Restrições (Obrigatório)

- **Não inclua testes automatizados na spec.**
- O `core` não deve depender de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest` ou
  qualquer detalhe de infraestrutura — se a spec violar isso, corrija antes de
  escrever.
- Todos os caminhos citados devem existir no projeto **ou** estar
  explicitamente marcados como **novo arquivo**.
- **Não invente** arquivos, métodos, contratos, schemas ou integrações sem
  evidência no PRD ou na codebase.
- Quando faltar informação suficiente, registrar em **Pendências / Dúvidas** e
  usar a tool `question` se necessário.
- Toda referência a código existente deve incluir caminho relativo real
  (`src/equiny/...`).
- Se uma seção não se aplicar, preencher explicitamente com **Não aplicável**.
- A spec deve ser consistente com os padrões da codebase (nomenclatura,
  organização de módulos, contratos e convenções por camada).---
description: Prompt para criar uma especificação técnica detalhada com base no PRD e na arquitetura do equiny-server.
---

# Prompt: Criar Spec (equiny-server)

**Objetivo:** Detalhar a implementação técnica de uma feature, fix ou
refatoração no `equiny-server`, atuando como um Tech Lead Sênior. O documento
deve servir como uma ponte estritamente definida entre o PRD e o código, com
nível de detalhe suficiente para que a implementação seja direta e sem
ambiguidades.

## Entrada

- **PRD:** deve existir e estar finalizado antes de iniciar a spec.
- **Esboço da tarefa:** descrição da feature, fix ou refatoração a implementar.
- **Acesso à codebase:** necessário para pesquisa e validação de padrões.

> Se o PRD estiver ausente ou incompleto, não inicie a spec.
> Registre a lacuna em **Pendências / Dúvidas** e use a tool `question`.

---

## Diretrizes de Execução

### 1. Pesquisa e Contextualização

**1.1 Leitura obrigatória antes de escrever:**

- PRD associado à spec (localizado um nível acima na árvore de documentos).
- `documentation/architecture.md` — fluxo de dados, princípios e armadilhas.
- `documentation/rules/rules.md` — índice de regras; leia os docs acionados
  pelas camadas impactadas.

**1.2 Identificação de camadas impactadas**

Com base no PRD e no esboço da tarefa, classifique as camadas envolvidas:

| Camada | Localização | Responsabilidade |
|---|---|---|
| `core` | `src/equiny/core/` | Entidades, DTOs, erros, ports (interfaces), use cases |
| `database` | `src/equiny/database/` | Models SQLAlchemy, mappers, repositórios concretos |
| `rest` | `src/equiny/rest/` | Controllers HTTP finos; valida, adapta e delega |
| `routers` | `src/equiny/routers/` | Composição de rotas por contexto |
| `pipes` | `src/equiny/pipes/` | Providers de DI via `Depends(...)` |
| `validation` | `src/equiny/validation/` | Schemas Pydantic de entrada/saída |
| `providers` | `src/equiny/providers/` | Adaptadores de infraestrutura (jwt, hash, cache, storage, email, push) |
| `pubsub` | `src/equiny/pubsub/` | Jobs Inngest e PubSub Redis (eventos assíncronos) |
| `websocket` | `src/equiny/websocket/` | Channels e canais em tempo real |

**1.3 Mapeamento da codebase**

Use **Serena** para localizar arquivos e implementações similares. Reporte:

- Arquivos e módulos diretamente relacionados à feature (caminhos relativos reais)
- Implementações análogas que devem servir de referência
- Contratos existentes que a feature deve respeitar (interfaces, schemas, DTOs)
- Fluxo de dados atual e onde ele precisa ser estendido ou alterado
- Pontos de atenção: acoplamentos, riscos, arquivos que provavelmente serão impactados
- Lacunas: o que não foi encontrado e seria esperado

**1.4 Síntese e decisões**

Com base na pesquisa, tome as decisões de implementação:

- Defina o que será criado, modificado e removido — com justificativa baseada
  nas evidências coletadas
- Priorize consistência com os padrões identificados na codebase
- Mapeie o fluxo de dados principal da feature:
  `HTTP Request → Middleware → Router → Controller → Pipe/Depends → UseCase → Repository (port) → SQLAlchemy → PostgreSQL → Response JSON`
- Se houver eventos assíncronos: `UseCase → Broker → PubSub (Inngest/Redis) → Job / Canal WebSocket`
- Registre em **Pendências / Dúvidas** (seção 10) tudo que não teve evidência
  suficiente para decidir

---

### 2. Uso de Ferramentas Auxiliares

- **MCP Serena:** use para localizar arquivos e implementações similares na
  codebase. Acione sempre na fase de pesquisa.
- **MCP Context7:** use quando houver dúvida sobre uso correto de uma biblioteca
  específica (ex: `FastAPI`, `SQLAlchemy`, `Pydantic`, `Inngest`, `Redis`). Não
  use para decisões de arquitetura — essas seguem as regras do projeto.
- **Tool `question`:** use quando houver lacunas no PRD, incongruências com a
  codebase ou decisões críticas sem evidência suficiente. Não avance sem
  resposta quando o impacto for alto.

---

### 3. Qualidade e Densidade

- Seja direto; prefira listas e tabelas a blocos longos de texto.
- Use **negrito** para conceitos/decisões e `code` para termos técnicos
  (ex: `FastAPI`, `Depends`, `Session`, `DTO`, `UseCase`, `Pydantic`).
- Escreva em PT-BR; mantenha termos de programação em inglês e em `code`.
- **Nível de detalhe esperado em métodos:** descreva a assinatura Python (nome,
  parâmetros tipados e retorno) e uma linha de responsabilidade. Não escreva
  implementação — a spec define contratos, não código.

  Exemplo: `execute(dto: CreateHorseDto) -> HorseDto` — cria um cavalo e
  retorna o DTO com o ID gerado; lança `HorseAlreadyExistsError` se o nome
  já estiver em uso para o mesmo dono.

---

## Estrutura do Documento (modelo obrigatório)

Use frontmatter e hierarquia de cabeçalhos sem pular níveis.

### Cabeçalho (Frontmatter)

```md
---
title: <Título claro>
prd: <caminho para o PRD referente à spec, localizado um nível acima do diretório da spec>
status: <em_progresso|concluido>
last_updated_at: <YYYY-MM-DD>
---
```

---

# 1. Objetivo (Obrigatório)

[Resumo claro em um parágrafo do que será entregue funcionalmente e tecnicamente.]

---

# 2. Escopo (Obrigatório)

## 2.1 In-scope

[Liste o que está contemplado por esta spec.]

## 2.2 Out-of-scope

[Liste explicitamente o que não será tratado nesta spec.]

---

# 3. Requisitos (Obrigatório)

## 3.1 Funcionais

[Liste os requisitos funcionais relevantes para implementação, resumidos a partir do PRD.]

## 3.2 Não funcionais

[Liste apenas requisitos técnicos verificáveis/mensuráveis, quando aplicável.]

Categorias relevantes para o server (usar apenas se aplicável):

- **Performance:** ex: latência máxima de endpoint, throughput esperado
- **Segurança:** autenticação obrigatória, escopo de permissão
- **Idempotência:** jobs Inngest, operações de escrita
- **Resiliência:** retry, fallback em providers externos
- **Observabilidade:** logs, rastreamento de eventos
- **Compatibilidade retroativa:** mudanças de contrato HTTP ou schema de banco

> Evite requisitos vagos (ex: "ser rápido"). Prefira critérios verificáveis.

---

# 4. Regras de Negócio e Invariantes (Obrigatório)

[Liste as regras e invariantes de domínio que a implementação deve garantir.
Ex: "um cavalo não pode ter dois registros de saúde no mesmo dia".]

---

# 5. O que já existe? (Obrigatório)

[Liste recursos da codebase que serão utilizados ou impactados. Inclua apenas
itens realmente relevantes para implementar a mudança.]

## [Nome da Camada]

- **`NomeDaClasseOuModulo`** (`src/equiny/camada/arquivo.py`) — *[Breve
  descrição do uso (ex: use case a estender, repositório a implementar,
  schema similar).]*

---

# 6. O que deve ser criado? (Depende da tarefa)

[Descreva novos componentes dividindo por camadas. Para cada arquivo novo,
detalhe e marque explicitamente como **novo arquivo**.]

> Se uma camada não se aplicar, **não inclua ela na spec**.

## Camada Core (Entidades / Structures / DTOs)

- **Localização:** `src/equiny/core/<contexto>/` (**novo arquivo** se aplicável)
- **Tipo:** `@entity` | `@structure` | `@dto`
- **Atributos:** propriedades com tipos Python
- **Métodos / factory:** assinatura e responsabilidade

## Camada Core (Erros de Domínio)

- **Localização:** `src/equiny/core/<contexto>/errors/` (**novo arquivo** se aplicável)
- **Classe base:** ex: `DomainError`, `NotFoundError`, `ConflictError`
- **Motivo:** quando deve ser levantado

## Camada Core (Interfaces / Ports)

- **Localização:** `src/equiny/core/<contexto>/interfaces/` (**novo arquivo** se aplicável)
- **Métodos:** assinatura com tipos e responsabilidade

## Camada Core (Use Cases)

- **Localização:** `src/equiny/core/<contexto>/use_cases/` (**novo arquivo** se aplicável)
- **Dependências (ports injetados):** quais interfaces são consumidas
- **Método principal:** `execute(dto: ...) -> ...` — assinatura e responsabilidade
- **Fluxo resumido:** sequência de passos (busca, validação, persistência, evento)

## Camada Database (Models SQLAlchemy)

- **Localização:** `src/equiny/database/<contexto>/models/` (**novo arquivo** se aplicável)
- **Tabela:** nome da tabela no banco
- **Colunas:** nome, tipo SQLAlchemy e constraints relevantes
- **Relacionamentos:** ForeignKey, relações ORM

## Camada Database (Mappers)

- **Localização:** `src/equiny/database/<contexto>/mappers/` (**novo arquivo** se aplicável)
- **Métodos:**
  - `to_entity(model: ...) -> Entity` — assinatura e responsabilidade
  - `to_model(entity: ...) -> Model` — assinatura e responsabilidade

## Camada Database (Repositórios)

- **Localização:** `src/equiny/database/<contexto>/repositories/` (**novo arquivo** se aplicável)
- **Interface implementada:** port do `core`
- **Dependências:** `Session` SQLAlchemy
- **Métodos:** assinatura com tipos e responsabilidade

## Camada Validation (Schemas Pydantic)

- **Localização:** `src/equiny/validation/<contexto>/` (**novo arquivo** se aplicável)
- **Tipo:** `RequestSchema` | `ResponseSchema`
- **Atributos:** campos com tipos Pydantic e validações relevantes
- **Método `to_dto()` (se aplicável):** assinatura e DTO retornado

## Camada REST (Controllers)

- **Localização:** `src/equiny/rest/<contexto>/` (**novo arquivo** se aplicável)
- **Método HTTP e path:** ex: `POST /horses`
- **`status_code`:** código HTTP esperado
- **`response_model`:** schema Pydantic de saída
- **Dependências injetadas via `Depends`:** repositórios, providers, auth
- **Fluxo:** schema de entrada → `to_dto()` → `UseCase.execute()` → resposta

## Camada Routers

- **Localização:** `src/equiny/routers/` (**novo arquivo** se aplicável)
- **Prefixo da rota:** ex: `/horses`
- **Controllers registrados:** lista de controllers que compõem o router

## Camada Pipes

- **Localização:** `src/equiny/pipes/` (**novo arquivo** se aplicável)
- **Método `Depends`:** assinatura e o que provê (ex: repositório concreto)
- **Sessão SQLAlchemy:** se o pipe precisa de sessão, indicar como é obtida

## Camada Providers

- **Localização:** `src/equiny/providers/<nome>/` (**novo arquivo** se aplicável)
- **Interface implementada (port):** do `core`
- **Biblioteca/SDK utilizado:** ex: `boto3`, `firebase-admin`, `redis`
- **Métodos:** assinatura com tipos e responsabilidade

## Camada PubSub (Jobs Inngest)

- **Localização:** `src/equiny/pubsub/inngest/jobs/<contexto>/` (**novo arquivo** se aplicável)
- **Evento consumido:** nome do evento (`Event.NAME`) e payload esperado
- **Dependências:** use cases e repositórios instanciados no job
- **Passos (`step.run`):** sequência de ações do job
- **Idempotência:** como garantir que re-execuções são seguras

## Camada PubSub (Eventos de Domínio)

- **Localização:** `src/equiny/core/<contexto>/events/` (**novo arquivo** se aplicável)
- **`NAME`:** string identificadora do evento (ex: `"profiling/horse_created"`)
- **Payload:** atributos publicados com tipos

## Camada WebSocket (Channels)

- **Localização:** `src/equiny/websocket/channels/` (**novo arquivo** se aplicável)
- **Eventos suportados:** lista de `Event.NAME` que o channel trata
- **Dependências:** use cases e repositórios injetados
- **Fluxo por evento:** payload recebido → schema → `UseCase.execute()` → resposta/emissão

## Migrações Alembic (se aplicável)

- **Localização:** `migrations/versions/`
- **Operações:** tabelas criadas/alteradas, colunas adicionadas/removidas
- **Reversibilidade:** se o `downgrade` é seguro ou tem impacto de dados

---

# 7. O que deve ser modificado? (Depende da tarefa)

[Descreva alterações em código existente.]

## [Nome da Camada]

- **Arquivo:** `src/equiny/camada/arquivo.py`
- **Mudança:** [Descreva a mudança específica]
- **Justificativa:** [Por que a mudança é necessária]

> Se não houver alterações em código existente, escrever: **Não aplicável**.

---

# 8. O que deve ser removido? (Depende da tarefa)

[Descreva remoções de código legado, endpoints obsoletos ou limpeza de
refatoração.]

## [Nome da Camada]

- **Arquivo:** `src/equiny/camada/arquivo.py`
- **Motivo da remoção:** [Por que pode ser removido]
- **Impacto esperado:** [Dependências que precisam ser atualizadas]

> Se não houver remoções, escrever: **Não aplicável**.

---

# 9. Decisões Técnicas e Trade-offs (Obrigatório)

[Registre decisões relevantes para revisão futura.]

Para cada decisão importante:

- **Decisão**
- **Alternativas consideradas**
- **Motivo da escolha**
- **Impactos / trade-offs**

---

# 10. Diagramas e Referências (Obrigatório)

- **Fluxo de dados:** diagrama em notação ASCII mostrando a interação entre
  camadas para o fluxo principal da feature.
- **Fluxo assíncrono (se aplicável):** diagrama separado para eventos Inngest
  ou WebSocket, mostrando publicação → job → efeito.
- **Referências:** caminhos de arquivos similares na codebase para servir de
  exemplo de implementação.

---

# 11. Pendências / Dúvidas (Quando aplicável)

[Liste perguntas em aberto, incongruências e pontos que dependem de
confirmação.]

Para cada item:

- **Descrição da pendência**
- **Impacto na implementação**
- **Ação sugerida:** (ex: usar tool `question`, validar com produto, validar
  com arquitetura)

> Se não houver pendências, escrever: **Sem pendências**.

---

## Restrições (Obrigatório)

- **Não inclua testes automatizados na spec.**
- O `core` não deve depender de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest` ou
  qualquer detalhe de infraestrutura — se a spec violar isso, corrija antes de
  escrever.
- Todos os caminhos citados devem existir no projeto **ou** estar
  explicitamente marcados como **novo arquivo**.
- **Não invente** arquivos, métodos, contratos, schemas ou integrações sem
  evidência no PRD ou na codebase.
- Quando faltar informação suficiente, registrar em **Pendências / Dúvidas** e
  usar a tool `question` se necessário.
- Toda referência a código existente deve incluir caminho relativo real
  (`src/equiny/...`).
- Se uma seção não se aplicar, preencher explicitamente com **Não aplicável**.
- A spec deve ser consistente com os padrões da codebase (nomenclatura,
  organização de módulos, contratos e convenções por camada).