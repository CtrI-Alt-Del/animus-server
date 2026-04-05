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
- **AI (`src/animus/ai/`)**: Workflows, teams e saídas estruturadas com Agno/Gemini para casos de uso síncronos guiados pelo `core`.
- **PubSub (`src/animus/pubsub/`)**: Orquestracao assincrona por eventos (Inngest).

## Fluxo de Dados (resumo)

HTTP Request -> Middleware -> Router -> Controller -> UseCase (`core`) -> Repository Interface -> Repository SQLAlchemy -> Database -> Response JSON.

Eventos assincronos: UseCase publica evento via `Broker` -> PubSub (Inngest) -> Job/Canal WebSocket -> Cliente conectado.

Fluxos de autenticacao ja implementados:
- `POST /auth/sign-up` -> `SignUpController` -> `SignUpUseCase` -> `AccountsRepository` / `HashProvider` / `OtpProvider` / `CacheProvider` -> `Broker` -> `SendAccountVerificationEmailJob` -> `EmailSenderProvider`.
- `POST /auth/resend-verification-email` -> `ResendVerificationEmailController` -> `ResendVerificationEmailUseCase` -> `AccountsRepository` / `OtpProvider` / `CacheProvider` -> `Broker` -> `SendAccountVerificationEmailJob`.
- `POST /auth/verify-email` -> `VerifyEmailController` -> `VerifyEmailUseCase` -> `AccountsRepository` / `CacheProvider` / `JwtProvider` -> `SessionDto`.
- `POST /auth/sign-in` -> `SignInController` -> `SignInUseCase` -> `AccountsRepository` / `HashProvider` / `JwtProvider` -> `SessionDto`.

Fluxos de intake ja implementados:
- `POST /intake/analyses` -> `CreateAnalysisController` -> `AuthPipe` / `DatabasePipe` -> `CreateAnalysisUseCase` -> `AnalisysesRepository` -> PostgreSQL (`analyses`) -> `AnalysisDto`.
- `GET /intake/analyses` -> `ListAnalysesController` -> `AuthPipe` / `DatabasePipe` -> `ListAnalysesUseCase` -> `AnalisysesRepository` -> PostgreSQL (`analyses`) -> `CursorPaginationResponseSchema[AnalysisDto]`.
- `GET /intake/analyses/{analysis_id}` -> `GetAnalysisController` -> `AuthPipe` / `DatabasePipe` -> `GetAnalysisUseCase` -> `AnalisysesRepository` -> PostgreSQL (`analyses`) -> `AnalysisDto`.
- `PATCH /intake/analyses/{analysis_id}/name` -> `RenameAnalysisController` -> `AuthPipe` / `DatabasePipe` -> `RenameAnalysisUseCase` -> `AnalisysesRepository` -> PostgreSQL (`analyses`) -> `AnalysisDto`.
- `PATCH /intake/analyses/{analysis_id}/archive` -> `ArchiveAnalysisController` -> `AuthPipe` / `DatabasePipe` -> `ArchiveAnalysisUseCase` -> `AnalisysesRepository` -> PostgreSQL (`analyses`) -> `AnalysisDto`.
- `POST /intake/petitions` -> `CreatePetitionController` -> `AuthPipe` / `IntakePipe.verify_analysis_by_account(...)` -> `CreatePetitionUseCase` -> `PetitionsRepository` / `AnalisysesRepository` / `Broker` -> PostgreSQL (`petitions`, `petition_summaries`, `analyses`) -> `PetitionDto`.
- `GET /intake/analyses/{analysis_id}/petition` -> `GetAnalysisPetitionController` -> `IntakePipe.verify_analysis_by_account_from_request(...)` -> `GetAnalysisPetitionUseCase` -> `PetitionsRepository` -> PostgreSQL (`petitions`) -> `PetitionDto`.
- `POST /intake/petitions/{petition_id}/summary` -> `SummarizePetitionController` -> `AuthPipe` / `IntakePipe.verify_petition_document_path_by_account(...)` -> `StoragePipe` -> `GetDocumentContentUseCase` -> `FileStorageProvider` / `PdfProvider` / `DocxProvider` -> `SummarizePetitionWorkflow` -> `CreatePetitionSummaryUseCase` -> `PetitionSummariesRepository` -> PostgreSQL (`petition_summaries`) -> `PetitionSummaryDto`.
- `GET /intake/petitions/{petition_id}/summary` -> `GetPetitionSummaryController` -> `IntakePipe.verify_petition_by_account(...)` -> `GetPetitionSummaryUseCase` -> `PetitionSummariesRepository` -> PostgreSQL (`petition_summaries`) -> `PetitionSummaryDto`.
- `GET /intake/analyses/{analysis_id}/petitions` -> `ListAnalysisPetitionsController` -> `IntakePipe.verify_analysis_by_account_from_request(...)` -> `ListAnalysisPetitionsUseCase` -> `PetitionsRepository` / `PetitionSummariesRepository` -> PostgreSQL (`petitions`, `petition_summaries`) -> `ListResponse[AnalysisPetitionDto]`.
- `POST /intake/analyses/{analysis_id}/precedents/search` -> `SearchAnalysisPrecedentsController` -> `IntakePipe.verify_analysis_by_account_from_request(...)` -> `RequestAnalysisPrecedentsSearchUseCase` -> `Broker` -> `AnalysisPrecedentsSearchRequestedEvent` -> `SearchAnalysisPrecedentsJob`.
- `GET /intake/analyses/{analysis_id}/precedents` -> `ListAnalysisPrecedentsController` -> `IntakePipe.verify_analysis_by_account_from_request(...)` -> `ListAnalysisPrecedentsUseCase` -> `AnalysisPrecedentsRepository` -> PostgreSQL (`analysis_precedents`) -> `list[AnalysisPrecedentDto]`.
- `GET /intake/analyses/{analysis_id}/status` -> `GetAnalysisStatusController` -> `IntakePipe.verify_analysis_by_account_from_request(...)` -> `Analysis.status` -> `AnalysisStatusDto`.
- `PATCH /intake/analyses/{analysis_id}/precedents/choose` -> `ChooseAnalysisPrecedentController` -> `IntakePipe.verify_analysis_by_account_from_request(...)` -> `ChooseAnalysisPrecedentUseCase` -> `AnalysisPrecedentsRepository` / `AnalisysesRepository` -> PostgreSQL (`analysis_precedents`, `analyses`) -> `AnalysisStatusDto`.
- `GET /intake/analyses/{analysis_id}/report` -> `GetAnalysisReportController` -> `AuthPipe` / `DatabasePipe` -> `GetAnalysisReportUseCase` -> `AnalisysesRepository` / `PetitionsRepository` / `PetitionSummariesRepository` / `AnalysisPrecedentsRepository` -> PostgreSQL (`analyses`, `petitions`, `petition_summaries`, `analysis_precedents`) -> `AnalysisReportDto`.

Fluxo assincrono de precedentes:
- `AnalysisPrecedentsSearchRequestedEvent` -> `SearchAnalysisPrecedentsJob` -> `UpdateAnalysisStatusUseCase` (`SEARCHING_PRECEDENTS`) -> `SearchAnalysisPrecedentsUseCase` -> busca vetorial + hidratacao de precedentes.
- O mesmo job segue para `GENERATING_SYNTHESIS`, executa o workflow de sintese, substitui os `analysis_precedents` persistidos e conclui em `WAITING_PRECEDENT_CHOISE`.
- Em falhas nao tratadas, o job marca a `Analysis` como `FAILED`, preservando observabilidade por polling via status persistido.

Fluxo assincrono de substituicao de peticao:
- `CreatePetitionUseCase` detecta peticao anterior, publica `PetitionReplacedEvent`, remove a peticao antiga com cascade do `PetitionSummary` e atualiza a `Analysis` para `PETITION_UPLOADED` antes de persistir a nova peticao.
- `PetitionReplacedEvent` -> `RemovePetitionDocumentFileJob` -> `GcsFileStorageProvider.remove_files(...)`, tratando blob inexistente como no-op para manter idempotencia.

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
| **Linguagem** | Python 3.13+ | Linguagem principal |
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
├── ai/
├── validation/
├── database/
├── providers/
├── pubsub/
```

## Contrato da API

A API do animus Server e RESTful com payloads JSON. Os atributos seguem padrao `snake_case`.
