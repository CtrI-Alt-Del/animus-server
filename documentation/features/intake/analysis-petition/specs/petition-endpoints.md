---
title: Endpoints de peticoes e resumo da peticao
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/CID5
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-45
status: closed
last_updated_at: 2026-03-27
---

# 1. Objetivo

Entregar os endpoints `POST /intake/petitions` e `POST /intake/petitions/{petition_id}/summary` no `animus-server`, cobrindo a persistencia da `Petition`, a validacao de ownership da `Analysis`, a leitura segura do documento armazenado no GCS, a extracao de texto para `PDF` e `DOCX`, a geracao sincronica do resumo com `Agno` + `Gemini` e a persistencia do resultado em `petition_summaries`, sem mover regra de negocio para `controllers`, `pipes` ou adaptadores de infraestrutura.

---

# 2. Escopo

## 2.1 In-scope

- Criar o fluxo HTTP de cadastro de peticao em `POST /intake/petitions` com retorno de `PetitionDto`.
- Criar o fluxo HTTP de resumo em `POST /intake/petitions/{petition_id}/summary` com retorno de `PetitionSummaryDto`.
- Criar os `use_cases`, `ports`, `repositories`, `models`, `mappers`, `pipes`, `router` e providers diretamente necessarios para o fluxo de peticoes.
- Estender `storage` para baixar o arquivo e extrair texto por tipo de documento (`PDF` e `DOCX`).
- Implementar o `workflow` de AI sincrono com `Agno` + `Gemini`, com saida estruturada e persistencia do resumo.
- Ajustar exports publicos e wiring da aplicacao para expor o novo router de `intake`.

## 2.2 Out-of-scope

- O endpoint de signed URL de upload (`ANI-44`) e toda a superficie HTTP de `storage/upload`.
- OCR, leitura de imagens, suporte a documentos escaneados sem camada de texto e qualquer processamento multimodal.
- Busca de precedentes, embeddings, RAG e qualquer comportamento de `RF 03` alem da producao do resumo da peticao.
- Edicao manual do resumo, versionamento de resumos ou historico de reprocessamentos bem-sucedidos.
- Qualquer definicao completa de CRUD/listagem de `Analysis` ou de `Folder` alem do necessario para ownership check.

---

# 3. Requisitos

## 3.1 Funcionais

- `POST /intake/petitions` deve receber `analysis_id`, `uploaded_at` e `document { file_path, name }`, persistir a peticao e retornar `201` com `PetitionDto` contendo o `id` gerado.
- `POST /intake/petitions` deve validar que a `Analysis` informada pertence ao usuario autenticado antes de persistir a peticao.
- `POST /intake/petitions/{petition_id}/summary` deve validar ownership da peticao a partir da `Analysis` relacionada antes de acessar o documento no storage.
- O resumo deve ser gerado a partir do conteudo textual do documento armazenado, com suporte a arquivos `PDF` e `DOCX`.
- O `workflow` de AI deve retornar `PetitionSummaryDto { content, main_points }` e persistir o resumo associado a `petition_id`.
- O resumo deve refletir os elementos centrais da peticao descritos no PRD: fatos, fundamento juridico e pedido, sem impor campos fixos ao usuario da API.
- Falhas de leitura de arquivo corrompido ou ilegivel devem interromper o fluxo antes da chamada ao `workflow` de AI.
- O fluxo de resumo deve permanecer manual e sincrono: a analise so acontece quando o endpoint de `summary` e chamado.

## 3.2 Nao funcionais

- **Seguranca:** ambos os endpoints exigem autenticacao via `Bearer access token` e ownership check por `account_id`.
- **Compatibilidade retroativa:** `PetitionSummary` e `PetitionSummaryDto` ja existentes devem ser reaproveitados; nao deve surgir um contrato paralelo para o mesmo conceito.
- **Compatibilidade retroativa:** o port `SummarizePetitionWorkflow` existente deve ser corrigido para refletir `PetitionSummaryDto`, removendo o acoplamento indevido com `PrecedentEmbedding`.
- **Idempotencia:** a escrita em `petition_summaries` deve ser segura para reexecucao do mesmo `petition_id`, evitando linhas duplicadas em retries do endpoint.
- **Resiliencia:** download do storage, extracao do documento e chamada ao modelo devem falhar em cadeia curta; nenhuma escrita em `petition_summaries` deve ocorrer se qualquer etapa anterior falhar.

---

# 4. O que ja existe?

## Camada Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) - entidade de dominio usada para ownership check; expoe `account_id`, `status`, `summary` e `folder_id`.
- **`Petition`** (`src/animus/core/intake/domain/entities/petition.py`) - entidade de peticao ja pronta, com `analysis_id`, `uploaded_at` e `document`.
- **`PetitionDocument`** (`src/animus/core/intake/domain/structures/petition_document.py`) - `Structure` do documento associado a peticao com `file_path` e `name`.
- **`PetitionDto`** (`src/animus/core/intake/domain/entities/dtos/petition_dto.py`) - DTO de saida da peticao, com `id` opcional para suportar criacao.
- **`PetitionSummary`** (`src/animus/core/intake/domain/structures/petition_summary.py`) - `Structure` do resumo da peticao ja existente, com `content` e `main_points`.
- **`PetitionSummaryDto`** (`src/animus/core/intake/domain/structures/dtos/petition_summary_dto.py`) - DTO do resumo ja existente.
- **`PetitionsRepository`** (`src/animus/core/intake/interfaces/petitions_repository.py`) - port ja existente para persistencia de peticoes; hoje so expoe listagem por `analysis_id` e escrita.
- **`AnalisysesRepository`** (`src/animus/core/intake/interfaces/analisyses_repository.py`) - port ja existente para consultas de `Analysis`; ainda sem adaptador concreto na branch atual.
- **`SummarizePetitionWorkflow`** (`src/animus/core/intake/interfaces/summarize_petition_workflow.py`) - port ja existente, mas hoje esta inconsistente com o dominio de peticoes: importa `typing.Text`, retorna `ListResponse[PrecedentEmbedding]` e nao e referenciado por nenhum consumidor.
- **`FileStorageProvider`** (`src/animus/core/storage/interfaces/file_storage_provider.py`) - port atual de storage; hoje so cobre `generate_upload_url(...)`.
- **`PdfProvider`** (`src/animus/core/storage/interfaces/pdf_provider.py`) - port ja existente para extracao de texto de `PDF` a partir de `File`.
- **`File`** (`src/animus/core/storage/domain/structures/file.py`) - `Structure` binaria com `value`, `key`, `size_in_bytes` e `mime_type`; sera reutilizada na leitura do storage.

## Camada Database

- **`Model`** (`src/animus/database/sqlalchemy/models/model.py`) - base declarativa comum com `created_at` e `updated_at`.
- **`Sqlalchemy`** (`src/animus/database/sqlalchemy/sqlalchemy.py`) - bootstrap de `engine` e `Session` reutilizado pelo middleware e pelos repositories.
- **`AccountModel`** (`src/animus/database/sqlalchemy/models/auth/account_model.py`) - referencia concreta de `model` com `String(26)` como chave primaria e uso da base comum.
- **`AccountMapper`** (`src/animus/database/sqlalchemy/mappers/auth/account_mapper.py`) - referencia direta de `Data Mapper` dominio <-> ORM.
- **`SqlalchemyAccountsRepository`** (`src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`) - referencia de implementacao de port com `Session` injetada.
- **`src/animus/database/sqlalchemy/models/intake/__init__.py`** e **`src/animus/database/sqlalchemy/repositories/intake/__init__.py`** - pacotes de `intake` ja existem, mas estao vazios.

## Camada REST / Routers / Pipes

- **`SignUpController`** (`src/animus/rest/controllers/auth/sign_up_controller.py`) - melhor referencia de controller fino com `_Body`, `Depends(...)` e repasse por named params.
- **`SignInController`** (`src/animus/rest/controllers/auth/sign_in_controller.py`) - referencia de endpoint autenticado que retorna DTO do `core` diretamente.
- **`AuthRouter`** (`src/animus/routers/auth/auth_router.py`) - referencia de router agregador com `register() -> APIRouter` e registro de controllers.
- **`FastAPIApp`** (`src/animus/app.py`) - composition root atual; ja registra middlewares, `AuthRouter`, `DocsRouter` e `AppErrorHandler`.
- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) - pipe atual de acesso a `Session` por `request.state.sqlalchemy_session`; hoje so expoe `AccountsRepository`.
- **`ProvidersPipe`** (`src/animus/pipes/providers_pipe.py`) - ponto atual de montagem de providers de infraestrutura; ainda nao cobre `storage` nem `AI`.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) - traduz `ConflictError`, `NotFoundError`, `ValidationError`, `AuthError`, `ForbiddenError` e `AppError` para HTTP.

## Configuracao e tooling

- **`pyproject.toml`** - ja possui `agno`, `alembic`, `redis`, `python-jose` e `fastapi`, mas ainda nao declara bibliotecas para `GCS`, extracao de `PDF` ou leitura de `DOCX`.
- **`docker-compose.yaml`** - ja sobe `fake-gcs-server` em `http://localhost:4443`, o que da suporte local ao provider de storage sem inventar outro emulador.
- **`src/animus/constants/env.py`** e **`.env.example`** - concentram configuracao da aplicacao; ainda nao trazem variaveis explicitas para bucket de storage nem para `Gemini`.

## Lacunas identificadas na branch atual

- Nao existem `controllers`, `router` ou `pipes` do contexto `intake` alem do pacote vazio `src/animus/rest/controllers/intake/__init__.py`.
- Nao existe `AuthPipe` para extrair `account_id` do `Bearer token`.
- Nao existe provider concreto de `storage`, parser concreto de `PDF`, parser de `DOCX` nem qualquer `StoragePipe`.
- Nao existe implementacao concreta de `SummarizePetitionWorkflow`, nem estrutura inicial de `src/animus/ai/agno/`.
- Nao existe `PetitionSummariesRepository` no `core`, nem persistencia SQLAlchemy de `petitions` e `petition_summaries`.
- O port `AnalisysesRepository` ainda nao possui evidencia de adapter SQLAlchemy na branch atual, embora seja pre-requisito para ownership check.
- `PetitionSummary` e `PetitionSummaryDto` existem, mas nao sao exportados em `src/animus/core/intake/domain/structures/__init__.py` nem em `src/animus/core/intake/domain/structures/dtos/__init__.py`.

---

# 5. O que deve ser criado?

## Camada Core (Erros de Dominio)

- **Localizacao:** `src/animus/core/intake/domain/errors/analysis_not_found_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** quando `analysis_id` nao existir durante o ownership check de criacao da peticao.

- **Localizacao:** `src/animus/core/intake/domain/errors/petition_not_found_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** quando `petition_id` nao existir durante o fluxo de resumo.

- **Localizacao:** `src/animus/core/intake/domain/errors/unsupported_petition_document_type_error.py` (**novo arquivo**)
- **Classe base:** `ValidationError`
- **Motivo:** quando o `file_path` da peticao nao terminar com `.pdf` ou `.docx`.

- **Localizacao:** `src/animus/core/intake/domain/errors/unreadable_petition_document_error.py` (**novo arquivo**)
- **Classe base:** `ValidationError`
- **Motivo:** quando o arquivo existir no storage, mas nao puder ser convertido em texto util.

- **Localizacao:** `src/animus/core/intake/domain/errors/petition_document_not_found_error.py` (**novo arquivo**)
- **Classe base:** `NotFoundError`
- **Motivo:** quando o arquivo referenciado pela peticao nao existir no storage.

- **Localizacao:** `src/animus/core/intake/domain/errors/__init__.py` (**novo arquivo**)
- **Classe base:** nao aplicavel
- **Motivo:** estabilizar exports publicos dos novos erros do contexto `intake`.

## Camada Core (Interfaces / Ports)

- **Localizacao:** `src/animus/core/intake/interfaces/petition_summaries_repository.py` (**novo arquivo**)
- **Metodos:**
  - `find_by_petition_id(petition_id: Id) -> PetitionSummary | None` - consulta o resumo atual associado a peticao.
  - `add(petition_id: Id, petition_summary: PetitionSummary) -> None` - persiste um novo resumo da peticao.
  - `replace(petition_id: Id, petition_summary: PetitionSummary) -> None` - substitui o resumo ja existente da peticao.

- **Localizacao:** `src/animus/core/storage/interfaces/docx_provider.py` (**novo arquivo**)
- **Metodos:**
  - `extract_content(docx_file: File) -> Text` - extrai texto legivel de um arquivo `DOCX` baixado do storage.

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/intake/use_cases/create_petition_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `PetitionsRepository`
- **Metodo principal:** `execute(analysis_id: str, uploaded_at: str, document: PetitionDocumentDto) -> PetitionDto` - cria a `Petition`, persiste e retorna o DTO com `id` gerado.
- **Fluxo resumido:** validar/converter `analysis_id`, `uploaded_at` e `document` -> `Petition.create(PetitionDto(...))` -> `PetitionsRepository.add(...)` -> retornar `petition.dto`.

- **Localizacao:** `src/animus/core/intake/use_cases/create_petition_summary_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `PetitionSummariesRepository`
- **Metodo principal:** `execute(petition_id: str, dto: PetitionSummaryDto) -> PetitionSummaryDto` - converte o DTO em `PetitionSummary`, decide entre criar/substituir e devolve o DTO normalizado.
- **Fluxo resumido:** `PetitionSummary.create(dto)` -> `find_by_petition_id(...)` -> `add(...)` quando ausente / `replace(...)` quando existente -> retornar `petition_summary.dto`.

- **Localizacao:** `src/animus/core/intake/use_cases/__init__.py` (**novo arquivo**)
- **Dependencias (ports injetados):** nao aplicavel
- **Metodo principal:** nao aplicavel - exporta os `use_cases` publicos do contexto `intake`.

- **Localizacao:** `src/animus/core/storage/use_cases/get_document_content_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `FileStorageProvider`, `PdfProvider`, `DocxProvider`
- **Metodo principal:** `execute(file_path: Text) -> Text` - baixa o arquivo, escolhe parser por extensao e traduz erros tecnicos para erros de dominio (`PetitionDocumentNotFoundError`, `UnreadablePetitionDocumentError`, `UnsupportedPetitionDocumentTypeError`).

## Camada Database (Models SQLAlchemy)

- **Localizacao:** `src/animus/database/sqlalchemy/models/intake/analysis_model.py` (**novo arquivo**)
- **Tabela:** `analyses`
- **Colunas:** `id` (`String(26)`, `primary_key=True`), `name` (`String`, `nullable=False`), `folder_id` (`String(26)`, `nullable=True`), `account_id` (`String(26)`, `nullable=False`, `index=True`), `status` (`String`, `nullable=False`), `is_archived` (`Boolean`, `nullable=False`), `summary` (`Text`, `nullable=False`)
- **Relacionamentos:** **Nao aplicavel** neste escopo.

- **Localizacao:** `src/animus/database/sqlalchemy/models/intake/petition_model.py` (**novo arquivo**)
- **Tabela:** `petitions`
- **Colunas:** `id` (`String(26)`, `primary_key=True`), `analysis_id` (`String(26)`, `nullable=False`, `index=True`), `uploaded_at` (`DateTime(timezone=True)`, `nullable=False`), `document_file_path` (`String`, `nullable=False`), `document_name` (`String`, `nullable=False`)
- **Relacionamentos:** `summary` 1:1 com `PetitionSummaryModel` por `petition_id`; `analysis_id` deve permanecer alinhado ao contrato da `Analysis` mesmo enquanto a base concreta desse agregado estiver pendente na branch.

- **Localizacao:** `src/animus/database/sqlalchemy/models/intake/petition_summary_model.py` (**novo arquivo**)
- **Tabela:** `petition_summaries`
- **Colunas:** `petition_id` (`String(26)`, `ForeignKey('petitions.id')`, `primary_key=True`), `content` (`Text`, `nullable=False`), `main_points` (`JSON`, `nullable=False`)
- **Relacionamentos:** `petition` 1:1 com `PetitionModel`.

## Camada Database (Mappers)

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/intake/petition_mapper.py` (**novo arquivo**)
- **Metodos:**
  - `to_entity(model: PetitionModel) -> Petition` - reconstrui a entidade de dominio a partir do model ORM.
  - `to_model(entity: Petition) -> PetitionModel` - cria o model ORM da peticao a partir da entidade.

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/intake/petition_summary_mapper.py` (**novo arquivo**)
- **Metodos:**
  - `to_entity(model: PetitionSummaryModel) -> PetitionSummary` - reconstrui a `Structure` de resumo a partir do model ORM.
  - `to_model(petition_id: Id, petition_summary: PetitionSummary) -> PetitionSummaryModel` - cria o model ORM 1:1 do resumo associado a uma peticao.

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/intake/__init__.py` (**novo arquivo**)
- **Metodos:** nao aplicavel - exporta `PetitionMapper` e `PetitionSummaryMapper`.

## Camada Database (Repositorios)

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petitions_repository.py` (**novo arquivo**)
- **Interface implementada:** `PetitionsRepository`
- **Dependencias:** `Session` SQLAlchemy, `PetitionMapper`
- **Metodos:**
  - `find_by_id(petition_id: Id) -> Petition | None` - busca a peticao por `id` e retorna `None` quando ausente; a traducao para erro de dominio ocorre na camada de orquestracao (`pipes/use_cases`).
  - `find_all_by_analysis_id_ordered_by_uploaded_at(analysis_id: Id) -> ListResponse[Petition]` - lista peticoes da analise em ordem cronologica de upload.
  - `add(petition: Petition) -> None` - persiste uma nova peticao.
  - `add_many(petitions: list[Petition]) -> None` - persiste varias peticoes em lote.

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_summaries_repository.py` (**novo arquivo**)
- **Interface implementada:** `PetitionSummariesRepository`
- **Dependencias:** `Session` SQLAlchemy, `PetitionSummaryMapper`
- **Metodos:**
  - `find_by_petition_id(petition_id: Id) -> PetitionSummary | None` - consulta resumo por `petition_id`.
  - `add(petition_id: Id, petition_summary: PetitionSummary) -> None` - insere resumo novo.
  - `replace(petition_id: Id, petition_summary: PetitionSummary) -> None` - atualiza resumo existente.

## Camada Database (Seeders)

- **Localizacao:** `src/animus/database/sqlalchemy/seeders/intake_seeder.py` (**novo arquivo**)
- **Dependencias:** `AnalisysesRepository`, `PetitionsRepository`, `PetitionSummariesRepository`
- **Metodos:**
  - `seed(account_ids: list[Id]) -> dict[str, Id] | None` - cria dados iniciais de `Analysis`, `Petition` e `PetitionSummary` para o contexto `intake` quando existir ao menos uma conta seeded.

## Camada REST (Controllers)

- **Localizacao:** `src/animus/rest/controllers/intake/create_petition_controller.py` (**novo arquivo**)
- **`*Body`:** `_DocumentBody` com `file_path: str` e `name: str`; `_Body` com `analysis_id: str`, `uploaded_at: str` e `document: _DocumentBody`; `document.to_dto() -> PetitionDocumentDto` converte o payload aninhado para o tipo do dominio.
- **Metodo HTTP e path:** `POST /intake/petitions`
- **`status_code`:** `201`
- **`response_model`:** `PetitionDto`
- **Dependencias injetadas via `Depends`:** `account_id: Id` via `AuthPipe.get_account_id`, `analisyses_repository: AnalisysesRepository` via `DatabasePipe.get_analisyses_repository_from_request`, `petitions_repository: PetitionsRepository` via `DatabasePipe.get_petitions_repository_from_request`
- **Fluxo:** `_Body` -> `IntakePipe.verify_analysis_by_account(body.analysis_id, account_id, analisyses_repository)` -> `CreatePetitionUseCase.execute(...)` -> resposta `PetitionDto`.

- **Localizacao:** `src/animus/rest/controllers/intake/summarize_petition_controller.py` (**novo arquivo**)
- **`*Body`:** nao aplicavel
- **Metodo HTTP e path:** `POST /intake/petitions/{petition_id}/summary`
- **`status_code`:** `201`
- **`response_model`:** `PetitionSummaryDto`
- **Dependencias injetadas via `Depends`:** `document_content: Text` via `StoragePipe.get_document_content`, `workflow: SummarizePetitionWorkflow` via `AiPipe.get_summarize_petition_workflow`
- **Fluxo:** `petition_id` de path -> `StoragePipe.get_document_content(...)` -> `workflow.run(petition_id=petition_id, petition_document_content=document_content)` -> resposta `PetitionSummaryDto`.

## Camada Routers

- **Localizacao:** `src/animus/routers/intake/intake_router.py` (**novo arquivo**)
- **Prefixo da rota:** `/intake`
- **Controllers registrados:** `CreatePetitionController`, `SummarizePetitionController`

- **Localizacao:** `src/animus/routers/intake/__init__.py` (**novo arquivo**)
- **Prefixo da rota:** nao aplicavel
- **Controllers registrados:** nao aplicavel

## Camada Pipes

- **Localizacao:** `src/animus/pipes/auth_pipe.py` (**novo arquivo**)
- **Metodo `Depends`:** `get_account_id(authorization: Annotated[str, Header(alias='Authorization')], jwt_provider: Annotated[JwtProvider, Depends(ProvidersPipe.get_jwt_provider)]) -> Id` - valida o header `Bearer`, decodifica o token e devolve o `account_id` autenticado.
- **Sessao SQLAlchemy:** nao aplicavel.

- **Localizacao:** `src/animus/pipes/intake_pipe.py` (**novo arquivo**)
- **Metodo `Depends`:**
  - `verify_analysis_by_account(analysis_id: str, account_id: Id, analisyses_repository: AnalisysesRepository) -> Analysis` - valida que a analise existe e pertence ao usuario autenticado.
  - `verify_petition_document_path_by_account(petition_id: str, account_id: Annotated[Id, Depends(AuthPipe.get_account_id)], petitions_repository: Annotated[PetitionsRepository, Depends(DatabasePipe.get_petitions_repository_from_request)], analisyses_repository: Annotated[AnalisysesRepository, Depends(DatabasePipe.get_analisyses_repository_from_request)]) -> Text` - valida ownership da peticao via analise relacionada e devolve `petition.document.file_path`.
- **Sessao SQLAlchemy:** obtida indiretamente pelos repositories fornecidos por `DatabasePipe`.

- **Localizacao:** `src/animus/pipes/storage_pipe.py` (**novo arquivo**)
- **Metodo `Depends`:** `get_document_content(file_path: Annotated[Text, Depends(IntakePipe.verify_petition_document_path_by_account)], file_storage_provider: Annotated[FileStorageProvider, Depends(ProvidersPipe.get_file_storage_provider)], pdf_provider: Annotated[PdfProvider, Depends(ProvidersPipe.get_pdf_provider)], docx_provider: Annotated[DocxProvider, Depends(ProvidersPipe.get_docx_provider)]) -> Text` - baixa o arquivo e roteia a extracao pelo parser compativel com a extensao.
- **Sessao SQLAlchemy:** nao aplicavel.

- **Localizacao:** `src/animus/pipes/ai_pipe.py` (**novo arquivo**)
- **Metodo `Depends`:** `get_summarize_petition_workflow(petition_summaries_repository: Annotated[PetitionSummariesRepository, Depends(DatabasePipe.get_petition_summaries_repository_from_request)]) -> SummarizePetitionWorkflow` - monta o workflow concreto com o `CreatePetitionSummaryUseCase` ja injetado.
- **Sessao SQLAlchemy:** nao aplicavel.

## Camada Providers

- **Localizacao:** `src/animus/providers/storage/file_storage/gcs/gcs_file_storage_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `FileStorageProvider`
- **Biblioteca/SDK utilizado:** `google-cloud-storage`
- **Metodos:**
  - `get_file(file_path: Text) -> File` - baixa bytes e metadados do objeto do bucket configurado e devolve a `Structure` `File`.

- **Localizacao:** `src/animus/providers/storage/document/pdf/pypdf_pdf_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `PdfProvider`
- **Biblioteca/SDK utilizado:** `pypdf`
- **Metodos:**
  - `extract_content(pdf_file: File) -> Text` - extrai texto de todas as paginas a partir de `bytes` em memoria, sem escrita em disco.

- **Localizacao:** `src/animus/providers/storage/document/docx/python_docx_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `DocxProvider`
- **Biblioteca/SDK utilizado:** `python-docx`
- **Metodos:**
  - `extract_content(docx_file: File) -> Text` - extrai texto dos paragrafos do documento `DOCX` carregado em memoria.

- **Localizacao:** `src/animus/ai/agno/teams/intake_teams.py` (**novo arquivo**)
- **Interface implementada (port):** nao aplicavel
- **Biblioteca/SDK utilizado:** `agno`, `agno.models.google.Gemini`
- **Metodos:**
  - `summarize_petition_agent -> Agent` - agente especializado em resumir peticoes em PT-BR, com `output_schema` estruturado para `PetitionSummaryDto`.

- **Localizacao:** `src/animus/ai/agno/outputs/intake/petition_summary_output.py` (**novo arquivo**)
- **Interface implementada (port):** nao aplicavel
- **Biblioteca/SDK utilizado:** `pydantic`
- **Classe:**
  - `PetitionSummaryOutput` - schema estruturado com `content` e `main_points` consumido pelo agente e pelo workflow.

- **Localizacao:** `src/animus/ai/agno/workflows/intake/agno_summarize_petition_workflow.py` (**novo arquivo**)
- **Interface implementada (port):** `SummarizePetitionWorkflow`
- **Biblioteca/SDK utilizado:** `agno`, `Gemini`
- **Metodos:**
  - `run(petition_id: str, petition_document_content: Text) -> PetitionSummaryDto` - executa o agente com timeout de `60s`, converte a saida estruturada para `PetitionSummaryDto`, persiste via `CreatePetitionSummaryUseCase` e retorna o DTO persistido.

## Migracoes Alembic (se aplicavel)

- **Localizacao:** `migrations/versions/<timestamp>_create_analyses_table.py` (**novo arquivo**)
- **Operacoes:** criar `analyses` com indice em `account_id` para suportar ownership check por conta.
- **Reversibilidade:** `downgrade` remove indice e tabela `analyses`.

- **Localizacao:** `migrations/versions/<timestamp>_create_petitions_and_summaries_tables.py` (**novo arquivo**)
- **Operacoes:** criar `petitions` e `petition_summaries`, incluindo `petition_summaries.petition_id` 1:1 com `petitions.id` e indices minimos para `analysis_id`.
- **Reversibilidade:** `downgrade` pode remover as duas tabelas; seguro apenas se a branch ainda nao tiver dependencias externas sobre `petition_id`.

---

# 6. O que deve ser modificado?

## Camada Core

- **Arquivo:** `src/animus/core/intake/interfaces/petitions_repository.py`
- **Mudanca:** adicionar `find_by_id(petition_id: Id) -> Petition | None` ao port existente, preservando os metodos de listagem e escrita ja publicados.
- **Justificativa:** o fluxo de resumo precisa localizar uma peticao pelo `petition_id` de path antes de acessar o storage.

- **Arquivo:** `src/animus/core/intake/interfaces/analisyses_repository.py`
- **Mudanca:** corrigir a semantica do parametro de `find_by_id(...)` para `analysis_id: Id` e padronizar retorno `Analysis | None` quando nao encontrada.
- **Justificativa:** o nome atual `account_id` conflita com o uso real de ownership check e induz implementacao incorreta.

- **Arquivo:** `src/animus/core/intake/interfaces/summarize_petition_workflow.py`
- **Mudanca:** trocar o import de `typing.Text` por `animus.core.shared.domain.structures.Text`, alterar o retorno para `PetitionSummaryDto` e incluir `petition_id: str` na assinatura de `run(...)`.
- **Justificativa:** o port atual reflete acoplamento residual com embeddings de precedentes e nao consegue representar a persistencia do resumo exigida pelo ticket.

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudanca:** exportar `PetitionSummariesRepository` e `SummarizePetitionWorkflow` junto dos contratos existentes.
- **Justificativa:** estabilizar os imports publicos do contexto `intake`.

- **Arquivo:** `src/animus/core/intake/domain/structures/__init__.py`
- **Mudanca:** exportar `PetitionSummary`.
- **Justificativa:** a `Structure` ja existe, mas hoje esta invisivel no barrel publico do contexto.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/__init__.py`
- **Mudanca:** exportar `PetitionSummaryDto`.
- **Justificativa:** permitir consumo consistente do DTO pelo `workflow`, controllers e adapters externos.

- **Arquivo:** `src/animus/core/storage/interfaces/file_storage_provider.py`
- **Mudanca:** adicionar `get_file(file_path: Text) -> File` ao contrato.
- **Justificativa:** com a decisao de manter parsing fora do storage provider, o adapter precisa devolver o arquivo bruto para `StoragePipe`.

- **Arquivo:** `src/animus/core/storage/interfaces/__init__.py`
- **Mudanca:** exportar `DocxProvider` junto de `FileStorageProvider` e `PdfProvider`.
- **Justificativa:** manter a API publica do contexto `storage` coerente com o suporte a `DOCX` definido no PRD.

- **Arquivo:** `src/animus/core/intake/domain/errors/__init__.py`
- **Mudanca:** exportar `PetitionDocumentNotFoundError` junto dos erros existentes de `intake`.
- **Justificativa:** estabilizar import publico para traducao de erro de arquivo ausente no fluxo de resumo.

## Camada Database

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/__init__.py`
- **Mudanca:** exportar `AnalysisModel`, `PetitionModel` e `PetitionSummaryModel`.
- **Justificativa:** alinhar o pacote `intake` ao padrao de exports publicos ja usado em `auth`.

- **Arquivo:** `src/animus/database/sqlalchemy/mappers/__init__.py`
- **Mudanca:** exportar o subpacote `intake` para estabilizar imports internos da camada.
- **Justificativa:** seguir o mesmo padrao de barreira publica ja presente em `mappers/auth`.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/__init__.py`
- **Mudanca:** exportar `SqlalchemyPetitionsRepository` e `SqlalchemyPetitionSummariesRepository`.
- **Justificativa:** permitir que `DatabasePipe` monte os adapters concretos sem depender de caminhos internos volateis.

- **Arquivo:** `migrations/env.py`
- **Mudanca:** importar o pacote `animus.database.sqlalchemy.models.intake` para incluir os novos models no `target_metadata` do Alembic.
- **Justificativa:** sem esse import o autogenerate nao enxerga as tabelas novas.

- **Arquivo:** `src/animus/database/sqlalchemy/seed.py`
- **Mudanca:** incluir execucao do `IntakeSeeder` apos `AuthSeeder`, reaproveitando `account_ids` semeados.
- **Justificativa:** disponibilizar dados de `intake` para validacao local manual dos endpoints.

- **Arquivo:** `src/animus/database/sqlalchemy/seeders/__init__.py`
- **Mudanca:** exportar `IntakeSeeder` junto de `AuthSeeder`.
- **Justificativa:** manter barrel publico da camada de seeders consistente com os seeders disponiveis.

## Camada REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudanca:** exportar `CreatePetitionController` e `SummarizePetitionController`.
- **Justificativa:** manter o pacote publico do contexto alinhado ao padrao dos controllers de `auth`.

- **Arquivo:** `src/animus/app.py`
- **Mudanca:** registrar `IntakeRouter.register()` na composicao da aplicacao.
- **Justificativa:** sem incluir o router no composition root os novos endpoints nao ficam expostos.

## Camada Routers

- **Arquivo:** `src/animus/routers/__init__.py`
- **Mudanca:** exportar `IntakeRouter` junto de `AuthRouter`.
- **Justificativa:** estabilizar o pacote de routers da aplicacao.

## Camada Pipes

- **Arquivo:** `src/animus/pipes/database_pipe.py`
- **Mudanca:** adicionar `get_petitions_repository_from_request(...) -> PetitionsRepository`, `get_petition_summaries_repository_from_request(...) -> PetitionSummariesRepository` e `get_analisyses_repository_from_request(...) -> AnalisysesRepository`.
- **Justificativa:** o contexto `intake` precisa resolver repositories concretos por `Depends(...)` a partir da `Session` aberta no middleware.

- **Arquivo:** `src/animus/pipes/providers_pipe.py`
- **Mudanca:** adicionar `get_file_storage_provider() -> FileStorageProvider`, `get_pdf_provider() -> PdfProvider` e `get_docx_provider() -> DocxProvider`.
- **Justificativa:** manter a montagem de adaptadores de infraestrutura centralizada no pipe ja existente.

- **Arquivo:** `src/animus/pipes/storage_pipe.py`
- **Mudanca:** delegar leitura/parsing para `GetDocumentContentUseCase` e tratar explicitamente `PetitionDocumentNotFoundError` em vez de traduzir tudo para erro de documento ilegivel.
- **Justificativa:** manter regra de dominio de leitura no `core` e diferenciar semanticamente arquivo ausente de arquivo ilegivel.

- **Arquivo:** `src/animus/pipes/__init__.py`
- **Mudanca:** exportar `AuthPipe`, `IntakePipe`, `StoragePipe` e `AiPipe`.
- **Justificativa:** manter o barrel de `pipes` coerente com a nova superficie de DI.

## Camada Providers

- **Arquivo:** `src/animus/constants/env.py`
- **Mudanca:** adicionar configuracao minima para `storage` e `Gemini`, ao menos `MODE` (`dev|stg|prod`), `GCS_BUCKET_NAME`, `STORAGE_EMULATOR_HOST` e `GEMINI_API_KEY`; o uso de `STORAGE_EMULATOR_HOST` deve ficar restrito a `MODE=dev`.
- **Justificativa:** os novos adapters de `storage` e `AI` precisam de configuracao centralizada e validada, com separacao explicita entre ambiente local e ambiente produtivo.

- **Arquivo:** `.env.example`
- **Mudanca:** documentar `MODE`, as novas variaveis de bucket/emulador e `GEMINI_API_KEY`, deixando claro que `STORAGE_EMULATOR_HOST` e apenas para desenvolvimento local.
- **Justificativa:** manter bootstrap local coerente com o novo wiring e reduzir risco de configuracao incorreta em `stg`/`prod`.

- **Arquivo:** `pyproject.toml`
- **Mudanca:** adicionar `google-cloud-storage`, `pypdf` e `python-docx` como dependencias da aplicacao.
- **Justificativa:** a branch atual nao possui SDK de GCS nem bibliotecas para extracao de `PDF` e `DOCX`.

---

# 7. O que deve ser removido?

**Nao aplicavel**.

---

# 8. Decisoes Tecnicas e Trade-offs

- **Decisao:** manter a extracao de texto no `StoragePipe`, com `FileStorageProvider` devolvendo `File` e parsers separados por tipo (`PdfProvider` e `DocxProvider`).
  - **Alternativas consideradas:** fazer `FileStorageProvider.get_file_content(...) -> Text` encapsular download e parsing; suportar apenas `PDF` no backend inicial.
  - **Motivo da escolha:** preserva separacao entre `storage` e parsing, reaproveita o port `PdfProvider` ja existente e cumpre o PRD de `PDF` + `DOCX`.
  - **Impactos / trade-offs:** aumenta o numero de adapters e `Depends(...)`, mas deixa a extensao para novos formatos mais previsivel.

- **Decisao:** corrigir `SummarizePetitionWorkflow.run(...)` para receber `petition_id` e retornar `PetitionSummaryDto`.
  - **Alternativas consideradas:** manter a assinatura atual e persistir o resumo no controller; guardar `petition_id` no construtor do workflow.
  - **Motivo da escolha:** o proprio ticket exige que a persistencia aconteca dentro do fluxo do `workflow`; sem `petition_id` a assinatura atual fica impossivel de implementar de forma limpa.
  - **Impactos / trade-offs:** o port de AI fica explicitamente acoplado ao contexto de persistencia do resumo, mas elimina estado oculto e controller gordo.

- **Decisao:** seguir a organizacao de AI definida para o projeto, criando o workflow em `src/animus/ai/agno/workflows/intake/` e o time em `src/animus/ai/agno/teams/`.
  - **Alternativas consideradas:** usar a estrutura sugerida no Jira em `src/animus/providers/intake/summarize_petition/agno/`.
  - **Motivo da escolha:** este task deve seguir o path real esperado para AI no projeto, evitando documentar a implementacao em um namespace diferente do acordado.
  - **Impactos / trade-offs:** cria mais estrutura de pacote upfront, mas evita fragmentacao futura da camada AI.

- **Decisao:** determinar o parser do documento pela extensao do `file_path` (`.pdf` ou `.docx`), e nao pelo `mime_type` retornado pelo storage.
  - **Alternativas consideradas:** confiar apenas no `mime_type`; tentar autodetectar o tipo lendo os bytes.
  - **Motivo da escolha:** o contrato de upload ja define a extensao no `file_path`, e ambientes com fake GCS podem variar metadados de `content-type`.
  - **Impactos / trade-offs:** o fluxo passa a depender do contrato de path gerado no upload; mudancas nesse contrato exigem alinhar o roteamento do `StoragePipe`.

- **Decisao:** reaproveitar `PetitionSummary` e `PetitionSummaryDto` existentes, corrigindo apenas exports e consumidores.
  - **Alternativas consideradas:** criar um novo schema HTTP ou um DTO separado apenas para o provider de AI.
  - **Motivo da escolha:** evita duplicacao de conceitos no `core` e reduz churn em um contexto que ja possui a modelagem de resumo pronta.
  - **Impactos / trade-offs:** `PetitionSummaryDto` pode ser reutilizado diretamente como contrato estruturado do `workflow` e do provider de AI; o cuidado passa a ser apenas manter os exports e imports publicos do contexto consistentes.

- **Decisao:** manter `PetitionsRepository.find_all_by_analysis_id_ordered_by_uploaded_at(...)` sem impor unicidade de `analysis_id` na tabela `petitions`.
  - **Alternativas consideradas:** tornar `analysis_id` unico e bloquear historico; sobrescrever sempre a peticao anterior da mesma analise.
  - **Motivo da escolha:** o port ja publicado no `core` assume potencial pluralidade de peticoes por analise, e o endpoint de resumo trabalha com `petition_id` explicito, nao com "peticao atual" implicita.
  - **Impactos / trade-offs:** o backend preserva historico tecnico de uploads por analise, enquanto a regra de UI do PRD continua limitando um envio por interacao do usuario.

---

# 9. Diagramas e Referencias

- **Fluxo de dados:**

```text
POST /intake/petitions
  -> FastAPIApp.register()
  -> IntakeRouter
  -> CreatePetitionController
  -> AuthPipe.get_account_id()
  -> IntakePipe.verify_analysis_by_account(...)
  -> CreatePetitionUseCase.execute(...)
       -> Petition.create(...)
       -> PetitionsRepository.add(...)
       -> PostgreSQL (petitions)
  -> 201 PetitionDto

POST /intake/petitions/{petition_id}/summary
  -> FastAPIApp.register()
  -> IntakeRouter
  -> SummarizePetitionController
  -> AuthPipe.get_account_id()
  -> IntakePipe.verify_petition_document_path_by_account(...)
  -> StoragePipe.get_document_content(...)
       -> FileStorageProvider.get_file(...)
       -> PdfProvider.extract_content(...) | DocxProvider.extract_content(...)
  -> AiPipe.get_summarize_petition_workflow(...)
  -> SummarizePetitionWorkflow.run(...)
       -> Gemini (structured output)
       -> CreatePetitionSummaryUseCase.execute(...)
       -> PetitionSummariesRepository.find_by_petition_id(...)
       -> PetitionSummariesRepository.add(...) | PetitionSummariesRepository.replace(...)
       -> PostgreSQL (petition_summaries)
  -> 201 PetitionSummaryDto
```

- **Fluxo assincrono:** **Nao aplicavel**.

- **Referencias:**
  - `src/animus/rest/controllers/auth/sign_up_controller.py`
  - `src/animus/core/auth/use_cases/sign_up_use_case.py`
  - `src/animus/database/sqlalchemy/repositories/auth/sqlalchemy_accounts_repository.py`
  - `src/animus/database/sqlalchemy/mappers/auth/account_mapper.py`
  - `src/animus/routers/auth/auth_router.py`
  - `src/animus/app.py`
  - `src/animus/pipes/database_pipe.py`
  - `src/animus/core/intake/domain/entities/petition.py`
  - `src/animus/core/intake/domain/structures/petition_summary.py`
  - `src/animus/core/storage/interfaces/pdf_provider.py`

---
