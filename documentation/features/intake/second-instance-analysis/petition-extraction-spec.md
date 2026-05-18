---
title: Extração e sumarização de petição inicial em análise de segunda instância
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AQDxAg
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-116
status: closed
last_updated_at: 2026-05-14
---

# 1. Objetivo

Implementar o pipeline assíncrono de extração da petição inicial dentro dos autos completos de uma `SECOND_INSTANCE` analysis e, em seguida, sumarizar o conteúdo extraído como `CaseSummary`. A entrega cria cache persistido dos limites da petição extraída, adiciona providers de leitura parcial de PDF, adiciona workflows Agno específicos para extração e sumarização de segunda instância, e registra um novo job Inngest que publica `CaseSummaryFinishedEvent` ao concluir.

# 2. Escopo

## 2.1 In-scope

- Criar o domínio `ExtractedPetition` para persistir `analysis_id`, `first_page` e `last_page`.
- Criar port e repositório SQLAlchemy para cache de extração por `analysis_id`.
- Criar `SecondInstanceCaseSummarizationTriggeredEvent` para acionar o job assíncrono.
- Alterar `RequestCaseSummaryUseCase` para publicar `SecondInstanceCaseSummarizationTriggeredEvent` quando a análise for `SECOND_INSTANCE`.
- Reutilizar o endpoint existente `POST /intake/analyses/{analysis_id}/case-summaries` como gatilho HTTP do processamento.
- Estender `PdfProvider` com contagem de páginas e extração de intervalo de páginas.
- Criar `ExtractPetitionWorkflow` e implementação `AgnoExtractPetitionWorkflow` para identificar páginas da petição inicial.
- Criar `AgnoSummarizeSecondInstanceCaseWorkflow` para resumir a petição extraída com prompt orientado a recurso de segunda instância.
- Criar `SummarizeSecondInstanceCaseJob` para orquestrar extração, cache, sumarização, atualização de status e publicação de evento de conclusão.
- Registrar o novo job na composição Inngest.
- Criar migration Alembic para a tabela `extracted_petitions`.

## 2.2 Out-of-scope

- Criar novos endpoints HTTP.
- Implementar confirmação ou correção manual da peça extraída pelo juiz.
- Implementar seleção manual de páginas no PDF.
- Implementar OCR ou leitura de autos escaneados sem camada textual.
- Alterar geração de minuta de sentença ou exportação de PDF.
- Alterar busca de precedentes, síntese de precedentes ou regras de ranqueamento.
- Alterar o fluxo de `CASE_ASSESSMENT` ou `FIRST_INSTANCE`, exceto para preservar o comportamento atual no branching do use case.
- Validar limite de 20MB no job, pois o payload atual de `CreateAnalysisDocumentController` não recebe tamanho do arquivo.

# 3. Requisitos

## 3.1 Funcionais

- Ao solicitar resumo de caso para uma análise `SECOND_INSTANCE`, o sistema deve iniciar extração da petição inicial a partir do documento principal da análise.
- Se já existir `ExtractedPetition` para a análise, o job deve reutilizar o cache e não chamar novamente o workflow de extração.
- Se não existir cache, o job deve localizar `first_page` e `last_page` via `AgnoExtractPetitionWorkflow` e persistir o resultado.
- O job deve extrair apenas as páginas identificadas como petição inicial e usar esse conteúdo para gerar `CaseSummary`.
- A sumarização de segunda instância deve orientar `requested_relief`, `central_question`, `standing_issue` e `procedural_issues` para contexto recursal.
- Ao concluir a sumarização, o job deve publicar `CaseSummaryFinishedEvent(analysis_id, account_id)`.
- Quando não for possível identificar a petição inicial nos autos, o job deve marcar a análise como `PETITION_NOT_FOUND`.
- Em falha não tratada, o job deve marcar a análise como `FAILED`.

## 3.2 Não funcionais

- **Segurança:** o job deve processar somente documentos vinculados à `analysis_id` persistida; a autorização do usuário permanece no endpoint existente via `IntakePipe.verify_analysis_by_account_from_request(...)`.
- **Idempotência:** reexecuções do job devem reutilizar `ExtractedPetition` quando existir e substituir `CaseSummary` existente via fluxo já suportado por `CreateCaseSummaryUseCase`.
- **Resiliência:** exceções na extração, leitura de PDF, sumarização ou persistência devem resultar em status `FAILED` na analysis, exceto quando a petição inicial não for encontrada, caso em que o status deve ser `PETITION_NOT_FOUND`.
- **Compatibilidade retroativa:** o endpoint `POST /intake/analyses/{analysis_id}/case-summaries` deve manter o mesmo contrato HTTP e continuar publicando `CaseSummaryRequestedEvent` para `CASE_ASSESSMENT` e `FIRST_INSTANCE`.
- **Compatibilidade de fluxo:** a diferenciação entre jobs deve acontecer no `RequestCaseSummaryUseCase`, com branching por `AnalysisType` e publicação de eventos distintos, sem criar novo endpoint.
- **Compatibilidade de dados:** a nova tabela `extracted_petitions` deve usar `analysis_id` como chave primária e `ON DELETE CASCADE` para acompanhar o ciclo de vida de `analyses`.

# 4. O que já existe?

## Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analyses.py`) - entidade que normaliza `AnalysisType` e status por tipo de análise.
- **`AnalysisType`** (`src/animus/core/intake/domain/entities/analysis_type.py`) - enum com `CASE_ASSESSMENT`, `FIRST_INSTANCE` e `SECOND_INSTANCE`; expõe `uses_case_assessment_or_first_instance_flow()`.
- **`SecondInstanceAnalysisStatus`** (`src/animus/core/intake/domain/entities/second_instance_analysis_status.py`) - status de segunda instância; já contém `EXTRACTING_PETITION`, `ANALYZING_CASE`, `CASE_ANALYZED`, `PETITION_NOT_FOUND` e `FAILED`.
- **`AnalysisDocument`** (`src/animus/core/intake/domain/structures/analysis_document.py`) - structure do documento principal da análise.
- **`CaseSummary`** (`src/animus/core/intake/domain/structures/case_summary.py`) - structure do resumo persistido por análise.
- **`CaseSummaryDto`** (`src/animus/core/intake/domain/structures/dtos/case_summary_dto.py`) - DTO retornado por workflows e use cases de sumarização.
- **`AnalysisDocumentsRepository`** (`src/animus/core/intake/interfaces/analysis_documents_repository.py`) - port para buscar o documento por `analysis_id`.
- **`CaseSummariesRepository`** (`src/animus/core/intake/interfaces/case_summaries_repository.py`) - port para adicionar, substituir e buscar resumo por `analysis_id`.
- **`SummarizeFirstInstanceCaseWorkflow`** (`src/animus/core/intake/interfaces/summarize_case_workflow.py`) - contrato atual de sumarização geral: `run(analysis_id: str, document_content: Text) -> CaseSummaryDto`.
- **`RequestCaseSummaryUseCase`** (`src/animus/core/intake/use_cases/request_case_summary_use_case.py`) - use case que hoje atualiza status e publica `CaseSummaryRequestedEvent`.
- **`CreateCaseSummaryUseCase`** (`src/animus/core/intake/use_cases/create_case_summary_use_case.py`) - cria ou substitui `CaseSummary` e atualiza status para `CASE_ANALYZED`.
- **`UpdateAnalysisStatusUseCase`** (`src/animus/core/intake/use_cases/update_analysis_status_use_case.py`) - altera status da analysis via `AnalisysesRepository`.
- **`CaseSummaryFinishedEvent`** (`src/animus/core/intake/domain/events/case_summary_finished_event.py`) - evento existente de conclusão do resumo.
- **`CaseSummaryRequestedEvent`** (`src/animus/core/intake/domain/events/case_summary_requested_event.py`) - evento atual do fluxo de sumarização geral.

## Storage / Providers

- **`File`** (`src/animus/core/storage/domain/structures/file.py`) - structure de arquivo em memória retornada por storage.
- **`FileStorageProvider`** (`src/animus/core/storage/interfaces/file_storage_provider.py`) - port para recuperar arquivo por `FilePath`.
- **`PdfProvider`** (`src/animus/core/storage/interfaces/pdf_provider.py`) - port atual com `extract_content(pdf_file: File) -> Text`.
- **`PypdfPdfProvider`** (`src/animus/providers/storage/document/pdf/pypdf_pdf_provider.py`) - adapter atual que usa `pypdf.PdfReader` para extrair texto de todas as páginas.
- **`GcsFileStorageProvider`** (`src/animus/providers/storage/file_storage/gcs/gcs_file_storage_provider.py`) - adapter de storage usado por jobs para baixar o documento persistido.

## AI

- **`CaseSummaryOutput`** (`src/animus/ai/agno/outputs/intake/case_summary_output.py`) - schema Pydantic usado para normalizar a saída do agente de resumo.
- **`IntakeSquad`** (`src/animus/ai/agno/teams/intake_squad.py`) - team Agno que concentra agentes de intake como propriedades `@property`.
- **`AgnoSummarizeFirstInstanceCaseWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_summarize_case_workflow.py`) - workflow análogo para sumarização geral de documento jurídico.

## Database

- **`AnalysisModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_model.py`) - model de `analyses`; já relaciona `document`, `case_summary`, `petition_draft` e `judgment_draft`.
- **`AnalysisDocumentModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_document_model.py`) - tabela `analysis_documents` com `analysis_id`, path e nome do documento.
- **`CaseSummaryModel`** (`src/animus/database/sqlalchemy/models/intake/case_summary_model.py`) - tabela `case_summaries` com PK em `analysis_id`.
- **`CaseSummaryMapper`** (`src/animus/database/sqlalchemy/mappers/intake/case_summary_mapper.py`) - referência para mapear structure e model com campos escalares e JSON.
- **`SqlalchemyCaseSummariesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_case_summaries_repository.py`) - referência de repositório com `find_by_analysis_id`, `add` e `replace`.

## REST

- **`RequestCaseSummaryController`** (`src/animus/rest/controllers/intake/request_case_summary_controller.py`) - expõe `POST /analyses/{analysis_id}/case-summaries` e delega para `RequestCaseSummaryUseCase`.
- **`CreateAnalysisDocumentController`** (`src/animus/rest/controllers/intake/create_analysis_document_controller.py`) - persiste metadados do documento principal; não deve ser alterado para esta spec.

## PubSub

- **`SummarizeFirstInstanceCaseJob`** (`src/animus/pubsub/inngest/jobs/intake/summarize_case_job.py`) - padrão de job Inngest com `_normalize_payload`, execução síncrona em executor, tratamento de falha e publicação de evento final.
- **`SearchAnalysisPrecedentsJob`** (`src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`) - referência de job de intake com múltiplos steps e status de erro.
- **`InngestPubSub`** (`src/animus/pubsub/inngest/inngest_pubsub.py`) - composition root onde jobs de intake são registrados.

## Seeders

- **`StorageSeeder`** (`src/animus/database/sqlalchemy/seeders/storage_seeder.py`) - já usa prefixo `intake/analises/{analysis_id}/documents/{arquivo}` para arquivos PDF seedados.
- **`IntakeSeeder`** (`src/animus/database/sqlalchemy/seeders/intake_seeder.py`) - ainda usa contratos legados de `Petition` e `PetitionSummary`; não é pré-requisito para esta spec, mas é um ponto de atenção fora do recorte.

# 5. O que deve ser criado?

## Camada Core (Structures / DTOs)

- **Localização:** `src/animus/core/intake/domain/structures/extracted_petition.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `analysis_id: Id`, `first_page: Integer`, `last_page: Integer`
- **Métodos / factory:** `create(dto: ExtractedPetitionDto) -> ExtractedPetition` - normaliza `analysis_id`, valida páginas e cria a structure; `dto -> ExtractedPetitionDto` - expõe contrato serializável.
- **Validações:** `first_page >= 1` e `last_page >= first_page`; usar `ValidationError` para intervalos inválidos.

- **Localização:** `src/animus/core/intake/domain/structures/dtos/extracted_petition_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `analysis_id: str`, `first_page: int`, `last_page: int`

- **Localização:** `src/animus/core/intake/domain/structures/dtos/petition_extraction_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `first_page: int`, `last_page: int`
- **Responsabilidade:** transportar o resultado de extração entre `ExtractPetitionWorkflow` e o job, sem expor schema Pydantic da camada AI ao `core`.

## Camada Core (Interfaces / Ports)

- **Localização:** `src/animus/core/intake/interfaces/extracted_petitions_repository.py` (**novo arquivo**)
- **Métodos:** `find_by_analysis_id(analysis_id: Id) -> ExtractedPetition | None` - busca cache de extração; `add(extracted_petition: ExtractedPetition) -> None` - persiste cache novo; `replace(extracted_petition: ExtractedPetition) -> None` - atualiza cache existente.

- **Localização:** `src/animus/core/intake/interfaces/extract_petition_workflow.py` (**novo arquivo**)
- **Métodos:** `run(pdf_file: File) -> PetitionExtractionDto` - identifica as páginas inicial e final da petição inicial dentro dos autos.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/create_extracted_petition_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `ExtractedPetitionsRepository`
- **Método principal:** `execute(analysis_id: str, first_page: int, last_page: int) -> ExtractedPetitionDto` - cria `ExtractedPetition`, valida o intervalo e persiste o cache.
- **Fluxo resumido:** normaliza entrada, cria structure, consulta `find_by_analysis_id(...)`; se não existir, chama `add(...)`; se existir, chama `replace(...)`; retorna DTO.

## Camada Database (Models SQLAlchemy)

- **Localização:** `src/animus/database/sqlalchemy/models/intake/extracted_petition_model.py` (**novo arquivo**)
- **Tabela:** `extracted_petitions`
- **Colunas:** `analysis_id: String(26), primary_key=True, ForeignKey('analyses.id', ondelete='CASCADE')`; `first_page: Integer, nullable=False`; `last_page: Integer, nullable=False`; colunas herdadas `created_at` e `updated_at` via `Model`.
- **Relacionamentos:** `analysis: relationship('AnalysisModel', back_populates='extracted_petition')`

## Camada Database (Mappers)

- **Localização:** `src/animus/database/sqlalchemy/mappers/intake/extracted_petition_mapper.py` (**novo arquivo**)
- **Métodos:** `to_entity(model: ExtractedPetitionModel) -> ExtractedPetition` - traduz cache persistido para structure; `to_model(extracted_petition: ExtractedPetition) -> ExtractedPetitionModel` - traduz structure para persistência.

## Camada Database (Repositórios)

- **Localização:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_extracted_petitions_repository.py` (**novo arquivo**)
- **Interface implementada:** `ExtractedPetitionsRepository`
- **Dependências:** `Session` SQLAlchemy
- **Métodos:** `find_by_analysis_id(analysis_id: Id) -> ExtractedPetition | None` - busca por PK; `add(extracted_petition: ExtractedPetition) -> None` - adiciona model novo; `replace(extracted_petition: ExtractedPetition) -> None` - carrega model existente por PK e atualiza `first_page` e `last_page`.
- **Seeders da camada database:** não há seeder obrigatório para `extracted_petitions`; `StorageSeeder` já usa paths em `documents`. Não criar dados seedados de extração sem PDF real correspondente.

## Camada Providers

- **Localização:** `src/animus/core/storage/interfaces/pdf_provider.py` (**arquivo existente**)
- **Interface implementada (port):** `PdfProvider`
- **Métodos novos:** `count_pages(pdf_file: File) -> Integer` - retorna quantidade de páginas do PDF; `extract_pages(pdf_file: File, start: Integer, end: Integer) -> Text` - extrai texto do intervalo 1-based e inclusivo `[start, end]`.

- **Localização:** `src/animus/providers/storage/document/pdf/pypdf_pdf_provider.py` (**arquivo existente**)
- **Biblioteca/SDK utilizado:** `pypdf`
- **Métodos novos:** `count_pages(pdf_file: File) -> Integer` - usa `len(PdfReader(...).pages)`; `extract_pages(pdf_file: File, start: Integer, end: Integer) -> Text` - usa `reader.pages[start.value - 1 : end.value]`, une textos com `\n` e retorna `Text.create(...)`.

## Camada AI (Outputs)

- **Localização:** `src/animus/ai/agno/outputs/intake/petition_extraction_output.py` (**novo arquivo**)
- **Tipo:** `BaseModel`
- **Atributos:** `first_page: int | None = None`, `last_page: int | None = None`
- **Responsabilidade:** contrato estruturado de saída do agente que identifica a petição inicial.

## Camada AI (Workflows)

- **Localização:** `src/animus/ai/agno/workflows/intake/agno_extract_petition_workflow.py` (**novo arquivo**)
- **Interface implementada:** `ExtractPetitionWorkflow`
- **Dependências:** `PdfProvider`
- **Método principal:** `run(pdf_file: File) -> PetitionExtractionDto` - executa loop iterativo de análise do PDF até localizar `first_page` e `last_page` ou falhar.
- **Fluxo resumido:** contar páginas, extrair ranges sequenciais em janelas fixas de `5` páginas, chamar `IntakeSquad.petition_extractor_agent`, manter histórico de mensagens entre iterações, validar `PetitionExtractionOutput` interno e retornar `PetitionExtractionDto`.

- **Localização:** `src/animus/ai/agno/workflows/intake/agno_summarize_second_instance_case_workflow.py` (**novo arquivo**)
- **Interface implementada:** `SummarizeFirstInstanceCaseWorkflow`
- **Dependências:** `CaseSummariesRepository`, `AnalysisDocumentsRepository`, `AnalisysesRepository`
- **Método principal:** `run(analysis_id: str, document_content: Text) -> CaseSummaryDto` - sumariza a petição extraída com contexto de recurso e persiste via `CreateCaseSummaryUseCase`.
- **Fluxo resumido:** montar prompt especializado, chamar `IntakeSquad.second_instance_case_summarizer_agent`, normalizar `CaseSummaryOutput`, executar `CreateCaseSummaryUseCase.execute(...)`.

## Camada AI (Agents)

- **Localização:** `src/animus/ai/agno/teams/intake_squad.py` (**arquivo existente**)
- **Agent novo:** `petition_extractor_agent` - identifica início e fim da petição inicial em ranges de páginas dos autos.
- **Agent novo:** `second_instance_case_summarizer_agent` - gera `CaseSummaryOutput` com foco em recurso de segunda instância.
- **Responsabilidade:** ambos devem ser propriedades `@property`, usar `textwrap.dedent` para instruções e declarar `output_schema` adequado.

## Camada Core (Eventos de Domínio)

- **Localização:** `src/animus/core/intake/domain/events/petition_extraction_requested_event.py` (**novo arquivo**)
- **`NAME`:** `intake/petition.extraction.requested`
- **Payload:** `analysis_id: str`

## Camada PubSub (Jobs Inngest)

- **Localização:** `src/animus/pubsub/inngest/jobs/intake/extract_petition_job.py` (**novo arquivo**)
- **Evento consumido:** `SecondInstanceCaseSummarizationTriggeredEvent.name` com payload `analysis_id`.
- **Dependências:** `SqlalchemyAnalysisDocumentsRepository`, `SqlalchemyCaseSummariesRepository`, `SqlalchemyAnalisysesRepository`, `SqlalchemyExtractedPetitionsRepository`, `GcsFileStorageProvider`, `PypdfPdfProvider`, `AgnoExtractPetitionWorkflow`, `AgnoSummarizeSecondInstanceCaseWorkflow`, `CreateExtractedPetitionUseCase`, `UpdateAnalysisStatusUseCase`, `InngestBroker`.
- **Passos (`step.run`):** `normalize_payload`; `extract_and_summarize`; `publish_finished_event`; em exceção, `mark_analysis_as_failed`.
- **Métodos:** `handle(inngest: Inngest) -> Any` - registra function Inngest; `_normalize_payload(data: dict[str, Any]) -> dict[str, str]` - normaliza payload; `_extract_and_summarize(payload: _Payload) -> dict[str, str]` - delega execução bloqueante para executor; `_extract_and_summarize_sync(payload: _Payload) -> dict[str, str]` - executa transação de extração e sumarização; `_mark_petition_as_not_found(payload: _Payload) -> None` - delega marcação de ausência de petição; `_mark_petition_as_not_found_sync(payload: _Payload) -> None` - atualiza status para `PETITION_NOT_FOUND` e comita; `_mark_analysis_as_failed(payload: _Payload) -> None` - delega marcação de falha; `_mark_analysis_as_failed_sync(payload: _Payload) -> None` - atualiza status para `FAILED` e comita; `_handle_failure(context: Context) -> None` - trata falhas capturadas pelo Inngest.
- **Idempotência:** `ExtractedPetitionsRepository.find_by_analysis_id(...)` evita nova chamada ao workflow de extração; `CreateCaseSummaryUseCase` já substitui resumo existente; publicação de `CaseSummaryFinishedEvent` só ocorre após sucesso da execução principal.

## Migrações Alembic

- **Localização:** `migrations/versions/` (**novo arquivo**)
- **Operações:** criar tabela `extracted_petitions` com `analysis_id`, `first_page`, `last_page`, timestamps herdados pelo padrão das migrations existentes e FK cascade para `analyses.id`; adicionar índice se o padrão de autogeração criar índice para PK/FK.
- **Reversibilidade:** `downgrade` pode remover `extracted_petitions`; perda de cache é aceitável porque a extração pode ser reexecutada a partir do PDF original.

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/use_cases/request_case_summary_use_case.py`
- **Mudança:** concentrar o branching por `AnalysisType`; quando `analysis.type.uses_case_assessment_or_first_instance_flow()` for `True`, manter status `ANALYZING_CASE` e publicar `CaseSummaryRequestedEvent`; quando `analysis.type == AnalysisType.SECOND_INSTANCE`, setar `SecondInstanceAnalysisStatus.EXTRACTING_PETITION` e publicar `SecondInstanceCaseSummarizationTriggeredEvent`.
- **Justificativa:** o endpoint existente continua sendo o gatilho do processamento, mas o fluxo de segunda instância precisa extrair a petição dos autos antes da sumarização.

- **Arquivo:** `src/animus/core/intake/domain/events/__init__.py`
- **Mudança:** exportar `SecondInstanceCaseSummarizationTriggeredEvent` em imports e `__all__`.
- **Justificativa:** manter padrão de exports públicos dos eventos de intake.

- **Arquivo:** `src/animus/core/intake/domain/structures/__init__.py`
- **Mudança:** exportar `ExtractedPetition` em `TYPE_CHECKING`, `__all__` e `__getattr__`.
- **Justificativa:** manter padrão de lazy exports das structures do domínio.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/__init__.py`
- **Mudança:** exportar `ExtractedPetitionDto` e `PetitionExtractionDto`.
- **Justificativa:** manter acesso público aos DTOs do contexto.

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudança:** exportar `ExtractedPetitionsRepository` e `ExtractPetitionWorkflow`.
- **Justificativa:** manter padrão de imports agregados para ports do `core`.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** exportar `CreateExtractedPetitionUseCase`.
- **Justificativa:** manter consistência com os demais use cases públicos.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/analysis_model.py`
- **Mudança:** adicionar relacionamento `extracted_petition: relationship('ExtractedPetitionModel', back_populates='analysis', uselist=False, cascade='all, delete-orphan')`.
- **Justificativa:** manter navegação ORM e cascade coerentes com `document` e `case_summary`.

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/__init__.py`
- **Mudança:** exportar `ExtractedPetitionModel`.
- **Justificativa:** registrar o model no pacote de models de intake.

- **Arquivo:** `src/animus/database/sqlalchemy/mappers/intake/__init__.py`
- **Mudança:** exportar `ExtractedPetitionMapper`.
- **Justificativa:** manter padrão de exports dos mappers.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/__init__.py`
- **Mudança:** exportar `SqlalchemyExtractedPetitionsRepository`.
- **Justificativa:** permitir composition root em jobs e pipes.

## Pipes

- **Arquivo:** `src/animus/pipes/database_pipe.py`
- **Mudança:** adicionar `get_extracted_petitions_repository_from_request(sqlalchemy: Session) -> ExtractedPetitionsRepository`.
- **Justificativa:** manter disponibilidade do repositório via `Depends(...)` caso a próxima etapa exponha leitura/correção manual por HTTP; não é usado diretamente pelo job.

## Providers

- **Arquivo:** `src/animus/core/storage/interfaces/pdf_provider.py`
- **Mudança:** adicionar `count_pages(...)` e `extract_pages(...)` ao `Protocol`.
- **Justificativa:** o workflow de extração precisa iterar por ranges e o job precisa extrair apenas a petição identificada.

- **Arquivo:** `src/animus/providers/storage/document/pdf/pypdf_pdf_provider.py`
- **Mudança:** implementar os novos métodos sem alterar `extract_content(...)`.
- **Justificativa:** preservar compatibilidade do fluxo atual e adicionar leitura parcial para segunda instância.

## AI

- **Arquivo:** `src/animus/ai/agno/outputs/intake/__init__.py`
- **Mudança:** exportar `PetitionExtractionOutput`.
- **Justificativa:** manter padrão dos outputs Agno de intake.

- **Arquivo:** `src/animus/ai/agno/teams/intake_squad.py`
- **Mudança:** adicionar agents `petition_extractor_agent` e `second_instance_case_summarizer_agent`.
- **Justificativa:** separar prompts de extração e de sumarização recursal do agente atual de petição inicial.

- **Arquivo:** `src/animus/ai/agno/workflows/intake/__init__.py`
- **Mudança:** exportar `AgnoExtractPetitionWorkflow` e `AgnoSummarizeSecondInstanceCaseWorkflow`.
- **Justificativa:** manter padrão de exports dos workflows de intake.

## PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/__init__.py`
- **Mudança:** exportar `SummarizeSecondInstanceCaseJob`.
- **Justificativa:** permitir registro no composition root do Inngest.

- **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
- **Mudança:** importar e registrar `SummarizeSecondInstanceCaseJob.handle(inngest)` em `register_intake_jobs(...)`.
- **Justificativa:** tornar o consumidor de `SecondInstanceCaseSummarizationTriggeredEvent` ativo no runtime Inngest.

# 7. O que deve ser removido?

**Não aplicável**.

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** reutilizar `SecondInstanceAnalysisStatus.EXTRACTING_PETITION` em vez de criar `ANALYZING_DOCUMENT`.
- **Alternativas consideradas:** criar `ANALYZING_DOCUMENT` conforme texto do Jira.
- **Motivo da escolha:** a codebase já possui `EXTRACTING_PETITION` no enum de segunda instância e esse nome descreve melhor a etapa específica do job.
- **Impactos / trade-offs:** evita mudança de contrato de status para o app; diverge do rascunho técnico do Jira e precisa ficar registrado para revisão.

- **Decisão:** usar o endpoint existente `POST /intake/analyses/{analysis_id}/case-summaries` como gatilho.
- **Alternativas consideradas:** publicar `SecondInstanceCaseSummarizationTriggeredEvent` diretamente em `CreateAnalysisDocumentUseCase` após upload.
- **Motivo da escolha:** preserva o fluxo atual da API, no qual upload de metadados e solicitação de processamento são ações separadas.
- **Impactos / trade-offs:** a extração não inicia automaticamente apenas com `POST /document`; o app precisa continuar chamando o endpoint de request de resumo.

- **Decisão:** diferenciar o job acionado no `POST /intake/analyses/{analysis_id}/case-summaries` por `AnalysisType`, dentro de `RequestCaseSummaryUseCase`.
- **Alternativas consideradas:** criar endpoint dedicado para segunda instância; publicar sempre o mesmo evento e decidir o fluxo dentro de um único job.
- **Motivo da escolha:** mantém a superfície HTTP estável e usa o tipo de análise, que já é informação de domínio persistida, para escolher o evento correto.
- **Impactos / trade-offs:** o branching fica centralizado no `UseCase`; em contrapartida, a observabilidade precisa considerar dois eventos possíveis partindo do mesmo endpoint.

- **Decisão:** persistir cache em tabela dedicada `extracted_petitions` com PK `analysis_id`.
- **Alternativas consideradas:** adicionar colunas `extracted_petition_first_page` e `extracted_petition_last_page` em `analysis_documents`.
- **Motivo da escolha:** cache é resultado de processamento, não metadado de upload; tabela própria evita misturar responsabilidades.
- **Impactos / trade-offs:** exige migration e novo repository, mas mantém `analysis_documents` focado no documento original.

- **Decisão:** implementar `AgnoSummarizeSecondInstanceCaseWorkflow` separado de `AgnoSummarizeFirstInstanceCaseWorkflow`.
- **Alternativas consideradas:** parametrizar o prompt do workflow existente por tipo de análise.
- **Motivo da escolha:** o prompt de segunda instância tem semântica recursal própria e deve evoluir sem risco de regressão nos fluxos `CASE_ASSESSMENT` e `FIRST_INSTANCE`.
- **Impactos / trade-offs:** há alguma duplicação controlada de normalização de `CaseSummaryOutput`, compensada por isolamento de comportamento.

- **Decisão:** `SummarizeSecondInstanceCaseJob` publica `CaseSummaryFinishedEvent` somente após a sumarização persistir com sucesso.
- **Alternativas consideradas:** publicar evento específico de extração concluída antes da sumarização.
- **Motivo da escolha:** ANI-116 define um job único para extração e sumarização; o evento relevante para consumidores existentes é a conclusão do resumo.
- **Impactos / trade-offs:** a etapa intermediária de extração não fica observável por evento dedicado além do status persistido e do cache.

- **Decisão:** quando o workflow não encontrar limites válidos de petição inicial, marcar `SecondInstanceAnalysisStatus.PETITION_NOT_FOUND` em vez de `FAILED`.
- **Alternativas consideradas:** tratar ausência de petição como falha técnica (`FAILED`) ou criar evento dedicado de "petição não encontrada".
- **Motivo da escolha:** ausência de petição é resultado de negócio do processamento documental, não erro de infraestrutura.
- **Impactos / trade-offs:** melhora observabilidade e UX para tratamento orientado no app, com custo de ampliar contrato de status de segunda instância.

- **Decisão:** usar janela fixa de `5` páginas por iteração no `AgnoExtractPetitionWorkflow`.
- **Alternativas consideradas:** janelas menores de `3` páginas; janelas maiores de `10` páginas ou mais.
- **Motivo da escolha:** `5` páginas equilibram contexto suficiente para identificar começo/fim da petição com custo e payload controlados por iteração.
- **Impactos / trade-offs:** pode exigir mais iterações em autos muito longos, mas reduz risco de diluição de contexto e mantém previsibilidade operacional.

# 9. Diagramas e Referências

- **Fluxo de dados:**

```text
HTTP Request
  -> Middleware
  -> IntakeRouter
  -> RequestCaseSummaryController
  -> IntakePipe.verify_analysis_by_account_from_request(...)
  -> RequestCaseSummaryUseCase
  -> load Analysis
  -> [CASE_ASSESSMENT | FIRST_INSTANCE]
       status = ANALYZING_CASE
       Broker.publish(CaseSummaryRequestedEvent)
  -> [SECOND_INSTANCE]
       status = EXTRACTING_PETITION
       Broker.publish(SecondInstanceCaseSummarizationTriggeredEvent)
  -> Response 202
```

- **Fluxo assíncrono:**

```text
SecondInstanceCaseSummarizationTriggeredEvent(analysis_id)
  -> SummarizeSecondInstanceCaseJob
  -> SqlalchemyAnalysisDocumentsRepository.find_by_analysis_id(...)
  -> GcsFileStorageProvider.get_file(document.file_path)
  -> SqlalchemyExtractedPetitionsRepository.find_by_analysis_id(...)
  -> [cache miss]
       AgnoExtractPetitionWorkflow.run(pdf_file)
       CreateExtractedPetitionUseCase.execute(analysis_id, first_page, last_page)
  -> [cache hit]
       reutiliza first_page/last_page persistidos
  -> PypdfPdfProvider.extract_pages(pdf_file, start, end)
  -> status = ANALYZING_CASE
  -> AgnoSummarizeSecondInstanceCaseWorkflow.run(analysis_id, petition_content)
  -> CreateCaseSummaryUseCase.execute(...)
  -> status = CASE_ANALYZED
  -> session.commit()
  -> InngestBroker.publish(CaseSummaryFinishedEvent(analysis_id, account_id))
```

- **Fluxo de falha:**

```text
SummarizeSecondInstanceCaseJob exception
  -> mark_analysis_as_failed
  -> UpdateAnalysisStatusUseCase.execute(analysis_id, 'FAILED')
  -> session.commit()
  -> re-raise para observabilidade do Inngest
```

```text
SummarizeSecondInstanceCaseJob sem limites de petição
  -> mark_petition_as_not_found
  -> UpdateAnalysisStatusUseCase.execute(analysis_id, 'PETITION_NOT_FOUND')
  -> session.commit()
  -> encerra job sem publicar CaseSummaryFinishedEvent
```

- **Referências:**

- `src/animus/pubsub/inngest/jobs/intake/summarize_case_job.py` - padrão principal para `SummarizeSecondInstanceCaseJob`.
- `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py` - referência para jobs com múltiplos steps e marcação de falha.
- `src/animus/ai/agno/workflows/intake/agno_summarize_case_workflow.py` - base para `AgnoSummarizeSecondInstanceCaseWorkflow`.
- `src/animus/ai/agno/teams/intake_squad.py` - local dos novos agents.
- `src/animus/providers/storage/document/pdf/pypdf_pdf_provider.py` - base para `count_pages` e `extract_pages`.
- `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_case_summaries_repository.py` - referência para repository com `find_by_analysis_id`, `add` e `replace`.
- `src/animus/database/sqlalchemy/mappers/intake/case_summary_mapper.py` - referência para mapper structure/model.
- `migrations/versions/20260511_120000_intake_analysis_documents_case_summaries_and_drafts.py` - referência para migration com FK cascade por `analysis_id`.
