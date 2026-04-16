---
title: ANI-77 - Persistencia de filtros aplicados na busca de precedentes
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AYAMAQ
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-77
status: closed
last_updated_at: 2026-04-15
---

# 1. Objetivo

Implementar a persistencia do ultimo conjunto de filtros aplicados na busca de precedentes (`courts`, `precedent_kinds`, `limit`) dentro da analise, sem acoplar essa persistencia ao request sincrono de disparo da busca. A gravacao deve acontecer somente ao final bem-sucedido do fluxo assincrono (`SearchAnalysisPrecedentsJob`), substituindo integralmente o snapshot anterior e mantendo os contratos de leitura da analise coerentes para `GET /intake/analyses`, `GET /intake/analyses/{analysis_id}` e `GET /intake/analyses/{analysis_id}/report`.

---

# 2. Escopo

## 2.1 In-scope

- Persistir no `analyses` os filtros normalizados da ultima busca concluida com sucesso.
- Evoluir `Analysis` e `AnalysisDto` para carregar e expor o snapshot persistido de filtros.
- Atualizar `AnalysisModel`, `AnalysisMapper` e `SqlalchemyAnalisysesRepository` para leitura/escrita dos novos campos.
- Ajustar o job assíncrono de busca para salvar filtros no mesmo passo transacional que finaliza precedentes e status final.
- Garantir que fluxos que atualizam status da analise nao descartem os filtros persistidos por sobrescrita acidental.
- Adicionar migration Alembic para incluir os novos campos com compatibilidade para dados legados.

## 2.2 Out-of-scope

- Alterar o algoritmo de busca vetorial, classificacao ou sintese dos precedentes.
- Alterar o contrato HTTP do endpoint `POST /intake/analyses/{analysis_id}/precedents/search` (permanece `202`).
- Criar novo endpoint para filtros; o consumo continua via contratos de leitura da analise.
- Alteracoes de UX/mobile (persistencia local, sliders, badges, etc.).
- Inclusao de testes automatizados nesta spec.

---

# 3. Requisitos

## 3.1 Funcionais

- O endpoint de busca deve continuar recebendo `courts`, `precedent_kinds` e `limit`, normalizando via `AnalysisPrecedentsSearchFilters` antes de publicar evento.
- A etapa sincrona deve apenas publicar `AnalysisPrecedentsSearchRequestedEvent` com payload normalizado; nao deve persistir filtros nesta etapa.
- O `SearchAnalysisPrecedentsJob` deve consumir os filtros normalizados e executar busca + sintese no fluxo atual.
- Apos substituir os `analysis_precedents`, o job deve persistir na `Analysis` os filtros recebidos no payload como ultimo snapshot salvo.
- Cada execucao bem-sucedida deve sobrescrever integralmente os filtros anteriores, sem merge.
- Leituras da analise devem conseguir devolver os filtros persistidos no contrato selecionado (`AnalysisDto`).
- Em falha do job, o status deve continuar indo para `FAILED` e os filtros previamente persistidos devem permanecer inalterados.

## 3.2 Nao funcionais

- **Compatibilidade retroativa:** migration deve suportar linhas legadas de `analyses` sem quebra de leitura/escrita.
- **Consistencia transacional:** update de filtros e status final da analise deve ocorrer no mesmo escopo transacional que persiste `analysis_precedents` no passo final do job.
- **Idempotencia:** reexecucoes do job com o mesmo payload devem manter resultado deterministico de filtros persistidos (snapshot substituivel).
- **Observabilidade:** manter o fluxo atual de status (`SEARCHING_PRECEDENTS` -> `GENERATING_SYNTHESIS` -> `WAITING_PRECEDENT_CHOISE` ou `FAILED`) sem regressao.
- **Seguranca de contrato:** mudanca de leitura deve ser aditiva e em `snake_case`, sem expor ORM.

---

# 4. O que ja existe?

## Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) - entidade da analise; hoje nao guarda filtros aplicados.
- **`AnalysisDto`** (`src/animus/core/intake/domain/entities/dtos/analysis_dto.py`) - contrato HTTP/dominio de analise; hoje sem campos de filtros.
- **`AnalysisPrecedentsSearchFilters`** (`src/animus/core/intake/domain/structures/analysis_precedents_search_filters.py`) - normalizacao, deduplicacao e validacao de filtros de busca.
- **`AnalysisPrecedentsSearchFiltersDto`** (`src/animus/core/intake/domain/structures/dtos/analysis_precedents_search_filters_dto.py`) - DTO usado no request e no payload do job.
- **`RequestAnalysisPrecedentsSearchUseCase`** (`src/animus/core/intake/use_cases/request_analysis_precedents_search_use_case.py`) - valida disponibilidade de resumo e publica evento assíncrono com filtros normalizados.
- **`AnalisysesRepository`** (`src/animus/core/intake/interfaces/analisyses_repository.py`) - contrato de persistencia da analise (`find_by_id`, `find_many`, `add`, `replace`).
- **`GetAnalysisUseCase` / `ListAnalysesUseCase` / `GetAnalysisReportUseCase`** (`src/animus/core/intake/use_cases/*.py`) - retornam `AnalysisDto` direta ou indiretamente.

## Rest

- **`SearchAnalysisPrecedentsController`** (`src/animus/rest/controllers/intake/search_analysis_precedents_controller.py`) - endpoint `POST /intake/analyses/{analysis_id}/precedents/search` com `status_code=202`.
- **`GetAnalysisController`** (`src/animus/rest/controllers/intake/get_analysis_controller.py`) - retorna `AnalysisDto`.
- **`ListAnalysesController`** (`src/animus/rest/controllers/intake/list_analyses_controller.py`) - retorna `CursorPaginationResponse[AnalysisDto]`.
- **`GetAnalysisReportController`** (`src/animus/rest/controllers/intake/get_analysis_report_controller.py`) - retorna `AnalysisReportDto` com `analysis: AnalysisDto`.

## Routers

- **`IntakeRouter`** (`src/animus/routers/intake/intake_router.py`) - registra os controllers de intake, incluindo busca e leituras de analise.

## Database

- **`AnalysisModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_model.py`) - tabela `analyses`; hoje sem colunas para filtros da busca de precedentes.
- **`AnalysisMapper`** (`src/animus/database/sqlalchemy/mappers/intake/analysis_mapper.py`) - conversao dominio <-> ORM para `Analysis`.
- **`SqlalchemyAnalisysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`) - leitura/escrita da analise (`find_by_id`, `find_many`, `replace`).

## PubSub

- **`AnalysisPrecedentsSearchRequestedEvent`** (`src/animus/core/intake/domain/events/analysis_precedents_search_requested_event.py`) - evento com `analysis_id`, `courts`, `precedent_kinds`, `limit`.
- **`SearchAnalysisPrecedentsJob`** (`src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`) - consome evento, busca precedentes, gera sinteses, persiste `analysis_precedents` e atualiza status.

## Lacunas encontradas

- Nao existe persistencia de filtros aplicados no estado da analise.
- Atualizacoes de status em alguns use cases recriam `Analysis` manualmente por `AnalysisDto`, risco de perda silenciosa de novos campos.
- O repositorio Alembic possui duas heads ativas (`20260404_120000` e `4ab74425d1ee`), exigindo cuidado na estrategia de migration.

---

# 5. O que deve ser criado?

## Migracoes Alembic (se aplicavel)

- **Localizacao:** `migrations/versions/<timestamp>_add_analysis_precedents_filters_columns.py` (**novo arquivo**)
- **Operacoes (upgrade):**
  - adicionar colunas na tabela `analyses` para snapshot de filtros:
    - `precedents_search_courts` (`JSON`)
    - `precedents_search_precedent_kinds` (`JSON`)
    - `precedents_search_limit` (`Integer`)
  - manter registros legados com `NULL` nos novos campos ate a primeira busca concluida com sucesso, preservando o significado de "filtros ainda nao aplicados".
- **Operacoes (downgrade):** remover as 3 colunas adicionadas.
- **Reversibilidade:** downgrade e tecnicamente reversivel, com perda dos dados de filtros persistidos apos rollback.

---

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/entities/dtos/analysis_dto.py`
- **Mudanca:** adicionar campo de filtros persistidos no DTO da analise (recomendado: `precedents_search_filters: AnalysisPrecedentsSearchFiltersDto | None = None`).
- **Justificativa:** `AnalysisDto` e o contrato de leitura ja reutilizado por `get/list/report`; incluir o campo aqui evita criar envelope paralelo.

- **Arquivo:** `src/animus/core/intake/domain/entities/analysis.py`
- **Mudanca:** evoluir entidade para carregar/expor filtros persistidos no `create(...)` e na propriedade `dto`; incluir operacao explicita para atualizar status preservando demais atributos (ex.: `set_status(status: str) -> None`).
- **Justificativa:** manter o estado da analise completo no dominio e reduzir risco de sobrescrita de campos em updates parciais.

- **Arquivo:** `src/animus/core/intake/use_cases/update_analysis_status_use_case.py`
- **Mudanca:** parar de reconstruir `Analysis` via `AnalysisDto` incompleto; atualizar status na entidade carregada e chamar `replace(...)`.
- **Justificativa:** preservar filtros persistidos (e campos futuros) em mudancas de status.

- **Arquivo:** `src/animus/core/intake/use_cases/choose_analysis_precedent_use_case.py`
- **Mudanca:** aplicar o mesmo padrao de atualizacao de status preservando filtros ao marcar `PRECEDENT_CHOSED`.
- **Justificativa:** evita apagar filtros apos o usuario escolher precedente.

- **Arquivo:** `src/animus/core/intake/use_cases/create_petition_use_case.py`
- **Mudanca:** na transicao para `PETITION_UPLOADED`, preservar snapshot de filtros existente na analise.
- **Justificativa:** evitar perda acidental de estado persistido em fluxos de peticao.

- **Arquivo:** `src/animus/core/intake/use_cases/create_petition_summary_use_case.py`
- **Mudanca:** na transicao para `PETITION_ANALYZED`, preservar snapshot de filtros existente na analise.
- **Justificativa:** manter consistencia de estado ao longo do ciclo de vida da analise.

- **Arquivo:** `src/animus/core/intake/use_cases/request_petition_summary_use_case.py`
- **Mudanca:** na transicao para `ANALYZING_PETITION`, preservar snapshot de filtros existente na analise.
- **Justificativa:** impedir regressao por sobrescrita na atualizacao de status.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/analysis_model.py`
- **Mudanca:** adicionar mapeamento ORM das 3 novas colunas da tabela `analyses`.
- **Justificativa:** permitir persistencia fisica do snapshot de filtros na mesma entidade agregadora (`Analysis`).

- **Arquivo:** `src/animus/database/sqlalchemy/mappers/intake/analysis_mapper.py`
- **Mudanca:** mapear filtros persistidos entre `AnalysisModel` e `AnalysisDto` nos dois sentidos (`to_entity`, `to_model`).
- **Justificativa:** manter traducao dominio <-> persistencia centralizada no mapper.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`
- **Mudanca:** incluir novas colunas no `replace(...)` (e por consequencia manter `add/find_by_id/find_many` consistentes via mapper atualizado).
- **Justificativa:** garantir que alteracoes da entidade `Analysis` sejam realmente refletidas no banco.

## PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`
- **Mudanca:** no passo `_generate_syntheses_and_persist_sync(payload, analysis_precedents_data) -> None`, apos persistir `analysis_precedents`, carregar `Analysis`, atualizar filtros com `payload.filters_dto`, ajustar status final (`WAITING_PRECEDENT_CHOISE`) e commitar no mesmo escopo transacional.
- **Justificativa:** requisito central da task: filtros persistidos devem representar o ultimo processamento assíncrono concluido com sucesso.

## Rest

- **Arquivo:** `src/animus/rest/controllers/intake/get_analysis_controller.py`
- **Mudanca:** sem alteracao estrutural de endpoint; contrato de saida e ampliado indiretamente por `AnalysisDto`.
- **Justificativa:** evitar mudanca de rota/handler quando a evolucao ja ocorre no contrato de dominio.

- **Arquivo:** `src/animus/rest/controllers/intake/list_analyses_controller.py`
- **Mudanca:** sem alteracao estrutural de endpoint; resposta passa a refletir `AnalysisDto` atualizado.
- **Justificativa:** manter o mesmo fluxo de leitura paginada.

- **Arquivo:** `src/animus/rest/controllers/intake/get_analysis_report_controller.py`
- **Mudanca:** sem alteracao estrutural de endpoint; `analysis` dentro de `AnalysisReportDto` herdara o novo campo do `AnalysisDto`.
- **Justificativa:** reaproveitar contrato existente do relatorio, sem DTO paralelo.

## Routers

- **Nao aplicavel** (nenhuma alteracao de composicao de rotas).

## Validation

- **Nao aplicavel** para novo arquivo em `src/animus/validation/`; o contrato de leitura permanece em `AnalysisDto` no `core`.

---

# 7. O que deve ser removido?

**Nao aplicavel**.

---

# 8. Decisoes Tecnicas e Trade-offs

- **Decisao:** persistir filtros como snapshot denormalizado na propria tabela `analyses`.
  - **Alternativas consideradas:** tabela separada `analysis_precedents_search_filters` com relacao 1:1.
  - **Motivo da escolha:** leitura da analise ja passa por `analyses`; manter snapshot no mesmo agregado reduz joins e complexidade.
  - **Impactos / trade-offs:** perde validacao relacional fina no banco para itens de lista; mitigado por normalizacao no dominio.

- **Decisao:** reutilizar `AnalysisPrecedentsSearchFiltersDto` / `AnalysisPrecedentsSearchFilters` como formato de dominio para persistencia.
  - **Alternativas consideradas:** criar DTO especifico para persistencia.
  - **Motivo da escolha:** evita duplicacao de contrato e garante que o que e persistido ja esta normalizado pelo fluxo existente.
  - **Impactos / trade-offs:** acoplamento intencional entre payload de busca e snapshot persistido.

- **Decisao:** persistir filtros somente no job, ao final bem-sucedido do fluxo assíncrono.
  - **Alternativas consideradas:** persistir no endpoint sincrono ao receber request.
  - **Motivo da escolha:** garante que o estado salvo representa o que efetivamente foi aplicado e concluido com sucesso.
  - **Impactos / trade-offs:** entre request e fim do job, leitura pode refletir snapshot anterior.

- **Decisao:** atualizar status da analise preservando estado carregado (sem reconstruir `AnalysisDto` parcial).
  - **Alternativas consideradas:** manter reconstrucao manual em cada use case.
  - **Motivo da escolha:** previne perda de campos adicionados (como filtros persistidos) e reduz risco de regressao futura.
  - **Impactos / trade-offs:** pequeno refactor em varios use cases que hoje montam `AnalysisDto` manualmente.

- **Decisao:** manter contratos REST e rotas atuais, ampliando apenas `AnalysisDto` de forma aditiva.
  - **Alternativas consideradas:** criar endpoint/DTO dedicado para filtros persistidos.
  - **Motivo da escolha:** menor impacto de API, reaproveitando contratos ja consumidos.
  - **Impactos / trade-offs:** clientes que desserializam estritamente devem tolerar novo campo adicional.

---

# 9. Diagramas e Referencias

- **Fluxo de dados (principal):**

```text
HTTP POST /intake/analyses/{analysis_id}/precedents/search
  -> SearchAnalysisPrecedentsController._Body
  -> RequestAnalysisPrecedentsSearchUseCase.execute(analysis_id, dto)
  -> AnalysisPrecedentsSearchFilters.create(dto)   # normaliza/deduplica
  -> Broker.publish(AnalysisPrecedentsSearchRequestedEvent)
  -> HTTP 202 Accepted
```

- **Fluxo assíncrono (persistencia final):**

```text
AnalysisPrecedentsSearchRequestedEvent
  -> SearchAnalysisPrecedentsJob.handle
     -> step normalize_payload
     -> step search_precedents
        -> UpdateAnalysisStatus(SEARCHING_PRECEDENTS)
        -> SearchAnalysisPrecedentsUseCase.execute(...)
     -> step generate_syntheses_and_persist
        -> UpdateAnalysisStatus(GENERATING_SYNTHESIS)
        -> workflow de sintese
        -> AnalysisPrecedentsRepository.remove_many/add_many
        -> AnalysisRepository.find_by_id
        -> Analysis.set_precedents_search_filters(payload.filters_dto)
        -> Analysis.set_status(WAITING_PRECEDENT_CHOISE)
        -> AnalysisRepository.replace
        -> commit
     -> on exception: UpdateAnalysisStatus(FAILED)
```

- **Referencias de implementacao na codebase:**
  - `src/animus/rest/controllers/intake/search_analysis_precedents_controller.py`
  - `src/animus/core/intake/use_cases/request_analysis_precedents_search_use_case.py`
  - `src/animus/core/intake/domain/structures/analysis_precedents_search_filters.py`
  - `src/animus/core/intake/domain/events/analysis_precedents_search_requested_event.py`
  - `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`
  - `src/animus/core/intake/domain/entities/analysis.py`
  - `src/animus/core/intake/domain/entities/dtos/analysis_dto.py`
  - `src/animus/database/sqlalchemy/models/intake/analysis_model.py`
  - `src/animus/database/sqlalchemy/mappers/intake/analysis_mapper.py`
  - `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`
  - `migrations/versions/20260330_120000_update_petition_summaries_structure.py` (referencia de migration com JSON + backfill)

---

# 10. Pendencias / Duvidas

- **Descricao da pendencia:** PRD RF-03 indica quantidade de precedentes em faixa `1..20` com padrao `5`, mas o backend atual valida `limit` em `5..10` e default `10` em `AnalysisPrecedentsSearchFiltersDto`.
- **Impacto na implementacao:** altera validacao de dominio, payload aceito no endpoint e valor default persistido na migration.
- **Acao sugerida:** validar com produto/arquitetura se ANI-77 deve manter faixa atual (escopo minimo) ou absorver alinhamento de faixa/default nesta mesma entrega.

- **Descricao da pendencia:** base Alembic local possui duas heads (`20260404_120000` e `4ab74425d1ee`).
- **Impacto na implementacao:** definicao de `down_revision` da nova migration pode gerar divergencia de historico e conflitos de upgrade.
- **Acao sugerida:** validar com arquitetura a estrategia de branch de migration (encadear na head oficial do fluxo ativo ou criar merge revision dedicado).
