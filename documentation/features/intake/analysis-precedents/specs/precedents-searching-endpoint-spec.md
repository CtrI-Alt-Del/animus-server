---
title: Endpoint assincrono de busca de precedentes da analise
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AYAMAQ
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-48
status: closed
last_updated_at: 2026-03-29
---

# 1. Objetivo

Implementar o disparo assincrono da busca de precedentes para uma `Analysis`, expondo o endpoint de requisicao da busca, os endpoints de leitura dos `AnalysisPrecedent` e das `AnalysisPetition` da analise, aplicando filtros opcionais de `court` e `precedent_kind`, reutilizando o `PetitionSummary` ja gerado como entrada semantica, consultando o indice vetorial existente, calculando `applicability_percentage`, gerando `synthesis` via `Agno` + `Gemini`, persistindo os `AnalysisPrecedent` resultantes e atualizando `Analysis.status` ao longo do processamento sem mover regra de negocio para `controller`, `pipe`, repository ORM ou job.

---

# 2. Escopo

## 2.1 In-scope

- Expor o endpoint HTTP que solicita a busca assincrona de precedentes para uma analise existente.
- Expor o endpoint HTTP que retorna os `AnalysisPrecedent` persistidos de uma analise.
- Expor o endpoint HTTP que retorna as `AnalysisPetition` da analise em formato `ListResponse`.
- Expor o endpoint HTTP que retorna o `Analysis.status` atual para polling da analise.
- Expor o endpoint HTTP que marca um `AnalysisPrecedent` como escolhido para a analise.
- Validar autenticacao, ownership da `Analysis` e pre-condicao de existencia do `PetitionSummary` antes de publicar o job.
- Permitir filtros opcionais por `court` e `precedent_kind` no request de busca.
- Permitir configuracao de quantidade de resultados com `limit` entre `5` e `10`, com padrao `10`.
- Criar o evento de requisicao do job e o job Inngest responsavel por buscar, sintetizar e persistir os `AnalysisPrecedent`.
- Criar a persistencia SQLAlchemy de `analysis_precedents` e o port correspondente no `core`.
- Implementar o provider de embeddings do `PetitionSummary` usando o mesmo espaco vetorial ja usado na vetorizacao de precedentes.
- Atualizar `Analysis.status` para `SEARCHING_PRECEDENTS`, `GENERATING_SYNTHESIS`, `WAITING_PRECEDENT_CHOISE` e `FAILED` conforme o andamento do job.

## 2.2 Out-of-scope

- Exportacao do precedente escolhido para PDF (`RF 06`).
- Filtro avancado para incluir precedentes sem status preenchido na base.
- Persistencia explicita de um campo textual de classificacao (`Aplicavel`, `Possivelmente aplicavel`, `Nao aplicavel`); nesta task o backend persiste `applicability_percentage`, e o agrupamento podera ser derivado na superficie de leitura.
- Reindexacao completa da base vetorial de precedentes; esta spec nao altera o conjunto de campos ja indexados no pipeline atual.
- Assumir o Qdrant como fonte ja saneada para status validos de busca, sem reexecutar exclusao de status proibidos nesta feature.


---

# 3. Requisitos

## 3.1 Funcionais

- O endpoint `POST /intake/analyses/{analysis_id}/precedents/search` deve aceitar `analysis_id` no path e body JSON com `courts`, `precedent_kinds` e `limit` opcionais.
- O endpoint `POST /intake/analyses/{analysis_id}/precedents/search` deve retornar `202 Accepted` sem body e publicar um evento que dispara o job de busca.
- O endpoint `GET /intake/analyses/{analysis_id}/precedents` deve retornar `200` com `list[AnalysisPrecedentDto]` dos precedentes persistidos da analise.
- O endpoint `GET /intake/analyses/{analysis_id}/petitions` deve retornar `200` com `ListResponse[AnalysisPetition]` da analise.
- O endpoint `GET /intake/analyses/{analysis_id}/status` deve retornar `200` com `AnalysisStatusDto` contendo o status atual da analise.
- O endpoint `PATCH /intake/analyses/{analysis_id}/precedents/choose` deve marcar exatamente um `AnalysisPrecedent` da analise como escolhido, identificado por `court`, `kind` e `number` via query params.
- O endpoint de escolha deve retornar `200` com o `AnalysisStatusDto` atualizado da analise.
- Os cinco endpoints devem retornar `404` quando a `Analysis` nao existir.
- Os cinco endpoints devem retornar `403` quando a `Analysis` nao pertencer a conta autenticada.
- O endpoint deve falhar antes da publicacao do job quando a analise ainda nao possuir `PetitionSummary` persistido.
- O job deve usar o `PetitionSummary` da analise como entrada da busca semantica.
- O job deve restringir a busca vetorial pelo universo definido por `courts` e `precedent_kinds` quando esses filtros forem informados.
- O job deve desduplicar resultados por `PrecedentIdentifier` e calcular `applicability_percentage` com a formula `score_thesis * 0.7 + score_enunciation * 0.3`.
- O job deve persistir os precedentes encontrados como `AnalysisPrecedent`, com `is_chosen = False`, `applicability_percentage` preenchido e `synthesis` preenchida ao final da segunda fase.
- O endpoint de escolha deve limpar `is_chosen` dos demais precedentes da mesma analise e marcar apenas o precedente informado como `is_chosen = True`.
- O endpoint de escolha deve atualizar `Analysis.status` para `PRECEDENT_CHOSED` apos a marcacao bem-sucedida.
- O job deve atualizar `Analysis.status` para `SEARCHING_PRECEDENTS` antes da busca, `GENERATING_SYNTHESIS` antes do workflow de IA, `WAITING_PRECEDENT_CHOISE` ao concluir com sucesso e `FAILED` quando houver excecao nao tratada.
- O workflow de sintese deve receber o resumo da peticao e a lista de precedentes candidatos, retornando a mesma colecao com `synthesis` preenchida por precedente.

## 3.2 Nao funcionais

- **Performance:** o endpoint HTTP deve apenas validar/preparar a requisicao e devolver `202`, sem executar busca vetorial ou chamada ao LLM no ciclo da request.
- **Seguranca:** o endpoint exige autenticacao por `Bearer access token` e ownership check por `account_id`.
- **Idempotencia:** reexecucoes do mesmo job para a mesma analise nao podem duplicar linhas em `analysis_precedents`; o job deve limpar os registros atuais da analise e depois inserir o novo conjunto em chamadas explicitas separadas no mesmo escopo transacional.
- **Resiliencia:** falha em embeddings, consulta vetorial, hidratacao de precedentes ou workflow de IA deve resultar em `Analysis.status = FAILED`.
- **Observabilidade:** o job deve manter transicoes persistidas em `Analysis.status` para permitir polling pelo mobile, sem publicar eventos de marco intermediarios.
- **Compatibilidade retroativa:** a busca continua usando o espaco vetorial atual (`thesis` + `enunciation/questao`) sem alterar o contrato publico dos endpoints ja existentes em `intake`.

---

# 4. O que ja existe?

## Camada Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) - entidade da analise, ja usada no ownership check e com `status` persistido em `analyses`.
- **`AnalysisStatus`** (`src/animus/core/intake/domain/entities/analysis_status.py`) - enum de estados do fluxo; ja contem `SEARCHING_PRECEDENTS`, `GENERATING_SYNTHESIS`, `WAITING_PRECEDENT_CHOISE` e `FAILED`.
- **`AnalysisStatusDto`** (`src/animus/core/intake/domain/entities/dtos/analysis_status_dto.py`) - DTO ja existente e adequado para responder o endpoint de polling de status sem criar schema paralelo.
- **`AnalysisPrecedentDto`** (`src/animus/core/intake/domain/structures/dtos/analysis_precedent_dto.py`) - DTO ja existente e adequado para responder o endpoint de listagem dos precedentes persistidos.
- **`PetitionSummary`** (`src/animus/core/intake/domain/structures/petition_summary.py`) - resumo textual ja persistido em `petition_summaries` e base natural para a busca semantica.
- **`AnalysisPrecedent`** (`src/animus/core/intake/domain/structures/analysis_precedent.py`) - `Structure` ja modelada com `precedent`, `is_chosen`, `applicability_percentage` e `synthesis`.
- **`AnalysisPetition`** (`src/animus/core/intake/domain/structures/analysis_petition.py`) - `Structure` do agregado de leitura por analise, contendo `petition` e `summary` (opcional quando ainda nao houver resumo).
- **`AnalysisStatusValue.PRECEDENT_CHOSED`** (`src/animus/core/intake/domain/entities/analysis_status.py`) - estado final ja existente para representar a escolha concluida do precedente.
- **`PetitionSummariesRepository`** (`src/animus/core/intake/interfaces/petition_summaries_repository.py`) - ja expoe `find_by_analysis_id(analysis_id: Id) -> PetitionSummary | None`.
- **`PrecedentsEmbeddingsRepository`** (`src/animus/core/intake/interfaces/precedents_embeddings_repository.py`) - port atual da busca vetorial; hoje ainda sem filtros nem limite por universo de busca.
- **`PrecedentsRepository`** (`src/animus/core/intake/interfaces/precedents_repository.py`) - port do catalogo de precedentes; hoje insuficiente para hidratacao em lote por identificador composto.
- **`PetitionSummaryEmbeddingsProvider`** (`src/animus/core/intake/interfaces/petition_embeddings_provider.py`) - port ja esbocado para embeddings do resumo, mas sem implementacao concreta e com inconsistencias de naming/export.
- **`SynthesizeAnalysisPrecedentsWorkflow`** (`src/animus/core/intake/interfaces/synthesize_analysis_precedents_workflow.py`) - port ja existente para sintese, mas hoje nao recebe `PetitionSummary`, o que impede explicar a relacao com o caso.

## Camada Database

- **`PrecedentModel`** (`src/animus/database/sqlalchemy/models/intake/precedent_model.py`) - tabela `precedents` com `court`, `kind`, `number`, `status`, `enunciation` e `thesis`.
- **`PrecedentMapper`** (`src/animus/database/sqlalchemy/mappers/intake/precedents_mapper.py`) - reconstrui `Precedent` a partir do ORM atual.
- **`SqlalchemyPrecedentsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_precendents_repository.py`) - referencia de repository concreto do contexto `intake`; hoje usa lookup incompleto para um identificador que, pelo Glossario, deveria ser `court + kind + number`.
- **`SqlalchemyAnalisysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`) - repository ja pronto para `find_by_id(...)` e `replace(...)` da `Analysis`.
- **`SqlalchemyPetitionSummariesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_summaries_repository.py`) - repository existente para leitura do resumo da peticao.
- **`QdrantPrecedentsEmbeddingsRepository`** (`src/animus/database/qdrant/qdrant_precedents_embeddings_repository.py`) - adaptador vetorial atual com named vectors `thesis` e `enunciation`; ja persiste `court` e `kind` no payload, o que permite evoluir para filtros no Qdrant.

## Camada REST / Routers / Pipes

- **`CreatePetitionController`** (`src/animus/rest/controllers/intake/create_petition_controller.py`) - melhor referencia de controller fino no contexto `intake`, com `_Body`, `Depends(...)` e uso de `IntakePipe`.
- **`IntakePipe.verify_analysis_by_account_from_request(...)`** (`src/animus/pipes/intake_pipe.py`) - verificacao reutilizavel de ownership e existencia da analise, adequada tanto para o endpoint de busca quanto para o endpoint de status.
- **`SummarizePetitionController`** (`src/animus/rest/controllers/intake/summarize_petition_controller.py`) - referencia do padrao de wiring de AI e storage via pipes.
- **`IntakeRouter`** (`src/animus/routers/intake/intake_router.py`) - router agregador atual com prefixo `/intake`.
- **`AuthPipe`** (`src/animus/pipes/auth_pipe.py`) - guard ja pronto para autenticar a conta via `Authorization: Bearer`.
- **`IntakePipe`** (`src/animus/pipes/intake_pipe.py`) - ja possui `verify_analysis_by_account_from_request(...)`, reutilizavel no novo endpoint.
- **`PubSubPipe`** (`src/animus/pipes/pubsub_pipe.py`) - ja expone `Broker` para publicacao de eventos a partir de `request.state.inngest_client`.

## Camada AI

- **`AgnoSummarizePetitionWorkflow`** (`src/animus/ai/agno/workflows/intake/agno_summarize_petition_workflow.py`) - referencia direta de implementacao Agno no dominio `intake`, incluindo `_StepNames`, `Team`, output estruturado e persistencia via use case.
- **`IntakeTeam`** (`src/animus/ai/agno/teams/intake_teams.py`) - team existente com agente configurado em `Gemini`, padrao a ser estendido para a sintese dos precedentes.
- **`PetitionSummaryOutput`** (`src/animus/ai/agno/outputs/intake/petition_summary_output.py`) - referencia de output estruturado Pydantic para workflows do contexto.

## Camada PubSub

- **`InngestBroker`** (`src/animus/pubsub/inngest/inngest_broker.py`) - broker concreto ja usado pelos fluxos de `auth`; nesta feature ele e usado apenas no endpoint para publicar o evento de requisicao do job.
- **`VectorizePrecedentsJob`** (`src/animus/pubsub/inngest/jobs/intake/vectorize_precedents_job.py`) - referencia de job do contexto `intake` que monta repositories/providers concretos e usa `Sqlalchemy.session()`.
- **`InngestPubSub`** (`src/animus/pubsub/inngest/inngest_pubsub.py`) - composition root atual dos jobs Inngest.

## Lacunas identificadas na codebase

- Nao existe endpoint para requisitar a busca de precedentes da analise.
- Nao existe endpoint para listar os precedentes da analise apos o processamento.
- Nao existe endpoint para listar as peticoes da analise com o resumo associado em uma resposta agregada.
- Nao existe evento de requisicao do job de busca.
- Nao existe persistencia de `AnalysisPrecedent` em SQLAlchemy.
- Nao existe endpoint para marcar um `AnalysisPrecedent` como escolhido.
- Nao existe implementacao concreta de `PetitionSummaryEmbeddingsProvider`.
- Nao existe implementacao concreta de `SynthesizeAnalysisPrecedentsWorkflow`.
- O port `PrecedentsEmbeddingsRepository` ainda nao suporta filtros por `court` e `precedent_kind`.
- O port `PrecedentsRepository` ainda nao suporta hidratacao em lote por identificador composto.
- O package `src/animus/core/intake/interfaces/__init__.py` e `src/animus/core/intake/domain/structures/__init__.py` possuem inconsistencias de naming/export para os tipos de embeddings do resumo.
- O significado funcional de `ementa` no contexto desta feature precisa seguir o identificador ja existente do precedente, sem introduzir novo campo persistido na modelagem atual.

---

# 5. O que deve ser criado?

## Camada Core (Structures / DTOs)

- **Localizacao:** `src/animus/core/intake/domain/structures/dtos/analysis_precedents_search_filters_dto.py` (**novo arquivo**)
- **Tipo:** `@dto`
- **Atributos:** `courts: list[str]`, `precedent_kinds: list[str]`, `limit: int = 10`
- **Responsabilidade:** contrato de dados para atravessar controller -> use cases -> evento do job sem carregar tipos de infraestrutura.

- **Localizacao:** `src/animus/core/intake/domain/structures/analysis_precedents_search_filters.py` (**novo arquivo**)
- **Tipo:** `@structure`
- **Atributos:** `courts: list[Court]`, `precedent_kinds: list[PrecedentKind]`, `limit: Integer`
- **Metodos / factory:**
  - `create(dto: AnalysisPrecedentsSearchFiltersDto) -> AnalysisPrecedentsSearchFilters` - normaliza listas, remove duplicados preservando ordem e valida `limit` entre `5` e `10`.
  - `dto -> AnalysisPrecedentsSearchFiltersDto` - devolve o contrato serializavel para evento/job.

## Camada Core (Erros de Dominio)

- **Localizacao:** `src/animus/core/intake/domain/errors/petition_summary_unavailable_error.py` (**novo arquivo**)
- **Classe base:** `ConflictError`
- **Motivo:** quando a `Analysis` existe e pertence a conta autenticada, mas ainda nao possui `PetitionSummary` persistido para iniciar a busca de precedentes.

## Camada Core (Interfaces / Ports)

- **Localizacao:** `src/animus/core/intake/interfaces/analysis_precedents_repository.py` (**novo arquivo**)
- **Metodos:**
  - `find_many_by_analysis_id(analysis_id: Id) -> ListResponse[AnalysisPrecedent]` - consulta os precedentes ja persistidos para a analise.
  - `find_by_analysis_id_and_precedent_id(analysis_id: Id, precedent_id: Id) -> AnalysisPrecedent | None` - busca um precedente especifico ja associado a analise.
  - `remove_many_by_analysis_id(analysis_id: Id) -> None` - remove todos os precedentes atualmente associados a analise.
  - `add_many_by_analysis_id(analysis_id: Id, analysis_precedents: list[AnalysisPrecedent]) -> None` - persiste o novo conjunto de precedentes da analise.
  - `choose_by_analysis_id_and_precedent_id(analysis_id: Id, precedent_id: Id) -> None` - limpa a marcacao anterior da analise e marca apenas o precedente informado como escolhido.

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/intake/use_cases/list_analysis_petitions_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `PetitionsRepository`, `PetitionSummariesRepository`
- **Metodo principal:** `execute(analysis_id: str) -> ListResponse[AnalysisPetition]` - lista peticoes da analise e agrega o resumo de cada peticao quando existir.
- **Fluxo resumido:** `Id.create(analysis_id)` -> `PetitionsRepository.find_all_by_analysis_id_ordered_by_uploaded_at(...)` -> para cada peticao consultar `PetitionSummariesRepository.find_by_petition_id(...)` -> montar `AnalysisPetition` -> retornar `ListResponse`.

- **Localizacao:** `src/animus/core/intake/use_cases/request_analysis_precedents_search_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `PetitionSummariesRepository`, `Broker`
- **Metodo principal:** `execute(analysis_id: str, dto: AnalysisPrecedentsSearchFiltersDto) -> None` - valida a disponibilidade do resumo, normaliza filtros e publica o evento de requisicao do job.
- **Fluxo resumido:** `Id.create(analysis_id)` -> `PetitionSummariesRepository.find_by_analysis_id(...)` -> `AnalysisPrecedentsSearchFilters.create(dto)` -> `Broker.publish(AnalysisPrecedentsSearchRequestedEvent(...))`.

- **Localizacao:** `src/animus/core/intake/use_cases/search_analysis_precedents_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `PetitionSummariesRepository`, `PetitionSummaryEmbeddingsProvider`, `PrecedentsEmbeddingsRepository`, `PrecedentsRepository`
- **Metodo principal:** `execute(analysis_id: str, dto: AnalysisPrecedentsSearchFiltersDto) -> list[AnalysisPrecedentDto]` - executa a fase de busca, deduplicacao e calculo de `applicability_percentage`.
- **Fluxo resumido:** carregar `PetitionSummary` -> gerar embeddings -> consultar Qdrant com filtros -> hidratar `Precedent` em lote -> agregar por identificador usando melhor `score` por campo -> calcular `applicability_percentage` -> ordenar desc -> truncar em `limit` -> montar `AnalysisPrecedentDto` com `synthesis=None`.

- **Localizacao:** `src/animus/core/intake/use_cases/update_analysis_status_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalisysesRepository`
- **Metodo principal:** `execute(analysis_id: str, status: str) -> None` - atualiza o status persistido da analise mantendo os demais campos do agregado.
- **Fluxo resumido:** `find_by_id(...)` -> recriar `Analysis` com o mesmo DTO e novo `status` -> `AnalisysesRepository.replace(...)`.

- **Localizacao:** `src/animus/core/intake/use_cases/choose_analysis_precedent_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalysisPrecedentsRepository`, `AnalisysesRepository`
- **Metodo principal:** `execute(analysis_id: str, precedent_identifier_dto: PrecedentIdentifierDto) -> AnalysisStatusDto` - valida a existencia do `AnalysisPrecedent` pelo identificador composto (`court`, `kind`, `number`), marca apenas ele como escolhido e atualiza a analise para `PRECEDENT_CHOSED`.
- **Fluxo resumido:** `Id.create(analysis_id)` -> `PrecedentIdentifier.create(...)` -> `AnalysisPrecedentsRepository.find_many_by_analysis_id(...)` -> localizar item por `precedent.identifier` -> `AnalysisPrecedentsRepository.choose_by_analysis_id_and_precedent_id(...)` -> `AnalisysesRepository.find_by_id(...)` -> recriar `Analysis` com status `PRECEDENT_CHOSED` -> `AnalisysesRepository.replace(...)` -> retornar `analysis.status.dto`.

- **Localizacao:** `src/animus/core/intake/use_cases/list_analysis_precedents_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalysisPrecedentsRepository`
- **Metodo principal:** `execute(analysis_id: str) -> list[AnalysisPrecedentDto]` - lista os `AnalysisPrecedent` persistidos da analise e devolve DTOs ordenados conforme o repository.
- **Fluxo resumido:** `Id.create(analysis_id)` -> `AnalysisPrecedentsRepository.find_many_by_analysis_id(...)` -> mapear `AnalysisPrecedent.dto` -> retornar `list[AnalysisPrecedentDto]`.

## Camada Database (Models SQLAlchemy)

- **Localizacao:** `src/animus/database/sqlalchemy/models/intake/analysis_precedent_model.py` (**novo arquivo**)
- **Tabela:** `analysis_precedents`
- **Colunas:**
  - `analysis_id` - `String(26)`, `ForeignKey('analyses.id')`, parte da chave primaria
  - `precedent_id` - `String(26)`, `ForeignKey('precedents.id')`, parte da chave primaria
  - `is_chosen` - `Boolean`, `nullable=False`, `default=False`
  - `applicability_percentage` - `Float`, `nullable=True`
  - `synthesis` - `Text`, `nullable=True`
- **Relacionamentos:** `analysis` -> `AnalysisModel`; `precedent` -> `PrecedentModel`

## Camada Database (Mappers)

- **Localizacao:** `src/animus/database/sqlalchemy/mappers/intake/analysis_precedent_mapper.py` (**novo arquivo**)
- **Metodos:**
  - `to_entity(model: AnalysisPrecedentModel) -> AnalysisPrecedent` - reconstrui a `Structure` com `Precedent` hidratado via relacionamento ORM.
  - `to_model(entity: AnalysisPrecedent) -> AnalysisPrecedentModel` - cria o model ORM a partir da `Structure`, reaproveitando `precedent.id` ja persistido.

## Camada Database (Repositorios)

- **Localizacao:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analysis_precedents_repository.py` (**novo arquivo**)
- **Interface implementada:** `AnalysisPrecedentsRepository`
- **Dependencias:** `Session` SQLAlchemy
- **Metodos:**
  - `find_many_by_analysis_id(analysis_id: Id) -> ListResponse[AnalysisPrecedent]` - busca precedentes da analise com `joinedload` do `PrecedentModel`, ordenando por `applicability_percentage DESC`.
  - `find_by_analysis_id_and_precedent_id(analysis_id: Id, precedent_id: Id) -> AnalysisPrecedent | None` - busca o registro especifico da tabela associativa usando a PK composta.
  - `remove_many_by_analysis_id(analysis_id: Id) -> None` - remove os registros atuais da analise no escopo da `Session` recebida.
  - `add_many_by_analysis_id(analysis_id: Id, analysis_precedents: list[AnalysisPrecedent]) -> None` - insere o novo conjunto no escopo da mesma `Session`, sem `upsert` por linha.
  - `choose_by_analysis_id_and_precedent_id(analysis_id: Id, precedent_id: Id) -> None` - zera `is_chosen` dos registros da analise e marca o precedente alvo como `True` na mesma `Session`.

## Camada REST (Controllers)

- **Localizacao:** `src/animus/rest/controllers/intake/search_analysis_precedents_controller.py` (**novo arquivo**)
- **`*Body`:** `_Body` no mesmo arquivo do controller, com `courts: list[str] = []`, `precedent_kinds: list[str] = []`, `limit: int = 10` e `to_dto() -> AnalysisPrecedentsSearchFiltersDto`.
- **Metodo HTTP e path:** `POST /intake/analyses/{analysis_id}/precedents/search`
- **`status_code`:** `202`
- **`response_model`:** **Nao aplicavel** (`202` sem body)
- **Path params:** `analysis_id: IdSchema`
- **Dependencias injetadas via `Depends`:** `account_id: Id` via `AuthPipe`, `analisyses_repository: AnalisysesRepository` via `DatabasePipe`, `petition_summaries_repository: PetitionSummariesRepository` via `DatabasePipe`, `broker: Broker` via `PubSubPipe`
- **Fluxo:** `analysis_id: IdSchema` + `_Body.to_dto()` -> `IntakePipe.verify_analysis_by_account_from_request(...)` -> controller instancia `RequestAnalysisPrecedentsSearchUseCase(...)` com ports/provedores ja resolvidos -> `execute(...)` -> `Response(status_code=202)`.

- **Localizacao:** `src/animus/rest/controllers/intake/get_analysis_status_controller.py` (**novo arquivo**)
- **`*Body`:** **Nao aplicavel**.
- **Metodo HTTP e path:** `GET /intake/analyses/{analysis_id}/status`
- **`status_code`:** `200`
- **`response_model`:** `AnalysisStatusDto`
- **Dependencias injetadas via `Depends`:** `analysis: Analysis` via `IntakePipe.verify_analysis_by_account_from_request(...)`
- **Fluxo:** `analysis` (resolvida por `IntakePipe.verify_analysis_by_account_from_request(...)`) -> `analysis.status.dto` -> `AnalysisStatusDto`

- **Localizacao:** `src/animus/rest/controllers/intake/list_analysis_precedents_controller.py` (**novo arquivo**)
- **`*Body`:** **Nao aplicavel**.
- **Metodo HTTP e path:** `GET /intake/analyses/{analysis_id}/precedents`
- **`status_code`:** `200`
- **`response_model`:** `list[AnalysisPrecedentDto]`
- **Dependencias injetadas via `Depends`:** `analysis: Analysis` via `IntakePipe.verify_analysis_by_account_from_request(...)`, `analysis_precedents_repository: AnalysisPrecedentsRepository` via `DatabasePipe`
- **Fluxo:** `analysis` (resolvida por `IntakePipe.verify_analysis_by_account_from_request(...)`) -> controller instancia `ListAnalysisPrecedentsUseCase(...)` -> `execute(analysis.id.value)` -> `list[AnalysisPrecedentDto]`

- **Localizacao:** `src/animus/rest/controllers/intake/list_analysis_petitions_controller.py` (**novo arquivo**)
- **`*Body`:** **Nao aplicavel**.
- **Metodo HTTP e path:** `GET /intake/analyses/{analysis_id}/petitions`
- **`status_code`:** `200`
- **`response_model`:** `ListResponse[AnalysisPetition]`
- **Dependencias injetadas via `Depends`:** `analysis: Analysis` via `IntakePipe.verify_analysis_by_account_from_request(...)`, `petitions_repository: PetitionsRepository` via `DatabasePipe`, `petition_summaries_repository: PetitionSummariesRepository` via `DatabasePipe`
- **Fluxo:** `analysis` (resolvida por `IntakePipe.verify_analysis_by_account_from_request(...)`) -> controller instancia `ListAnalysisPetitionsUseCase(...)` -> `execute(analysis.id.value)` -> `ListResponse[AnalysisPetition]`

- **Localizacao:** `src/animus/rest/controllers/intake/choose_analysis_precedent_controller.py` (**novo arquivo**)
- **`*Body`:** **Nao aplicavel**.
- **Metodo HTTP e path:** `PATCH /intake/analyses/{analysis_id}/precedents/choose`
- **`status_code`:** `200`
- **`response_model`:** `AnalysisStatusDto`
- **Dependencias injetadas via `Depends`:** `account_id: Id` via `AuthPipe`, `analisyses_repository: AnalisysesRepository` via `DatabasePipe`, `analysis_precedents_repository: AnalysisPrecedentsRepository` via `DatabasePipe`
- **Query params:** `court: str`, `kind: str`, `number: int`
- **Fluxo:** `analysis_id` + (`court`, `kind`, `number`) -> `IntakePipe.verify_analysis_by_account_from_request(...)` -> controller instancia `ChooseAnalysisPrecedentUseCase(...)` -> `execute(...)` -> `AnalysisStatusDto`

## Camada AI (Workflows Agno)

- **Localizacao:** `src/animus/ai/agno/outputs/intake/analysis_precedents_synthesis_output.py` (**novo arquivo**)
- **Classe:** `AnalysisPrecedentsSynthesisOutput`
- **Atributos:** `items: list[AnalysisPrecedentSynthesisItemOutput]`, onde cada item contem `court: str`, `kind: str`, `number: int`, `synthesis: str`
- **Responsabilidade:** limitar a saida do LLM apenas ao identificador do precedente e ao texto de sintese, evitando que o modelo altere `applicability_percentage` ou campos estruturais.

- **Localizacao:** `src/animus/ai/agno/workflows/intake/agno_synthesize_analysis_precedents_workflow.py` (**novo arquivo**)
- **Interface implementada:** `SynthesizeAnalysisPrecedentsWorkflow`
- **Biblioteca/SDK utilizado:** `agno`, `Gemini`
- **Metodos:**
  - `run(petition_summary: PetitionSummary, analysis_precedents: list[AnalysisPrecedentDto]) -> ListResponse[AnalysisPrecedent]` - gera a `synthesis` de cada precedente mantendo `applicability_percentage`, `precedent` e `is_chosen` recebidos.

## Camada Providers

- **Localizacao:** `src/animus/providers/intake/petition_summary_embeddings/openai/openai_petition_summary_embeddings_provider.py`
- **Interface implementada (port):** `PetitionSummaryEmbeddingsProvider`
- **Biblioteca/SDK utilizado:** `OpenAI`
- **Metodos:**
  - `generate(petition_summary: PetitionSummary) -> list[PetitionSummaryEmbedding]` - gera embeddings a partir dos campos estruturados do resumo usando `text-embedding-3-large`, com chunking semantico voltado para busca de precedentes.

## Camada PubSub (Eventos de Dominio)

- **Localizacao:** `src/animus/core/intake/domain/events/analysis_precedents_search_requested_event.py` (**novo arquivo**)
- **`NAME`:** `"intake/analysis.precedents.search.requested"`
- **Payload:** `analysis_id: str`, `courts: list[str]`, `precedent_kinds: list[str]`, `limit: int`

## Camada PubSub (Jobs Inngest)

- **Localizacao:** `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py` (**novo arquivo**)
- **Evento consumido:** `AnalysisPrecedentsSearchRequestedEvent.name`
- **Dependencias:** repositories, providers, workflow e broker concretos montados no proprio job a partir do escopo transacional aberto para a execucao
- **Passos (`step.run`):**
  - `search_precedents` - instancia `UpdateAnalysisStatusUseCase(...)` e `SearchAnalysisPrecedentsUseCase(...)`, atualiza `Analysis.status` para `SEARCHING_PRECEDENTS` e executa a busca
  - `generate_syntheses_and_persist` - instancia `UpdateAnalysisStatusUseCase(...)`, atualiza `Analysis.status` para `GENERATING_SYNTHESIS`, executa o workflow de IA, limpa o conjunto atual com `AnalysisPrecedentsRepository.remove_many_by_analysis_id(...)`, persiste o novo conjunto com `AnalysisPrecedentsRepository.add_many_by_analysis_id(...)` e atualiza `Analysis.status` para `WAITING_PRECEDENT_CHOISE`
- **Idempotencia:** o job executa `remove_many_by_analysis_id(...)` e `add_many_by_analysis_id(...)` em chamadas separadas, mas dentro do mesmo escopo transacional; a formula de score e deterministica e o resultado final nao duplica linhas.

## Migracoes Alembic (se aplicavel)

- **Localizacao:** `migrations/versions/<timestamp>_create_analysis_precedents_table.py` (**novo arquivo**)
- **Operacoes:** criar `analysis_precedents` com PK composta (`analysis_id`, `precedent_id`) e FKs para `analyses` e `precedents`.
- **Reversibilidade:** `downgrade` remove a tabela; seguro enquanto nao houver dependencias externas de leitura sobre o conjunto persistido.

---

# 6. O que deve ser modificado?

## Camada Core

- **Arquivo:** `src/animus/core/intake/interfaces/precedents_embeddings_repository.py`
- **Mudanca:** alterar `find_many(...)` para receber `AnalysisPrecedentsSearchFilters` e um limite de candidatos coerente com o `limit` final.
- **Justificativa:** o filtro de `court` e `precedent_kind` precisa restringir o universo da busca vetorial, nao apenas filtrar o resultado depois da consulta.

- **Arquivo:** `src/animus/core/intake/interfaces/precedents_repository.py`
- **Mudanca:** substituir o lookup atual por um contrato baseado no identificador composto real do precedente e adicionar leitura em lote (`find_many_by_identifiers(...)`).
- **Justificativa:** a chave unica do dominio e `court + kind + number`, e a fase de busca precisa hidratar varios precedentes de uma vez sem N+1 desnecessario.

- **Arquivo:** `src/animus/core/intake/interfaces/synthesize_analysis_precedents_workflow.py`
- **Mudanca:** incluir `petition_summary: PetitionSummary` na assinatura de `run(...)`.
- **Justificativa:** a sintese explicativa depende explicitamente da relacao entre cada precedente e o resumo da peticao; a interface atual nao fornece esse contexto.

- **Arquivo:** `src/animus/core/intake/interfaces/__init__.py`
- **Mudanca:** exportar `AnalysisPrecedentsRepository`, `PetitionSummaryEmbeddingsProvider` e `SynthesizeAnalysisPrecedentsWorkflow`, corrigindo os nomes atualmente inconsistentes.
- **Justificativa:** estabilizar imports publicos do contexto `intake` para os novos fluxos de busca.

- **Arquivo:** `src/animus/core/intake/domain/structures/precedent_status.py`
- **Mudanca:** **Nao aplicavel**.
- **Justificativa:** a selecao de status validos para busca fica a cargo do pipeline que popula o Qdrant; esta feature nao precisa revalidar ou ampliar o enum para executar a busca.

- **Arquivo:** `src/animus/core/intake/domain/structures/__init__.py`
- **Mudanca:** exportar corretamente `PetitionSummaryEmbedding` e o novo `AnalysisPrecedentsSearchFilters`.
- **Justificativa:** o barrel atual nao reflete os nomes reais usados no dominio de embeddings do resumo.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/__init__.py`
- **Mudanca:** exportar `AnalysisPrecedentsSearchFiltersDto`.
- **Justificativa:** tornar o DTO de filtros acessivel para controller, use cases e evento assinado.

- **Arquivo:** `src/animus/core/intake/domain/events/__init__.py`
- **Mudanca:** exportar `AnalysisPrecedentsSearchRequestedEvent` no modulo de eventos do contexto.
- **Justificativa:** manter o modulo publico de eventos do contexto consistente com o fluxo assincrono completo.

- **Arquivo:** `src/animus/core/intake/domain/errors/__init__.py`
- **Mudanca:** exportar `PetitionSummaryUnavailableError`.
- **Justificativa:** permitir traducao HTTP consistente da pre-condicao de resumo ausente.

## Camada Database

- **Arquivo:** `src/animus/database/qdrant/qdrant_precedents_embeddings_repository.py`
- **Mudanca:** suportar filtros por `court` e `kind` na busca, respeitando o novo contrato do port.
- **Justificativa:** a busca precisa acontecer dentro do universo filtrado pelo usuario para cumprir o PRD.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_precendents_repository.py`
- **Mudanca:** corrigir a semantica do identificador de precedente e implementar leitura em lote por identificadores compostos.
- **Justificativa:** o repository atual nao honra a chave unica descrita no Glossario e nao atende a fase de hidratacao da busca.

- **Arquivo:** `src/animus/database/sqlalchemy/models/intake/__init__.py`
- **Mudanca:** exportar `AnalysisPrecedentModel`.
- **Justificativa:** manter o pacote de models do contexto `intake` alinhado aos novos models persistidos.

- **Arquivo:** `src/animus/database/sqlalchemy/mappers/intake/__init__.py`
- **Mudanca:** exportar `AnalysisPrecedentMapper`.
- **Justificativa:** estabilizar imports internos da camada `database`.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/__init__.py`
- **Mudanca:** exportar `SqlalchemyAnalysisPrecedentsRepository`.
- **Justificativa:** permitir o uso do repository concreto sem depender de caminhos internos volateis.

## Camada REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudanca:** exportar `SearchAnalysisPrecedentsController`, `ListAnalysisPrecedentsController`, `ListAnalysisPetitionsController`, `GetAnalysisStatusController` e `ChooseAnalysisPrecedentController`.
- **Justificativa:** manter o pacote publico de controllers do contexto coerente com a nova superficie HTTP.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudanca:** exportar `ListAnalysisPrecedentsUseCase` e `ListAnalysisPetitionsUseCase`.
- **Justificativa:** manter o barrel publico de casos de uso do contexto `intake` consistente com os fluxos de leitura e escrita da feature.

## Camada Routers

- **Arquivo:** `src/animus/routers/intake/intake_router.py`
- **Mudanca:** registrar `SearchAnalysisPrecedentsController`, `ListAnalysisPrecedentsController`, `ListAnalysisPetitionsController`, `GetAnalysisStatusController` e `ChooseAnalysisPrecedentController` no `IntakeRouter` existente.
- **Justificativa:** expor a requisicao assincrona, a leitura dos precedentes e peticoes da analise, o polling de status e a confirmacao do precedente escolhido no mesmo contexto funcional que ja agrupa peticoes, resumo e busca de precedentes.

## Camada Pipes

- **Arquivo:** `src/animus/pipes/ai_pipe.py`
- **Mudanca:** adicionar `get_synthesize_analysis_precedents_workflow() -> SynthesizeAnalysisPrecedentsWorkflow`.
- **Justificativa:** manter a montagem do workflow concreto de AI centralizada no `AiPipe`, em linha com as regras da camada AI.

## Camada AI

- **Arquivo:** `src/animus/ai/agno/teams/intake_teams.py`
- **Mudanca:** adicionar um agente dedicado a sintetizar a relacao entre `PetitionSummary` e lista de precedentes.
- **Justificativa:** reaproveitar o team do contexto `intake` em vez de criar um team paralelo para um unico agente adicional.

- **Arquivo:** `src/animus/ai/agno/outputs/intake/__init__.py`
- **Mudanca:** exportar `AnalysisPrecedentsSynthesisOutput`.
- **Justificativa:** manter os outputs estruturados do contexto `intake` acessiveis pelo workflow e pelo team.

- **Arquivo:** `src/animus/ai/agno/outputs/__init__.py`
- **Mudanca:** exportar `AnalysisPrecedentsSynthesisOutput` junto de `PetitionSummaryOutput`.
- **Justificativa:** estabilizar o barrel publico de outputs Agno.

- **Arquivo:** `src/animus/ai/agno/workflows/intake/__init__.py`
- **Mudanca:** exportar `AgnoSynthesizeAnalysisPrecedentsWorkflow`.
- **Justificativa:** manter o pacote de workflows do contexto consistente com as implementacoes concretas disponiveis.

## Camada PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/__init__.py`
- **Mudanca:** exportar `SearchAnalysisPrecedentsJob`.
- **Justificativa:** alinhar o pacote de jobs do contexto `intake` ao novo job de busca.

- **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
- **Mudanca:** registrar `SearchAnalysisPrecedentsJob.handle(inngest)` no bootstrap do Inngest.
- **Justificativa:** sem o registro, o evento publicado pelo endpoint nao dispara processamento algum.

---

# 7. O que deve ser removido?

**Nao aplicavel**.

---

# 8. Decisoes Tecnicas e Trade-offs

- **Decisao:** manter o endpoint de requisicao assincrono e publicar apenas um evento de inicio de job.
  - **Alternativas consideradas:** executar a busca e a sintese no ciclo da request; usar endpoint sincrono com polling apenas do lado do cliente.
  - **Motivo da escolha:** a busca vetorial e a chamada ao LLM sao operacoes potencialmente lentas e ja existe infraestrutura Inngest no projeto.
  - **Impactos / trade-offs:** o contrato HTTP fica mais leve (`202`), mas o cliente precisa consultar o estado da `Analysis` para acompanhar o progresso.

- **Decisao:** usar `AnalysisPrecedentsSearchFilters` como `Structure` de dominio, em vez de repassar listas de `str` e `int` soltas por todo o fluxo.
  - **Alternativas consideradas:** usar apenas `_Body` do controller; passar named params primitivos do endpoint direto para job e repositories.
  - **Motivo da escolha:** filtros de `court` e `precedent_kind` exigem conversao para tipos de dominio e validacao de faixa para `limit`.
  - **Impactos / trade-offs:** adiciona um DTO/Structure novo, mas centraliza a validacao e evita regra de negocio no `controller` e no job.

- **Decisao:** persistir o resultado final com `remove_many_by_analysis_id(...)` seguido de `add_many_by_analysis_id(...)`, em vez de um metodo unico de replace ou `upsert` por linha.
  - **Alternativas consideradas:** usar `replace_many_by_analysis_id(...)`; usar apenas `add_many(...)`; usar `upsert` por linha mantendo registros antigos.
  - **Motivo da escolha:** segue a preferencia de contratos explicitos por operacao e deixa claro no repository quando o job esta limpando estado anterior e quando esta gravando o novo conjunto.
  - **Impactos / trade-offs:** aumenta o numero de chamadas ao repository, mas melhora a clareza do contrato; a atomicidade continua dependente de ambas ocorrerem na mesma transacao.

- **Decisao:** filtrar `court` e `precedent_kind` diretamente na consulta vetorial e assumir o Qdrant como fonte ja saneada para status validos.
  - **Alternativas consideradas:** revalidar status no `SearchAnalysisPrecedentsUseCase`; ampliar o enum de `PrecedentStatus` para cobrir todos os casos do Glossario nesta task.
  - **Motivo da escolha:** os precedentes indexados no Qdrant ja passaram pela validacao de status necessaria para busca.
  - **Impactos / trade-offs:** simplifica o fluxo desta feature e evita logica redundante, mas mantem a corretude dependente do pipeline de ingestao/indexacao.

- **Decisao:** o workflow de sintese recebe `PetitionSummary` explicitamente na assinatura.
  - **Alternativas consideradas:** manter a interface atual recebendo apenas a lista de precedentes; passar apenas `analysis_id` e deixar o workflow buscar o resumo internamente.
  - **Motivo da escolha:** a relacao com o caso inicial e o dado central da sintese; receber o resumo explicitamente mantem o contrato de AI orientado a dados de dominio, nao a lookup implcito.
  - **Impactos / trade-offs:** a interface muda e exige atualizacao do `AiPipe`, mas o workflow fica mais previsivel e menos acoplado a repository.

- **Decisao:** usar `OpenAI` embeddings no `PetitionSummary`.
  - **Alternativas consideradas:** usar `Gemini` embeddings; manter um provider local de embeddings; concatenar tudo em um unico texto e gerar apenas um vetor.
  - **Motivo da escolha:** o projeto ja possui providers OpenAI em uso nos fluxos ativos, reduz o peso operacional da imagem e elimina a dependencia do stack local `torch`/CUDA.
  - **Impactos / trade-offs:** simplifica deploy e build, mas troca um modelo local por uma dependencia de API externa para geracao dos embeddings.

- **Decisao:** manter as rotas sob o `IntakeRouter` existente.
  - **Alternativas consideradas:** criar um router dedicado a `analyses` fora de `/intake`; expor paths nus fora do contexto atual.
  - **Motivo da escolha:** toda a superficie HTTP deste dominio continua agrupada em `src/animus/routers/intake/intake_router.py` com prefixo `/intake`.
  - **Impactos / trade-offs:** preserva consistencia com a codebase atual e concentra busca, polling e escolha do precedente no mesmo namespace HTTP.

---

# 9. Diagramas e Referencias

- **Fluxo de dados:**

```text
GET /intake/analyses/{analysis_id}/status
  -> AuthPipe.get_account_id_from_request()
  -> IntakePipe.verify_analysis_by_account_from_request(...)
  -> analysis.status.dto
  -> 200 AnalysisStatusDto

GET /intake/analyses/{analysis_id}/precedents
  -> AuthPipe.get_account_id_from_request()
  -> IntakePipe.verify_analysis_by_account_from_request(...)
  -> ListAnalysisPrecedentsUseCase
       -> AnalysisPrecedentsRepository.find_many_by_analysis_id(...)
  -> 200 list[AnalysisPrecedentDto]

GET /intake/analyses/{analysis_id}/petitions
  -> AuthPipe.get_account_id_from_request()
  -> IntakePipe.verify_analysis_by_account_from_request(...)
  -> ListAnalysisPetitionsUseCase
       -> PetitionsRepository.find_all_by_analysis_id_ordered_by_uploaded_at(...)
       -> PetitionSummariesRepository.find_by_petition_id(...)
  -> 200 ListResponse[AnalysisPetition]

PATCH /intake/analyses/{analysis_id}/precedents/choose?court={court}&kind={kind}&number={number}
  -> AuthPipe.get_account_id_from_request()
  -> IntakePipe.verify_analysis_by_account_from_request(...)
  -> ChooseAnalysisPrecedentUseCase
       -> AnalysisPrecedentsRepository.find_many_by_analysis_id(...)
       -> AnalysisPrecedentsRepository.choose_by_analysis_id_and_precedent_id(...)
       -> AnalisysesRepository.find_by_id(...)
       -> AnalisysesRepository.replace(..., status=PRECEDENT_CHOSED)
  -> 200 AnalysisStatusDto

POST /intake/analyses/{analysis_id}/precedents/search
  -> AuthPipe.get_account_id_from_request()
  -> IntakePipe.verify_analysis_by_account_from_request(...)
  -> RequestAnalysisPrecedentsSearchUseCase
       -> PetitionSummariesRepository.find_by_analysis_id(...)
       -> AnalysisPrecedentsSearchFilters.create(...)
       -> Broker.publish(AnalysisPrecedentsSearchRequestedEvent)
  -> 202 Accepted

AnalysisPrecedentsSearchRequestedEvent
  -> SearchAnalysisPrecedentsJob
       -> abre session e monta repositories/providers/workflow
       -> step.run('search_precedents')
            -> instancia UpdateAnalysisStatusUseCase(...)
            -> instancia SearchAnalysisPrecedentsUseCase(...)
            -> atualiza status SEARCHING_PRECEDENTS
            -> PetitionSummariesRepository.find_by_analysis_id(...)
            -> PetitionSummaryEmbeddingsProvider.generate(...)
            -> PrecedentsEmbeddingsRepository.find_many(...)
            -> PrecedentsRepository.find_many_by_identifiers(...)
            -> calcular applicability_percentage
       -> step.run('generate_syntheses_and_persist')
            -> instancia UpdateAnalysisStatusUseCase(...)
            -> atualiza status GENERATING_SYNTHESIS
            -> SynthesizeAnalysisPrecedentsWorkflow.run(...)
            -> AnalysisPrecedentsRepository.remove_many_by_analysis_id(...)
            -> AnalysisPrecedentsRepository.add_many_by_analysis_id(...)
            -> instancia UpdateAnalysisStatusUseCase(...)
            -> atualiza status WAITING_PRECEDENT_CHOISE
       -> except Exception
            -> instancia UpdateAnalysisStatusUseCase(...)
            -> atualiza status FAILED
            -> raise
```

- **Fluxo assincrono:**

```text
Controller
  -> AnalysisPrecedentsSearchRequestedEvent
  -> Inngest job
       -> status SEARCHING_PRECEDENTS
       -> busca vetorial + score
       -> status GENERATING_SYNTHESIS
       -> Gemini sintetiza relacao com a peticao
       -> persistencia em analysis_precedents
       -> status WAITING_PRECEDENT_CHOISE

PATCH choose endpoint
  -> marca um unico precedent como chosen
  -> status PRECEDENT_CHOSED
```

- **Referencias:**
  - `src/animus/rest/controllers/intake/create_petition_controller.py`
  - `src/animus/rest/controllers/intake/summarize_petition_controller.py`
  - `src/animus/rest/controllers/intake/get_analysis_status_controller.py` (**novo arquivo**)
  - `src/animus/rest/controllers/intake/list_analysis_petitions_controller.py` (**novo arquivo**)
  - `src/animus/rest/controllers/intake/list_analysis_precedents_controller.py` (**novo arquivo**)
  - `src/animus/rest/controllers/intake/choose_analysis_precedent_controller.py` (**novo arquivo**)
  - `src/animus/core/intake/use_cases/list_analysis_petitions_use_case.py` (**novo arquivo**)
  - `src/animus/core/intake/use_cases/list_analysis_precedents_use_case.py` (**novo arquivo**)
  - `src/animus/core/intake/domain/structures/analysis_petition.py`
  - `src/animus/routers/intake/intake_router.py`
  - `src/animus/pipes/intake_pipe.py`
  - `src/animus/pipes/pubsub_pipe.py`
  - `src/animus/core/intake/use_cases/create_petition_summary_use_case.py`
  - `src/animus/core/intake/domain/structures/analysis_precedent.py`
  - `src/animus/core/intake/interfaces/petition_summaries_repository.py`
  - `src/animus/database/qdrant/qdrant_precedents_embeddings_repository.py`
  - `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`
  - `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_summaries_repository.py`
  - `src/animus/pubsub/inngest/jobs/intake/vectorize_precedents_job.py`
  - `src/animus/ai/agno/workflows/intake/agno_summarize_petition_workflow.py`
  - `src/animus/ai/agno/teams/intake_teams.py`

---

# 10. Pendencias / Duvidas

**Sem pendencias**.
