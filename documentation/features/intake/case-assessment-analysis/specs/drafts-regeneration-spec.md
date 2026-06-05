---
title: Regeração assíncrona de minutas com comentários do usuário
prd: https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/49053697, https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/49348609
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-126
status: closed
last_updated_at: 2026-05-30
---

# 1. Objetivo

Implementar dois endpoints assíncronos de regeração dirigida por comentários do usuário para minutas já persistidas: `POST /intake/analyses/{analysis_id}/petition-drafts/regenerate` para minuta de petição inicial de `CASE_ASSESSMENT` e `POST /intake/analyses/{analysis_id}/judgment-drafts/regenerate` para minuta de sentença de `SECOND_INSTANCE`. Cada fluxo deve validar ownership e pré-condições, persistir imediatamente o status de geração correspondente na análise, publicar evento de domínio dedicado, executar job Inngest que usa a minuta atual, `CaseSummary`, precedentes escolhidos e comentários como contexto de revisão, persistir a versão revisada via use case existente de criação/substituição e atualizar status da análise para `DONE` em sucesso ou `FAILED` em falha não recuperável.

# 2. Escopo

## 2.1 In-scope

- Criar endpoints HTTP assíncronos de regeração para minutas de petição e sentença.
- Receber `comments: str` no body do controller como orientação textual do usuário.
- Criar use cases de trigger para validar pré-condições e publicar eventos dedicados.
- Criar eventos de domínio com `analysis_id` e `comments`.
- Criar workflows de IA especializados em revisão dirigida por comentários, reutilizando os outputs estruturados existentes.
- Criar agents revisores em `IntakeSquad` para petição e sentença.
- Criar jobs Inngest com `retries=2`, steps explícitos, `on_failure` e marcação de status `FAILED`.
- Reutilizar `CreatePetitionDraftUseCase` e `CreateSecondInstanceJudgmentDraftUseCase` para substituir a minuta anterior e concluir a análise com `DONE`.
- Registrar controllers, events, interfaces, use cases, workflows e jobs nos `__init__.py` e composition roots correspondentes.
- Introduzir contrato HTTP `422 Unprocessable Entity` para pré-condições de regeração sem alterar o significado dos erros existentes de leitura de minuta.

## 2.2 Out-of-scope

- Novo upload, nova extração de documento, nova sumarização ou nova busca de precedentes.
- Suporte a múltiplas versões simultâneas de minuta por análise.
- Edição manual do conteúdo da minuta no app.
- Exportação PDF de petição ou sentença.
- Mudanças no schema das tabelas `petition_drafts` ou `judgment_drafts`.
- Alterações nos fluxos de geração inicial, exceto referências e reuso de componentes existentes.

# 3. Requisitos

## 3.1 Funcionais

- O endpoint de petição deve ser `POST /intake/analyses/{analysis_id}/petition-drafts/regenerate`.
- O endpoint de sentença deve ser `POST /intake/analyses/{analysis_id}/judgment-drafts/regenerate`.
- Ambos os endpoints devem responder `202 Accepted` sem body quando o evento for publicado com sucesso.
- Ambos os endpoints devem exigir autenticação e ownership via `IntakePipe.verify_analysis_by_account_from_request`.
- O body de ambos os endpoints deve conter `comments: str` obrigatório, com texto não vazio após trim.
- A regeração de petição deve exigir análise `CASE_ASSESSMENT`.
- A regeração de sentença deve exigir análise `SECOND_INSTANCE`.
- Se `analysis_id` não existir, deve preservar o comportamento global de `AnalysisNotFoundError`.
- Se a análise não pertencer à conta autenticada, deve preservar o comportamento global de autorização do `IntakePipe`.
- Se a análise não possuir minuta atual persistida, o endpoint deve falhar com erro de domínio mapeado para `422`.
- Se a análise não possuir precedentes persistidos ou nenhum precedente escolhido, o endpoint deve falhar com erro de domínio mapeado para `422`.
- O trigger deve publicar exatamente um evento dedicado contendo `analysis_id` e `comments`.
- Ao aceitar a solicitação, o trigger de petição deve atualizar a análise para `GENERATING_PETITION_DRAFT` antes de publicar o evento.
- Ao aceitar a solicitação, o trigger de sentença deve atualizar a análise para `GENERATING_JUDGMENT_DRAFT` antes de publicar o evento.
- O job de petição deve carregar a `PetitionDraft` atual, `CaseSummary`, precedentes escolhidos e comentários antes de chamar o workflow.
- O job de sentença deve carregar a `SecondInstanceJudgmentDraft` atual, `CaseSummary`, precedentes escolhidos e comentários antes de chamar o workflow.
- O workflow de petição deve revisar a minuta atual preservando o que não foi pedido para alterar e retornar `PetitionDraftDto` com `structured_facts`, `legal_grounds`, `central_thesis`, `requests` e `precedent_citations`.
- O workflow de sentença deve revisar a minuta atual preservando o que não foi pedido para alterar e retornar `SecondInstanceJudgmentDraftDto` com `report`, `merit_analysis`, `precedent_adherence_analysis`, `ruling`, `preliminary_issues` e `no_applicable_precedent_notice`.
- Em sucesso, o job de petição deve publicar `PetitionDraftGenerationFinishedEvent` com `analysis_id`, `account_id` e `analysis_type`.
- Em sucesso, o job de sentença deve publicar `SecondInstanceJudgmentDraftGenerationFinishedEvent` com `analysis_id`, `account_id` e `analysis_type`.
- Em falha não recuperável, ambos os jobs devem atualizar a análise para `FAILED` no `except` interno e reforçar a marcação no `on_failure`.

## 3.2 Não funcionais

- **Segurança:** os endpoints devem reutilizar `IntakePipe.verify_analysis_by_account_from_request`; nenhum job deve inferir autorização por dados do payload.
- **Idempotência:** reexecuções dos jobs devem substituir a minuta existente via `replace(...)`, usando os use cases de criação existentes; não deve haver criação de múltiplas minutas para a mesma análise.
- **Assincronicidade:** endpoints devem apenas validar e publicar evento; processamento pesado deve ficar no Inngest.
- **Resiliência:** jobs devem usar `retries=2`, `except` interno com marcação `FAILED` e `on_failure` idempotente.
- **Observabilidade por estado persistido:** o app deve continuar acompanhando a evolução por `GET /intake/analyses/{analysis_id}/status`.
- **Compatibilidade retroativa:** não deve haver alteração no contrato dos endpoints de geração inicial nem nos DTOs persistidos existentes.
- **Timeout de IA:** agents revisores devem usar `timeout=60`, alinhado aos agents de geração existentes.

# 4. O que já existe?

## Core

- **`PetitionDraft`** (`src/animus/core/intake/domain/structures/petition_draft.py`) — structure da minuta de petição já persistida e usada como base da revisão.
- **`SecondInstanceJudgmentDraft`** (`src/animus/core/intake/domain/structures/second_instance_judgment_draft.py`) — structure da minuta de sentença já persistida e usada como base da revisão.
- **`PetitionDraftDto`** (`src/animus/core/intake/domain/structures/dtos/petition_draft_dto.py`) — DTO estruturado retornado pelo workflow de petição.
- **`SecondInstanceJudgmentDraftDto`** (`src/animus/core/intake/domain/structures/dtos/second_instance_judgment_draft_dto.py`) — DTO estruturado retornado pelo workflow de sentença.
- **`CaseSummary`** (`src/animus/core/intake/domain/structures/case_summary.py`) — contexto imutável do caso usado nos prompts de revisão.
- **`AnalysisPrecedent`** (`src/animus/core/intake/domain/structures/analysis_precedent.py`) — precedentes classificados; a regeração deve usar apenas itens com `is_chosen.is_true`.
- **`CaseAssessmentAnalysisStatus`** (`src/animus/core/intake/domain/structures/case_assessment_analysis_status.py`) — contém `GENERATING_PETITION_DRAFT`, `DONE` e `FAILED` para petição.
- **`SecondInstanceAnalysisStatus`** (`src/animus/core/intake/domain/structures/second_instance_analysis_status.py`) — contém `GENERATING_JUDGMENT_DRAFT`, `DONE` e `FAILED` para sentença.
- **`PetitionDraftsRepository`** (`src/animus/core/intake/interfaces/petition_drafts_repository.py`) — port com `find_by_analysis_id(...)`, `add(...)` e `replace(...)`.
- **`SecondInstanceJudgmentDraftsRepository`** (`src/animus/core/intake/interfaces/judgment_drafts_repository.py`) — port com `find_by_analysis_id(...)`, `add(...)` e `replace(...)`.
- **`CaseSummariesRepository`** (`src/animus/core/intake/interfaces/case_summaries_repository.py`) — port usado para buscar o resumo do caso por análise.
- **`AnalysisPrecedentsRepository`** (`src/animus/core/intake/interfaces/analysis_precedents_repository.py`) — port usado para listar precedentes da análise.
- **`AnalysesRepository`** (`src/animus/core/intake/interfaces/analyses_repository.py`) — port usado para buscar, validar tipo e substituir status da análise.
- **`GeneratePetitionDraftWorkflow`** (`src/animus/core/intake/interfaces/generate_petition_draft_workflow.py`) — interface de geração inicial; serve como referência de assinatura e isolamento do `core`.
- **`GenerateSecondInstanceJudgmentDraftWorkflow`** (`src/animus/core/intake/interfaces/generate_judgment_draft_workflow.py`) — interface de geração inicial de sentença; serve como referência análoga.
- **`TriggerPetitionDraftGenerationUseCase`** (`src/animus/core/intake/use_cases/trigger_petition_draft_generation_use_case.py`) — referência de trigger assíncrono para `CASE_ASSESSMENT`.
- **`TriggerSecondInstanceJudgmentDraftGenerationUseCase`** (`src/animus/core/intake/use_cases/trigger_second_instance_judgment_draft_generation_use_case.py`) — referência de trigger assíncrono para `SECOND_INSTANCE`.
- **`CreatePetitionDraftUseCase`** (`src/animus/core/intake/use_cases/create_petition_draft_use_case.py`) — cria ou substitui `PetitionDraft` e conclui status `DONE`.
- **`CreateSecondInstanceJudgmentDraftUseCase`** (`src/animus/core/intake/use_cases/create_judgment_draft_use_case.py`) — cria ou substitui `SecondInstanceJudgmentDraft` e conclui status `DONE`.
- **`PetitionDraftGenerationFinishedEvent`** (`src/animus/core/intake/domain/events/petition_draft_generation_finished_event.py`) — evento já consumido por notificação de conclusão de petição.
- **`SecondInstanceJudgmentDraftGenerationFinishedEvent`** (`src/animus/core/intake/domain/events/second_instance_judgment_draft_generation_finished_event.py`) — evento já consumido por notificação de conclusão de sentença.
- **`AppError`** (`src/animus/core/shared/domain/errors/app_error.py`) — classe base de erro de aplicação usada pelos handlers globais; os novos erros de domínio de regeração devem herdar dela indiretamente ou diretamente.

## REST

- **`TriggerPetitionDraftGenerationController`** (`src/animus/rest/controllers/intake/trigger_petition_draft_generation_controller.py`) — referência de controller de trigger assíncrono para petição.
- **`TriggerSecondInstanceJudgmentDraftGenerationController`** (`src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_generation_controller.py`) — referência de controller de trigger assíncrono para sentença.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) — handler global que deve receber novo mapeamento para `422`.

## Routers

- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) — registra controllers de `intake` relacionados a análises.

## Pipes

- **`DatabasePipe.get_petition_drafts_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP para `PetitionDraftsRepository`.
- **`DatabasePipe.get_judgment_drafts_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP para `SecondInstanceJudgmentDraftsRepository`.
- **`DatabasePipe.get_case_summaries_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP para `CaseSummariesRepository`.
- **`DatabasePipe.get_analysis_precedents_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP para `AnalysisPrecedentsRepository`.
- **`DatabasePipe.get_analyses_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP para `AnalysesRepository`.
- **`AiPipe.get_generate_petition_draft_workflow()`** (`src/animus/pipes/ai_pipe.py`) — factory estática para o workflow de geração inicial de petição.
- **`AiPipe.get_generate_judgment_draft_workflow()`** (`src/animus/pipes/ai_pipe.py`) — factory estática para o workflow de geração inicial de sentença.
- **`PubSubPipe.get_broker_from_request(...)`** (`src/animus/pipes/pubsub_pipe.py`) — provider do `Broker` usado pelos triggers HTTP.

## AI

- **`PetitionDraftOutput`** (`src/animus/ai/agno/outputs/intake/petition_draft_output.py`) — output estruturado reutilizável para petição.
- **`SecondInstanceJudgmentDraftOutput`** (`src/animus/ai/agno/outputs/intake/second_instance_judgment_draft_output.py`) — output estruturado reutilizável para sentença.
- **`AgnoGeneratePetitionDraftWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_generate_petition_draft_workflow.py`) — referência para `_StepNames`, `session_state`, prompt e normalização robusta de output.
- **`AgnoGenerateSecondInstanceJudgmentDraftWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_generate_second_instance_judgment_draft_workflow.py`) — referência para workflow de sentença.
- **`IntakeSquad.petition_draft_generator_agent`** (`src/animus/ai/agno/squads/intake_squad.py`) — agent de geração inicial de petição.
- **`IntakeSquad.second_instance_judgment_draft_generator_agent`** (`src/animus/ai/agno/squads/intake_squad.py`) — agent de geração inicial de sentença.

## PubSub

- **`GeneratePetitionDraftJob`** (`src/animus/pubsub/inngest/jobs/intake/generate_petition_draft_job.py`) — referência principal de job Inngest para petição.
- **`GenerateSecondInstanceJudgmentDraftJob`** (`src/animus/pubsub/inngest/jobs/intake/generate_second_instance_judgment_draft_job.py`) — referência principal de job Inngest para sentença.
- **`InngestPubSub.register_intake_jobs(...)`** (`src/animus/pubsub/inngest/inngest_pubsub.py`) — composition root para registro dos novos jobs.
- **Seeders da camada database:** existem `src/animus/database/sqlalchemy/seeders/intake_seeder.py`, `auth_seeder.py` e `storage_seeder.py`, mas a feature não requer novos dados de seed nem novos paths persistidos/gerados.

# 5. O que deve ser criado?

## Camada Core (Erros de Domínio)

- **Localização:** `src/animus/core/intake/domain/errors/draft_regeneration_precondition_error.py` (**novo arquivo**)
- **Classe base:** `AppError`
- **Motivo:** erro base de domínio para pré-condições específicas de regeração de minutas no contexto `intake`, mapeado para `422` pelo `AppErrorHandler`.

- **Localização:** `src/animus/core/intake/domain/errors/petition_draft_regeneration_unavailable_error.py` (**novo arquivo**)
- **Classe base:** `DraftRegenerationPreconditionError`
- **Motivo:** levantado quando uma análise `CASE_ASSESSMENT` não possui `PetitionDraft` persistida para revisar.

- **Localização:** `src/animus/core/intake/domain/errors/judgment_draft_regeneration_unavailable_error.py` (**novo arquivo**)
- **Classe base:** `DraftRegenerationPreconditionError`
- **Motivo:** levantado quando uma análise `SECOND_INSTANCE` não possui `SecondInstanceJudgmentDraft` persistida para revisar.

- **Localização:** `src/animus/core/intake/domain/errors/draft_regeneration_chosen_precedents_required_error.py` (**novo arquivo**)
- **Classe base:** `DraftRegenerationPreconditionError`
- **Motivo:** levantado quando não há precedentes persistidos ou nenhum precedente escolhido para a regeração.

- **Localização:** `src/animus/core/intake/domain/errors/draft_regeneration_case_summary_unavailable_error.py` (**novo arquivo**)
- **Classe base:** `DraftRegenerationPreconditionError`
- **Motivo:** levantado quando o contexto de `CaseSummary` necessário ao workflow de revisão não está persistido.

- **Localização:** `src/animus/core/intake/domain/errors/draft_regeneration_comments_required_error.py` (**novo arquivo**)
- **Classe base:** `DraftRegenerationPreconditionError`
- **Motivo:** levantado quando `comments` vier vazio após normalização.

## Camada Core (Eventos de Domínio)

- **Localização:** `src/animus/core/intake/domain/events/petition_draft_regeneration_triggered_event.py` (**novo arquivo**)
- **`name`:** `"intake/petition_draft.regeneration.triggered"`
- **Payload:** `analysis_id: str`, `comments: str`
- **Métodos / factory:** `__init__(analysis_id: str, comments: str) -> None` — cria evento de domínio para iniciar a revisão assíncrona da minuta de petição.

- **Localização:** `src/animus/core/intake/domain/events/second_instance_judgment_draft_regeneration_triggered_event.py` (**novo arquivo**)
- **`name`:** `"intake/judgment_draft.regeneration.triggered"`
- **Payload:** `analysis_id: str`, `comments: str`
- **Métodos / factory:** `__init__(analysis_id: str, comments: str) -> None` — cria evento de domínio para iniciar a revisão assíncrona da minuta de sentença.

## Camada Core (Interfaces / Ports)

- **Localização:** `src/animus/core/intake/interfaces/regenerate_petition_draft_workflow.py` (**novo arquivo**)
- **Métodos:**
  - `run(analysis_id: str, current_draft: PetitionDraft, case_summary: CaseSummary, precedents: list[AnalysisPrecedent], comments: str) -> PetitionDraftDto` — revisa a minuta de petição atual com base em comentários, preservando contrato de saída estruturado.

- **Localização:** `src/animus/core/intake/interfaces/regenerate_judgment_draft_workflow.py` (**novo arquivo**)
- **Métodos:**
  - `run(analysis_id: str, current_draft: SecondInstanceJudgmentDraft, case_summary: CaseSummary, precedents: list[AnalysisPrecedent], comments: str) -> SecondInstanceJudgmentDraftDto` — revisa a minuta de sentença atual com base em comentários, preservando contrato de saída estruturado.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/trigger_petition_draft_regeneration_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `AnalysesRepository`, `PetitionDraftsRepository`, `CaseSummariesRepository`, `AnalysisPrecedentsRepository`, `Broker`
- **Método principal:** `execute(analysis_id: str, comments: str) -> None` — valida pré-condições da regeração de petição e publica `PetitionDraftRegenerationTriggeredEvent`.
- **Fluxo resumido:**
  - Normaliza `analysis_id` como `Id`.
  - Normaliza `comments` com trim; se vazio, lança `DraftRegenerationCommentsRequiredError`.
  - Busca `Analysis`; se ausente, lança `AnalysisNotFoundError`.
  - Se `analysis.type.is_case_analysis.is_false`, lança `InconsistentAnalysisTypeError`.
  - Busca `PetitionDraft` por `analysis_id`; se ausente, lança `PetitionDraftRegenerationUnavailableError`.
  - Busca `CaseSummary`; se ausente, lança `DraftRegenerationCaseSummaryUnavailableError`.
  - Busca precedentes por `analysis_id`; se lista vazia ou sem `is_chosen.is_true`, lança `DraftRegenerationChosenPrecedentsRequiredError`.
  - Atualiza a `Analysis` para `GENERATING_PETITION_DRAFT` e persiste via `AnalysesRepository.replace(...)`.
  - Publica `PetitionDraftRegenerationTriggeredEvent(analysis_id=analysis_id_entity.value, comments=normalized_comments)` via `Broker.publish(...)`.

- **Localização:** `src/animus/core/intake/use_cases/trigger_second_instance_judgment_draft_regeneration_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `AnalysesRepository`, `SecondInstanceJudgmentDraftsRepository`, `CaseSummariesRepository`, `AnalysisPrecedentsRepository`, `Broker`
- **Método principal:** `execute(analysis_id: str, comments: str) -> None` — valida pré-condições da regeração de sentença e publica `SecondInstanceJudgmentDraftRegenerationTriggeredEvent`.
- **Fluxo resumido:**
  - Normaliza `analysis_id` como `Id`.
  - Normaliza `comments` com trim; se vazio, lança `DraftRegenerationCommentsRequiredError`.
  - Busca `Analysis`; se ausente, lança `AnalysisNotFoundError`.
  - Se `analysis.type.is_second_instance.is_false`, lança `SecondInstanceAnalysisRequiredError`.
  - Busca `SecondInstanceJudgmentDraft` por `analysis_id`; se ausente, lança `SecondInstanceJudgmentDraftRegenerationUnavailableError`.
  - Busca `CaseSummary`; se ausente, lança `DraftRegenerationCaseSummaryUnavailableError`.
  - Busca precedentes por `analysis_id`; se lista vazia ou sem `is_chosen.is_true`, lança `DraftRegenerationChosenPrecedentsRequiredError`.
  - Atualiza a `Analysis` para `GENERATING_JUDGMENT_DRAFT` e persiste via `AnalysesRepository.replace(...)`.
  - Publica `SecondInstanceJudgmentDraftRegenerationTriggeredEvent(analysis_id=analysis_id_entity.value, comments=normalized_comments)` via `Broker.publish(...)`.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/trigger_petition_draft_regeneration_controller.py` (**novo arquivo**)
- **`_Body`:** `comments: str` com validação Pydantic para string obrigatória e não vazia.
- **Método HTTP e path:** `POST /analyses/{analysis_id}/petition-drafts/regenerate`
- **`status_code`:** `202 Accepted`
- **`response_model`:** Não aplicável.
- **Dependências injetadas via `Depends`:** `IntakePipe.verify_analysis_by_account_from_request`, `DatabasePipe.get_analyses_repository_from_request`, `DatabasePipe.get_petition_drafts_repository_from_request`, `DatabasePipe.get_case_summaries_repository_from_request`, `DatabasePipe.get_analysis_precedents_repository_from_request`, `PubSubPipe.get_broker_from_request`
- **Fluxo:** `_Body.comments` via named param → `TriggerPetitionDraftRegenerationUseCase.execute(analysis_id=analysis.id.value, comments=body.comments)` → `Response(status_code=202)`.

- **Localização:** `src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_regeneration_controller.py` (**novo arquivo**)
- **`_Body`:** `comments: str` com validação Pydantic para string obrigatória e não vazia.
- **Método HTTP e path:** `POST /analyses/{analysis_id}/judgment-drafts/regenerate`
- **`status_code`:** `202 Accepted`
- **`response_model`:** Não aplicável.
- **Dependências injetadas via `Depends`:** `IntakePipe.verify_analysis_by_account_from_request`, `DatabasePipe.get_analyses_repository_from_request`, `DatabasePipe.get_judgment_drafts_repository_from_request`, `DatabasePipe.get_case_summaries_repository_from_request`, `DatabasePipe.get_analysis_precedents_repository_from_request`, `PubSubPipe.get_broker_from_request`
- **Fluxo:** `_Body.comments` via named param → `TriggerSecondInstanceJudgmentDraftRegenerationUseCase.execute(analysis_id=analysis.id.value, comments=body.comments)` → `Response(status_code=202)`.

## Camada Pipes

- **Localização:** `src/animus/pipes/ai_pipe.py`
- **Método `Depends`:** `get_regenerate_petition_draft_workflow() -> RegeneratePetitionDraftWorkflow` — factory estática sem `Depends`, para uso por job Inngest.
- **Sessão SQLAlchemy:** Não aplicável.

- **Localização:** `src/animus/pipes/ai_pipe.py`
- **Método `Depends`:** `get_regenerate_judgment_draft_workflow() -> RegenerateSecondInstanceJudgmentDraftWorkflow` — factory estática sem `Depends`, para uso por job Inngest.
- **Sessão SQLAlchemy:** Não aplicável.

## Camada AI (Workflows Agno)

- **Localização:** `src/animus/ai/agno/workflows/intake/agno_regenerate_petition_draft_workflow.py` (**novo arquivo**)
- **Interface implementada:** `RegeneratePetitionDraftWorkflow`
- **Dependências:** `IntakeSquad`; não acessa banco, `Session` ou HTTP.
- **Métodos:**
  - `__init__() -> None` — cria `IntakeSquad` e `_StepNames`.
  - `run(analysis_id: str, current_draft: PetitionDraft, case_summary: CaseSummary, precedents: list[AnalysisPrecedent], comments: str) -> PetitionDraftDto` — monta `agno.Workflow`, executa revisão e normaliza saída para DTO.
  - `_build_petition_draft_regeneration_input_step(_: StepInput, run_context: RunContext) -> StepOutput` — monta prompt com minuta atual, resumo, precedentes escolhidos e comentários.
  - `_normalize_petition_draft_output(output: object, analysis_id: str) -> PetitionDraftDto` — reutiliza a estratégia robusta de coerção do workflow de geração existente.

- **Localização:** `src/animus/ai/agno/workflows/intake/agno_regenerate_second_instance_judgment_draft_workflow.py` (**novo arquivo**)
- **Interface implementada:** `RegenerateSecondInstanceJudgmentDraftWorkflow`
- **Dependências:** `IntakeSquad`; não acessa banco, `Session` ou HTTP.
- **Métodos:**
  - `__init__() -> None` — cria `IntakeSquad` e `_StepNames`.
  - `run(analysis_id: str, current_draft: SecondInstanceJudgmentDraft, case_summary: CaseSummary, precedents: list[AnalysisPrecedent], comments: str) -> SecondInstanceJudgmentDraftDto` — monta `agno.Workflow`, executa revisão e normaliza saída para DTO.
  - `_build_judgment_draft_regeneration_input_step(_: StepInput, run_context: RunContext) -> StepOutput` — monta prompt com minuta atual, resumo, precedentes escolhidos e comentários.
  - `_normalize_judgment_draft_output(output: object, analysis_id: str) -> SecondInstanceJudgmentDraftDto` — valida `SecondInstanceJudgmentDraftOutput` e preenche DTO.

## Camada AI (Squad)

- **Localização:** `src/animus/ai/agno/squads/intake_squad.py`
- **Métodos:**
  - `petition_draft_reviser_agent(self) -> Agent` — agent especializado em revisar minuta de petição existente a partir de comentários, com `OpenAIChat`, `temperature=0`, `timeout=60` e `output_schema=PetitionDraftOutput`.
  - `second_instance_judgment_draft_reviser_agent(self) -> Agent` — agent especializado em revisar minuta de sentença existente a partir de comentários, com `OpenAIChat`, `temperature=0`, `timeout=60` e `output_schema=SecondInstanceJudgmentDraftOutput`.

## Camada PubSub (Jobs Inngest)

- **Localização:** `src/animus/pubsub/inngest/jobs/intake/regenerate_petition_draft_job.py` (**novo arquivo**)
- **Evento consumido:** `PetitionDraftRegenerationTriggeredEvent.name`
- **Dependências:** `SqlalchemyAnalysesRepository`, `SqlalchemyPetitionDraftsRepository`, `SqlalchemyCaseSummariesRepository`, `SqlalchemyAnalysisPrecedentsRepository`, `AiPipe.get_regenerate_petition_draft_workflow()`, `CreatePetitionDraftUseCase`, `UpdateAnalysisStatusUseCase`, `InngestBroker`
- **Passos (`step.run`):**
  - `normalize_payload` — normaliza `analysis_id` e `comments`.
  - `mark_analysis_as_regenerating_petition_draft` — reforça de forma idempotente `CaseAssessmentAnalysisStatus.create_as_generating_petition_draft()` e executa `session.commit()`.
  - `regenerate_and_persist_petition_draft` — busca minuta atual, `CaseSummary`, precedentes escolhidos e análise; executa workflow; persiste via `CreatePetitionDraftUseCase`; executa `session.commit()`; retorna `{ analysis_id, account_id, analysis_type }`.
  - `publish_finished_event` — publica `PetitionDraftGenerationFinishedEvent`.
  - `mark_analysis_as_failed` — em exceção, aplica `CaseAssessmentAnalysisStatus.create_as_failed()` e executa `session.commit()`.
- **Métodos internos:**
  - `handle(inngest: Inngest) -> Any` — registra função com `fn_id='regenerate-petition-draft'`, trigger dedicado, `retries=2` e `on_failure=RegeneratePetitionDraftJob._handle_failure`.
  - `_normalize_payload(data: dict[str, Any]) -> dict[str, str]` — retorna `analysis_id` e `comments` normalizados.
  - `_mark_analysis_as_regenerating_petition_draft(payload: _Payload) -> None` — delega marcação de status para executor síncrono.
  - `_regenerate_and_persist_petition_draft(payload: _Payload) -> dict[str, str]` — delega execução de IA e persistência para executor síncrono.
  - `_mark_analysis_as_failed(payload: _Payload) -> None` — delega marcação de falha para executor síncrono.
  - `_handle_failure(context: Context) -> None` — extrai payload original e reforça `FAILED`.
- **Idempotência:** `CreatePetitionDraftUseCase.execute(...)` substitui a minuta existente via `replace(...)`.

- **Localização:** `src/animus/pubsub/inngest/jobs/intake/regenerate_second_instance_judgment_draft_job.py` (**novo arquivo**)
- **Evento consumido:** `SecondInstanceJudgmentDraftRegenerationTriggeredEvent.name`
- **Dependências:** `SqlalchemyAnalysesRepository`, `SqlalchemySecondInstanceJudgmentDraftsRepository`, `SqlalchemyCaseSummariesRepository`, `SqlalchemyAnalysisPrecedentsRepository`, `AiPipe.get_regenerate_judgment_draft_workflow()`, `CreateSecondInstanceJudgmentDraftUseCase`, `UpdateAnalysisStatusUseCase`, `InngestBroker`
- **Passos (`step.run`):**
  - `normalize_payload` — normaliza `analysis_id` e `comments`.
  - `mark_analysis_as_regenerating_judgment_draft` — reforça de forma idempotente `SecondInstanceAnalysisStatus.create_as_generating_judgment_draft()` e executa `session.commit()`.
  - `regenerate_and_persist_judgment_draft` — busca minuta atual, `CaseSummary`, precedentes escolhidos e análise; executa workflow; persiste via `CreateSecondInstanceJudgmentDraftUseCase`; executa `session.commit()`; retorna `{ analysis_id, account_id, analysis_type }`.
  - `publish_finished_event` — publica `SecondInstanceJudgmentDraftGenerationFinishedEvent`.
  - `mark_analysis_as_failed` — em exceção, aplica `SecondInstanceAnalysisStatus.create_as_failed()` e executa `session.commit()`.
- **Métodos internos:**
  - `handle(inngest: Inngest) -> Any` — registra função com `fn_id='regenerate-second-instance-judgment-draft'`, trigger dedicado, `retries=2` e `on_failure=RegenerateSecondInstanceJudgmentDraftJob._handle_failure`.
  - `_normalize_payload(data: dict[str, Any]) -> dict[str, str]` — retorna `analysis_id` e `comments` normalizados.
  - `_mark_analysis_as_regenerating_judgment_draft(payload: _Payload) -> None` — delega marcação de status para executor síncrono.
  - `_regenerate_and_persist_judgment_draft(payload: _Payload) -> dict[str, str]` — delega execução de IA e persistência para executor síncrono.
  - `_mark_analysis_as_failed(payload: _Payload) -> None` — delega marcação de falha para executor síncrono.
  - `_handle_failure(context: Context) -> None` — extrai payload original e reforça `FAILED`.
- **Idempotência:** `CreateSecondInstanceJudgmentDraftUseCase.execute(...)` substitui a minuta existente via `replace(...)`.

## Migrações Alembic

Não aplicável.

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/errors/__init__.py`
- **Mudança:** exportar `DraftRegenerationPreconditionError` e os erros concretos de pré-condição de regeração.
- **Justificativa:** manter contratos públicos do contexto `intake` acessíveis a use cases, controllers e jobs.

- **Arquivo:** `src/animus/core/intake/domain/events/__init__.py`
- **Mudança:** exportar `PetitionDraftRegenerationTriggeredEvent` e `SecondInstanceJudgmentDraftRegenerationTriggeredEvent`.
- **Justificativa:** disponibilizar eventos para triggers e jobs.

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudança:** exportar `RegeneratePetitionDraftWorkflow` e `RegenerateSecondInstanceJudgmentDraftWorkflow`.
- **Justificativa:** manter contratos públicos de workflow disponíveis para `AiPipe` e jobs.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** exportar `TriggerPetitionDraftRegenerationUseCase` e `TriggerSecondInstanceJudgmentDraftRegenerationUseCase`.
- **Justificativa:** seguir padrão dos triggers existentes.

## REST

- **Arquivo:** `src/animus/rest/handlers/app_error_handler.py`
- **Mudança:** importar `DraftRegenerationPreconditionError`, criar `handle_draft_regeneration_precondition_error(...) -> JSONResponse` com status `422` e registrá-lo em `register(...)`.
- **Justificativa:** cumprir contrato explícito do ticket para pré-condições de regeração.

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** exportar `TriggerPetitionDraftRegenerationController` e `TriggerSecondInstanceJudgmentDraftRegenerationController`.
- **Justificativa:** tornar os novos controllers disponíveis ao router.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** importar e registrar `TriggerPetitionDraftRegenerationController.handle(router)` e `TriggerSecondInstanceJudgmentDraftRegenerationController.handle(router)`.
- **Justificativa:** expor os endpoints na superfície HTTP de análises.

## Pipes

- **Arquivo:** `src/animus/pipes/ai_pipe.py`
- **Mudança:** importar as novas interfaces e adicionar `get_regenerate_petition_draft_workflow()` e `get_regenerate_judgment_draft_workflow()` com import interno das implementações Agno.
- **Justificativa:** manter criação de workflows concretos centralizada no `AiPipe`, inclusive para jobs.

## AI

- **Arquivo:** `src/animus/ai/agno/squads/intake_squad.py`
- **Mudança:** adicionar properties `petition_draft_reviser_agent` e `second_instance_judgment_draft_reviser_agent`.
- **Justificativa:** separar geração inicial de revisão dirigida por comentários.

- **Arquivo:** `src/animus/ai/agno/workflows/intake/__init__.py`
- **Mudança:** exportar `AgnoRegeneratePetitionDraftWorkflow` e `AgnoRegenerateSecondInstanceJudgmentDraftWorkflow`.
- **Justificativa:** manter composition pública dos workflows de intake.

## PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/__init__.py`
- **Mudança:** exportar `RegeneratePetitionDraftJob` e `RegenerateSecondInstanceJudgmentDraftJob`.
- **Justificativa:** permitir registro no composition root do Inngest.

- **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
- **Mudança:** importar e registrar os dois novos jobs em `register_intake_jobs(...)`.
- **Justificativa:** tornar os consumidores dos eventos executáveis pelo Inngest.

# 7. O que deve ser removido?

Não aplicável.

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** criar eventos de regeração dedicados em vez de reutilizar eventos de geração inicial.
- **Alternativas consideradas:** reutilizar `PetitionDraftGenerationTriggeredEvent` e `SecondInstanceJudgmentDraftGenerationTriggeredEvent` adicionando `comments` opcional.
- **Motivo da escolha:** geração inicial e regeração têm semânticas e payloads diferentes; adicionar campo opcional enfraqueceria o contrato dos jobs existentes.
- **Impactos / trade-offs:** adiciona dois eventos e dois jobs, mas evita branching nos jobs de geração inicial.

- **Decisão:** criar workflows revisores dedicados.
- **Alternativas consideradas:** adicionar `current_draft` e `comments` opcionais aos workflows de geração inicial.
- **Motivo da escolha:** o prompt de revisão deve preservar a minuta atual e modificar apenas o que foi solicitado; isso é comportamento diferente de gerar do zero.
- **Impactos / trade-offs:** aumenta wiring no `AiPipe` e no `IntakeSquad`, mas mantém responsabilidades claras.

- **Decisão:** exigir `422` para pré-condições de regeração por meio de erros de domínio específicos de `intake`.
- **Alternativas consideradas:** reutilizar `PetitionDraftUnavailableError`, `SecondInstanceJudgmentDraftUnavailableError`, `AnalysisPrecedentsUnavailableError` e `ChosenAnalysisPrecedentsRequiredError`.
- **Motivo da escolha:** os erros existentes hoje são mapeados para `404` ou `409`; o ticket definiu `422` para pré-condições de regeração.
- **Impactos / trade-offs:** adiciona uma família de erros de domínio para regeração e um mapeamento REST específico, mas evita mudar contratos de endpoints existentes que já usam os erros antigos.

- **Decisão:** validar `CaseSummary` no trigger, embora o ticket destaque apenas minuta e precedentes como pré-condições `422`.
- **Alternativas consideradas:** deixar o job encerrar sem falha quando `CaseSummary` estiver ausente, como alguns jobs de geração inicial fazem.
- **Motivo da escolha:** a regeração depende explicitamente do `CaseSummary` como contexto imutável; falhar cedo evita publicar evento que não pode ser processado corretamente.
- **Impactos / trade-offs:** torna o endpoint mais estrito, mas reduz falhas assíncronas silenciosas.

- **Decisão:** publicar os eventos de conclusão já existentes após regeração.
- **Alternativas consideradas:** criar eventos `RegenerationFinishedEvent` específicos.
- **Motivo da escolha:** para o consumidor mobile e notificações, o efeito observado é “minuta disponível/atualizada”; os eventos existentes já carregam `analysis_type` e acionam notificações de conclusão.
- **Impactos / trade-offs:** consumidores não distinguem geração inicial de regeração pelo evento final; se essa distinção for necessária no futuro, adicionar novo campo ou evento específico.

# 9. Diagramas e Referências

- **Fluxo de dados — petição:**

```text
HTTP Request
  -> Middleware
  -> IntakeRouter / AnalysesRouter
  -> TriggerPetitionDraftRegenerationController
  -> IntakePipe.verify_analysis_by_account_from_request
  -> DatabasePipe + PubSubPipe
  -> TriggerPetitionDraftRegenerationUseCase
  -> PetitionDraftsRepository / CaseSummariesRepository / AnalysisPrecedentsRepository / Broker
  -> InngestBroker
  -> 202 Accepted

PetitionDraftRegenerationTriggeredEvent
  -> RegeneratePetitionDraftJob
  -> SQLAlchemy repositories
  -> AiPipe.get_regenerate_petition_draft_workflow()
  -> AgnoRegeneratePetitionDraftWorkflow
  -> CreatePetitionDraftUseCase
  -> PostgreSQL (petition_drafts, analyses)
  -> PetitionDraftGenerationFinishedEvent
```

- **Fluxo de dados — sentença:**

```text
HTTP Request
  -> Middleware
  -> IntakeRouter / AnalysesRouter
  -> TriggerSecondInstanceJudgmentDraftRegenerationController
  -> IntakePipe.verify_analysis_by_account_from_request
  -> DatabasePipe + PubSubPipe
  -> TriggerSecondInstanceJudgmentDraftRegenerationUseCase
  -> SecondInstanceJudgmentDraftsRepository / CaseSummariesRepository / AnalysisPrecedentsRepository / Broker
  -> InngestBroker
  -> 202 Accepted

SecondInstanceJudgmentDraftRegenerationTriggeredEvent
  -> RegenerateSecondInstanceJudgmentDraftJob
  -> SQLAlchemy repositories
  -> AiPipe.get_regenerate_judgment_draft_workflow()
  -> AgnoRegenerateSecondInstanceJudgmentDraftWorkflow
  -> CreateSecondInstanceJudgmentDraftUseCase
  -> PostgreSQL (judgment_drafts, analyses)
  -> SecondInstanceJudgmentDraftGenerationFinishedEvent
```

- **Referências:**
- `src/animus/core/intake/use_cases/trigger_petition_draft_generation_use_case.py`
- `src/animus/core/intake/use_cases/trigger_second_instance_judgment_draft_generation_use_case.py`
- `src/animus/core/intake/use_cases/create_petition_draft_use_case.py`
- `src/animus/core/intake/use_cases/create_judgment_draft_use_case.py`
- `src/animus/rest/controllers/intake/trigger_petition_draft_generation_controller.py`
- `src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_generation_controller.py`
- `src/animus/ai/agno/workflows/intake/agno_generate_petition_draft_workflow.py`
- `src/animus/ai/agno/workflows/intake/agno_generate_second_instance_judgment_draft_workflow.py`
- `src/animus/ai/agno/squads/intake_squad.py`
- `src/animus/pubsub/inngest/jobs/intake/generate_petition_draft_job.py`
- `src/animus/pubsub/inngest/jobs/intake/generate_second_instance_judgment_draft_job.py`
- `src/animus/pubsub/inngest/inngest_pubsub.py`

# 10. Pendências / Dúvidas

- **Descrição da pendência:** O arquivo placeholder apontava apenas para o PRD RF 07, mas o ticket ANI-126 também inclui RF 08.
- **Impacto na implementação:** poderia gerar uma spec incompleta cobrindo apenas petição.
- **Ação sugerida:** decisão confirmada via `question`: esta spec cobre petição e sentença.

- **Descrição da pendência:** O contrato `422` exigido pelo ticket não existe atualmente nos handlers globais para erros de domínio de `intake`.
- **Impacto na implementação:** a implementação deve criar `DraftRegenerationPreconditionError` e registrá-lo no `AppErrorHandler`; caso contrário, pré-condições seriam serializadas como `404`, `409` ou `400`.
- **Ação sugerida:** decisão confirmada via `question`: exigir `422`.

- **Descrição da pendência:** O PRD não especifica limite máximo de tamanho para `comments`.
- **Impacto na implementação:** comentários muito longos podem aumentar custo e latência do workflow de IA.
- **Ação sugerida:** validar com produto; até lá, exigir apenas string não vazia e registrar o risco operacional.
