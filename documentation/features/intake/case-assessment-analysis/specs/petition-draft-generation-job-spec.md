---
title: Pipeline assíncrono de sumarização e geração de minuta de petição inicial
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AYDsAg
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-93
status: closed
last_updated_at: 2026-05-24
---

# 1. Objetivo

Implementar o pipeline assíncrono de `CASE_ASSESSMENT` para duas etapas: sumarização do caso e geração ou regeração da minuta de petição inicial. A entrega deve incluir um job dedicado de sumarização, separado do fluxo já existente de `FIRST_INSTANCE`, para produzir `CaseSummary` a partir do documento persistido; e um job de geração de minuta que consome o resumo e os precedentes escolhidos já persistidos, gera a minuta via workflow de IA, persiste `PetitionDraft` e publica `PetitionDraftGenerationFinishedEvent` após sucesso.

# 2. Escopo

## 2.1 In-scope

- Criar evento dedicado para solicitar sumarização de `CASE_ASSESSMENT`, evitando colisão com o `CaseSummaryCaseSummarizationTriggeredEvent` já consumido por `SummarizeFirstInstanceCaseJob`.
- Criar endpoint HTTP para solicitar a sumarização de `CASE_ASSESSMENT`.
- Criar `TriggerCaseAssessmentCaseSummarizationUseCase` para validar pré-condições, atualizar status para `ANALYZING_CASE` e publicar o evento de sumarização.
- Criar `SummarizeCaseAssessmentCaseJob` baseado estruturalmente em `SummarizeSecondInstanceCaseJob`, reutilizando o padrão de steps, `publish_finished_event`, `except` + `on_failure` e `run_in_executor`.
- Criar `AgnoSummarizeCaseAssessmentCaseWorkflow` para produzir e persistir `CaseSummary` de análises `CASE_ASSESSMENT` com prompt próprio.
- Criar endpoint HTTP para solicitar a geração ou regeração da minuta de petição inicial.
- Criar os eventos de domínio `PetitionDraftGenerationTriggeredEvent` e `PetitionDraftGenerationFinishedEvent`.
- Criar `TriggerPetitionDraftGenerationUseCase` para validar pré-condições e publicar o evento de geração da minuta.
- Criar o use case `CreatePetitionDraftUseCase` para criar ou substituir `PetitionDraft` e concluir a análise com status `DONE`.
- Criar a interface `GeneratePetitionDraftWorkflow` no `core`.
- Criar a implementação `AgnoGeneratePetitionDraftWorkflow` na camada `ai`.
- Criar `PetitionDraftOutput` como saída estruturada do agente, alinhada ao contrato persistido de `PetitionDraftDto`.
- Adicionar agente de geração de minuta de petição inicial em `IntakeSquad`.
- Adicionar factory `AiPipe.get_generate_petition_draft_workflow()` sem `Depends`, para uso por job Inngest.
- Criar `GeneratePetitionDraftJob` em Inngest com `retries=2`, `on_failure` e steps explícitos.
- Registrar os novos jobs na composição de jobs de intake do Inngest.
- Encadear sumarização e geração apenas por estado persistido e publicação explícita de eventos, sem acoplamento entre workflows.
- Publicar `CaseSummaryFinishedEvent { analysis_id, account_id }` após sumarização bem-sucedida.
- Publicar `PetitionDraftGenerationFinishedEvent { analysis_id, account_id }` após persistência bem-sucedida da minuta.
- Usar reexecução segura: se já existir `CaseSummary` ou `PetitionDraft`, substituir a versão anterior.

## 2.2 Out-of-scope

- Alterar o fluxo de seleção ou confirmação de precedentes.
- Reexecutar upload, extração em janelas paginadas, busca de precedentes ou qualquer etapa de `SECOND_INSTANCE`.
- Alterar fluxos de `FIRST_INSTANCE` ou `SECOND_INSTANCE` além de reaproveitar componentes já existentes.
- Implementar exportação da minuta em PDF.
- Implementar edição manual da minuta no app.
- Criar notificação push, WebSocket ou consumidor específico para `PetitionDraftGenerationFinishedEvent`.
- Incluir testes automatizados nesta spec.

# 3. Requisitos

## 3.1 Funcionais

- O fluxo de sumarização deve iniciar a partir de `CaseAssessmentCaseSummarizationTriggeredEvent` contendo `analysis_id`.
- O endpoint HTTP de trigger da sumarização deve ser `POST /intake/analyses/{analysis_id}/case-assessment-case-summaries`.
- O endpoint de trigger deve responder `202 Accepted` sem body quando a solicitação for aceita.
- O endpoint deve depender de `IntakePipe.verify_analysis_by_account_from_request` para garantir que a análise pertença à conta autenticada.
- O endpoint deve instanciar `TriggerCaseAssessmentCaseSummarizationUseCase` e delegar a ele a validação de pré-condições e a publicação do evento.
- O endpoint deve seguir o padrão já adotado pelos demais triggers assíncronos de `intake`: controller fino, sem body, retorno explícito de `Response(status_code=202)` e sem lógica de negócio embutida.
- Se a análise não pertencer à conta autenticada, a requisição deve falhar no `IntakePipe.verify_analysis_by_account_from_request`, preservando o contrato de autorização já usado pelos demais endpoints de `analyses`.
- Se a análise não existir, a resposta HTTP deve seguir o mapeamento global já existente para `AnalysisNotFoundError`.
- Se o documento da análise não existir, a resposta HTTP deve seguir o mapeamento global já existente para `AnalysisDocumentNotFoundError`.
- Se a análise existir mas não for do tipo `CASE_ASSESSMENT`, a resposta HTTP deve seguir o mapeamento global já existente para `InconsistentAnalysisTypeError`.
- Em sucesso, o endpoint deve publicar exatamente um `CaseAssessmentCaseSummarizationTriggeredEvent` com o `analysis_id` da análise validada.
- Em sucesso, o endpoint deve persistir o status `ANALYZING_CASE` antes da publicação do evento.
- O fluxo chamador da sumarização deve validar que existe `AnalysisDocument` para a análise.
- O fluxo chamador da sumarização deve validar que a análise existe.
- O fluxo chamador da sumarização deve validar que `analysis.type` é `CASE_ASSESSMENT`.
- Antes de publicar o evento de sumarização, o fluxo chamador deve atualizar a análise para `CaseAssessmentAnalysisStatus.ANALYZING_CASE`.
- O job de sumarização deve buscar `AnalysisDocument` e `Analysis` por `analysis_id`.
- Se `AnalysisDocument` não existir, o job de sumarização deve falhar com `AnalysisDocumentNotFoundError`.
- Se `Analysis` não existir, o job de sumarização deve falhar com `AnalysisNotFoundError`.
- O job de sumarização deve extrair o conteúdo do documento via `GetDocumentContentUseCase` usando `GcsFileStorageProvider`, `PypdfPdfProvider` e `PythonDocxProvider`.
- O job de sumarização deve executar `AgnoSummarizeCaseAssessmentCaseWorkflow` para produzir e persistir `CaseSummary`.
- Após persistir `CaseSummary` com sucesso, o job de sumarização deve publicar `CaseSummaryFinishedEvent { analysis_id, account_id }`.
- Qualquer exceção não recuperável no job de sumarização deve atualizar a análise para `CaseAssessmentAnalysisStatus.FAILED` no `except` interno e também no `on_failure` do Inngest.
- O endpoint HTTP de trigger da geração da minuta deve ser `POST /intake/analyses/{analysis_id}/petition-drafts`.
- O endpoint de trigger da geração deve responder `202 Accepted` sem body quando a solicitação for aceita.
- O endpoint de trigger da geração deve depender de `IntakePipe.verify_analysis_by_account_from_request` para garantir que a análise pertença à conta autenticada.
- O endpoint de trigger da geração deve instanciar `TriggerPetitionDraftGenerationUseCase` e delegar a ele a validação de pré-condições e a publicação do evento.
- O endpoint de trigger da geração deve seguir o padrão já adotado pelos demais triggers assíncronos de `intake`: controller fino, sem body, retorno explícito de `Response(status_code=202)` e sem lógica de negócio embutida.
- Se a análise não pertencer à conta autenticada, a requisição de geração deve falhar no `IntakePipe.verify_analysis_by_account_from_request`, preservando o contrato de autorização já usado pelos demais endpoints de `analyses`.
- Se a análise não existir, a resposta HTTP da geração deve seguir o mapeamento global já existente para `AnalysisNotFoundError`.
- Se a análise existir mas não for do tipo `CASE_ASSESSMENT`, a resposta HTTP da geração deve seguir o mapeamento global já existente para `InconsistentAnalysisTypeError`.
- Se `CaseSummary` não existir, a resposta HTTP da geração deve seguir o mapeamento global já existente para `CaseSummaryUnavailableError`.
- Se não houver precedentes persistidos para a análise, a resposta HTTP da geração deve seguir o mapeamento global já existente para `AnalysisPrecedentsUnavailableError`.
- Se houver precedentes persistidos, mas nenhum com `is_chosen = True`, a resposta HTTP da geração deve seguir o mapeamento global já existente para `ChosenAnalysisPrecedentsRequiredError`.
- Em sucesso, o endpoint de geração deve publicar exatamente um `PetitionDraftGenerationTriggeredEvent` com o `analysis_id` da análise validada.
- O job de geração deve iniciar a partir de `PetitionDraftGenerationTriggeredEvent` contendo `analysis_id`.
- Ao iniciar, o job de geração deve atualizar a análise para `CaseAssessmentAnalysisStatus.GENERATING_PETITION_DRAFT` quando a análise existir.
- O job de geração deve buscar `CaseSummary` por `analysis_id`.
- Se `CaseSummary` não existir, o job de geração deve encerrar sem falha e sem publicar evento de conclusão.
- O job de geração deve buscar `AnalysisPrecedent` por `analysis_id`.
- Se não houver precedentes persistidos, o job de geração deve levantar `ChosenAnalysisPrecedentsRequiredError`.
- Se houver precedentes persistidos, mas nenhum com `is_chosen = True`, o job de geração deve levantar `ChosenAnalysisPrecedentsRequiredError`.
- O workflow de IA deve receber somente o `CaseSummary` e os precedentes escolhidos já persistidos.
- A minuta gerada deve conter as seções obrigatórias do PRD: fatos estruturados, fundamentos jurídicos, tese central, pedidos e citações dos precedentes com trechos destacados.
- Cada citação deve identificar o precedente de origem com tribunal, tipo e número.
- O texto deve preservar o caráter de sugestão e não afirmar mérito, estratégia obrigatória ou condução final do caso.
- A primeira geração deve persistir via `PetitionDraftsRepository.add(...)`.
- A regeração deve substituir a versão anterior via `PetitionDraftsRepository.replace(...)`.
- Em sucesso, `CreatePetitionDraftUseCase` deve definir status final `CaseAssessmentAnalysisStatus.DONE`.
- Após persistir com sucesso, o job de geração deve publicar `PetitionDraftGenerationFinishedEvent { analysis_id, account_id }`.
- Qualquer exceção não recuperável no job de geração deve atualizar a análise para `CaseAssessmentAnalysisStatus.FAILED` no `except` interno e também no `on_failure` do Inngest.

## 3.2 Não funcionais

- **Idempotência:** reexecuções do job de sumarização devem ser seguras porque `CreateCaseSummaryUseCase` já decide entre `add(...)` e `replace(...)`; reexecuções do job de geração não devem criar múltiplas minutas para a mesma análise, e `CreatePetitionDraftUseCase` deve usar `replace(...)` quando houver registro existente.
- **Resiliência:** o job de sumarização deve usar `retries=0` e `on_failure=SummarizeCaseAssessmentCaseJob._handle_failure`, alinhado ao padrão de sumarização; o job de geração deve usar `retries=2` e `on_failure=GeneratePetitionDraftJob._handle_failure`.
- **Observabilidade por estado persistido:** o app deve acompanhar evolução por status da análise e pelo relatório de `CASE_ASSESSMENT` já existente.
- **Segurança:** os endpoints de trigger de sumarização e de geração devem reutilizar a autorização já padronizada no módulo `intake` via `IntakePipe.verify_analysis_by_account_from_request`.
- **Evolução de contrato e persistência:** deve haver alteração coordenada de schema HTTP, DTO de domínio, model SQLAlchemy, mapper, repository e schema de banco para refletir os novos campos estruturados de `PetitionDraft`.
- **Compatibilidade de eventos:** o fluxo de sumarização de `CASE_ASSESSMENT` não deve reutilizar `CaseSummaryCaseSummarizationTriggeredEvent`, porque esse evento já é consumido por `SummarizeFirstInstanceCaseJob` e criaria disparos concorrentes indevidos.
- **Timeout de IA:** o agente de geração da minuta deve usar `timeout=60`, alinhado ao PRD e ao padrão dos agentes de intake.

# 4. O que já existe?

## Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) — entidade que normaliza `AnalysisType` e status por tipo de análise.
- **`AnalysisType`** (`src/animus/core/intake/domain/structures/analysis_type.py`) — structure que diferencia `CASE_ASSESSMENT`, `FIRST_INSTANCE` e `SECOND_INSTANCE`.
- **`CaseAssessmentAnalysisStatus`** (`src/animus/core/intake/domain/structures/case_assessment_analysis_status.py`) — já possui `ANALYZING_CASE`, `GENERATING_PETITION_DRAFT`, `DONE` e `FAILED`.
- **`CaseSummary`** (`src/animus/core/intake/domain/structures/case_summary.py`) — resumo estruturado usado como entrada do prompt da minuta.
- **`CaseSummaryDto`** (`src/animus/core/intake/domain/structures/dtos/case_summary_dto.py`) — DTO com `case_summary`, `legal_issue`, `central_question`, `requested_relief`, `key_facts`, `procedural_issues` e demais campos úteis ao prompt.
- **`AnalysisPrecedent`** (`src/animus/core/intake/domain/structures/analysis_precedent.py`) — structure dos precedentes classificados, incluindo `is_chosen`, `synthesis`, `applicability_level`, `legal_features` e `precedent`.
- **`PetitionDraft`** (`src/animus/core/intake/domain/structures/petition_draft.py`) — structure da minuta de petição, atualmente com `analysis_id` e `content`, devendo evoluir para campos estruturados persistidos.
- **`PetitionDraftDto`** (`src/animus/core/intake/domain/structures/dtos/petition_draft_dto.py`) — DTO atualmente com `analysis_id: str` e `content: str`, devendo evoluir para o novo contrato estruturado.
  - Novo contrato esperado: `analysis_id: str`, `structured_facts: str`, `legal_grounds: str`, `central_thesis: str`, `requests: list[str]`, `precedent_citations: list[str]`.
- **`ChosenAnalysisPrecedentsRequiredError`** (`src/animus/core/intake/domain/errors/chosen_analysis_precedents_required_error.py`) — erro de domínio para ausência de precedentes escolhidos.
- **`InconsistentAnalysisTypeError`** (`src/animus/core/intake/domain/errors/inconsistent_analysis_type_error.py`) — erro existente para tipo de análise incoerente.
- **`AnalysisDocumentNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_document_not_found_error.py`) — erro já usado quando a análise não possui documento persistido.
- **`AnalysisNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_not_found_error.py`) — erro já usado quando a análise não existe.
- **`PetitionDraftUnavailableError`** (`src/animus/core/intake/domain/errors/petition_draft_unavailable_error.py`) — erro já usado pelo relatório quando a minuta ainda não existe.
- **`CaseSummariesRepository`** (`src/animus/core/intake/interfaces/case_summaries_repository.py`) — port usado para obter e persistir `CaseSummary` por `analysis_id`.
- **`PetitionDraftsRepository`** (`src/animus/core/intake/interfaces/petition_drafts_repository.py`) — port existente com `find_by_analysis_id(...)`, `add(...)` e `replace(...)`.
- **`AnalysisPrecedentsRepository`** (`src/animus/core/intake/interfaces/analysis_precedents_repository.py`) — port usado para listar precedentes da análise.
- **`AnalysisDocumentsRepository`** (`src/animus/core/intake/interfaces/analysis_documents_repository.py`) — port usado para buscar documento da análise.
- **`AnalysesRepository`** (`src/animus/core/intake/interfaces/analyses_repository.py`) — port usado para buscar e substituir `Analysis`.
- **`SummarizeFirstInstanceCaseWorkflow`** (`src/animus/core/intake/interfaces/summarize_case_workflow.py`) — contrato existente de workflow que recebe `analysis_id` e `document_content: Text` e retorna `CaseSummaryDto`; serve de referência de interface e comportamento para o fluxo novo.
- **`CreateCaseSummaryUseCase`** (`src/animus/core/intake/use_cases/create_case_summary_use_case.py`) — use case existente que persiste `CaseSummary` e ajusta status conforme o tipo da análise.
- **`TriggerFirstInstanceCaseSummarizationUseCase`** (`src/animus/core/intake/use_cases/trigger_first_instance_case_summarization_use_case.py`) — referência para o padrão de trigger por evento, atualização prévia de status e publicação via `Broker`.
- **`CreateSecondInstanceJudgmentDraftUseCase`** (`src/animus/core/intake/use_cases/create_judgment_draft_use_case.py`) — referência análoga para persistência idempotente de minuta e transição para `DONE`.
- **`TriggerPetitionDraftGenerationUseCase`** (`src/animus/core/intake/use_cases/trigger_petition_draft_generation_use_case.py`) — valida pré-condições de `CASE_ASSESSMENT` antes da publicação do evento de geração da minuta.
- **`TriggerSecondInstanceJudgmentDraftGenerationUseCase`** (`src/animus/core/intake/use_cases/trigger_second_instance_judgment_draft_generation_use_case.py`) — referência para validação de pré-condições antes da publicação de evento assíncrono.
- **`UpdateAnalysisStatusUseCase`** (`src/animus/core/intake/use_cases/update_analysis_status_use_case.py`) — use case usado por jobs para atualizar status sem colocar regra em repositórios.
- **`GetCaseAssessmentAnalysisReportUseCase`** (`src/animus/core/intake/use_cases/get_case_assessment_analysis_report_use_case.py`) — já consome `PetitionDraftsRepository` e exige minuta para montar o relatório de `CASE_ASSESSMENT`.
- **`TriggerFirstInstanceCaseSummarizationController`** (`src/animus/rest/controllers/intake/trigger_first_instance_case_summarization_controller.py`) — referência principal para o padrão do controller HTTP de trigger assíncrono com `POST`, `202`, verificação de ownership e delegação direta ao use case.
- **`TriggerPetitionDraftGenerationController`** (`src/animus/rest/controllers/intake/trigger_petition_draft_generation_controller.py`) — endpoint HTTP de trigger para iniciar a geração ou regeração da minuta de petição inicial.
- **`TriggerSecondInstanceJudgmentDraftGenerationController`** (`src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_generation_controller.py`) — referência complementar para endpoint de trigger assíncrono específico por tipo de análise.

## Database

- **`SqlalchemyAnalysisDocumentsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/__init__.py`) — export já disponível para buscar o documento da análise.
- **`SqlalchemyCaseSummariesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/__init__.py`) — export já disponível para persistir e buscar `CaseSummary`.
- **`SqlalchemyAnalysisPrecedentsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/__init__.py`) — export já disponível para buscar precedentes escolhidos.
- **`SqlalchemyAnalysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/__init__.py`) — export já disponível para buscar conta da análise e atualizar status.
- **`PetitionDraftModel`** (`src/animus/database/sqlalchemy/models/intake/petition_draft_model.py`) — model existente da tabela `petition_drafts`.
- **`PetitionDraftMapper`** (`src/animus/database/sqlalchemy/mappers/intake/petition_draft_mapper.py`) — mapper existente entre `PetitionDraftModel` e `PetitionDraft`.
- **`SqlalchemyPetitionDraftsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_drafts_repository.py`) — implementação existente de `PetitionDraftsRepository`.
- **`Sqlalchemy.session()`** (`src/animus/database/sqlalchemy/sqlalchemy.py`) — escopo transacional usado por jobs Inngest.
- **Seeders da camada database:** não há `seeders` impactados em `src/animus/database/**/seeders/` e não há novos paths persistidos/gerados.

## AI

- **`AiPipe`** (`src/animus/pipes/ai_pipe.py`) — composition point dos workflows de IA; já possui `get_summarize_case_workflow(...)` e factory sem `Depends` para `get_generate_judgment_draft_workflow()`.
- **`AgnoSummarizeFirstInstanceCaseWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_summarize_first_instance_case_workflow.py`) — workflow existente usado apenas como referência estrutural para steps, integração com agente e persistência via `CreateCaseSummaryUseCase`.
- **`AgnoGenerateSecondInstanceJudgmentDraftWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_generate_second_instance_judgment_draft_workflow.py`) — principal referência para workflow Agno com `_StepNames`, `session_state`, step de montagem de prompt e normalização de output.
- **`IntakeSquad`** (`src/animus/ai/agno/squads/intake_squad.py`) — squad que concentra agentes do intake e já define agentes com `OpenAIChat`, `timeout=60` quando aplicável e `output_schema`.
- **`SecondInstanceJudgmentDraftOutput`** (`src/animus/ai/agno/outputs/intake/second_instance_judgment_draft_output.py`) — referência de output estruturado para normalização em DTO de domínio.

## Providers

- **`GcsFileStorageProvider`** (`src/animus/providers/storage`) — provider usado para obter o arquivo persistido da análise.
- **`PypdfPdfProvider`** (`src/animus/providers/storage`) — provider usado para leitura de PDF.
- **`PythonDocxProvider`** (`src/animus/providers/storage`) — provider usado para leitura de DOCX.
- **`GetDocumentContentUseCase`** (`src/animus/core/storage/use_cases/get_document_content_use_case.py`) — use case usado para extrair conteúdo textual do documento da análise.

## PubSub

- **`SummarizeSecondInstanceCaseJob`** (`src/animus/pubsub/inngest/jobs/intake/summarize_second_instance_case_job.py`) — referência principal de estrutura para job de sumarização: `publish_finished_event`, `except` + `on_failure`, `run_in_executor` e retorno de `{ analysis_id, account_id }`.
- **`SummarizeFirstInstanceCaseJob`** (`src/animus/pubsub/inngest/jobs/intake/summarize_first_instance_case_job.py`) — referência complementar para leitura de documento, `GetDocumentContentUseCase` e reuso do workflow de sumarização já persistente.
- **`GenerateSecondInstanceJudgmentDraftJob`** (`src/animus/pubsub/inngest/jobs/intake/generate_judgment_draft_job.py`) — referência principal para job de geração de minuta: `retries=2`, `on_failure`, `run_in_executor`, steps separados e idempotência via use case.
- **`InngestBroker`** (`src/animus/pubsub/inngest/inngest_broker.py`) — broker concreto para publicar eventos de domínio no Inngest.
- **`InngestJob`** (`src/animus/pubsub/inngest/inngest_job.py`) — helper para extrair payload original em `on_failure`.
- **`InngestPubSub.register_intake_jobs(...)`** (`src/animus/pubsub/inngest/inngest_pubsub.py`) — composition root onde os novos jobs devem ser registrados.

## Pipes

- **`DatabasePipe.get_petition_drafts_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP já existente para `PetitionDraftsRepository`; confirma que o repository concreto já está integrado ao projeto.

# 5. O que deve ser criado?

## Camada Core (Eventos de Domínio)

- **Localização:** `src/animus/core/intake/domain/events/case_assessment_case_summary_requested_event.py` (**novo arquivo**)
- **`name`:** `"intake/case_assessment.case_summary.triggered"`
- **Payload:** `analysis_id: str`
- **Métodos / factory:** `__init__(analysis_id: str) -> None` — cria evento dedicado para iniciar a sumarização de `CASE_ASSESSMENT` sem colidir com o trigger de `FIRST_INSTANCE`.

- **Localização:** `src/animus/core/intake/domain/events/petition_draft_generation_triggered_event.py` (**novo arquivo**)
- **`name`:** `"intake/petition_draft.generation.triggered"`
- **Payload:** `analysis_id: str`
- **Métodos / factory:** `__init__(analysis_id: str) -> None` — cria evento consumido pelo job de geração de minuta.

- **Localização:** `src/animus/core/intake/domain/events/petition_draft_generation_finished_event.py` (**novo arquivo**)
- **`name`:** `"intake/petition_draft.generation.finished"`
- **Payload:** `analysis_id: str`, `account_id: str`
- **Métodos / factory:** `__init__(analysis_id: str, account_id: str) -> None` — cria evento publicado após persistência bem-sucedida.

## Camada Core (Interfaces / Ports)

- **Localização:** `src/animus/core/intake/interfaces/generate_petition_draft_workflow.py` (**novo arquivo**)
- **Métodos:**
  - `run(analysis_id: str, case_summary: CaseSummary, precedents: list[AnalysisPrecedent]) -> PetitionDraftDto` — gera a minuta de petição inicial a partir de dados de domínio já persistidos, sem persistir e sem conhecer detalhes de Agno.

- **Localização:** `src/animus/core/intake/interfaces/summarize_case_workflow.py` (**arquivo existente**)
- **Métodos:**
  - Adicionar `SummarizeCaseAssessmentCaseWorkflow(Protocol)` com `run(analysis_id: str, document_content: Text) -> CaseSummaryDto` — sumariza o documento de `CASE_ASSESSMENT` com prompt e instruções próprias do contexto, sem conhecer persistência concreta.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/trigger_case_assessment_case_summarization_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `AnalysisDocumentsRepository`, `AnalysesRepository`, `Broker`
- **Método principal:** `execute(analysis_id: str) -> None` — valida pré-condições de sumarização de `CASE_ASSESSMENT`, marca a análise como `ANALYZING_CASE` e publica o evento de sumarização.
- **Responsabilidade de borda:** não recebe `Request`, `Response`, `Depends(...)` e não conhece detalhes de serialização HTTP.
- **Fluxo resumido:**
  - Normaliza `analysis_id` como `Id`.
  - Busca `AnalysisDocument` por `analysis_id`; se ausente, lança `AnalysisDocumentNotFoundError`.
  - Busca `Analysis`; se ausente, lança `AnalysisNotFoundError`.
  - Se `analysis.type.is_case_analysis.is_false`, lança `InconsistentAnalysisTypeError`.
  - Atualiza status com `analysis.set_status(CaseAssessmentAnalysisStatus.create_as_analyzing_case())`.
  - Persiste a análise via `AnalysesRepository.replace(analysis)`.
  - Publica `CaseAssessmentCaseSummarizationTriggeredEvent(analysis_id=analysis_id_entity.value)` via `Broker.publish(...)`.

- **Localização:** `src/animus/core/intake/use_cases/trigger_petition_draft_generation_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `AnalysesRepository`, `CaseSummariesRepository`, `AnalysisPrecedentsRepository`, `Broker`
- **Método principal:** `execute(analysis_id: str) -> None` — valida pré-condições da geração de minuta de `CASE_ASSESSMENT` e publica o evento de geração.
- **Responsabilidade de borda:** não recebe `Request`, `Response`, `Depends(...)` e não conhece detalhes de serialização HTTP.
- **Fluxo resumido:**
  - Normaliza `analysis_id` como `Id`.
  - Busca `Analysis`; se ausente, lança `AnalysisNotFoundError`.
  - Se `analysis.type.is_case_analysis.is_false`, lança `InconsistentAnalysisTypeError`.
  - Busca `CaseSummary` por `analysis_id`; se ausente, lança `CaseSummaryUnavailableError`.
  - Busca precedentes por `analysis_id`; se não houver itens, lança `AnalysisPrecedentsUnavailableError`.
  - Se não houver precedente com `is_chosen = True`, lança `ChosenAnalysisPrecedentsRequiredError`.
  - Publica `PetitionDraftGenerationTriggeredEvent(analysis_id=analysis_id_entity.value)` via `Broker.publish(...)`.

## Camada Rest (Controller HTTP)

- **Localização:** `src/animus/rest/controllers/intake/trigger_case_assessment_case_summarization_controller.py` (**novo arquivo**)
- **Método HTTP e path:** `POST /analyses/{analysis_id}/case-assessment-case-summaries`
- **Status de resposta:** `202 Accepted`
- **Body:** não recebe payload.
- **Assinatura esperada:** seguir o padrão de `TriggerFirstInstanceCaseSummarizationController` e `TriggerSecondInstanceCaseSummarizationController`.
- **Dependências:** `IntakePipe.verify_analysis_by_account_from_request`, `DatabasePipe.get_analysis_documents_repository_from_request`, `DatabasePipe.get_analyses_repository_from_request`, `PubSubPipe.get_broker_from_request`.
- **Fluxo resumido:**
  - Obtém `analysis` validada por ownership via `IntakePipe`.
  - Instancia `TriggerCaseAssessmentCaseSummarizationUseCase`.
  - Chama `use_case.execute(analysis_id=analysis.id.value)`.
  - Retorna `Response(status_code=202)`.
- **Erros esperados:** o controller não deve capturar nem traduzir erros manualmente; deve deixar o tratamento global do app converter exceções de domínio e autorização em respostas HTTP.

- **Localização:** `src/animus/rest/controllers/intake/trigger_petition_draft_generation_controller.py` (**novo arquivo**)
- **Método HTTP e path:** `POST /analyses/{analysis_id}/petition-drafts`
- **Status de resposta:** `202 Accepted`
- **Body:** não recebe payload.
- **Assinatura esperada:** seguir o padrão de `TriggerSecondInstanceJudgmentDraftGenerationController`.
- **Dependências:** `IntakePipe.verify_analysis_by_account_from_request`, `DatabasePipe.get_analyses_repository_from_request`, `DatabasePipe.get_case_summaries_repository_from_request`, `DatabasePipe.get_analysis_precedents_repository_from_request`, `PubSubPipe.get_broker_from_request`.
- **Fluxo resumido:**
  - Obtém `analysis` validada por ownership via `IntakePipe`.
  - Instancia `TriggerPetitionDraftGenerationUseCase`.
  - Chama `use_case.execute(analysis_id=analysis.id.value)`.
  - Retorna `Response(status_code=202)`.
- **Erros esperados:** o controller não deve capturar nem traduzir erros manualmente; deve deixar o tratamento global do app converter exceções de domínio e autorização em respostas HTTP.

- **Localização:** `src/animus/core/intake/use_cases/create_petition_draft_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `PetitionDraftsRepository`, `AnalysesRepository`
- **Método principal:** `execute(analysis_id: str, dto: PetitionDraftDto) -> PetitionDraftDto` — cria ou substitui a minuta da análise e conclui o status de `CASE_ASSESSMENT`.
- **Fluxo resumido:**
  - Normaliza `analysis_id` como `Id`.
  - Normaliza `dto` para garantir que `dto.analysis_id` corresponda ao `analysis_id` recebido.
  - Cria `PetitionDraft` via `PetitionDraft.create(normalized_dto)`.
  - Busca minuta existente com `PetitionDraftsRepository.find_by_analysis_id(analysis_id_entity)`.
  - Se inexistente, chama `PetitionDraftsRepository.add(petition_draft)`.
  - Se existente, chama `PetitionDraftsRepository.replace(petition_draft)`.
  - Busca `Analysis` com `AnalysesRepository.find_by_id(analysis_id_entity)`; se ausente, lança `AnalysisNotFoundError`.
  - Se `analysis.type.is_case_analysis.is_false`, lança `InconsistentAnalysisTypeError`.
  - Atualiza status com `analysis.set_status(CaseAssessmentAnalysisStatus.create_as_done())`.
  - Persiste a análise com `AnalysesRepository.replace(analysis)`.
  - Retorna `petition_draft.dto`.

## Camada AI (Outputs Agno)

- **Localização:** `src/animus/ai/agno/outputs/intake/petition_draft_output.py` (**novo arquivo**)
- **Tipo:** `BaseModel`
- **Atributos:**
  - `structured_facts: str`
  - `legal_grounds: str`
  - `central_thesis: str`
  - `requests: list[str]`
  - `precedent_citations: list[str]`

## Camada Core (DTOs / Structures)

- **Localização:** `src/animus/core/intake/domain/structures/dtos/petition_draft_dto.py`
- **Mudança:** substituir `content: str` por `structured_facts: str`, `legal_grounds: str`, `central_thesis: str`, `requests: list[str]` e `precedent_citations: list[str]`.
- **Justificativa:** o contrato público da minuta deve refletir explicitamente as seções obrigatórias.

- **Localização:** `src/animus/core/intake/domain/structures/petition_draft.py`
- **Mudança:** substituir o campo `content` pelos mesmos atributos estruturados definidos no DTO.
- **Justificativa:** manter a `Structure` aderente ao contrato do domínio e à persistência.

## Camada AI (Workflow de Sumarização)

- **Localização:** `src/animus/ai/agno/workflows/intake/agno_summarize_case_assessment_case_workflow.py` (**novo arquivo**)
- **Interface implementada:** `SummarizeCaseAssessmentCaseWorkflow`
- **Dependências:** nenhuma dependência de banco; instancia `IntakeSquad` no construtor e reutiliza `CreateCaseSummaryUseCase` via composição equivalente aos workflows de sumarização já existentes.
- **Métodos:**
  - `__init__(...) -> None` — configura dependências de agente e steps do workflow.
  - `run(analysis_id: str, document_content: str) -> CaseSummaryDto` — executa o fluxo de sumarização com prompt específico para `CASE_ASSESSMENT`.
  - `_build_case_assessment_summary_input_step(...) -> StepOutput` — prepara a entrada textual do agente com foco no contexto de `CASE_ASSESSMENT`.
  - `_normalize_case_assessment_summary_output(...) -> CaseSummaryDto` — valida e adapta a saída estruturada do agente para o `CaseSummaryDto` esperado pelo domínio.

## Camada AI (Workflows Agno)

- **Localização:** `src/animus/ai/agno/workflows/intake/agno_generate_petition_draft_workflow.py` (**novo arquivo**)
- **Interface implementada:** `GeneratePetitionDraftWorkflow`
- **Dependências:** nenhuma dependência de banco; instancia `IntakeSquad` no construtor.
- **Métodos:**
  - `__init__() -> None` — cria `IntakeSquad` e `_StepNames`.
  - `run(analysis_id: str, case_summary: CaseSummary, precedents: list[AnalysisPrecedent]) -> PetitionDraftDto` — monta `agno.Workflow`, executa os steps e normaliza `PetitionDraftOutput` para o novo `PetitionDraftDto` estruturado.
  - `_build_petition_draft_input_step(_: StepInput, run_context: RunContext) -> StepOutput` — valida `session_state`, transforma `CaseSummary` e precedentes escolhidos em prompt textual para o agente.
  - `_normalize_petition_draft_output(output: object, analysis_id: str) -> PetitionDraftDto` — valida `PetitionDraftOutput` e preenche explicitamente os campos estruturados persistidos.

## Camada PubSub (Jobs Inngest)

- **Localização:** `src/animus/pubsub/inngest/jobs/intake/summarize_case_assessment_case_job.py` (**novo arquivo**)
- **Evento consumido:** `CaseAssessmentCaseSummarizationTriggeredEvent.name`
- **Dependências:** `SqlalchemyAnalysisDocumentsRepository`, `SqlalchemyCaseSummariesRepository`, `SqlalchemyAnalysesRepository`, `GetDocumentContentUseCase`, `GcsFileStorageProvider`, `PypdfPdfProvider`, `PythonDocxProvider`, `AiPipe.get_summarize_case_assessment_case_workflow()`, `UpdateAnalysisStatusUseCase`, `InngestBroker`.
- **Passos (`step.run`):**
  - `normalize_payload` — normaliza `analysis_id` do evento.
  - `summarize_case` — carrega análise e documento, extrai conteúdo, executa workflow de sumarização e retorna `{ analysis_id, account_id }`.
  - `publish_finished_event` — publica `CaseSummaryFinishedEvent` quando a sumarização persistir com sucesso.
  - `mark_analysis_as_failed` — em exceções não tratadas, atualiza status para `FAILED` e executa `session.commit()`.
- **Métodos internos:**
  - `handle(inngest: Inngest) -> Any` — registra função com `fn_id='summarize-case-assessment-case'`, `trigger=TriggerEvent(event=CaseAssessmentCaseSummarizationTriggeredEvent.name)`, `retries=0` e `on_failure=SummarizeCaseAssessmentCaseJob._handle_failure`.
  - `_normalize_payload(data: dict[str, Any]) -> dict[str, str]` — retorna `{'analysis_id': str(data['analysis_id'])}`.
  - `_summarize_case(payload: _Payload) -> dict[str, str]` — delega execução síncrona via `run_in_executor`.
  - `_summarize_case_sync(payload: _Payload) -> dict[str, str]` — busca `AnalysisDocument` e `Analysis`, extrai conteúdo, instancia `AgnoSummarizeCaseAssessmentCaseWorkflow`, persiste `CaseSummary` e retorna `{ analysis_id, account_id }`.
  - `_mark_analysis_as_failed(payload: _Payload) -> None` — delega execução síncrona via `run_in_executor`.
  - `_mark_analysis_as_failed_sync(payload: _Payload) -> None` — busca análise e, se existir, aplica `CaseAssessmentAnalysisStatus.create_as_failed()`.
  - `_handle_failure(context: Context) -> None` — extrai payload original via `get_event_data_from_context_failure(...)`, normaliza e reforça status `FAILED`.
- **Idempotência:** o job reutiliza `CreateCaseSummaryUseCase` via `AgnoSummarizeCaseAssessmentCaseWorkflow`, que já decide entre `add(...)` e `replace(...)`.

- **Localização:** `src/animus/pubsub/inngest/jobs/intake/generate_petition_draft_job.py` (**novo arquivo**)
- **Evento consumido:** `PetitionDraftGenerationTriggeredEvent.name`
- **Dependências:** `SqlalchemyAnalysesRepository`, `SqlalchemyCaseSummariesRepository`, `SqlalchemyAnalysisPrecedentsRepository`, `SqlalchemyPetitionDraftsRepository`, `AiPipe.get_generate_petition_draft_workflow()`, `CreatePetitionDraftUseCase`, `UpdateAnalysisStatusUseCase`, `InngestBroker`.
- **Passos (`step.run`):**
  - `normalize_payload` — normaliza `analysis_id` do evento.
  - `mark_analysis_as_generating_petition_draft` — atualiza status para `GENERATING_PETITION_DRAFT` e executa `session.commit()`.
  - `generate_and_persist_petition_draft` — busca `CaseSummary`, precedentes escolhidos e análise; executa workflow; persiste minuta; conclui status `DONE`; executa `session.commit()`; retorna `{ analysis_id, account_id }` ou `None` se `CaseSummary` não existir.
  - `publish_finished_event` — publica `PetitionDraftGenerationFinishedEvent` quando o step anterior retornar payload.
  - `mark_analysis_as_failed` — em exceções não tratadas, atualiza status para `FAILED` e executa `session.commit()`.
- **Métodos internos:**
  - `handle(inngest: Inngest) -> Any` — registra função com `fn_id='generate-petition-draft'`, `trigger=TriggerEvent(event=PetitionDraftGenerationTriggeredEvent.name)`, `retries=2` e `on_failure=GeneratePetitionDraftJob._handle_failure`.
  - `_normalize_payload(data: dict[str, Any]) -> dict[str, str]` — retorna `{'analysis_id': str(data['analysis_id'])}`.
  - `_mark_analysis_as_generating_petition_draft(payload: _Payload) -> None` — delega execução síncrona via `run_in_executor`.
  - `_mark_analysis_as_generating_petition_draft_sync(payload: _Payload) -> None` — busca análise e, se existir, aplica `CaseAssessmentAnalysisStatus.create_as_generating_petition_draft()`.
  - `_generate_and_persist_petition_draft(payload: _Payload) -> dict[str, str] | None` — delega execução síncrona via `run_in_executor`.
  - `_generate_and_persist_petition_draft_sync(payload: _Payload) -> dict[str, str] | None` — monta repositories, valida dados mínimos, chama workflow e `CreatePetitionDraftUseCase`.
  - `_mark_analysis_as_failed(payload: _Payload) -> None` — delega execução síncrona via `run_in_executor`.
  - `_mark_analysis_as_failed_sync(payload: _Payload) -> None` — busca análise e, se existir, aplica `CaseAssessmentAnalysisStatus.create_as_failed()`.
  - `_handle_failure(context: Context) -> None` — extrai payload original via `get_event_data_from_context_failure(...)`, normaliza e reforça status `FAILED`.
- **Idempotência:** `CreatePetitionDraftUseCase` decide entre `add(...)` e `replace(...)`; reentregas do Inngest substituem a minuta anterior sem duplicidade.

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/events/__init__.py`
- **Mudança:** exportar `CaseAssessmentCaseSummarizationTriggeredEvent`, `PetitionDraftGenerationTriggeredEvent` e `PetitionDraftGenerationFinishedEvent` em imports e `__all__`.
- **Justificativa:** manter eventos públicos disponíveis para jobs, brokers e fluxos futuros.

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudança:** exportar `GeneratePetitionDraftWorkflow` e `SummarizeCaseAssessmentCaseWorkflow`, ambos importados a partir dos módulos alinhados ao padrão atual de interfaces.
- **Justificativa:** seguir o padrão de contratos públicos do contexto `intake`.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** exportar `TriggerCaseAssessmentCaseSummarizationUseCase`, `TriggerPetitionDraftGenerationUseCase` e `CreatePetitionDraftUseCase`.
- **Justificativa:** manter consistência com os demais use cases públicos.

## Rest

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** exportar `TriggerCaseAssessmentCaseSummarizationController` e `TriggerPetitionDraftGenerationController`.
- **Justificativa:** manter o controller público no pacote de intake, alinhado aos demais endpoints.

- **Arquivo:** `src/animus/rest/controllers/intake/trigger_case_assessment_case_summarization_controller.py`
- **Mudança:** implementar controller síncrono com `@router.post('/analyses/{analysis_id}/case-assessment-case-summaries', status_code=202)` seguindo o padrão dos demais triggers de intake.
- **Justificativa:** expor o gatilho HTTP de ponta a ponta sem mover regra de negócio para a borda.

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** registrar `TriggerCaseAssessmentCaseSummarizationController.handle(router)` e `TriggerPetitionDraftGenerationController.handle(router)`.
- **Justificativa:** tornar o endpoint acessível na composição HTTP do módulo de análises.

## AI

- **Arquivo:** `src/animus/ai/agno/squads/intake_squad.py`
- **Mudança:** adicionar propriedade `petition_draft_generator_agent(self) -> Agent` com `OpenAIChat`, `timeout=60`, `temperature=0` e `output_schema=PetitionDraftOutput`.
- **Justificativa:** centralizar o agente de geração de minuta no squad de intake.

- **Arquivo:** `src/animus/ai/agno/outputs/intake/__init__.py`
- **Mudança:** exportar `PetitionDraftOutput`.
- **Justificativa:** manter o contrato público dos outputs de intake.

- **Arquivo:** `src/animus/ai/agno/workflows/intake/__init__.py`
- **Mudança:** exportar `AgnoGeneratePetitionDraftWorkflow` e `AgnoSummarizeCaseAssessmentCaseWorkflow`.
- **Justificativa:** manter composição pública dos workflows Agno de intake.

## Pipes

- **Arquivo:** `src/animus/pipes/ai_pipe.py`
- **Mudança:** adicionar `get_generate_petition_draft_workflow() -> GeneratePetitionDraftWorkflow`, importando `AgnoGeneratePetitionDraftWorkflow` dentro do método e retornando a interface do `core`.
- **Justificativa:** jobs não usam `Depends`; o pipe deve funcionar como factory estática, seguindo `get_generate_judgment_draft_workflow()`.

- **Arquivo:** `src/animus/pipes/ai_pipe.py`
- **Mudança:** adicionar `get_summarize_case_assessment_case_workflow() -> SummarizeCaseAssessmentCaseWorkflow`, importando `AgnoSummarizeCaseAssessmentCaseWorkflow` dentro do método e retornando a interface do `core`.
- **Justificativa:** manter o workflow de sumarização específico acessível ao job sem depender de `Depends`.

## PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/__init__.py`
- **Mudança:** exportar `SummarizeCaseAssessmentCaseJob` e `GeneratePetitionDraftJob`, sem expor job intermediário de trigger da geração.
- **Justificativa:** disponibilizar os jobs para o composition root do Inngest.

- **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
- **Mudança:** importar `SummarizeCaseAssessmentCaseJob` e `GeneratePetitionDraftJob`, registrando ambos em `register_intake_jobs(...)`, sem registrar job intermediário de trigger da geração.
- **Justificativa:** tornar os jobs executáveis pelo Inngest.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/petition_draft_model.py`
- **Mudança:** substituir a coluna `content` pelas colunas `structured_facts`, `legal_grounds`, `central_thesis`, `requests` e `precedent_citations`.
- **Justificativa:** o contrato persistido de `PetitionDraft` passa a refletir explicitamente as seções obrigatórias da minuta.

- **Arquivo:** `src/animus/database/sqlalchemy/mappers/intake/petition_draft_mapper.py`
- **Mudança:** mapear os novos campos estruturados entre `PetitionDraftModel` e `PetitionDraft`.
- **Justificativa:** manter a tradução domínio <-> persistência aderente ao novo contrato.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_drafts_repository.py`
- **Mudança:** atualizar `add(...)` e `replace(...)` para persistir e substituir todos os novos campos.
- **Justificativa:** garantir idempotência sem perder granularidade do novo schema.

- **Arquivo:** `migrations/versions/<nova_migration_petition_draft_estruturado>.py`
- **Mudança:** criar migration para substituir `content` por `structured_facts`, `legal_grounds`, `central_thesis`, `requests` e `precedent_citations` na tabela `petition_drafts`.
- **Justificativa:** a mudança de contrato exige evolução explícita do schema do banco.

## Testes

- **Arquivo:** `tests/rest/controllers/intake/test_trigger_case_assessment_case_summarization_controller.py` (**novo arquivo**)
- **Mudança:** criar testes de integração do endpoint HTTP de trigger.
- **Cenários mínimos obrigatórios:**
  - retorna `202`, publica `CaseAssessmentCaseSummarizationTriggeredEvent` e persiste `ANALYZING_CASE` quando a análise `CASE_ASSESSMENT` possui documento;
  - retorna o status HTTP mapeado para `AnalysisDocumentNotFoundError` quando o documento não existir;
  - retorna o status HTTP mapeado para `InconsistentAnalysisTypeError` quando a análise não for `CASE_ASSESSMENT`;
  - não publica evento quando qualquer pré-condição falhar.
- **Justificativa:** garantir o contrato de ponta a ponta do endpoint desde a borda HTTP até a publicação do evento.

- **Arquivo:** `tests/rest/controllers/intake/test_trigger_petition_draft_generation_controller.py` (**novo arquivo**)
- **Mudança:** criar testes de integração do endpoint HTTP de trigger da geração da minuta.
- **Cenários mínimos obrigatórios:**
  - retorna `202` e publica `PetitionDraftGenerationTriggeredEvent` quando a análise `CASE_ASSESSMENT` possui `CaseSummary` e precedente escolhido;
  - retorna o status HTTP mapeado para `CaseSummaryUnavailableError` quando o resumo não existir;
  - retorna o status HTTP mapeado para `AnalysisPrecedentsUnavailableError` quando não houver precedentes persistidos;
  - retorna o status HTTP mapeado para `ChosenAnalysisPrecedentsRequiredError` quando não houver precedente escolhido;
  - retorna o status HTTP mapeado para `InconsistentAnalysisTypeError` quando a análise não for `CASE_ASSESSMENT`;
  - não publica evento quando qualquer pré-condição falhar.
- **Justificativa:** garantir o contrato de ponta a ponta do endpoint de geração desde a borda HTTP até a publicação do evento.

# 7. O que deve ser removido?

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/trigger_petition_draft_generation_job.py`
- **Mudança:** remover o job intermediário que observava `CaseSummaryFinishedEvent` apenas para republicar `PetitionDraftGenerationTriggeredEvent`.
- **Justificativa:** o trigger da geração passa a ser explícito por endpoint HTTP dedicado, mantendo o mesmo padrão dos demais gatilhos assíncronos de `intake`.

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** criar `CaseAssessmentCaseSummarizationTriggeredEvent` em vez de reutilizar `CaseSummaryCaseSummarizationTriggeredEvent`.
- **Alternativas consideradas:** reutilizar `CaseSummaryCaseSummarizationTriggeredEvent` com um segundo consumer; adicionar `analysis_type` ao payload do evento existente.
- **Motivo da escolha:** hoje `SummarizeFirstInstanceCaseJob` já consome `CaseSummaryCaseSummarizationTriggeredEvent` sem filtro por tipo; reutilizar o mesmo evento faria dois jobs reagirem ao mesmo trigger. Alterar o payload do evento existente ampliaria contrato já usado por `FIRST_INSTANCE`.
- **Impactos / trade-offs:** adiciona mais um evento no domínio, mas evita regressão e mantém isolamento claro entre pipelines assíncronos.

- **Decisão:** criar `AgnoSummarizeCaseAssessmentCaseWorkflow` específico para `CASE_ASSESSMENT`.
- **Alternativas consideradas:** reutilizar `AgnoSummarizeFirstInstanceCaseWorkflow` mudando apenas o gatilho do job.
- **Motivo da escolha:** `CASE_ASSESSMENT` e `FIRST_INSTANCE` representam contextos de análise distintos no domínio, e a sumarização deve poder evoluir com prompt e foco semântico próprios.
- **Impactos / trade-offs:** adiciona um workflow novo e mais wiring no `AiPipe`, mas elimina ambiguidade semântica e reduz acoplamento indevido entre fluxos.

- **Decisão:** expor o trigger de geração da minuta por endpoint HTTP dedicado, em vez de depender de um job intermediário acionado por `CaseSummaryFinishedEvent`.
- **Alternativas consideradas:** manter o encadeamento automático por job após `CaseSummaryFinishedEvent`; acoplar o disparo da geração ao job de sumarização.
- **Motivo da escolha:** o endpoint explicita a intenção do usuário, permite reexecução controlada da geração e alinha `CASE_ASSESSMENT` ao padrão já adotado pelos demais triggers assíncronos de `intake`.
- **Impactos / trade-offs:** aumenta a superfície HTTP do módulo `intake`, mas elimina uma etapa intermediária no Inngest e melhora previsibilidade operacional.

- **Decisão:** `CreatePetitionDraftUseCase.execute(...)` retorna `PetitionDraftDto`.
- **Alternativas consideradas:** retornar `None`, como descrito no esboço do Jira.
- **Motivo da escolha:** os use cases análogos de criação no contexto retornam DTO, como `CreateCaseSummaryUseCase` e `CreateSecondInstanceJudgmentDraftUseCase`; manter o retorno preserva consistência interna e facilita reuso futuro.
- **Impactos / trade-offs:** o job não precisa usar o retorno; a diferença em relação ao esboço não altera o comportamento funcional.

- **Decisão:** substituir `PetitionDraftDto.content` por campos estruturados persistidos no domínio e no banco.
- **Alternativas consideradas:** manter `content: str` como campo único; persistir apenas o texto final e usar estrutura apenas no output temporário do agente.
- **Motivo da escolha:** o PRD exige seções obrigatórias e o novo requisito pede que esses campos existam como atributos do `PetitionDraft`, não apenas como convenção textual.
- **Impactos / trade-offs:** amplia o impacto da mudança para DTO, schema HTTP, model SQLAlchemy, mapper, repository e migration, mas elimina ambiguidade sobre a presença das seções obrigatórias.

- **Decisão:** expor o trigger de sumarização de `CASE_ASSESSMENT` por endpoint HTTP dedicado, em vez de reaproveitar `POST /analyses/{analysis_id}/case-summaries`.
- **Alternativas consideradas:** reutilizar o endpoint já usado por `FIRST_INSTANCE` e variar apenas a validação de tipo internamente.
- **Motivo da escolha:** o fluxo passa a ter evento, workflow e semântica próprios; um endpoint dedicado reduz ambiguidade contratual e facilita observabilidade, testes e evolução independente.
- **Impactos / trade-offs:** aumenta a superfície HTTP do módulo `intake`, mas evita acoplamento implícito entre dois gatilhos de domínio diferentes.

- **Decisão:** o job de geração retorna `None` quando `CaseSummary` não existe e não publica evento de conclusão.
- **Alternativas consideradas:** lançar `CaseSummaryUnavailableError` e marcar a análise como `FAILED`.
- **Motivo da escolha:** o Jira exige encerramento sem falha quando `CaseSummary` não existir; a validação de pré-condição deve acontecer antes da publicação do evento pelo fluxo chamador.
- **Impactos / trade-offs:** em evento inconsistente publicado fora do fluxo esperado, a análise pode não receber evento de conclusão; isso evita falso negativo operacional por dado ausente.

- **Decisão:** usar `InconsistentAnalysisTypeError` se `CreatePetitionDraftUseCase`, o trigger da sumarização ou o trigger da geração receberem análise que não seja `CASE_ASSESSMENT`.
- **Alternativas consideradas:** criar `CaseAssessmentAnalysisRequiredError`.
- **Motivo da escolha:** já existe erro de domínio para tipo incoerente e o ticket não exige um erro novo.
- **Impactos / trade-offs:** a mensagem é menos específica do que um erro dedicado, mas evita ampliar o contrato de erros sem necessidade.

# 9. Diagramas e Referências

- **Fluxo HTTP completo do trigger:**

```text
POST /intake/analyses/{analysis_id}/case-assessment-case-summaries
  -> IntakePipe.verify_analysis_by_account_from_request
  -> TriggerCaseAssessmentCaseSummarizationController.handle(...)
  -> TriggerCaseAssessmentCaseSummarizationUseCase.execute(analysis_id)
  -> AnalysisDocumentsRepository.find_by_analysis_id(...)
  -> AnalysesRepository.find_by_id(...)
  -> AnalysesRepository.replace(... ANALYZING_CASE ...)
  -> Broker.publish(CaseAssessmentCaseSummarizationTriggeredEvent)
  -> HTTP 202
```

- **Fluxo HTTP completo do trigger da geração:**

```text
POST /intake/analyses/{analysis_id}/petition-drafts
  -> IntakePipe.verify_analysis_by_account_from_request
  -> TriggerPetitionDraftGenerationController.handle(...)
  -> TriggerPetitionDraftGenerationUseCase.execute(analysis_id)
  -> AnalysesRepository.find_by_id(...)
  -> CaseSummariesRepository.find_by_analysis_id(...)
  -> AnalysisPrecedentsRepository.find_many_by_analysis_id(...)
  -> Broker.publish(PetitionDraftGenerationTriggeredEvent)
  -> HTTP 202
```

- **Fluxo de sumarização:**

```text
TriggerCaseAssessmentCaseSummarizationUseCase.execute(analysis_id)
  -> AnalysesRepository.replace(... ANALYZING_CASE ...)
  -> Broker.publish(CaseAssessmentCaseSummarizationTriggeredEvent)
  -> Inngest
  -> SummarizeCaseAssessmentCaseJob.handle(...)
  -> normalize_payload
  -> summarize_case
  -> SqlalchemyAnalysisDocumentsRepository.find_by_analysis_id(...)
  -> GetDocumentContentUseCase.execute(file_path)
  -> AgnoSummarizeCaseAssessmentCaseWorkflow.run(...)
  -> CreateCaseSummaryUseCase.execute(...)
  -> PostgreSQL case_summaries + analyses.status
  -> publish_finished_event
  -> InngestBroker.publish(CaseSummaryFinishedEvent)
```

- **Fluxo de geração da minuta:**

```text
POST /intake/analyses/{analysis_id}/petition-drafts
  -> TriggerPetitionDraftGenerationUseCase.execute(analysis_id)
  -> Broker.publish(PetitionDraftGenerationTriggeredEvent)
  -> PetitionDraftGenerationTriggeredEvent { analysis_id }
  -> Inngest
  -> GeneratePetitionDraftJob.handle(...)
  -> normalize_payload
  -> mark_analysis_as_generating_petition_draft
  -> SqlalchemyAnalysesRepository
  -> PostgreSQL analyses.status = GENERATING_PETITION_DRAFT
  -> generate_and_persist_petition_draft
  -> SqlalchemyCaseSummariesRepository.find_by_analysis_id(...)
  -> SqlalchemyAnalysisPrecedentsRepository.find_many_by_analysis_id(...)
  -> chosen_precedents = [precedent where is_chosen]
  -> AiPipe.get_generate_petition_draft_workflow()
  -> AgnoGeneratePetitionDraftWorkflow.run(...)
  -> CreatePetitionDraftUseCase.execute(...)
  -> SqlalchemyPetitionDraftsRepository.add(...) or replace(...)
  -> SqlalchemyAnalysesRepository.replace(... DONE ...)
  -> PostgreSQL petition_drafts + analyses.status
  -> publish_finished_event
  -> InngestBroker.publish(PetitionDraftGenerationFinishedEvent)
```

- **Fluxo de falha:**

```text
SummarizeCaseAssessmentCaseJob
  -> exception in step
  -> mark_analysis_as_failed
  -> SqlalchemyAnalysesRepository.replace(... FAILED ...)
  -> raise
  -> Inngest on_failure
  -> _handle_failure
  -> mark_analysis_as_failed

GeneratePetitionDraftJob
  -> exception in step
  -> mark_analysis_as_failed
  -> SqlalchemyAnalysesRepository.replace(... FAILED ...)
  -> raise
  -> Inngest retries=2
  -> on_failure
  -> _handle_failure
  -> mark_analysis_as_failed
```

- **Referências:**
- `src/animus/pubsub/inngest/jobs/intake/summarize_second_instance_case_job.py` — referência principal de estrutura para o job de sumarização.
- `src/animus/pubsub/inngest/jobs/intake/summarize_first_instance_case_job.py` — referência para extração do conteúdo do documento e execução do workflow de sumarização.
- `src/animus/pubsub/inngest/jobs/intake/generate_judgment_draft_job.py` — referência principal de estrutura do job de geração.
- `src/animus/ai/agno/workflows/intake/agno_summarize_first_instance_case_workflow.py` — referência estrutural para o novo workflow de sumarização dedicado.
- `src/animus/ai/agno/workflows/intake/agno_generate_second_instance_judgment_draft_workflow.py` — referência para workflow Agno com prompt e normalização.
- `src/animus/ai/agno/squads/intake_squad.py` — referência para criação de agentes com `output_schema`.
- `src/animus/core/intake/use_cases/trigger_first_instance_case_summarization_use_case.py` — referência para trigger por evento com atualização prévia de status.
- `src/animus/rest/controllers/intake/trigger_first_instance_case_summarization_controller.py` — referência principal para o formato do endpoint HTTP de trigger com `202`.
- `src/animus/core/intake/use_cases/trigger_petition_draft_generation_use_case.py` — referência para validação de pré-condições antes da publicação do evento de geração da minuta.
- `src/animus/rest/controllers/intake/trigger_petition_draft_generation_controller.py` — referência principal para o formato do endpoint HTTP de geração da minuta com `202`.
- `tests/rest/controllers/intake/test_trigger_case_summary_controller.py` — referência principal para o padrão de teste end-to-end do endpoint de trigger.
- `tests/rest/controllers/intake/test_trigger_case_summary_controller.py` — referência principal para o padrão de teste do endpoint HTTP de trigger.
- `src/animus/core/intake/use_cases/create_case_summary_use_case.py` — referência para persistência idempotente do resumo do caso.
- `src/animus/core/intake/use_cases/create_judgment_draft_use_case.py` — referência para persistência idempotente de minuta e status `DONE`.
- `src/animus/core/intake/domain/events/case_summary_finished_event.py` — referência de evento de conclusão com `analysis_id` e `account_id`.
- `src/animus/core/intake/domain/events/petition_draft_generation_triggered_event.py` — referência de evento de trigger com `analysis_id`.

# 10. Pendências / Dúvidas

Sem pendências.

## Restrições

- O `core` não deve depender de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest`, `Agno` ou qualquer detalhe de infraestrutura.
- Os jobs podem montar repositories concretos e controlar `session.commit()` por etapa, seguindo o padrão atual de jobs Inngest.
- Alterar `PetitionDraft` e `PetitionDraftDto` para refletir os campos estruturados persistidos.
- Criar migration de banco para evoluir a tabela `petition_drafts`.
- Não reutilizar `CaseSummaryCaseSummarizationTriggeredEvent` no job de `CASE_ASSESSMENT`.
- Não publicar evento de conclusão da geração quando `CaseSummary` estiver ausente.
- Toda instanciação concreta de workflow deve passar por `AiPipe`.
