---
title: Seed do dataset de treino de precedentes da analise
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AYAMAQ
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-63
status: open
last_updated_at: 2026-04-20
---

# 1. Objetivo

Implementar um job tecnico de `Inngest` que percorre as peticoes da Xertica ja armazenadas em `GCS`, cria uma `Analysis` e uma `Petition` para cada arquivo, executa o pipeline existente de resumo e busca de precedentes com `K=20` e sem sintese textual, classifica automaticamente a aplicabilidade desses precedentes via `Agno` + `GPT-4o`, persiste apenas os labels de alta confianca e materializa linhas de dataset exportadas em `parquet` para alimentar o treino do modelo de `applicability score`, sem alterar o contrato HTTP publico do fluxo de precedentes.

---

# 2. Escopo

## 2.1 In-scope

- Criar o `SeedAnalysesPrecedentsDatasetJob` em `Inngest` para processamento em lote das peticoes de `intake/xertica/petitions/`.
- Resolver a conta tecnica existente pelo e-mail `animus.ctrlaltdel@gmail.com` antes de criar as `Analysis` do lote.
- Reutilizar os fluxos existentes de criacao de `Analysis`, criacao de `Petition`, leitura do documento, resumo da peticao e busca de precedentes.
- Permitir que a busca interna do job persista `20` `AnalysisPrecedent` por analise, sem ampliar o limite do endpoint publico.
- Criar o workflow de classificacao de aplicabilidade dos precedentes da analise.
- Persistir `AnalysisPrecedentApplicabilityFeedback` apenas quando a classificacao retornar `confidence = high`.
- Persistir `AnalysisPrecedentDatasetRow` derivado de cada feedback salvo.
- Exportar as linhas geradas no lote atual para `intake/datasets/analysis-precedents/{ulid}-{date}.parquet`.
- Tornar o job seguro para reexecucao, evitando recriar processamento para o mesmo `document_file_path` ja semeado.

## 2.2 Out-of-scope

- Expor endpoint HTTP, `router` ou `controller` para disparar o seed do dataset.
- Alterar a UX do app de busca de precedentes ou o PRD do RF-03.
- Persistir `synthesis` dos precedentes no fluxo de dataset.
- Alterar a faixa publica de `limit` do endpoint `POST /intake/analyses/{analysis_id}/precedents/search`.
- Treinar o modelo de ML, versionar artefatos de treino ou publicar modelo em producao.
- Criar conta nova automaticamente para a Xertica; a spec assume que a conta com e-mail `animus.ctrlaltdel@gmail.com` ja existe.

---

# 3. Requisitos

## 3.1 Funcionais

- O job deve consumir os arquivos `*.pdf` de `intake/xertica/petitions/` no `GCS`.
- Para cada arquivo ainda nao processado, o job deve criar uma nova `Analysis` vinculada a conta resolvida por e-mail.
- Para cada `Analysis` criada, o job deve criar uma `Petition` apontando para o `document_file_path` ja existente no bucket.
- O job deve extrair o conteudo do PDF via `GetDocumentContentUseCase` e gerar `PetitionSummary` pelo workflow atual de resumo.
- O job deve executar a busca de precedentes usando o pipeline atual de embeddings e `Qdrant`, retornando `20` candidatos persistidos por analise.
- O job nao deve gerar `synthesis` dos precedentes nesse fluxo; a persistencia deve ocorrer com `synthesis=None`.
- O workflow de classificacao deve receber o resumo da peticao e a lista de `AnalysisPrecedent` persistidos da analise.
- O workflow deve executar os steps `BUILD_CLASSIFICATION_INPUT` -> `CLASSIFY_PRECEDENTS_APPLICABILITY` -> `CREATE_CLASSIFICATIONS`.
- A saida do agente deve incluir, por precedente, o nivel de aplicabilidade e um `confidence` textual.
- Apenas classificacoes com `confidence = high` devem gerar `AnalysisPrecedentApplicabilityFeedback` com `is_from_human=False`.
- Para cada feedback salvo, deve ser criada uma `AnalysisPrecedentDatasetRow` com os atributos necessarios para treino.
- Ao final do lote, o job deve exportar as linhas geradas no processamento atual para `intake/datasets/analysis-precedents/{ulid}-{date}.parquet`.
- Se um `document_file_path` ja tiver sido processado anteriormente, o job deve pular o arquivo e seguir para o proximo.

## 3.2 Nao funcionais

- **Performance:** o job deve reutilizar o fluxo existente de busca; o aumento de `K` para `20` deve existir apenas no caminho interno do seed, sem impactar o endpoint HTTP.
- **Seguranca:** nao deve haver nova superficie HTTP; o acesso continua restrito ao bucket configurado e a uma conta interna existente do sistema.
- **Idempotencia:** reexecucoes do job nao devem recriar `Analysis`/`Petition` para o mesmo `document_file_path`; feedbacks e dataset rows devem usar a chave natural `analysis_id + precedent_id` para permitir `replace` sem duplicacao.
- **Resiliencia:** falha ao resumir, buscar, classificar ou exportar deve falhar o lote com erro explicito no `Inngest`, preservando o rastreamento por step.
- **Observabilidade:** o job deve usar `context.step.run(...)` por etapa relevante e por arquivo processado, com nomes deterministas e legiveis.
- **Compatibilidade retroativa:** nenhum contrato HTTP existente deve mudar; a busca publica continua com validacao `5..10` e padrao `10`.

---

# 4. O que ja existe?

## Core (Intake)

- **`CreateAnalysisUseCase`** (`src/animus/core/intake/use_cases/create_analysis_use_case.py`) - cria uma `Analysis` com nome gerado e `status=WAITING_PETITION`.
- **`CreatePetitionUseCase`** (`src/animus/core/intake/use_cases/create_petition_use_case.py`) - cria a `Petition`, atualiza o status da analise e trata substituicao de peticao.
- **`CreatePetitionSummaryUseCase`** (`src/animus/core/intake/use_cases/create_petition_summary_use_case.py`) - persiste o resumo e move a analise para `PETITION_ANALYZED`.
- **`SearchAnalysisPrecedentsUseCase`** (`src/animus/core/intake/use_cases/search_analysis_precedents_use_case.py`) - executa embeddings, busca vetorial, deduplicacao, score e ordenacao dos precedentes.
- **`CreateAnalysisPrecedentsUseCase`** (`src/animus/core/intake/use_cases/create_analysis_precedents_use_case.py`) - persiste os `AnalysisPrecedent` e atualiza a analise para `WAITING_PRECEDENT_CHOISE`; ja suporta `synthesis_output=None`.
- **`AnalysisPrecedent`** (`src/animus/core/intake/domain/structures/analysis_precedent.py`) - ja carrega `similarity_score`, `thesis_similarity_score`, `enunciation_similarity_score`, `total_search_hits`, `similarity_rank` e `applicability_level`.
- **`AnalysisPrecedentApplicabilityLevel`** (`src/animus/core/intake/domain/structures/analysis_precedent_applicability_level.py`) - encapsula a classificacao ordinal `NOT_APPLICABLE | POSSIBLY_APPLICABLE | APPLICABLE`.
- **`AnalysisPrecedentApplicabilityFeedback`** (`src/animus/core/intake/domain/structures/analysis_precedent_applicability_feedback.py`) - estrutura existente, mas hoje modelada com `analysis_precedent_id`, ainda sem persistencia ou uso.
- **`AnalysisPrecedentDatasetRow`** (`src/animus/core/intake/domain/structures/analysis_precedent_dataset_row.py`) - estrutura existente para dataset, tambem ainda sem persistencia ou uso.
- **`PetitionsRepository`** (`src/animus/core/intake/interfaces/petitions_repository.py`) - contrato atual de leitura/escrita de `Petition`; ainda nao possui busca por `document_file_path`.
- **`PetitionSummariesRepository`** (`src/animus/core/intake/interfaces/petition_summaries_repository.py`) - permite recuperar `PetitionSummary` por `petition_id` e `analysis_id`.
- **`AnalysisPrecedentsRepository`** (`src/animus/core/intake/interfaces/analysis_precedents_repository.py`) - persiste e lista precedentes da analise.
- **`PrecedentsEmbeddingsRepository`** (`src/animus/core/intake/interfaces/precedents_embeddings_repository.py`) - contrato de busca vetorial com filtros e `limit`.
- **`SynthesizeAnalysisPrecedentsWorkflow`** (`src/animus/core/intake/interfaces/synthesize_analysis_precedents_workflow.py`) - referencia de workflow de `Agno` que busca dados, usa agente e persiste no step final.

## Core (Auth)

- **`AccountsRepository`** (`src/animus/core/auth/interfaces/accounts_repository.py`) - ja expoe `find_by_email(email: Email) -> Account | None`.
- **`AccountNotFoundError`** (`src/animus/core/auth/domain/errors/account_not_found_error.py`) - erro existente para conta inexistente.

## Database

- **`AnalysisPrecedentModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_precedent_model.py`) - tabela `analysis_precedents` ja contem `similarity_score`, `thesis_similarity_score`, `enunciation_similarity_score`, `total_search_hits`, `similarity_rank` e `applicability_level`.
- **`SqlalchemyAnalysisPrecedentsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analysis_precedents_repository.py`) - referencia de persistencia dos precedentes da analise.
- **`SqlalchemyPetitionsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petitions_repository.py`) - repository atual de `Petition`; faltando busca por `document_file_path`.
- **`SqlalchemyAccountsRepository`** (`src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`) - implementacao concreta de busca de conta por e-mail.
- **`SqlalchemyAnalisysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`) - persistencia da analise, inclusive `add_many(...)` e `replace(...)`.
- **`SqlalchemyPetitionSummariesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_summaries_repository.py`) - suporte de persistencia/leitura do resumo.
- **Migracoes existentes** (`migrations/versions/20260328_150000_create_analysis_precedents_table.py`, `migrations/versions/20260418_130000_add_analysis_precedent_scores_columns.py`) - base atual da tabela `analysis_precedents` e das colunas de score.

## AI

- **`AgnoSummarizePetitionWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_summarize_petition_workflow.py`) - referencia direta do padrao `Workflow` + `Team` + step executor final que persiste resultado.
- **`AgnoSynthesizeAnalysisPrecedentsWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_synthesize_analysis_precedents_workflow.py`) - referencia do fluxo que carrega `PetitionSummary`, monta prompt, usa agente e persiste via `UseCase`.
- **`IntakeTeam`** (`src/animus/ai/agno/teams/intake_team.py`) - team existente com agentes `GPT-4o` no contexto `intake`.
- **`AnalysisPrecedentsSynthesisOutput`** (`src/animus/ai/agno/outputs/intake/analysis_precedents_synthesis_output.py`) - referencia de output estruturado Pydantic para lista de itens.

## Providers / Storage

- **`GcsFileStorageProvider`** (`src/animus/providers/storage/file_storage/gcs/gcs_file_storage_provider.py`) - provider concreto de `GCS`, com `client`, `get_file(...)` e `upload_files(...)`.
- **`GetDocumentContentUseCase`** (`src/animus/core/storage/use_cases/get_document_content_use_case.py`) - leitura reutilizavel de PDF/DOCX a partir de `FileStorageProvider`.
- **`StorageSeeder`** (`src/animus/database/sqlalchemy/seeders/storage_seeder.py`) - referencia de acesso direto ao `client` do `GcsFileStorageProvider` para operacoes de bucket/prefixo.
- **`OpenAIPetitionSummaryEmbeddingsProvider`** (`src/animus/providers/intake/petition_summary_embeddings/openai/openai_petition_summary_embeddings_provider.py`) - provider atual de embeddings do resumo.

## PubSub

- **`SearchAnalysisPrecedentsJob`** (`src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`) - principal referencia de job multi-step do contexto `intake`, com mudanca de status e execucao de `UseCase`/workflow.
- **`SummarizePetitionJob`** (`src/animus/pubsub/inngest/jobs/intake/summarize_petition_job.py`) - referencia de job que reusa `GetDocumentContentUseCase` e workflow concreto de `Agno`.
- **`VectorizeAllPrecedentsJob`** (`src/animus/pubsub/inngest/jobs/intake/vectorize_all_precedents_job.py`) - referencia de processamento em lote com pagina e `step.run(...)` iterativo.
- **`InngestPubSub`** (`src/animus/pubsub/inngest/inngest_pubsub.py`) - composition root que registra os jobs `intake`.

## Lacunas identificadas

- Nao existe job para seed do dataset de treino.
- Nao existe workflow de classificacao de aplicabilidade dos precedentes.
- Nao existem tabelas, models, mappers e repositories para `feedbacks` e `dataset_rows`.
- As estruturas atuais de `feedback` e `dataset row` assumem `analysis_precedent_id`, mas `analysis_precedents` hoje usa chave primaria composta `analysis_id + precedent_id`.
- `PetitionsRepository` ainda nao permite localizar uma `Petition` pelo `document_file_path`, o que impede idempotencia natural do seed.
- O projeto ainda nao possui dependencia para gravar `parquet`.

---

# 5. O que deve ser criado?

## Camada Core (Interfaces / Ports)

- **Localizacao:** `src/animus/core/storage/interfaces/parquet_provider.py` (**novo arquivo**)
- **Metodos:**
- `write_analysis_precedents_dataset(rows: list[AnalysisPrecedentDatasetRowDto], local_file_path: FilePath) -> None` - materializa localmente um arquivo `.parquet` do dataset de precedentes em um caminho temporario do filesystem, sem fazer upload.

- **Localizacao:** `src/animus/core/intake/interfaces/classify_analysis_precedents_applicability_workflow.py` (**novo arquivo**)
- **Metodos:**
- `run(analysis_id: str, analysis_precedents: list[AnalysisPrecedentDto]) -> list[AnalysisPrecedentDatasetRowDto]` - classifica a aplicabilidade dos precedentes de uma analise, persiste feedbacks e dataset rows automaticos e retorna as linhas materializadas para exportacao.

- **Localizacao:** `src/animus/core/intake/interfaces/analysis_precedent_applicability_feedbacks_repository.py` (**novo arquivo**)
- **Metodos:**
- `find_by_analysis_id_and_precedent_id(analysis_id: Id, precedent_id: Id) -> AnalysisPrecedentApplicabilityFeedback | None` - localiza o feedback do precedente da analise pela chave natural.
- `add(feedback: AnalysisPrecedentApplicabilityFeedback) -> None` - persiste um feedback novo.
- `replace(feedback: AnalysisPrecedentApplicabilityFeedback) -> None` - substitui o feedback existente para a mesma chave natural.

- **Localizacao:** `src/animus/core/intake/interfaces/analysis_precedent_dataset_rows_repository.py` (**novo arquivo**)
- **Metodos:**
- `find_by_analysis_id_and_precedent_id(analysis_id: Id, precedent_id: Id) -> AnalysisPrecedentDatasetRow | None` - localiza a linha de dataset derivada para a mesma chave natural.
- `add(dataset_row: AnalysisPrecedentDatasetRow) -> None` - persiste uma linha nova do dataset.
- `replace(dataset_row: AnalysisPrecedentDatasetRow) -> None` - substitui a linha existente para a mesma chave natural.

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/intake/use_cases/create_analysis_precedent_applicability_feedback_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalysisPrecedentApplicabilityFeedbacksRepository`
- **Metodo principal:** `execute(analysis_id: str, precedent_id: str, applicability_level: int) -> AnalysisPrecedentApplicabilityFeedbackDto` - cria ou substitui o feedback automatico para um precedente da analise.
- **Fluxo resumido:** normaliza IDs -> monta `AnalysisPrecedentApplicabilityFeedback` com `created_at=now` -> `find_by...` -> `add(...)` ou `replace(...)` -> retorna DTO persistivel.

- **Localizacao:** `src/animus/core/intake/use_cases/create_analysis_precedent_dataset_row_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalysisPrecedentDatasetRowsRepository`
- **Metodo principal:** `execute(analysis_precedent: AnalysisPrecedentDto, feedback: AnalysisPrecedentApplicabilityFeedbackDto) -> AnalysisPrecedentDatasetRowDto` - cria ou substitui a linha de dataset derivada de um precedente classificado.
- **Fluxo resumido:** combina metadados do `AnalysisPrecedentDto` com o label do feedback -> monta `AnalysisPrecedentDatasetRow` -> `find_by...` -> `add(...)` ou `replace(...)` -> retorna DTO para exportacao.

## Camada Database (Models SQLAlchemy)

- **Localizacao:** `src/animus/database/sqlalchemy/models/intake/analysis_precedent_applicability_feedback_model.py` (**novo arquivo**)
- **Tabela:** `analysis_precedent_applicability_feedbacks`
- **Colunas:**
- `analysis_id` - `String(26)`, `nullable=False`, parte da chave primaria e parte da `ForeignKeyConstraint` composta para `analysis_precedents`
- `precedent_id` - `String(26)`, `nullable=False`, parte da chave primaria e parte da `ForeignKeyConstraint` composta para `analysis_precedents`
- `applicability_level` - `Integer`, `nullable=False`
- `created_at` / `updated_at` - herdados de `Model`
- **Relacionamentos:** referencia composta para `AnalysisPrecedentModel`

- **Localizacao:** `src/animus/database/sqlalchemy/models/intake/analysis_precedent_dataset_row_model.py` (**novo arquivo**)
- **Tabela:** `analysis_precedent_dataset_rows`
- **Colunas:**
- `analysis_id` - `String(26)`, `nullable=False`, parte da chave primaria
- `precedent_id` - `String(26)`, `nullable=False`, parte da chave primaria
- `applicability_level` - `Integer`, `nullable=False`
- `thesis_similarity_score` - `Float`, `nullable=False`
- `enunciation_similarity_score` - `Float`, `nullable=False`
- `total_search_hits` - `Integer`, `nullable=False`
- `similarity_rank` - `Integer`, `nullable=False`
- `precedent_court` - `String`, `nullable=False`
- `precedent_kind` - `String`, `nullable=False`
- `precedent_number` - `Integer`, `nullable=False`
- `precedent_status` - `String`, `nullable=False`
- `last_updated_in_pangea_at` - `DateTime(timezone=True)`, `nullable=False`
- `created_at` / `updated_at` - herdados de `Model`
- **Relacionamentos:** referencia composta para `analysis_precedent_applicability_feedbacks` usando `analysis_id + precedent_id`

## Camada Database (Mappers)

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/intake/analysis_precedent_applicability_feedback_mapper.py` (**novo arquivo**)
- **Metodos:**
- `to_entity(model: AnalysisPrecedentApplicabilityFeedbackModel) -> AnalysisPrecedentApplicabilityFeedback` - reconstrui o feedback a partir do model ORM.
- `to_model(entity: AnalysisPrecedentApplicabilityFeedback) -> AnalysisPrecedentApplicabilityFeedbackModel` - converte o feedback para persistencia.

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/intake/analysis_precedent_dataset_row_mapper.py` (**novo arquivo**)
- **Metodos:**
- `to_entity(model: AnalysisPrecedentDatasetRowModel) -> AnalysisPrecedentDatasetRow` - reconstrui a linha do dataset a partir do model ORM.
- `to_model(entity: AnalysisPrecedentDatasetRow) -> AnalysisPrecedentDatasetRowModel` - converte a linha do dataset para persistencia.

## Camada Database (Repositorios)

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analysis_precedent_applicability_feedbacks_repository.py` (**novo arquivo**)
- **Interface implementada:** `AnalysisPrecedentApplicabilityFeedbacksRepository`
- **Dependencias:** `Session` SQLAlchemy
- **Metodos:**
- `find_by_analysis_id_and_precedent_id(...) -> AnalysisPrecedentApplicabilityFeedback | None` - busca pela chave natural do feedback.
- `add(feedback: AnalysisPrecedentApplicabilityFeedback) -> None` - persiste um feedback novo.
- `replace(feedback: AnalysisPrecedentApplicabilityFeedback) -> None` - atualiza `applicability_level` e `created_at` do feedback existente.

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analysis_precedent_dataset_rows_repository.py` (**novo arquivo**)
- **Interface implementada:** `AnalysisPrecedentDatasetRowsRepository`
- **Dependencias:** `Session` SQLAlchemy
- **Metodos:**
- `find_by_analysis_id_and_precedent_id(...) -> AnalysisPrecedentDatasetRow | None` - busca a linha derivada pela mesma chave natural.
- `add(dataset_row: AnalysisPrecedentDatasetRow) -> None` - persiste uma nova linha do dataset.
- `replace(dataset_row: AnalysisPrecedentDatasetRow) -> None` - atualiza a linha existente mantendo a mesma chave natural.

## Camada AI (Outputs Estruturados)

- **Localizacao:** `src/animus/ai/agno/outputs/intake/analysis_precedents_applicability_classification_output.py` (**novo arquivo**)
- **Tipo:** `BaseModel`
- **Atributos:**
- `items: list[AnalysisPrecedentApplicabilityClassificationItemOutput]`
- `AnalysisPrecedentApplicabilityClassificationItemOutput.precedent_id: str`
- `AnalysisPrecedentApplicabilityClassificationItemOutput.applicability_level: int`
- `AnalysisPrecedentApplicabilityClassificationItemOutput.confidence: str`

## Camada AI (Workflows)

- **Localizacao:** `src/animus/ai/agno/workflows/intake/agno_classify_analysis_precedents_applicability_workflow.py` (**novo arquivo**)
- **Interface implementada:** `ClassifyAnalysisPrecedentsApplicabilityWorkflow`
- **Dependencias:** `PetitionSummariesRepository`, `CreateAnalysisPrecedentApplicabilityFeedbackUseCase`, `CreateAnalysisPrecedentDatasetRowUseCase`
- **Metodo principal:** `run(analysis_id: str, analysis_precedents: list[AnalysisPrecedentDto]) -> list[AnalysisPrecedentDatasetRowDto]` - classifica a aplicabilidade, filtra itens de alta confianca e persiste feedbacks/linhas de dataset.
- **Passos (`step.run`/workflow steps):**
- `BUILD_CLASSIFICATION_INPUT` - carrega o `PetitionSummary` da analise e monta o prompt estruturado.
- `CLASSIFY_PRECEDENTS_APPLICABILITY` - delega ao agente `GPT-4o` a classificacao de cada precedente.
- `CREATE_CLASSIFICATIONS` - filtra `confidence=high`, cria feedbacks automaticos e dataset rows, retornando a lista final exportavel.
- **Idempotencia:** a persistencia final usa `replace(...)` pela chave natural `analysis_id + precedent_id`.

## Camada PubSub (Jobs Inngest)

- **Localizacao:** `src/animus/pubsub/inngest/jobs/intake/seed_analyses_precedents_dataset_job.py` (**novo arquivo**)
- **Evento consumido:** `TriggerEvent(event='intake/seed-analyses-precedents-dataset.requested')` diretamente no job; nao cria `Event` de dominio no `core`, porque o disparo e operacional.
- **Dependencias:** `SqlalchemyAccountsRepository`, `SqlalchemyAnalisysesRepository`, `SqlalchemyPetitionsRepository`, `SqlalchemyPetitionSummariesRepository`, `SqlalchemyAnalysisPrecedentsRepository`, novos repositories de feedback/dataset row, `GcsFileStorageProvider`, `ParquetProvider`, `GetDocumentContentUseCase`, `AgnoSummarizePetitionWorkflow`, `SearchAnalysisPrecedentsUseCase`, `CreateAnalysisPrecedentsUseCase`, `AgnoClassifyAnalysisPrecedentsApplicabilityWorkflow`.
- **Passos (`step.run`):**
- `resolve_account` - resolve a conta pelo e-mail `animus.ctrlaltdel@gmail.com`.
- `list_petition_files` - lista os blobs `*.pdf` do prefixo `intake/xertica/petitions/`.
- `process_file_<n>` - para cada arquivo: verifica idempotencia por `document_file_path`, cria `Analysis`, cria `Petition`, resume a peticao, busca `20` precedentes, persiste precedentes sem sintese e classifica aplicabilidade.
- `export_dataset` - gera um `ULID`, monta dois caminhos distintos, `local_file_path` temporario e `bucket_file_path=intake/datasets/analysis-precedents/{ulid}-{date}.parquet`, delega a escrita local ao `ParquetProvider` e depois faz upload do arquivo temporario para o `GCS` no caminho final do bucket.
- **Idempotencia:** arquivos com `document_file_path` ja encontrado em `PetitionsRepository.find_by_document_file_path(...)` devem ser ignorados; feedbacks e dataset rows usam `replace` pela chave natural `analysis_id + precedent_id`.

## Camada Providers

- **Localizacao:** `src/animus/providers/storage/parquet/pyarrow_parquet_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `ParquetProvider`
- **Biblioteca/SDK utilizado:** `pyarrow`
- **Metodos:**
- `write_analysis_precedents_dataset(rows: list[AnalysisPrecedentDatasetRowDto], local_file_path: FilePath) -> None` - converte os DTOs do lote atual para tabela `pyarrow` e grava um arquivo `.parquet` temporario/local no filesystem; o upload continua sendo responsabilidade do job via `GcsFileStorageProvider` ou `client` equivalente.

## Migracoes Alembic

- **Localizacao:** `migrations/versions/`
- **Operacoes:** criar `analysis_precedent_applicability_feedbacks` e `analysis_precedent_dataset_rows` com FKs compostas para `analysis_precedents`; nao recriar colunas de score ja existentes em `analysis_precedents`.
- **Reversibilidade:** `downgrade` seguro com `drop_table(...)` das duas novas tabelas.

---

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/structures/analysis_precedent_applicability_feedback.py`
- **Mudanca:** substituir a referencia atual `analysis_precedent_id` por referencia composta baseada em `analysis_id` e `precedent_id`, mantendo `applicability_level` e `created_at`.
- **Justificativa:** a tabela `analysis_precedents` nao possui `id` proprio; a modelagem atual nao e persistivel com o schema real.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/analysis_precedent_applicability_feedback_dto.py`
- **Mudanca:** alinhar o DTO de feedback a mesma chave composta usada pela estrutura.
- **Justificativa:** manter contrato consistente entre dominio, repository e migration.

- **Arquivo:** `src/animus/core/intake/domain/structures/analysis_precedent_dataset_row.py`
- **Mudanca:** remover a dependencia de `analysis_precedent_id` e passar a materializar a linha a partir de `analysis_id + precedent_id`.
- **Justificativa:** a linha do dataset precisa refletir a chave natural do label persistido e nao um ID inexistente.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/analysis_precedent_dataset_dto.py`
- **Mudanca:** alinhar os campos do DTO de dataset row a chave composta e ao schema de exportacao.
- **Justificativa:** permitir persistencia e serializacao em `parquet` sem campo artificial.

- **Arquivo:** `src/animus/core/intake/interfaces/petitions_repository.py`
- **Mudanca:** adicionar `find_by_document_file_path(file_path: FilePath) -> Petition | None`.
- **Justificativa:** o seed precisa deduplicar arquivos ja processados para ser seguro em reexecucao.

- **Arquivo:** `src/animus/core/intake/use_cases/search_analysis_precedents_use_case.py`
- **Mudanca:** adicionar um parametro interno opcional de quantidade final retornada, por exemplo `results_limit: int | None = None`, mantendo o comportamento atual quando ausente.
- **Justificativa:** o job precisa persistir `20` precedentes sem ampliar a validacao publica `5..10` usada pelos endpoints.

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudanca:** exportar os novos ports criados para feedbacks, dataset rows e workflow de classificacao.
- **Justificativa:** manter o package de interfaces coerente com o novo dominio publico do contexto.

- **Arquivo:** `src/animus/core/storage/interfaces/__init__.py`
- **Mudanca:** exportar `ParquetProvider`.
- **Justificativa:** manter o package de interfaces de storage coerente com o novo adaptador de escrita.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudanca:** exportar os novos use cases de feedback e dataset row.
- **Justificativa:** manter o package de casos de uso coerente com os novos fluxos do contexto.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petitions_repository.py`
- **Mudanca:** implementar `find_by_document_file_path(...)` usando `PetitionModel.document_file_path`.
- **Justificativa:** fornecer a consulta de idempotencia exigida pelo job.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/__init__.py`
- **Mudanca:** expor os novos repositories concretos de feedback e dataset row.
- **Justificativa:** manter o package de repositories alinhado aos novos adaptadores.

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/__init__.py`
- **Mudanca:** expor os novos models ORM.
- **Justificativa:** manter o package de models consistente com o schema novo.

- **Arquivo:** `src/animus/database/sqlalchemy/mappers/intake/__init__.py`
- **Mudanca:** expor os novos mappers.
- **Justificativa:** manter o package de mappers consistente com os novos tipos persistidos.

## AI

- **Arquivo:** `src/animus/ai/agno/teams/intake_team.py`
- **Mudanca:** adicionar um novo agente, por exemplo `analysis_precedents_applicability_classifier_agent`, usando `GPT-4o` e output estruturado de classificacao.
- **Justificativa:** o time `intake` ja e o ponto padrao de composicao dos agentes juridicos do contexto.

## PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/__init__.py`
- **Mudanca:** exportar `SeedAnalysesPrecedentsDatasetJob`.
- **Justificativa:** manter o package de jobs `intake` consistente.

- **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
- **Mudanca:** registrar o novo job na lista de jobs `intake`.
- **Justificativa:** sem esse registro o handler nao sera exposto ao runtime do `Inngest`.

## Tooling

- **Arquivo:** `pyproject.toml`
- **Mudanca:** adicionar dependencia de escrita `parquet` via `pyarrow`.
- **Justificativa:** o projeto atualmente nao possui biblioteca para materializar o artefato exigido pelo ticket.

## Providers

- **Arquivo:** `src/animus/providers/storage/__init__.py`
- **Mudanca:** exportar `PyarrowParquetProvider`.
- **Justificativa:** manter o package de providers de storage coerente com a nova implementacao.

> Nao ha necessidade de alterar `controllers`, `routers`, `pipes` HTTP ou contratos REST existentes.

---

# 7. O que deve ser removido?

**Nao aplicavel**.

---

# 8. Decisoes Tecnicas e Trade-offs

## 8.1 Reusar o pipeline atual dentro do job, sem encadear jobs existentes

- **Decisao:** o `SeedAnalysesPrecedentsDatasetJob` deve chamar diretamente `CreateAnalysisUseCase`, `CreatePetitionUseCase`, `AgnoSummarizePetitionWorkflow`, `SearchAnalysisPrecedentsUseCase` e `CreateAnalysisPrecedentsUseCase`, em vez de publicar `PetitionSummaryRequestedEvent` e `AnalysisPrecedentsSearchRequestedEvent`.
- **Alternativas consideradas:** disparar os jobs existentes de resumo e busca; duplicar toda a logica no job de seed.
- **Motivo da escolha:** evita orquestracao assincrona aninhada, reduz latencia operacional e permite exportar o dataset ao final do mesmo lote.
- **Impactos / trade-offs:** o job fica mais longo e monta mais dependencias concretas, mas continua sem mover regra de negocio para a camada `pubsub`.

## 8.2 Manter a PK composta de `analysis_precedents`

- **Decisao:** nao adicionar `id` proprio em `analysis_precedents`; os novos feedbacks e dataset rows devem referenciar `analysis_id + precedent_id`.
- **Alternativas consideradas:** adicionar surrogate key em `analysis_precedents`; manter o campo `analysis_precedent_id` nas estruturas atuais.
- **Motivo da escolha:** e a menor mudanca correta frente ao schema ja em producao e evita migracao invasiva em uma tabela ja usada pelo fluxo publico.
- **Impactos / trade-offs:** as estruturas de feedback/dataset row precisam ser ajustadas, e os novos repositories passam a operar com chave natural composta.

## 8.3 Reusar as colunas de score ja existentes

- **Decisao:** usar `thesis_similarity_score`, `enunciation_similarity_score`, `total_search_hits` e `similarity_rank` como fonte do dataset, sem criar colunas novas como `thesis_max`, `enunciation_max` e `total_hits`.
- **Alternativas consideradas:** criar colunas duplicadas com nomes novos; renomear as colunas atuais.
- **Motivo da escolha:** a semantica necessaria ao treino ja esta disponivel no schema atual e a codebase inteira ja usa esses nomes.
- **Impactos / trade-offs:** o ticket fica adaptado ao vocabulário real do repositorio, e a spec precisa registrar explicitamente essa equivalencia.

## 8.4 Separar o limite interno `K=20` do contrato publico `5..10`

- **Decisao:** adicionar override interno no `SearchAnalysisPrecedentsUseCase` para a quantidade final retornada, sem alterar `AnalysisPrecedentsSearchFilters` nem o endpoint publico.
- **Alternativas consideradas:** ampliar a validacao global para `20`; duplicar o caso de uso de busca apenas para o seed.
- **Motivo da escolha:** preserva compatibilidade retroativa e evita um segundo algoritmo de scoring/deduplicacao.
- **Impactos / trade-offs:** o caso de uso ganha um caminho interno adicional, que deve ser documentado e usado apenas pelo job tecnico.

## 8.5 Persistir apenas labels de alta confianca

- **Decisao:** somente itens com `confidence = high` retornados pelo agente devem gerar `feedback` e `dataset row`.
- **Alternativas consideradas:** persistir todas as classificacoes com um campo de confianca; descartar todo o resultado se algum item vier com baixa confianca.
- **Motivo da escolha:** segue o criterio do ticket e reduz ruido no dataset de treino.
- **Impactos / trade-offs:** uma analise pode terminar com zero linhas de dataset mesmo tendo `20` precedentes persistidos; isso deve ser tratado como resultado valido, nao como erro.

## 8.6 Usar chave natural simples para labels do dataset

- **Decisao:** `AnalysisPrecedentApplicabilityFeedback` e `AnalysisPrecedentDatasetRow` devem usar apenas `analysis_id + precedent_id` como identificador unico.
- **Alternativas consideradas:** incluir `is_from_human` na chave primaria para suportar label automatico e humano em paralelo.
- **Motivo da escolha:** e o escopo explicitamente desejado para esta task e reduz a complexidade de schema, repositories e regras de substituicao.
- **Impactos / trade-offs:** o sistema passa a manter um unico label por precedente da analise; se no futuro houver revisao humana paralela, sera necessaria nova migracao/modelagem.

## 8.7 Resolver a conta tecnica por e-mail fixo existente

- **Decisao:** o job deve resolver a conta pelo e-mail `animus.ctrlaltdel@gmail.com` usando `AccountsRepository.find_by_email(...)`.
- **Alternativas consideradas:** receber `account_id` por configuracao; criar conta automaticamente; hardcode de `account_id` literal.
- **Motivo da escolha:** o dado operacional fornecido para a task e o e-mail da conta existente, e o repository ja suporta lookup por e-mail.
- **Impactos / trade-offs:** a execucao depende da existencia previa dessa conta em cada ambiente onde o job for rodado.

## 8.8 Gerar o arquivo via `ParquetProvider`

- **Decisao:** a serializacao do dataset para `.parquet` deve acontecer via `ParquetProvider`, e nao diretamente dentro do job.
- **Alternativas consideradas:** usar `pyarrow` diretamente no `SeedAnalysesPrecedentsDatasetJob`; usar `pandas`.
- **Motivo da escolha:** escrever `parquet` e detalhe de infraestrutura; isolar isso em um port/adaptador preserva a camada `pubsub` como orquestracao e segue o padrao do projeto para `PdfProvider`, `DocxProvider` e demais providers.
- **Impactos / trade-offs:** adiciona um port e um provider concreto a mais, mas evita acoplamento do job a `pyarrow.Table` e `write_table(...)`.

## 8.9 Exportar `parquet` com nome unico por execucao

- **Decisao:** cada execucao deve gerar `intake/datasets/analysis-precedents/{ulid}-{date}.parquet`.
- **Alternativas consideradas:** usar apenas `{date}.parquet`; sobrescrever o arquivo do mesmo dia.
- **Motivo da escolha:** evita colisao entre execucoes no mesmo dia e facilita rastrear o artefato produzido por cada run.
- **Impactos / trade-offs:** multiplos arquivos podem ser gerados no mesmo dia, exigindo criterio de consumo posterior fora do escopo desta task.

## 8.10 Separar caminho local temporario do caminho final no bucket

- **Decisao:** o fluxo deve trabalhar com dois caminhos distintos no `export_dataset`: um `local_file_path` temporario para a escrita do `.parquet` e um `bucket_file_path` final em `intake/datasets/analysis-precedents/{ulid}-{date}.parquet` para upload.
- **Alternativas consideradas:** fazer o `ParquetProvider` escrever diretamente no bucket; reutilizar o mesmo valor de `FilePath` para escrita local e remota.
- **Motivo da escolha:** a escrita com `pyarrow` acontece no filesystem local do processo, enquanto o artefato definitivo precisa existir como objeto remoto no `GCS`; explicitar os dois caminhos elimina ambiguidade de implementacao.
- **Impactos / trade-offs:** o job precisa coordenar a etapa adicional de upload e limpeza do arquivo temporario, mas o contrato do provider fica simples e focado em serializacao.

---

# 9. Diagramas e Referencias

## 9.1 Fluxo de dados

```text
Inngest TriggerEvent
  -> SeedAnalysesPrecedentsDatasetJob
  -> resolve Account by email (animus.ctrlaltdel@gmail.com)
  -> GcsFileStorageProvider.client.list_blobs(prefix='intake/xertica/petitions/')
  -> for each PDF not yet seeded:
       -> PetitionsRepository.find_by_document_file_path(file_path)
       -> CreateAnalysisUseCase.execute(account_id)
       -> CreatePetitionUseCase.execute(analysis_id, uploaded_at, document)
       -> GetDocumentContentUseCase.execute(file_path)
       -> AgnoSummarizePetitionWorkflow.run(petition_id, document_content)
       -> SearchAnalysisPrecedentsUseCase.execute(analysis_id, filters_dto, results_limit=20)
       -> CreateAnalysisPrecedentsUseCase.execute(..., synthesis_output=None)
       -> AgnoClassifyAnalysisPrecedentsApplicabilityWorkflow.run(analysis_id, analysis_precedents)
            -> CreateAnalysisPrecedentApplicabilityFeedbackUseCase.execute(...)
            -> CreateAnalysisPrecedentDatasetRowUseCase.execute(...)
  -> generate ULID + date
  -> build local_file_path=/tmp/.../{ulid}-{date}.parquet
  -> build bucket_file_path=intake/datasets/analysis-precedents/{ulid}-{date}.parquet
  -> ParquetProvider.write_analysis_precedents_dataset(rows, local_file_path)
  -> upload local_file_path to bucket_file_path
  -> remove local temp file
```

## 9.2 Fluxo assincrono

```text
Operator / Inngest CLI
  -> event: intake/seed-analyses-precedents-dataset.requested
  -> SeedAnalysesPrecedentsDatasetJob.handle
     -> step resolve_account
     -> step list_petition_files
     -> step process_file_1
     -> step process_file_2
     -> ...
     -> step export_dataset
```

## 9.3 Referencias

- `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`
- `src/animus/pubsub/inngest/jobs/intake/summarize_petition_job.py`
- `src/animus/pubsub/inngest/jobs/intake/vectorize_all_precedents_job.py`
- `src/animus/ai/agno/workflows/intake/agno_summarize_petition_workflow.py`
- `src/animus/ai/agno/workflows/intake/agno_synthesize_analysis_precedents_workflow.py`
- `src/animus/core/intake/use_cases/search_analysis_precedents_use_case.py`
- `src/animus/core/intake/use_cases/create_analysis_precedents_use_case.py`
- `src/animus/database/sqlalchemy/seeders/storage_seeder.py`

---

# 10. Pendencias / Duvidas

**Sem pendencias**.
