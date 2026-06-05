---
title: Edição manual da minuta de sentença na análise de 2ª instância
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AQDxAg
ticket: N/A
status: open
last_updated_at: 2026-06-05
---

# 1. Objetivo

Implementar a edição manual da minuta já gerada para análises `SECOND_INSTANCE`, expondo um endpoint `PUT` no mesmo recurso HTTP já usado para leitura e geração da minuta, com validação explícita dos campos obrigatórios, preservação do status atual da análise e sobrescrita integral do draft persistido, sem alterar o fluxo assíncrono de geração/regeração nem o contrato do relatório de 2ª instância, que já reflete a minuta persistida mais recente.

# 2. Escopo

## 2.1 In-scope

- Criar `UpdateSecondInstanceJudgmentDraftUseCase` no `core/intake`.
- Expor `PUT /intake/analyses/{analysis_id}/second-instance-judgment-drafts`.
- Reutilizar `SecondInstanceJudgmentDraftDto`, `SecondInstanceJudgmentDraft` e `SecondInstanceJudgmentDraftsRepository.replace(...)`.
- Validar `report`, `merit_analysis` e `precedent_adherence_analysis` como obrigatórios e não vazios após `strip()`.
- Validar `ruling` como lista obrigatória, não vazia e sem itens vazios após `strip()`.
- Permitir `preliminary_issues` e `no_applicable_precedent_notice` como opcionais.
- Exigir que a análise exista, pertença à conta autenticada, seja do tipo `SECOND_INSTANCE` e já tenha minuta persistida.
- Sobrescrever integralmente a minuta persistida no salvamento manual.
- Registrar o novo controller no `src/animus/rest/controllers/intake/__init__.py` e no `AnalysesRouter`.

## 2.2 Out-of-scope

- Alterações no fluxo assíncrono de geração da minuta.
- Alterações no fluxo assíncrono de regeração da minuta por comentários.
- Mudanças em `models`, `mappers`, `repositories` SQLAlchemy ou migrações Alembic.
- Novos endpoints de leitura da minuta, pois `GET /intake/analyses/{analysis_id}/second-instance-judgment-drafts` já existe.
- Exportação PDF.
- Versionamento histórico de edições manuais.
- Alterações nos fluxos `FIRST_INSTANCE` e `CASE_ASSESSMENT`.

# 3. Requisitos

## 3.1 Funcionais

- O endpoint de edição manual deve ser `PUT /intake/analyses/{analysis_id}/second-instance-judgment-drafts`.
- O body deve conter os campos `report`, `merit_analysis`, `precedent_adherence_analysis`, `ruling`, `preliminary_issues` e `no_applicable_precedent_notice`.
- `report`, `merit_analysis` e `precedent_adherence_analysis` devem ser obrigatórios e não podem ser vazios após `strip()`.
- `ruling` deve conter pelo menos um item e nenhum item pode ser vazio após `strip()`.
- `preliminary_issues` e `no_applicable_precedent_notice` podem ser `null`.
- A edição deve falhar com `404` quando não existir minuta persistida para a análise.
- A edição deve falhar quando a análise não existir.
- A edição deve falhar quando a análise não for `SECOND_INSTANCE`.
- A edição deve reutilizar o ownership check via `IntakePipe.verify_analysis_by_account_from_request`.
- O `PUT` deve sobrescrever todos os campos persistidos da minuta existente.
- O `PUT` deve retornar `SecondInstanceJudgmentDraftDto` com status HTTP `200`.
- O relatório retornado por `GET /intake/analyses/{analysis_id}/second-instance-report` deve refletir a minuta atualizada sem exigir endpoint adicional.

## 3.2 Não funcionais

- **Segurança:** o endpoint deve reutilizar autenticação Bearer e ownership check via `IntakePipe.verify_analysis_by_account_from_request`.
- **Compatibilidade retroativa:** a feature não deve alterar os contratos HTTP já existentes de `GET /intake/analyses/{analysis_id}/second-instance-judgment-drafts`, `POST /intake/analyses/{analysis_id}/second-instance-judgment-drafts`, `POST /intake/analyses/{analysis_id}/judgment-drafts/regenerate` e `GET /intake/analyses/{analysis_id}/second-instance-report`.
- **Observabilidade:** a edição manual não deve alterar `analyses.status`; a análise permanece no estado já persistido após a geração anterior.
- **Resiliência:** a sobrescrita deve continuar usando o fluxo transacional existente por request, sem `commit` manual em controller ou repository.
- **Compatibilidade de persistência:** a feature deve reutilizar a tabela `second_instance_judgment_drafts` sem novas colunas ou migrations.

# 4. O que já existe?

## Core

- **`SecondInstanceJudgmentDraft`** (`src/animus/core/intake/domain/structures/second_instance_judgment_draft.py`) — structure já usada para criar e serializar a minuta persistida; deve continuar sendo o ponto central de normalização dos campos.
- **`SecondInstanceJudgmentDraftDto`** (`src/animus/core/intake/domain/structures/dtos/second_instance_judgment_draft_dto.py`) — DTO já usado como contrato de entrada/saída da minuta.
- **`SecondInstanceJudgmentDraftsRepository`** (`src/animus/core/intake/interfaces/judgment_drafts_repository.py`) — port existente com `find_by_analysis_id(...)`, `add(...)` e `replace(...)`.
- **`GetSecondInstanceJudgmentDraftUseCase`** (`src/animus/core/intake/use_cases/get_second_instance_judgment_draft_use_case.py`) — referência de leitura da minuta existente com `404` quando ausente.
- **`CreateSecondInstanceJudgmentDraftUseCase`** (`src/animus/core/intake/use_cases/create_judgment_draft_use_case.py`) — referência de construção da structure a partir de `SecondInstanceJudgmentDraftDto` e persistência via `add(...)`/`replace(...)`.
- **`SecondInstanceJudgmentDraftUnavailableError`** (`src/animus/core/intake/domain/errors/judgment_draft_unavailable_error.py`) — erro existente de `NotFoundError` para ausência de minuta persistida.
- **`SecondInstanceAnalysisRequiredError`** (`src/animus/core/intake/domain/errors/second_instance_analysis_required_error.py`) — erro existente para análise de tipo incompatível.
- **`AnalysisNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_not_found_error.py`) — erro já usado quando a análise não existe.
- **`GetSecondInstanceAnalysisReportUseCase`** (`src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`) — já busca a minuta via `judgment_drafts_repository.find_by_analysis_id(...)` e devolve `draft` no relatório.

## Database

- **`SecondInstanceJudgmentDraftModel`** (`src/animus/database/sqlalchemy/models/intake/judgment_draft_model.py`) — model 1:1 da tabela `second_instance_judgment_drafts` com `analysis_id` como chave primária.
- **`SecondInstanceJudgmentDraftMapper`** (`src/animus/database/sqlalchemy/mappers/intake/judgment_draft_mapper.py`) — mapper existente entre model e structure.
- **`SqlalchemySecondInstanceJudgmentDraftsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`) — implementação concreta da port com `replace(...)` que sobrescreve os campos já persistidos.
- **Seeders da camada database:** não aplicável; não há indício de seeder específico para minutas de 2ª instância, e a feature não exige carga inicial nem novos arquivos persistidos/gerados.

## REST

- **`GetSecondInstanceJudgmentDraftController`** (`src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`) — já expõe `GET /analyses/{analysis_id}/second-instance-judgment-drafts` e define o recurso HTTP a ser reutilizado pelo `PUT`.
- **`TriggerSecondInstanceJudgmentDraftGenerationController`** (`src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_generation_controller.py`) — já usa `POST /analyses/{analysis_id}/second-instance-judgment-drafts`, reforçando que o recurso existente está em path plural.
- **`TriggerSecondInstanceJudgmentDraftRegenerationController`** (`src/animus/rest/controllers/intake/trigger_second_instance_judgment_draft_regeneration_controller.py`) — referência de validação local com `_Body` + `field_validator`.
- **`UpdatePetitionDraftController`** (`src/animus/rest/controllers/intake/update_petition_draft_controller.py`) — melhor referência de controller `PUT` para edição manual de draft persistido com body local e `to_dto(...)`.

## Routers

- **`AnalysesRouter`** (`src/animus/routers/intake/analyses_router.py`) — router de composição que já registra os endpoints de julgamento de 2ª instância e deve registrar o controller novo.

## Pipes

- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) — já provê `AnalysesRepository` e `SecondInstanceJudgmentDraftsRepository` via `Depends(...)`.
- **`IntakePipe`** (`src/animus/pipes/intake_pipe.py`) — já resolve ownership check por análise e deve continuar sendo a pré-condição de acesso do endpoint.

## PubSub

- **`GenerateSecondInstanceJudgmentDraftJob`** (`src/animus/pubsub/inngest/jobs/intake/generate_second_instance_judgment_draft_job.py`) — gera e persiste a primeira versão da minuta usando `CreateSecondInstanceJudgmentDraftUseCase`.
- **`RegenerateSecondInstanceJudgmentDraftJob`** (`src/animus/pubsub/inngest/jobs/intake/regenerate_second_instance_judgment_draft_job.py`) — substitui a minuta por uma nova versão gerada pela IA; não deve ser alterado por esta feature.

# 5. O que deve ser criado?

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/update_second_instance_judgment_draft_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `AnalysesRepository`, `SecondInstanceJudgmentDraftsRepository`
- **Método principal:** `execute(analysis_id: str, dto: SecondInstanceJudgmentDraftDto) -> SecondInstanceJudgmentDraftDto` — valida a análise, garante que a minuta já exista, reconstrói a structure normalizada e sobrescreve o draft persistido.
- **Fluxo resumido:** normaliza `analysis_id` no DTO → busca `Analysis` → lança `AnalysisNotFoundError` se ausente → valida `analysis.type.is_second_instance` → busca draft atual → lança `SecondInstanceJudgmentDraftUnavailableError` se ausente → cria `SecondInstanceJudgmentDraft` → `replace(...)` → retorna DTO.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/update_second_instance_judgment_draft_controller.py` (**novo arquivo**)
- **`_Body`:**
  - `report: str`
  - `merit_analysis: str`
  - `precedent_adherence_analysis: str`
  - `ruling: list[str]`
  - `preliminary_issues: str | None = None`
  - `no_applicable_precedent_notice: str | None = None`
- **Validações relevantes do `_Body`:**
  - `report`, `merit_analysis` e `precedent_adherence_analysis` devem rejeitar branco após `strip()` com erro por campo.
  - `ruling` deve rejeitar lista vazia e itens em branco.
  - `preliminary_issues` e `no_applicable_precedent_notice`, quando enviados como `str`, devem aceitar texto preenchido; `null` continua permitido.
- **Método HTTP e path:** `PUT /intake/analyses/{analysis_id}/second-instance-judgment-drafts`
- **`status_code`:** `200`
- **`response_model`:** `SecondInstanceJudgmentDraftDto`
- **Dependências injetadas via `Depends`:** `IntakePipe.verify_analysis_by_account_from_request`, `DatabasePipe.get_analyses_repository_from_request`, `DatabasePipe.get_judgment_drafts_repository_from_request`
- **Fluxo:** `_Body.to_dto(analysis_id)` → `UpdateSecondInstanceJudgmentDraftUseCase.execute()` → `SecondInstanceJudgmentDraftDto`

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/structures/second_instance_judgment_draft.py`
- **Mudança:** reforçar a factory `create(dto: SecondInstanceJudgmentDraftDto) -> SecondInstanceJudgmentDraft` para normalizar e validar os campos obrigatórios (`report`, `merit_analysis`, `precedent_adherence_analysis`) e `ruling` antes de criar a structure.
- **Justificativa:** manter o invariante do draft no domínio, evitando persistir minutas inválidas tanto no `PUT` manual quanto nos fluxos assíncronos já existentes.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** exportar `UpdateSecondInstanceJudgmentDraftUseCase`.
- **Justificativa:** manter o padrão de exports públicos da camada `core/intake/use_cases`.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** importar e exportar `UpdateSecondInstanceJudgmentDraftController`.
- **Justificativa:** manter a superfície pública dos controllers de `intake` consistente com os demais endpoints.

## Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** registrar `UpdateSecondInstanceJudgmentDraftController.handle(router)` junto aos demais endpoints de `second-instance-judgment-drafts`.
- **Justificativa:** expor o novo endpoint no router oficial de análises.

# 7. O que deve ser removido?

**Não aplicável**.

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** usar `PUT /analyses/{analysis_id}/second-instance-judgment-drafts` no mesmo recurso HTTP já existente.
- **Alternativas consideradas:** criar path singular (`/second-instance-judgment-draft`) ou um path dedicado de edição.
- **Motivo da escolha:** a codebase já usa `GET` e `POST` no recurso plural `second-instance-judgment-drafts`; manter o `PUT` no mesmo recurso evita duplicação e preserva consistência de nomenclatura.
- **Impactos / trade-offs:** o path plural não comunica relação 1:1 tão explicitamente quanto um singular, mas reduz divergência com os contratos já publicados.

- **Decisão:** criar um `UpdateSecondInstanceJudgmentDraftUseCase` separado em vez de reutilizar `CreateSecondInstanceJudgmentDraftUseCase`.
- **Alternativas consideradas:** chamar `CreateSecondInstanceJudgmentDraftUseCase` diretamente no controller ou torná-lo genérico para create/update.
- **Motivo da escolha:** o fluxo de edição manual tem pré-condições próprias: a minuta deve existir e o status da análise não deve mudar. `CreateSecondInstanceJudgmentDraftUseCase` hoje aceita ausência de draft e força `DONE`, o que conflita com a feature.
- **Impactos / trade-offs:** adiciona um caso de uso novo, mas evita condicionais extras e preserva semântica clara entre criação assíncrona e edição manual.

- **Decisão:** validar no `_Body` do controller e também reforçar a factory `SecondInstanceJudgmentDraft.create(...)`.
- **Alternativas consideradas:** validar apenas no controller ou apenas no domínio.
- **Motivo da escolha:** o controller entrega erro HTTP por campo de forma mais amigável; o domínio protege a integridade da structure quando a mesma factory for chamada por jobs ou outros fluxos futuros.
- **Impactos / trade-offs:** aumenta a duplicação parcial de validação, mas reduz risco de persistência inválida por caminhos não HTTP.

- **Decisão:** não alterar `GetSecondInstanceAnalysisReportUseCase` nem o controller de relatório.
- **Alternativas consideradas:** criar lógica adicional para recarregar ou transformar o draft após edição.
- **Motivo da escolha:** o relatório já lê o draft atual diretamente do repositório e devolve `draft` no DTO, então a edição manual já será refletida automaticamente após a persistência.
- **Impactos / trade-offs:** mantém a mudança mínima; depende do comportamento já existente do relatório, que foi confirmado no código.

# 9. Diagramas e Referências

- **Fluxo de dados:**

```text
HTTP PUT /intake/analyses/{analysis_id}/second-instance-judgment-drafts
-> Auth middleware
-> AnalysesRouter
-> UpdateSecondInstanceJudgmentDraftController
-> IntakePipe.verify_analysis_by_account_from_request
-> DatabasePipe.get_analyses_repository_from_request
-> DatabasePipe.get_judgment_drafts_repository_from_request
-> UpdateSecondInstanceJudgmentDraftUseCase.execute(...)
-> AnalysesRepository.find_by_id(...)
-> SecondInstanceJudgmentDraftsRepository.find_by_analysis_id(...)
-> SecondInstanceJudgmentDraft.create(...)
-> SecondInstanceJudgmentDraftsRepository.replace(...)
-> PostgreSQL.second_instance_judgment_drafts
-> SecondInstanceJudgmentDraftDto
-> Response 200 JSON
```

- **Fluxo assíncrono (se aplicável):** não aplicável; a edição manual é síncrona e não publica eventos.

- **Referências:**
  - `src/animus/rest/controllers/intake/update_petition_draft_controller.py`
  - `src/animus/core/intake/use_cases/update_petition_draft_use_case.py`
  - `src/animus/rest/controllers/intake/get_second_instance_judgment_draft_controller.py`
  - `src/animus/core/intake/use_cases/create_judgment_draft_use_case.py`
  - `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_judgment_drafts_repository.py`
  - `src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py`

# 10. Pendências / Dúvidas

**Sem pendências**.
