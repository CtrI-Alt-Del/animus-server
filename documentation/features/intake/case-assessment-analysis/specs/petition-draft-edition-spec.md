---
title: Edição manual da minuta de petição inicial
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AYDsAg
ticket: N/A
status: open
last_updated_at: 2026-06-04
---

# 1. Objetivo

Implementar a edição manual síncrona da `PetitionDraft` de análises `CASE_ASSESSMENT`, expondo um endpoint idempotente para sobrescrever a minuta persistida com o conteúdo completo enviado pelo app. A entrega deve reutilizar o contrato estruturado já existente de `PetitionDraftDto`, preservar a autorização por ownership da análise, impedir salvamento com campos vazios e manter o restante do pipeline assíncrono de geração e regeração inalterado.

# 2. Escopo

## 2.1 In-scope

- Criar endpoint HTTP para salvar a versão editada da `petition draft`.
- Validar que `structured_facts`, `legal_grounds` e `central_thesis` não sejam vazios.
- Validar que `requests` e `precedent_citations` não sejam listas vazias nem contenham itens vazios.
- Reutilizar `PetitionDraftDto`, `PetitionDraft`, `PetitionDraftsRepository.replace(...)` e `SqlalchemyPetitionDraftsRepository`.
- Exigir que a minuta já exista para a análise antes de permitir edição.
- Registrar o novo controller no router de `intake`.

## 2.2 Out-of-scope

- Exportação da minuta em `DOCX`.
- Mudanças na UI/mobile, debounce, feedback visual de autosave ou share sheet.
- Alterações no fluxo de geração inicial ou regeração da minuta.
- Alterações no schema da tabela `petition_drafts`.
- Versionamento de minutas, histórico de edições ou edição colaborativa.
- Suporte a edição manual de `CaseSummary` ou de minuta de sentença.

# 3. Requisitos

## 3.1 Funcionais

- O backend deve expor `PUT /intake/analyses/{analysis_id}/petition-drafts`.
- O endpoint deve receber no body o contrato completo de `PetitionDraftDto` (`src/animus/core/intake/domain/structures/dtos/petition_draft_dto.py`), exceto por `analysis_id`, que deve continuar vindo do path param `analysis_id`.
- O endpoint deve retornar `200 OK` com `PetitionDraftDto` representando o estado persistido após a edição.
- O endpoint deve exigir autenticação e ownership via `IntakePipe.verify_analysis_by_account_from_request(...)`.
- A edição só deve ser permitida para análises do tipo `CASE_ASSESSMENT`.
- A edição deve falhar com `404` quando a análise não possuir `PetitionDraft` persistida.
- O salvamento deve sobrescrever integralmente o conteúdo anterior da minuta.
- O salvamento não deve alterar o status da análise.
- O `GET /intake/analyses/{analysis_id}/petition-drafts` deve refletir imediatamente o conteúdo salvo pelo `PUT`.

## 3.2 Não funcionais

- **Segurança:** o endpoint deve reutilizar `IntakePipe.verify_analysis_by_account_from_request(...)`; nenhuma decisão de ownership deve depender apenas do body.
- **Idempotência:** chamadas repetidas de `PUT` com o mesmo payload devem produzir o mesmo estado persistido.
- **Compatibilidade retroativa:** não deve haver mudança no contrato de `PetitionDraftDto`, na tabela `petition_drafts` nem nos eventos/jobs de geração e regeração.
- **Validação:** a resposta de erro para campos vazios deve continuar no contrato HTTP de validação já usado pela borda `FastAPI` (`422`).

# 4. O que já existe?

## Core

- **`PetitionDraft`** (`src/animus/core/intake/domain/structures/petition_draft.py`) — structure de domínio já estruturada com `structured_facts`, `legal_grounds`, `central_thesis`, `requests` e `precedent_citations`.
- **`PetitionDraftDto`** (`src/animus/core/intake/domain/structures/dtos/petition_draft_dto.py`) — DTO estável já usado na geração, regeração, persistência e leitura da minuta.
- **`PetitionDraftsRepository`** (`src/animus/core/intake/interfaces/petition_drafts_repository.py`) — port com `find_by_analysis_id(...)`, `add(...)` e `replace(...)`.
- **`CreatePetitionDraftUseCase`** (`src/animus/core/intake/use_cases/create_petition_draft_use_case.py`) — referência de persistência da minuta; não pode ser reutilizado diretamente porque força status `DONE` e aceita criação quando a minuta não existe.
- **`GetPetitionDraftUseCase`** (`src/animus/core/intake/use_cases/get_petition_draft_use_case.py`) — referência de leitura protegida por ownership e de uso de `PetitionDraftUnavailableError`.
- **`TriggerPetitionDraftRegenerationUseCase`** (`src/animus/core/intake/use_cases/trigger_petition_draft_regeneration_use_case.py`) — referência de fluxo que trata `PetitionDraft` como recurso já existente e separado da geração inicial.
- **`PetitionDraftUnavailableError`** (`src/animus/core/intake/domain/errors/petition_draft_unavailable_error.py`) — erro `NotFoundError` já alinhado ao cenário em que a minuta ainda não existe.
- **`AnalysisNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_not_found_error.py`) — erro para análise inexistente.
- **`InconsistentAnalysisTypeError`** (`src/animus/core/intake/domain/errors/inconsistent_analysis_type_error.py`) — erro já usado quando o tipo da análise é incompatível com o fluxo.

## Database

- **`PetitionDraftModel`** (`src/animus/database/sqlalchemy/models/intake/petition_draft_model.py`) — model da tabela `petition_drafts`, já com colunas estruturadas e sem necessidade de migração.
- **`PetitionDraftMapper`** (`src/animus/database/sqlalchemy/mappers/intake/petition_draft_mapper.py`) — mapper entre `PetitionDraftModel` e `PetitionDraft`.
- **`SqlalchemyPetitionDraftsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_drafts_repository.py`) — implementação concreta; `replace(...)` já sobrescreve todos os campos estruturados da minuta.
- **Seeders da camada database:** `src/animus/database/sqlalchemy/seeders/intake_seeder.py` existe, mas não semeia `petition_drafts`; não há impacto em `seeders` nem em novos paths persistidos/gerados.

## REST

- **`GetPetitionDraftController`** (`src/animus/rest/controllers/intake/get_petition_draft_controller.py`) — referência de recurso `petition-drafts` e de `response_model=PetitionDraftDto`.
- **`TriggerPetitionDraftRegenerationController`** (`src/animus/rest/controllers/intake/trigger_petition_draft_regeneration_controller.py`) — referência de `_Body` com `field_validator(...)` e de rota relacionada ao mesmo recurso.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) — já traduz `ValidationError`, `NotFoundError` e `ForbiddenError`; não requer novo handler para esta feature.

## Routers

- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) — composition root que registra todos os controllers de análises do módulo `intake`, incluindo `GetPetitionDraftController` e triggers de minuta.

## Pipes

- **`IntakePipe.verify_analysis_by_account_from_request(...)`** (`src/animus/pipes/intake_pipe.py`) — guard de ownership já utilizado pelos endpoints de `intake` por `analysis_id`.
- **`DatabasePipe.get_petition_drafts_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP já pronto para `PetitionDraftsRepository`.
- **`DatabasePipe.get_analyses_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP já pronto para `AnalysesRepository`.

# 5. O que deve ser criado?

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/update_petition_draft_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `AnalysesRepository`, `PetitionDraftsRepository`
- **Método principal:** `execute(analysis_id: str, dto: PetitionDraftDto) -> PetitionDraftDto` — valida contexto mínimo da análise, exige que a minuta já exista, sobrescreve o registro persistido e retorna o DTO salvo.
- **Fluxo resumido:**
  - Normaliza `analysis_id` como `Id`.
  - Reconstrói `PetitionDraftDto` com `analysis_id` vindo do path param para evitar divergência entre path e body.
  - Busca `Analysis`; se ausente, lança `AnalysisNotFoundError`.
  - Se `analysis.type.is_case_analysis.is_false`, lança `InconsistentAnalysisTypeError`.
  - Busca `PetitionDraft` existente por `analysis_id`; se ausente, lança `PetitionDraftUnavailableError`.
  - Cria `PetitionDraft` a partir do DTO normalizado.
  - Persiste via `PetitionDraftsRepository.replace(...)`.
  - Retorna `petition_draft.dto`.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/update_petition_draft_controller.py` (**novo arquivo**)
- **`_Body`:** schema Pydantic no mesmo arquivo, com:
  - `structured_facts: str`
  - `legal_grounds: str`
  - `central_thesis: str`
  - `requests: list[str]`
  - `precedent_citations: list[str]`
- **Validações relevantes do `_Body`:**
  - rejeitar `structured_facts`, `legal_grounds` e `central_thesis` quando `value.strip() == ''`;
  - rejeitar `requests` e `precedent_citations` quando vazias;
  - rejeitar itens de lista cujo `item.strip() == ''`;
  - expor erros por campo no `422`, sem criar envelope de erro customizado.
- **Método auxiliar do `_Body`:** `to_dto(analysis_id: str) -> PetitionDraftDto` — monta o DTO de saída para o `UseCase`, preservando o contrato já existente da camada `core`.
- **Método HTTP e path:** `PUT /analyses/{analysis_id}/petition-drafts`
- **`status_code`:** `200`
- **`response_model`:** `PetitionDraftDto`
- **Dependências injetadas via `Depends`:** `IntakePipe.verify_analysis_by_account_from_request(...)`, `DatabasePipe.get_analyses_repository_from_request(...)`, `DatabasePipe.get_petition_drafts_repository_from_request(...)`
- **Fluxo:** `_Body.to_dto(analysis.id.value)` → `UpdatePetitionDraftUseCase.execute(...)` → `PetitionDraftDto`

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** exportar `UpdatePetitionDraftUseCase`.
- **Justificativa:** manter o `composition root` e imports públicos do contexto `intake` consistentes com o padrão do projeto.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** exportar `UpdatePetitionDraftController`.
- **Justificativa:** estabilizar imports públicos dos controllers de `intake`.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** registrar `UpdatePetitionDraftController.handle(router)` no mesmo agrupamento do recurso `petition-drafts`.
- **Justificativa:** anexar o novo endpoint ao router correto, preservando a organização por contexto.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_drafts_repository.py`
- **Mudança:** **Não aplicável**.
- **Justificativa:** `replace(...)` já sobrescreve todos os campos necessários da minuta.

## Pipes

- **Arquivo:** `src/animus/pipes/database_pipe.py`
- **Mudança:** **Não aplicável**.
- **Justificativa:** os providers de `AnalysesRepository` e `PetitionDraftsRepository` já existem e cobrem o wiring necessário.

## Migrações Alembic

- **Arquivo:** `migrations/versions/`
- **Mudança:** **Não aplicável**.
- **Justificativa:** o schema atual de `petition_drafts` já suporta os campos editáveis persistidos.

# 7. O que deve ser removido?

**Não aplicável**.

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** usar `PUT /intake/analyses/{analysis_id}/petition-drafts` como endpoint de salvamento.
- **Alternativas consideradas:** `PATCH /.../petition-drafts`; `PUT /.../petition-draft`.
- **Motivo da escolha:** o app envia o draft completo a cada autosave, o contrato atual já trata a minuta como um recurso único por análise, e a codebase já usa o plural `petition-drafts` no `GET` e no trigger de regeração.
- **Impactos / trade-offs:** o endpoint fica naturalmente idempotente e consistente com o recurso existente; em contrapartida, não oferece atualização parcial por seção.

- **Decisão:** criar `UpdatePetitionDraftUseCase` em vez de reutilizar `CreatePetitionDraftUseCase`.
- **Alternativas consideradas:** reutilizar `CreatePetitionDraftUseCase`; mover a edição diretamente para o controller.
- **Motivo da escolha:** `CreatePetitionDraftUseCase` altera status para `DONE` e aceita criação quando não há minuta, o que diverge do requisito de edição manual; manter um `UseCase` dedicado preserva a regra fora da borda HTTP.
- **Impactos / trade-offs:** adiciona um artefato novo no `core`, mas evita branchs condicionais e regressões em fluxos assíncronos já existentes.

- **Decisão:** validar campos vazios no `_Body` do controller, não em `PetitionDraft` ou `Text`.
- **Alternativas consideradas:** endurecer `PetitionDraft.create(...)`; endurecer `Text.create(...)`; criar erro de domínio específico para edição inválida.
- **Motivo da escolha:** a codebase atual não impõe invariantes de não vazio em `Text.create(...)`, e endurecer o domínio teria efeito colateral nos fluxos existentes de geração/regeração. A exigência de não vazio é estritamente necessária para este contrato HTTP.
- **Impactos / trade-offs:** a validação fica concentrada na borda e retorna `422` com erro por campo; por outro lado, outros produtores internos de `PetitionDraftDto` continuam livres para gerar strings vazias, o que deve ser reavaliado apenas se o domínio passar a exigir essa invariável de forma global.

- **Decisão:** reutilizar `PetitionDraftUnavailableError` para o caso de edição sem minuta prévia.
- **Alternativas consideradas:** criar erro novo específico para edição manual indisponível.
- **Motivo da escolha:** o significado de domínio é o mesmo: a análise ainda não possui minuta persistida.
- **Impactos / trade-offs:** reduz novos nomes e mantém o contrato `404` coerente com o `GET`; a mensagem de erro permanece genérica, não específica de “edição”.

# 9. Diagramas e Referências

- **Fluxo de dados:**

```text
HTTP PUT /intake/analyses/{analysis_id}/petition-drafts
  -> Auth middleware
  -> AnalysesRouter
  -> UpdatePetitionDraftController
  -> IntakePipe.verify_analysis_by_account_from_request(...)
  -> DatabasePipe.get_analyses_repository_from_request(...)
  -> DatabasePipe.get_petition_drafts_repository_from_request(...)
  -> UpdatePetitionDraftUseCase.execute(analysis_id, dto)
  -> AnalysesRepository.find_by_id(...)
  -> PetitionDraftsRepository.find_by_analysis_id(...)
  -> PetitionDraftsRepository.replace(...)
  -> SqlalchemyPetitionDraftsRepository
  -> PetitionDraftModel / PostgreSQL (petition_drafts)
  -> PetitionDraftDto
  -> Response JSON 200
```

- **Fluxo assíncrono (se aplicável):** **Não aplicável**.

- **Referências:**
  - `src/animus/rest/controllers/intake/get_petition_draft_controller.py`
  - `src/animus/rest/controllers/intake/trigger_petition_draft_regeneration_controller.py`
  - `src/animus/core/intake/use_cases/create_petition_draft_use_case.py`
  - `src/animus/core/intake/use_cases/get_petition_draft_use_case.py`
  - `src/animus/core/intake/use_cases/trigger_petition_draft_regeneration_use_case.py`
  - `src/animus/core/intake/domain/structures/petition_draft.py`
  - `src/animus/core/intake/domain/structures/dtos/petition_draft_dto.py`
  - `src/animus/core/intake/interfaces/petition_drafts_repository.py`
  - `src/animus/database/sqlalchemy/models/intake/petition_draft_model.py`
  - `src/animus/database/sqlalchemy/mappers/intake/petition_draft_mapper.py`
  - `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_drafts_repository.py`
  - `src/animus/routers/intake/analyses_router.py`

# 10. Pendências / Dúvidas

**Sem pendências**.
