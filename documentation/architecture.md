# Arquitetura do Projeto Animus Server

## Visao Geral

O animus Server usa arquitetura em camadas inspirada em Clean Architecture e Hexagonal Architecture (Ports and Adapters). O objetivo e reduzir acoplamento, isolar regra de negocio no `core` e facilitar testes unitarios e de integracao.

## Principios da Arquitetura

- **Dependencias para dentro**: camadas externas dependem das internas; o `core` nao depende de infraestrutura.
- **Separacao de responsabilidades**: cada camada tem um papel unico (dominio, transporte HTTP, persistencia, integracoes).
- **Ports and Adapters**: o `core` define contratos e as camadas externas implementam adaptadores concretos.
- **Use cases como orquestradores**: fluxos de negocio passam por `UseCase`, evitando logica espalhada.
- **Inversao de Dependencias**: controllers e jobs consomem interfaces do `core`, nao implementacoes concretas.
- **Controllers e jobs finos**: bordas validam/adaptam dados e delegam regra de negocio para o dominio.
- **Infraestrutura isolada**: SQLAlchemy, Redis, Inngest e SDKs externos ficam fora do `core`.
- **Testabilidade por design**: desacoplamento entre camadas permite teste unitario do dominio sem HTTP ou banco.

## Camadas

- **Core (`src/animus/core/`)**: Entidades, DTOs, erros de dominio, interfaces (ports) e use cases.
- **Rest (`src/animus/rest/`)**: Controllers HTTP e middlewares de request (sessao SQLAlchemy e client Inngest).
- **Routers (`src/animus/routers/`)**: Composicao de rotas por contexto e registro de endpoints.
- **Pipes (`src/animus/pipes/`)**: Providers de dependencia para `Depends(...)` (repositorios, auth, broker e upload).
- **Validation (`src/animus/validation/`)**: Schemas Pydantic de entrada/saida e conversao para DTO.
- **Database (`src/animus/database/`)**: Models SQLAlchemy, mappers e implementacoes concretas de repositorios.
- **Providers (`src/animus/providers/`)**: Adaptadores de infraestrutura.
- **PubSub (`src/animus/pubsub/`)**: Orquestracao assincrona por eventos (Inngest).

## Fluxo de Dados (resumo)

HTTP Request -> Middleware -> Router -> Controller -> UseCase (`core`) -> Repository Interface -> Repository SQLAlchemy -> Database -> Response JSON.

Eventos assincronos: UseCase publica evento via `Broker` -> PubSub (Inngest) -> Job/Canal WebSocket -> Cliente conectado.

## Padroes Principais

- **Clean + Hexagonal** para separar regra de negocio de infraestrutura.
- **Use Case** como ponto de entrada da regra de negocio.
- **Port and Adapter** para repositorios, broker e providers externos.
- **Data Mapper** para traducao dominio <-> ORM.
- **Dependency Injection** por `Depends(...)` e Pipes.
- **Event-Driven** para notificacoes e processamento assincrono.

## Decisoes Arquiteturais

- `core` nao depende de FastAPI, SQLAlchemy, Redis ou Inngest.
- Controllers sao finos: validam, convertem e delegam para use case.
- Transacao SQLAlchemy e controlada por middleware por request/job.
- Repositorios concretos vivem em `database`, contratos vivem no `core`.
- Eventos de dominio sao publicados por interface `Broker`, nao por SDK direto no dominio.

## Armadilhas a Evitar

1. Colocar regra de negocio em controller, pipe, job ou repository.
2. Acessar model ORM diretamente no `rest`.
3. Fazer `commit`/`rollback` manual em repositorio/controller.
4. Acoplar `core` a framework, SDK externo ou detalhes de infraestrutura.
5. Quebrar contratos de interface definidos no `core`.

## Stack Tecnologica

| Tecnologia | Pacote | Finalidade |
|------------|--------|------------|
| **Linguagem** | Python 3.12+ | Linguagem principal |
| **Framework** | FastAPI | API HTTP e DI |
| **Servidor ASGI** | Uvicorn (`fastapi[standard]`) | Runtime da aplicacao |
| **Banco de Dados** | PostgreSQL | Persistencia relacional |
| **ORM** | SQLAlchemy | Mapeamento e repositorios |
| **Driver SQL** | Psycopg 3 (`psycopg[binary]`) | Conexao PostgreSQL |
| **Migracoes** | Alembic | Versionamento de schema |
| **Cache/PubSub** | Redis | Cache e eventos em tempo real |
| **Jobs/Eventos** | Inngest | Processamento assincrono |
| **Validacao** | Pydantic | Schemas de request/response |
| **Testes** | Pytest | Suite de testes |
| **Lint/Format** | Ruff | Qualidade de codigo |
| **Type Check** | Pyright | Checagem estatica de tipos |
| **Task Runner** | Poe the Poet | Automacao de tarefas |
| **Dependencias** | uv | Gerenciamento de pacotes |
| **Infra Local** | Docker Compose | Ambientes locais (db/cache) |

## Infraestrutura de Hospedagem

No ambiente de producao, os servicos principais estao distribuidos da seguinte forma:

| Servico | Plataforma | Observacao |
|---|---|---|
| **API FastAPI** | Google Cloud Run | Executa a aplicacao HTTP em container (deploy serverless). |
| **PostgreSQL** | Supabase | Banco relacional gerenciado para persistencia principal. |
| **Redis** | Upstash | Cache e pub/sub em servico gerenciado. |
| **Inngest** | Inngest Cloud | Orquestracao de jobs e eventos assincronos. |

## Estrutura de Diretorios (essencial)

```text
src/animus/
├── core/
├── rest/
├── routers/
├── pipes/
├── validation/
├── database/
├── providers/
├── pubsub/
```

## Contrato da API

A API do animus Server e RESTful com payloads JSON. Os atributos seguem padrao `snake_case`.
