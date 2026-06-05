---
title: Descrição da decisão do juiz na análise de 2ª instância
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AQDxAg
ticket: N/A
status: open
last_updated_at: 2026-06-04
---

# 1. Objetivo

Implementar a etapa de submissão da decisão pretendida pelo juiz no fluxo `SECOND_INSTANCE`, persistindo uma `SecondInstanceDecision` 1:1 por análise antes da busca de precedentes. A descrição deve atualizar o status da análise para `DECISION_SUBMITTED`, bloquear busca de precedentes enquanto ausente, ser adicionada como contexto após a recuperação vetorial dos precedentes para orientar a síntese/classificação e a geração/regeração da minuta de acórdão, além de compor o relatório de 2ª instância retornado pela API.

# 2. Escopo

## 2.1 In-scope

- Criar `SecondInstanceDecisionDto` e `SecondInstanceDecision` no `core/intake`.
- Criar persistência 1:1 na tabela `second_instance_decisions`, vinculada a `analyses.id` por `analysis_id`.
- Criar `SecondInstanceDecisionsRepository` e implementação SQLAlchemy.
- Criar endpoint `POST /intake/analyses/{analysis_id}/second-instance-decision` para submissão e ressubmissão.
- Criar endpoint `GET /intake/analyses/{analysis_id}/second-instance-decision` para leitura.
- Adicionar o status `DECISION_SUBMITTED` em `SecondInstanceAnalysisStatusValue` entre `CASE_ANALYZED` e `SEARCHING_PRECEDENTS`.
- Atualizar a submissão para validar que a análise é `SECOND_INSTANCE` e pertence à conta autenticada.
- Validar `description` como texto obrigatório e não vazio após `strip()`.
- Fazer ressubmissões substituírem a decisão anterior e atualizarem o status para `DECISION_SUBMITTED` sem remover precedentes ou minuta já persistidos.
- Exigir decisão persistida antes de publicar o evento de busca de precedentes para análises `SECOND_INSTANCE`.
- Manter a recuperação vetorial de precedentes baseada no `CaseSummary`, sem adicionar a descrição da decisão aos embeddings ou à consulta ao Qdrant.
- Usar a descrição da decisão como contexto adicional após a busca de precedentes, no workflow de síntese/classificação de precedentes.
- Usar a descrição da decisão como contexto adicional nos workflows de geração e regeração de minuta de acórdão.
- Incluir `second_instance_decision` no `SecondInstanceAnalysisReport` e no `SecondInstanceAnalysisReportDto`.
- Criar migração Alembic para a tabela `second_instance_decisions`.

## 2.2 Out-of-scope

- UI mobile ou estados visuais da nova etapa.
- Alteração de ranqueamento manual, escolha ou desescolha de precedentes.
- Versionamento histórico de decisões submetidas.
- Remoção automática de precedentes, síntese ou minuta quando a decisão for ressubmetida.
- Alterações funcionais nos fluxos `CASE_ASSESSMENT` e `FIRST_INSTANCE`, exceto compatibilidade das assinaturas genéricas afetadas por precedentes.
- Criação de endpoint novo de exportação PDF no server, pois não foi encontrado exportador PDF dedicado na codebase.

# 3. Requisitos

## 3.1 Funcionais

- O endpoint `POST /intake/analyses/{analysis_id}/second-instance-decision` deve aceitar body `{ "description": "..." }`.
- `description` deve ser obrigatório e não pode ser vazio após `strip()`.
- A submissão deve exigir autenticação Bearer e ownership via `IntakePipe.verify_analysis_by_account_from_request`.
- A submissão deve falhar se a análise não for `SECOND_INSTANCE`.
- A primeira submissão deve persistir uma decisão vinculada a `analysis_id` e retornar `SecondInstanceDecisionDto` com status HTTP `201`.
- A ressubmissão deve substituir a decisão existente para o mesmo `analysis_id`, retornar `SecondInstanceDecisionDto` com status HTTP `201` e atualizar a análise para `DECISION_SUBMITTED`.
- A ressubmissão deve preservar precedentes, escolhas de precedentes e minuta já persistidos; esses dados só serão substituídos pelos fluxos já existentes de nova busca ou nova geração.
- O endpoint `GET /intake/analyses/{analysis_id}/second-instance-decision` deve retornar a decisão persistida com status HTTP `200`.
- O `GET` deve retornar erro de domínio traduzido para `404` quando não existir decisão para a análise.
- O status `DECISION_SUBMITTED` deve existir em `SecondInstanceAnalysisStatusValue` e ter factory `create_as_decision_submitted() -> SecondInstanceAnalysisStatus`.
- O trigger `POST /intake/analyses/{analysis_id}/precedents/search` deve rejeitar análises `SECOND_INSTANCE` sem decisão persistida.
- O trigger de busca de precedentes para outros tipos de análise deve continuar funcionando sem decisão.
- A busca vetorial de precedentes deve continuar usando o `CaseSummary` como base de embeddings, sem incluir `SecondInstanceDecision.description` nos chunks de busca.
- A síntese/classificação de precedentes deve receber e incluir a descrição da decisão no prompt após a recuperação dos candidatos.
- A descrição da decisão na síntese/classificação deve ser tratada como contexto opcional: para análises `FIRST_INSTANCE` e `CASE_ASSESSMENT`, o workflow deve receber `None` e preservar o comportamento atual.
- A inclusão da decisão na síntese/classificação não deve adicionar campos obrigatórios ao output estruturado dos precedentes.
- O trigger de geração de minuta de acórdão deve exigir decisão persistida para análises `SECOND_INSTANCE`.
- O job de geração de minuta deve carregar a decisão persistida e passá-la ao workflow de IA.
- O job de regeração de minuta deve carregar a decisão persistida e passá-la ao workflow de IA.
- O relatório de 2ª instância deve incluir `second_instance_decision: SecondInstanceDecisionDto`.

## 3.2 Não funcionais

- **Segurança:** os novos endpoints devem reutilizar `IntakePipe.verify_analysis_by_account_from_request` para autenticação e ownership.
- **Idempotência:** ressubmissões devem substituir a linha 1:1 em `second_instance_decisions`, nunca criar duplicatas.
- **Compatibilidade retroativa:** o payload de `AnalysisPrecedentsSearchTriggeredEvent` deve permanecer compatível; o contexto da decisão deve ser carregado por repositório no processamento.
- **Resiliência:** jobs existentes devem manter marcação de `FAILED` em falhas não tratadas; ausência de decisão em fluxo `SECOND_INSTANCE` deve falhar por erro de domínio antes de chamar IA.
- **Observabilidade:** progresso deve continuar sendo acompanhado pelo status persistido em `analyses.status`, incluindo o novo estado `DECISION_SUBMITTED`.
- **Compatibilidade de contrato HTTP:** `SecondInstanceAnalysisReportDto` terá novo campo obrigatório `second_instance_decision`, exigindo alinhamento com clientes que consomem o relatório.

# 4. O que já existe?

## Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) — entidade que normaliza status por `AnalysisType` e expõe `set_status(status: AnalysisStatus | str) -> None`.
- **`AnalysisType`** (`src/animus/core/intake/domain/structures/analysis_type.py`) — diferencia `CASE_ASSESSMENT`, `FIRST_INSTANCE` e `SECOND_INSTANCE`.
- **`SecondInstanceAnalysisStatus`** (`src/animus/core/intake/domain/structures/second_instance_analysis_status.py`) — enum/structure de status de 2ª instância a estender com `DECISION_SUBMITTED`.
- **`SecondInstanceAnalysisReport`** (`src/animus/core/intake/domain/structures/second_instance_analysis_report.py`) — structure do relatório a estender com a decisão.
- **`SecondInstanceAnalysisReportDto`** (`src/animus/core/intake/domain/structures/dtos/second_instance_analysis_report_dto.py`) — DTO retornado pelo endpoint de relatório a estender com a decisão.
- **`SecondInstanceJudgmentDraft`** (`src/animus/core/intake/domain/structures/second_instance_judgment_draft.py`) — referência de structure 1:1 por `analysis_id`.
- **`SecondInstanceJudgmentDraftDto`** (`src/animus/core/intake/domain/structures/dtos/second_instance_judgment_draft_dto.py`) — referência de DTO de structure persistida 1:1.
- **`CaseAssessmentBriefing`** (`src/animus/core/intake/domain/structures/case_assessment_briefing.py`) — referência de validação de campos textuais obrigatórios com `strip()` e `ValidationError`.
- **`SecondInstanceAnalysisRequiredError`** (`src/animus/core/intake/domain/errors/second_instance_analysis_required_error.py`) — erro existente para tipo de análise incompatível.
- **`CaseSummaryNotFoundError`** (`src/animus/core/intake/domain/errors/case_summary_not_found_error.py`) — erro de domínio para ausência de resumo do caso, com sufixo padronizado `NotFoundError`.
- **`AnalysesRepository`** (`src/animus/core/intake/interfaces/analyses_repository.py`) — port para buscar e substituir `Analysis`.
- **`CaseSummariesRepository`** (`src/animus/core/intake/interfaces/case_summaries_repository.py`) — port usado por busca, relatório e geração de minuta.
- **`AnalysisPrecedentsRepository`** (`src/animus/core/intake/interfaces/analysis_precedents_repository.py`) — port usado para listar/remover/substituir precedentes da análise.
- **`SecondInstanceJudgmentDraftsRepository`** (`src/animus/core/intake/interfaces/judgment_drafts_repository.py`) — referência de port 1:1 com `find_by_analysis_id(...)`, `add(...)` e `replace(...)`.
- **`CaseSummaryEmbeddingsProvider`** (`src/animus/core/intake/interfaces/case_summary_embeddings_provider.py`) — port de geração de embeddings que deve permanecer baseado apenas no `CaseSummary`.
- **`SynthesizeAnalysisPrecedentsWorkflow`** (`src/animus/core/intake/interfaces/synthesize_analysis_precedents_workflow.py`) — contrato do workflow de síntese/classificação de precedentes.
- **`GenerateSecondInstanceJudgmentDraftWorkflow`** (`src/animus/core/intake/interfaces/generate_judgment_draft_workflow.py`) — contrato do workflow de geração de minuta.
- **`RegenerateSecondInstanceJudgmentDraftWorkflow`** (`src/animus/core/intake/interfaces/regenerate_judgment_draft_workflow.py`) — contrato do workflow de regeração de minuta.
- **`RequestAnalysisPrecedentsSearchUseCase`** (`src/animus/core/intake/use_cases/request_analysis_precedents_search_use_case.py`) — use case que valida `CaseSummary` e publica `AnalysisPrecedentsSearchTriggeredEvent`.
- **`SearchAnalysisPrecedentsUseCase`** (`src/animus/core/intake/use_cases/search_analysis_precedents_use_case.py`) — use case que gera embeddings a partir do `CaseSummary`, busca no Qdrant e hidrata precedentes.
- **`TriggerSecondInstanceJudgmentDraftGenerationUseCase`** (`src/animus/core/intake/use_cases/trigger_second_instance_judgment_draft_generation_use_case.py`) — use case que valida precondições e publica evento de geração de minuta.
- **`GetSecondInstanceAnalysisReportUseCase`** (`src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`) — monta o relatório de 2ª instância com análise, documento, resumo, precedentes e minuta.

## Database

- **`AnalysisModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_model.py`) — model de `analyses`, com relacionamentos 1:1 para briefing, resumo, petição extraída e minuta.
- **`SecondInstanceJudgmentDraftModel`** (`src/animus/database/sqlalchemy/models/intake/judgment_draft_model.py`) — referência de model 1:1 com `analysis_id` como primary key e `ForeignKey('analyses.id', ondelete='CASCADE')`.
- **`CaseAssessmentBriefingModel`** (`src/animus/database/sqlalchemy/models/intake/case_assessment_briefing_model.py`) — referência de model 1:1 simples com campos `Text` obrigatórios.
- **`SecondInstanceJudgmentDraftMapper`** (`src/animus/database/sqlalchemy/mappers/intake/judgment_draft_mapper.py`) — referência de mapper `model -> structure` e `structure -> model`.
- **`CaseAssessmentBriefingMapper`** (`src/animus/database/sqlalchemy/mappers/intake/case_assessment_briefing_mapper.py`) — referência de mapper para structure 1:1 com campos textuais.
- **`SqlalchemySecondInstanceJudgmentDraftsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`) — referência de repository 1:1 com `find_by_analysis_id(...)`, `add(...)` e `replace(...)`.
- **`SqlalchemyCaseAssessmentBriefingsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_case_assessment_briefings_repository.py`) — referência de repository 1:1 com substituição in-place.
- **`migrations/versions/20260517_223000_restructure_second_instance_judgment_drafts.py`** — referência de evolução de tabela relacionada a minutas de 2ª instância.
- **Seeders da camada database:** `src/animus/database/sqlalchemy/seeders/intake_seeder.py` existe, mas cria apenas análise de exemplo `FIRST_INSTANCE`; não há seeder obrigatório para `SecondInstanceDecision`.

## REST

- **`SearchAnalysisPrecedentsController`** (`src/animus/rest/controllers/intake/search_analysis_precedents_controller.py`) — endpoint `POST /intake/analyses/{analysis_id}/precedents/search`, usa `_Body.to_dto()`, `IntakePipe`, `DatabasePipe` e `PubSubPipe`.
- **`GetSecondInstanceAnalysisReportController`** (`src/animus/rest/controllers/intake/get_second_instance_analysis_report_controller.py`) — endpoint de relatório de 2ª instância a estender com o novo repositório.
- **`GetSecondInstanceJudgmentDraftController`** (`src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`) — referência de GET fino com ownership por `IntakePipe`.
- **`TriggerSecondInstanceJudgmentDraftGenerationController`** (`src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_generation_controller.py`) — endpoint de trigger de minuta a estender com o novo repositório.
- **`CreateCaseAssessmentBriefingController`** (`src/animus/rest/controllers/intake/create_case_assessment_briefing_controller.py`) — referência de POST com `_Body` local e repasse por named params.
- **`src/animus/rest/controllers/intake/__init__.py`** — exports públicos dos controllers de `intake`.

## Routers

- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) — registra controllers de análises e deve registrar os dois novos controllers.

## Pipes

- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) — provider de repositories SQLAlchemy via `Depends(...)`, deve expor `SecondInstanceDecisionsRepository`.
- **`IntakePipe`** (`src/animus/pipes/intake_pipe.py`) — ownership check reutilizado pelos novos endpoints.
- **`PubSubPipe`** (`src/animus/pipes/pubsub_pipe.py`) — provider de `Broker` usado pelo trigger de busca de precedentes.
- **`AiPipe`** (`src/animus/pipes/ai_pipe.py`) — composition point de workflows Agno existentes.

## AI

- **`AgnoSynthesizeAndClassifyAnalysisPrecedentsWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_synthesize_analysis_precedents_workflow.py`) — monta prompt de síntese/classificação de precedentes.
- **`AgnoGenerateSecondInstanceJudgmentDraftWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_generate_second_instance_judgment_draft_workflow.py`) — monta prompt da minuta de acórdão.
- **`AgnoRegenerateSecondInstanceJudgmentDraftWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_regenerate_second_instance_judgment_draft_workflow.py`) — monta prompt da revisão da minuta com comentários.
- **`IntakeSquad`** (`src/animus/ai/agno/squads/intake_squad.py`) — contém agentes consumidos pelos workflows de precedentes e minuta; não precisa conhecer repositórios.

## PubSub

- **`AnalysisPrecedentsSearchTriggeredEvent`** (`src/animus/core/intake/domain/events/analysis_precedents_search_triggered_event.py`) — evento existente de busca de precedentes; deve ser renomeado de `AnalysisPrecedentsSearchRequestedEvent` para `AnalysisPrecedentsSearchTriggeredEvent` mantendo payload e `name`.
- **`SearchAnalysisPrecedentsJob`** (`src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`) — job que executa busca vetorial e síntese/classificação de precedentes.
- **`GenerateSecondInstanceJudgmentDraftJob`** (`src/animus/pubsub/inngest/jobs/intake/generate_second_instance_judgment_draft_job.py`) — job que gera e persiste minuta.
- **`RegenerateSecondInstanceJudgmentDraftJob`** (`src/animus/pubsub/inngest/jobs/intake/regenerate_second_instance_judgment_draft_job.py`) — job que regenera e substitui minuta.

# 5. O que deve ser criado?

## Camada Core (Entidades / Structures / DTOs)

- **Localização:** `src/animus/core/intake/domain/structures/dtos/second_instance_decision_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `analysis_id: str`, `description: str`

- **Localização:** `src/animus/core/intake/domain/structures/second_instance_decision.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `analysis_id: Id`, `description: Text`
- **Métodos / factory:**
  - `create(dto: SecondInstanceDecisionDto) -> SecondInstanceDecision` — valida `analysis_id`, aplica `strip()` em `description`, rejeita texto vazio com `ValidationError` e cria a structure.
  - `dto(self) -> SecondInstanceDecisionDto` — serializa a decisão para cruzar fronteiras.

## Camada Core (Erros de Domínio)

- **Localização:** `src/animus/core/intake/domain/errors/second_instance_decision_not_found_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** levantado quando uma decisão de 2ª instância é exigida, mas não existe para `analysis_id`.

## Camada Core (Interfaces / Ports)

- **Localização:** `src/animus/core/intake/interfaces/second_instance_decisions_repository.py` (**novo arquivo**)
- **Métodos:**
  - `find_by_analysis_id(analysis_id: Id) -> SecondInstanceDecision | None` — busca a decisão 1:1 por análise.
  - `add(decision: SecondInstanceDecision) -> None` — adiciona decisão nova.
  - `replace(decision: SecondInstanceDecision) -> None` — substitui decisão existente; se não existir, adiciona.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/create_second_instance_decision_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `SecondInstanceDecisionsRepository`, `AnalysesRepository`
- **Método principal:**
  - `execute(analysis_id: str, description: str) -> SecondInstanceDecisionDto` — cria ou substitui a decisão e atualiza a análise para `DECISION_SUBMITTED`.
- **Fluxo resumido:** valida `analysis_id` → busca `Analysis` → lança `AnalysisNotFoundError` se ausente → valida `analysis.type.is_second_instance` → cria `SecondInstanceDecision` → `add(...)` ou `replace(...)` → `analysis.set_status(SecondInstanceAnalysisStatus.create_as_decision_submitted())` → `AnalysesRepository.replace(...)` → retorna DTO.

- **Localização:** `src/animus/core/intake/use_cases/get_second_instance_decision_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `SecondInstanceDecisionsRepository`
- **Método principal:**
  - `execute(analysis_id: str) -> SecondInstanceDecisionDto` — retorna a decisão persistida para a análise.
- **Fluxo resumido:** valida `analysis_id` → busca decisão por `analysis_id` → lança `SecondInstanceDecisionNotFoundError` se ausente → retorna DTO.

## Camada Database (Models SQLAlchemy)

- **Localização:** `src/animus/database/sqlalchemy/models/intake/second_instance_decision_model.py` (**novo arquivo**)
- **Tabela:** `second_instance_decisions`
- **Colunas:** `analysis_id String(26) primary key ForeignKey('analyses.id', ondelete='CASCADE')`, `description Text nullable=False`
- **Relacionamentos:** `analysis: Mapped[Any] = relationship('AnalysisModel', back_populates='second_instance_decision')`

## Camada Database (Mappers)

- **Localização:** `src/animus/database/sqlalchemy/mappers/intake/second_instance_decision_mapper.py` (**novo arquivo**)
- **Métodos:**
  - `to_entity(model: SecondInstanceDecisionModel) -> SecondInstanceDecision` — cria `SecondInstanceDecision` a partir do model.
  - `to_model(decision: SecondInstanceDecision) -> SecondInstanceDecisionModel` — cria model SQLAlchemy a partir da structure.

## Camada Database (Repositórios)

- **Localização:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_second_instance_decisions_repository.py` (**novo arquivo**)
- **Interface implementada:** `SecondInstanceDecisionsRepository`
- **Dependências:** `Session` SQLAlchemy
- **Métodos:**
  - `__init__(sqlalchemy: Session) -> None` — armazena a sessão do escopo atual.
  - `find_by_analysis_id(analysis_id: Id) -> SecondInstanceDecision | None` — usa `Session.get(SecondInstanceDecisionModel, analysis_id.value)` e mapeia para domínio.
  - `add(decision: SecondInstanceDecision) -> None` — adiciona o model criado pelo mapper à sessão.
  - `replace(decision: SecondInstanceDecision) -> None` — atualiza `description` no model existente ou delega para `add(...)` se ausente.
- **Seeders da camada database:** não aplicável; `src/animus/database/sqlalchemy/seeders/intake_seeder.py` não precisa gerar decisão de 2ª instância.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/create_second_instance_decision_controller.py` (**novo arquivo**)
- **`_Body`:** `description: str`; validar texto não vazio após `strip()` na borda e manter validação de domínio em `SecondInstanceDecision.create(...)`.
- **Método HTTP e path:** `POST /intake/analyses/{analysis_id}/second-instance-decision`
- **`status_code`:** `201`
- **`response_model`:** `SecondInstanceDecisionDto`
- **Dependências injetadas via `Depends`:** `IntakePipe.verify_analysis_by_account_from_request`, `DatabasePipe.get_second_instance_decisions_repository_from_request`, `DatabasePipe.get_analyses_repository_from_request`
- **Fluxo:** `_Body` → named params diretos → `CreateSecondInstanceDecisionUseCase.execute(analysis_id=analysis.id.value, description=body.description)` → `SecondInstanceDecisionDto`

- **Localização:** `src/animus/rest/controllers/intake/get_second_instance_decision_controller.py` (**novo arquivo**)
- **`*Body`:** não aplicável
- **Método HTTP e path:** `GET /intake/analyses/{analysis_id}/second-instance-decision`
- **`status_code`:** `200`
- **`response_model`:** `SecondInstanceDecisionDto`
- **Dependências injetadas via `Depends`:** `IntakePipe.verify_analysis_by_account_from_request`, `DatabasePipe.get_second_instance_decisions_repository_from_request`
- **Fluxo:** `analysis` validada pelo pipe → `GetSecondInstanceDecisionUseCase.execute(analysis_id=analysis.id.value)` → `SecondInstanceDecisionDto`

## Migrações Alembic

- **Localização:** `migrations/versions/20260604_160000_create_second_instance_decisions.py` (**novo arquivo**)
- **Operações:** criar tabela `second_instance_decisions` com `analysis_id String(26)` como primary key e foreign key para `analyses.id` com `ondelete='CASCADE'`; criar coluna `description Text nullable=False`.
- **Reversibilidade:** `downgrade` deve remover a tabela; seguro estruturalmente, mas destrói decisões persistidas se aplicado em ambiente com dados.

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/structures/second_instance_analysis_status.py`
- **Mudança:** adicionar `DECISION_SUBMITTED` em `SecondInstanceAnalysisStatusValue`, criar `create_as_decision_submitted() -> SecondInstanceAnalysisStatus` e não incluir esse status em `get_processing_statuses()`.
- **Justificativa:** representar a etapa intermediária após análise do caso e antes da busca de precedentes sem tratá-la como processamento ativo.

- **Arquivo:** `src/animus/core/intake/domain/structures/second_instance_analysis_report.py`
- **Mudança:** adicionar atributo `second_instance_decision: SecondInstanceDecision`, preencher em `create(...)` e serializar em `dto`.
- **Justificativa:** relatório de 2ª instância deve expor a decisão que direcionou precedentes e minuta.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/second_instance_analysis_report_dto.py`
- **Mudança:** adicionar `second_instance_decision: SecondInstanceDecisionDto`.
- **Justificativa:** contrato HTTP do relatório precisa incluir a nova seção consumida pelo app/exportador.

- **Arquivo:** `src/animus/core/intake/domain/structures/__init__.py`
- **Mudança:** exportar `SecondInstanceDecision` por `TYPE_CHECKING`, `__all__` e `__getattr__`.
- **Justificativa:** manter padrão de exports lazy do contexto `intake`.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/__init__.py`
- **Mudança:** exportar `SecondInstanceDecisionDto`.
- **Justificativa:** permitir imports estáveis de DTOs em controllers e use cases.

- **Arquivo:** `src/animus/core/intake/domain/errors/__init__.py`
- **Mudança:** exportar `SecondInstanceDecisionNotFoundError`.
- **Justificativa:** manter padrão de acesso aos erros do contexto.

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudança:** exportar `SecondInstanceDecisionsRepository`.
- **Justificativa:** permitir DI e imports pelo pacote de interfaces.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** exportar `CreateSecondInstanceDecisionUseCase` e `GetSecondInstanceDecisionUseCase`.
- **Justificativa:** manter padrão de imports públicos de use cases.

- **Arquivo:** `src/animus/core/intake/use_cases/request_analysis_precedents_search_use_case.py`
- **Mudança:** injetar `AnalysesRepository` e `SecondInstanceDecisionsRepository`; antes de publicar evento, se `Analysis.type` for `SECOND_INSTANCE`, exigir decisão persistida.
- **Justificativa:** bloquear busca de precedentes sem a decisão pretendida pelo juiz.

- **Arquivo:** `src/animus/core/intake/domain/events/analysis_precedents_search_triggered_event.py`
- **Mudança:** renomear a classe `AnalysisPrecedentsSearchRequestedEvent` para `AnalysisPrecedentsSearchTriggeredEvent`, preservando `name = 'intake/analyses.precedents.search.triggered'`, payload e assinatura do construtor.
- **Justificativa:** alinhar nomenclatura do evento ao sufixo `TriggeredEvent` já usado nos demais fluxos assíncronos de `intake`.

- **Arquivo:** `src/animus/core/intake/domain/errors/case_summary_not_found_error.py`
- **Mudança:** garantir que o erro de ausência de resumo do caso use a classe `CaseSummaryNotFoundError` e atualizar imports tocados por esta feature.
- **Justificativa:** padronizar erros de recurso ausente com sufixo `NotFoundError`.

- **Arquivo:** `src/animus/core/intake/use_cases/search_analysis_precedents_use_case.py`
- **Mudança:** não alterar a geração de embeddings nem a chamada a `CaseSummaryEmbeddingsProvider.generate(case_summary)`; a recuperação vetorial deve continuar baseada apenas no `CaseSummary`.
- **Justificativa:** a descrição da decisão deve influenciar a análise posterior dos candidatos, não a etapa de recuperação vetorial.

- **Arquivo:** `src/animus/core/intake/use_cases/trigger_second_instance_judgment_draft_generation_use_case.py`
- **Mudança:** injetar `SecondInstanceDecisionsRepository` e exigir decisão persistida antes de publicar `SecondInstanceJudgmentDraftGenerationTriggeredEvent`.
- **Justificativa:** garantir que a geração da minuta sempre tenha o contexto decisório exigido pelo fluxo.

- **Arquivo:** `src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`
- **Mudança:** injetar `SecondInstanceDecisionsRepository`, carregar decisão por `analysis_id` e incluí-la em `SecondInstanceAnalysisReport`.
- **Justificativa:** relatório deve expor a descrição da decisão.

- **Arquivo:** `src/animus/core/intake/interfaces/synthesize_analysis_precedents_workflow.py`
- **Mudança:** alterar assinatura para `run(analysis_id: str, filters_dto: AnalysisPrecedentsSearchFiltersDto, analysis_precedents: list[AnalysisPrecedentDto], second_instance_decision: SecondInstanceDecision | None = None) -> None`.
- **Justificativa:** permitir que a síntese/classificação use a decisão quando existir, preservando compatibilidade semântica com outros tipos de análise.
- **Comportamento esperado:** quando `second_instance_decision is None`, o workflow deve montar o prompt atual sem bloco adicional de decisão e manter o output estruturado existente.

- **Arquivo:** `src/animus/core/intake/interfaces/generate_judgment_draft_workflow.py`
- **Mudança:** alterar assinatura para `run(analysis_id: str, case_summary: CaseSummary, precedents: list[AnalysisPrecedent], second_instance_decision: SecondInstanceDecision) -> SecondInstanceJudgmentDraftDto`.
- **Justificativa:** minuta de 2ª instância deve refletir a decisão pretendida.

- **Arquivo:** `src/animus/core/intake/interfaces/regenerate_judgment_draft_workflow.py`
- **Mudança:** alterar assinatura para `run(analysis_id: str, current_draft: SecondInstanceJudgmentDraft, case_summary: CaseSummary, precedents: list[AnalysisPrecedent], comments: str, second_instance_decision: SecondInstanceDecision) -> SecondInstanceJudgmentDraftDto`.
- **Justificativa:** regeração deve preservar coerência com a decisão mais recente.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/analysis_model.py`
- **Mudança:** adicionar relacionamento `second_instance_decision` 1:1 com `SecondInstanceDecisionModel`, `back_populates='analysis'`, `uselist=False` e `cascade='all, delete-orphan'`.
- **Justificativa:** manter cascade de remoção da decisão quando a análise for removida.

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/__init__.py`
- **Mudança:** importar e exportar `SecondInstanceDecisionModel`.
- **Justificativa:** garantir registro do model no metadata SQLAlchemy.

- **Arquivo:** `src/animus/database/sqlalchemy/mappers/intake/__init__.py`
- **Mudança:** importar e exportar `SecondInstanceDecisionMapper`.
- **Justificativa:** manter padrão de exports de mappers do contexto.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/__init__.py`
- **Mudança:** importar e exportar `SqlalchemySecondInstanceDecisionsRepository`.
- **Justificativa:** permitir wiring pelo `DatabasePipe` e jobs.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/search_analysis_precedents_controller.py`
- **Mudança:** injetar `AnalysesRepository` e `SecondInstanceDecisionsRepository` e repassar ao `RequestAnalysisPrecedentsSearchUseCase`.
- **Justificativa:** aplicar precondição de decisão no domínio antes de publicar evento.

- **Arquivo:** `src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_generation_controller.py`
- **Mudança:** injetar `SecondInstanceDecisionsRepository` e repassar ao use case.
- **Justificativa:** garantir precondição da minuta no fluxo HTTP.

- **Arquivo:** `src/animus/rest/controllers/intake/get_second_instance_analysis_report_controller.py`
- **Mudança:** injetar `SecondInstanceDecisionsRepository` e repassar ao use case.
- **Justificativa:** incluir decisão no relatório.

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** importar e exportar `CreateSecondInstanceDecisionController` e `GetSecondInstanceDecisionController`.
- **Justificativa:** disponibilizar controllers para o router.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** registrar `CreateSecondInstanceDecisionController.handle(router)` e `GetSecondInstanceDecisionController.handle(router)`.
- **Justificativa:** expor os novos endpoints sob o router de análises existente.

## Pipes

- **Arquivo:** `src/animus/pipes/database_pipe.py`
- **Mudança:** importar `SecondInstanceDecisionsRepository` e `SqlalchemySecondInstanceDecisionsRepository`; adicionar `get_second_instance_decisions_repository_from_request(sqlalchemy: Session) -> SecondInstanceDecisionsRepository`.
- **Justificativa:** manter controllers finos e DI centralizada.

## AI

- **Arquivo:** `src/animus/ai/agno/workflows/intake/agno_synthesize_analysis_precedents_workflow.py`
- **Mudança:** receber `second_instance_decision` opcional no `run(...)`, armazenar em `session_state` e incluir um bloco `Descrição da decisão pretendida pelo juiz` no prompt somente quando não for `None`.
- **Justificativa:** orientar classificação, síntese e aderência dos precedentes ao resultado pretendido em `SECOND_INSTANCE`, sem alterar `FIRST_INSTANCE` e `CASE_ASSESSMENT`.
- **Regra de compatibilidade:** o bloco condicional deve orientar a interpretação dos candidatos, mas não deve exigir novos campos no `AnalysisPrecedentsSynthesisOutput` nem mudar o formato persistido por `CreateAnalysisPrecedentsUseCase`.

- **Arquivo:** `src/animus/ai/agno/workflows/intake/agno_generate_second_instance_judgment_draft_workflow.py`
- **Mudança:** receber `second_instance_decision` no `run(...)`, validar tipo no step de input e incluir `Descrição da decisão pretendida pelo juiz` no prompt da minuta.
- **Justificativa:** alinhar fundamentação, análise de aderência/distinção e dispositivo sugerido à decisão informada.

- **Arquivo:** `src/animus/ai/agno/workflows/intake/agno_regenerate_second_instance_judgment_draft_workflow.py`
- **Mudança:** receber `second_instance_decision` no `run(...)`, validar tipo no step de input e incluir a decisão no prompt junto da minuta atual e comentários.
- **Justificativa:** garantir que revisões também considerem a decisão vigente.

## PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`
- **Mudança:** instanciar `SqlalchemySecondInstanceDecisionsRepository` apenas na etapa de síntese/classificação; carregar `second_instance_decision` depois que os candidatos já tiverem sido recuperados quando a análise for `SECOND_INSTANCE`; para outros tipos, repassar `None` ao workflow.
- **Justificativa:** usar a decisão após a busca de precedentes, sem alterar a recuperação vetorial, o payload do evento ou o comportamento dos demais tipos de análise.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/generate_second_instance_judgment_draft_job.py`
- **Mudança:** instanciar `SqlalchemySecondInstanceDecisionsRepository`, carregar decisão por `analysis_id`, lançar `SecondInstanceDecisionNotFoundError` se ausente e repassar ao workflow.
- **Justificativa:** garantir contexto obrigatório na geração da minuta.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/regenerate_second_instance_judgment_draft_job.py`
- **Mudança:** instanciar `SqlalchemySecondInstanceDecisionsRepository`, carregar decisão por `analysis_id`, lançar `SecondInstanceDecisionNotFoundError` se ausente e repassar ao workflow.
- **Justificativa:** garantir contexto obrigatório na regeração da minuta.

# 7. O que deve ser removido?

**Não aplicável**.

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** modelar `SecondInstanceDecision` como `@structure`, não como `@entity`.
- **Alternativas consideradas:** criar entidade com ID próprio; persistir apenas campo em `AnalysisModel`; usar DTO solto sem tipo de domínio.
- **Motivo da escolha:** estruturas 1:1 por `analysis_id`, como `SecondInstanceJudgmentDraft` e `CaseAssessmentBriefing`, já seguem esse padrão no contexto `intake`.
- **Impactos / trade-offs:** não há histórico/versionamento nativo; ressubmissões substituem o estado atual.

- **Decisão:** criar tabela própria `second_instance_decisions` em vez de adicionar coluna em `analyses`.
- **Alternativas consideradas:** adicionar `second_instance_decision_description` em `analyses`; armazenar em JSON de metadados.
- **Motivo da escolha:** mantém `Analysis` enxuta, preserva separação de dado específico de fluxo e replica padrão de resources 1:1.
- **Impactos / trade-offs:** exige migration e repository novo, mas evita poluir tabela central com campo de um único tipo de análise.

- **Decisão:** ressubmissão preserva precedentes e minuta já existentes.
- **Alternativas consideradas:** remover precedentes e minuta automaticamente; bloquear ressubmissão após busca; registrar pendência sem decisão.
- **Motivo da escolha:** decisão confirmada pelo usuário durante a elaboração da spec: substituir apenas a decisão e atualizar status, deixando dados downstream existentes até nova busca ou geração.
- **Impactos / trade-offs:** pode existir período de inconsistência entre decisão mais recente e dados downstream antigos; o status `DECISION_SUBMITTED` sinaliza que a próxima execução deve usar o novo contexto.

- **Decisão:** manter payload de `AnalysisPrecedentsSearchTriggeredEvent` sem `decision_description`.
- **Alternativas consideradas:** adicionar campo opcional no evento; criar evento específico para busca de precedentes de 2ª instância.
- **Motivo da escolha:** preserva compatibilidade do evento e centraliza leitura da decisão no job/use case por repositório.
- **Impactos / trade-offs:** o job usa a decisão persistida no momento da execução, não um snapshot imutável do momento do clique.

- **Decisão:** não adicionar `SecondInstanceDecision.description` à busca vetorial.
- **Alternativas consideradas:** estender `CaseSummaryEmbeddingsProvider.generate(...)` com contexto adicional; concatenar decisão aos chunks de embedding; criar provider específico para 2ª instância.
- **Motivo da escolha:** a decisão pretendida deve orientar a avaliação dos candidatos recuperados, sem restringir prematuramente a recuperação vetorial baseada no caso.
- **Impactos / trade-offs:** a etapa de Qdrant permanece igual; a influência da decisão ocorre na síntese/classificação e na minuta.

- **Decisão:** manter `AgnoSynthesizeAndClassifyAnalysisPrecedentsWorkflow` genérico, com `second_instance_decision` opcional.
- **Alternativas consideradas:** criar workflow exclusivo de síntese para `SECOND_INSTANCE`; adicionar campos obrigatórios novos no output de síntese; não passar a decisão para a síntese.
- **Motivo da escolha:** o workflow já é compartilhado entre tipos de análise; contexto opcional evita duplicação e preserva os fluxos `FIRST_INSTANCE` e `CASE_ASSESSMENT`.
- **Impactos / trade-offs:** o prompt passa a ter branch condicional, mas o contrato de saída e a persistência dos precedentes permanecem estáveis.

- **Decisão:** adicionar decisão ao relatório como campo obrigatório.
- **Alternativas consideradas:** campo opcional para compatibilidade com análises antigas.
- **Motivo da escolha:** a nova regra torna a decisão pré-condição para avançar no fluxo `SECOND_INSTANCE`; relatório sem decisão deixa de representar o fluxo válido.
- **Impactos / trade-offs:** clientes devem tratar o novo campo no contrato do relatório.

# 9. Diagramas e Referências

- **Fluxo de dados:**

```text
POST /intake/analyses/{analysis_id}/second-instance-decision
  -> Middleware
  -> AnalysesRouter
  -> CreateSecondInstanceDecisionController
  -> IntakePipe.verify_analysis_by_account_from_request
  -> DatabasePipe.get_second_instance_decisions_repository_from_request
  -> DatabasePipe.get_analyses_repository_from_request
  -> CreateSecondInstanceDecisionUseCase
  -> SecondInstanceDecisionsRepository (port)
  -> SqlalchemySecondInstanceDecisionsRepository
  -> SecondInstanceDecisionModel
  -> PostgreSQL second_instance_decisions
  -> Analysis.status = DECISION_SUBMITTED
  -> Response JSON SecondInstanceDecisionDto
```

- **Fluxo de leitura:**

```text
GET /intake/analyses/{analysis_id}/second-instance-decision
  -> Middleware
  -> AnalysesRouter
  -> GetSecondInstanceDecisionController
  -> IntakePipe.verify_analysis_by_account_from_request
  -> DatabasePipe.get_second_instance_decisions_repository_from_request
  -> GetSecondInstanceDecisionUseCase
  -> SecondInstanceDecisionsRepository.find_by_analysis_id
  -> PostgreSQL second_instance_decisions
  -> Response JSON SecondInstanceDecisionDto
```

- **Fluxo assíncrono de precedentes:**

```text
POST /intake/analyses/{analysis_id}/precedents/search
  -> SearchAnalysisPrecedentsController
  -> RequestAnalysisPrecedentsSearchUseCase
  -> exige CaseSummary
  -> se SECOND_INSTANCE, exige SecondInstanceDecision
  -> Broker.publish(AnalysisPrecedentsSearchTriggeredEvent)
  -> SearchAnalysisPrecedentsJob
  -> SearchAnalysisPrecedentsUseCase
  -> CaseSummaryEmbeddingsProvider.generate(case_summary)
  -> QdrantPrecedentsEmbeddingsRepository
  -> PrecedentsRepository
  -> carrega SecondInstanceDecision após recuperar candidatos
  -> AgnoSynthesizeAndClassifyAnalysisPrecedentsWorkflow(second_instance_decision | None)
  -> CreateAnalysisPrecedentsUseCase
  -> PostgreSQL analysis_precedents
```

- **Fluxo assíncrono de minuta:**

```text
POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts
  -> TriggerSecondInstanceJudgmentDraftGenerationController
  -> TriggerSecondInstanceJudgmentDraftGenerationUseCase
  -> exige SecondInstanceDecision + CaseSummary + precedentes escolhidos
  -> Broker.publish(SecondInstanceJudgmentDraftGenerationTriggeredEvent)
  -> GenerateSecondInstanceJudgmentDraftJob
  -> carrega SecondInstanceDecision
  -> AgnoGenerateSecondInstanceJudgmentDraftWorkflow(second_instance_decision)
  -> CreateSecondInstanceJudgmentDraftUseCase
  -> PostgreSQL second_instance_judgment_drafts
  -> SecondInstanceJudgmentDraftGenerationFinishedEvent
```

- **Referências:**

- `src/animus/core/intake/domain/structures/case_assessment_briefing.py`
- `src/animus/core/intake/domain/structures/second_instance_judgment_draft.py`
- `src/animus/core/intake/interfaces/case_assessment_briefings_repository.py`
- `src/animus/core/intake/interfaces/judgment_drafts_repository.py`
- `src/animus/core/intake/use_cases/create_case_assessment_briefing_use_case.py`
- `src/animus/core/intake/use_cases/create_judgment_draft_use_case.py`
- `src/animus/database/sqlalchemy/models/intake/case_assessment_briefing_model.py`
- `src/animus/database/sqlalchemy/models/intake/judgment_draft_model.py`
- `src/animus/database/sqlalchemy/mappers/intake/case_assessment_briefing_mapper.py`
- `src/animus/database/sqlalchemy/mappers/intake/judgment_draft_mapper.py`
- `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_case_assessment_briefings_repository.py`
- `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`
- `src/animus/rest/controllers/intake/create_case_assessment_briefing_controller.py`
- `src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`
- `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`
- `src/animus/pubsub/inngest/jobs/intake/generate_second_instance_judgment_draft_job.py`
- `src/animus/ai/agno/workflows/intake/agno_synthesize_analysis_precedents_workflow.py`
- `src/animus/ai/agno/workflows/intake/agno_generate_second_instance_judgment_draft_workflow.py`

# 10. Pendências / Dúvidas

Sem pendências.

- **Ticket Jira:** não há ticket associado; manter `ticket: N/A` no frontmatter.
- **Exportação PDF:** responsabilidade exclusiva do client-side; no server, a mudança necessária é expor `second_instance_decision` em `SecondInstanceAnalysisReportDto`.
