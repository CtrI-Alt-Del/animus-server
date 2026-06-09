---
title: Edição manual da minuta de sentença na análise de 2ª instância
prd: https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/49348609/PRD+RF+08+An+lise+para+2+Inst+ncia+para+o+perfil+Juiz
ticket: N/A
status: open
last_updated_at: 2026-06-05
---

# 1. Objetivo

Detalhar a implementação da edição manual da `SecondInstanceJudgmentDraft` já gerada para análises `SECOND_INSTANCE`, permitindo que o app sobrescreva de forma síncrona o conteúdo persistido da minuta pelo endpoint `PUT /intake/analyses/{analysis_id}/second-instance-judgment-drafts`, com validação explícita dos campos obrigatórios, preservação do status atual da análise e reaproveitamento da persistência, do relatório e do recurso HTTP já existentes.

# 2. Escopo

## 2.1 In-scope

- Expor `PUT /intake/analyses/{analysis_id}/second-instance-judgment-drafts` no módulo `intake`.
- Reutilizar `SecondInstanceJudgmentDraftDto` como contrato de entrada e saída do endpoint.
- Reutilizar `SecondInstanceJudgmentDraft.create(...)` para reconstruir a structure normalizada a partir do payload editado.
- Exigir que a análise exista, pertença à conta autenticada, seja do tipo `SECOND_INSTANCE` e já possua minuta persistida.
- Validar `report`, `merit_analysis` e `precedent_adherence_analysis` como obrigatórios e não vazios após `strip()`.
- Validar `ruling` como lista obrigatória, não vazia e sem itens vazios após `strip()`.
- Permitir `preliminary_issues` e `no_applicable_precedent_notice` como campos opcionais.
- Sobrescrever integralmente a minuta persistida via `SecondInstanceJudgmentDraftsRepository.replace(...)`.
- Manter `GET /intake/analyses/{analysis_id}/second-instance-judgment-drafts` e `GET /intake/analyses/{analysis_id}/second-instance-report` refletindo a versão mais recente salva.

## 2.2 Out-of-scope

- Alterações no fluxo assíncrono de geração inicial da minuta.
- Alterações no fluxo assíncrono de regeração por comentários do usuário.
- Versionamento histórico, diff entre versões ou auditoria de edições manuais.
- Alterações de schema em `second_instance_judgment_drafts` ou migrações Alembic.
- Mudanças em `FIRST_INSTANCE`, `CASE_ASSESSMENT` ou no contrato de exportação em `DOCX`.
- Mudanças de UX/mobile, autosave, debounce ou feedback visual do app.

# 3. Requisitos

## 3.1 Funcionais

- O backend deve expor `PUT /intake/analyses/{analysis_id}/second-instance-judgment-drafts`.
- O endpoint deve receber os campos `report`, `merit_analysis`, `precedent_adherence_analysis`, `ruling`, `preliminary_issues` e `no_applicable_precedent_notice`.
- `report`, `merit_analysis` e `precedent_adherence_analysis` devem ser obrigatórios e não podem ser vazios após `strip()`.
- `ruling` deve conter ao menos um item e nenhum item pode ser vazio após `strip()`.
- `preliminary_issues` e `no_applicable_precedent_notice` podem ser omitidos ou enviados como `null`.
- O endpoint deve exigir autenticação Bearer e ownership via `IntakePipe.verify_analysis_by_account_from_request(...)`.
- A edição deve falhar com `404` quando a análise não existir.
- A edição deve falhar com `409` quando a análise não for `SECOND_INSTANCE`.
- A edição deve falhar com `404` quando ainda não existir minuta persistida para a análise.
- O salvamento deve sobrescrever integralmente a minuta anterior, sem atualização parcial por campo.
- O endpoint deve retornar `200 OK` com `SecondInstanceJudgmentDraftDto` refletindo o estado persistido após a sobrescrita.
- O relatório retornado por `GET /intake/analyses/{analysis_id}/second-instance-report` deve refletir a minuta mais recente sem endpoint adicional.

## 3.2 Não funcionais

- **Segurança:** o endpoint deve reaproveitar autenticação e ownership check já existentes, sem confiar em `analysis_id` vindo do body.
- **Idempotência:** chamadas repetidas de `PUT` com o mesmo payload devem produzir o mesmo estado persistido.
- **Compatibilidade retroativa:** não deve haver mudança nos contratos já publicados de `GET /intake/analyses/{analysis_id}/second-instance-judgment-drafts`, `POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts`, `POST /intake/analyses/{analysis_id}/judgment-drafts/regenerate` e `GET /intake/analyses/{analysis_id}/second-instance-report`.
- **Observabilidade:** a edição manual não deve reabrir fluxo assíncrono nem alterar `analyses.status`; o polling de status continua refletindo o valor já persistido.
- **Resiliência:** a gravação deve seguir o escopo transacional por request já existente, sem `commit()` manual em controller ou repository.
- **Compatibilidade de persistência:** a feature deve reutilizar a tabela `second_instance_judgment_drafts` sem novas colunas, relações ou arquivos persistidos auxiliares.

# 4. O que já existe?

## Core

- **`SecondInstanceJudgmentDraft`** (`src/animus/core/intake/domain/structures/second_instance_judgment_draft.py`) — structure 1:1 da minuta, com `create(dto: SecondInstanceJudgmentDraftDto) -> SecondInstanceJudgmentDraft` e normalização de campos obrigatórios e `ruling`.
- **`SecondInstanceJudgmentDraftDto`** (`src/animus/core/intake/domain/structures/dtos/second_instance_judgment_draft_dto.py`) — DTO já estável para atravessar controller, use case, repository e relatório.
- **`SecondInstanceJudgmentDraftsRepository`** (`src/animus/core/intake/interfaces/judgment_drafts_repository.py`) — port com `find_by_analysis_id(analysis_id: Id) -> SecondInstanceJudgmentDraft | None`, `add(judgment_draft: SecondInstanceJudgmentDraft) -> None` e `replace(judgment_draft: SecondInstanceJudgmentDraft) -> None`.
- **`GetSecondInstanceJudgmentDraftUseCase`** (`src/animus/core/intake/use_cases/get_second_instance_judgment_draft_use_case.py`) — leitura da minuta existente com erro de domínio quando ausente.
- **`CreateSecondInstanceJudgmentDraftUseCase`** (`src/animus/core/intake/use_cases/create_judgment_draft_use_case.py`) — referência de persistência da minuta em fluxos assíncronos; não atende edição manual porque possui semântica de criação/substituição após geração.
- **`GetSecondInstanceAnalysisReportUseCase`** (`src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`) — já carrega a minuta atual do repositório e a inclui em `SecondInstanceAnalysisReportDto`.
- **`AnalysisNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_not_found_error.py`) — erro de domínio para análise inexistente.
- **`SecondInstanceAnalysisRequiredError`** (`src/animus/core/intake/domain/errors/second_instance_analysis_required_error.py`) — erro de domínio para análise de tipo incompatível.
- **`SecondInstanceJudgmentDraftUnavailableError`** (`src/animus/core/intake/domain/errors/judgment_draft_unavailable_error.py`) — erro de domínio para ausência de minuta persistida.

## Database

- **`SecondInstanceJudgmentDraftModel`** (`src/animus/database/sqlalchemy/models/intake/judgment_draft_model.py`) — model da tabela `second_instance_judgment_drafts`, com vínculo 1:1 por `analysis_id`.
- **`SecondInstanceJudgmentDraftMapper`** (`src/animus/database/sqlalchemy/mappers/intake/judgment_draft_mapper.py`) — mapper entre model ORM e structure de domínio.
- **`SqlalchemySecondInstanceJudgmentDraftsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`) — implementação concreta da port; `replace(...)` já sobrescreve `report`, `merit_analysis`, `precedent_adherence_analysis`, `ruling`, `preliminary_issues` e `no_applicable_precedent_notice`.
- **Seeders da camada database:** `src/animus/database/sqlalchemy/seeders/intake_seeder.py` existe, mas não há seeder específico para minutas de 2ª instância; não foi encontrada necessidade de ajuste em seeders nem em paths persistidos/gerados.

## REST

- **`GetSecondInstanceJudgmentDraftController`** (`src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`) — já expõe o mesmo recurso HTTP em `GET /analyses/{analysis_id}/second-instance-judgment-drafts`.
- **`TriggerSecondInstanceJudgmentDraftGenerationController`** (`src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_generation_controller.py`) — já expõe `POST /analyses/{analysis_id}/second-instance-judgment-drafts`, consolidando o recurso plural para o draft de 2ª instância.
- **`TriggerSecondInstanceJudgmentDraftRegenerationController`** (`src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_regeneration_controller.py`) — referência de controller com `_Body` local e validação por `field_validator(...)` para ações sobre a mesma minuta.
- **`UpdatePetitionDraftController`** (`src/animus/rest/controllers/intake/update_petition_draft_controller.py`) — implementação análoga do fluxo de edição manual de draft já persistido no contexto `CASE_ASSESSMENT`.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) — já traduz `NotFoundError`, `ConflictError` e `ValidationError`; não há evidência de necessidade de handler novo.

## Routers

- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) — composition root do módulo `intake`; já agrupa endpoints de minuta, relatório e decisão de 2ª instância.

## Pipes

- **`IntakePipe.verify_analysis_by_account_from_request(...)`** (`src/animus/pipes/intake_pipe.py`) — guard de ownership por `analysis_id`, já usado pelos endpoints de `intake`.
- **`DatabasePipe.get_analyses_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP de `AnalysesRepository`.
- **`DatabasePipe.get_judgment_drafts_repository_from_request(...)`** (`src/animus/pipes/database_pipe.py`) — provider HTTP de `SecondInstanceJudgmentDraftsRepository`.

## PubSub

- **`GenerateSecondInstanceJudgmentDraftJob`** (`src/animus/pubsub/inngest/jobs/intake/generate_second_instance_judgment_draft_job.py`) — fluxo assíncrono de geração inicial; continua sendo a origem da primeira versão persistida da minuta.
- **`RegenerateSecondInstanceJudgmentDraftJob`** (`src/animus/pubsub/inngest/jobs/intake/regenerate_second_instance_judgment_draft_job.py`) — fluxo assíncrono de regeração com comentários; não deve ser alterado pela edição manual.

# 5. O que deve ser criado?

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/update_second_instance_judgment_draft_use_case.py`
- **Dependências (ports injetados):** `AnalysesRepository`, `SecondInstanceJudgmentDraftsRepository`
- **Método principal:** `execute(analysis_id: str, dto: SecondInstanceJudgmentDraftDto) -> SecondInstanceJudgmentDraftDto` — valida a análise, garante que o draft já exista, normaliza o payload e sobrescreve a minuta persistida.
- **Fluxo resumido:** normaliza `analysis_id` como `Id` → recompõe `SecondInstanceJudgmentDraftDto` com `analysis_id` do path → busca `Analysis` → lança `AnalysisNotFoundError` se ausente → valida `analysis.type.is_second_instance` → busca draft atual → lança `SecondInstanceJudgmentDraftUnavailableError` se ausente → cria `SecondInstanceJudgmentDraft` → `replace(...)` → retorna `judgment_draft.dto`.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/update_second_instance_judgment_draft_controller.py`
- **`_Body`:** schema Pydantic local com:
- `report: str`
- `merit_analysis: str`
- `precedent_adherence_analysis: str`
- `ruling: list[str]`
- `preliminary_issues: str | None = None`
- `no_applicable_precedent_notice: str | None = None`
- **Validações relevantes do `_Body`:** rejeitar branco em `report`, `merit_analysis` e `precedent_adherence_analysis`; rejeitar lista `ruling` vazia e itens em branco; manter campos opcionais apenas tipados como `str | None`.
- **Método auxiliar:** `to_dto(analysis_id: str) -> SecondInstanceJudgmentDraftDto` — monta o DTO do `core` usando `analysis_id` vindo do path param.
- **Método HTTP e path:** `PUT /intake/analyses/{analysis_id}/second-instance-judgment-drafts`
- **`status_code`:** `200`
- **`response_model`:** `SecondInstanceJudgmentDraftDto`
- **Dependências injetadas via `Depends`:** `IntakePipe.verify_analysis_by_account_from_request(...)`, `DatabasePipe.get_analyses_repository_from_request(...)`, `DatabasePipe.get_judgment_drafts_repository_from_request(...)`
- **Fluxo:** `_Body.to_dto(analysis.id.value)` → `UpdateSecondInstanceJudgmentDraftUseCase.execute(...)` → `SecondInstanceJudgmentDraftDto`

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/structures/second_instance_judgment_draft.py`
- **Mudança:** reforçar a factory `create(dto: SecondInstanceJudgmentDraftDto) -> SecondInstanceJudgmentDraft` como ponto central de normalização de `report`, `merit_analysis`, `precedent_adherence_analysis`, `ruling` e `analysis_id`.
- **Justificativa:** manter o invariante da structure no domínio e evitar persistência de drafts inválidos por fluxos HTTP ou assíncronos.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** exportar `UpdateSecondInstanceJudgmentDraftUseCase`.
- **Justificativa:** manter a superfície pública do contexto `intake` consistente com os demais use cases.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** importar e exportar `UpdateSecondInstanceJudgmentDraftController`.
- **Justificativa:** manter a superfície pública dos controllers de `intake` estável para o router.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** registrar `UpdateSecondInstanceJudgmentDraftController.handle(router)` junto dos endpoints do recurso `second-instance-judgment-drafts`.
- **Justificativa:** expor o novo endpoint no router oficial do módulo `intake`.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`
- **Mudança:** **Não aplicável**.
- **Justificativa:** `replace(...)` já sobrescreve integralmente todos os campos editáveis necessários.

## Pipes

- **Arquivo:** `src/animus/pipes/database_pipe.py`
- **Mudança:** **Não aplicável**.
- **Justificativa:** os providers HTTP já existentes cobrem `AnalysesRepository` e `SecondInstanceJudgmentDraftsRepository`.

## Migrações Alembic

- **Arquivo:** `migrations/versions/`
- **Mudança:** **Não aplicável**.
- **Justificativa:** a tabela atual já suporta a edição manual sem evolução de schema.

# 7. O que deve ser removido?

**Não aplicável**.

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** usar `PUT /intake/analyses/{analysis_id}/second-instance-judgment-drafts` no mesmo recurso já exposto por `GET` e `POST`.
- **Alternativas consideradas:** `PATCH /.../second-instance-judgment-drafts`; path singular dedicado.
- **Motivo da escolha:** a codebase já trata a minuta como um recurso 1:1 por análise, mas com path plural estável; `PUT` comunica sobrescrita completa e preserva consistência com os endpoints existentes.
- **Impactos / trade-offs:** o contrato fica naturalmente idempotente, mas não suporta atualização parcial de seções isoladas.

- **Decisão:** criar `UpdateSecondInstanceJudgmentDraftUseCase` separado em vez de reutilizar `CreateSecondInstanceJudgmentDraftUseCase`.
- **Alternativas consideradas:** reutilizar `CreateSecondInstanceJudgmentDraftUseCase`; mover a regra para o controller.
- **Motivo da escolha:** a edição manual exige pré-condição de draft já existente e não deve alterar status nem semântica da geração inicial.
- **Impactos / trade-offs:** adiciona um use case dedicado no `core`, mas evita condicionais ambíguas e regressão nos fluxos assíncronos.

- **Decisão:** validar o payload na borda HTTP e reforçar a normalização no domínio.
- **Alternativas consideradas:** validar apenas no controller; validar apenas em `SecondInstanceJudgmentDraft.create(...)`.
- **Motivo da escolha:** a borda devolve `422` por campo com melhor ergonomia para o app, enquanto o domínio protege a integrity da structure em qualquer produtor futuro.
- **Impactos / trade-offs:** há duplicação parcial de validação, mas o risco de persistência inválida cai significativamente.

- **Decisão:** reutilizar `SecondInstanceJudgmentDraftUnavailableError` quando não houver minuta prévia.
- **Alternativas consideradas:** criar erro novo específico para edição manual.
- **Motivo da escolha:** o significado de domínio já existe e é o mesmo: a análise ainda não possui minuta persistida disponível para leitura ou sobrescrita.
- **Impactos / trade-offs:** reduz novos nomes e mantém comportamento alinhado com o `GET`; a mensagem permanece genérica, não específica de “edição”.

- **Decisão:** não alterar `GetSecondInstanceAnalysisReportUseCase` para refletir a edição manual.
- **Alternativas consideradas:** recarregar draft por caminho alternativo ou criar endpoint dedicado de leitura pós-edição.
- **Motivo da escolha:** o relatório já busca a minuta atual diretamente em `SecondInstanceJudgmentDraftsRepository.find_by_analysis_id(...)`.
- **Impactos / trade-offs:** a mudança fica mínima e consistente; depende do contrato atual do relatório, que já foi confirmado no código.

# 9. Diagramas e Referências

- **Fluxo de dados:**

```text
HTTP PUT /intake/analyses/{analysis_id}/second-instance-judgment-drafts
-> Auth middleware
-> AnalysesRouter
-> UpdateSecondInstanceJudgmentDraftController
-> IntakePipe.verify_analysis_by_account_from_request(...)
-> DatabasePipe.get_analyses_repository_from_request(...)
-> DatabasePipe.get_judgment_drafts_repository_from_request(...)
-> UpdateSecondInstanceJudgmentDraftUseCase.execute(analysis_id, dto)
-> AnalysesRepository.find_by_id(...)
-> SecondInstanceJudgmentDraftsRepository.find_by_analysis_id(...)
-> SecondInstanceJudgmentDraft.create(...)
-> SecondInstanceJudgmentDraftsRepository.replace(...)
-> SqlalchemySecondInstanceJudgmentDraftsRepository
-> PostgreSQL.second_instance_judgment_drafts
-> SecondInstanceJudgmentDraftDto
-> Response JSON 200
```

- **Fluxo assíncrono (se aplicável):** **Não aplicável**.

- **Referências:**
- `src/animus/rest/controllers/intake/update_petition_draft_controller.py`
- `src/animus/core/intake/use_cases/update_petition_draft_use_case.py`
- `src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`
- `src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_generation_controller.py`
- `src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_regeneration_controller.py`
- `src/animus/core/intake/use_cases/create_judgment_draft_use_case.py`
- `src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`
- `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`

# 10. Pendências / Dúvidas

- **Descrição da pendência:** não foi encontrado ticket Jira específico para a edição manual da minuta de sentença; o próprio PRD registra “ticket a criar” para essa entrega.
- **Impacto na implementação:** não bloqueia a implementação técnica, mas reduz a rastreabilidade entre PRD, spec e execução no board.
- **Ação sugerida:** criar a task correspondente no Jira e substituir `ticket: N/A` no frontmatter quando a referência existir.
