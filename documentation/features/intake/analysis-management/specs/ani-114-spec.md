---
title: ANI-114 - Endpoint de busca de rascunho de sentenca
prd: documentation/features/intake/analysis-management/prd.md
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-114
status: closed
last_updated_at: 2026-05-23
---

# 1. Objetivo

Implementar e ajustar o endpoint autenticado
`GET /intake/analyses/{analysis_id}/petition-drafts` para retornar a
`SecondInstanceJudgmentDraftDto` gerada pelo job de minuta de sentenca de
segunda instancia. A entrega deve validar existencia da analise, ownership da
conta autenticada, tipo de analise e disponibilidade do draft antes de expor o
artefato persistido.

---

# 2. Escopo

## 2.1 In-scope

- Expor a leitura HTTP do `SecondInstanceJudgmentDraft` por `analysis_id` em
  `GET /intake/analyses/{analysis_id}/petition-drafts`.
- Reaproveitar o contrato estruturado `SecondInstanceJudgmentDraftDto`.
- Garantir `404` quando a `Analysis` nao existir.
- Garantir `403` quando a `Analysis` nao pertencer ao `account_id` autenticado.
- Garantir `409` quando a analise nao for de segunda instancia.
- Garantir `404` quando a minuta ainda nao tiver sido gerada para a analise.
- Remover a exposicao GET parcial em
  `/intake/analyses/{analysis_id}/second-instance-judgment-drafts`.
- Manter a persistencia e o job de geracao ja preparados por `ANI-92` e `ANI-94`.

## 2.2 Out-of-scope

- Gerar ou regerar a minuta de sentenca.
- Alterar o job `GenerateSecondInstanceJudgmentDraftJob`.
- Alterar tabelas, mappers ou repositorios SQLAlchemy de judgment draft.
- Alterar o endpoint `POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts`,
  que continua sendo o trigger assincrono de geracao.
- Criar schema `validation/` novo para request ou response.
- Implementar exportacao em PDF da minuta.

---

# 3. Requisitos

## 3.1 Funcionais

- O endpoint deve responder em
  `GET /intake/analyses/{analysis_id}/petition-drafts`.
- A request deve exigir Bearer token valido via `AuthPipe`.
- O `UseCase` deve receber `analysis_id: str` e `account_id: str`.
- O `UseCase` deve buscar a `Analysis` pelo `analysis_id`.
- Se a `Analysis` nao existir, deve levantar `AnalysisNotFoundError`.
- Se `analysis.account_id` for diferente do `account_id` autenticado, deve
  levantar `ForbiddenError`.
- Se `analysis.type` nao for `AnalysisType.create_as_second_instance()`, deve
  levantar `SecondInstanceAnalysisRequiredError`.
- O `UseCase` deve buscar a minuta via
  `SecondInstanceJudgmentDraftsRepository.find_by_analysis_id(...)`.
- Se a minuta nao existir, deve levantar `SecondInstanceJudgmentDraftUnavailableError`,
  mantendo o mapeamento atual para `404`.
- Se a minuta existir, deve retornar `SecondInstanceJudgmentDraftDto`.

## 3.2 Nao funcionais

- **Seguranca:** a leitura do draft deve ser restrita ao dono da analise.
- **Compatibilidade retroativa:** o endpoint novo nao deve alterar o trigger
  `POST` de geracao nem o formato persistido do draft.
- **Consistencia arquitetural:** ownership e tipo da analise devem ser
  decididos no `core`, mantendo o controller fino.
- **Observabilidade:** erros de dominio devem continuar passando pelo
  `AppErrorHandler`, sem `HTTPException` manual no controller.

---

# 4. O que ja existe?

## Core

- **`SecondInstanceJudgmentDraft`**
  (`src/animus/core/intake/domain/structures/second_instance_judgment_draft.py`) -
  estrutura de dominio do draft com `analysis_id`, `report`,
  `merit_analysis`, `precedent_adherence_analysis`, `ruling`,
  `preliminary_issues` e `no_applicable_precedent_notice`.
- **`SecondInstanceJudgmentDraftDto`**
  (`src/animus/core/intake/domain/structures/dtos/second_instance_judgment_draft_dto.py`) -
  DTO estruturado que cruza a fronteira do `core` para REST.
- **`SecondInstanceJudgmentDraftsRepository`**
  (`src/animus/core/intake/interfaces/judgment_drafts_repository.py`) -
  port com `find_by_analysis_id(analysis_id: Id) -> SecondInstanceJudgmentDraft | None`,
  `add(...)` e `replace(...)`.
- **`GetSecondInstanceJudgmentDraftUseCase`**
  (`src/animus/core/intake/use_cases/get_second_instance_judgment_draft_use_case.py`) -
  use case atual de leitura; ja busca o draft, mas ainda nao valida a analise,
  ownership, tipo nem recebe `account_id`.
- **`CreateSecondInstanceJudgmentDraftUseCase`**
  (`src/animus/core/intake/use_cases/create_judgment_draft_use_case.py`) -
  persiste ou substitui a minuta gerada e atualiza status da analise.
- **`TriggerSecondInstanceJudgmentDraftGenerationUseCase`**
  (`src/animus/core/intake/use_cases/trigger_second_instance_judgment_draft_generation_use_case.py`) -
  valida pre-condicoes e publica o evento de geracao.
- **`AnalysisNotFoundError`**, **`SecondInstanceJudgmentDraftUnavailableError`**,
  **`ForbiddenError`** e **`SecondInstanceAnalysisRequiredError`**
  (`src/animus/core/intake/domain/errors/` e
  `src/animus/core/shared/domain/errors/`) - erros de dominio ja usados para
  existencia, draft indisponivel, ownership e tipo incoerente.

## Database

- **`SecondInstanceJudgmentDraftModel`**
  (`src/animus/database/sqlalchemy/models/intake/judgment_draft_model.py`) -
  model da tabela `second_instance_judgment_drafts`, com FK cascade para
  `analyses.id`.
- **`SecondInstanceJudgmentDraftMapper`**
  (`src/animus/database/sqlalchemy/mappers/intake/judgment_draft_mapper.py`) -
  traduz entre model SQLAlchemy e estrutura de dominio.
- **`SqlalchemySecondInstanceJudgmentDraftsRepository`**
  (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`) -
  implementa o port de leitura, inclusao e substituicao sem controlar commit.
- **`DatabasePipe.get_judgment_drafts_repository_from_request`**
  (`src/animus/pipes/database_pipe.py`) - fornece o repositorio concreto por
  `Depends(...)`.

## REST

- **`GetSecondInstanceJudgmentDraftController`**
  (`src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`) -
  controller existente, mas atualmente exposto em
  `/analyses/{analysis_id}/second-instance-judgment-drafts` e usando
  `IntakePipe.verify_analysis_by_account_from_request`.
- **`TriggerSecondInstanceJudgmentDraftGenerationController`**
  (`src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_generation_controller.py`) -
  controller de trigger assincrono que deve permanecer fora desta mudanca.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) -
  handler global que hoje mapeia `ConflictError` para `409`,
  `NotFoundError` para `404`, `ValidationError` para `400`, `AuthError` para
  `401`, `ForbiddenError` para `403` e `AppError` generico para `400`.

## Routers

- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) -
  registra `GetSecondInstanceJudgmentDraftController` junto dos demais
  controllers de intake.

## PubSub

- **`GenerateSecondInstanceJudgmentDraftJob`**
  (`src/animus/pubsub/inngest/jobs/intake/generate_judgment_draft_job.py`) -
  consome o evento de geracao, executa o workflow de IA e persiste o draft via
  `CreateSecondInstanceJudgmentDraftUseCase`.

---

# 5. O que deve ser criado?

- **Nao aplicavel.** O endpoint deve reaproveitar os DTOs, ports, repositorios
  e erros de dominio existentes.

---

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/use_cases/get_second_instance_judgment_draft_use_case.py`
- **Mudanca:** alterar o construtor para receber
  `analyses_repository: AnalysesRepository` e
  `judgment_drafts_repository: SecondInstanceJudgmentDraftsRepository`.
- **Metodo principal:** `execute(analysis_id: str, account_id: str) -> SecondInstanceJudgmentDraftDto`
  - valida analise, ownership e tipo; busca o draft persistido; retorna o DTO
  estruturado.
- **Fluxo resumido:**
  1. Criar `Id` para `analysis_id` e `account_id`.
  2. Buscar `Analysis` via `AnalysesRepository.find_by_id(...)`.
  3. Levantar `AnalysisNotFoundError` se nao existir.
  4. Comparar `analysis.account_id` com `account_id`; levantar
     `ForbiddenError` se divergir.
  5. Validar `analysis.type == AnalysisType.create_as_second_instance()`;
     levantar `SecondInstanceAnalysisRequiredError` se divergir.
  6. Buscar draft via `SecondInstanceJudgmentDraftsRepository.find_by_analysis_id(...)`.
  7. Levantar `SecondInstanceJudgmentDraftUnavailableError` se nao existir.
  8. Retornar `judgment_draft.dto`.
- **Justificativa:** o Jira define `GetJudgmentDraftUseCase.execute(analysis_id, account_id)`;
  manter essas decisoes no `core` evita espalhar regra de dominio no pipe.

## REST

- **Arquivo:** `src/animus/rest/handlers/app_error_handler.py`
- **Mudanca:** **Nao aplicavel.**
- **Justificativa:** `SecondInstanceJudgmentDraftUnavailableError` herda de
  `NotFoundError`, e o handler global ja traduz `NotFoundError` para `404`.

- **Arquivo:** `src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`
- **Mudanca:** alterar a rota para
  `GET /analyses/{analysis_id}/petition-drafts`, manter `status_code=200` e
  `response_model=SecondInstanceJudgmentDraftDto`.
- **Dependencias via `Depends`:**
  - `account_id: Annotated[Id, Depends(AuthPipe.get_account_id_from_request)]`
  - `analyses_repository: Annotated[AnalysesRepository, Depends(DatabasePipe.get_analyses_repository_from_request)]`
  - `judgment_drafts_repository: Annotated[SecondInstanceJudgmentDraftsRepository, Depends(DatabasePipe.get_judgment_drafts_repository_from_request)]`
- **Fluxo:** path param `analysis_id` + `account_id.value` ->
  `GetSecondInstanceJudgmentDraftUseCase.execute(...)` -> DTO.
- **Justificativa:** alinhar URL ao contrato correto informado para `ANI-114`;
  a rota `GET /intake/analyses/{analysis_id}/judgment-draft` descrita no ticket
  esta incorreta. O controller permanece fino e nao replica ownership/type
  checks.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudanca:** manter o registro de `GetSecondInstanceJudgmentDraftController`.
  Ajustar apenas se a ordem de imports/registro ficar inconsistente apos as
  alteracoes no controller.
- **Justificativa:** a composicao ja esta no router correto; nao ha necessidade
  de novo sub-router.

## Database

- **Nao aplicavel.** A tabela, mapper, repositorio e pipe do draft ja existem e
  atendem a leitura por `analysis_id`.

## PubSub

- **Nao aplicavel.** O job de geracao e o trigger assincrono permanecem fora do
  escopo deste endpoint de leitura.

---

# 7. O que deve ser removido?

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`
- **Motivo da remocao:** a exposicao GET em
  `/analyses/{analysis_id}/second-instance-judgment-drafts` diverge do contrato
  corrigido desta spec.
- **Impacto esperado:** apenas o GET deve mudar para `/petition-drafts`; o POST
  de trigger em `/second-instance-judgment-drafts` deve continuar existindo.

---

# 8. Decisoes Tecnicas e Trade-offs

- **Decisao:** retornar `SecondInstanceJudgmentDraftDto` estruturado em vez de
  criar um DTO `{ content: str }`.
- **Alternativas consideradas:** seguir literalmente o trecho simplificado do
  Jira (`JudgmentDraftDto { content: str }`) ou transformar as secoes
  persistidas em uma string unica.
- **Motivo da escolha:** o PRD RF 08 exige minuta estruturada em secoes
  obrigatorias, e a codebase ja persiste essas secoes em
  `SecondInstanceJudgmentDraftDto`.
- **Impactos / trade-offs:** o ticket deve ser atualizado se o cliente ainda
  estiver esperando `content`; a API fica mais fiel ao dominio atual.

- **Decisao:** validar existencia, ownership e tipo no `UseCase`.
- **Alternativas consideradas:** continuar usando
  `IntakePipe.verify_analysis_by_account_from_request` no controller.
- **Motivo da escolha:** o Jira define assinatura com `account_id` no use case e
  o fluxo de dominio fica testavel sem FastAPI.
- **Impactos / trade-offs:** o controller injeta um repositorio a mais, mas
  remove regra de autorizacao da borda para este endpoint.

- **Decisao:** usar `GET /intake/analyses/{analysis_id}/petition-drafts` como
  rota de leitura, apesar de o ticket citar
  `GET /intake/analyses/{analysis_id}/judgment-draft`.
- **Alternativas consideradas:** seguir a rota escrita no Jira ou manter o GET
  atual em `/second-instance-judgment-drafts`.
- **Motivo da escolha:** a rota correta foi explicitamente informada durante a
  atualizacao da spec.
- **Impactos / trade-offs:** a spec passa a contradizer o texto atual do ticket
  neste ponto; essa divergencia fica registrada para evitar implementacao na URL
  errada.

- **Decisao:** reutilizar `SecondInstanceJudgmentDraftUnavailableError` para
  draft ainda nao gerado, mantendo retorno `404`.
- **Alternativas consideradas:** criar um erro especifico novo para draft ainda
  nao gerado.
- **Motivo da escolha:** a API deve manter o comportamento de recurso
  indisponivel como `NotFoundError`, alinhado ao tratamento atual dos demais
  artefatos derivados em intake.
- **Impactos / trade-offs:** evita criar novo tipo de erro e novo mapeamento
  global sem necessidade.

- **Decisao:** nao alterar database, migrations ou job.
- **Alternativas consideradas:** remodelar a tabela para um `content` unico.
- **Motivo da escolha:** `ANI-92` e `ANI-94` ja prepararam persistencia e
  geracao estruturadas.
- **Impactos / trade-offs:** a entrega fica focada na superficie de leitura.

---

# 9. Diagramas e Referencias

- **Fluxo de dados:**

```text
GET /intake/analyses/{analysis_id}/petition-drafts
  -> AnalysesRouter
  -> GetSecondInstanceJudgmentDraftController
  -> AuthPipe.get_account_id_from_request()
  -> DatabasePipe.get_analyses_repository_from_request()
  -> DatabasePipe.get_judgment_drafts_repository_from_request()
  -> GetSecondInstanceJudgmentDraftUseCase.execute(analysis_id, account_id)
      -> AnalysesRepository.find_by_id(Id)
          -> None: AnalysisNotFoundError -> 404
          -> account mismatch: ForbiddenError -> 403
          -> not SECOND_INSTANCE: SecondInstanceAnalysisRequiredError -> 409
      -> SecondInstanceJudgmentDraftsRepository.find_by_analysis_id(Id)
          -> None: SecondInstanceJudgmentDraftUnavailableError -> 404
      -> SecondInstanceJudgmentDraft.dto
  -> 200 SecondInstanceJudgmentDraftDto
```

- **Fluxo assincrono relacionado (fora do escopo da mudanca):**

```text
POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts
  -> TriggerSecondInstanceJudgmentDraftGenerationUseCase
  -> SecondInstanceJudgmentDraftGenerationTriggeredEvent
  -> GenerateSecondInstanceJudgmentDraftJob
  -> CreateSecondInstanceJudgmentDraftUseCase
  -> second_instance_judgment_drafts
```

- **Referencias:**
  - `src/animus/core/intake/use_cases/get_second_instance_judgment_draft_use_case.py`
  - `src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`
  - `src/animus/rest/controllers/intake/get_second_instance_analysis_report_controller.py`
  - `src/animus/core/intake/interfaces/judgment_drafts_repository.py`
  - `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`
  - `src/animus/rest/handlers/app_error_handler.py`
  - `src/animus/routers/intake/analyses_router.py`
  - PRD RF 08 no Confluence:
    `https://joaogoliveiragarcia.atlassian.net/wiki/x/AQDxAg`

---

# 10. Pendencias / Duvidas

- **Descricao da pendencia:** o Jira cita `JudgmentDraftDto { content: str }`,
  mas o PRD RF 08 e a codebase atual usam `SecondInstanceJudgmentDraftDto`
  estruturado.
- **Impacto na implementacao:** se o app mobile ja estiver integrado ao campo
  `content`, sera necessario alinhar contrato antes do merge.
- **Acao sugerida:** atualizar o ticket `ANI-114` para explicitar o contrato
  estruturado ou confirmar com produto que o endpoint deve retornar uma string
  consolidada.

- **Descricao da pendencia:** o Jira cita a rota
  `GET /intake/analyses/{analysis_id}/judgment-draft`, mas a rota correta
  informada para implementacao e
  `GET /intake/analyses/{analysis_id}/petition-drafts`.
- **Impacto na implementacao:** seguir o ticket literalmente levaria a API a
  expor uma URL incorreta.
- **Acao sugerida:** atualizar o ticket `ANI-114` para substituir a rota
  incorreta pela rota definida nesta spec.

- **Descricao da pendencia:** o ticket tambem cita retorno `422` quando a
  minuta ainda nao foi gerada, mas o comportamento definido nesta spec e manter
  `404`.
- **Impacto na implementacao:** seguir o ticket literalmente mudaria o contrato
  de erro atual dos artefatos indisponiveis.
- **Acao sugerida:** atualizar o ticket `ANI-114` para refletir `404` em draft
  ainda nao gerado.

- **Descricao da pendencia:** o Jira nao explicita o comportamento quando
  `analysis_id` pertence ao usuario, mas a analise nao e de segunda instancia.
- **Impacto na implementacao:** a spec assume `409` via
  `SecondInstanceAnalysisRequiredError`, por consistencia com o trigger de
  geracao.
- **Acao sugerida:** validar se produto prefere `404` para esconder analises de
  tipo incorreto ou manter o erro de conflito do dominio.

---

## Restricoes

- **Nao inclua testes automatizados na spec.**
- O `core` nao deve depender de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest` ou
  qualquer detalhe de infraestrutura.
- Todos os caminhos citados existem no projeto ou estao explicitamente marcados
  como **novo arquivo**.
- O endpoint de leitura nao deve iniciar geracao, regeracao ou exportacao de
  PDF.
- O `POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts`
  permanece como trigger assincrono e nao deve ser removido nesta entrega.
- Schemas `*Body` de entrada nao se aplicam porque o endpoint e `GET`.
- Nao criar schema em `validation/` para esta resposta; usar o DTO do `core`
  como `response_model`, seguindo o padrao existente nos controllers de
  relatorio.
