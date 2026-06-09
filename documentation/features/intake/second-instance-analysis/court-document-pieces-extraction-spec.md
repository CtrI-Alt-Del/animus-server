---
title: Extração determinística de peças processuais dos autos via outline do PDF
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AQDxAg
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-121
status: open
last_updated_at: 2026-05-27
---

# 1. Objetivo

Implementar a extração determinística das peças processuais mais importantes para análise de segunda instância, usando exclusivamente o `outline` nativo do PDF dos autos. A entrega cria estruturas e use case em `core/storage`, estende o `PdfProvider` e o `PypdfPdfProvider` para ler bookmarks, substitui no job de segunda instância a extração por LLM/cache pela extração por outline, concatena `sentenca`, `apelação` e `contrarrazoes` como `document_content`, e ajusta os status persistidos para refletir sucesso ou abort específico da extração de peças processuais, desbloqueando a sumarização que alimenta a geração posterior de minuta de decisão/acórdão de segunda instância.

# 2. Escopo

## 2.1 In-scope

- Criar estruturas de domínio em `core/storage` para representar `outline` bruto, itens classificados e peças extraídas.
- Criar erros de domínio para PDF sem índice e autos sem peças obrigatórias.
- Criar `ExtractCourtDocumentPiecesUseCase` recebendo `FileDto` e usando `PdfProvider` com `File` internamente.
- Estender `PdfProvider` com `extract_outline(pdf_file: File) -> list[PdfOutlineItem]`.
- Implementar leitura de `reader.outline` no `PypdfPdfProvider`, preservando ordem do outline e convertendo páginas para base 1.
- Alterar `SummarizeSecondInstanceCaseJob` para usar a extração determinística antes de chamar `AgnoSummarizeSecondInstanceCaseWorkflow`.
- Alterar o prompt de `AgnoSummarizeSecondInstanceCaseWorkflow` para tratar o conteúdo como peças processuais de segunda instância, não como petição inicial isolada.
- Adicionar status de processamento e abort específicos em `SecondInstanceAnalysisStatus`.
- Manter o endpoint existente de disparo assíncrono de resumo de segunda instância.

## 2.2 Out-of-scope

- Criar novos endpoints HTTP.
- Implementar confirmação ou correção manual de peça extraída pelo Juiz.
- Implementar OCR ou leitura de PDFs escaneados sem camada textual.
- Usar LLM, sliding window ou heurísticas sem outline para identificar peças.
- Persistir cache das peças extraídas em banco.
- Remover `ExtractedPetition`, `ExtractedPetitionsRepository` ou `AgnoExtractPetitionWorkflow` nesta entrega.
- Alterar busca de precedentes, classificação de precedentes, geração de minuta ou exportação de PDF.
- Alterar os fluxos `CASE_ASSESSMENT` e `FIRST_INSTANCE`.
- Incluir testes automatizados nesta spec.

# 3. Requisitos

## 3.1 Funcionais

- Ao processar uma análise `SECOND_INSTANCE`, o job deve baixar o PDF dos autos a partir de `AnalysisDocument.file_path` e extrair as peças por outline.
- A extração deve priorizar as peças indicadas pelo Glossário Jurídico como entradas mais importantes para minuta de decisão de segunda instância: `Sentença`, `Apelação` e `Contrarrazões`, quando houver.
- Se o PDF não possuir outline utilizável, o use case deve levantar `CourtDocumentIndexNotFoundError`.
- Se `sentenca` ou `apelação` não forem encontradas por string matching no outline, o use case deve levantar `InsufficientCourtDocumentError`.
- `contrarrazoes` são opcionais; a ausência desse tipo de peça não deve abortar o fluxo.
- Os ranges de páginas devem ser derivados diretamente do outline bruto, sem LLM e sem sliding window.
- Múltiplas sentenças devem ser extraídas e concatenadas em ordem crescente de página.
- Múltiplas contrarrazões devem ser extraídas e concatenadas em ordem crescente de página.
- Quando houver entradas `Apelação em PDF` e `Apelação`, a extração deve preferir as entradas com `em PDF`.
- O `document_content` enviado para `AgnoSummarizeSecondInstanceCaseWorkflow` deve concatenar as peças na ordem estável `sentenca`, `apelação`, `contrarrazoes`.
- O job deve marcar a análise como `COURT_DOCUMENT_PIECES_NOT_FOUND` para aborts de domínio causados por outline ausente ou peças obrigatórias ausentes.
- O job deve marcar a análise como `FAILED` para falhas operacionais não tratadas, como PDF corrompido, erro de storage ou exceção inesperada no provider.

Regras de classificação por `CourtDocumentOutline._classify(...)`:

| Título normalizado | Resultado |
|---|---|
| Contém `sentenca` | `CourtDocumentPieceKind.SENTENCA` |
| Contém `apelação em pdf` | `CourtDocumentPieceKind.APELACAO`, com preferência sobre entradas genéricas |
| Contém `apelação` | `CourtDocumentPieceKind.APELACAO` |
| Contém `contrarrazoes` ou `contra-razoes` | `CourtDocumentPieceKind.CONTRARRAZOES` |

O título deve ser normalizado com `casefold()`, remoção de acentos e `strip()` antes do matching.

## 3.2 Não funcionais

- **Performance:** a extração deve fazer leitura determinística do outline e dos ranges necessários, evitando chamadas de IA para localização das peças.
- **Segurança:** o job deve processar somente o documento persistido para a `analysis_id` do evento; a autorização permanece no endpoint existente via `IntakePipe.verify_analysis_by_account_from_request(...)`.
- **Idempotência:** reexecuções do job devem ser seguras; a extração é recalculada a partir do PDF e `CreateCaseSummaryUseCase` já substitui o resumo existente quando aplicável.
- **Resiliência:** aborts esperados de domínio devem atualizar status terminal específico sem publicar `CaseSummaryFinishedEvent`; falhas inesperadas devem atualizar `FAILED` e continuar observáveis pelo Inngest.
- **Observabilidade:** o app deve conseguir acompanhar `EXTRACTING_COURT_DOCUMENT_PIECES`, `ANALYZING_CASE`, `CASE_ANALYZED`, `COURT_DOCUMENT_PIECES_NOT_FOUND` e `FAILED` por `GET /intake/analyses/{analysis_id}/status`.
- **Compatibilidade retroativa:** o contrato HTTP do endpoint de disparo permanece inalterado; a alteração de contrato observável é a adição de novos valores de status para `SECOND_INSTANCE`.

# 4. O que já existe?

## Core / Storage

- **`File`** (`src/animus/core/storage/domain/structures/file.py`) — structure de arquivo em memória retornada por storage providers; o `PdfProvider` atual recebe esse tipo.
- **`FileDto`** (`src/animus/core/storage/domain/structures/dtos/file_dto.py`) — DTO serializável de `File`; será a entrada pública do novo use case conforme decisão da spec.
- **`PdfProvider`** (`src/animus/core/storage/interfaces/pdf_provider.py`) — port já possui `count_pages(pdf_file: File) -> Integer`, `extract_pages(pdf_file: File, start: Integer, end: Integer) -> Text` e `extract_content(pdf_file: File) -> Text`.
- **`GetDocumentContentUseCase`** (`src/animus/core/storage/use_cases/get_document_content_use_case.py`) — referência de use case em `core/storage` que orquestra providers sem depender de infraestrutura.

## Providers

- **`PypdfPdfProvider`** (`src/animus/providers/storage/document/pdf/pypdf_pdf_provider.py`) — implementação concreta de `PdfProvider` usando `pypdf.PdfReader`; já implementa contagem de páginas, extração por range e extração integral.
- **`GcsFileStorageProvider`** (`src/animus/providers/storage/file_storage/gcs/gcs_file_storage_provider.py`) — provider usado pelo job de segunda instância para baixar o PDF persistido no storage.

## Core / Intake

- **`SecondInstanceAnalysisStatus`** (`src/animus/core/intake/domain/structures/second_instance_analysis_status.py`) — enum/structure de status de segunda instância; hoje não possui status específico para extração ou abort de peças processuais.
- **`TriggerSecondInstanceCaseSummarizationUseCase`** (`src/animus/core/intake/use_cases/trigger_second_instance_case_summarization_use_case.py`) — valida analysis/documento, atualiza status e publica `SecondInstanceCaseSummarizationTriggeredEvent`.
- **`UpdateAnalysisStatusUseCase`** (`src/animus/core/intake/use_cases/update_analysis_status_use_case.py`) — referência para atualizar status da analysis por repository, sem regra no job.
- **`CreateCaseSummaryUseCase`** (`src/animus/core/intake/use_cases/create_case_summary_use_case.py`) — persiste ou substitui `CaseSummary` e conclui status de análise de caso.
- **`SummarizeFirstInstanceCaseWorkflow`** (`src/animus/core/intake/interfaces/summarize_case_workflow.py`) — contrato usado pelo workflow de sumarização: `run(analysis_id: str, document_content: Text) -> CaseSummaryDto`.

## REST / Routers / Pipes

- **`TriggerSecondInstanceCaseSummarizationController`** (`src/animus/rest/controllers/intake/trigger_second_instance_case_summarization_controller.py`) — expõe `POST /intake/analyses/{analysis_id}/case-summaries/second-instance` com `202` e delega ao use case.
- **`IntakePipe.verify_analysis_by_account_from_request`** (`src/animus/pipes/intake_pipe.py`) — valida autenticação/ownership antes do disparo do processamento.
- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) — provê repositories de `analyses` e `analysis_documents` usados pelo controller.
- **`PubSubPipe.get_broker_from_request`** (`src/animus/pipes/pubsub_pipe.py`) — provê `Broker` para publicação do evento Inngest.

## AI

- **`AgnoSummarizeSecondInstanceCaseWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_summarize_second_instance_case_workflow.py`) — consumidor do `document_content`; hoje o prompt descreve o conteúdo como petição inicial e precisa ser ajustado para peças processuais.
- **`AgnoExtractPetitionWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_extract_petition_workflow.py`) — implementação legada por LLM/sliding window para localizar petição; deve deixar de ser usada neste fluxo, mas não será removida nesta entrega.

## PubSub

- **`SecondInstanceCaseSummarizationTriggeredEvent`** (`src/animus/core/intake/domain/events/secod_instance_summarization_triggered_event.py`) — evento já consumido pelo job de resumo de segunda instância.
- **`SummarizeSecondInstanceCaseJob`** (`src/animus/pubsub/inngest/jobs/intake/summarize_second_instance_case_job.py`) — job atual baixa o PDF, tenta localizar petição por `AgnoExtractPetitionWorkflow`, usa cache em `ExtractedPetitionsRepository` e chama o workflow de resumo.
- **`CaseSummaryFinishedEvent`** (`src/animus/core/intake/domain/events/case_summary_finished_event.py`) — evento publicado após a sumarização persistir com sucesso.

## Database / Seeders

- **`AnalysisModel.status`** (`src/animus/database/sqlalchemy/models/intake/analysis_model.py`) — status persistido como `String`, sem enum nativo no banco; novos valores não exigem migration.
- **`SqlalchemyAnalysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analyses_repository.py`) — usa `SecondInstanceAnalysisStatus.get_processing_statuses()` para listar análises em processamento.
- **`StorageSeeder`** (`src/animus/database/sqlalchemy/seeders/storage_seeder.py`) — seeda arquivos em paths de storage; não há impacto obrigatório, mas PDFs usados para segunda instância só completarão o novo fluxo se possuírem outline compatível.

## Confluence / Domínio Jurídico

- **`Glossário Jurídico — Conceitos do Domínio do Animus`** (`https://joaogoliveiragarcia.atlassian.net/wiki/x/AwBXAQ`) — define segunda instância como fase de revisão da sentença por apelação e confirma que as peças mais importantes como entrada são `Sentença`, `Apelação` e `Contrarrazões`, se houver.

# 5. O que deve ser criado?

## Camada Core (Structures / DTOs)

- **Localização:** `src/animus/core/storage/domain/structures/court_document_piece_kind.py` (**novo arquivo**)
- **Tipo:** `StrEnum` auxiliar de domínio
- **Atributos:** `SENTENCA = 'sentenca'`, `APELACAO = 'apelação'`, `CONTRARRAZOES = 'contrarrazoes'`
- **Métodos / factory:** Não aplicável.

- **Localização:** `src/animus/core/storage/domain/structures/pdf_outline_item.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `title: Text`, `page_number: Integer`
- **Métodos / factory:** `create(title: str, page_number: int) -> PdfOutlineItem` — normaliza título e página base 1; lança `ValidationError` se `page_number < 1`.

- **Localização:** `src/animus/core/storage/domain/structures/court_document_outline_item.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `title: Text`, `page_start: Integer`, `kind: CourtDocumentPieceKind`, `outline_index: Integer`
- **Métodos / factory:** `create(title: Text, page_start: Integer, kind: CourtDocumentPieceKind, outline_index: Integer) -> CourtDocumentOutlineItem` — preserva a posição do item no outline bruto para cálculo determinístico do teto do range.

- **Localização:** `src/animus/core/storage/domain/structures/court_document_outline.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `items: list[CourtDocumentOutlineItem]`
- **Métodos / factory:** `create_from_pdf_outline_items(pdf_outline_items: list[PdfOutlineItem]) -> CourtDocumentOutline` — classifica os itens relevantes por string matching, preserva ordem e valida presença de sentença e apelação; lança `InsufficientCourtDocumentError` se faltar peça obrigatória.
- **Métodos / factory:** `find_sentencas() -> list[CourtDocumentOutlineItem]` — retorna sentenças ordenadas por `page_start`.
- **Métodos / factory:** `find_apelacoes() -> list[CourtDocumentOutlineItem]` — retorna apelações ordenadas por `page_start`, preferindo títulos com `apelação em pdf` quando existirem.
- **Métodos / factory:** `find_contrarrazoes() -> list[CourtDocumentOutlineItem]` — retorna contrarrazões ordenadas por `page_start`.
- **Métodos / factory:** `has_required_pieces() -> bool` — retorna `True` quando há pelo menos uma sentença e uma apelação.
- **Métodos / factory:** `_classify(title: Text) -> CourtDocumentPieceKind | None` — aplica as regras de matching descritas nesta spec.

- **Localização:** `src/animus/core/storage/domain/structures/extracted_court_document_pieces.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `sentenca: Text`, `apelação: Text`, `contrarrazoes: Text | None`
- **Métodos / factory:** `create(sentenca: Text, apelação: Text, contrarrazoes: Text | None = None) -> ExtractedCourtDocumentPieces` — cria o resultado da extração após validação feita por `CourtDocumentOutline`.

## Camada Core (Erros de Domínio)

- **Localização:** `src/animus/core/storage/domain/errors/court_document_index_not_found_error.py` (**novo arquivo**)
- **Classe base:** `AppError`
- **Motivo:** levantar quando `PdfProvider.extract_outline(...)` retornar lista vazia ou sem destinos utilizáveis.

- **Localização:** `src/animus/core/storage/domain/errors/insufficient_court_document_error.py` (**novo arquivo**)
- **Classe base:** `AppError`
- **Motivo:** levantar quando o outline não contiver pelo menos uma sentença e uma apelação classificáveis.

- **Localização:** `src/animus/core/storage/domain/errors/__init__.py` (**novo arquivo**)
- **Classe base:** Não aplicável.
- **Motivo:** exportar `CourtDocumentIndexNotFoundError` e `InsufficientCourtDocumentError` como API pública do domínio de storage.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/storage/use_cases/extract_court_document_pieces_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `PdfProvider`
- **Método principal:** `execute(pdf_file: FileDto) -> ExtractedCourtDocumentPieces` — extrai sentença, apelação e contrarrazões opcionais de um PDF a partir do outline.
- **Métodos:** `__init__(pdf_provider: PdfProvider) -> None` — armazena o port de PDF.
- **Métodos:** `_to_file(pdf_file: FileDto) -> File` — converte a entrada pública do use case para a structure exigida pelo `PdfProvider`.
- **Métodos:** `_extract_many(pdf_file: File, pieces: list[CourtDocumentOutlineItem], pdf_outline_items: list[PdfOutlineItem], total_pages: Integer) -> Text` — extrai e concatena múltiplas ocorrências em ordem cronológica.
- **Métodos:** `_find_ceiling(item: CourtDocumentOutlineItem, pdf_outline_items: list[PdfOutlineItem], total_pages: Integer) -> Integer` — calcula `page_end` como a página anterior ao próximo item bruto do outline; para o último item, retorna `total_pages`.
- **Fluxo resumido:** converter `FileDto` para `File`; chamar `PdfProvider.extract_outline(file)`; se vazio, lançar `CourtDocumentIndexNotFoundError`; criar `CourtDocumentOutline`; contar páginas; extrair ranges de sentenças, apelações e contrarrazões; retornar `ExtractedCourtDocumentPieces`.

## Migrações Alembic

**Não aplicável.** A entrega não cria tabela nem altera schema; `AnalysisModel.status` é `String` e aceita os novos valores sem migration.

# 6. O que deve ser modificado?

## Core / Storage

- **Arquivo:** `src/animus/core/storage/interfaces/pdf_provider.py`
- **Mudança:** adicionar `extract_outline(pdf_file: File) -> list[PdfOutlineItem]` ao `Protocol` e importar `PdfOutlineItem`.
- **Justificativa:** o use case precisa ler o outline via port do `core`, sem conhecer `pypdf` ou detalhes do provider concreto.

- **Arquivo:** `src/animus/core/storage/domain/structures/__init__.py`
- **Mudança:** exportar `CourtDocumentPieceKind`, `PdfOutlineItem`, `CourtDocumentOutlineItem`, `CourtDocumentOutline` e `ExtractedCourtDocumentPieces`.
- **Justificativa:** manter os novos tipos acessíveis pelo padrão público do módulo de structures.

- **Arquivo:** `src/animus/core/storage/use_cases/__init__.py`
- **Mudança:** exportar `ExtractCourtDocumentPiecesUseCase`.
- **Justificativa:** manter o padrão de imports agregados de use cases do contexto `storage`.

## Core / Intake

- **Arquivo:** `src/animus/core/intake/domain/structures/second_instance_analysis_status.py`
- **Mudança:** adicionar `EXTRACTING_COURT_DOCUMENT_PIECES` e `COURT_DOCUMENT_PIECES_NOT_FOUND` em `SecondInstanceAnalysisStatusValue`, adicionar factories `create_as_extracting_court_document_pieces() -> SecondInstanceAnalysisStatus` e `create_as_court_document_pieces_not_found() -> SecondInstanceAnalysisStatus`, e incluir `EXTRACTING_COURT_DOCUMENT_PIECES` em `get_processing_statuses()`.
- **Justificativa:** o fluxo deixa de extrair petição por LLM e passa a extrair peças processuais por outline; aborts esperados precisam de status específico diferente de `FAILED` e de `PETITION_NOT_FOUND`.

- **Arquivo:** `src/animus/core/intake/use_cases/trigger_second_instance_case_summarization_use_case.py`
- **Mudança:** substituir `SecondInstanceAnalysisStatus.create_as_extracting_petition()` por `SecondInstanceAnalysisStatus.create_as_extracting_court_document_pieces()`.
- **Justificativa:** o status inicial do job deve refletir o processamento real desta entrega.

## Providers

- **Arquivo:** `src/animus/providers/storage/document/pdf/pypdf_pdf_provider.py`
- **Mudança:** implementar `extract_outline(pdf_file: File) -> list[PdfOutlineItem]` usando `PdfReader(BytesIO(pdf_file.value)).outline` e `reader.get_destination_page_number(destination)`.
- **Justificativa:** `pypdf` expõe bookmarks via `reader.outline`; `get_destination_page_number(...)` retorna índice base 0, então o provider deve converter para página base 1 antes de criar `PdfOutlineItem`.
- **Mudança:** achatar listas aninhadas do outline em pré-ordem, ignorar destinos sem título ou sem página, e preservar a ordem final dos bookmarks retornados.
- **Justificativa:** PDFs jurídicos podem organizar peças em bookmarks aninhados; a extração deve continuar determinística e baseada na ordem do outline.

## AI

- **Arquivo:** `src/animus/ai/agno/workflows/intake/agno_summarize_second_instance_case_workflow.py`
- **Mudança:** ajustar `_build_summarization_input_step(...)` para descrever `document_content` como peças processuais extraídas dos autos, incluindo sentença, apelação e contrarrazões quando houver.
- **Justificativa:** o conteúdo de entrada deixa de ser apenas petição inicial; o prompt atual induz o agente a interpretar o material de forma incorreta.

## PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_second_instance_case_job.py`
- **Mudança:** remover do fluxo principal o uso de `AgnoExtractPetitionWorkflow`, `SqlalchemyExtractedPetitionsRepository` e `CreateExtractedPetitionUseCase`.
- **Justificativa:** a identificação de peças passa a ser determinística por outline e não deve usar cache de páginas de petição.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_second_instance_case_job.py`
- **Mudança:** instanciar `ExtractCourtDocumentPiecesUseCase(pdf_provider)` e chamar `execute(pdf_file=pdf_file.dto)` após baixar o arquivo pelo `GcsFileStorageProvider`.
- **Justificativa:** o use case recebe `FileDto`, enquanto o `PdfProvider` permanece recebendo `File` internamente conforme contrato existente.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_second_instance_case_job.py`
- **Mudança:** montar `document_content: Text` com cabeçalhos estáveis para `sentenca`, `apelação` e `contrarrazoes` quando existirem, e passar esse valor para `AgnoSummarizeSecondInstanceCaseWorkflow.run(...)`.
- **Justificativa:** o workflow precisa receber um texto único, mas com separação explícita entre peças para reduzir ambiguidade no prompt.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_second_instance_case_job.py`
- **Mudança:** capturar `CourtDocumentIndexNotFoundError` e `InsufficientCourtDocumentError`, marcar a análise como `COURT_DOCUMENT_PIECES_NOT_FOUND`, executar `session.commit()` e encerrar sem publicar `CaseSummaryFinishedEvent`.
- **Justificativa:** outline ausente e peças obrigatórias ausentes são aborts funcionais esperados, não sucesso parcial nem falha técnica genérica.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_second_instance_case_job.py`
- **Mudança:** adicionar métodos `_mark_court_document_pieces_as_not_found(payload: _Payload) -> None` e `_mark_court_document_pieces_as_not_found_sync(payload: _Payload) -> None` seguindo o padrão atual de `_mark_petition_as_not_found(...)`.
- **Justificativa:** manter o padrão de execução assíncrona com `run_in_executor` e atualização de status em sessão SQLAlchemy própria.

## Database / Seeders

**Não aplicável.** Não há alteração em models, mappers, repositories, seeders ou paths persistidos; o fluxo continua consumindo `analysis_documents.file_path` já existente.

# 7. O que deve ser removido?

**Não aplicável.** `AgnoExtractPetitionWorkflow`, `ExtractedPetition`, `ExtractedPetitionsRepository` e a tabela relacionada não devem ser removidos nesta entrega; uma limpeza desses componentes deve ser tratada em refatoração separada se não houver outros consumidores.

# 8. Decisões Técnicas e Trade-offs

| Decisão | Alternativas consideradas | Motivo da escolha | Impactos / trade-offs |
|---|---|---|---|
| O use case recebe `FileDto`, mas o `PdfProvider` continua recebendo `File`. | Usar `File` ponta a ponta ou alterar `PdfProvider` para receber `FileDto`. | Decisão confirmada durante a elaboração da spec; preserva contratos existentes do provider e atende o contrato solicitado no Jira para o use case. | O use case precisa converter `FileDto` para `File` antes de chamar o provider. |
| Usar outline nativo do PDF como única fonte de ranges. | Manter `AgnoExtractPetitionWorkflow` com sliding window ou criar fallback por texto sem outline. | O Jira exige extração determinística sem LLM e sem sliding window. | PDFs sem outline utilizável abortam o fluxo com status específico. |
| Criar `COURT_DOCUMENT_PIECES_NOT_FOUND` em vez de reutilizar `PETITION_NOT_FOUND` ou `FAILED`. | Reutilizar `PETITION_NOT_FOUND`; marcar todo abort como `FAILED`. | Decisão confirmada durante a elaboração da spec; sentença/apelação não são petição e abort funcional não deve se misturar com falha técnica. | O app precisa reconhecer novo valor de status para segunda instância. |
| Adicionar `EXTRACTING_COURT_DOCUMENT_PIECES` como status de processamento. | Manter `EXTRACTING_PETITION` durante a extração. | O fluxo processado pelo job muda de petição inicial para peças processuais. | Há novo valor observável em `GET /status`; `EXTRACTING_PETITION` permanece no enum para compatibilidade com dados ou fluxos legados. |
| Não persistir cache das peças extraídas. | Criar tabela de cache ou reaproveitar `extracted_petitions`. | A extração por outline é determinística e barata o suficiente para reexecução; as peças extraídas podem ser extensas e não há requisito de leitura posterior. | Reprocessamentos relerão o PDF, mas evitam migration e persistência de texto jurídico sensível adicional. |
| Manter estruturas de extração em `core/storage`. | Criar os tipos em `core/intake`. | A leitura/classificação de peças de PDF é um fluxo de documento/storage e não depende de HTTP, DB, Inngest ou AI. | `core/intake` só conhece os efeitos via status e job; o processamento documental fica isolado. |
| Preferir títulos com `apelação em pdf` quando existirem. | Concatenar todas as entradas de apelação ou escolher a primeira entrada genérica. | O Jira explicita a preferência por `Apelação em PDF`. | Se houver mais de uma entrada preferencial, todas devem ser concatenadas em ordem de página. |
| Não remover o pipeline legado de extração de petição nesta tarefa. | Remover workflow, repository, model e migration de `extracted_petitions`. | Remoção exigiria análise de consumidores e possível cleanup de dados fora do recorte da task. | Código legado pode ficar sem uso neste fluxo até uma refatoração dedicada. |

# 9. Diagramas e Referências

- **Fluxo de dados:**

```text
HTTP Request
  -> Middleware
  -> IntakeRouter / AnalysesRouter
  -> TriggerSecondInstanceCaseSummarizationController
  -> IntakePipe.verify_analysis_by_account_from_request(...)
  -> DatabasePipe / PubSubPipe
  -> TriggerSecondInstanceCaseSummarizationUseCase
  -> AnalysisDocumentsRepository.find_by_analysis_id(...)
  -> AnalysesRepository.find_by_id(...)
  -> Analysis.set_status(EXTRACTING_COURT_DOCUMENT_PIECES)
  -> AnalysesRepository.replace(...)
  -> Broker.publish(SecondInstanceCaseSummarizationTriggeredEvent)
  -> 202 Accepted
```

- **Fluxo assíncrono:**

```text
SecondInstanceCaseSummarizationTriggeredEvent(analysis_id)
  -> SummarizeSecondInstanceCaseJob
  -> normalize_payload
  -> SqlalchemyAnalysisDocumentsRepository.find_by_analysis_id(...)
  -> GcsFileStorageProvider.get_file(document.file_path) -> File
  -> ExtractCourtDocumentPiecesUseCase.execute(pdf_file=File.dto)
      -> _to_file(FileDto) -> File
      -> PdfProvider.extract_outline(File) -> list[PdfOutlineItem]
      -> CourtDocumentOutline.create_from_pdf_outline_items(pdf_outline_items)
      -> PdfProvider.count_pages(File)
      -> PdfProvider.extract_pages(File, page_start, page_end)
      -> ExtractedCourtDocumentPieces(sentenca, apelação, contrarrazoes?)
  -> Text.create(document_content com cabeçalhos por peça)
  -> UpdateAnalysisStatusUseCase(..., ANALYZING_CASE)
  -> AgnoSummarizeSecondInstanceCaseWorkflow.run(analysis_id, document_content)
  -> CreateCaseSummaryUseCase.execute(...)
  -> session.commit()
  -> InngestBroker.publish(CaseSummaryFinishedEvent)
```

- **Fluxo de abort por domínio:**

```text
PdfProvider.extract_outline(File) -> []
  -> CourtDocumentIndexNotFoundError
  -> SummarizeSecondInstanceCaseJob._mark_court_document_pieces_as_not_found(...)
  -> UpdateAnalysisStatusUseCase(..., COURT_DOCUMENT_PIECES_NOT_FOUND)
  -> session.commit()
  -> encerra sem CaseSummaryFinishedEvent
```

```text
CourtDocumentOutline.create_from_pdf_outline_items(pdf_outline_items)
  -> sentença ou apelação ausente
  -> InsufficientCourtDocumentError
  -> SummarizeSecondInstanceCaseJob._mark_court_document_pieces_as_not_found(...)
  -> UpdateAnalysisStatusUseCase(..., COURT_DOCUMENT_PIECES_NOT_FOUND)
  -> session.commit()
  -> encerra sem CaseSummaryFinishedEvent
```

- **Referências:**

- `src/animus/core/storage/interfaces/pdf_provider.py` — port a estender com `extract_outline(...)`.
- `src/animus/providers/storage/document/pdf/pypdf_pdf_provider.py` — adapter concreto a estender usando `pypdf`.
- `src/animus/core/storage/domain/structures/file.py` — structure exigida pelo `PdfProvider`.
- `src/animus/core/storage/domain/structures/dtos/file_dto.py` — DTO de entrada do novo use case.
- `src/animus/core/storage/use_cases/get_document_content_use_case.py` — referência de use case de storage com providers injetados.
- `src/animus/pubsub/inngest/jobs/intake/summarize_second_instance_case_job.py` — job que será alterado para consumir a extração determinística.
- `src/animus/ai/agno/workflows/intake/agno_summarize_second_instance_case_workflow.py` — consumidor do `document_content` a ajustar.
- `src/animus/ai/agno/workflows/intake/agno_extract_petition_workflow.py` — implementação legada que deixa de ser usada neste fluxo.
- `src/animus/core/intake/domain/structures/second_instance_analysis_status.py` — enum/structure a estender com novos status.
- `src/animus/core/intake/use_cases/trigger_second_instance_case_summarization_use_case.py` — ponto que define o status inicial do processamento.
- `src/animus/database/sqlalchemy/models/intake/analysis_model.py` — confirmação de que `status` é `String` e não exige migration para novos valores.
- Documentação `pypdf` consultada via Context7 — `reader.outline` representa bookmarks e `get_destination_page_number(...)` retorna página base 0.
- `https://joaogoliveiragarcia.atlassian.net/wiki/x/AwBXAQ` — glossário jurídico que fundamenta a seleção de `Sentença`, `Apelação` e `Contrarrazões` como peças de entrada para segunda instância.

# 10. Pendências / Dúvidas

**Sem pendências.** As decisões críticas sobre contrato `FileDto`/`File` e criação de novos status foram confirmadas durante a elaboração desta spec.

# 11. Restrições

- O `core` não deve importar `pypdf`, `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest`, Agno ou qualquer detalhe de infraestrutura.
- `ExtractCourtDocumentPiecesUseCase.execute(...)` deve receber `FileDto`; chamadas ao `PdfProvider` dentro do use case devem usar `File`.
- `PdfProvider.extract_outline(...)`, `count_pages(...)` e `extract_pages(...)` devem receber `File`, preservando o contrato existente do provider.
- A extração deve ser determinística por outline; não adicionar fallback por LLM, OCR ou sliding window nesta entrega.
- Não criar migration Alembic nem persistir conteúdo das peças extraídas.
- Não incluir testes automatizados nesta spec.
- Todos os novos arquivos citados estão explicitamente marcados como **novo arquivo**; todos os demais caminhos citados existem no projeto.
- O job deve publicar `CaseSummaryFinishedEvent` somente após a sumarização persistir com sucesso.
- O job não deve publicar evento de conclusão quando o status final for `COURT_DOCUMENT_PIECES_NOT_FOUND` ou `FAILED`.
- Schemas `*Body` de entrada não se aplicam porque nenhum endpoint HTTP novo será criado.
