---
title: Exportação da minuta de sentença da análise de 2ª instância em DOCX
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AQDxAg
ticket: N/A
status: open
last_updated_at: 2026-06-05
---

# 1. Objetivo

Implementar a exportação síncrona da minuta persistida de análises `SECOND_INSTANCE` em arquivo `DOCX`, expondo um endpoint HTTP que reutiliza a minuta, a descrição da decisão pretendida e os precedentes escolhidos já persistidos, gera o documento com `python-docx`, faz upload do arquivo para o storage já configurado no projeto e retorna `AnalysisDocumentDto`, sem alterar o fluxo assíncrono de geração/regeração da minuta, sem criar registro em `analysis_documents` e sem introduzir mudanças de banco.

# 2. Escopo

## 2.1 In-scope

- Criar `ExportSecondInstanceJudgmentDraftDocxUseCase` no `core/intake`.
- Criar a port `SecondInstanceJudgmentDraftDocxProvider` no `core/intake/interfaces`.
- Criar provider concreto com `python-docx` na camada `providers`.
- Expor `POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts/docx`.
- Reutilizar `SecondInstanceJudgmentDraft`, `SecondInstanceDecision`, `AnalysisPrecedent` e `AnalysisDocumentDto`.
- Incluir no arquivo exportado a decisão pretendida, a minuta completa e os precedentes escolhidos da análise.
- Reaproveitar a validação de ownership via `IntakePipe.verify_analysis_by_account_from_request`.
- Salvar o arquivo gerado no storage remoto em path dedicado de exportação de minuta.

## 2.2 Out-of-scope

- Exportação da minuta em `PDF`.
- Alterações nos fluxos assíncronos de geração ou regeração da minuta.
- Persistência do export em `analysis_documents` ou criação de tabela específica para exports.
- Versionamento histórico de arquivos exportados.
- Alterações nos relatórios `CASE_ASSESSMENT`, `FIRST_INSTANCE` ou `SECOND_INSTANCE` em JSON.
- Mudanças em mobile, `share sheet` ou download no cliente.
- Alterações no fluxo de exportação da minuta de petição já existente.

# 3. Requisitos

## 3.1 Funcionais

- O endpoint de exportação deve ser `POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts/docx`.
- O endpoint deve aceitar apenas análises existentes, da conta autenticada e do tipo `SECOND_INSTANCE`.
- A exportação deve falhar com `404` quando a minuta ainda não existir para a análise.
- A exportação deve falhar quando a descrição da decisão de 2ª instância não existir para a análise.
- A exportação deve falhar quando não houver precedentes escolhidos (`is_chosen = True`) para compor a seção de precedentes do documento.
- A exportação deve validar que `report`, `merit_analysis`, `precedent_adherence_analysis` e `ruling` da minuta persistida continuam preenchidos; campos opcionais continuam não bloqueantes.
- O documento gerado deve conter, nesta ordem, cabeçalho, descrição da decisão pretendida, seções da minuta persistida, lista de precedentes escolhidos e aviso de ausência de precedente aplicável quando a minuta o trouxer preenchido.
- O endpoint deve retornar `AnalysisDocumentDto` com `analysis_id`, `uploaded_at`, `file_path` e `name`.
- O arquivo deve ser salvo no bucket em path específico de exportação de minuta de 2ª instância.
- O conteúdo exportado deve refletir a última versão persistida da minuta, incluindo edições manuais e regerações.

## 3.2 Não funcionais

- **Segurança:** o endpoint deve exigir autenticação Bearer e ownership check por `IntakePipe.verify_analysis_by_account_from_request(...)`.
- **Compatibilidade retroativa:** a feature não deve alterar os contratos HTTP de `GET /intake/analyses/{analysis_id}/second-instance-judgment-drafts`, `PUT /intake/analyses/{analysis_id}/second-instance-judgment-drafts`, `POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts` nem `GET /intake/analyses/{analysis_id}/second-instance-report`.
- **Compatibilidade de persistência:** não deve haver migration, alteração em tabela existente nem criação de registro em `analysis_documents`.
- **Resiliência:** a geração deve usar arquivo temporário local com limpeza no mesmo fluxo síncrono e delegar o upload ao `FileStorageProvider`, sem `commit` manual em controller, provider ou repository.
- **Observabilidade:** a exportação não deve publicar eventos nem alterar `analyses.status`; o único artefato novo é o arquivo gerado no storage.

# 4. O que já existe?

## Core

- **`SecondInstanceJudgmentDraft`** (`src/animus/core/intake/domain/structures/second_instance_judgment_draft.py`) — structure persistida da minuta com os campos obrigatórios e opcionais que compõem o corpo do documento.
- **`SecondInstanceJudgmentDraftDto`** (`src/animus/core/intake/domain/structures/dtos/second_instance_judgment_draft_dto.py`) — DTO já usado para leitura, geração, regeração e edição manual da minuta.
- **`SecondInstanceDecision`** (`src/animus/core/intake/domain/structures/second_instance_decision.py`) — structure 1:1 que representa a descrição da decisão pretendida e deve compor o documento exportado.
- **`AnalysisPrecedent`** (`src/animus/core/intake/domain/structures/analysis_precedent.py`) — structure que já traz `precedent`, `synthesis`, `applicability_level`, `similarity_score` e `is_chosen` para montar a seção de precedentes do arquivo.
- **`AnalysisDocumentDto`** (`src/animus/core/intake/domain/structures/dtos/analysis_document_dto.py`) — contrato já usado pelo fluxo de exportação da minuta de petição para devolver metadados do arquivo gerado.
- **`SecondInstanceJudgmentDraftsRepository`** (`src/animus/core/intake/interfaces/judgment_drafts_repository.py`) — port existente para buscar a minuta persistida por `analysis_id`.
- **`SecondInstanceDecisionsRepository`** (`src/animus/core/intake/interfaces/second_instance_decisions_repository.py`) — port existente para buscar a decisão persistida por `analysis_id`.
- **`AnalysisPrecedentsRepository`** (`src/animus/core/intake/interfaces/analysis_precedents_repository.py`) — port já usado pelo relatório e pela geração da minuta para recuperar precedentes da análise.
- **`AnalysesRepository`** (`src/animus/core/intake/interfaces/analyses_repository.py`) — port necessário para validar existência, tipo e obter o nome da análise para o arquivo.
- **`GetSecondInstanceJudgmentDraftUseCase`** (`src/animus/core/intake/use_cases/get_second_instance_judgment_draft_use_case.py`) — referência de leitura da minuta persistida com `SecondInstanceJudgmentDraftUnavailableError` quando ausente.
- **`UpdateSecondInstanceJudgmentDraftUseCase`** (`src/animus/core/intake/use_cases/update_second_instance_judgment_draft_use_case.py`) — confirma que a última versão persistida pode vir tanto de edição manual quanto de fluxo assíncrono.
- **`GetSecondInstanceAnalysisReportUseCase`** (`src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`) — referência de agregação de decisão, minuta e precedentes escolhidos para o contexto de 2ª instância.
- **`ExportPetitionDraftDocxUseCase`** (`src/animus/core/intake/use_cases/export_petition_draft_docx_use_case.py`) — implementação análoga mais próxima para validar completude do draft e delegar a geração do arquivo a um provider especializado.
- **`ChosenAnalysisPrecedentsRequiredError`** (`src/animus/core/intake/domain/errors/chosen_analysis_precedents_required_error.py`) — erro existente adequado para bloquear export quando não houver precedentes escolhidos.
- **`SecondInstanceJudgmentDraftUnavailableError`** (`src/animus/core/intake/domain/errors/judgment_draft_unavailable_error.py`) — erro já usado quando a minuta ainda não existe.
- **`SecondInstanceDecisionNotFoundError`** (`src/animus/core/intake/domain/errors/second_instance_decision_not_found_error.py`) — erro já usado quando a decisão pretendida ainda não foi persistida.
- **`SecondInstanceAnalysisRequiredError`** (`src/animus/core/intake/domain/errors/second_instance_analysis_required_error.py`) — erro existente para tipo de análise incompatível.

## Database

- **`SqlalchemySecondInstanceJudgmentDraftsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`) — implementação concreta da port de minuta, com `find_by_analysis_id(...)` e `replace(...)` sem controle manual de transação.
- **`SqlalchemySecondInstanceDecisionsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_second_instance_decisions_repository.py`) — implementação concreta da port de decisão pretendida.
- **Seeders da camada database:** não aplicável; não há seeder específico para exportação de minuta e a feature não exige dados iniciais nem novos arquivos persistidos pela camada `database`.

## REST

- **`GetSecondInstanceJudgmentDraftController`** (`src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`) — define o recurso HTTP já existente da minuta persistida.
- **`UpdateSecondInstanceJudgmentDraftController`** (`src/animus/rest/controllers/intake/update_second_instance_judgment_draft_controller.py`) — reforça que a exportação deve refletir a última minuta persistida no mesmo recurso plural.
- **`GetSecondInstanceDecisionController`** (`src/animus/rest/controllers/intake/get_second_instance_decision_controller.py`) — referência de acesso fino à decisão pretendida por análise.
- **`ExportPetitionDraftDocxController`** (`src/animus/rest/controllers/intake/export_petition_draft_docx_controller.py`) — principal referência de endpoint `POST` síncrono que retorna `AnalysisDocumentDto` e injeta provider especializado via `ProvidersPipe`.

## Routers

- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) — router oficial que já registra o endpoint de exportação da minuta de petição e os endpoints de minuta de 2ª instância; deve registrar o endpoint novo no mesmo contexto.

## Pipes

- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) — já fornece `AnalysesRepository`, `SecondInstanceJudgmentDraftsRepository`, `SecondInstanceDecisionsRepository` e `AnalysisPrecedentsRepository` via `Depends(...)`.
- **`ProvidersPipe`** (`src/animus/pipes/providers_pipe.py`) — já provê `PetitionDraftDocxProvider`, `FileStorageProvider` e `PdfProvider`; é o ponto correto para adicionar o provider concreto novo de exportação em `DOCX`.
- **`IntakePipe`** (`src/animus/pipes/intake_pipe.py`) — ownership check reutilizado pela feature.

## Providers

- **`PythonDocxPetitionDraftProvider`** (`src/animus/providers/storage/document/docx/python_docx_petition_draft_provider.py`) — referência direta de provider que gera `DOCX`, salva em arquivo temporário, copia para o path de upload, aciona `FileStorageProvider.upload_files(...)` e retorna `AnalysisDocumentDto`.
- **`FileStorageProvider`** (`src/animus/core/storage/interfaces/file_storage_provider.py`) — port existente para upload no storage remoto.

# 5. O que deve ser criado?

## Camada Core (Erros de Domínio)

- **Localização:** `src/animus/core/intake/domain/errors/second_instance_judgment_draft_export_incomplete_error.py` (**novo arquivo**)
- **Classe base:** `ValidationError`
- **Motivo:** levantar quando a minuta persistida existir, mas algum campo obrigatório para exportação (`report`, `merit_analysis`, `precedent_adherence_analysis`, `ruling`) estiver ausente, vazio ou contiver item inválido.

## Camada Core (Interfaces / Ports)

- **Localização:** `src/animus/core/intake/interfaces/second_instance_judgment_draft_docx_provider.py` (**novo arquivo**)
- **Métodos:**
  - `export(analysis_id: str, analysis_name: str, judgment_draft: SecondInstanceJudgmentDraft, second_instance_decision: SecondInstanceDecision, precedents: list[AnalysisPrecedent]) -> AnalysisDocumentDto` — gera o `DOCX`, faz upload no storage e retorna os metadados do arquivo exportado.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/export_second_instance_judgment_draft_docx_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `AnalysesRepository`, `SecondInstanceJudgmentDraftsRepository`, `SecondInstanceDecisionsRepository`, `AnalysisPrecedentsRepository`, `SecondInstanceJudgmentDraftDocxProvider`
- **Método principal:** `execute(analysis_id: str) -> AnalysisDocumentDto` — valida a análise, garante a existência e a completude da minuta persistida, garante decisão pretendida e precedentes escolhidos e delega a geração do `DOCX` ao provider.
- **Fluxo resumido:**
  - Normaliza `analysis_id` como `Id`.
  - Busca `Analysis`; se ausente, lança `AnalysisNotFoundError`.
  - Valida `analysis.type.is_second_instance`; se falso, lança `SecondInstanceAnalysisRequiredError`.
  - Busca `SecondInstanceJudgmentDraft`; se ausente, lança `SecondInstanceJudgmentDraftUnavailableError`.
  - Valida os campos obrigatórios da minuta persistida; se houver faltas, lança `SecondInstanceJudgmentDraftExportIncompleteError` com a lista de campos inválidos.
  - Busca `SecondInstanceDecision`; se ausente, lança `SecondInstanceDecisionNotFoundError`.
  - Busca precedentes por `analysis_id`, filtra `is_chosen = True` e, se a lista ficar vazia, lança `ChosenAnalysisPrecedentsRequiredError`.
  - Chama `SecondInstanceJudgmentDraftDocxProvider.export(...)` com `analysis.id.value`, `analysis.name.value`, `judgment_draft`, `second_instance_decision` e `classified_precedents`.
  - Retorna `AnalysisDocumentDto`.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/export_second_instance_judgment_draft_docx_controller.py` (**novo arquivo**)
- **`*Body`:** não aplicável.
- **Método HTTP e path:** `POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts/docx`
- **`status_code`:** `201`
- **`response_model`:** `AnalysisDocumentDto`
- **Dependências injetadas via `Depends`:**
  - `IntakePipe.verify_analysis_by_account_from_request`
  - `DatabasePipe.get_analyses_repository_from_request`
  - `DatabasePipe.get_judgment_drafts_repository_from_request`
  - `DatabasePipe.get_second_instance_decisions_repository_from_request`
  - `DatabasePipe.get_analysis_precedents_repository_from_request`
  - `ProvidersPipe.get_second_instance_judgment_draft_docx_provider`
- **Fluxo:** análise validada pelo `IntakePipe` → `ExportSecondInstanceJudgmentDraftDocxUseCase.execute(analysis_id=analysis.id.value)` → `AnalysisDocumentDto`

## Camada Providers

- **Localização:** `src/animus/providers/storage/document/docx/python_docx_second_instance_judgment_draft_provider.py` (**novo arquivo**)
- **Interface implementada (port):** `SecondInstanceJudgmentDraftDocxProvider`
- **Biblioteca/SDK utilizado:** `python-docx` + `FileStorageProvider`
- **Métodos:**
  - `__init__(file_storage_provider: FileStorageProvider) -> None` — recebe o provider de storage concreto.
  - `export(analysis_id: str, analysis_name: str, judgment_draft: SecondInstanceJudgmentDraft, second_instance_decision: SecondInstanceDecision, precedents: list[AnalysisPrecedent]) -> AnalysisDocumentDto` — monta o documento, grava temporariamente em `.docx`, envia para o storage e retorna o DTO de saída.
  - `_build_document(judgment_draft: SecondInstanceJudgmentDraft, second_instance_decision: SecondInstanceDecision, precedents: list[AnalysisPrecedent], analysis_name: str, generated_at: str) -> DocxDocument` — organiza o conteúdo do documento na ordem definida pela feature.
  - `_build_file_name(analysis_name: str) -> str` — normaliza o nome da análise para um nome de arquivo estável em `snake/kebab` compatível com o storage.
- **Path persistido gerado:** `intake/analyses/{analysis_id}/second-instance-judgment-draft-exports/{sanitized_analysis_name}-minuta-sentenca.docx`
- **Estrutura do documento gerado:**
  - Cabeçalho com nome da análise e data/hora de geração.
  - Seção `Descrição da decisão pretendida` com `SecondInstanceDecision.description`.
  - Seção `Questões preliminares` quando `judgment_draft.preliminary_issues` existir.
  - Seção `Relatório` com `judgment_draft.report`.
  - Seção `Fundamentação` com `judgment_draft.merit_analysis`.
  - Seção `Análise de aderência ou distinção` com `judgment_draft.precedent_adherence_analysis`.
  - Seção `Dispositivo sugerido` com cada item de `judgment_draft.ruling` em lista.
  - Seção `Precedentes associados` com um bloco por precedente escolhido contendo tribunal, tipo, número, questão, status, tese firmada quando houver, percentual de aplicabilidade, nível de classificação e síntese explicativa quando houver.
  - Seção `Aviso de ausência de precedente aplicável` somente quando `judgment_draft.no_applicable_precedent_notice` existir.

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudança:** importar e exportar `SecondInstanceJudgmentDraftDocxProvider`.
- **Justificativa:** manter a surface pública das ports de `intake` consistente com o padrão já usado por `PetitionDraftDocxProvider`.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** importar e exportar `ExportSecondInstanceJudgmentDraftDocxUseCase`.
- **Justificativa:** manter o padrão de exports públicos dos use cases do contexto `intake`.

- **Arquivo:** `src/animus/core/intake/domain/errors/__init__.py`
- **Mudança:** importar e exportar `SecondInstanceJudgmentDraftExportIncompleteError`.
- **Justificativa:** expor o novo erro de domínio no agregador oficial de erros do contexto.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** importar e exportar `ExportSecondInstanceJudgmentDraftDocxController`.
- **Justificativa:** manter os controllers de `intake` centralizados no agregador público da camada.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** registrar `ExportSecondInstanceJudgmentDraftDocxController.handle(router)` próximo aos demais endpoints de minuta de 2ª instância.
- **Justificativa:** expor o endpoint no router oficial de análises e preservar a organização por contexto do recurso.

## Pipes

- **Arquivo:** `src/animus/pipes/providers_pipe.py`
- **Mudança:** adicionar `get_second_instance_judgment_draft_docx_provider() -> SecondInstanceJudgmentDraftDocxProvider`, instanciando o provider concreto novo com `ProvidersPipe.get_file_storage_provider()`.
- **Justificativa:** seguir o padrão atual de composição dos providers de exportação na borda HTTP.

## Providers

- **Arquivo:** `src/animus/providers/storage/document/docx/__init__.py`
- **Mudança:** exportar `PythonDocxSecondInstanceJudgmentDraftProvider`.
- **Justificativa:** manter o namespace `docx` consistente com os providers concretos disponíveis.

- **Arquivo:** `src/animus/providers/storage/document/__init__.py`
- **Mudança:** reexportar `PythonDocxSecondInstanceJudgmentDraftProvider`.
- **Justificativa:** preservar o padrão de agregação intermediária da camada `providers/storage/document`.

- **Arquivo:** `src/animus/providers/storage/__init__.py`
- **Mudança:** reexportar `PythonDocxSecondInstanceJudgmentDraftProvider`.
- **Justificativa:** permitir import centralizado do provider concreto no mesmo nível já usado por `PythonDocxPetitionDraftProvider`.

# 7. O que deve ser removido?

**Não aplicável**.

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** expor o endpoint novo em `POST /analyses/{analysis_id}/second-instance-judgment-drafts/docx`.
- **Alternativas consideradas:** usar `/export`, usar path singular dedicado ou reaproveitar `/second-instance-report`.
- **Motivo da escolha:** a codebase já usa `POST /analyses/{analysis_id}/petition-drafts/docx` para exportação síncrona de draft em `DOCX`; repetir o mesmo padrão reduz atrito de naming e evita introduzir um estilo novo de rota.
- **Impactos / trade-offs:** o endpoint fica acoplado ao formato `DOCX` no path, mas isso é consistente com o único fluxo análogo já implementado.

- **Decisão:** reutilizar `AnalysisDocumentDto` como resposta e não persistir o export em `analysis_documents`.
- **Alternativas consideradas:** criar DTO específico de exportação ou persistir cada arquivo exportado como `AnalysisDocument`.
- **Motivo da escolha:** a feature análoga de exportação da minuta de petição já devolve `AnalysisDocumentDto` sem nova persistência, e não há evidência de requisito para histórico de exports.
- **Impactos / trade-offs:** o arquivo fica disponível no storage, mas o backend não mantém catálogo relacional desses exports.

- **Decisão:** criar um provider dedicado `SecondInstanceJudgmentDraftDocxProvider` em vez de expandir `PetitionDraftDocxProvider`.
- **Alternativas consideradas:** generalizar o provider existente ou colocar a lógica de `python-docx` dentro do use case.
- **Motivo da escolha:** a minuta de sentença tem estrutura, dependências e conteúdo diferentes da minuta de petição; separar providers mantém responsabilidade única e evita condicionais de tipo dentro do exportador.
- **Impactos / trade-offs:** adiciona uma port e um provider concretos novos, mas preserva clareza arquitetural e reuso do padrão já aceito no projeto.

- **Decisão:** validar completude do draft no use case antes de chamar o provider.
- **Alternativas consideradas:** confiar apenas nas validações existentes da structure ou deixar falhas explodirem durante a montagem do documento.
- **Motivo da escolha:** o fluxo análogo `ExportPetitionDraftDocxUseCase` já faz uma checagem explícita de completude antes do provider; repetir o padrão mantém a borda previsível e devolve erro de domínio mais claro.
- **Impactos / trade-offs:** há validação parcialmente redundante com a structure, mas o comportamento de exportação fica explícito e mais fácil de revisar.

- **Decisão:** exportar apenas precedentes escolhidos (`is_chosen = True`).
- **Alternativas consideradas:** exportar todos os precedentes recuperados ou depender do relatório JSON para uma filtragem indireta.
- **Motivo da escolha:** `GetSecondInstanceAnalysisReportUseCase` já filtra os precedentes para o conjunto escolhido, e a geração/regeração da minuta também parte dessa seleção curada pelo usuário.
- **Impactos / trade-offs:** precedentes não escolhidos ficam fora do arquivo, mas o documento permanece aderente ao estado final da análise usado para a minuta.

- **Decisão:** manter o arquivo em path estável por análise, com nome sanitizado, em vez de gerar identificador único por exportação.
- **Alternativas consideradas:** gerar `file_id` único a cada chamada ou persistir timestamp no nome final.
- **Motivo da escolha:** o provider análogo de minuta de petição já usa nome estável baseado na análise; seguir esse padrão produz implementação menor e consistente.
- **Impactos / trade-offs:** exports sucessivos tendem a sobrescrever o mesmo objeto no storage, o que simplifica o fluxo, mas elimina histórico de versões exportadas.

# 9. Diagramas e Referências

- **Fluxo de dados:**

```text
HTTP POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts/docx
-> Auth middleware
-> AnalysesRouter
-> ExportSecondInstanceJudgmentDraftDocxController
-> IntakePipe.verify_analysis_by_account_from_request
-> DatabasePipe.get_analyses_repository_from_request
-> DatabasePipe.get_judgment_drafts_repository_from_request
-> DatabasePipe.get_second_instance_decisions_repository_from_request
-> DatabasePipe.get_analysis_precedents_repository_from_request
-> ProvidersPipe.get_second_instance_judgment_draft_docx_provider
-> ExportSecondInstanceJudgmentDraftDocxUseCase.execute(...)
-> AnalysesRepository.find_by_id(...)
-> SecondInstanceJudgmentDraftsRepository.find_by_analysis_id(...)
-> SecondInstanceDecisionsRepository.find_by_analysis_id(...)
-> AnalysisPrecedentsRepository.find_many_by_analysis_id(...)
-> SecondInstanceJudgmentDraftDocxProvider.export(...)
-> FileStorageProvider.upload_files(...)
-> GCS
-> AnalysisDocumentDto
-> Response 201 JSON
```

- **Fluxo assíncrono (se aplicável):** não aplicável; a exportação é síncrona e não publica eventos.

- **Referências:**
  - `src/animus/core/intake/use_cases/export_petition_draft_docx_use_case.py`
  - `src/animus/rest/controllers/intake/export_petition_draft_docx_controller.py`
  - `src/animus/providers/storage/document/docx/python_docx_petition_draft_provider.py`
  - `src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`
  - `src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`
  - `src/animus/rest/controllers/intake/update_second_instance_judgment_draft_controller.py`
  - `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`
  - `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_second_instance_decisions_repository.py`

# 10. Pendências / Dúvidas

- **Descrição da pendência:** o PRD oficial em Confluence (`RF 08`) ainda descreve a exportação da minuta de 2ª instância em `PDF`, enquanto a decisão registrada nesta sessão foi seguir com exportação da minuta em `DOCX`.
- **Impacto na implementação:** a spec abaixo fica consistente com a codebase e com a decisão atual de produto, mas diverge do PRD como fonte oficial; sem atualizar o PRD, futuras implementações ou revisões podem reabrir a discussão de formato.
- **Ação sugerida:** alinhar o PRD no Confluence antes de iniciar a implementação para que a fonte de verdade passe a refletir `DOCX` para a minuta de 2ª instância.
Atualize o PRD
