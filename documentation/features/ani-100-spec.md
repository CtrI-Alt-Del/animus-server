---
title: Endpoint para consultar minuta de petição da análise
prd: https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/49053697
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-100
status: closed
last_updated_at: 2026-05-26
---

# 1. Objetivo

Implementar o endpoint autenticado `GET /intake/analyses/{analysis_id}/petition-drafts` para consultar exclusivamente a `PetitionDraft` persistida de uma análise de intake. A entrega deve criar um `GetPetitionDraftUseCase` dedicado, expor um contrato HTTP estável em `PetitionDraftDto`, validar existência e ownership da análise antes da leitura da minuta e reutilizar os contratos e adaptadores de persistência já existentes, sem alterar o fluxo assíncrono de geração da minuta.

---

# 2. Escopo

## 2.1 In-scope

- Criar caso de uso `GetPetitionDraftUseCase` no contexto `intake`.
- Criar controller `GetPetitionDraftController` para `GET /intake/analyses/{analysis_id}/petition-drafts`.
- Registrar o controller no router de análises.
- Reutilizar `AnalysesRepository` para validar existência e ownership da análise.
- Reutilizar `PetitionDraftsRepository.find_by_analysis_id(...)` para buscar a minuta persistida.
- Retornar `PetitionDraftDto` como contrato de resposta.
- Retornar erros de domínio já existentes para análise inexistente, acesso negado e minuta indisponível.

## 2.2 Out-of-scope

- Gerar, regerar ou alterar conteúdo da minuta.
- Alterar o job assíncrono de geração de `PetitionDraft`.
- Alterar estrutura da tabela `petition_drafts` ou criar migration.
- Criar schemas Pydantic adicionais em `validation/`.
- Agregar dados de relatório completo da análise.
- Alterar contratos dos endpoints de relatório, resumo do caso, precedentes ou geração de minuta.

---

# 3. Requisitos

## 3.1 Funcionais

- O endpoint deve retornar a `PetitionDraft` persistida para o `analysis_id` informado.
- O endpoint deve expor apenas os campos de `PetitionDraftDto`: `analysis_id`, `structured_facts`, `legal_grounds`, `central_thesis`, `requests` e `precedent_citations`.
- O endpoint deve seguir exatamente a rota `GET /intake/analyses/{analysis_id}/petition-drafts`.
- Os novos artefatos devem usar a nomenclatura `GetPetitionDraft...`.
- A conta autenticada deve ter ownership da análise consultada.
- Quando a análise não existir, o fluxo deve levantar `AnalysisNotFoundError`.
- Quando a análise existir, mas pertencer a outra conta, o fluxo deve levantar `ForbiddenError`.
- Quando a análise ainda não possuir minuta persistida, o fluxo deve levantar `PetitionDraftUnavailableError`.

## 3.2 Não funcionais

- **Segurança:** autenticação obrigatória via `AuthPipe.get_account_id_from_request`; ownership validado no `core` antes de ler a minuta.
- **Compatibilidade retroativa:** nenhum endpoint, DTO ou schema de banco existente deve ser alterado.
- **Performance:** a consulta deve executar apenas a leitura da análise por ID e a leitura da minuta por `analysis_id`, sem agregações de relatório.
- **Observabilidade:** erros devem seguir o fluxo global de `AppErrorHandler`, preservando respostas HTTP consistentes para `NotFoundError` e `ForbiddenError`.

---

# 4. O que já existe?

## Core

- **`PetitionDraft`** (`src/animus/core/intake/domain/structures/petition_draft.py`) — structure de domínio da minuta, com factory `create(...)` e propriedade `dto`.
- **`PetitionDraftDto`** (`src/animus/core/intake/domain/structures/dtos/petition_draft_dto.py`) — DTO já usado para transportar a minuta entre camadas.
- **`PetitionDraftsRepository`** (`src/animus/core/intake/interfaces/petition_drafts_repository.py`) — port com `find_by_analysis_id(analysis_id: Id) -> PetitionDraft | None`.
- **`AnalysesRepository`** (`src/animus/core/intake/interfaces/analyses_repository.py`) — port com `find_by_id(id: Id) -> Analysis | None`.
- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) — entidade com `account_id`, usada para validar ownership.
- **`AnalysisNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_not_found_error.py`) — erro de domínio para análise inexistente.
- **`PetitionDraftUnavailableError`** (`src/animus/core/intake/domain/errors/petition_draft_unavailable_error.py`) — erro de domínio para minuta ausente.
- **`ForbiddenError`** (`src/animus/core/shared/domain/errors/forbidden_error.py`) — erro compartilhado para acesso negado.
- **`GetSecondInstanceJudgmentDraftUseCase`** (`src/animus/core/intake/use_cases/get_second_instance_judgment_draft_use_case.py`) — referência análoga para leitura de draft persistido por `analysis_id`.

## Database

- **`PetitionDraftModel`** (`src/animus/database/sqlalchemy/models/intake/petition_draft_model.py`) — model SQLAlchemy da tabela `petition_drafts`, com `analysis_id` como chave primária e FK para `analyses`.
- **`PetitionDraftMapper`** (`src/animus/database/sqlalchemy/mappers/intake/petition_draft_mapper.py`) — mapper entre `PetitionDraftModel` e `PetitionDraft`.
- **`SqlalchemyPetitionDraftsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_drafts_repository.py`) — implementação concreta de `PetitionDraftsRepository`.
- **Migration `20260522_120000_restructure_petition_drafts.py`** (`migrations/versions/20260522_120000_restructure_petition_drafts.py`) — estrutura persistida atual da minuta.

## Pipes

- **`AuthPipe.get_account_id_from_request(...)`** (`src/animus/pipes/auth_pipe.py`) — resolve a conta autenticada a partir do request.
- **`DatabasePipe.get_analyses_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — injeta `AnalysesRepository`.
- **`DatabasePipe.get_petition_drafts_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — injeta `PetitionDraftsRepository`.
- **`IntakePipe.verify_analysis_by_account_from_request(...)`** (`src/animus/pipes/intake_pipe.py`) — referência existente de validação de ownership na borda, mas não será usado neste fluxo para não duplicar a validação exigida no `GetPetitionDraftUseCase`.

## REST e Routers

- **`GetSecondInstanceJudgmentDraftController`** (`src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`) — referência análoga de endpoint `GET` para draft persistido.
- **`GetCaseSummaryController`** (`src/animus/rest/controllers/intake/get_case_summary_controller.py`) — referência de controller fino que retorna DTO por `analysis_id`.
- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) — composição dos controllers de análise em `/intake`.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) — tradução global de `NotFoundError` para 404 e `ForbiddenError` para 403.

---

# 5. O que deve ser criado?

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/get_petition_draft_use_case.py` (**novo arquivo**)
- **Classe:** `GetPetitionDraftUseCase`
- **Dependências:** `AnalysesRepository` e `PetitionDraftsRepository`
- **Método principal:** `execute(analysis_id: str, account_id: str) -> PetitionDraftDto` — valida a análise e retorna a minuta persistida.
- **Fluxo resumido:**
  - Criar `Id` para `analysis_id` e `account_id`.
  - Buscar a análise via `AnalysesRepository.find_by_id(...)`.
  - Se a análise não existir, levantar `AnalysisNotFoundError`.
  - Se `analysis.account_id.value != account_id_entity.value`, levantar `ForbiddenError`.
  - Buscar a minuta via `PetitionDraftsRepository.find_by_analysis_id(...)`.
  - Se a minuta não existir, levantar `PetitionDraftUnavailableError`.
  - Retornar `petition_draft.dto`.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/get_petition_draft_controller.py` (**novo arquivo**)
- **`*Body`:** não aplicável; endpoint sem corpo.
- **Método HTTP e path:** `GET /intake/analyses/{analysis_id}/petition-drafts`
- **`status_code`:** `200`
- **`response_model`:** `PetitionDraftDto`
- **Dependências injetadas via `Depends`:**
  - `account_id: Id` via `AuthPipe.get_account_id_from_request`
  - `analyses_repository: AnalysesRepository` via `DatabasePipe.get_analyses_repository_from_request`
  - `petition_drafts_repository: PetitionDraftsRepository` via `DatabasePipe.get_petition_drafts_repository_from_request`
- **Fluxo:** `analysis_id` + `account_id` + repositories → `GetPetitionDraftUseCase.execute(...)` → `PetitionDraftDto`.

---

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** exportar `GetPetitionDraftUseCase`.
- **Justificativa:** manter o contrato público do módulo de use cases consistente com os demais casos de uso de `intake`.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** exportar `GetPetitionDraftController`.
- **Justificativa:** permitir importação pelo router e preservar o padrão de composição dos controllers.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** registrar `GetPetitionDraftController.handle(router)`.
- **Justificativa:** expor o novo endpoint dentro do router de análises já montado sob o prefixo `/intake`.

## Pipes e Database

- **Mudança:** não aplicável.
- **Justificativa:** `DatabasePipe` já expõe os dois repositories necessários e a camada `database` já possui model, mapper, migration e repository para `petition_drafts`.

---

# 7. O que deve ser removido?

Não aplicável.

---

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** usar o RF 07 como PRD funcional de referência.
- **Alternativas consideradas:** manter o link original para RF 03 presente no arquivo vazio.
- **Motivo da escolha:** o RF 03 declara que geração de minuta para Advogado é escopo do RF 07, e o RF 07 contém explicitamente a regra de minuta de petição inicial.
- **Impactos / trade-offs:** o frontmatter passa a apontar para o PRD diretamente relacionado à feature, evitando ambiguidade futura.

- **Decisão:** validar ownership dentro de `GetPetitionDraftUseCase`.
- **Alternativas consideradas:** reutilizar `IntakePipe.verify_analysis_by_account_from_request(...)` no controller, como alguns endpoints existentes fazem.
- **Motivo da escolha:** o ticket ANI-100 define o contrato `execute(analysis_id: str, account_id: str) -> PetitionDraftDto` e exige que o use case valide que a análise existe e pertence à conta autenticada.
- **Impactos / trade-offs:** o controller injeta `AuthPipe` e `AnalysesRepository` diretamente; em troca, a regra de acesso fica testável no `core` e não depende de um guard de borda.

- **Decisão:** reutilizar `PetitionDraftDto` como `response_model`.
- **Alternativas consideradas:** criar um schema novo em `validation/intake`.
- **Motivo da escolha:** o DTO já representa exatamente o contrato desejado e endpoints análogos usam DTOs de domínio como resposta.
- **Impactos / trade-offs:** reduz duplicação e mantém o endpoint alinhado ao contrato persistido atual.

- **Decisão:** não alterar `PetitionDraftsRepository`.
- **Alternativas consideradas:** criar método específico para o endpoint.
- **Motivo da escolha:** `find_by_analysis_id(analysis_id: Id) -> PetitionDraft | None` já atende ao fluxo de leitura.
- **Impactos / trade-offs:** mantém a camada `database` sem mudanças e evita novo contrato redundante.

---

# 9. Diagramas e Referências

**Fluxo de dados:**

```text
HTTP Request
  -> Middleware de request
  -> IntakeRouter / AnalysesRouter
  -> GetPetitionDraftController
  -> AuthPipe.get_account_id_from_request
  -> DatabasePipe.get_analyses_repository_from_request
  -> DatabasePipe.get_petition_drafts_repository_from_request
  -> GetPetitionDraftUseCase.execute(analysis_id, account_id)
  -> AnalysesRepository.find_by_id(Id)
  -> SQLAlchemy / analyses
  -> valida ownership
  -> PetitionDraftsRepository.find_by_analysis_id(Id)
  -> SQLAlchemy / petition_drafts
  -> PetitionDraftDto
  -> Response JSON 200
```

**Fluxo assíncrono:** não aplicável. Esta spec cobre apenas leitura de minuta já persistida.

**Referências:**

- `src/animus/core/intake/domain/structures/petition_draft.py`
- `src/animus/core/intake/domain/structures/dtos/petition_draft_dto.py`
- `src/animus/core/intake/interfaces/petition_drafts_repository.py`
- `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_drafts_repository.py`
- `src/animus/pipes/database_pipe.py`
- `src/animus/pipes/auth_pipe.py`
- `src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`
- `src/animus/core/intake/use_cases/get_second_instance_judgment_draft_use_case.py`
- `src/animus/routers/intake/analyses_router.py`

---

# 10. Pendências / Dúvidas

Sem pendências.

---

# 11. Restrições

- O endpoint não deve disparar geração ou regeração de minuta.
- O endpoint não deve retornar relatório completo da análise.
- O `core` não deve importar `FastAPI`, `SQLAlchemy`, `Depends`, `Request` ou qualquer detalhe de infraestrutura.
- A ausência da minuta deve ser tratada por `PetitionDraftUnavailableError`, não por retorno `None` no controller.
- A camada `database` deve continuar apenas implementando persistência e mapeamento; não deve receber regra de ownership.
- Schemas `*Body` não se aplicam a este endpoint, pois a entrada é composta apenas por path param e conta autenticada.
