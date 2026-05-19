# Plano de Implementação: ANI-77 - Persistência de filtros aplicados na busca de precedentes

Este documento detalha o plano de execução para a implementação da persistência do último conjunto de filtros aplicados na busca de precedentes na entidade `Analysis`.

## 1. Fases e Objetivos

| Fase | Objetivo | Depende de | Pode rodar em paralelo com |
| --- | --- | --- | --- |
| **F1 (Core)** | Evoluir contratos e estado da `Analysis` para suportar filtros persistidos. | - | - |
| **F2 (Drivers/Infra - DB)** | Implementar a persistência física (Migration, Model, Mapper e Repository). | F1 | F4 |
| **F3 (Drivers/Infra - PubSub)** | Persistir filtros no Job assíncrono apenas em caso de sucesso. | F1, F2 | F4 |
| **F4 (API Layer)** | Expor o novo campo nos contratos de leitura existentes de forma aditiva. | F1 | F2, F3 |

---

## 2. Detalhamento das Tarefas

### F1: Core (Entidades, DTOs e Casos de Uso)
- **T1.1: Atualizar `AnalysisDto`**
  - **Arquivo:** `src/animus/core/intake/domain/entities/dtos/analysis_dto.py`
  - **Ação:** Adicionar campo `precedents_search_filters: AnalysisPrecedentsSearchFiltersDto | None = None`.
  - **Resultado:** Contrato de domínio preparado para o snapshot.
- **T1.2: Evoluir Entidade `Analysis`**
  - **Arquivo:** `src/animus/core/intake/domain/entities/analysis.py`
  - **Ação:** Incluir campo no `create(...)`, atualizar serialização no método `dto`, e adicionar métodos explícitos `set_status(...)` e `set_precedents_search_filters(...)`.
  - **Resultado:** Entidade protege o estado e evita sobrescritas acidentais.
- **T1.3: Ajustar `RequestAnalysisPrecedentsSearchUseCase`**
  - **Arquivo:** `src/animus/core/intake/use_cases/request_analysis_precedents_search_use_case.py`
  - **Ação:** Garantir que o passo síncrono apenas publique o evento com filtros normalizados, sem persistir no banco.
- **T1.4: Refatorar `UpdateAnalysisStatusUseCase`**
  - **Arquivo:** `src/animus/core/intake/use_cases/update_analysis_status_use_case.py`
  - **Ação:** Parar de reconstruir a entidade via DTO incompleto; carregar a entidade, atualizar o status e chamar `replace(...)`.
  - **Dependência:** T1.2
- **T1.5: Refatorar Use Cases de Fluxo (Petition e Choice)**
  - **Arquivos:** 
    - `src/animus/core/intake/use_cases/choose_analysis_precedent_use_case.py`
    - `src/animus/core/intake/use_cases/create_petition_use_case.py`
    - `src/animus/core/intake/use_cases/create_petition_summary_use_case.py`
    - `src/animus/core/intake/use_cases/request_petition_summary_use_case.py`
  - **Ação:** Aplicar o padrão de atualização de status preservando o estado carregado da `Analysis`.

### F2: Drivers/Infra - Database
- **T2.1: Estratégia de Migration**
  - **Ação:** Definir `down_revision` (considerando as duas heads atuais), tipos de coluna (`JSON` para listas, `Integer` para limit) e valores de backfill para registros legados.
- **T2.2: Criar Migration Alembic**
  - **Arquivo:** `migrations/versions/<timestamp>_add_analysis_precedents_filters_columns.py`
  - **Ação:** Adicionar `precedents_search_courts`, `precedents_search_precedent_kinds` e `precedents_search_limit` na tabela `analyses`.
- **T2.3: Atualizar `AnalysisModel`**
  - **Arquivo:** `src/animus/database/sqlalchemy/models/intake/analysis_model.py`
  - **Ação:** Mapear as 3 novas colunas no ORM.
- **T2.4: Atualizar `AnalysisMapper`**
  - **Arquivo:** `src/animus/database/sqlalchemy/mappers/intake/analysis_mapper.py`
  - **Ação:** Implementar a tradução domínio <-> ORM para os novos campos de filtros.
- **T2.5: Ajustar `SqlalchemyAnalisysesRepository`**
  - **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`
  - **Ação:** Garantir que o método `replace(...)` inclua as novas colunas na persistência.

### F3: Drivers/Infra - PubSub (Jobs)
- **T3.1: Atualizar `SearchAnalysisPrecedentsJob`**
  - **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`
  - **Ação:** No passo final de persistência (`_generate_syntheses_and_persist_sync`), carregar a `Analysis`, injetar os filtros do payload e atualizar o status para `WAITING_PRECEDENT_CHOISE`.
- **T3.2: Consistência Transacional**
  - **Ação:** Certificar que a gravação dos precedentes e o snapshot de filtros ocorram no mesmo commit.
- **T3.3: Tratamento de Erro**
  - **Ação:** Garantir que, em caso de falha (`FAILED`), o snapshot de filtros anterior permaneça inalterado.

### F4: API Layer
- **T4.1: Validação de Leitura (Controllers)**
  - **Arquivos:**
    - `src/animus/rest/controllers/intake/get_analysis_controller.py`
    - `src/animus/rest/controllers/intake/list_analyses_controller.py`
    - `src/animus/rest/controllers/intake/get_analysis_report_controller.py`
  - **Ação:** Confirmar que a resposta reflete o novo campo do `AnalysisDto` sem quebra de contrato.
- **T4.2: Validação de Escrita (Search Controller)**
  - **Arquivo:** `src/animus/rest/controllers/intake/search_analysis_precedents_controller.py`
  - **Ação:** Confirmar que o contrato de entrada e o status `202` permanecem inalterados.

---

## 3. Ordem de Execução Recomendada (Bottom-Up)

1. **Core (F1):** T1.1 -> T1.2 -> T1.3 -> (T1.4 a T1.8).
2. **Database (F2):** T2.1 -> T2.2 -> T2.3 -> T2.4 -> T2.5.
3. **PubSub (F3):** T3.1 -> T3.2 -> T3.3.
4. **API (F4):** T4.1 -> T4.2 -> T4.3.
