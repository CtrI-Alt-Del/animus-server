---
title: "Endpoints de CRUD de analises no contexto Intake"
prd: "Nao aplicavel - PRD formal ausente; spec baseada na descricao do ticket ANI-29 por aprovacao do solicitante em 2026-03-31"
ticket: "https://joaogoliveiragarcia.atlassian.net/browse/ANI-29"
status: closed
last_updated_at: 2026-03-31
---

# 1. Objetivo

Implementar a superficie HTTP de CRUD de analises no contexto `intake`, reutilizando o dominio `Analysis` e os adaptadores ja existentes no projeto. A entrega adiciona cinco endpoints autenticados para criar, listar, detalhar, renomear e arquivar analises, com `controllers` finos, `use cases` dedicados, filtros por conta na listagem, ocultacao de existencia de recurso de outra conta com `404`, e um contrato HTTP explicito para paginacao por cursor.

---

# 2. Escopo

## 2.1 In-scope

- Adicionar `POST /intake/analyses`.
- Adicionar `GET /intake/analyses`.
- Adicionar `GET /intake/analyses/{analysis_id}`.
- Adicionar `PATCH /intake/analyses/{analysis_id}/name`.
- Adicionar `PATCH /intake/analyses/{analysis_id}/archive`.
- Criar `use cases` dedicados para cada endpoint novo.
- Reutilizar `AuthPipe` e `DatabasePipe` para autenticacao e injecao de repositorio.
- Ajustar o contrato de `AnalisysesRepository` para suportar listagem filtrada por conta e geracao de nome padrao sequencial.
- Ajustar a implementacao `SqlalchemyAnalisysesRepository` para refletir o novo contrato.
- Adicionar um schema HTTP reutilizavel para `cursor pagination` com `next_cursor: str | null`.
- Registrar os novos controllers no `IntakeRouter`.

## 2.2 Out-of-scope

- Criar endpoints de `folders`.
- Validar existencia ou ownership de `folder_id` contra persistencia de pastas.
- Alterar o comportamento dos endpoints ja existentes de `petitions`.
- Criar jobs `Inngest`, eventos de dominio, canais `WebSocket` ou `providers` novos.
- Alterar o schema da tabela `analyses` via migration.
- Corrigir o typo historico `AnalisysesRepository` para `AnalysesRepository` nesta tarefa.

---

# 3. Requisitos

## 3.1 Funcionais

- O servidor deve exigir autenticacao Bearer em todos os endpoints novos via `AuthPipe.get_account_id_from_request`.
- O endpoint de criacao deve aceitar apenas `folder_id` opcional no body; o cliente nao informa `name`.
- O servidor deve gerar automaticamente um nome unico no formato `Nova analise #N` para a conta autenticada.
- A analise criada deve nascer com `status = WAITING_PETITION`, `is_archived = false` e `created_at` no instante atual.
- O endpoint de listagem deve aceitar `search`, `cursor`, `limit` e `is_archived`, retornando `items` e `next_cursor`.
- O endpoint de detalhamento deve retornar `404` quando a analise nao existir ou pertencer a outra conta.
- O endpoint de rename deve aceitar `name` no body, persistir a alteracao e retornar `404` quando a analise nao existir ou pertencer a outra conta.
- O endpoint de archive deve ser idempotente, marcar `is_archived = true` e retornar `404` quando a analise nao existir ou pertencer a outra conta.
- Todos os endpoints novos devem ser registrados no `IntakeRouter`, mantendo o prefixo `/intake` ja adotado na codebase.

## 3.2 Nao funcionais

- **Performance:** a listagem deve usar paginacao por cursor no repositorio SQLAlchemy, com `limit + 1` para detectar proxima pagina e filtros por `account_id`, `is_archived` e busca textual por `name`.
- **Seguranca:** detalhe, rename e archive nao devem vazar a existencia de analises de outras contas; o resultado HTTP deve permanecer `404` para recurso ausente ou nao pertencente ao `account_id` autenticado.
- **Idempotencia:** `PATCH /intake/analyses/{analysis_id}/archive` deve retornar `200` mesmo se a analise ja estiver arquivada.
- **Compatibilidade retroativa:** a mudanca e apenas aditiva na API HTTP; nao deve exigir migration nova nem alterar o comportamento atual de `POST /intake/petitions`.

---

# 4. Regras de Negocio e Invariantes

- Toda `Analysis` pertence a exatamente uma conta identificada por `account_id`.
- A criacao de analise nao aceita nome vindo do cliente.
- O nome automatico deve ser gerado no servidor e ser unico dentro do conjunto atual de analises da conta no momento da criacao.
- A criacao sempre fixa `status` em `AnalysisStatusValue.WAITING_PETITION`.
- A criacao sempre fixa `is_archived` em `false`.
- O `rename` deve reaproveitar `Name.create`, portanto o valor e normalizado com `strip()` e deve ter pelo menos 2 caracteres.
- A listagem deve retornar apenas analises da conta autenticada e do estado de arquivamento solicitado.
- O acesso a uma analise de outra conta em detalhe, rename e archive deve ser tratado como `AnalysisNotFoundError`.
- O archive nunca desfaz arquivamento e nao deve falhar se a analise ja estiver arquivada.
- Quando informado, `folder_id` deve ser um ULID valido; a existencia da pasta nao e garantida nesta tarefa.

---

# 5. O que ja existe?

## Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) — entidade de dominio ja existente, com `name`, `folder_id`, `account_id`, `status`, `is_archived`, `created_at`, `create(...)` e `dto`.
- **`AnalysisStatus` e `AnalysisStatusValue`** (`src/animus/core/intake/domain/entities/analysis_status.py`) — estrutura de status ja existente; a criacao deve reutilizar `WAITING_PETITION`.
- **`AnalysisDto`** (`src/animus/core/intake/domain/entities/dtos/analysis_dto.py`) — contrato de saida ja existente para representar a analise nas bordas.
- **`AnalysisNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_not_found_error.py`) — erro de dominio ja mapeado para `404` por `AppErrorHandler`.
- **`AnalisysesRepository`** (`src/animus/core/intake/interfaces/analisyses_repository.py`) — port ja existente com `find_by_id`, `find_many`, `add`, `add_many` e `replace`.
- **`CursorPaginationResponse`** (`src/animus/core/shared/responses/cursor_pagination_response.py`) — resposta compartilhada ja existente para pagina por cursor; serve de contrato interno entre repositorio e `use case`.
- **`CreatePetitionUseCase`** (`src/animus/core/intake/use_cases/create_petition_use_case.py`) — referencia de `use case` simples que constroi entidade, persiste e retorna `Dto`.
- **`Account`** (`src/animus/core/auth/domain/entities/account.py`) — referencia de entidade com metodos mutadores de dominio (`verify`, `activate`, `deactivate`).
- **`VerifyEmailUseCase`** (`src/animus/core/auth/use_cases/verify_email_use_case.py`) — referencia de fluxo que muta entidade e persiste com `repository.replace(...)`.

## Database

- **`AnalysisModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_model.py`) — model ORM ja existente para a tabela `analyses`; possui `id`, `name`, `folder_id`, `account_id`, `status`, `is_archived` e herda `created_at` e `updated_at` de `Model`.
- **`AnalysisMapper`** (`src/animus/database/sqlalchemy/mappers/intake/analysis_mapper.py`) — traduz `AnalysisModel` para `Analysis` e vice-versa.
- **`SqlalchemyAnalisysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`) — implementacao concreta atual do port de analises; ja possui `find_by_id`, `find_many`, `add`, `add_many` e `replace`.
- **Migration da tabela `analyses`** (`migrations/versions/20260328_110000_create_analyses_table.py`) — evidencia que a persistencia principal ja existe e nao requer schema novo para esta feature.

## REST

- **`CreatePetitionController`** (`src/animus/rest/controllers/intake/create_petition_controller.py`) — referencia direta de controller fino no contexto `intake`, com `Depends(...)`, instanciacao do `use case` e retorno de `Dto`.
- **`SignInController`** (`src/animus/rest/controllers/auth/sign_in_controller.py`) — referencia de controller que repassa `named params` primitivos para `UseCase.execute(...)`.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) — ja traduz `NotFoundError` para `404`, `ForbiddenError` para `403` e `ValidationError` para `400`.

## Routers

- **`IntakeRouter`** (`src/animus/routers/intake/intake_router.py`) — router agregador do modulo `intake`, com prefixo `/intake` e registro atual de `CreatePetitionController` e `SummarizePetitionController`.

## Pipes

- **`AuthPipe`** (`src/animus/pipes/auth_pipe.py`) — resolve `account_id` a partir do header `Authorization` usando `JwtProvider` e `AccountsRepository`.
- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) — entrega `AnalisysesRepository` e outros repositorios concretos por `Depends(...)`.
- **`IntakePipe`** (`src/animus/pipes/intake_pipe.py`) — contem validacao de ownership de analise para o fluxo atual de `petitions`, mas hoje devolve `403` em caso de outra conta; isso nao atende ao requisito novo de ocultacao com `404`.

## Validation

- **`src/animus/validation/shared/__init__.py`** — modulo de validacao compartilhada existe, mas ainda nao possui schema reutilizavel para resposta paginada por cursor com `next_cursor` serializado como `string`.

---

# 6. O que deve ser criado?

## Camada Core (Use Cases)

### `CreateAnalysisUseCase`

- **Localizacao:** `src/animus/core/intake/use_cases/create_analysis_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalisysesRepository`
- **Metodo principal:** `execute(account_id: str, folder_id: str | None = None) -> AnalysisDto` — cria uma nova analise para a conta autenticada com nome automatico, status inicial e retorno em `Dto`.
- **Fluxo resumido:** converte `account_id` e `folder_id`; consulta o proximo numero disponivel para nome gerado; constroi `AnalysisDto` com `WAITING_PETITION`, `is_archived = false` e `created_at = now`; cria a entidade; persiste com `add(...)`; retorna `analysis.dto`.

### `ListAnalysesUseCase`

- **Localizacao:** `src/animus/core/intake/use_cases/list_analyses_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalisysesRepository`
- **Metodo principal:** `execute(account_id: str, search: str, cursor: str | None, limit: int, is_archived: bool) -> CursorPaginationResponse[AnalysisDto]` — lista analises da conta autenticada com filtro textual e paginacao por cursor.
- **Fluxo resumido:** converte `account_id`, `search`, `cursor`, `limit` e `is_archived`; delega ao repositorio; transforma cada `Analysis` retornada em `AnalysisDto`; devolve `CursorPaginationResponse` interno com `items` em `Dto`.

### `GetAnalysisUseCase`

- **Localizacao:** `src/animus/core/intake/use_cases/get_analysis_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalisysesRepository`
- **Metodo principal:** `execute(account_id: str, analysis_id: str) -> AnalysisDto` — busca uma analise por ID e devolve `404` sem vazar existencia para outra conta.
- **Fluxo resumido:** converte IDs; busca a analise; se nao existir ou se `analysis.account_id` divergir do `account_id` autenticado, levanta `AnalysisNotFoundError`; retorna `analysis.dto`.

### `RenameAnalysisUseCase`

- **Localizacao:** `src/animus/core/intake/use_cases/rename_analysis_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalisysesRepository`
- **Metodo principal:** `execute(account_id: str, analysis_id: str, name: str) -> AnalysisDto` — renomeia uma analise da conta autenticada e devolve o `Dto` atualizado.
- **Fluxo resumido:** busca a analise por ID com a mesma regra de ownership do `GetAnalysisUseCase`; executa a mutacao de dominio de rename; persiste com `replace(...)`; retorna `analysis.dto`.

### `ArchiveAnalysisUseCase`

- **Localizacao:** `src/animus/core/intake/use_cases/archive_analysis_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalisysesRepository`
- **Metodo principal:** `execute(account_id: str, analysis_id: str) -> AnalysisDto` — arquiva a analise da conta autenticada de forma idempotente.
- **Fluxo resumido:** busca a analise por ID com a mesma regra de ownership do `GetAnalysisUseCase`; executa a mutacao de dominio de archive; persiste o estado final com `replace(...)`; retorna `analysis.dto`.

## Camada Validation (Schemas Pydantic de Saida)

### `CursorPaginationResponseSchema`

- **Localizacao:** `src/animus/validation/shared/cursor_pagination_response_schema.py` (**novo arquivo**)
- **Tipo:** `ResponseSchema`
- **Atributos:** `items: list[ItemT]`, `next_cursor: str | None`
- **Objetivo:** expor um contrato HTTP reutilizavel para paginacao por cursor com serializacao explicita de `next_cursor` como `string | null`, sem depender diretamente do wrapper interno `CursorPaginationResponse` baseado em `pydantic.dataclasses`.

## Camada REST (Controllers)

### `CreateAnalysisController`

- **Localizacao:** `src/animus/rest/controllers/intake/create_analysis_controller.py` (**novo arquivo**)
- **`*Body`:** `_Body(folder_id: str | None = None)`; `folder_id` opcional, enviado como ULID em string quando presente.
- **Metodo HTTP e path:** `POST /analyses`.
- **`status_code`:** `201`
- **`response_model`:** `AnalysisDto`
- **Dependencias injetadas via `Depends`:** `Id` por `AuthPipe.get_account_id_from_request`; `AnalisysesRepository` por `DatabasePipe.get_analisyses_repository_from_request`.
- **Fluxo:** `_Body` e `account_id` -> `CreateAnalysisUseCase.execute(account_id=account_id.value, folder_id=body.folder_id)` -> resposta.

### `ListAnalysesController`

- **Localizacao:** `src/animus/rest/controllers/intake/list_analyses_controller.py` (**novo arquivo**)
- **`*Body`:** nao aplicavel; entrada por query params `search: str = ''`, `cursor: str | None = None`, `limit: int`, `is_archived: bool = False`.
- **Metodo HTTP e path:** `GET /analyses`.
- **`status_code`:** `200`
- **`response_model`:** `CursorPaginationResponseSchema[AnalysisDto]`
- **Dependencias injetadas via `Depends`:** `Id` por `AuthPipe.get_account_id_from_request`; `AnalisysesRepository` por `DatabasePipe.get_analisyses_repository_from_request`.
- **Fluxo:** query params -> `ListAnalysesUseCase.execute(...)` -> adaptacao de `next_cursor` para `str | None` no contrato HTTP -> resposta.

### `GetAnalysisController`

- **Localizacao:** `src/animus/rest/controllers/intake/get_analysis_controller.py` (**novo arquivo**)
- **`*Body`:** nao aplicavel.
- **Metodo HTTP e path:** `GET /analyses/{analysis_id}`.
- **`status_code`:** `200`
- **`response_model`:** `AnalysisDto`
- **Dependencias injetadas via `Depends`:** `Id` por `AuthPipe.get_account_id_from_request`; `AnalisysesRepository` por `DatabasePipe.get_analisyses_repository_from_request`.
- **Fluxo:** `analysis_id` e `account_id` -> `GetAnalysisUseCase.execute(account_id=account_id.value, analysis_id=analysis_id)` -> resposta.

### `RenameAnalysisController`

- **Localizacao:** `src/animus/rest/controllers/intake/rename_analysis_controller.py` (**novo arquivo**)
- **`*Body`:** `_Body(name: str)`; nome obrigatorio, validado no dominio por `Name.create`.
- **Metodo HTTP e path:** `PATCH /analyses/{analysis_id}/name`.
- **`status_code`:** `200`
- **`response_model`:** `AnalysisDto`
- **Dependencias injetadas via `Depends`:** `Id` por `AuthPipe.get_account_id_from_request`; `AnalisysesRepository` por `DatabasePipe.get_analisyses_repository_from_request`.
- **Fluxo:** `_Body` + `analysis_id` + `account_id` -> `RenameAnalysisUseCase.execute(account_id=account_id.value, analysis_id=analysis_id, name=body.name)` -> resposta.

### `ArchiveAnalysisController`

- **Localizacao:** `src/animus/rest/controllers/intake/archive_analysis_controller.py` (**novo arquivo**)
- **`*Body`:** nao aplicavel.
- **Metodo HTTP e path:** `PATCH /analyses/{analysis_id}/archive`.
- **`status_code`:** `200`
- **`response_model`:** `AnalysisDto`
- **Dependencias injetadas via `Depends`:** `Id` por `AuthPipe.get_account_id_from_request`; `AnalisysesRepository` por `DatabasePipe.get_analisyses_repository_from_request`.
- **Fluxo:** `analysis_id` e `account_id` -> `ArchiveAnalysisUseCase.execute(account_id=account_id.value, analysis_id=analysis_id)` -> resposta.

## Camada Routers

**Nao aplicavel.** Nao ha `router` novo; apenas extensao do `IntakeRouter` existente.

## Camada Pipes

**Nao aplicavel.** Os endpoints novos reutilizam `AuthPipe` e `DatabasePipe` existentes.

## Camada Providers

**Nao aplicavel.**

## Camada PubSub (Eventos de Dominio)

**Nao aplicavel.**

## Camada PubSub (Jobs Inngest)

**Nao aplicavel.**

## Camada WebSocket (Channels)

**Nao aplicavel.**

## Migracoes Alembic (se aplicavel)

**Nao aplicavel.** A tabela `analyses` ja existe e os endpoints previstos operam sobre o schema atual.

---

# 7. O que deve ser modificado?

## Camada Core

- **Arquivo:** `src/animus/core/intake/domain/entities/analysis.py`
- **Mudanca:** adicionar os metodos `rename(name: str) -> None` e `archive() -> None` na entidade `Analysis`.
- **Justificativa:** manter as mutacoes de nome e arquivamento dentro do dominio, alinhadas ao padrao ja usado em `Account`.

- **Arquivo:** `src/animus/core/intake/interfaces/analisyses_repository.py`
- **Mudanca:** alterar a assinatura de `find_many(...)` para receber `account_id: Id` e `is_archived: Logical`; adicionar `find_next_generated_name_number(account_id: Id) -> Integer`.
- **Justificativa:** a listagem precisa ser escopada pela conta autenticada e pelo estado de arquivamento; a criacao precisa de um contrato explicito para calcular o proximo sufixo do nome automatico sem acoplar o `use case` a SQLAlchemy.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudanca:** exportar os cinco novos `use cases` de analises.
- **Justificativa:** manter o padrao de exports publicos do contexto `intake`.

## Camada Database

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`
- **Mudanca:** atualizar `find_many(...)` para filtrar por `account_id`, `is_archived` e `name`, preservando o cursor por `id`; implementar `find_next_generated_name_number(...)` com base nas analises atuais da conta; manter `replace(...)` para persistir rename e archive.
- **Justificativa:** a implementacao concreta precisa refletir o novo port do `core` e garantir que a listagem nao atravesse fronteiras de conta.

## Camada Validation

- **Arquivo:** `src/animus/validation/shared/__init__.py`
- **Mudanca:** exportar `CursorPaginationResponseSchema`.
- **Justificativa:** estabilizar o import publico do schema reutilizavel de paginacao HTTP.

## Camada REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudanca:** exportar os novos controllers de analises.
- **Justificativa:** manter o padrao de agregacao publica dos endpoints do contexto.

## Camada Routers

- **Arquivo:** `src/animus/routers/intake/intake_router.py`
- **Mudanca:** registrar `CreateAnalysisController`, `ListAnalysesController`, `GetAnalysisController`, `RenameAnalysisController` e `ArchiveAnalysisController` no router existente.
- **Justificativa:** expor os novos endpoints dentro do modulo `intake`, preservando o prefixo `/intake` e a composicao centralizada do contexto.

---

# 8. O que deve ser removido?

**Nao aplicavel.**

---

# 9. Decisoes Tecnicas e Trade-offs

- **Decisao:** manter os endpoints sob `IntakeRouter`, resultando em paths reais `/intake/analyses...`.
- **Alternativas consideradas:** criar um router novo sem prefixo de contexto; alterar o prefixo atual de `IntakeRouter`.
- **Motivo da escolha:** `src/animus/routers/intake/intake_router.py` ja define `prefix='/intake'`, e o `app` inclui esse router diretamente.
- **Impactos / trade-offs:** o ticket descreve paths relativos `/analyses...`, mas a implementacao final segue o padrao existente da codebase e evita churn desnecessario no roteamento.

- **Decisao:** implementar a regra de ownership com `404` dentro dos `use cases` de analises, sem alterar `IntakePipe.verify_analysis_by_account(...)`.
- **Alternativas consideradas:** reaproveitar `IntakePipe.verify_analysis_by_account(...)`; alterar o pipe existente para devolver `404` em vez de `403`.
- **Motivo da escolha:** o pipe atual ja e usado por `CreatePetitionController` e hoje produz `403` para recurso de outra conta.
- **Impactos / trade-offs:** evita regressao no fluxo atual de `petitions`, ao custo de repetir a regra de fetch + ownership nos `use cases` novos.

- **Decisao:** criar `CursorPaginationResponseSchema` em `validation/shared` para o contrato HTTP da listagem.
- **Alternativas consideradas:** expor `CursorPaginationResponse[AnalysisDto]` diretamente no `response_model`; criar um schema local apenas no controller de listagem.
- **Motivo da escolha:** o ticket exige `next_cursor: string | null`, enquanto o wrapper interno atual usa `Id | None`; alem disso, `pydantic.dataclasses` genericas nao sao a melhor base para um contrato HTTP generico e reutilizavel.
- **Impactos / trade-offs:** adiciona um arquivo novo na camada `validation`, mas mantem o `core` desacoplado do contrato HTTP final e prepara reuso futuro.

- **Decisao:** preservar o typo historico `AnalisysesRepository` e `SqlalchemyAnalisysesRepository` nesta tarefa.
- **Alternativas consideradas:** renomear todos os arquivos, classes, imports e pipes para `Analyses...`.
- **Motivo da escolha:** o typo ja esta espalhado em `core`, `database`, `pipes` e controllers existentes; a tarefa do ticket e funcional, nao de nomenclatura.
- **Impactos / trade-offs:** a inconsistencia nominal permanece por ora, mas evita uma refatoracao transversal fora do escopo.

- **Decisao:** nao validar `folder_id` contra um repositorio de pastas nesta entrega.
- **Alternativas consideradas:** expandir `FoldersRepository` com `find_by_id(...)` e criar implementacao concreta; rejeitar qualquer `folder_id` recebido.
- **Motivo da escolha:** a codebase atual possui apenas `src/animus/core/intake/interfaces/folders_repository.py`, sem `find_by_id(...)`, sem model ORM e sem repositorio SQLAlchemy correspondente.
- **Impactos / trade-offs:** o endpoint aceita `folder_id` apenas como ULID valido e pode persistir referencia sem validacao relacional; isso fica registrado em pendencia explicita.

- **Decisao:** gerar o nome automatico por meio de um novo metodo do repositorio que retorna o proximo numero disponivel para o prefixo `Nova analise #` por conta.
- **Alternativas consideradas:** usar contagem total de analises; usar ULID no nome; mover toda a logica de descoberta do numero para SQLAlchemy sem contrato explicito no `core`.
- **Motivo da escolha:** a regra de nomeacao e de dominio, mas precisa consultar o estado atual persistido; o port explicito reduz acoplamento e evita nomes opacos para o usuario.
- **Impactos / trade-offs:** sem constraint de unicidade no banco, duas criacoes concorrentes ainda podem disputar o mesmo nome gerado; se o requisito evoluir para unicidade forte sob concorrencia, sera necessaria uma estrategia transacional ou schema adicional.

---

# 10. Diagramas e Referencias

- **Fluxo de dados:**

```text
POST /intake/analyses
  -> IntakeRouter
  -> CreateAnalysisController
  -> AuthPipe.get_account_id_from_request
  -> DatabasePipe.get_analisyses_repository_from_request
  -> CreateAnalysisUseCase
  -> AnalisysesRepository.find_next_generated_name_number
  -> AnalisysesRepository.add
  -> SqlalchemyAnalisysesRepository
  -> AnalysisModel / PostgreSQL (table: analyses)
  -> AnalysisDto
  -> JSON 201
```

- **Fluxo de dados:**

```text
GET /intake/analyses
  -> IntakeRouter
  -> ListAnalysesController
  -> AuthPipe.get_account_id_from_request
  -> DatabasePipe.get_analisyses_repository_from_request
  -> ListAnalysesUseCase
  -> AnalisysesRepository.find_many
  -> SqlalchemyAnalisysesRepository
  -> AnalysisModel / PostgreSQL (table: analyses)
  -> CursorPaginationResponse[AnalysisDto]
  -> CursorPaginationResponseSchema[AnalysisDto]
  -> JSON 200
```

- **Fluxo assincrono (se aplicavel):** Nao aplicavel.

- **Referencias:** `src/animus/rest/controllers/intake/create_petition_controller.py`
- **Referencias:** `src/animus/rest/controllers/auth/sign_in_controller.py`
- **Referencias:** `src/animus/core/intake/use_cases/create_petition_use_case.py`
- **Referencias:** `src/animus/core/auth/use_cases/verify_email_use_case.py`
- **Referencias:** `src/animus/core/auth/domain/entities/account.py`
- **Referencias:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`
- **Referencias:** `src/animus/routers/intake/intake_router.py`
- **Referencias:** `src/animus/pipes/auth_pipe.py`
- **Referencias:** `src/animus/rest/handlers/app_error_handler.py`

---

# 11. Pendencias / Duvidas

- **Descricao da pendencia:** nao existe PRD formal localizado na arvore local nem em pagina Confluence encontrada; esta spec foi baseada na descricao do ticket `ANI-29` por aprovacao explicita do solicitante.
- **Impacto na implementacao:** o ticket passa a ser a principal fonte de verdade funcional, reduzindo rastreabilidade entre PRD e spec.
- **Acao sugerida:** registrar um PRD formal posteriormente e atualizar o frontmatter `prd` da spec.

- **Descricao da pendencia:** `folder_id` pode ser persistido sem validacao de existencia ou ownership porque a codebase nao oferece `find_by_id(...)` em `FoldersRepository` nem adaptador SQLAlchemy correspondente.
- **Impacto na implementacao:** a API pode aceitar um `folder_id` valido sintaticamente, mas sem garantia de referencia consistente.
- **Acao sugerida:** validar com produto/arquitetura se essa validacao deve entrar em uma tarefa futura de `folders`.

- **Descricao da pendencia:** o ticket nao define explicitamente a ordenacao da listagem; a spec assume a estrategia ja existente em `SqlalchemyAnalisysesRepository`, com cursor baseado em `id` crescente.
- **Impacto na implementacao:** a ordem visivel no cliente pode divergir da expectativa de UX caso se espere itens mais recentes primeiro.
- **Acao sugerida:** validar com produto se a ordenacao atual atende ao caso de uso; se nao atender, abrir ajuste especifico de ordenacao e cursor.
