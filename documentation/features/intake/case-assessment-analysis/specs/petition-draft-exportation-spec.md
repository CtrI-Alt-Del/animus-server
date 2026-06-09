---
title: Geração do arquivo DOCX da minuta de petição inicial
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AYDsAg
ticket: N/A
status: open
last_updated_at: 2026-06-05
---

# 1. Objetivo

Implementar a geração sob demanda de um arquivo `DOCX` para a `PetitionDraft` de análises `CASE_ASSESSMENT`, persistindo o artefato no storage configurado pelo projeto e devolvendo ao cliente o `file_path` do arquivo gerado. A entrega deve validar a existência e a completude da minuta persistida, reutilizar o padrão já adotado de paths em `storage`, manter o `core` isolado de filesystem e SDKs, e não alterar os contratos atuais de leitura, edição, geração ou regeração da minuta.

# 2. Escopo

## 2.1 In-scope

- Criar endpoint HTTP para gerar o `DOCX` da minuta atual e devolver seu `file_path`.
- Validar ownership da análise via `IntakePipe.verify_analysis_by_account_from_request(...)`.
- Exigir que a análise seja do tipo `CASE_ASSESSMENT`.
- Exigir que a minuta já exista para a análise.
- Bloquear a geração quando qualquer seção obrigatória estiver vazia ou inconsistente.
- Gerar o documento em memória, materializar um arquivo temporário local e fazer upload para o storage já usado pelo projeto.
- Persistir o artefato gerado no bucket usando convenção de `file_path` alinhada ao padrão de `intake/analyses/{analysis_id}/...`.
- Devolver ao cliente apenas o `file_path` do artefato gerado.
- Registrar o novo controller no router de `intake`.

## 2.2 Out-of-scope

- Download binário do `DOCX` no mesmo endpoint.
- Geração de PDF da minuta.
- Persistência do `file_path` gerado em tabela do banco.
- Versionamento histórico de exports.
- Alterações na UI/mobile, share sheet, loading state ou obtenção do arquivo a partir do `file_path`.
- Alterações no schema da tabela `petition_drafts`.
- Alterações nos fluxos assíncronos de geração ou regeração da minuta.
- Exportação de minutas de `SECOND_INSTANCE`.

# 3. Requisitos

## 3.1 Funcionais

- O backend deve expor `POST /intake/analyses/{analysis_id}/petition-drafts/docx`.
- O endpoint deve retornar `201 Created` com body JSON no contrato de `AnalysisDocumentDto`.
- O endpoint deve exigir autenticação e ownership via `IntakePipe.verify_analysis_by_account_from_request(...)`.
- A geração só deve ser permitida para análises do tipo `CASE_ASSESSMENT`.
- A geração deve falhar com `404` quando a análise não possuir `PetitionDraft` persistida.
- O `DOCX` gerado deve refletir sempre o estado persistido atual da minuta, incluindo edições manuais já salvas.
- O `DOCX` deve conter exclusivamente as seções da minuta: `structured_facts`, `legal_grounds`, `central_thesis`, `requests` e `precedent_citations`.
- `requests` e `precedent_citations` devem ser renderizados como listas no documento.
- A geração deve falhar com `422` quando qualquer campo obrigatório estiver vazio após `strip()`, quando `requests` ou `precedent_citations` estiverem vazios, ou quando uma dessas listas contiver item vazio.
- A mensagem de erro de `422` deve informar quais seções impedem a geração do arquivo.
- O `file_path` retornado deve apontar para o artefato recém-gerado em um prefixo do tipo `intake/analyses/{analysis_id}/petition-draft-exports/`.
- O basename do arquivo deve preservar a intenção do PRD de nomear o documento como `[Nome da análise] — Minuta.docx`, com normalização compatível com path de storage.
- O payload de resposta deve seguir `AnalysisDocumentDto`, preenchendo `analysis_id`, `uploaded_at`, `file_path` e `name`.
- Requisições repetidas devem sobrescrever o artefato anterior quando o `file_path` calculado for o mesmo, ou substituir logicamente a versão acessível mais recente quando a estratégia escolhida usar nome único por geração.

## 3.2 Não funcionais

- **Performance:** a geração do `DOCX` deve ser síncrona e sem IA; o único I/O externo permitido no fluxo é o upload do arquivo ao storage.
- **Segurança:** o endpoint deve reutilizar `IntakePipe.verify_analysis_by_account_from_request(...)`; nenhuma decisão de ownership deve depender apenas do `analysis_id` recebido no path.
- **Observabilidade:** erros de domínio devem subir para o `AppErrorHandler`; o controller não deve capturar exceções manualmente.
- **Compatibilidade retroativa:** a entrega deve ser aditiva, sem alterar `PetitionDraftDto`, `PetitionDraft`, `petition_drafts`, contratos dos endpoints existentes nem fluxos assíncronos.
- **Persistência:** a feature não deve criar novos registros ou tabelas, mas passa a gerar um novo path de arquivo em storage por exportação.
- **Infraestrutura:** o `core` não deve conhecer filesystem local, `GCS`, `Supabase`, `python-docx` ou detalhes de upload.

# 4. O que já existe?

## Core / Intake

- **`PetitionDraft`** (`src/animus/core/intake/domain/structures/petition_draft.py`) — structure de domínio já normalizada com `structured_facts`, `legal_grounds`, `central_thesis`, `requests` e `precedent_citations`.
- **`PetitionDraftDto`** (`src/animus/core/intake/domain/structures/dtos/petition_draft_dto.py`) — DTO estável da minuta, já usado em leitura, geração, regeração e edição.
- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) — entidade que expõe `name`, `type` e `account_id`, necessários para compor o nome do arquivo e validar o tipo da análise.
- **`AnalysisDocumentDto`** (`src/animus/core/intake/domain/structures/dtos/analysis_document_dto.py`) — DTO já existente com `analysis_id`, `uploaded_at`, `file_path` e `name`; deve ser reutilizado como contrato de resposta da exportação.
- **`PetitionDraftsRepository`** (`src/animus/core/intake/interfaces/petition_drafts_repository.py`) — port com `find_by_analysis_id(...)`, `add(...)` e `replace(...)`.
- **`AnalysesRepository`** (`src/animus/core/intake/interfaces/analyses_repository.py`) — port usado para buscar a análise por ID.
- **`GetPetitionDraftUseCase`** (`src/animus/core/intake/use_cases/get_petition_draft_use_case.py`) — referência de leitura protegida por ownership e de uso de `PetitionDraftUnavailableError`.
- **`UpdatePetitionDraftUseCase`** (`src/animus/core/intake/use_cases/update_petition_draft_use_case.py`) — referência de validação de tipo `CASE_ASSESSMENT` e de sobrescrita da minuta persistida.
- **`PetitionDraftUnavailableError`** (`src/animus/core/intake/domain/errors/petition_draft_unavailable_error.py`) — erro já alinhado ao cenário em que a minuta ainda não existe.
- **`InconsistentAnalysisTypeError`** (`src/animus/core/intake/domain/errors/inconsistent_analysis_type_error.py`) — erro já usado quando o tipo da análise é incompatível com o fluxo.
- **`AnalysisNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_not_found_error.py`) — erro para análise inexistente.

## Core / Shared / Storage

- **`FilePath`** (`src/animus/core/shared/domain/structures/file_path.py`) — structure já usada como identidade de arquivos persistidos/gerados em storage.
- **`File`** (`src/animus/core/storage/domain/structures/file.py`) — structure usada para trafegar conteúdo binário em memória.
- **`FileStorageProvider`** (`src/animus/core/storage/interfaces/file_storage_provider.py`) — port atual com `generate_upload_url(...)`, `get_file(...)`, `upload_files(...)` e `remove_files(...)`.
- **`UploadUrlDto`** (`src/animus/core/storage/domain/structures/dtos/upload_url_dto.py`) — DTO que já expõe `file_path`, reforçando o padrão do projeto de devolver paths de storage para o cliente.
- **`GenerateAnalysisDocumentUploadUrlUseCase`** (`src/animus/core/storage/use_cases/generate_petition_upload_url_use_case.py`) — referência de convenção para construção de paths no prefixo `intake/analyses/{analysis_id}/...`.
- **`DocxProvider`** (`src/animus/core/storage/interfaces/docx_provider.py`) — port genérico já existente para leitura de `DOCX`; esta feature não cria esse contrato e não deve reutilizá-lo como port principal da exportação.

## Database

- **`PetitionDraftModel`** (`src/animus/database/sqlalchemy/models/intake/petition_draft_model.py`) — model da tabela `petition_drafts`, já com todas as colunas estruturadas necessárias à montagem do documento.
- **`PetitionDraftMapper`** (`src/animus/database/sqlalchemy/mappers/intake/petition_draft_mapper.py`) — mapper entre `PetitionDraftModel` e `PetitionDraft`.
- **`SqlalchemyPetitionDraftsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_drafts_repository.py`) — implementação concreta usada para carregar a minuta persistida.
- **`SqlalchemyAnalysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analyses_repository.py`) — implementação concreta usada para buscar o nome e o tipo da análise.
- **Seeders da camada database:** `src/animus/database/sqlalchemy/seeders/intake_seeder.py` existe, mas a feature não cria dados iniciais nem altera `seeders`.

## REST

- **`GetPetitionDraftController`** (`src/animus/rest/controllers/intake/get_petition_draft_controller.py`) — referência de rota `GET` do recurso `petition-drafts`.
- **`UpdatePetitionDraftController`** (`src/animus/rest/controllers/intake/update_petition_draft_controller.py`) — referência de validação de campos não vazios na borda HTTP e de uso do mesmo recurso REST.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) — handler global já configurado para `404`, `403`, `409`, `400` e `422` para precondições específicas.

## Routers

- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) — composition root que já registra os endpoints de `petition-drafts` do contexto `intake`.

## Pipes

- **`IntakePipe.verify_analysis_by_account_from_request(...)`** (`src/animus/pipes/intake_pipe.py`) — guard de ownership já usado nos endpoints de análise por `analysis_id`.
- **`DatabasePipe.get_analyses_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP já pronto para `AnalysesRepository`.
- **`DatabasePipe.get_petition_drafts_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP já pronto para `PetitionDraftsRepository`.
- **`ProvidersPipe.get_file_storage_provider()`** (`src/animus/pipes/providers_pipe.py`) — provider já pronto do storage concreto.

## Providers

- **`PythonDocxProvider`** (`src/animus/providers/storage/document/docx/python_docx_provider.py`) — implementação concreta baseada em `python-docx`, já capaz de ler `DOCX` a partir de `bytes` em memória com `BytesIO`.
- **`GcsFileStorageProvider`** (`src/animus/providers/storage/file_storage/gcs/gcs_file_storage_provider.py`) — implementa `upload_files(...)` a partir de `FilePath` local, servindo de referência de comportamento do adaptador de storage.
- **`SupabaseFileStorageProvider`** (`src/animus/providers/storage/file_storage/supabase/supabase_file_storage_provider.py`) — mantém a mesma semântica de `upload_files(...)`, reforçando que o port atual opera via arquivo local temporário.

## Implementações análogas

- **`SeedAnalysesPrecedentsDatasetJob._export_dataset_sync(...)`** (`src/animus/pubsub/inngest/jobs/intake/seed_analyses_precedents_dataset_job.py`) — referência concreta de fluxo que cria arquivo local temporário, monta `bucket_file_path`, faz upload e remove o arquivo local ao final.

## Lacunas identificadas

- Não existe endpoint HTTP para gerar o `DOCX` da minuta e devolver seu `file_path`.
- Não existe hoje um fluxo que reutilize `AnalysisDocumentDto` para representar um artefato exportado da minuta.
- O `PythonDocxProvider` hoje só cobre leitura (`extract_content(...)`), não geração de documento.
- Não existe port do `core/intake` que encapsule a geração + upload do artefato `DOCX`.
- O `DocxProvider` existente é genérico e de leitura; ele não cobre a semântica específica da exportação da minuta.

# 5. O que deve ser criado?

## Camada Core (Structures / DTOs)

**Não aplicável**.

## Camada Core (Erros de Domínio)

- **Localização:** `src/animus/core/intake/domain/errors/petition_draft_export_incomplete_error.py` (**novo arquivo**)
- **Classe base:** `AppError`
- **Motivo:** levantado quando a minuta existe, mas não pode ser exportada porque uma ou mais seções obrigatórias estão vazias ou inconsistentes.
- **Construtor:** `__init__(missing_fields: list[str]) -> None` — cria mensagem determinística listando os campos que bloqueiam a geração do arquivo.

## Camada Core (Interfaces / Ports)

- **Localização:** `src/animus/core/intake/interfaces/petition_draft_docx_provider.py` (**novo arquivo**)
- **Observação:** este port é o contrato novo da feature; **não** será criado um novo `DocxProvider`.
- **Métodos:**
  - `export(analysis_id: str, analysis_name: str, petition_draft: PetitionDraft) -> AnalysisDocumentDto` — gera o `DOCX`, faz upload para o storage e devolve o metadado do artefato no contrato reutilizado pelo projeto.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/export_petition_draft_docx_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `AnalysesRepository`, `PetitionDraftsRepository`, `PetitionDraftDocxProvider`
- **Método principal:** `execute(analysis_id: str) -> AnalysisDocumentDto` — valida a análise, garante a existência e a completude da minuta e delega a geração/upload do `DOCX` ao provider.
- **Fluxo resumido:**
  - Normaliza `analysis_id` como `Id`.
  - Busca `Analysis`; se ausente, lança `AnalysisNotFoundError`.
  - Se `analysis.type.is_case_analysis.is_false`, lança `InconsistentAnalysisTypeError`.
  - Busca `PetitionDraft` por `analysis_id`; se ausente, lança `PetitionDraftUnavailableError`.
  - Avalia campos faltantes ou vazios da minuta persistida.
  - Se houver campos inválidos, lança `PetitionDraftExportIncompleteError` com a lista ordenada.
  - Delega ao `PetitionDraftDocxProvider.export(...)` usando `analysis.id.value`, `analysis.name.value` e a `PetitionDraft` atual.
  - Retorna o DTO com `file_path`.
- **Método auxiliar interno:** `_collect_missing_fields(petition_draft: PetitionDraft) -> list[str]` — identifica `structured_facts`, `legal_grounds`, `central_thesis`, `requests` e `precedent_citations` vazios ou com itens em branco.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/export_petition_draft_docx_controller.py` (**novo arquivo**)
- **`*Body`:** **Não aplicável**.
- **Método HTTP e path:** `POST /analyses/{analysis_id}/petition-drafts/docx`
- **`status_code`:** `201`
- **`response_model`:** `AnalysisDocumentDto`
- **Dependências injetadas via `Depends`:** `IntakePipe.verify_analysis_by_account_from_request(...)`, `DatabasePipe.get_analyses_repository_from_request(...)`, `DatabasePipe.get_petition_drafts_repository_from_request(...)`, `ProvidersPipe.get_petition_draft_docx_provider()`
- **Fluxo:** `analysis.id.value` → `ExportPetitionDraftDocxUseCase.execute(...)` → `AnalysisDocumentDto`

## Camada Pipes

- **Localização:** `src/animus/pipes/providers_pipe.py` (**arquivo existente**)
- **Método `Depends`:** `get_petition_draft_docx_provider() -> PetitionDraftDocxProvider` — provê o adaptador concreto de geração + upload do `DOCX`.

## Camada Providers

- **Localização:** `src/animus/providers/storage/document/docx/python_docx_petition_draft_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `PetitionDraftDocxProvider`
- **Biblioteca/SDK utilizado:** `python-docx`
- **Dependências:** `FileStorageProvider`
- **Métodos:**
  - `__init__(file_storage_provider: FileStorageProvider) -> None` — armazena o provider de storage concreto.
  - `export(analysis_id: str, analysis_name: str, petition_draft: PetitionDraft) -> AnalysisDocumentDto` — monta o `DOCX`, grava um arquivo temporário local, faz upload para o `file_path` final, remove o temporário e retorna os metadados do artefato.
- **Fluxo resumido do provider:**
  - Sanitiza o nome da análise para basename compatível com path.
  - Monta `bucket_file_path` em `intake/analyses/{analysis_id}/petition-draft-exports/{sanitized_name}-minuta.docx` ou variante equivalente definida na implementação.
  - Monta `local_file_path` temporário fora do bucket, em diretório temporário controlado pelo provider.
  - Gera o `Document()` em memória com as seções da minuta.
  - Salva o documento no `local_file_path`.
  - Executa `file_storage_provider.upload_files([bucket_file_path])` reaproveitando o contrato atual da infraestrutura.
  - Remove o arquivo temporário local mesmo em fluxo bem-sucedido.
  - Retorna `AnalysisDocumentDto(analysis_id=analysis_id, uploaded_at=..., file_path=bucket_file_path.value, name=...)`.

## Camada Validation (Schemas Pydantic de Saída)

**Não aplicável**.

## Migrações Alembic

**Não aplicável**.

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/errors/__init__.py`
- **Mudança:** exportar `PetitionDraftExportIncompleteError`.
- **Justificativa:** manter o barrel de erros do contexto `intake` consistente.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/__init__.py`
- **Mudança:** **Não aplicável**.
- **Justificativa:** `AnalysisDocumentDto` já existe e deve ser reutilizado como contrato de resposta.

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudança:** exportar `PetitionDraftDocxProvider`.
- **Justificativa:** estabilizar o import público do novo port de infraestrutura.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** exportar `ExportPetitionDraftDocxUseCase`.
- **Justificativa:** manter o barrel de casos de uso atualizado com o novo fluxo síncrono.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** exportar `ExportPetitionDraftDocxController`.
- **Justificativa:** manter a composição pública dos controllers de `intake` consistente com o padrão do projeto.

- **Arquivo:** `src/animus/rest/handlers/app_error_handler.py`
- **Mudança:** mapear `PetitionDraftExportIncompleteError` para `422 Unprocessable Entity`.
- **Justificativa:** a falha não é de autenticação nem de ausência do recurso; é uma precondição de exportação sobre dados já persistidos.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** registrar `ExportPetitionDraftDocxController.handle(router)` junto ao agrupamento de `petition-drafts`.
- **Justificativa:** anexar o novo endpoint ao mesmo recurso HTTP já existente para leitura, edição, geração e regeração da minuta.

## Pipes

- **Arquivo:** `src/animus/pipes/providers_pipe.py`
- **Mudança:** adicionar `get_petition_draft_docx_provider() -> PetitionDraftDocxProvider`, instanciando o provider concreto com `get_file_storage_provider()`.
- **Justificativa:** manter o wiring do endpoint tipado por port do `core`, sem depender do adaptador concreto no controller.

## Providers

- **Arquivo:** `src/animus/providers/storage/document/docx/__init__.py`
- **Mudança:** exportar `PythonDocxPetitionDraftProvider`.
- **Justificativa:** estabilizar imports públicos do submódulo de `docx`.

- **Arquivo:** `src/animus/providers/storage/document/__init__.py`
- **Mudança:** exportar `PythonDocxPetitionDraftProvider` junto aos providers já existentes.
- **Justificativa:** manter consistência dos exports do pacote de storage document.

- **Arquivo:** `src/animus/providers/storage/__init__.py`
- **Mudança:** exportar `PythonDocxPetitionDraftProvider` se o projeto mantiver agregação nesse nível.
- **Justificativa:** seguir o padrão atual de exports públicos da camada providers.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_drafts_repository.py`
- **Mudança:** **Não aplicável**.
- **Justificativa:** a exportação continua somente leitura sobre a minuta persistida.

## Seeders da camada database

- **Arquivo:** `src/animus/database/sqlalchemy/**/seeders/`
- **Mudança:** **Não aplicável**.
- **Justificativa:** a feature não exige carga inicial nem altera seeders, apenas gera artefato em storage durante execução do endpoint.

# 7. O que deve ser removido?

**Não aplicável**.

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** o endpoint deve ser `POST`, não `GET`.
- **Alternativas consideradas:** `GET /.../petition-drafts/docx` retornando binário; `GET` retornando apenas path.
- **Motivo da escolha:** a operação cria um novo artefato em storage; tratá-la como `POST` deixa explícito o side effect e evita modelar como leitura pura um fluxo que materializa arquivo.
- **Impactos / trade-offs:** o contrato HTTP fica menos “download-like”, mas mais consistente com a semântica real de geração de artefato.

- **Decisão:** devolver apenas `file_path`, não o binário do documento.
- **Alternativas consideradas:** streaming/binário direto na resposta; signed URL no mesmo payload.
- **Motivo da escolha:** segue o esclarecimento funcional da tarefa e o padrão já presente no projeto de trabalhar com `file_path` como identidade prática de arquivos gerados ou carregados.
- **Impactos / trade-offs:** desacopla geração e obtenção do arquivo; em contrapartida, o consumo do path no cliente ou em fluxo posterior fica fora deste recorte.

- **Decisão:** encapsular geração do `DOCX` e upload no mesmo provider de infraestrutura do contexto `intake`.
- **Alternativas consideradas:** fazer o `UseCase` gerar bytes e manipular filesystem; estender `FileStorageProvider` com upload por bytes; acoplar `PythonDocxProvider` diretamente ao controller.
- **Motivo da escolha:** o port do `core` continua simples e o `UseCase` não conhece `python-docx`, arquivo temporário, `GCS`, `Supabase` nem estratégia de upload.
- **Impactos / trade-offs:** o provider concreto fica mais rico, mas a regra de negócio permanece no `core`.

- **Decisão:** criar `PetitionDraftDocxProvider` como port específico da feature, em vez de expandir `DocxProvider`.
- **Alternativas consideradas:** adicionar `export(...)` ao `DocxProvider`; montar toda a geração dentro do `UseCase`.
- **Motivo da escolha:** `DocxProvider` já existe como contrato genérico de leitura, enquanto esta feature precisa de um contrato orientado ao domínio `PetitionDraft`, ao `analysis_id`, ao `analysis_name` e à estratégia de `file_path` do contexto `intake`.
- **Impactos / trade-offs:** adiciona um port novo no contexto `intake`, mas evita poluir um contrato genérico com comportamento específico da exportação da minuta.

- **Decisão:** usar arquivo temporário local antes do upload, em vez de estender imediatamente o port de storage para upload por bytes.
- **Alternativas consideradas:** mudar `FileStorageProvider` para aceitar `bytes`; usar SDK do storage diretamente no `UseCase`.
- **Motivo da escolha:** o contrato atual de `FileStorageProvider.upload_files(...)` já existe e há referência concreta no job de dataset para fluxo local -> upload -> limpeza.
- **Impactos / trade-offs:** introduz etapa de escrita local temporária na infraestrutura; em troca, evita expandir um port compartilhado que impactaria múltiplos adaptadores.

- **Decisão:** validar completude da minuta no `UseCase` antes da geração do arquivo.
- **Alternativas consideradas:** confiar apenas na validação do `PUT` de edição manual; exportar mesmo com seções vazias; validar apenas no provider.
- **Motivo da escolha:** a minuta pode ter sido gerada por fluxos antigos, IA ou dados legados; a precondição de exportação precisa ser garantida sobre o estado persistido real.
- **Impactos / trade-offs:** o fluxo ganha uma verificação extra de domínio e um erro `422` específico; em troca, evita gerar arquivo inconsistente.

# 9. Diagramas e Referências

- **Fluxo de dados:**

```text
HTTP POST /intake/analyses/{analysis_id}/petition-drafts/docx
  -> Auth middleware
  -> AnalysesRouter
  -> ExportPetitionDraftDocxController
  -> IntakePipe.verify_analysis_by_account_from_request(...)
  -> DatabasePipe.get_analyses_repository_from_request(...)
  -> DatabasePipe.get_petition_drafts_repository_from_request(...)
  -> ProvidersPipe.get_petition_draft_docx_provider()
  -> ExportPetitionDraftDocxUseCase.execute(analysis_id)
       -> AnalysesRepository.find_by_id(...)
       -> PetitionDraftsRepository.find_by_analysis_id(...)
       -> validate draft completeness
       -> PetitionDraftDocxProvider.export(...)
            -> build local_file_path
            -> build bucket_file_path
            -> python-docx Document()
            -> FileStorageProvider.upload_files([bucket_file_path])
            -> delete local temp file
       -> AnalysisDocumentDto(analysis_id, uploaded_at, file_path, name)
  -> Response JSON 201
```

- **Fluxo assíncrono (se aplicável):** **Não aplicável**.

- **Referências:**
  - `src/animus/rest/controllers/intake/get_petition_draft_controller.py`
  - `src/animus/rest/controllers/intake/update_petition_draft_controller.py`
  - `src/animus/core/intake/use_cases/get_petition_draft_use_case.py`
  - `src/animus/core/intake/use_cases/update_petition_draft_use_case.py`
  - `src/animus/core/storage/use_cases/generate_petition_upload_url_use_case.py`
  - `src/animus/core/storage/interfaces/file_storage_provider.py`
  - `src/animus/providers/storage/document/docx/python_docx_provider.py`
  - `src/animus/pubsub/inngest/jobs/intake/seed_analyses_precedents_dataset_job.py`
  - `src/animus/pipes/providers_pipe.py`
  - `src/animus/routers/intake/analyses_router.py`

# 10. Pendências / Dúvidas

**Sem pendências**.
