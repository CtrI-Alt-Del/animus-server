---
title: ANI-92 - Case summary, analysis document, reports e status tipado por tipo de analise no intake
prd: documentation/features/intake/analyses-management/prd.md
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-92
status: closed
last_updated_at: 2026-05-16
---

# 1. Objetivo

Refatorar o dominio `intake` para suportar tres tipos de analise distintos, **CaseAssessmentAnalysis**, **FirstInstanceAnalysis** e **SecondInstanceAnalysis**, removendo o conceito legado de `Petition` como agregado principal de documento, introduzindo `AnalysisDocument` como artefato unico por analise, renomeando `PetitionSummary` para `CaseSummary`, tipando `Analysis.type` por `AnalysisType` e `Analysis.status` por contratos de status por tipo, adicionando os contratos persistidos de `PetitionDraft` e `SecondInstanceJudgmentDraft`, e expandindo a superficie HTTP com relatorios separados por tipo. Nesta etapa, `LAWYER` e normalizado para `CASE_ASSESSMENT`, `JUDGE` e normalizado para `SECOND_INSTANCE`, e `FIRST_INSTANCE` possui contrato dedicado de status sem reutilizar mais o tipo concreto de `CASE_ASSESSMENT`.

---

# 2. Escopo

## 2.1 In-scope

- Renomear `PetitionSummary*` para `CaseSummary*` em `core`, `database`, `rest`, `pipes`, `pubsub`, `providers`, `ai` e exports publicos.
- Substituir o conceito `Petition` por `AnalysisDocument` nos fluxos sincronos e assincronos do resumo do caso.
- Criar `AnalysisDocument` e seu contrato de persistencia, leitura e escrita por `analysis_id`.
- Criar `PetitionDraft`, `PetitionDraftDto`, `PetitionDraftsRepository`, `SecondInstanceJudgmentDraft`, `SecondInstanceJudgmentDraftDto` e `SecondInstanceJudgmentDraftsRepository` como contratos persistidos do novo dominio.
- Adicionar `Analysis.type` em `Analysis` e `AnalysisDto`, com valores `CASE_ASSESSMENT`, `FIRST_INSTANCE` e `SECOND_INSTANCE`.
- Remover `AnalysisStatus` e `AnalysisStatusValue` como abstrações canonicas do dominio e substitui-los por contratos tipados de status, com `CaseAssessmentAnalysisStatus | FirstInstanceAnalysisStatus | SecondInstanceAnalysisStatus` no estado atual do codigo.
- Renomear `WAITING_PETITION` para `WAITING_DOCUMENT_UPLOAD` em todos os fluxos e contratos de dominio.
- Atualizar os fluxos atuais de upload/substituicao de documento, request de resumo, leitura de resumo, busca de precedentes, listagem, polling de processamento, relatorio e notificacao para os novos contratos.
- Adicionar endpoints de report dedicados por tipo de analise: `case-assessment-report`, `first-instance-report` e `second-instance-report`.
- Atualizar migrations para renomear tabelas e colunas e criar as tabelas/estruturas faltantes dos drafts.

## 2.2 Out-of-scope

- Implementar o job de geracao de `PetitionDraft`; esta entrega cria o contrato e a persistencia, mas nao o pipeline do `ANI-93`.
- Implementar o job de geracao de `SecondInstanceJudgmentDraft`; esta entrega cria o contrato e a persistencia, mas nao o pipeline do `ANI-94`.
- Implementar o endpoint de leitura de `SecondInstanceJudgmentDraft`; isso continua dependente do `ANI-114`.
- Alterar o algoritmo de busca vetorial, ranking ou classificacao de precedentes.
- Alterar autenticacao, ownership ou regras globais de traducao de erro ja existentes.

---

# 3. Requisitos

## 3.1 Funcionais

- O servidor deve persistir `Analysis.type` com dominio fechado em `CASE_ASSESSMENT`, `FIRST_INSTANCE` ou `SECOND_INSTANCE`.
- `POST /intake/analyses` deve receber `type` no body e criar a analise com status inicial `WAITING_DOCUMENT_UPLOAD`.
- O documento associado a uma analise deve deixar de ser representado por `Petition` e passar a ser representado por `AnalysisDocument`, com os campos `analysis_id`, `uploaded_at`, `file_path` e `name`.
- Deve existir no maximo um `AnalysisDocument` ativo por analise; novo upload substitui o anterior no mesmo fluxo ja existente hoje para `Petition`.
- O resumo estruturado do caso deve ser persistido como `CaseSummary` e consultado por `analysis_id`, nao por `petition_id`.
- O request assíncrono de resumo deve partir de `analysis_id`, buscar `AnalysisDocument`, mover a analise para o status de processamento adequado e publicar `CaseSummaryCaseSummarizationTriggeredEvent`.
- O dominio de `CASE_ASSESSMENT` deve aceitar os status `WAITING_DOCUMENT_UPLOAD`, `DOCUMENT_UPLOADED`, `ANALYZING_CASE`, `CASE_ANALYZED`, `SEARCHING_PRECEDENTS`, `GENERATING_PETITION_DRAFT`, `DONE` e `FAILED`.
- O dominio de `SECOND_INSTANCE` deve aceitar os status `WAITING_DOCUMENT_UPLOAD`, `DOCUMENT_UPLOADED`, `EXTRACTING_PETITION`, `ANALYZING_CASE`, `CASE_ANALYZED`, `SEARCHING_PRECEDENTS`, `GENERATING_JUDGMENT_DRAFT`, `DONE` e `FAILED`.
- `FIRST_INSTANCE` deve usar `FirstInstanceAnalysisStatus` como contrato concreto de status no agregado `Analysis`.
- `Analysis.status` deve passar a ser serializado a partir de `CaseAssessmentAnalysisStatus | FirstInstanceAnalysisStatus | SecondInstanceAnalysisStatus`, sem wrapper `AnalysisStatus` como fonte canonica.
- Os artefatos `PetitionDraft` e `SecondInstanceJudgmentDraft` devem existir como contratos de leitura/escrita por `analysis_id`, mesmo que seus pipelines de geracao sejam entregues depois.
- Os fluxos centrados em `analysis` devem ser expostos por:
- `POST /intake/analyses/{analysis_id}/document`
- `GET /intake/analyses/{analysis_id}/document`
- `POST /intake/analyses/{analysis_id}/case-summaries`
- `GET /intake/analyses/{analysis_id}/case-summaries`
- `GET /intake/analyses/{analysis_id}/case-assessment-report`
- `GET /intake/analyses/{analysis_id}/first-instance-report`
- `GET /intake/analyses/{analysis_id}/second-instance-report`
- As rotas legadas de `petitions` ainda coexistem no codigo durante a transicao e nao devem ser tratadas como removidas nesta spec incremental.
- Eventos, controllers, jobs, providers e caminhos de arquivos que hoje carregam o nome `petition_summary` devem ser renomeados para `case_summary`.

## 3.2 Nao funcionais

- **Compatibilidade de dados:** migrations devem preservar os dados hoje em `petitions` e `petition_summaries`, migrando-os para os novos contratos centrados em `analysis` sem perda de informacao.
- **Compatibilidade HTTP:** os endpoints novos de `analysis` e os endpoints legados de `petitions` coexistem temporariamente; a remocao final das rotas antigas continua sendo breaking e exige coordenacao com o cliente mobile.
- **Performance:** `SqlalchemyAnalysesRepository.find_many(...)` e `find_many_in_processing(...)` devem continuar sem joins adicionais; a troca de status nao deve degradar o polling ou a paginacao principal.
- **Observabilidade:** nomes de eventos, jobs, payloads e logs devem deixar de usar `petition_summary` e refletir `case_summary`.
- **Seguranca:** ownership continua validado por `analysis_id` da conta autenticada; a mudanca nao deve mover regra de acesso para `database`, `router` ou `provider`.

---

# 4. O que ja existe?

## Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analyses.py`) - agregado principal da analise; hoje ja possui `type`, normalizacao de valores legados (`LAWYER` -> `CASE_ASSESSMENT`, `JUDGE` -> `SECOND_INSTANCE`) e serializacao direta de status por tipo.
- **`AnalysisStatus` e `AnalysisStatusValue`** (`src/animus/core/intake/domain/entities/analysis_status.py`) - contrato legado ainda existente para compatibilidade e testes, mas nao e mais a fonte canonica do dominio.
- **`AnalysisDto`** (`src/animus/core/intake/domain/entities/dtos/analysis_dto.py`) - contrato publico de analise; ja possui `type`.
- **`Petition`** (`src/animus/core/intake/domain/entities/petition.py`) - entidade atual do documento da analise; sera substituida por `AnalysisDocument`.
- **`PetitionDto`** (`src/animus/core/intake/domain/entities/dtos/petition_dto.py`) - DTO atual do documento; sera substituido por `AnalysisDocumentDto`.
- **`PetitionsRepository`** (`src/animus/core/intake/interfaces/petitions_repository.py`) - port atual do documento, ainda centrado em `petition_id`.
- **`CreatePetitionUseCase`** (`src/animus/core/intake/use_cases/create_petition_use_case.py`) - fluxo atual de upsert do documento da analise.
- **`GetAnalysisPetitionUseCase`** (`src/animus/core/intake/use_cases/get_analysis_petition_use_case.py`) - leitura atual do documento por analise.
- **`PetitionSummary`** (`src/animus/core/intake/domain/structures/petition_summary.py`) - estrutura atual do resumo, ja usando o campo `case_summary`, mas com nomenclatura legada.
- **`PetitionSummaryDto`** (`src/animus/core/intake/domain/structures/dtos/petition_summary_dto.py`) - DTO atual do resumo estruturado.
- **`PetitionSummariesRepository`** (`src/animus/core/intake/interfaces/petition_summaries_repository.py`) - port atual do resumo, ainda centrado em `petition_id`.
- **`TriggerFistInstanceCaseSummarizationUseCase`** (`src/animus/core/intake/use_cases/request_petition_summary_use_case.py`) - request assíncrono de resumo, ainda centrado em `petition_id`.
- **`CreatePetitionSummaryUseCase`** (`src/animus/core/intake/use_cases/create_petition_summary_use_case.py`) - persistencia do resumo atual, ainda ligada a `PetitionsRepository`.
- **`GetPetitionSummaryUseCase`** (`src/animus/core/intake/use_cases/get_petition_summary_use_case.py`) - leitura do resumo por `petition_id`.
- **`SearchAnalysisPrecedentsUseCase`** (`src/animus/core/intake/use_cases/search_analysis_precedents_use_case.py`) - depende de `PetitionSummariesRepository` e do provider de embeddings do resumo.
- **`GetCaseAssessmentAnalysisReportUseCase`** (`src/animus/core/intake/use_cases/get_case_assessment_analysis_report_use_case.py`) - agrega `Analysis`, `AnalysisDocument`, `CaseSummary`, precedentes e `PetitionDraft`.
- **`GetFirstInstanceAnalysisReportUseCase`** (`src/animus/core/intake/use_cases/get_first_instance_analysis_report_use_case.py`) - agrega `Analysis`, `AnalysisDocument`, `CaseSummary`, precedentes e `SecondInstanceJudgmentDraft`.
- **`GetSecondInstanceAnalysisReportUseCase`** (`src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`) - agrega `Analysis`, `AnalysisDocument`, `CaseSummary`, `precedents` e `draft` opcional.

## Database

- **`AnalysisModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_model.py`) - model atual de `analyses`; ja possui `type`, `document`, `case_summary`, `petition_draft` e `judgment_draft`.
- **`SqlalchemyAnalysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analyses_repository.py`) - usa `AnalysisStatusValue` nos filtros de listagem e processamento.
- **`PetitionModel`** (`src/animus/database/sqlalchemy/models/intake/petition_model.py`) - tabela atual do documento da analise, com `id`, `analysis_id`, `uploaded_at`, `document_file_path` e `document_name`.
- **`SqlalchemyPetitionsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petitions_repository.py`) - implementacao concreta atual do documento.
- **`PetitionSummaryModel`** (`src/animus/database/sqlalchemy/models/intake/petition_summary_model.py`) - model atual do resumo estruturado.
- **`SqlalchemyPetitionSummariesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_summaries_repository.py`) - implementacao concreta atual do resumo.

## REST

- **`CreateAnalysisController`** (`src/animus/rest/controllers/intake/create_analysis_controller.py`) - cria analise com `type` obrigatorio.
- **`CreatePetitionController`** (`src/animus/rest/controllers/intake/create_petition_controller.py`) - expõe `POST /petitions` para upsert do documento da analise.
- **`GetAnalysisPetitionController`** (`src/animus/rest/controllers/intake/get_analysis_petition_controller.py`) - expõe `GET /analyses/{analysis_id}/petition`.
- **`SummarizePetitionController`** (`src/animus/rest/controllers/intake/summarize_petition_controller.py`) - expõe `POST /petitions/{petition_id}/summary`.
- **`GetPetitionSummaryController`** (`src/animus/rest/controllers/intake/get_petition_summary_controller.py`) - expõe `GET /petitions/{petition_id}/summary`.
- **`GetAnalysisStatusController`** (`src/animus/rest/controllers/intake/get_analysis_status_controller.py`) - devolve `AnalysisStatusDto` a partir de `analysis.status.dto`.
- **`UpdateAnalysisStatusController`** (`src/animus/rest/controllers/intake/update_analysis_status_controller.py`) - escreve status diretamente no agregado atual.
- **`GetCaseAssessmentAnalysisReportController`** (`src/animus/rest/controllers/intake/get_case_assessment_analysis_report_controller.py`) - expõe `GET /analyses/{analysis_id}/case-assessment-report`.
- **`GetFirstInstanceAnalysisReportController`** (`src/animus/rest/controllers/intake/get_first_instance_analysis_report_controller.py`) - expõe `GET /analyses/{analysis_id}/first-instance-report`.
- **`GetSecondInstanceAnalysisReportController`** (`src/animus/rest/controllers/intake/get_second_instance_analysis_report_controller.py`) - expõe `GET /analyses/{analysis_id}/second-instance-report`.

## Routers

- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) - router principal do contexto `analyses`.
- **`PetitionsRouter`** (`src/animus/routers/intake/petitions_router.py`) - router legado ainda exposto no composition root durante a transicao.

## Pipes / Providers / AI / PubSub

- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) - hoje expõe `PetitionsRepository` e `PetitionSummariesRepository`.
- **`SummarizePetitionWorkflow`** (`src/animus/core/intake/interfaces/summarize_petition_workflow.py`) - interface atual do workflow de resumo.
- **`AgnoSummarizePetitionWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_summarize_petition_workflow.py`) - workflow atual de resumo.
- **`FistInstanceCaseSummarizationTriggeredEvent`** (`src/animus/core/intake/domain/events/petition_summary_requested_event.py`) - evento atual do resumo.
- **`PetitionSummaryFinishedEvent`** (`src/animus/core/intake/domain/events/petition_summary_finished_event.py`) - evento atual de conclusao do resumo.
- **`SummarizePetitionJob`** (`src/animus/pubsub/inngest/jobs/intake/summarize_petition_job.py`) - job atual de resumo.
- **`OpenAICaseSummaryEmbeddingsProvider`** (`src/animus/providers/intake/petition_summary_embeddings/openai/openai_petition_summary_embeddings_provider.py`) - provider atual de embeddings do resumo.
- **`SendPetitionSummaryFinishedNotificationJob`** (`src/animus/pubsub/inngest/jobs/notification/send_petition_summary_finished_notification_job.py`) - job atual de notificacao do resumo.
- **`OneSignalPushNotificationProvider`** (`src/animus/providers/notification/push_notification/one_signal/one_signal_push_notification_provider.py`) - provider atual com metodo `send_petition_summary_finished_message(...)`.

## Seeders

- **`StorageSeeder`** (`src/animus/database/sqlalchemy/seeders/storage_seeder.py`) - ainda escreve arquivos de exemplo no prefixo `intake/analises/{analysis_id}/petitions/...`; precisa ser alinhado para `documents`.
- **`SeedAnalysesPrecedentsDatasetJob`** (`src/animus/pubsub/inngest/jobs/intake/seed_analyses_precedents_dataset_job.py`) - hoje cria `Petition` e `PetitionSummary` no fluxo de seed do dataset; precisa passar a criar `AnalysisDocument` e `CaseSummary`.

---

# 5. O que deve ser criado?

## Camada Core (Entidades / Structures / DTOs)

- **Localizacao:** `src/animus/core/intake/domain/entities/analysis_type.py` (**novo arquivo**)
- **Tipo:** `StrEnum`
- **Valores:** `CASE_ASSESSMENT`, `FIRST_INSTANCE`, `SECOND_INSTANCE`
- **Responsabilidade:** discriminar o fluxo da analise e definir o conjunto valido de status e artefatos derivados.

- **Localizacao:** `src/animus/core/intake/domain/entities/case_assessment_analysis_status.py` (**novo arquivo**)
- **Tipo:** `StrEnum`
- **Valores:** `WAITING_DOCUMENT_UPLOAD`, `DOCUMENT_UPLOADED`, `ANALYZING_CASE`, `CASE_ANALYZED`, `SEARCHING_PRECEDENTS`, `GENERATING_PETITION_DRAFT`, `DONE`, `FAILED`
- **Metodos:** `get_processing_statuses() -> tuple[CaseAssessmentAnalysisStatus, ...]` - devolve os status que devem entrar no polling de processamento de `CASE_ASSESSMENT` e, temporariamente, de `FIRST_INSTANCE`.

- **Localizacao:** `src/animus/core/intake/domain/entities/second_instance_analysis_status.py` (**novo arquivo**)
- **Tipo:** `StrEnum`
- **Valores:** `WAITING_DOCUMENT_UPLOAD`, `DOCUMENT_UPLOADED`, `EXTRACTING_PETITION`, `ANALYZING_CASE`, `CASE_ANALYZED`, `SEARCHING_PRECEDENTS`, `GENERATING_JUDGMENT_DRAFT`, `DONE`, `FAILED`
- **Metodos:** `get_processing_statuses() -> tuple[SecondInstanceAnalysisStatus, ...]` - devolve os status que devem entrar no polling de processamento de `SECOND_INSTANCE`.

- **Localizacao:** `src/animus/core/intake/domain/structures/case_assessment_analysis_report.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `analysis`, `document`, `case_summary`, `precedents`, `petition_draft`

- **Localizacao:** `src/animus/core/intake/domain/structures/first_instance_analysis_report.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `analysis`, `document`, `case_summary`, `precedents`, `judgment_draft`

- **Localizacao:** `src/animus/core/intake/domain/structures/second_instance_analysis_report.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `analysis`, `document`, `case_summary`, `precedents`, `draft`

- **Localizacao:** `src/animus/core/intake/domain/structures/dtos/case_assessment_analysis_report_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `analysis`, `document`, `case_summary`, `precedents`, `petition_draft`

- **Localizacao:** `src/animus/core/intake/domain/structures/dtos/first_instance_analysis_report_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `analysis`, `document`, `case_summary`, `precedents`, `judgment_draft`

- **Localizacao:** `src/animus/core/intake/domain/structures/dtos/second_instance_analysis_report_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `analysis`, `document`, `case_summary`, `precedents`, `draft`

- **Localizacao:** `src/animus/core/intake/domain/structures/analysis_document.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `file_path: FilePath`, `name: Text`, `analysis_id: Id`, `uploaded_at: Datetime`
- **Metodos / factory:** `create(dto: AnalysisDocumentDto) -> AnalysisDocument` - monta o documento da analise a partir do DTO; `dto -> AnalysisDocumentDto` - expõe o contrato de borda/persistencia.

- **Localizacao:** `src/animus/core/intake/domain/structures/dtos/analysis_document_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `analysis_id: str`, `uploaded_at: str`, `file_path: str`, `name: str`

- **Localizacao:** `src/animus/core/intake/domain/structures/case_summary.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `case_summary: Text`, `legal_issue: Text`, `central_question: Text`, `relevant_laws: list[Text]`, `key_facts: list[Text]`, `search_terms: list[Text]`, `type_of_action: Text | None`, `secondary_legal_issues: list[Text]`, `alternative_questions: list[Text]`, `jurisdiction_issue: Text | None`, `standing_issue: Text | None`, `requested_relief: list[Text]`, `procedural_issues: list[Text]`, `excluded_or_accessory_topics: list[Text]`
- **Metodos / factory:** `create(dto: CaseSummaryDto) -> CaseSummary` - cria a estrutura do resumo; `dto -> CaseSummaryDto` - expõe o contrato serializavel.

- **Localizacao:** `src/animus/core/intake/domain/structures/dtos/case_summary_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** mesmos campos do `CaseSummary` em tipos primitivos serializaveis.

- **Localizacao:** `src/animus/core/intake/domain/structures/petition_draft.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `analysis_id: Id`, `content: Text`
- **Metodos / factory:** `create(dto: PetitionDraftDto) -> PetitionDraft` - cria o rascunho da petição; `dto -> PetitionDraftDto` - expõe o contrato serializavel.

- **Localizacao:** `src/animus/core/intake/domain/structures/dtos/petition_draft_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `analysis_id: str`, `content: str`

- **Localizacao:** `src/animus/core/intake/domain/structures/judgment_draft.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `analysis_id: Id`, `content: Text`
- **Metodos / factory:** `create(dto: SecondInstanceJudgmentDraftDto) -> SecondInstanceJudgmentDraft` - cria o rascunho da sentenca; `dto -> SecondInstanceJudgmentDraftDto` - expõe o contrato serializavel.

- **Localizacao:** `src/animus/core/intake/domain/structures/dtos/judgment_draft_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `analysis_id: str`, `content: str`

## Camada Core (Erros de Dominio)

- **Localizacao:** `src/animus/core/intake/domain/errors/case_summary_unavailable_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** deve ser levantado quando o `CaseSummary` ainda nao existir para a analise.

- **Localizacao:** `src/animus/core/intake/domain/errors/analysis_document_not_found_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** deve ser levantado quando a analise nao possuir documento associado.

- **Localizacao:** `src/animus/core/intake/domain/errors/petition_draft_unavailable_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** deve ser levantado quando o report de `CASE_ASSESSMENT` exigir `PetitionDraft` e ele ainda nao existir.

- **Localizacao:** `src/animus/core/intake/domain/errors/judgment_draft_unavailable_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** deve ser levantado quando o report de `FIRST_INSTANCE` exigir `SecondInstanceJudgmentDraft` e ele ainda nao existir.

## Camada Core (Interfaces / Ports)

- **Localizacao:** `src/animus/core/intake/interfaces/analysis_documents_repository.py` (**novo arquivo**)
- **Metodos:** `find_by_analysis_id(analysis_id: Id) -> AnalysisDocument | None` - busca o documento ativo da analise; `find_by_file_path(file_path: FilePath) -> AnalysisDocument | None` - busca por caminho de arquivo; `add(document: AnalysisDocument) -> None` - persiste documento novo; `replace(document: AnalysisDocument) -> None` - substitui documento existente; `remove_by_analysis_id(analysis_id: Id) -> None` - remove documento atual quando necessario.

- **Localizacao:** `src/animus/core/intake/interfaces/case_summaries_repository.py` (**novo arquivo**)
- **Metodos:** `find_by_analysis_id(analysis_id: Id) -> CaseSummary | None` - busca o resumo por analise; `add(analysis_id: Id, case_summary: CaseSummary) -> None` - persiste resumo novo; `replace(analysis_id: Id, case_summary: CaseSummary) -> None` - substitui resumo existente.

- **Localizacao:** `src/animus/core/intake/interfaces/case_summary_embeddings_provider.py` (**novo arquivo**)
- **Metodos:** `generate(case_summary: CaseSummary) -> list[CaseSummaryEmbedding]` - gera embeddings do resumo do caso para a busca vetorial de precedentes.

- **Localizacao:** `src/animus/core/intake/interfaces/petition_drafts_repository.py` (**novo arquivo**)
- **Metodos:** `find_by_analysis_id(analysis_id: Id) -> PetitionDraft | None` - busca o rascunho de petição da analise; `add(petition_draft: PetitionDraft) -> None` - persiste rascunho novo; `replace(petition_draft: PetitionDraft) -> None` - substitui rascunho existente.

- **Localizacao:** `src/animus/core/intake/interfaces/judgment_drafts_repository.py` (**novo arquivo**)
- **Metodos:** `find_by_analysis_id(analysis_id: Id) -> SecondInstanceJudgmentDraft | None` - busca o rascunho de sentenca da analise; `add(judgment_draft: SecondInstanceJudgmentDraft) -> None` - persiste rascunho novo; `replace(judgment_draft: SecondInstanceJudgmentDraft) -> None` - substitui rascunho existente.

- **Localizacao:** `src/animus/core/intake/interfaces/summarize_case_workflow.py` (**novo arquivo**)
- **Metodos:** `run(analysis_id: str, document_content: Text) -> CaseSummaryDto` - executa a sumarizacao do caso a partir do documento da analise.

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/intake/use_cases/create_analysis_document_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalysisDocumentsRepository`, `AnalysesRepository`, `Broker`
- **Metodo principal:** `execute(analysis_id: str, uploaded_at: str, file_path: str, name: str) -> AnalysisDocumentDto` - cria ou substitui o documento da analise e atualiza o status para `DOCUMENT_UPLOADED`.
- **Fluxo resumido:** busca `Analysis`; remove/substitui documento anterior quando existir; constroi `AnalysisDocument`; persiste; ajusta `analysis.status`; persiste a analise; publica evento de substituicao de arquivo se necessario.

- **Localizacao:** `src/animus/core/intake/use_cases/get_analysis_document_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalysisDocumentsRepository`
- **Metodo principal:** `execute(analysis_id: str) -> AnalysisDocumentDto` - retorna o documento associado a analise.

- **Localizacao:** `src/animus/core/intake/use_cases/request_case_summary_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalysisDocumentsRepository`, `AnalysesRepository`, `Broker`
- **Metodo principal:** `execute(analysis_id: str) -> None` - valida a existencia do documento, move a analise para o estado de processamento do caso e publica o evento assíncrono do resumo.
- **Fluxo resumido:** busca `AnalysisDocument` por `analysis_id`; busca `Analysis`; ajusta `analysis.status`; persiste a analise; publica `CaseSummaryCaseSummarizationTriggeredEvent(analysis_id)`.

- **Localizacao:** `src/animus/core/intake/use_cases/create_case_summary_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `CaseSummariesRepository`, `AnalysisDocumentsRepository`, `AnalysesRepository`
- **Metodo principal:** `execute(analysis_id: str, dto: CaseSummaryDto) -> CaseSummaryDto` - persiste ou substitui o resumo do caso e move a analise para `CASE_ANALYZED`.
- **Fluxo resumido:** valida `AnalysisDocument`; cria `CaseSummary`; faz upsert no repositorio; busca `Analysis`; ajusta `analysis.status`; persiste a analise; retorna `case_summary.dto`.

- **Localizacao:** `src/animus/core/intake/use_cases/get_case_summary_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `CaseSummariesRepository`
- **Metodo principal:** `execute(analysis_id: str) -> CaseSummaryDto` - retorna o resumo do caso da analise.

- **Localizacao:** `src/animus/core/intake/use_cases/get_case_assessment_analysis_report_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalysesRepository`, `AnalysisDocumentsRepository`, `CaseSummariesRepository`, `AnalysisPrecedentsRepository`, `PetitionDraftsRepository`
- **Metodo principal:** `execute(analysis_id: str, account_id: str) -> CaseAssessmentAnalysisReportDto`.

- **Localizacao:** `src/animus/core/intake/use_cases/get_first_instance_analysis_report_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalysesRepository`, `AnalysisDocumentsRepository`, `CaseSummariesRepository`, `AnalysisPrecedentsRepository`, `SecondInstanceJudgmentDraftsRepository`
- **Metodo principal:** `execute(analysis_id: str, account_id: str) -> FirstInstanceAnalysisReportDto`.

- **Localizacao:** `src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalysesRepository`, `AnalysisDocumentsRepository`, `CaseSummariesRepository`, `AnalysisPrecedentsRepository`
- **Metodo principal:** `execute(analysis_id: str, account_id: str) -> SecondInstanceAnalysisReportDto`.

## Camada Database (Models SQLAlchemy)

- **Localizacao:** `src/animus/database/sqlalchemy/models/intake/analysis_document_model.py` (**novo arquivo**)
- **Tabela:** `analysis_documents`
- **Colunas:** `analysis_id`, `uploaded_at`, `document_file_path`, `document_name`, `created_at`, `updated_at`
- **Relacionamentos:** `analysis: relationship('AnalysisModel', back_populates='document')`

- **Localizacao:** `src/animus/database/sqlalchemy/models/intake/case_summary_model.py` (**novo arquivo**)
- **Tabela:** `case_summaries`
- **Colunas:** `analysis_id`, `case_summary`, `legal_issue`, `central_question`, `relevant_laws`, `key_facts`, `search_terms`, `type_of_action`, `secondary_legal_issues`, `alternative_questions`, `jurisdiction_issue`, `standing_issue`, `requested_relief`, `procedural_issues`, `excluded_or_accessory_topics`, `created_at`, `updated_at`
- **Relacionamentos:** `analysis: relationship('AnalysisModel', back_populates='case_summary')`

- **Localizacao:** `src/animus/database/sqlalchemy/models/intake/petition_draft_model.py` (**novo arquivo**)
- **Tabela:** `petition_drafts`
- **Colunas:** `analysis_id`, `content`, `created_at`, `updated_at`
- **Relacionamentos:** `analysis: relationship('AnalysisModel', back_populates='petition_draft')`

- **Localizacao:** `src/animus/database/sqlalchemy/models/intake/judgment_draft_model.py` (**novo arquivo**)
- **Tabela:** `second_instance_judgment_drafts`
- **Colunas:** `analysis_id`, `content`, `created_at`, `updated_at`
- **Relacionamentos:** `analysis: relationship('AnalysisModel', back_populates='judgment_draft')`

## Camada Database (Mappers)

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/intake/analysis_document_mapper.py` (**novo arquivo**)
- **Metodos:** `to_entity(model: AnalysisDocumentModel) -> AnalysisDocument` - traduz o model ORM para o documento da analise; `to_model(document: AnalysisDocument) -> AnalysisDocumentModel` - traduz o documento para persistencia.

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/intake/case_summary_mapper.py` (**novo arquivo**)
- **Metodos:** `to_entity(model: CaseSummaryModel) -> CaseSummary` - traduz o resumo persistido para a estrutura de dominio; `to_model(analysis_id: Id, case_summary: CaseSummary) -> CaseSummaryModel` - traduz para persistencia.

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/intake/petition_draft_mapper.py` (**novo arquivo**)
- **Metodos:** `to_entity(model: PetitionDraftModel) -> PetitionDraft` - traduz o model persistido para o rascunho de petição; `to_model(petition_draft: PetitionDraft) -> PetitionDraftModel` - traduz para persistencia.

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/intake/judgment_draft_mapper.py` (**novo arquivo**)
- **Metodos:** `to_entity(model: SecondInstanceJudgmentDraftModel) -> SecondInstanceJudgmentDraft` - traduz o model persistido para o rascunho de sentenca; `to_model(judgment_draft: SecondInstanceJudgmentDraft) -> SecondInstanceJudgmentDraftModel` - traduz para persistencia.

## Camada Database (Repositorios)

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analysis_documents_repository.py` (**novo arquivo**)
- **Interface implementada:** `AnalysisDocumentsRepository`
- **Dependencias:** `Session`
- **Metodos:** `find_by_analysis_id(...)`, `find_by_file_path(...)`, `add(...)`, `replace(...)`, `remove_by_analysis_id(...)`

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_case_summaries_repository.py` (**novo arquivo**)
- **Interface implementada:** `CaseSummariesRepository`
- **Dependencias:** `Session`
- **Metodos:** `find_by_analysis_id(...)`, `add(...)`, `replace(...)`

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_drafts_repository.py` (**novo arquivo**)
- **Interface implementada:** `PetitionDraftsRepository`
- **Dependencias:** `Session`
- **Metodos:** `find_by_analysis_id(...)`, `add(...)`, `replace(...)`

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py` (**novo arquivo**)
- **Interface implementada:** `SecondInstanceJudgmentDraftsRepository`
- **Dependencias:** `Session`
- **Metodos:** `find_by_analysis_id(...)`, `add(...)`, `replace(...)`

## Camada REST (Controllers)

- **Localizacao:** `src/animus/rest/controllers/intake/create_analysis_document_controller.py` (**novo arquivo**)
- **`*Body`:** `_Body(uploaded_at: str, file_path: str, name: str)`
- **Metodo HTTP e path:** `POST /analyses/{analysis_id}/document`
- **`status_code`:** `201`
- **`response_model`:** `AnalysisDocumentDto`
- **Dependencias injetadas via `Depends`:** `Id` por `AuthPipe.get_account_id_from_request`; `AnalysesRepository`; `AnalysisDocumentsRepository`; `Broker`
- **Fluxo:** valida ownership da analise -> `CreateAnalysisDocumentUseCase.execute(...)` -> resposta.

- **Localizacao:** `src/animus/rest/controllers/intake/get_analysis_document_controller.py` (**novo arquivo**)
- **`*Body`:** nao aplicavel
- **Metodo HTTP e path:** `GET /analyses/{analysis_id}/document`
- **`status_code`:** `200`
- **`response_model`:** `AnalysisDocumentDto`
- **Dependencias injetadas via `Depends`:** `Analysis` por `IntakePipe.verify_analysis_by_account_from_request`; `AnalysisDocumentsRepository`
- **Fluxo:** `GetAnalysisDocumentUseCase.execute(analysis_id=analysis.id.value)` -> resposta.

- **Localizacao:** `src/animus/rest/controllers/intake/request_case_summary_controller.py` (**novo arquivo**)
- **`*Body`:** nao aplicavel
- **Metodo HTTP e path:** `POST /analyses/{analysis_id}/case-summaries`
- **`status_code`:** `202`
- **`response_model`:** nao aplicavel
- **Dependencias injetadas via `Depends`:** `Analysis` por `IntakePipe.verify_analysis_by_account_from_request`; `AnalysisDocumentsRepository`; `AnalysesRepository`; `Broker`
- **Fluxo:** `RequestCaseSummaryUseCase.execute(analysis_id=analysis.id.value)` -> `202`.

- **Localizacao:** `src/animus/rest/controllers/intake/get_case_summary_controller.py` (**novo arquivo**)
- **`*Body`:** nao aplicavel
- **Metodo HTTP e path:** `GET /analyses/{analysis_id}/case-summaries`
- **`status_code`:** `200`
- **`response_model`:** `CaseSummaryDto`
- **Dependencias injetadas via `Depends`:** `Analysis` por `IntakePipe.verify_analysis_by_account_from_request`; `CaseSummariesRepository`
- **Fluxo:** `GetCaseSummaryUseCase.execute(analysis_id=analysis.id.value)` -> resposta.

- **Localizacao:** `src/animus/rest/controllers/intake/get_case_assessment_analysis_report_controller.py` (**novo arquivo**)
- **Metodo HTTP e path:** `GET /analyses/{analysis_id}/case-assessment-report`
- **`status_code`:** `200`
- **`response_model`:** `CaseAssessmentAnalysisReportDto`

- **Localizacao:** `src/animus/rest/controllers/intake/get_first_instance_analysis_report_controller.py` (**novo arquivo**)
- **Metodo HTTP e path:** `GET /analyses/{analysis_id}/first-instance-report`
- **`status_code`:** `200`
- **`response_model`:** `FirstInstanceAnalysisReportDto`

- **Localizacao:** `src/animus/rest/controllers/intake/get_second_instance_analysis_report_controller.py` (**novo arquivo**)
- **Metodo HTTP e path:** `GET /analyses/{analysis_id}/second-instance-report`
- **`status_code`:** `200`
- **`response_model`:** `SecondInstanceAnalysisReportDto`

## Camada Routers

**Nao aplicavel.** Nao ha router novo obrigatorio; os novos controllers passam a ser registrados no `AnalysesRouter` existente.

## Camada Pipes

**Nao aplicavel.** Nao ha arquivo novo; o `DatabasePipe` apenas ganha novos factories para os repositorios renomeados/criados.

## Camada Providers

**Nao aplicavel.** Nao ha provider conceitualmente novo; os providers existentes de resumo/notificacao so serao renomeados.

## Camada PubSub (Eventos de Dominio)

- **Localizacao:** `src/animus/core/intake/domain/events/case_summary_requested_event.py` (**novo arquivo**)
- **`NAME`:** `intake/case.summary.triggered`
- **Payload:** `analysis_id: str`

- **Localizacao:** `src/animus/core/intake/domain/events/case_summary_finished_event.py` (**novo arquivo**)
- **`NAME`:** `intake/case_summary.finished`
- **Payload:** `analysis_id: str`, `account_id: str`

## Camada PubSub (Jobs Inngest)

- **Localizacao:** `src/animus/pubsub/inngest/jobs/intake/summarize_case_job.py` (**novo arquivo**)
- **Evento consumido:** `CaseSummaryCaseSummarizationTriggeredEvent.NAME`
- **Dependencias:** `AnalysisDocumentsRepository`, `CaseSummariesRepository`, `AnalysesRepository`, `SummarizeFirstInstanceCaseWorkflow`
- **Passos (`step.run`):** normalizar payload -> carregar `AnalysisDocument` -> ler conteudo do arquivo -> executar workflow -> persistir `CaseSummary` -> publicar `CaseSummaryFinishedEvent`
- **Idempotencia:** resumo e atualizado por `replace(...)` quando a analise ja possuir `CaseSummary`; reexecucoes nao criam duplicata.

## Migrações Alembic (se aplicavel)

- **Localizacao:** `migrations/versions/` (**novo arquivo**)
- **Operacoes:** renomear `petitions` para `analysis_documents` ou recriar tabela equivalente centrada em `analysis_id`; renomear `petition_summaries` para `case_summaries` e trocar a chave estrangeira para `analysis_id`; adicionar `analyses.type`; criar `petition_drafts` e `judgment_drafts`; backfill de `analyses.type` e de `analyses.status` para os novos enums.
- **Reversibilidade:** `downgrade` pode restaurar nomes/tabelas antigas e remover os drafts; o backfill de status continua sendo reversao best-effort.

---

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/entities/analyses.py`
- **Mudanca:** adicionar `type: AnalysisType`; trocar `status: AnalysisStatus` por `status: CaseAssessmentAnalysisStatus | SecondInstanceAnalysisStatus`; fazer `create(...)` e `dto` serializarem `type` e status direto; atualizar `set_status(status: str) -> None` para validar contra o enum do tipo correto, com `FIRST_INSTANCE` reaproveitando temporariamente o contrato de `CASE_ASSESSMENT`.
- **Justificativa:** o agregado `Analysis` passa a ser a fonte de verdade do fluxo por perfil.

- **Arquivo:** `src/animus/core/intake/domain/entities/dtos/analysis_dto.py`
- **Mudanca:** adicionar `type: str` ao DTO publico.
- **Justificativa:** o cliente precisa saber qual tela e qual workflow carregar.

- **Arquivo:** `src/animus/core/intake/domain/entities/analysis_status.py`
- **Mudanca:** remover o arquivo do surface canonico do dominio.
- **Justificativa:** `AnalysisStatus` deixa de existir como abstracao valida.

- **Arquivo:** `src/animus/core/intake/use_cases/create_analysis_use_case.py`
- **Mudanca:** alterar assinatura para `execute(account_id: str, type: str, folder_id: str | None = None) -> AnalysisDto`; criar analise com status `WAITING_DOCUMENT_UPLOAD`.
- **Justificativa:** `WAITING_PETITION` deixa de existir e a criacao passa a depender do tipo selecionado.

- **Arquivo:** `src/animus/core/intake/use_cases/list_analyses_use_case.py`
- **Mudanca:** trocar o conjunto de status listaveis para os novos estados tipados e remover dependencia de `AnalysisStatusValue`.
- **Justificativa:** a listagem principal nao pode depender de estados legados removidos.

- **Arquivo:** `src/animus/core/intake/use_cases/list_processing_analyses_use_case.py`
- **Mudanca:** manter assinatura e usar os novos estados de processamento consolidados no repositorio.
- **Justificativa:** polling continua no mesmo endpoint, mas sobre novo conjunto de status.

- **Arquivo:** `src/animus/core/intake/use_cases/search_analysis_precedents_use_case.py`
- **Mudanca:** trocar `PetitionSummariesRepository` por `CaseSummariesRepository` e `CaseSummaryEmbeddingsProvider` por `CaseSummaryEmbeddingsProvider`.
- **Justificativa:** a busca de precedentes passa a partir do `CaseSummary` por `analysis_id`.

- **Arquivo:** `src/animus/core/intake/use_cases/request_analysis_precedents_search_use_case.py`
- **Mudanca:** trocar leitura do resumo para `CaseSummariesRepository.find_by_analysis_id(...)`.
- **Justificativa:** o trigger de busca deixa de depender de `petition_id`.

- **Arquivo:** `src/animus/core/intake/use_cases/create_analysis_precedents_use_case.py`
- **Mudanca:** remover `WAITING_PRECEDENT_CHOISE` e mover a analise para o estado estavel adequado do tipo apos persistir precedentes, sem depender de status legado de escolha.
- **Justificativa:** os status de escolha de precedente deixam de existir.

- **Arquivo:** `src/animus/core/intake/use_cases/choose_analysis_precedent_use_case.py`
- **Mudanca:** parar de usar `PRECEDENT_CHOSED`; a escolha do precedente passa a apenas persistir a selecao e manter o status coerente com o fluxo por tipo.
- **Justificativa:** `PRECEDENT_CHOSED` deixa de existir.

- **Arquivo:** `src/animus/core/intake/use_cases/get_case_assessment_analysis_report_use_case.py`, `src/animus/core/intake/use_cases/get_first_instance_analysis_report_use_case.py`, `src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`
- **Mudanca:** separar o relatorio em tres use cases por tipo, com drafts distintos para `CASE_ASSESSMENT` e `FIRST_INSTANCE`, e `chosen_precedent` para `SECOND_INSTANCE`.
- **Justificativa:** o report passa a refletir explicitamente os artefatos do fluxo de cada tipo de analise.

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudanca:** exportar `AnalysisDocumentsRepository`, `CaseSummariesRepository`, `CaseSummaryEmbeddingsProvider`, `PetitionDraftsRepository`, `SecondInstanceJudgmentDraftsRepository`, `SummarizeFirstInstanceCaseWorkflow`; remover exports de `PetitionsRepository`, `PetitionSummariesRepository` e `SummarizePetitionWorkflow`.
- **Justificativa:** estabilizar o novo surface publico do bounded context.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudanca:** exportar os use cases novos de `AnalysisDocument` e `CaseSummary`; remover exports legados de `Petition` e `PetitionSummary`.
- **Justificativa:** impedir coexistencia de nomes antigos e novos no estado final.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/analysis_model.py`
- **Mudanca:** adicionar coluna `type`; adicionar relacionamentos `document`, `case_summary`, `petition_draft` e `judgment_draft`.
- **Justificativa:** `Analysis` passa a orquestrar artefatos derivados por tipo.

- **Arquivo:** `src/animus/database/sqlalchemy/mappers/intake/analysis_mapper.py`
- **Mudanca:** serializar `type` e o novo status direto no `AnalysisDto`.
- **Justificativa:** o mapper precisa reconstruir o agregado com o discriminador correto.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analyses_repository.py`
- **Mudanca:** trocar todos os filtros/assinaturas baseados em `AnalysisStatusValue` por strings/tuplas derivadas dos enums tipados; persistir `type` em `replace(...)`.
- **Justificativa:** a persistencia de analises e o ponto central dos filtros de listagem e polling.

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/__init__.py`
- **Mudanca:** exportar `AnalysisDocumentModel`, `CaseSummaryModel`, `PetitionDraftModel` e `SecondInstanceJudgmentDraftModel`; remover `PetitionModel` e `PetitionSummaryModel` como nomes canonicos.
- **Justificativa:** os exports publicos precisam refletir o novo dominio.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/__init__.py`
- **Mudanca:** exportar `SqlalchemyAnalysisDocumentsRepository`, `SqlalchemyCaseSummariesRepository`, `SqlalchemyPetitionDraftsRepository` e `SqlalchemySecondInstanceJudgmentDraftsRepository`; remover nomes legados.
- **Justificativa:** alinhar o package de repositorios ao dominio novo.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/create_analysis_controller.py`
- **Mudanca:** adicionar `type: str` ao `_Body`.
- **Justificativa:** o tipo passa a ser obrigatorio na criacao.

- **Arquivo:** `src/animus/rest/controllers/intake/get_analysis_controller.py`
- **Mudanca:** refletir `AnalysisDto.type` na resposta.
- **Justificativa:** o detalhe da analise precisa informar o perfil da analise.

- **Arquivo:** `src/animus/rest/controllers/intake/get_analysis_status_controller.py`
- **Mudanca:** manter o endpoint, mas serializar o valor vindo diretamente de `CaseAssessmentAnalysisStatus | SecondInstanceAnalysisStatus`.
- **Justificativa:** polling do cliente continua sobre o mesmo contrato DTO simples.

- **Arquivo:** `src/animus/rest/controllers/intake/update_analysis_status_controller.py`
- **Mudanca:** delegar a validacao para o novo `Analysis.set_status(...)` tipado.
- **Justificativa:** impedir escrita de status de outro perfil.

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudanca:** exportar `GetCaseAssessmentAnalysisReportController`, `GetFirstInstanceAnalysisReportController` e `GetSecondInstanceAnalysisReportController`, alem dos controllers de documento e resumo.
- **Justificativa:** o pacote de controllers precisa refletir os novos endpoints de report por tipo.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudanca:** registrar os novos controllers de report por tipo, alem dos controllers de document e case summary.
- **Justificativa:** a superficie HTTP passa a expor leitura de report especializada por tipo de analise.

- **Arquivo:** `src/animus/routers/intake/petitions_router.py`
- **Mudanca:** remover o router do composition root.
- **Justificativa:** nao deve mais existir rota `/intake/petitions`.

## Pipes

- **Arquivo:** `src/animus/pipes/database_pipe.py`
- **Mudanca:** adicionar factories para `AnalysisDocumentsRepository`, `CaseSummariesRepository`, `PetitionDraftsRepository` e `SecondInstanceJudgmentDraftsRepository`; remover factories legadas de `PetitionsRepository` e `PetitionSummariesRepository`.
- **Justificativa:** `Depends(...)` deve expor os contratos novos do dominio.

## Providers / AI / PubSub

- **Arquivo:** `src/animus/core/intake/domain/events/__init__.py`
- **Mudanca:** exportar apenas os eventos `CaseSummary*` e remover `PetitionSummary*`.
- **Justificativa:** estabilizar a API publica de eventos do bounded context.

- **Arquivo:** `src/animus/core/intake/interfaces/summarize_petition_workflow.py`
- **Mudanca:** renomear para `summarize_case_workflow.py` e trocar assinatura para `analysis_id` + `document_content`.
- **Justificativa:** o workflow passa a operar sobre o documento da analise, nao sobre `petition_id`.

- **Arquivo:** `src/animus/ai/agno/workflows/intake/agno_summarize_petition_workflow.py`
- **Mudanca:** renomear arquivo/classe para `AgnoSummarizeFirstInstanceCaseWorkflow`; trocar `CreatePetitionSummaryUseCase` por `CreateCaseSummaryUseCase`; trocar `PetitionSummaryDto` por `CaseSummaryDto`.
- **Justificativa:** alinhar o workflow ao nome canonico do resumo.

- **Arquivo:** `src/animus/ai/agno/outputs/intake/petition_summary_output.py`
- **Mudanca:** renomear para `case_summary_output.py`.
- **Justificativa:** remover o nome legado do output estruturado.

- **Arquivo:** `src/animus/providers/intake/petition_summary_embeddings/openai/openai_petition_summary_embeddings_provider.py`
- **Mudanca:** renomear caminho/classe para `case_summary_embeddings/openai/openai_case_summary_embeddings_provider.py` e trocar o contrato de entrada para `CaseSummary`.
- **Justificativa:** o provider deve refletir o novo artefato canonico.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_petition_job.py`
- **Mudanca:** renomear arquivo/classe para `summarize_case_job.py` / `SummarizeFirstInstanceCaseJob`; trocar payload para `analysis_id`; buscar `AnalysisDocument` em vez de `Petition`; trocar evento trigger para `CaseSummaryCaseSummarizationTriggeredEvent`; publicar `CaseSummaryFinishedEvent`.
- **Justificativa:** o job de resumo deixa de depender de `petition_id`.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/send_petition_summary_finished_notification_job.py`
- **Mudanca:** renomear para `send_case_summary_finished_notification_job.py` e trocar trigger e nomes de step para `case_summary`.
- **Justificativa:** observabilidade e contratos de notificação precisam refletir o novo nome.

- **Arquivo:** `src/animus/core/notification/interfaces/push_notification_provider.py`
- **Mudanca:** renomear `send_petition_summary_finished_message(...)` para `send_case_summary_finished_message(...)`.
- **Justificativa:** o provider nao deve expor o termo legado.

- **Arquivo:** `src/animus/core/notification/use_cases/send_petition_summary_finished_notification_use_case.py`
- **Mudanca:** renomear para `send_case_summary_finished_notification_use_case.py`.
- **Justificativa:** o use case de notificacao precisa refletir o novo evento.

- **Arquivo:** `src/animus/providers/notification/push_notification/one_signal/one_signal_push_notification_provider.py`
- **Mudanca:** renomear metodo e payload `type` para `case_summary_finished`.
- **Justificativa:** o payload push observado pelo app deve refletir o novo contrato.

## Seeders

- **Arquivo:** `src/animus/database/sqlalchemy/seeders/storage_seeder.py`
- **Mudanca:** trocar o prefixo de arquivos seedados de `petitions` para `documents`.
- **Justificativa:** o armazenamento de documentos da analise precisa seguir o mesmo contrato de path do dominio atualizado.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/seed_analyses_precedents_dataset_job.py`
- **Mudanca:** substituir criacao/leitura de `Petition` e `PetitionSummary` por `AnalysisDocument` e `CaseSummary`; ajustar imports do workflow e do provider de embeddings.
- **Justificativa:** o job de seeding precisa continuar funcional e coerente com o novo modelo canônico do intake.

---

# 7. O que deve ser removido?

**Nao aplicavel neste recorte incremental.** Apesar de a direcao arquitetural continuar apontando para a substituicao completa de `Petition` e `PetitionSummary`, o codigo atual ainda mantem models, repositorios, controllers e rotas legadas de `petitions` coexistindo com os contratos novos. A remocao final continua pendente e nao deve ser tratada como concluida nesta spec atualizada.

## Core

- **Arquivo:** `src/animus/core/intake/domain/entities/analysis_status.py`
- **Motivo da remocao:** substituido completamente, como fonte canonica, por `CaseAssessmentAnalysisStatus | SecondInstanceAnalysisStatus`.
- **Impacto esperado:** atualizar `Analysis`, `use_cases`, controllers e repositorios que hoje importam `AnalysisStatusValue`.

- **Arquivo:** `src/animus/core/intake/domain/entities/petition.py`
- **Motivo da remocao:** substituido por `AnalysisDocument`.
- **Impacto esperado:** atualizar repositorio, mappers, models, controllers, jobs e relatorio.

- **Arquivo:** `src/animus/core/intake/domain/entities/dtos/petition_dto.py`
- **Motivo da remocao:** substituido por `AnalysisDocumentDto`.
- **Impacto esperado:** atualizar contratos REST e mapeamento ORM.

- **Arquivo:** `src/animus/core/intake/interfaces/petitions_repository.py`
- **Motivo da remocao:** substituido por `AnalysisDocumentsRepository`.
- **Impacto esperado:** atualizar `DatabasePipe`, use cases, jobs e seeders.

- **Arquivo:** `src/animus/core/intake/domain/structures/petition_summary.py`
- **Motivo da remocao:** substituido por `CaseSummary`.
- **Impacto esperado:** atualizar buscas, relatorio, AI e persistencia.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/petition_summary_dto.py`
- **Motivo da remocao:** substituido por `CaseSummaryDto`.
- **Impacto esperado:** atualizar response models, workflow e outputs estruturados.

- **Arquivo:** `src/animus/core/intake/interfaces/petition_summaries_repository.py`
- **Motivo da remocao:** substituido por `CaseSummariesRepository`.
- **Impacto esperado:** atualizar `DatabasePipe`, use cases e jobs.

- **Arquivo:** `src/animus/core/intake/domain/events/petition_summary_requested_event.py`
- **Motivo da remocao:** substituido por `CaseSummaryCaseSummarizationTriggeredEvent`.
- **Impacto esperado:** atualizar trigger do job de resumo.

- **Arquivo:** `src/animus/core/intake/domain/events/petition_summary_finished_event.py`
- **Motivo da remocao:** substituido por `CaseSummaryFinishedEvent`.
- **Impacto esperado:** atualizar notificacao e listeners correlatos.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/petition_model.py`
- **Motivo da remocao:** substituido por `AnalysisDocumentModel`.
- **Impacto esperado:** atualizar mappers, repositorios e relacionamentos ORM.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petitions_repository.py`
- **Motivo da remocao:** substituido por `SqlalchemyAnalysisDocumentsRepository`.
- **Impacto esperado:** atualizar `DatabasePipe`, controllers e jobs.

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/petition_summary_model.py`
- **Motivo da remocao:** substituido por `CaseSummaryModel`.
- **Impacto esperado:** atualizar mappers, repositorios e relacoes do ORM.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_summaries_repository.py`
- **Motivo da remocao:** substituido por `SqlalchemyCaseSummariesRepository`.
- **Impacto esperado:** atualizar `DatabasePipe`, use cases, jobs e workflow.

## REST / Routers

- **Arquivo:** `src/animus/rest/controllers/intake/create_petition_controller.py`
- **Motivo da remocao:** substituido por `CreateAnalysisDocumentController`.
- **Impacto esperado:** cliente deixa de chamar `POST /intake/petitions`.

- **Arquivo:** `src/animus/rest/controllers/intake/get_analysis_petition_controller.py`
- **Motivo da remocao:** substituido por `GetAnalysisDocumentController`.
- **Impacto esperado:** leitura do documento passa a usar `/analyses/{analysis_id}/document`.

- **Arquivo:** `src/animus/rest/controllers/intake/summarize_petition_controller.py`
- **Motivo da remocao:** substituido por `RequestCaseSummaryController`.
- **Impacto esperado:** request do resumo passa a usar `/analyses/{analysis_id}/case-summaries`.

- **Arquivo:** `src/animus/rest/controllers/intake/get_petition_summary_controller.py`
- **Motivo da remocao:** substituido por `GetCaseSummaryController`.
- **Impacto esperado:** leitura do resumo passa a usar `/analyses/{analysis_id}/case-summaries`.

- **Arquivo:** `src/animus/routers/intake/petitions_router.py`
- **Motivo da remocao:** nao deve restar mais superficie HTTP de `petitions`.
- **Impacto esperado:** toda a composicao migra para `AnalysesRouter`.

## Providers / AI / PubSub

- **Arquivo:** `src/animus/core/intake/interfaces/summarize_petition_workflow.py`
- **Motivo da remocao:** substituido por `SummarizeFirstInstanceCaseWorkflow`.
- **Impacto esperado:** atualizar `AiPipe` e workflow concreto.

- **Arquivo:** `src/animus/ai/agno/workflows/intake/agno_summarize_petition_workflow.py`
- **Motivo da remocao:** substituido por `AgnoSummarizeFirstInstanceCaseWorkflow`.
- **Impacto esperado:** atualizar imports no job e no `AiPipe`.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_petition_job.py`
- **Motivo da remocao:** substituido por `SummarizeFirstInstanceCaseJob`.
- **Impacto esperado:** atualizar bootstrap do `Inngest` e eventos publicados.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/send_petition_summary_finished_notification_job.py`
- **Motivo da remocao:** substituido por `SendCaseSummaryFinishedNotificationJob`.
- **Impacto esperado:** atualizar bootstrap de notificacao e tipo do payload push.

---

# 8. Decisoes Tecnicas e Trade-offs

- **Decisao:** substituir `Petition` por `AnalysisDocument` como `@structure` unica por analise.
- **Alternativas consideradas:** manter `Petition` como entidade e apenas renomear rotas; criar `AnalysisDocument` como alias temporario.
- **Motivo da escolha:** o novo fluxo e centrado em `analysis_id`, nao em `petition_id`, e o usuario definiu explicitamente `AnalysisDocument` como estrutura com os campos do arquivo.
- **Impactos / trade-offs:** a migration e mais invasiva, mas o estado final elimina uma identidade tecnica desnecessaria para o documento.

- **Decisao:** remover `AnalysisStatus` completamente como fonte canonica e armazenar `Analysis.status` como `CaseAssessmentAnalysisStatus | SecondInstanceAnalysisStatus`, com `FIRST_INSTANCE` reaproveitando temporariamente o primeiro conjunto.
- **Alternativas consideradas:** manter um wrapper `AnalysisStatus` e validar internamente por tipo; manter um enum compartilhado com prefixos por perfil.
- **Motivo da escolha:** a diretriz do escopo pede substituicao completa; isso evita outra camada de indirecao e torna o fluxo por perfil explicito no agregado.
- **Impactos / trade-offs:** o diff e amplo e exige revisar todos os imports/assinaturas que hoje usam `AnalysisStatusValue`.

- **Decisao:** separar a leitura de report em tres endpoints e tres estruturas especificas por tipo de analise.
- **Alternativas consideradas:** manter um unico `AnalysisReport` com campos opcionais para drafts e precedente escolhido; expor um unico endpoint `/report` com variacao apenas no payload.
- **Motivo da escolha:** o contrato HTTP fica explicito por tipo, reduz ambiguidade no cliente e acompanha a renomeacao dos artefatos de dominio.
- **Impactos / trade-offs:** aumenta a quantidade de DTOs, controllers e use cases, mas elimina branching de serializacao na borda.

- **Decisao:** `WAITING_DOCUMENT_UPLOAD` substitui `WAITING_PETITION` nos dois perfis.
- **Alternativas consideradas:** manter estado inicial diferente por perfil; preservar `WAITING_PETITION` por retrocompatibilidade.
- **Motivo da escolha:** o fluxo agora gira em torno do documento da analise, nao da `petition` como conceito de dominio.
- **Impactos / trade-offs:** todo backfill de status e todo contrato mobile que compare strings precisa ser atualizado.

- **Decisao:** `CaseSummary` passa a ser chaveado por `analysis_id`.
- **Alternativas consideradas:** manter resumo preso a `petition_id` mesmo apos a introducao de `AnalysisDocument`.
- **Motivo da escolha:** a rota, o request assíncrono e o agregado principal passam a ser centrados em `analysis`; manter `petition_id` criaria um vazamento desnecessario do modelo legado.
- **Impactos / trade-offs:** a migration de `petition_summaries` precisa alterar FK/chave de lookup e os jobs passam a buscar `AnalysisDocument` antes do workflow.

- **Decisao:** incluir `PetitionDraft` e `SecondInstanceJudgmentDraft` no escopo apenas como contratos e persistencia.
- **Alternativas consideradas:** deixar drafts totalmente fora do `ANI-92`; implementar tambem jobs e endpoints de leitura na mesma entrega.
- **Motivo da escolha:** a atualizacao do dominio/base de dados precisa preparar esses artefatos para `ANI-93`, `ANI-94` e `ANI-114`, mas o ticket desta spec ainda e de groundwork estrutural.
- **Impactos / trade-offs:** o PR cria tabelas e portas novas sem expor ainda toda a superficie HTTP correspondente.

---

# 9. Diagramas e Referencias

- **Fluxo de dados:**

```text
POST /intake/analyses/{analysis_id}/document
  -> CreateAnalysisDocumentController
  -> CreateAnalysisDocumentUseCase.execute(...)
     -> AnalysisDocumentsRepository.find_by_analysis_id
     -> AnalysesRepository.find_by_id
     -> AnalysisDocumentsRepository.add|replace
     -> Analysis.set_status(DOCUMENT_UPLOADED)
     -> AnalysesRepository.replace

POST /intake/analyses/{analysis_id}/case-summaries
  -> RequestCaseSummaryController
  -> RequestCaseSummaryUseCase.execute(analysis_id)
     -> AnalysisDocumentsRepository.find_by_analysis_id
     -> AnalysesRepository.find_by_id
     -> Analysis.set_status(ANALYZING_CASE | EXTRACTING_PETITION)
     -> AnalysesRepository.replace
     -> Broker.publish(CaseSummaryCaseSummarizationTriggeredEvent)

Inngest -> SummarizeFirstInstanceCaseJob
  -> AnalysisDocumentsRepository.find_by_analysis_id
  -> SummarizeFirstInstanceCaseWorkflow.run(...)
  -> CreateCaseSummaryUseCase.execute(analysis_id, dto)
     -> CaseSummariesRepository.add|replace
     -> AnalysesRepository.find_by_id
     -> Analysis.set_status(CASE_ANALYZED)
     -> AnalysesRepository.replace
  -> Broker.publish(CaseSummaryFinishedEvent)

GET /intake/analyses/{analysis_id}/case-summaries
  -> GetCaseSummaryController
  -> GetCaseSummaryUseCase
  -> CaseSummariesRepository.find_by_analysis_id
  -> 200 CaseSummaryDto
```

- **Fluxo assincrono:**

```text
RequestCaseSummaryUseCase
  -> Broker.publish(CaseSummaryCaseSummarizationTriggeredEvent)
  -> SummarizeFirstInstanceCaseJob
     -> SummarizeFirstInstanceCaseWorkflow
     -> CreateCaseSummaryUseCase
     -> Broker.publish(CaseSummaryFinishedEvent)
  -> SendCaseSummaryFinishedNotificationJob
     -> SendCaseSummaryFinishedNotificationUseCase
     -> PushNotificationProvider.send_case_summary_finished_message(...)
```

- **Referencias:**
- `src/animus/core/intake/domain/entities/analyses.py` - agregado principal a ser tipado por perfil.
- `src/animus/core/intake/domain/entities/petition.py` - referencia direta do que deve virar `AnalysisDocument`.
- `src/animus/core/intake/use_cases/create_petition_use_case.py` - referencia do fluxo atual de upsert do documento.
- `src/animus/core/intake/use_cases/request_petition_summary_use_case.py` - referencia do fluxo atual de request do resumo, a ser centrado em `analysis_id`.
- `src/animus/database/sqlalchemy/models/intake/petition_model.py` - referencia do schema atual do documento.
- `src/animus/database/sqlalchemy/models/intake/petition_summary_model.py` - referencia do schema atual do resumo.
- `src/animus/rest/controllers/intake/create_petition_controller.py` - referencia do endpoint atual de documento.
- `src/animus/rest/controllers/intake/summarize_petition_controller.py` - referencia do endpoint atual de request do resumo.
- `src/animus/pubsub/inngest/jobs/intake/summarize_petition_job.py` - referencia do job atual de resumo.
- `src/animus/providers/intake/petition_summary_embeddings/openai/openai_petition_summary_embeddings_provider.py` - referencia do provider de embeddings a renomear.
- `src/animus/database/sqlalchemy/seeders/storage_seeder.py` - referencia do path legado de arquivos seedados.
- `src/animus/pubsub/inngest/jobs/intake/seed_analyses_precedents_dataset_job.py` - referencia do fluxo de seed que ainda depende de `Petition` e `PetitionSummary`.

---

# 10. Pendencias / Duvidas

- **Descricao da pendencia:** o PRD local esperado em `documentation/features/intake/analyses-management/prd.md` nao existe no repositorio.
- **Impacto na implementacao:** a frontmatter nao consegue apontar para um caminho local canonico e a rastreabilidade documental fica dependente de Confluence/Jira.
- **Acao sugerida:** criar posteriormente um `prd.md` local consolidando `RF 07` e o recorte estrutural de `ANI-92`.

- **Descricao da pendencia:** o mapeamento exato de status legados como `PETITION_ANALYZED`, `WAITING_PRECEDENT_CHOISE` e `PRECEDENT_CHOSED` para os novos fluxos tipados ainda nao esta documentado de forma explicita no PRD.
- **Impacto na implementacao:** a migration e os use cases que hoje usam esses estados precisam de uma regra final de backfill e de transicao para nao produzir comportamento divergente entre advogado e juiz.
- **Acao sugerida:** validar com produto/arquitetura a tabela oficial de mapeamento; no estado atual do codigo, `LAWYER` foi normalizado para `CASE_ASSESSMENT` e `JUDGE` para `SECOND_INSTANCE`.

- **Descricao da pendencia:** `FIRST_INSTANCE` ainda nao possui um contrato de status proprio e reaproveita `CaseAssessmentAnalysisStatus` no agregado `Analysis`.
- **Impacto na implementacao:** os endpoints, use cases e polling conseguem funcionar, mas o dominio ainda nao distingue formalmente os status de `CASE_ASSESSMENT` e `FIRST_INSTANCE`.
- **Acao sugerida:** definir a tabela de status dedicada de `FIRST_INSTANCE` antes de concluir a separacao completa dos fluxos.

- **Descricao da pendencia:** o schema aplicado no banco esta em `head`, mas `uv run alembic check` ainda falha porque os models ORM ainda registram `PetitionModel` e `PetitionSummaryModel` mesmo apos a migration estrutural de `analysis_documents` e `case_summaries`.
- **Impacto na implementacao:** a codebase fica com drift entre metadata ORM e migrations, impedindo considerar o schema plenamente consistente.
- **Acao sugerida:** remover ou isolar os models legados de `petitions` e alinhar tipos/indices remanescentes ate o `alembic check` ficar limpo.

- **Descricao da pendencia:** a spec assume que `POST /intake/analyses/{analysis_id}/document` continua com semantica de upsert, preservando o comportamento atual de substituicao do documento existente.
- **Impacto na implementacao:** se o cliente desejar semantica estritamente idempotente, pode ser preferivel `PUT` em vez de `POST`.
- **Acao sugerida:** alinhar com mobile antes do merge final do contrato HTTP; se nao houver preferencia, manter `POST` para minimizar churn na borda.

---

## Restricoes

- **Nao inclua testes automatizados na spec.**
- O `core` nao deve depender de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest` ou qualquer detalhe de infraestrutura.
- Todos os caminhos citados existem no projeto ou estao explicitamente marcados como **novo arquivo**.
- **Nao invente** jobs ou endpoints de geracao/leitura de drafts fora do que foi explicitamente colocado em escopo; `PetitionDraft` e `SecondInstanceJudgmentDraft` entram aqui como contratos e persistencia base.
- Toda referencia a codigo existente usa caminho relativo real em `src/animus/...` ou `migrations/...`.
- Se uma camada nao se aplica, ela foi preenchida explicitamente com **Nao aplicavel**.
- Schemas `*Body` de entrada continuam definidos no proprio controller que os utiliza.
