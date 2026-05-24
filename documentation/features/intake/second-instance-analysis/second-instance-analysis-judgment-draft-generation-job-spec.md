---
title: Job de geração de minuta de sentença para análise de segunda instância
prd: https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/49348609
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-94
status: open
last_updated_at: 2026-05-16
---

# 1. Objetivo

Implementar o disparo HTTP e o pipeline assíncrono para gerar ou regerar a minuta de sentença de uma análise `SECOND_INSTANCE` após a conclusão da busca e classificação de precedentes. A entrega deve reutilizar `CaseSummary` e `AnalysisPrecedent` já persistidos, gerar a minuta estruturada via workflow de IA, persistir o resultado em `second_instance_judgment_drafts` usando `SecondInstanceJudgmentDraftsRepository.add(...)` na primeira geração e `SecondInstanceJudgmentDraftsRepository.replace(...)` na regeração, e atualizar a análise para `DONE` em sucesso ou `FAILED` em falha operacional.

# 2. Escopo

## 2.1 In-scope

- Criar endpoint HTTP assíncrono para o app solicitar geração ou regeração de minuta de sentença.
- Criar evento de domínio `SecondInstanceJudgmentDraftGenerationTriggeredEvent` para desacoplar o request HTTP do job Inngest.
- Criar use case `TriggerSecondInstanceJudgmentDraftGenerationUseCase` para validar pré-condições e publicar o evento.
- Criar use case `CreateSecondInstanceJudgmentDraftUseCase` para encapsular persistência da minuta e transição da análise para `DONE`.
- Criar interface `GenerateSecondInstanceJudgmentDraftWorkflow` no `core`.
- Criar implementação `AgnoGenerateSecondInstanceJudgmentDraftWorkflow` na camada `ai`.
- Criar `SecondInstanceJudgmentDraftOutput` como saída estruturada do agente de IA antes da normalização para `SecondInstanceJudgmentDraftDto`.
- Adicionar agente `second_instance_judgment_draft_generator_agent` em `IntakeSquad`.
- Adicionar factory `AiPipe.get_generate_judgment_draft_workflow(...)`.
- Criar `GenerateSecondInstanceJudgmentDraftJob` em Inngest com `retries=2`, steps explícitos e `on_failure`.
- Registrar o novo job na composição Inngest.
- Estender o relatório de segunda instância para expor `draft` quando já existir, sem bloquear a consulta antes da geração.
- Reutilizar a persistência existente de minuta, incluindo a migration de rename da tabela para `second_instance_judgment_drafts`.

## 2.2 Out-of-scope

- Alterar a extração da petição inicial dos autos.
- Reexecutar sumarização de caso durante a geração ou regeração da minuta.
- Reexecutar busca, classificação ou síntese de precedentes durante a geração ou regeração da minuta.
- Criar nova tabela específica de segunda instância para minuta.
- Implementar exportação da minuta em PDF.
- Implementar edição manual da minuta no app.
- Criar notificação push específica de conclusão da minuta.
- Alterar o fluxo de `CASE_ASSESSMENT` ou `FIRST_INSTANCE`.

# 3. Requisitos

## 3.1 Funcionais

- O Juiz deve conseguir solicitar geração ou regeração da minuta para uma análise `SECOND_INSTANCE` por ação explícita do app.
- A solicitação deve ser aceita somente quando a análise existir, pertencer à conta autenticada, for `SECOND_INSTANCE`, possuir `CaseSummary` e possuir ao menos um `AnalysisPrecedent` persistido com `is_chosen = True`.
- O job deve reutilizar `CaseSummary` e `AnalysisPrecedent` persistidos para a `analysis_id` recebida.
- O job não deve reenviar autos, reextrair petição, recriar resumo de caso ou rebuscar precedentes.
- A minuta gerada deve conter, no mínimo, as seções `relatorio`, `fundamentacao`, `analise_de_aderencia_ou_distincao` e `dispositivo_sugerido`.
- A ausência de precedente com `applicability_level = 2` não deve bloquear a geração da minuta desde que exista pelo menos um precedente manual ou automaticamente escolhido.
- A primeira geração deve persistir a minuta via `SecondInstanceJudgmentDraftsRepository.add(...)`.
- A regeração deve substituir a minuta anterior via `SecondInstanceJudgmentDraftsRepository.replace(...)`.
- Em sucesso, a análise deve avançar para `SecondInstanceAnalysisStatus.DONE`.
- Em falha não recuperável no job, a análise deve avançar para `SecondInstanceAnalysisStatus.FAILED`.
- O relatório de segunda instância deve retornar a minuta quando ela já estiver persistida.

## 3.2 Não funcionais

- **Segurança:** o endpoint deve exigir autenticação e validar ownership via `IntakePipe.verify_analysis_by_account_from_request(...)`; o use case deve validar novamente existência e tipo da análise por contrato de domínio.
- **Idempotência:** múltiplas solicitações para a mesma `analysis_id` devem ser seguras; quando já existir `SecondInstanceJudgmentDraft`, o novo resultado substitui o anterior.
- **Resiliência:** o job deve usar `retries=2` e `on_failure` para reforçar status `FAILED` se o handler falhar depois do retry do Inngest.
- **Compatibilidade retroativa:** o DTO `SecondInstanceJudgmentDraftDto` e o repository `SecondInstanceJudgmentDraftsRepository` devem ser reutilizados; a tabela foi renomeada para `second_instance_judgment_drafts` por migration dedicada sem alterar o conteúdo persistido.
- **Compatibilidade HTTP:** o novo endpoint deve responder `202 Accepted` sem body, seguindo o padrão de `SearchAnalysisPrecedentsController` para disparos assíncronos.
- **Observabilidade por estado persistido:** o app deve acompanhar a evolução por `GET /intake/analyses/{analysis_id}/status` e pelo relatório de segunda instância.

# 4. O que já existe?

## Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analyses.py`) — entidade que normaliza `AnalysisType` e valida status por tipo de análise.
- **`AnalysisType`** (`src/animus/core/intake/domain/entities/analysis_type.py`) — enum que diferencia `CASE_ASSESSMENT`, `FIRST_INSTANCE` e `SECOND_INSTANCE`.
- **`SecondInstanceAnalysisStatus`** (`src/animus/core/intake/domain/entities/second_instance_analysis_status.py`) — já possui `GENERATING_JUDGMENT_DRAFT`, `DONE` e `FAILED`.
- **`CaseSummary`** (`src/animus/core/intake/domain/structures/case_summary.py`) — structure do resumo que alimenta o prompt da minuta.
- **`CaseSummaryDto`** (`src/animus/core/intake/domain/structures/dtos/case_summary_dto.py`) — DTO com `case_summary`, `legal_issue`, `central_question`, `requested_relief`, `procedural_issues` e demais campos úteis para o prompt.
- **`AnalysisPrecedent`** (`src/animus/core/intake/domain/structures/analysis_precedent.py`) — structure dos precedentes classificados, incluindo `synthesis`, `applicability_level` e `legal_features`.
- **`AnalysisPrecedentDto`** (`src/animus/core/intake/domain/structures/dtos/analysis_precedent_dto.py`) — DTO serializável dos precedentes usados como entrada do workflow.
- **`AnalysisPrecedentApplicabilityLevel`** (`src/animus/core/intake/domain/structures/analysis_precedent_applicability_level.py`) — define `0`, `1` e `2`, em que `2` representa precedente `APPLICABLE`.
- **`SecondInstanceJudgmentDraft`** (`src/animus/core/intake/domain/structures/second_judgment_draft.py`) — structure existente para minuta, com `analysis_id` e `content`.
- **`SecondInstanceJudgmentDraftDto`** (`src/animus/core/intake/domain/structures/dtos/second_instance_judgment_draft_dto.py`) — DTO existente para persistir e retornar a minuta como `content` textual.
- **`SecondInstanceAnalysisReportDraftDto`** (`src/animus/core/intake/domain/structures/dtos/second_instance_analysis_report_draft.py`) — DTO de saída do relatório de segunda instância para expor a minuta como `draft`.
- **`CaseSummariesRepository`** (`src/animus/core/intake/interfaces/case_summaries_repository.py`) — port usado para obter o resumo por `analysis_id`.
- **`AnalysisPrecedentsRepository`** (`src/animus/core/intake/interfaces/analysis_precedents_repository.py`) — port usado para listar os precedentes da análise.
- **`SecondInstanceJudgmentDraftsRepository`** (`src/animus/core/intake/interfaces/judgment_drafts_repository.py`) — port existente com `find_by_analysis_id(...)`, `add(...)` e `replace(...)`.
- **`RequestAnalysisPrecedentsSearchUseCase`** (`src/animus/core/intake/use_cases/request_analysis_precedents_search_use_case.py`) — referência para validação de pré-condição e publicação de evento assíncrono.
- **`CreateCaseSummaryUseCase`** (`src/animus/core/intake/use_cases/create_case_summary_use_case.py`) — referência para decidir entre `add(...)` e `replace(...)` conforme existência prévia.
- **`UpdateAnalysisStatusUseCase`** (`src/animus/core/intake/use_cases/update_analysis_status_use_case.py`) — referência para atualizar status em jobs, sem colocar lógica de status em repository.
- **`GetSecondInstanceAnalysisReportUseCase`** (`src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`) — relatório atual de segunda instância, ainda sem `judgment_draft`.

## Database

- **`SecondInstanceJudgmentDraftModel`** (`src/animus/database/sqlalchemy/models/intake/judgment_draft_model.py`) — model existente da tabela `second_instance_judgment_drafts`, com `analysis_id` como PK/FK e `content` textual.
- **`SecondInstanceJudgmentDraftMapper`** (`src/animus/database/sqlalchemy/mappers/intake/judgment_draft_mapper.py`) — mapper existente entre `SecondInstanceJudgmentDraftModel` e `SecondInstanceJudgmentDraft`.
- **`SqlalchemySecondInstanceJudgmentDraftsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`) — implementação existente de `SecondInstanceJudgmentDraftsRepository`.
- **Migrations `20260511_120000_intake_analysis_documents_case_summaries_and_drafts.py` e `20260516_143500_rename_judgment_drafts_table.py`** (`migrations/versions/...`) — criam a tabela original e depois a renomeiam para `second_instance_judgment_drafts`.

## AI

- **`AgnoSummarizeSecondInstanceCaseWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_summarize_second_instance_case_workflow.py`) — referência de workflow Agno especializado em segunda instância com `_StepNames`, `session_state` e normalização de output.
- **`AgnoSynthesizeAndClassifyAnalysisPrecedentsWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_synthesize_analysis_precedents_workflow.py`) — referência de workflow que recebe precedentes, monta prompt e persiste resultado em step dedicado.
- **`IntakeSquad`** (`src/animus/ai/agno/squads/intake_squad.py`) — squad que concentra agentes do intake, incluindo o agente de sumarização de segunda instância.
- **`CaseSummaryOutput`** (`src/animus/ai/agno/outputs/intake/case_summary_output.py`) — referência de output Pydantic para saída estruturada de agente.
- **`AnalysisPrecedentsSynthesisOutput`** (`src/animus/ai/agno/outputs/intake/analysis_precedents_synthesis_output.py`) — referência de output estruturado com listas e campos validados.

## REST / Routers / Pipes

- **`SearchAnalysisPrecedentsController`** (`src/animus/rest/controllers/intake/search_analysis_precedents_controller.py`) — referência principal de endpoint `POST` assíncrono, `202`, guard de análise e publicação via `Broker`.
- **`GetSecondInstanceAnalysisReportController`** (`src/animus/rest/controllers/intake/get_second_instance_analysis_report_controller.py`) — endpoint atual que expõe o relatório de segunda instância.
- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) — registra controllers de análises no contexto `/intake`.
- **`DatabasePipe.get_judgment_drafts_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — já fornece `SecondInstanceJudgmentDraftsRepository` para controllers.
- **`PubSubPipe.get_broker_from_request(...)`** (`src/animus/pipes/pubsub_pipe.py`) — fornece `Broker` concreto baseado em `InngestBroker`.
- **`AiPipe`** (`src/animus/pipes/ai_pipe.py`) — composition point para instanciar workflows concretos de IA.

## PubSub

- **`SummarizeSecondInstanceCaseJob`** (`src/animus/pubsub/inngest/jobs/intake/extract_petition_job.py`) — referência de job de segunda instância com `_normalize_payload`, `run_in_executor`, commits por etapa e `on_failure`.
- **`SearchAnalysisPrecedentsJob`** (`src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`) — referência de job com `retries=2`, mudança de status intermediária, workflow de IA e publicação de evento de conclusão.
- **`InngestPubSub.register_intake_jobs(...)`** (`src/animus/pubsub/inngest/inngest_pubsub.py`) — composition root dos jobs Inngest de intake.

# 5. O que deve ser criado?

## Camada Core (Erros de Domínio)

- **Localização:** `src/animus/core/intake/domain/errors/analysis_precedents_unavailable_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** levantar quando a geração da minuta for solicitada sem precedentes persistidos para a análise.

- **Localização:** `src/animus/core/intake/domain/errors/chosen_analysis_precedents_required_error.py` (**novo arquivo**)
- **Classe base:** `ConflictError`
- **Motivo:** levantar quando existirem precedentes persistidos, mas nenhum estiver marcado como escolhido para a geração da minuta.

- **Localização:** `src/animus/core/intake/domain/errors/second_instance_analysis_required_error.py` (**novo arquivo**)
- **Classe base:** `ConflictError`
- **Motivo:** levantar quando a geração de minuta de segunda instância for solicitada para análise que não é `AnalysisType.SECOND_INSTANCE`.

## Camada Core (Interfaces / Ports)

- **Localização:** `src/animus/core/intake/interfaces/generate_judgment_draft_workflow.py` (**novo arquivo**)
- **Métodos:**
  - `run(analysis_id: str, case_summary: CaseSummary, precedents: list[AnalysisPrecedent]) -> SecondInstanceJudgmentDraftDto` — gera a minuta estruturada a partir do resumo e dos precedentes já classificados, sem persistir.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/trigger_second_instance_judgment_draft_generation_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `AnalysesRepository`, `CaseSummariesRepository`, `AnalysisPrecedentsRepository`, `Broker`
- **Método principal:** `execute(analysis_id: str) -> None` — valida pré-condições de geração e publica `SecondInstanceJudgmentDraftGenerationTriggeredEvent`.
- **Fluxo resumido:**
  - Normaliza `analysis_id` como `Id`.
  - Busca `Analysis` em `AnalysesRepository.find_by_id(...)`; se ausente, lança `AnalysisNotFoundError`.
  - Verifica `analysis.type == AnalysisType.SECOND_INSTANCE`; se não, lança `SecondInstanceAnalysisRequiredError`.
  - Busca `CaseSummary` em `CaseSummariesRepository.find_by_analysis_id(...)`; se ausente, lança `CaseSummaryUnavailableError`.
  - Busca precedentes em `AnalysisPrecedentsRepository.find_many_by_analysis_id(...)`; se `items` estiver vazio, lança `AnalysisPrecedentsUnavailableError`.
  - Se não houver nenhum precedente com `is_chosen = True`, lança `ChosenAnalysisPrecedentsRequiredError`.
  - Publica `SecondInstanceJudgmentDraftGenerationTriggeredEvent(analysis_id=analysis_id_entity.value)` via `Broker.publish(...)`.

- **Localização:** `src/animus/core/intake/use_cases/create_judgment_draft_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `SecondInstanceJudgmentDraftsRepository`, `AnalysesRepository`
- **Método principal:** `execute(analysis_id: str, dto: SecondInstanceJudgmentDraftDto) -> SecondInstanceJudgmentDraftDto` — cria ou substitui a minuta da análise e conclui o status de segunda instância.
- **Fluxo resumido:**
  - Normaliza `analysis_id` como `Id`.
  - Cria `SecondInstanceJudgmentDraft` a partir de `dto`, garantindo que `dto.analysis_id` corresponda ao `analysis_id` recebido.
  - Busca minuta existente com `SecondInstanceJudgmentDraftsRepository.find_by_analysis_id(...)`.
  - Se inexistente, chama `SecondInstanceJudgmentDraftsRepository.add(judgment_draft)`.
  - Se existente, chama `SecondInstanceJudgmentDraftsRepository.replace(judgment_draft)`.
  - Busca `Analysis`; se ausente, lança `AnalysisNotFoundError`.
  - Verifica `analysis.type == AnalysisType.SECOND_INSTANCE`; se não, lança `SecondInstanceAnalysisRequiredError`.
  - Atualiza status com `analysis.set_status(SecondInstanceAnalysisStatus.DONE)` e persiste via `AnalysesRepository.replace(analysis)`.
  - Retorna `judgment_draft.dto`.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_generation_controller.py` (**novo arquivo**)
- **`*Body`:** Não aplicável; o endpoint não recebe body.
- **Método HTTP e path:** `POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts`
- **`status_code`:** `202`
- **`response_model`:** Não aplicável.
- **Dependências injetadas via `Depends`:**
  - `IntakePipe.verify_analysis_by_account_from_request` para autenticação e ownership.
  - `DatabasePipe.get_analyses_repository_from_request`.
  - `DatabasePipe.get_case_summaries_repository_from_request`.
  - `DatabasePipe.get_analysis_precedents_repository_from_request`.
  - `PubSubPipe.get_broker_from_request`.
- **Fluxo:** path param `analysis_id` → `TriggerSecondInstanceJudgmentDraftGenerationUseCase.execute(analysis_id=analysis_id)` → `Response(status_code=202)`.

## Camada PubSub (Eventos de Domínio)

- **Localização:** `src/animus/core/intake/domain/events/judgment_draft_generation_requested_event.py` (**novo arquivo**)
- **`NAME`:** `"intake/judgment_draft.generation.triggered"`
- **Payload:**
  - `analysis_id: str`

## Camada PubSub (Jobs Inngest)

- **Localização:** `src/animus/pubsub/inngest/jobs/intake/generate_judgment_draft_job.py` (**novo arquivo**)
- **Evento consumido:** `SecondInstanceJudgmentDraftGenerationTriggeredEvent.name`
- **Dependências:** `SqlalchemyAnalysesRepository`, `SqlalchemyCaseSummariesRepository`, `SqlalchemyAnalysisPrecedentsRepository`, `SqlalchemySecondInstanceJudgmentDraftsRepository`, `AiPipe.get_generate_judgment_draft_workflow(...)`, `CreateSecondInstanceJudgmentDraftUseCase`, `UpdateAnalysisStatusUseCase`.
- **Passos (`step.run`):**
  - `normalize_payload` — `data: dict[str, Any] -> dict[str, str]`; normaliza `analysis_id`.
  - `mark_analysis_as_generating_judgment_draft` — atualiza status para `SecondInstanceAnalysisStatus.GENERATING_JUDGMENT_DRAFT` e executa `session.commit()`.
  - `generate_and_persist_judgment_draft` — carrega análise, resumo e precedentes escolhidos; executa workflow; persiste `SecondInstanceJudgmentDraft`; conclui status `DONE`; executa `session.commit()`.
  - `mark_analysis_as_failed` — em exceções não tratadas, atualiza status para `SecondInstanceAnalysisStatus.FAILED` e executa `session.commit()`.
- **Métodos internos:**
  - `handle(inngest: Inngest) -> Any` — registra a função Inngest com `fn_id='generate-judgment-draft'`, `retries=2` e `on_failure=GenerateSecondInstanceJudgmentDraftJob._handle_failure`.
  - `_normalize_payload(data: dict[str, Any]) -> dict[str, str]` — retorna `{'analysis_id': str(data['analysis_id'])}`.
  - `_mark_analysis_as_generating_judgment_draft(payload: _Payload) -> None` — delega execução síncrona via `run_in_executor`.
  - `_mark_analysis_as_generating_judgment_draft_sync(payload: _Payload) -> None` — atualiza status para `GENERATING_JUDGMENT_DRAFT` se a análise existir.
  - `_generate_and_persist_judgment_draft(payload: _Payload) -> None` — delega execução síncrona via `run_in_executor`.
  - `_generate_and_persist_judgment_draft_sync(payload: _Payload) -> None` — orquestra repositories, workflow, persistência e status `DONE`.
  - `_mark_analysis_as_failed(payload: _Payload) -> None` — delega execução síncrona via `run_in_executor`.
  - `_mark_analysis_as_failed_sync(payload: _Payload) -> None` — atualiza status para `FAILED` se a análise existir.
  - `_handle_failure(context: Context) -> None` — extrai payload do contexto de falha e reforça status `FAILED`.
- **Idempotência:** o job sempre chama `CreateSecondInstanceJudgmentDraftUseCase`, que usa `replace(...)` quando já existir minuta persistida; reexecuções não criam duplicidade porque `second_instance_judgment_drafts.analysis_id` é chave primária.

## Camada AI (Outputs Agno)

- **Localização:** `src/animus/ai/agno/outputs/intake/second_instance_judgment_draft_output.py` (**novo arquivo**)
- **Tipo:** `BaseModel`
- **Atributos:**
  - `relatorio: str`
  - `fundamentacao: str`
  - `analise_de_aderencia_ou_distincao: str`
  - `dispositivo_sugerido: str`
  - `aviso_ausencia_precedente_aplicavel: str | None = None`

## Camada AI (Workflows Agno)

- **Localização:** `src/animus/ai/agno/workflows/intake/agno_generate_judgment_draft_workflow.py` (**novo arquivo**)
- **Interface implementada:** `GenerateSecondInstanceJudgmentDraftWorkflow`
- **Dependências:** não acessa banco diretamente; usa apenas entradas recebidas no `run(...)` e `IntakeSquad`.
- **Métodos:**
  - `__init__(self) -> None` — instancia `IntakeSquad` e `_StepNames`.
  - `run(self, analysis_id: str, case_summary: CaseSummary, precedents: list[AnalysisPrecedent]) -> SecondInstanceJudgmentDraftDto` — monta e executa o workflow Agno, normaliza output estruturado em `SecondInstanceJudgmentDraftDto`.
  - `_build_judgment_draft_input_step(self, _: StepInput, run_context: RunContext) -> StepOutput` — monta prompt com resumo do caso, precedentes, sínteses, níveis de aplicabilidade e aviso se não houver precedente `APPLICABLE`.
  - `_normalize_judgment_draft_output(self, output: object, analysis_id: str) -> SecondInstanceJudgmentDraftDto` — valida `SecondInstanceJudgmentDraftOutput` e concatena as seções em `content` textual com cabeçalhos estáveis.
- **Steps:**
  - `BUILD_JUDGMENT_DRAFT_INPUT` — executor Python para preparar o prompt.
  - `GENERATE_JUDGMENT_DRAFT` — agente `IntakeSquad.second_instance_judgment_draft_generator_agent`.

## Camada AI (Squad)

- **Localização:** `src/animus/ai/agno/squads/intake_squad.py`
- **Método novo:**
  - `second_instance_judgment_draft_generator_agent(self) -> Agent` — agente especializado em gerar minuta de sentença em PT-BR para segunda instância, com `output_schema=SecondInstanceJudgmentDraftOutput`, modelo `OpenAIChat(id='gpt-5.4', temperature=0, timeout=60, seed=42)` e instruções para retornar apenas o objeto estruturado esperado.

## Camada Pipes

- **Localização:** `src/animus/pipes/ai_pipe.py`
- **Método `Depends`:**
  - `get_generate_judgment_draft_workflow() -> GenerateSecondInstanceJudgmentDraftWorkflow` — instancia e retorna `AgnoGenerateSecondInstanceJudgmentDraftWorkflow` tipado pela interface do `core`.
- **Sessão SQLAlchemy:** Não aplicável; o workflow recebe `CaseSummary` e precedentes já carregados pelo job.

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/events/__init__.py`
- **Mudança:** exportar `SecondInstanceJudgmentDraftGenerationTriggeredEvent` em imports e `__all__`.
- **Justificativa:** manter exports públicos de eventos do intake consistentes.

- **Arquivo:** `src/animus/core/intake/domain/errors/__init__.py`
- **Mudança:** exportar `AnalysisPrecedentsUnavailableError`, `ChosenAnalysisPrecedentsRequiredError` e `SecondInstanceAnalysisRequiredError`.
- **Justificativa:** manter erros de domínio acessíveis pelos use cases e bordas.

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudança:** exportar `GenerateSecondInstanceJudgmentDraftWorkflow`.
- **Justificativa:** estabilizar import público do novo port.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** exportar `TriggerSecondInstanceJudgmentDraftGenerationUseCase` e `CreateSecondInstanceJudgmentDraftUseCase`.
- **Justificativa:** seguir o padrão dos use cases existentes importados por controllers e jobs.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/second_instance_analysis_report_dto.py`
- **Mudança:** adicionar `draft: SecondInstanceAnalysisReportDraftDto | None`.
- **Justificativa:** permitir que o app leia a minuta gerada pelo relatório de segunda instância sem criar endpoint adicional de leitura.

- **Arquivo:** `src/animus/core/intake/domain/structures/second_instance_analysis_report.py`
- **Mudança:** adicionar atributo `draft: SecondInstanceJudgmentDraft | None`, ajustar `create(...)` e `dto` para mapear `SecondInstanceAnalysisReportDraftDto`.
- **Justificativa:** refletir o novo campo opcional do DTO mantendo a consulta do relatório disponível antes da geração.

- **Arquivo:** `src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`
- **Mudança:** injetar `SecondInstanceJudgmentDraftsRepository`, buscar a minuta por `analysis_id` e montar `SecondInstanceAnalysisReport` com `draft` opcional.
- **Justificativa:** expor a minuta já persistida no relatório sem levantar `SecondInstanceJudgmentDraftUnavailableError` antes da geração.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** exportar `TriggerSecondInstanceJudgmentDraftGenerationController`.
- **Justificativa:** permitir registro pelo router de análises.

- **Arquivo:** `src/animus/rest/controllers/intake/get_second_instance_analysis_report_controller.py`
- **Mudança:** injetar `SecondInstanceJudgmentDraftsRepository` via `DatabasePipe.get_judgment_drafts_repository_from_request` e repassar ao `GetSecondInstanceAnalysisReportUseCase`.
- **Justificativa:** o relatório passa a retornar `judgment_draft` quando existir.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** importar e registrar `TriggerSecondInstanceJudgmentDraftGenerationController.handle(router)`.
- **Justificativa:** incluir o novo endpoint no contexto `/intake` sem lógica no router.

## AI

- **Arquivo:** `src/animus/ai/agno/outputs/intake/__init__.py`
- **Mudança:** exportar `SecondInstanceJudgmentDraftOutput`.
- **Justificativa:** manter output público do módulo de outputs do intake.

- **Arquivo:** `src/animus/ai/agno/workflows/intake/__init__.py`
- **Mudança:** exportar `AgnoGenerateSecondInstanceJudgmentDraftWorkflow`.
- **Justificativa:** manter exports públicos de workflows do intake.

- **Arquivo:** `src/animus/ai/agno/workflows/__init__.py`
- **Mudança:** exportar `AgnoGenerateSecondInstanceJudgmentDraftWorkflow` se o padrão de import público for mantido no nível superior.
- **Justificativa:** preservar consistência com o export atual de `AgnoSummarizeFirstInstanceCaseWorkflow`.

- **Arquivo:** `src/animus/ai/agno/__init__.py`
- **Mudança:** exportar `SecondInstanceJudgmentDraftOutput` e `AgnoGenerateSecondInstanceJudgmentDraftWorkflow` se usados como API pública do pacote.
- **Justificativa:** manter estabilidade dos imports públicos já existentes nesse nível.

## PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/__init__.py`
- **Mudança:** exportar `GenerateSecondInstanceJudgmentDraftJob`.
- **Justificativa:** permitir registro no composition root do Inngest.

- **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
- **Mudança:** importar `GenerateSecondInstanceJudgmentDraftJob` e adicioná-lo em `register_intake_jobs(...)`.
- **Justificativa:** registrar o consumidor do evento `SecondInstanceJudgmentDraftGenerationTriggeredEvent` no runtime Inngest.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/seeders/intake_seeder.py`
- **Mudança:** Não aplicável.
- **Justificativa:** não há seeders atuais para `second_instance_judgment_drafts`, nem necessidade de dados iniciais para geração de minuta.

# 7. O que deve ser removido?

**Não aplicável**.

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** reutilizar `SecondInstanceJudgmentDraft`, `SecondInstanceJudgmentDraftDto`, `SecondInstanceJudgmentDraftsRepository` e a tabela renomeada `second_instance_judgment_drafts` para a minuta de segunda instância.
- **Alternativas consideradas:** criar nova tabela específica para `SecondInstanceJudgmentDraft`, novo repository e mapper sem reutilizar a persistência existente.
- **Motivo da escolha:** a codebase já possuía persistência de minuta; o rename da tabela torna o schema explícito sem mudar o contrato do agregado.
- **Impactos / trade-offs:** reduz duplicação e melhora clareza do banco, ao custo de uma migration adicional de rename.

- **Decisão:** armazenar a minuta estruturada como `content: str` com seções estáveis, após receber output Pydantic estruturado da IA.
- **Alternativas consideradas:** alterar `SecondInstanceJudgmentDraftDto` e `judgment_drafts` para colunas separadas por seção.
- **Motivo da escolha:** o schema atual de persistência já existe e atende à entrega sem migration; o output estruturado garante validação antes da serialização textual.
- **Impactos / trade-offs:** o app lê um conteúdo textual já estruturado por cabeçalhos; se no futuro precisar editar ou renderizar seções independentemente, pode ser necessária refatoração de schema.

- **Decisão:** adicionar `draft: SecondInstanceAnalysisReportDraftDto | None` ao relatório de segunda instância.
- **Alternativas consideradas:** criar endpoint `GET` específico para a minuta ou lançar erro enquanto a minuta não existir.
- **Motivo da escolha:** o relatório já é a tela consolidada de segunda instância e precisa continuar acessível antes da geração para exibir precedentes.
- **Impactos / trade-offs:** consumidores devem tratar `judgment_draft` como opcional até o status `DONE`.

- **Decisão:** gerar a minuta apenas com precedentes escolhidos, sem criar flag persistida para ausência de precedente aplicável.
- **Alternativas consideradas:** adicionar campo em `SecondInstanceJudgmentDraftDto` ou `SecondInstanceAnalysisReportDto` como `has_applicable_precedent`.
- **Motivo da escolha:** a seleção explícita do usuário ou a auto-seleção de precedentes com `applicability_level == 2` define de forma auditável quais precedentes entram no prompt; a ausência de `2` por si só não impede geração se houver escolha manual.
- **Impactos / trade-offs:** o app precisa garantir pelo menos um precedente escolhido antes do disparo, e o workflow deixa de receber precedentes não selecionados.

- **Decisão:** o endpoint de geração usa `POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts` e retorna `202` sem body.
- **Alternativas consideradas:** criar `POST /judgment-drafts/generate` ou reaproveitar o endpoint de relatório.
- **Motivo da escolha:** segue o padrão de operação assíncrona orientada a recurso e evita verbo adicional na rota.
- **Impactos / trade-offs:** o mesmo endpoint cobre geração inicial e regeração; a semântica de substituição fica no use case e no repository.

- **Decisão:** o job marca `GENERATING_JUDGMENT_DRAFT` em step próprio antes de chamar IA.
- **Alternativas consideradas:** marcar o status no use case de request HTTP.
- **Motivo da escolha:** segue o padrão de `SearchAnalysisPrecedentsJob`, em que o status operacional reflete a execução real do job.
- **Impactos / trade-offs:** pode existir pequena janela entre o `202` e o início do job em que o status anterior ainda aparece.

# 9. Diagramas e Referências

- **Fluxo de dados:**

```text
HTTP Request
  POST /intake/analyses/{analysis_id}/judgment-drafts
    -> Middleware SQLAlchemy/Inngest
    -> IntakeRouter
    -> AnalysesRouter
    -> TriggerSecondInstanceJudgmentDraftGenerationController
    -> IntakePipe.verify_analysis_by_account_from_request
    -> DatabasePipe / PubSubPipe
    -> TriggerSecondInstanceJudgmentDraftGenerationUseCase
    -> AnalysesRepository / CaseSummariesRepository / AnalysisPrecedentsRepository
    -> Broker.publish(SecondInstanceJudgmentDraftGenerationTriggeredEvent)
    -> 202 Accepted
```

- **Fluxo assíncrono:**

```text
SecondInstanceJudgmentDraftGenerationTriggeredEvent
  -> InngestBroker
  -> GenerateSecondInstanceJudgmentDraftJob
      -> normalize_payload
      -> mark_analysis_as_generating_judgment_draft
          -> UpdateAnalysisStatusUseCase(..., GENERATING_JUDGMENT_DRAFT)
          -> session.commit()
      -> generate_and_persist_judgment_draft
          -> SqlalchemyAnalysesRepository.find_by_id(...)
          -> SqlalchemyCaseSummariesRepository.find_by_analysis_id(...)
          -> SqlalchemyAnalysisPrecedentsRepository.find_many_by_analysis_id(...)
          -> AiPipe.get_generate_judgment_draft_workflow(...)
          -> AgnoGenerateSecondInstanceJudgmentDraftWorkflow.run(...)
          -> CreateSecondInstanceJudgmentDraftUseCase.execute(...)
              -> SecondInstanceJudgmentDraftsRepository.add(...) ou replace(...)
              -> Analysis.set_status(DONE)
          -> session.commit()
      -> on exception
          -> UpdateAnalysisStatusUseCase(..., FAILED)
          -> session.commit()
```

- **Fluxo de leitura após geração:**

```text
GET /intake/analyses/{analysis_id}/second-instance-report
  -> GetSecondInstanceAnalysisReportController
  -> GetSecondInstanceAnalysisReportUseCase
  -> AnalysesRepository / AnalysisDocumentsRepository
  -> CaseSummariesRepository / AnalysisPrecedentsRepository
  -> SecondInstanceJudgmentDraftsRepository.find_by_analysis_id(...)
  -> SecondInstanceAnalysisReportDto(draft=SecondInstanceAnalysisReportDraftDto | None)
```

- **Referências:**
  - `src/animus/rest/controllers/intake/search_analysis_precedents_controller.py` — endpoint assíncrono com `202`, guard e `Broker`.
  - `src/animus/core/intake/use_cases/request_analysis_precedents_search_use_case.py` — validação de pré-condição e publicação de evento.
  - `src/animus/core/intake/use_cases/create_case_summary_use_case.py` — padrão de `add(...)` vs `replace(...)` e atualização de status sem repository assumir regra.
  - `src/animus/core/intake/use_cases/get_first_instance_analysis_report_use_case.py` — referência de leitura de `SecondInstanceJudgmentDraftsRepository` para compor relatório.
  - `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py` — job com `retries=2`, mudança de status, workflow AI e fallback de falha.
  - `src/animus/pubsub/inngest/jobs/intake/extract_petition_job.py` — job de segunda instância com `_Payload`, `run_in_executor`, commits e `on_failure`.
  - `src/animus/ai/agno/workflows/intake/agno_summarize_second_instance_case_workflow.py` — workflow Agno especializado em segunda instância.
  - `src/animus/ai/agno/workflows/intake/agno_synthesize_analysis_precedents_workflow.py` — montagem de prompt com resumo e precedentes.
  - `src/animus/ai/agno/squads/intake_squad.py` — local de agentes do intake.
  - `src/animus/ai/agno/outputs/intake/analysis_precedents_synthesis_output.py` — referência de output Pydantic estruturado.
  - `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py` — persistência existente da minuta.

# 10. Pendências / Dúvidas

**Sem pendências**.

# 11. Restrições

- O `core` deve continuar sem dependência de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest`, Agno ou SDKs externos.
- O endpoint deve delegar regra de negócio para use case e não controlar transação manualmente.
- O job pode abrir sessão SQLAlchemy e fazer `session.commit()` por etapa, seguindo o padrão existente de jobs Inngest.
- O workflow de IA deve retornar `SecondInstanceJudgmentDraftDto`, nunca tipos internos do Agno.
- A camada database não deve ser alterada para adicionar schema novo nesta entrega.
- A ausência de precedentes `APPLICABLE` deve ser tratada como aviso, não como bloqueio.
