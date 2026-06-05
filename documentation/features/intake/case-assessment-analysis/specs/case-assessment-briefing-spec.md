---
title: Briefing estruturado para Análise Inicial do Advogado
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AYDsAg
ticket: N/A
status: closed
last_updated_at: 2026-06-05
---

# 1. Objetivo

Implementar o novo ponto de entrada da análise `CASE_ASSESSMENT` para o perfil Advogado: o backend deve receber e persistir um `CaseAssessmentBriefing` estruturado, permitir documentos de apoio opcionais e múltiplos, disparar a geração assíncrona de `CaseSummary` a partir do briefing e dos documentos disponíveis, e substituir os status iniciais baseados em documento por status baseados em briefing. O pipeline posterior de precedentes, escolha de precedente e geração de minuta deve continuar consumindo o mesmo contrato de `CaseSummary` já existente.

# 2. Escopo

## 2.1 In-scope

- Criar a `Structure` `LegalArea` com enum `LegalAreaValue`, conforme PRD atualizado.
- Criar `CaseAssessmentBriefingDto` e `CaseAssessmentBriefing` no `core/intake`.
- Criar persistência 1:1 de briefing por `Analysis` na tabela `case_assessment_briefings`.
- Criar `CaseAssessmentBriefingsRepository` e implementação SQLAlchemy.
- Criar endpoint `POST /intake/analyses/{analysis_id}/case-assessment-briefing` para submeter ou ressubmeter o briefing.
- Atualizar status iniciais de `CASE_ASSESSMENT`: `WAITING_DOCUMENT_UPLOAD` para `WAITING_BRIEFING` e `DOCUMENT_UPLOADED` para `BRIEFING_SUBMITTED`.
- Alterar `CreateAnalysisUseCase` para iniciar análises `CASE_ASSESSMENT` em `WAITING_BRIEFING`.
- Ajustar o suporte a `AnalysisDocument` para permitir múltiplos documentos de apoio em análises `CASE_ASSESSMENT`, mantendo comportamento 1:1 efetivo para fluxos de juiz.
- Ajustar o trigger de geração de resumo para exigir briefing persistido, não documento obrigatório.
- Alterar o job `SummarizeCaseAssessmentCaseJob` para carregar briefing, carregar zero ou mais documentos, executar workflow de IA e persistir `CaseSummary`.
- Alterar `AgnoSummarizeCaseAssessmentCaseWorkflow` para montar prompt com briefing + documentos e preservar os campos preenchidos pelo advogado no `CaseSummary`.
- Resetar o `CaseSummary` existente quando o briefing for ressubmetido.
- Incluir o `CaseAssessmentBriefing` no `CaseAssessmentAnalysisReport` retornado ao cliente.
- Criar migração Alembic para tabela de briefing, alteração de status e suporte a múltiplos documentos.

## 2.2 Out-of-scope

- UI mobile do formulário, estados visuais, placeholders e mensagens inline.
- Edição manual do `CaseSummary` após geração.
- Alteração funcional na busca, ranqueamento, síntese ou escolha de precedentes.
- Alteração no fluxo de `FIRST_INSTANCE` e `SECOND_INSTANCE`, exceto preservação de compatibilidade no repositório genérico de documentos.
- Edição manual da minuta, salvamento automático e exportação DOCX.
- Versionamento histórico de briefings ou summaries.
- Remoção automática de precedentes e minutas já gerados em ressubmissões; esta spec reseta apenas `CaseSummary`, conforme requisito explícito.
- Testes automatizados.

# 3. Requisitos

## 3.1 Funcionais

- Ao criar uma análise `CASE_ASSESSMENT`, o status inicial deve ser `WAITING_BRIEFING`.
- O endpoint de submissão do briefing deve aceitar `legal_area`, `court_jurisdiction`, `main_claims` e `intended_thesis` como campos obrigatórios.
- `legal_area` deve ser validado por `LegalArea.create(value: str)` contra `LegalAreaValue`.
- `court_jurisdiction` deve ser validado por `Court.create(value: str)` contra `CourtValue` já existente.
- `main_claims` e `intended_thesis` não podem ser nulos nem vazios após `strip()`.
- A submissão deve exigir autenticação Bearer e ownership via `IntakePipe.verify_analysis_by_account_from_request`.
- A submissão deve falhar com `InconsistentAnalysisTypeError` se a análise não for `CASE_ASSESSMENT`.
- A primeira submissão deve persistir um briefing vinculado a `analysis_id` e atualizar a análise para `BRIEFING_SUBMITTED`.
- A ressubmissão deve substituir o briefing existente para o mesmo `analysis_id`, remover o `CaseSummary` existente da análise e atualizar o status para `BRIEFING_SUBMITTED`.
- O endpoint de submissão deve responder `201` com `CaseAssessmentBriefingDto`.
- O endpoint de trigger de geração do resumo deve validar que existe briefing persistido para a análise.
- O trigger de geração do resumo deve publicar `CaseAssessmentCaseSummarizationTriggeredEvent` e responder `202 Accepted` sem body.
- O trigger de geração do resumo deve atualizar a análise para `ANALYZING_CASE` antes de publicar o evento, seguindo o padrão atual de triggers assíncronos de `intake`.
- O job de sumarização deve carregar `CaseAssessmentBriefing` por `analysis_id`.
- O job de sumarização deve carregar todos os `AnalysisDocument` vinculados à análise; ausência de documentos deve ser válida.
- Para cada documento encontrado, o job deve extrair conteúdo via `GetDocumentContentUseCase` com `GcsFileStorageProvider`, `PypdfPdfProvider` e `PythonDocxProvider`.
- O workflow de IA deve receber `briefing` e `document_contents: list[Text]`.
- O `CaseSummary` gerado deve preservar os campos do advogado sem reescrita pela IA: `legal_issue = briefing.legal_area`, `central_question = briefing.intended_thesis` e `key_facts = [briefing.main_claims]`.
- A IA deve gerar `case_summary`, `relevant_laws`, `search_terms` e campos complementares já suportados por `CaseSummaryDto`.
- A persistência de `CaseSummary` deve continuar usando `CaseSummariesRepository.add(...)` ou `replace(...)`, mantendo idempotência.
- Ao concluir com sucesso, o job deve publicar `CaseSummaryFinishedEvent` com `analysis_id`, `account_id` e `analysis_type`.
- Em falha não recuperável, o job deve atualizar a análise para `FAILED` no `except` interno e no `on_failure` do Inngest.
- O endpoint `GET /intake/analyses/{analysis_id}/case-assessment-report` deve incluir o `briefing` persistido no payload de `CaseAssessmentAnalysisReportDto`.
- O endpoint atual de geração de signed URL em `storage` pode ser reutilizado para múltiplos uploads, pois já gera paths únicos em `intake/analyses/{analysis_id}/documents/{file_id}.{document_type}`.
- Para análises `CASE_ASSESSMENT`, `CreateAnalysisDocumentUseCase` deve adicionar documentos sem alterar status e sem substituir documentos anteriores.
- Para análises `FIRST_INSTANCE` e `SECOND_INSTANCE`, `CreateAnalysisDocumentUseCase` deve preservar o comportamento atual de substituir o documento anterior e atualizar status para `DOCUMENT_UPLOADED`.

## 3.2 Não funcionais

- **Segurança:** todos os endpoints de `intake` impactados devem reutilizar `AuthPipe.get_account_id_from_request` ou `IntakePipe.verify_analysis_by_account_from_request`.
- **Idempotência:** ressubmissões de briefing e reexecuções do job devem substituir dados 1:1 (`CaseAssessmentBriefing`, `CaseSummary`) em vez de criar duplicatas.
- **Compatibilidade retroativa:** fluxos `FIRST_INSTANCE` e `SECOND_INSTANCE` devem continuar funcionando com um documento por análise via `AnalysisDocumentsRepository.find_by_analysis_id(...)`.
- **Observabilidade:** o app deve acompanhar progresso por status persistido (`BRIEFING_SUBMITTED`, `ANALYZING_CASE`, `CASE_ANALYZED`, `FAILED`) e pelos eventos de conclusão já existentes.
- **Resiliência:** `SummarizeCaseAssessmentCaseJob` deve manter `on_failure` e marcação explícita de `FAILED`, seguindo o padrão atual de jobs de intake.
- **Compatibilidade de contrato downstream:** `CaseSummaryDto` não deve mudar; precedentes e minuta devem continuar consumindo os mesmos campos.

# 4. O que já existe?

## Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) — entidade que normaliza status conforme `AnalysisType` e expõe `set_status(status: AnalysisStatus | str) -> None`.
- **`AnalysisDto`** (`src/animus/core/intake/domain/entities/dtos/analysis_dto.py`) — DTO usado para criar e retornar análises.
- **`AnalysisType`** (`src/animus/core/intake/domain/structures/analysis_type.py`) — diferencia `CASE_ASSESSMENT`, `FIRST_INSTANCE` e `SECOND_INSTANCE`.
- **`CaseAssessmentAnalysisStatus`** (`src/animus/core/intake/domain/structures/case_assessment_analysis_status.py`) — status atual de `CASE_ASSESSMENT`, hoje ainda baseado em `WAITING_DOCUMENT_UPLOAD` e `DOCUMENT_UPLOADED`.
- **`Court`** (`src/animus/core/intake/domain/structures/court.py`) — referência direta para `LegalArea`: usa `StrEnum`, `create(value: str) -> Court`, normalização com `value.upper()` e `ValidationError`.
- **`AnalysisDocument`** (`src/animus/core/intake/domain/structures/analysis_document.py`) — structure atual do documento da análise, hoje sem `id` próprio e identificada por `analysis_id` + `file_path`.
- **`AnalysisDocumentDto`** (`src/animus/core/intake/domain/structures/dtos/analysis_document_dto.py`) — DTO com `analysis_id`, `uploaded_at`, `file_path` e `name`.
- **`CaseSummary`** (`src/animus/core/intake/domain/structures/case_summary.py`) — structure persistida e consumida por precedentes/minuta.
- **`CaseSummaryDto`** (`src/animus/core/intake/domain/structures/dtos/case_summary_dto.py`) — contrato downstream que deve permanecer estável.
- **`CaseAssessmentAnalysisReport` / `CaseAssessmentAnalysisReportDto`** (`src/animus/core/intake/domain/structures/case_assessment_analysis_report.py`) — relatório agregado atualmente sem briefing, a ser enriquecido com os dados estruturados submetidos pelo advogado.
- **`AnalysisDocumentsRepository`** (`src/animus/core/intake/interfaces/analysis_documents_repository.py`) — port atual para buscar/adicionar/substituir/remover documento da análise.
- **`CaseSummariesRepository`** (`src/animus/core/intake/interfaces/case_summaries_repository.py`) — port atual com `find_by_analysis_id(...)`, `add(...)` e `replace(...)`.
- **`AnalysesRepository`** (`src/animus/core/intake/interfaces/analyses_repository.py`) — port usado para buscar e substituir `Analysis`.
- **`SummarizeCaseAssessmentCaseWorkflow`** (`src/animus/core/intake/interfaces/summarize_case_workflow.py`) — contrato atual do workflow de `CASE_ASSESSMENT`, hoje recebe `document_content: Text` único.
- **`CreateAnalysisUseCase`** (`src/animus/core/intake/use_cases/create_analysis_use_case.py`) — define status inicial da análise.
- **`CreateAnalysisDocumentUseCase`** (`src/animus/core/intake/use_cases/create_analysis_document_use_case.py`) — hoje substitui documento por `analysis_id` e atualiza status para `DOCUMENT_UPLOADED`.
- **`RemoveAnalysisDocumentUseCase`** (`src/animus/core/intake/use_cases/remove_analysis_document_use_case.py`) — hoje remove documento por `analysis_id` após conferir `file_path`.
- **`GetAnalysisDocumentUseCase`** (`src/animus/core/intake/use_cases/get_analysis_document_use_case.py`) — hoje retorna um único documento por análise.
- **`CreateCaseSummaryUseCase`** (`src/animus/core/intake/use_cases/create_case_summary_use_case.py`) — persiste `CaseSummary`, mas hoje exige `AnalysisDocument` antes de criar o resumo.
- **`TriggerCaseAssessmentCaseSummarizationUseCase`** (`src/animus/core/intake/use_cases/trigger_case_assessment_case_summarization_use_case.py`) — hoje valida documento obrigatório, atualiza para `ANALYZING_CASE` e publica evento.
- **`UpdateAnalysisStatusUseCase`** (`src/animus/core/intake/use_cases/update_analysis_status_use_case.py`) — referência para jobs atualizarem status sem regra em repositório.
- **`AnalysisDocumentNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_document_not_found_error.py`) — erro atual para ausência de documento.
- **`AnalysisNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_not_found_error.py`) — erro atual para análise inexistente.
- **`InconsistentAnalysisTypeError`** (`src/animus/core/intake/domain/errors/inconsistent_analysis_type_error.py`) — erro atual para análise de tipo incompatível.

## Database

- **`AnalysisModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_model.py`) — model de `analyses`, hoje com relacionamento `document` 1:1.
- **`AnalysisDocumentModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_document_model.py`) — model de `analysis_documents`, hoje com `analysis_id` como primary key.
- **`CaseSummaryModel`** (`src/animus/database/sqlalchemy/models/intake/case_summary_model.py`) — model 1:1 de `case_summaries` por `analysis_id`.
- **`AnalysisDocumentMapper`** (`src/animus/database/sqlalchemy/mappers/intake/analysis_document_mapper.py`) — mapper entre `AnalysisDocumentModel` e `AnalysisDocument`.
- **`SqlalchemyAnalysisDocumentsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analysis_documents_repository.py`) — implementação atual de documento único por análise.
- **`SqlalchemyCaseSummariesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_case_summaries_repository.py`) — implementação atual de `CaseSummariesRepository`.
- **`SqlalchemyAnalysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analyses_repository.py`) — implementação atual de `AnalysesRepository`.
- **`migrations/versions/20260511_120000_intake_analysis_documents_case_summaries_and_drafts.py`** — migração que criou `analysis_documents` com `analysis_id` como primary key.
- **Seeders da camada database:** `src/animus/database/sqlalchemy/seeders/intake_seeder.py` existe, mas não cria `CASE_ASSESSMENT`; não há seeder obrigatório para esta feature.

## REST

- **`CreateAnalysisDocumentController`** (`src/animus/rest/controllers/intake/create_analysis_document_controller.py`) — endpoint `POST /intake/analyses/{analysis_id}/documents` que persiste metadados de documento.
- **`GetAnalysisDocumentController`** (`src/animus/rest/controllers/intake/get_analysis_document_controller.py`) — endpoint `GET /intake/analyses/{analysis_id}/documents` que retorna um único documento.
- **`RemoveAnalysisDocumentController`** (`src/animus/rest/controllers/intake/remove_analysis_document_controller.py`) — endpoint `DELETE /intake/analyses/{analysis_id}/documents?file_path=...`.
- **`TriggerCaseAssessmentCaseSummarizationController`** (`src/animus/rest/controllers/intake/trigger_case_assessment_case_summarization_controller.py`) — endpoint atual de trigger de resumo de `CASE_ASSESSMENT`.
- **`GetCaseSummaryController`** (`src/animus/rest/controllers/intake/get_case_summary_controller.py`) — endpoint de leitura do `CaseSummary` já persistido.
- **`src/animus/rest/controllers/intake/__init__.py`** — exports de controllers de `intake`.

## Routers

- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) — registra controllers de análises.
- **`IntakeRouter`** (`src/animus/routers/intake/intake_router.py`) — compõe `/intake` e inclui `AnalysesRouter`.
- **`StorageRouter`** (`src/animus/routers/storage/storage_router.py`) — registra signed URL de documentos em `/storage`.

## Pipes

- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) — provider de repositórios SQLAlchemy via `Depends(...)`.
- **`IntakePipe`** (`src/animus/pipes/intake_pipe.py`) — valida ownership de `Analysis` por `account_id`.
- **`PubSubPipe`** (`src/animus/pipes/pubsub_pipe.py`) — provider de `Broker` usado por controllers assíncronos.
- **`AiPipe`** (`src/animus/pipes/ai_pipe.py`) — composition point dos workflows Agno.

## Storage / Providers

- **`GenerateAnalysisDocumentUploadUrlUseCase`** (`src/animus/core/storage/use_cases/generate_petition_upload_url_use_case.py`) — já gera path único por documento usando ULID.
- **`GenerateAnalysisDocumentUploadUrlController`** (`src/animus/rest/controllers/storage/generate_petition_upload_url_controller.py`) — endpoint `POST /storage/analyses/{analysis_id}/documents?document_type=pdf|docx`.
- **`FileStorageProvider`** (`src/animus/core/storage/interfaces/file_storage_provider.py`) — port de storage com `generate_upload_url(...)`, `get_file(...)` e `remove_files(...)`.
- **`GcsFileStorageProvider`** (`src/animus/providers/storage/file_storage/gcs/gcs_file_storage_provider.py`) — provider concreto usado para signed URL, leitura e remoção de arquivos.
- **`GetDocumentContentUseCase`** (`src/animus/core/storage/use_cases/get_document_content_use_case.py`) — extrai texto de PDF/DOCX via providers.

## AI

- **`AgnoSummarizeCaseAssessmentCaseWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_summarize_case_assessment_case_workflow.py`) — workflow atual de sumarização de `CASE_ASSESSMENT`, hoje baseado em conteúdo de documento único.
- **`CaseSummaryOutput`** (`src/animus/ai/agno/outputs/intake/case_summary_output.py`) — output estruturado já compatível com `CaseSummaryDto`.
- **`IntakeSquad.case_assessment_case_summarizer_agent`** (`src/animus/ai/agno/squads/intake_squad.py`) — agente que deve ter prompt atualizado para briefing + documentos.

## PubSub

- **`CaseAssessmentCaseSummarizationTriggeredEvent`** (`src/animus/core/intake/domain/events/case_assessment_case_summary_triggered_event.py`) — evento existente com `name = 'intake/case_assessment.case_summary.triggered'` e payload `analysis_id`.
- **`CaseSummaryFinishedEvent`** (`src/animus/core/intake/domain/events/case_summary_finished_event.py`) — evento de conclusão já usado por notificações.
- **`SummarizeCaseAssessmentCaseJob`** (`src/animus/pubsub/inngest/jobs/intake/summarize_case_assessment_case_job.py`) — job existente a alterar.
- **`InngestPubSub.register_intake_jobs(...)`** (`src/animus/pubsub/inngest/inngest_pubsub.py`) — já registra `SummarizeCaseAssessmentCaseJob`.

# 5. O que deve ser criado?

## Camada Core (Entidades / Structures / DTOs)

- **Localização:** `src/animus/core/intake/domain/structures/legal_area.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `value: LegalAreaValue`
- **Enum `LegalAreaValue`:** `CONSTITUCIONAL`, `ADMINISTRATIVO`, `TRIBUTARIO`, `PREVIDENCIARIO`, `CIVIL`, `FAMILIA_E_SUCESSOES`, `CONSUMIDOR`, `EMPRESARIAL`, `TRABALHISTA`, `PENAL`, `AMBIENTAL`, `PROCESSUAL`
- **Métodos / factory:**
  - `create(value: str) -> LegalArea` — normaliza `value.upper()`, valida contra `LegalAreaValue` e lança `ValidationError` se inválido.
  - `dto(self) -> str` — retorna `self.value.value`.

- **Localização:** `src/animus/core/intake/domain/structures/dtos/case_assessment_briefing_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `analysis_id: str`, `legal_area: str`, `court_jurisdiction: str`, `main_claims: str`, `intended_thesis: str`

- **Localização:** `src/animus/core/intake/domain/structures/case_assessment_briefing.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `analysis_id: Id`, `legal_area: LegalArea`, `court_jurisdiction: Court`, `main_claims: Text`, `intended_thesis: Text`
- **Métodos / factory:**
  - `create(dto: CaseAssessmentBriefingDto) -> CaseAssessmentBriefing` — valida `analysis_id`, `legal_area`, `court_jurisdiction` e campos textuais obrigatórios; rejeita `main_claims` e `intended_thesis` vazios após `strip()` com `ValidationError`.
  - `dto(self) -> CaseAssessmentBriefingDto` — serializa a structure para cruzar fronteiras.

## Camada Core (Erros de Domínio)

- **Localização:** `src/animus/core/intake/domain/errors/case_assessment_briefing_not_found_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** levantado quando o trigger de geração de resumo é solicitado sem briefing persistido.

## Camada Core (Interfaces / Ports)

- **Localização:** `src/animus/core/intake/interfaces/case_assessment_briefings_repository.py` (**novo arquivo**)
- **Métodos:**
  - `find_by_analysis_id(analysis_id: Id) -> CaseAssessmentBriefing | None` — busca briefing 1:1 por análise.
  - `add(briefing: CaseAssessmentBriefing) -> None` — adiciona briefing novo.
  - `replace(briefing: CaseAssessmentBriefing) -> None` — substitui briefing existente para a mesma análise; se não existir, adiciona.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/create_case_assessment_briefing_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `CaseAssessmentBriefingsRepository`, `CaseSummariesRepository`, `AnalysesRepository`
- **Método principal:**
  - `execute(analysis_id: str, legal_area: str, court_jurisdiction: str, main_claims: str, intended_thesis: str) -> CaseAssessmentBriefingDto` — cria ou substitui briefing, reseta `CaseSummary` existente e atualiza status para `BRIEFING_SUBMITTED`.
- **Fluxo resumido:** valida `analysis_id` → busca `Analysis` → valida `CASE_ASSESSMENT` → cria `CaseAssessmentBriefing` → `add(...)` ou `replace(...)` → remove `CaseSummary` existente → `analysis.set_status(BRIEFING_SUBMITTED)` → `AnalysesRepository.replace(...)` → retorna DTO.

## Camada Database (Models SQLAlchemy)

- **Localização:** `src/animus/database/sqlalchemy/models/intake/case_assessment_briefing_model.py` (**novo arquivo**)
- **Tabela:** `case_assessment_briefings`
- **Colunas:** `analysis_id String(26) primary key ForeignKey('analyses.id', ondelete='CASCADE')`, `legal_area String nullable=False`, `court_jurisdiction String nullable=False`, `main_claims Text nullable=False`, `intended_thesis Text nullable=False`, timestamps herdados de `Model`
- **Relacionamentos:** `analysis: Mapped[Any] = relationship('AnalysisModel', back_populates='case_assessment_briefing')`

## Camada Database (Mappers)

- **Localização:** `src/animus/database/sqlalchemy/mappers/intake/case_assessment_briefing_mapper.py` (**novo arquivo**)
- **Métodos:**
  - `to_entity(model: CaseAssessmentBriefingModel) -> CaseAssessmentBriefing` — cria `CaseAssessmentBriefing` a partir do model.
  - `to_model(briefing: CaseAssessmentBriefing) -> CaseAssessmentBriefingModel` — cria model SQLAlchemy a partir da structure.

## Camada Database (Repositórios)

- **Localização:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_case_assessment_briefings_repository.py` (**novo arquivo**)
- **Interface implementada:** `CaseAssessmentBriefingsRepository`
- **Dependências:** `Session` SQLAlchemy
- **Métodos:**
  - `__init__(sqlalchemy: Session) -> None` — recebe sessão do escopo transacional.
  - `find_by_analysis_id(analysis_id: Id) -> CaseAssessmentBriefing | None` — usa `Session.get(CaseAssessmentBriefingModel, analysis_id.value)`.
  - `add(briefing: CaseAssessmentBriefing) -> None` — adiciona model mapeado à sessão.
  - `replace(briefing: CaseAssessmentBriefing) -> None` — atualiza campos do model existente ou delega para `add(...)`.
- **Seeders da camada database:** não há `seeders` impactados; não criar dados seed para briefing nesta spec.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/create_case_assessment_briefing_controller.py` (**novo arquivo**)
- **`_Body`:** `BaseModel` no mesmo arquivo com `legal_area: str`, `court_jurisdiction: str`, `main_claims: str`, `intended_thesis: str`; validação de domínio fica no use case via `LegalArea`, `Court` e `CaseAssessmentBriefing`.
- **Método HTTP e path:** `POST /analyses/{analysis_id}/case-assessment-briefing` dentro do prefixo `/intake`
- **`status_code`:** `201`
- **`response_model`:** `CaseAssessmentBriefingDto`
- **Dependências injetadas via `Depends`:** `IntakePipe.verify_analysis_by_account_from_request`, `DatabasePipe.get_case_assessment_briefings_repository_from_request`, `DatabasePipe.get_case_summaries_repository_from_request`, `DatabasePipe.get_analyses_repository_from_request`
- **Fluxo:** `_Body` → named params diretos → `CreateCaseAssessmentBriefingUseCase.execute(...)` → `CaseAssessmentBriefingDto`

## Camada Pipes

- **Localização:** `src/animus/pipes/database_pipe.py` (**arquivo existente**)
- **Método `Depends`:**
  - `get_case_assessment_briefings_repository_from_request(sqlalchemy: Annotated[Session, Depends(get_sqlalchemy_session_from_request)]) -> CaseAssessmentBriefingsRepository` — provê `SqlalchemyCaseAssessmentBriefingsRepository`.
- **Sessão SQLAlchemy:** obtida por `get_sqlalchemy_session_from_request(request.state.sqlalchemy_session)`.

## Camada PubSub (Eventos de Domínio)

- **Não aplicável.** Reutilizar `CaseAssessmentCaseSummarizationTriggeredEvent` existente em `src/animus/core/intake/domain/events/case_assessment_case_summary_triggered_event.py`.

## Migrações Alembic

- **Localização:** `migrations/versions/` (**novo arquivo**)
- **Operações:** criar tabela `case_assessment_briefings`; alterar `analysis_documents` para permitir múltiplos documentos por `analysis_id`; atualizar registros `CASE_ASSESSMENT` em `analyses.status` de `WAITING_DOCUMENT_UPLOAD` para `WAITING_BRIEFING` e de `DOCUMENT_UPLOADED` para `BRIEFING_SUBMITTED`; ajustar constraints/índices de `analysis_documents`.
- **Reversibilidade:** `downgrade` pode remover `case_assessment_briefings`, restaurar status antigos e restaurar `analysis_documents.analysis_id` como primary key apenas se não houver múltiplos documentos por análise; caso contrário, o downgrade deve documentar perda de dados por colapsar múltiplos documentos em um.

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/structures/case_assessment_analysis_status.py`
- **Mudança:** substituir `WAITING_DOCUMENT_UPLOAD` por `WAITING_BRIEFING`, substituir `DOCUMENT_UPLOADED` por `BRIEFING_SUBMITTED`, criar `create_as_waiting_briefing() -> CaseAssessmentAnalysisStatus` e `create_as_briefing_submitted() -> CaseAssessmentAnalysisStatus`.
- **Justificativa:** o gate inicial do fluxo do advogado passa a ser o briefing, não upload de documento.

- **Arquivo:** `src/animus/core/intake/use_cases/create_analysis_use_case.py`
- **Mudança:** para `AnalysisType.CASE_ASSESSMENT`, usar `CaseAssessmentAnalysisStatus.create_as_waiting_briefing()`; manter `SecondInstanceAnalysisStatus.create_as_waiting_document_upload()` para `SECOND_INSTANCE`.
- **Justificativa:** preservar fluxo do juiz e alterar apenas o fluxo do advogado.

- **Arquivo:** `src/animus/core/intake/interfaces/analysis_documents_repository.py`
- **Mudança:** adicionar `find_many_by_analysis_id(analysis_id: Id) -> list[AnalysisDocument]` e `remove_by_file_path(file_path: FilePath) -> None`; manter `find_by_analysis_id(...) -> AnalysisDocument | None` para compatibilidade.
- **Justificativa:** o novo job precisa de zero ou mais documentos, enquanto fluxos antigos ainda dependem de documento único.

- **Arquivo:** `src/animus/core/intake/interfaces/case_summaries_repository.py`
- **Mudança:** adicionar `remove_by_analysis_id(analysis_id: Id) -> None`.
- **Justificativa:** ressubmissão do briefing deve resetar `CaseSummary` existente.

- **Arquivo:** `src/animus/core/intake/interfaces/summarize_case_workflow.py`
- **Mudança:** alterar `SummarizeCaseAssessmentCaseWorkflow.run(...)` para `run(analysis_id: str, briefing: CaseAssessmentBriefingDto, document_contents: list[Text]) -> CaseSummaryDto`.
- **Justificativa:** o resumo de `CASE_ASSESSMENT` passa a ser derivado de briefing obrigatório e documentos opcionais.

- **Arquivo:** `src/animus/core/intake/use_cases/create_analysis_document_use_case.py`
- **Mudança:** para `CASE_ASSESSMENT`, sempre `add(document)` e não alterar status; para `FIRST_INSTANCE` e `SECOND_INSTANCE`, manter replace do documento anterior, publicação de `AnalysisDocumentReplacedEvent` e atualização para `DOCUMENT_UPLOADED`.
- **Justificativa:** documentos de apoio do advogado não são gate de status e podem ser múltiplos.

- **Arquivo:** `src/animus/core/intake/use_cases/remove_analysis_document_use_case.py`
- **Mudança:** buscar documento por `file_path`, validar que pertence ao `analysis_id`, remover via `remove_by_file_path(...)`; para `CASE_ASSESSMENT`, não alterar status; para demais tipos, manter retorno ao status de aguardando documento quando o documento único for removido.
- **Justificativa:** remoção por análise não é suficiente quando há múltiplos documentos.

- **Arquivo:** `src/animus/core/intake/use_cases/get_analysis_document_use_case.py`
- **Mudança:** manter retorno de um único documento para compatibilidade; documentar que, em `CASE_ASSESSMENT`, esse use case não representa a lista completa.
- **Justificativa:** evitar quebra imediata dos consumidores legados; a listagem de documentos não está especificada no PRD.

- **Arquivo:** `src/animus/core/intake/use_cases/create_case_summary_use_case.py`
- **Mudança:** remover a pré-condição de `AnalysisDocument` obrigatório; manter validação de `Analysis` e persistência idempotente do `CaseSummary`.
- **Justificativa:** `CASE_ASSESSMENT` pode gerar resumo sem documentos; o gate passa a ser `CaseAssessmentBriefing` no trigger/job.

- **Arquivo:** `src/animus/core/intake/use_cases/get_case_assessment_analysis_report_use_case.py`
- **Mudança:** injetar `CaseAssessmentBriefingsRepository`, carregar o briefing por `analysis_id`, falhar com `CaseAssessmentBriefingNotFoundError` quando ausente e incluir o briefing no `CaseAssessmentAnalysisReport` retornado.
- **Justificativa:** consolidar no report todos os insumos principais da análise inicial, incluindo o formulário estruturado do advogado.

- **Arquivo:** `src/animus/core/intake/use_cases/trigger_case_assessment_case_summarization_use_case.py`
- **Mudança:** trocar dependência `AnalysisDocumentsRepository` por `CaseAssessmentBriefingsRepository`; validar briefing persistido; manter validação de análise, tipo `CASE_ASSESSMENT`, atualização para `ANALYZING_CASE` e publicação de evento.
- **Justificativa:** a pré-condição funcional agora é briefing submetido.

- **Arquivo:** `src/animus/core/intake/domain/structures/__init__.py`
- **Mudança:** exportar `LegalArea`, `LegalAreaValue` e `CaseAssessmentBriefing`.
- **Justificativa:** manter padrão de exports públicos do domínio.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/__init__.py`
- **Mudança:** exportar `CaseAssessmentBriefingDto`.
- **Justificativa:** manter lazy exports de DTOs do contexto.

- **Arquivo:** `src/animus/core/intake/domain/structures/case_assessment_analysis_report.py`
- **Mudança:** adicionar `briefing: CaseAssessmentBriefing` ao agregado e serializar o campo em `CaseAssessmentAnalysisReportDto`.
- **Justificativa:** o cliente precisa recuperar no report os dados estruturados submetidos pelo advogado.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/case_assessment_analysis_report_dto.py`
- **Mudança:** adicionar `briefing: CaseAssessmentBriefingDto` ao contrato do relatório.
- **Justificativa:** refletir o briefing persistido no payload do report sem exigir nova chamada dedicada.

- **Arquivo:** `src/animus/core/intake/domain/errors/__init__.py`
- **Mudança:** exportar `CaseAssessmentBriefingNotFoundError`.
- **Justificativa:** disponibilizar erro de domínio aos use cases/controllers.

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudança:** exportar `CaseAssessmentBriefingsRepository`.
- **Justificativa:** permitir uso consistente nos pipes e jobs.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** exportar `CreateCaseAssessmentBriefingUseCase`.
- **Justificativa:** seguir padrão de exports de use cases do contexto.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/analysis_document_model.py`
- **Mudança:** remover `primary_key=True` de `analysis_id`, tornar `document_file_path` a chave primária ou chave única material de identidade, adicionar índice em `analysis_id` e manter FK cascade para `analyses.id`.
- **Justificativa:** permitir múltiplos documentos por análise sem criar novo DTO com `id` artificial.

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/analysis_model.py`
- **Mudança:** trocar relacionamento `document` 1:1 por relacionamento `documents` 1:N e adicionar `case_assessment_briefing` 1:1.
- **Justificativa:** refletir cardinalidade nova sem afetar contratos de domínio diretamente.

- **Arquivo:** `src/animus/database/sqlalchemy/mappers/intake/analysis_document_mapper.py`
- **Mudança:** manter mapeamento de `analysis_id`, `uploaded_at`, `document_file_path` e `document_name`.
- **Justificativa:** a estrutura pública de documento não precisa mudar para suportar múltiplos registros.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analysis_documents_repository.py`
- **Mudança:** implementar `find_many_by_analysis_id(...)`, alterar `find_by_analysis_id(...)` para retornar o documento mais recente por `uploaded_at` quando houver múltiplos, implementar `remove_by_file_path(...)` e ajustar `replace(...)` para compatibilidade com fluxos de documento único.
- **Justificativa:** job novo precisa de lista; fluxos antigos precisam continuar usando documento único.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_case_summaries_repository.py`
- **Mudança:** implementar `remove_by_analysis_id(analysis_id: Id) -> None`.
- **Justificativa:** permitir reset de resumo em ressubmissão do briefing.

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/__init__.py`
- **Mudança:** exportar `CaseAssessmentBriefingModel`.
- **Justificativa:** manter registry/imports de models do contexto.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/__init__.py`
- **Mudança:** exportar `SqlalchemyCaseAssessmentBriefingsRepository`.
- **Justificativa:** permitir wiring pelo `DatabasePipe`.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/trigger_case_assessment_case_summarization_controller.py`
- **Mudança:** ajustar path para `POST /analyses/{analysis_id}/case-summary`, trocar dependência de `AnalysisDocumentsRepository` por `CaseAssessmentBriefingsRepository` e instanciar `TriggerCaseAssessmentCaseSummarizationUseCase` com briefing repository.
- **Justificativa:** alinhar endpoint ao esboço da tarefa e à nova pré-condição de briefing.

- **Arquivo:** `src/animus/rest/controllers/intake/create_analysis_document_controller.py`
- **Mudança:** manter endpoint e body atuais; comportamento passa a variar por `Analysis.type` dentro do use case.
- **Justificativa:** signed URL e persistência de metadados já suportam chamadas repetidas; a regra de múltiplos documentos é de domínio.

- **Arquivo:** `src/animus/rest/controllers/intake/remove_analysis_document_controller.py`
- **Mudança:** manter query param `file_path`; delegar remoção por file path ao use case.
- **Justificativa:** `file_path` é a identidade prática do documento após suportar múltiplos por análise.

- **Arquivo:** `src/animus/rest/controllers/intake/get_analysis_document_controller.py`
- **Mudança:** manter contrato atual de retorno único; não criar listagem nesta spec.
- **Justificativa:** PRD não especifica endpoint de listagem e o app pode controlar documentos enviados durante o fluxo.

- **Arquivo:** `src/animus/rest/controllers/intake/get_case_assessment_analysis_report_controller.py`
- **Mudança:** injetar `CaseAssessmentBriefingsRepository` e repassar a dependência ao `GetCaseAssessmentAnalysisReportUseCase`.
- **Justificativa:** o report passa a depender do briefing persistido para compor a resposta completa.

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** exportar `CreateCaseAssessmentBriefingController`.
- **Justificativa:** manter composição de controllers.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** registrar `CreateCaseAssessmentBriefingController.handle(router)`.
- **Justificativa:** expor o novo endpoint sob `/intake`.

## Pipes

- **Arquivo:** `src/animus/pipes/database_pipe.py`
- **Mudança:** importar `CaseAssessmentBriefingsRepository` e `SqlalchemyCaseAssessmentBriefingsRepository`, criar provider `get_case_assessment_briefings_repository_from_request(...)`.
- **Justificativa:** manter controllers finos e dependência por port.

## AI

- **Arquivo:** `src/animus/pipes/ai_pipe.py`
- **Mudança:** ajustar `get_summarize_case_assessment_case_workflow(...)` para não receber `AnalysisDocumentsRepository` e retornar workflow compatível com briefing; manter `CaseSummariesRepository` e `AnalysesRepository` se o workflow continuar persistindo via `CreateCaseSummaryUseCase`.
- **Justificativa:** documents passam a ser carregados pelo job e enviados como conteúdo, não buscados pelo workflow.

- **Arquivo:** `src/animus/ai/agno/workflows/intake/agno_summarize_case_assessment_case_workflow.py`
- **Mudança:** alterar assinatura para `run(analysis_id: str, briefing: CaseAssessmentBriefingDto, document_contents: list[Text]) -> CaseSummaryDto`; montar prompt com briefing obrigatório e documentos opcionais; após normalizar output da IA, sobrescrever `legal_issue`, `central_question` e `key_facts` com dados do briefing; persistir via `CreateCaseSummaryUseCase`.
- **Justificativa:** cumprir o PRD de autoridade do advogado nos campos centrais sem alterar o contrato downstream.

- **Arquivo:** `src/animus/ai/agno/squads/intake_squad.py`
- **Mudança:** atualizar instruções de `case_assessment_case_summarizer_agent` para gerar resumo a partir de formulário estruturado e documentos opcionais.
- **Justificativa:** prompt atual assume documento jurídico único.

## PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_case_assessment_case_job.py`
- **Mudança:** em `_summarize_case_sync(...)`, instanciar `SqlalchemyCaseAssessmentBriefingsRepository`, carregar briefing obrigatório, carregar `analysis_documents_repository.find_many_by_analysis_id(...)`, extrair conteúdos em lista, chamar workflow com `briefing` e `document_contents`, manter publicação de `CaseSummaryFinishedEvent` e falha para `FAILED`.
- **Justificativa:** job passa a ser o orquestrador de briefing + docs opcionais.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/__init__.py`
- **Mudança:** não alterar registro se `SummarizeCaseAssessmentCaseJob` permanecer com o mesmo nome.
- **Justificativa:** job já está exportado.

- **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
- **Mudança:** não alterar registro se o mesmo job existente for modificado.
- **Justificativa:** `SummarizeCaseAssessmentCaseJob.handle(inngest)` já está em `register_intake_jobs(...)`.

# 7. O que deve ser removido?

## Core

- **Arquivo:** `src/animus/core/intake/domain/structures/case_assessment_analysis_status.py`
- **Motivo da remoção:** remover os valores `WAITING_DOCUMENT_UPLOAD` e `DOCUMENT_UPLOADED` apenas do enum `CaseAssessmentAnalysisStatusValue`, porque o fluxo `CASE_ASSESSMENT` não é mais gated por documento.
- **Impacto esperado:** atualizar factories e referências em `CreateAnalysisUseCase`, `CreateAnalysisDocumentUseCase`, `RemoveAnalysisDocumentUseCase` e qualquer comparação de status de `CASE_ASSESSMENT`.

## Core / Use Cases

- **Arquivo:** `src/animus/core/intake/use_cases/trigger_case_assessment_case_summarization_use_case.py`
- **Motivo da remoção:** remover pré-condição de `AnalysisDocument` obrigatório para gerar resumo.
- **Impacto esperado:** substituir por `CaseAssessmentBriefingNotFoundError` quando não houver briefing.

- **Arquivo:** `src/animus/core/intake/use_cases/create_case_summary_use_case.py`
- **Motivo da remoção:** remover dependência e check de `AnalysisDocumentsRepository` para criação de `CaseSummary`.
- **Impacto esperado:** ajustar construtor e todos os call sites, especialmente workflows de sumarização; validar se fluxos `FIRST_INSTANCE` e `SECOND_INSTANCE` ainda fazem suas próprias pré-condições antes de chamar esse use case.

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** `LegalArea` será uma `Structure` com enum fechado.
- **Alternativas consideradas:** modelar `legal_area` como `str` livre; criar enum apenas na borda HTTP; modelar apenas como `Text`.
- **Motivo da escolha:** decisão confirmada via `question` durante a elaboração da spec e alinhada ao esboço atual da tarefa.
- **Impactos / trade-offs:** reduz flexibilidade futura e exige alteração de enum se novas áreas forem necessárias.

- **Decisão:** `CaseAssessmentBriefing` será `@structure`, não `@entity`.
- **Alternativas consideradas:** criar entidade com `id` próprio; usar apenas DTO sem domínio; embutir briefing em `Analysis`.
- **Motivo da escolha:** o padrão existente usa `@structure` para dados 1:1 dependentes de `Analysis`, como `CaseSummary` e `AnalysisDocument`; `analysis_id` é a identidade persistente suficiente.
- **Impactos / trade-offs:** evita ID extra e simplifica repository, mas não oferece histórico/versionamento de briefings.

- **Decisão:** múltiplos documentos serão suportados alterando `analysis_documents` para identidade por `document_file_path` e mantendo `AnalysisDocumentDto` sem `id` novo.
- **Alternativas consideradas:** criar `analysis_document_id`; criar tabela separada para documentos de apoio; manter 1:1 e criar campo JSON.
- **Motivo da escolha:** o signed URL já gera `file_path` único com ULID e o endpoint de remoção já recebe `file_path`; é a menor mudança compatível.
- **Impactos / trade-offs:** usar path como identidade técnica acopla remoção/persistência ao storage path, mas evita quebra de DTO público.

- **Decisão:** o trigger de resumo atualizará status para `ANALYZING_CASE` antes de publicar evento.
- **Alternativas consideradas:** deixar o job fazer a primeira atualização de status.
- **Motivo da escolha:** segue o padrão atual de `TriggerCaseAssessmentCaseSummarizationUseCase` e dá feedback imediato por polling.
- **Impactos / trade-offs:** se a publicação falhar após status alterado, a transação por request deve garantir atomicidade; se o broker falhar fora da transação, pode haver status sem job.

- **Decisão:** ressubmissão do briefing reseta apenas `CaseSummary`.
- **Alternativas consideradas:** remover também precedentes, escolhas e minuta; manter todos os dados antigos; versionar tudo.
- **Motivo da escolha:** o esboço da tarefa menciona explicitamente reset do `CaseSummary`, mas não especifica reset downstream.
- **Impactos / trade-offs:** dados downstream antigos podem permanecer no banco; o status `BRIEFING_SUBMITTED` deve impedir o fluxo de exibir resultados como atuais até nova geração.

- **Decisão:** não criar endpoint de listagem de documentos nesta spec.
- **Alternativas consideradas:** alterar `GET /analyses/{analysis_id}/documents` para retornar lista; criar `GET /analyses/{analysis_id}/documents/list`.
- **Motivo da escolha:** PRD/esboço exigem suporte a múltiplos uploads, mas não especificam contrato de listagem; alterar resposta existente de DTO único para lista seria quebra explícita.
- **Impactos / trade-offs:** o app deve controlar documentos anexados no fluxo de submissão ou uma spec futura deve definir a listagem.

# 9. Diagramas e Referências

- **Fluxo de dados:**

```text
HTTP POST /intake/analyses/{analysis_id}/case-assessment-briefing
  -> Middleware SQLAlchemy/Auth
  -> IntakeRouter / AnalysesRouter
  -> CreateCaseAssessmentBriefingController
  -> IntakePipe.verify_analysis_by_account_from_request
  -> DatabasePipe.get_case_assessment_briefings_repository_from_request
  -> CreateCaseAssessmentBriefingUseCase
  -> CaseAssessmentBriefingsRepository / CaseSummariesRepository / AnalysesRepository
  -> SqlalchemyCaseAssessmentBriefingsRepository / SqlalchemyCaseSummariesRepository / SqlalchemyAnalysesRepository
  -> PostgreSQL (case_assessment_briefings, case_summaries, analyses)
  -> 201 CaseAssessmentBriefingDto
```

- **Fluxo assíncrono:**

```text
HTTP POST /intake/analyses/{analysis_id}/case-summary
  -> TriggerCaseAssessmentCaseSummarizationController
  -> TriggerCaseAssessmentCaseSummarizationUseCase
  -> CaseAssessmentBriefingsRepository.find_by_analysis_id
  -> AnalysesRepository.replace(status=ANALYZING_CASE)
  -> Broker.publish(CaseAssessmentCaseSummarizationTriggeredEvent)
  -> Inngest SummarizeCaseAssessmentCaseJob
  -> CaseAssessmentBriefingsRepository.find_by_analysis_id
  -> AnalysisDocumentsRepository.find_many_by_analysis_id
  -> GetDocumentContentUseCase for each document
  -> AgnoSummarizeCaseAssessmentCaseWorkflow.run(briefing, document_contents)
  -> CreateCaseSummaryUseCase
  -> CaseSummariesRepository.add/replace
  -> AnalysesRepository.replace(status=CASE_ANALYZED)
  -> InngestBroker.publish(CaseSummaryFinishedEvent)
```

- **Referências:**

- `src/animus/core/intake/domain/structures/court.py` — padrão de `Structure` com `StrEnum` e `ValidationError`.
- `src/animus/core/intake/domain/structures/analysis_document.py` — padrão de structure 1:1 dependente de `Analysis`.
- `src/animus/core/intake/domain/structures/case_summary.py` — padrão de structure persistida e DTO downstream.
- `src/animus/core/intake/use_cases/create_analysis_document_use_case.py` — referência para criação de documento e status por tipo de análise.
- `src/animus/core/intake/use_cases/trigger_case_assessment_case_summarization_use_case.py` — referência de trigger assíncrono existente a adaptar.
- `src/animus/rest/controllers/intake/create_analysis_document_controller.py` — padrão de controller fino com `_Body` local e `Depends`.
- `src/animus/rest/controllers/intake/trigger_case_assessment_case_summarization_controller.py` — padrão de endpoint `202` sem body para trigger.
- `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_case_summaries_repository.py` — padrão de repository 1:1 com `add(...)` e `replace(...)`.
- `src/animus/pubsub/inngest/jobs/intake/summarize_case_assessment_case_job.py` — job existente a modificar.
- `src/animus/ai/agno/workflows/intake/agno_summarize_case_assessment_case_workflow.py` — workflow existente a modificar.
- `src/animus/providers/storage/file_storage/gcs/gcs_file_storage_provider.py` — signed URL e leitura de arquivos no GCS.

# 10. Pendências / Dúvidas

Sem pendências.
