---
title: Leitura de Peticao e Summary por analise
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/CID5
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-61
status: closed
last_updated_at: 2026-04-02
---

# 1. Objetivo

Corrigir o fluxo de upload de peticoes para que uma nova `Petition` vinculada a uma `Analysis` substitua corretamente a anterior no banco e no storage. Tecnicamente, a entrega deve manter os contratos HTTP atuais, remover a `Petition` anterior e seu `PetitionSummary` associado, publicar `PetitionReplacedEvent` para limpeza assincrona do arquivo antigo no GCS e atualizar o `Analysis.status` para `PETITION_UPLOADED` apos a persistencia.

---

# 2. Escopo

## 2.1 In-scope

- Ajustar `CreatePetitionUseCase` para tratar substituicao de peticao na mesma analise.
- Publicar `PetitionReplacedEvent` quando ja existir uma peticao para a `Analysis`.
- Remover a `Petition` anterior do banco de modo que o `PetitionSummary` relacionado seja removido junto.
- Criar job Inngest para excluir o arquivo antigo via `FileStorageProvider`.
- Completar o adaptador `GcsFileStorageProvider` com remocao fisica de arquivos.
- Atualizar `Analysis.status` para `PETITION_UPLOADED` no fluxo de criacao/substituicao de peticao.
- Adicionar endpoint para buscar `Petition` por `analysis_id`.
- Adicionar endpoint para buscar `PetitionSummary` por `petition_id`.
- Manter o endpoint atual de criacao de peticao (`POST /intake/petitions`) como ponto de persistencia da nova peticao apos o upload via Signed URL.

## 2.2 Out-of-scope

- Alterar contrato HTTP de `POST /intake/petitions`.
- Alterar contrato HTTP de `POST /storage/analyses/{analysis_id}/petitions/upload`.
- Resetar `Analysis.status` para `WAITING_PETITION` durante a substituicao.
- Remover `analysis_precedents` ou sinteses ja geradas.
- Introduzir novos providers de storage ou mudar bucket/credenciais.

---

# 3. Requisitos

## 3.1 Funcionais

- Ao persistir uma nova `Petition` para uma `Analysis` que ja possui uma peticao, o sistema deve substituir a anterior.
- A substituicao deve publicar `PetitionReplacedEvent` com o `petition_document_path` do arquivo anterior.
- A `Petition` anterior deve ser removida do repositorio antes da persistencia da nova.
- O `PetitionSummary` associado a peticao removida deve deixar de existir apos a substituicao.
- O endpoint de criacao de peticao deve continuar validando ownership da `Analysis` pela conta autenticada.
- Apos criar/substituir a peticao, o sistema deve atualizar `Analysis.status` para `PETITION_UPLOADED`.
- A resposta de `CreatePetitionUseCase.execute(analysis_id: str, uploaded_at: str, document: PetitionDocumentDto) -> PetitionDto` deve continuar retornando a nova peticao persistida.
- O sistema deve expor `GET /intake/analyses/{analysis_id}/petition` para retornar a `PetitionDto` atual da analise autenticada.
- O sistema deve expor `GET /intake/petitions/{petition_id}/summary` para retornar a `PetitionSummaryDto` da peticao autenticada.

## 3.2 Nao funcionais

- **Seguranca:** a substituicao continua condicionada a ownership validado por `IntakePipe.verify_analysis_by_account_from_request(...)`.
- **Idempotencia:** o job `RemovePetitionDocumentFileJob` deve ser seguro em reexecucoes; a remocao do blob no GCS deve tratar arquivo inexistente como no-op.
- **Resiliencia:** a exclusao do arquivo antigo deve ocorrer assincronamente para nao bloquear a resposta do endpoint de persistencia da nova peticao.
- **Compatibilidade retroativa:** nao deve haver mudanca de payload ou `response_model` nos endpoints existentes de upload e criacao de peticao.

---

# 4. O que ja existe?

## Core

- **`CreatePetitionUseCase`** (`src/animus/core/intake/use_cases/create_petition_use_case.py`) — use case atual que cria e adiciona uma `Petition`; sera estendido para tratar substituicao e atualizacao de status da analise.
- **`PetitionsRepository`** (`src/animus/core/intake/interfaces/petitions_repository.py`) — port atual de persistencia de peticoes; ainda nao possui lookup direto por `analysis_id` nem remocao.
- **`PetitionReplacedEvent`** (`src/animus/core/intake/domain/events/petition_replaced_event.py`) — evento de dominio ja existente para sinalizar substituicao do arquivo da peticao.
- **`RequestAnalysisPrecedentsSearchUseCase`** (`src/animus/core/intake/use_cases/request_analysis_precedents_search_use_case.py`) — referencia de publicacao de eventos via `Broker` a partir de use case.
- **`ListAnalysisPetitionsUseCase`** (`src/animus/core/intake/use_cases/list_analysis_petitions_use_case.py`) — referencia de leitura orientada a `UseCase` no contexto `intake` para endpoints `GET`.

## Database

- **`PetitionModel`** (`src/animus/database/sqlalchemy/models/intake/petition_model.py`) — model ORM de `petitions`; possui relacao `summary` com `cascade='all, delete-orphan'`.
- **`PetitionSummaryModel`** (`src/animus/database/sqlalchemy/models/intake/petition_summary_model.py`) — model ORM de `petition_summaries`, vinculada por `petition_id`.
- **`SqlalchemyPetitionsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petitions_repository.py`) — implementacao concreta atual; so adiciona e lista peticoes.
- **`SqlalchemyPetitionSummariesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_summaries_repository.py`) — referencia do recurso agregado que hoje depende da `Petition` para lookup por `analysis_id`.

## REST

- **`CreatePetitionController`** (`src/animus/rest/controllers/intake/create_petition_controller.py`) — endpoint `POST /intake/petitions`; hoje valida ownership e chama `CreatePetitionUseCase` sem `Broker`.
- **`GeneratePetitionUploadUrlController`** (`src/animus/rest/controllers/storage/generate_petition_upload_url_controller.py`) — endpoint que gera o path unico de upload no storage; serve como entrada anterior ao `POST /intake/petitions`.

## Routers

- **`IntakeRouter`** (`src/animus/routers/intake/intake_router.py`) — router que registra `CreatePetitionController`.
- **`StorageRouter`** (`src/animus/routers/storage/storage_router.py`) — router do endpoint de Signed URL ja existente.

## Pipes

- **`IntakePipe.verify_analysis_by_account_from_request`** (`src/animus/pipes/intake_pipe.py`) — guard de ownership reutilizado pelo fluxo de criacao de peticao.
- **`DatabasePipe.get_petitions_repository_from_request`** (`src/animus/pipes/database_pipe.py`) — provider atual do repositório de peticoes.
- **`PubSubPipe.get_broker_from_request`** (`src/animus/pipes/pubsub_pipe.py`) — provider atual de `Broker`; ainda nao e consumido no controller de criacao de peticao.

## Providers

- **`FileStorageProvider`** (`src/animus/core/storage/interfaces/file_storage_provider.py`) — port ja exposto com `remove_files(file_paths: list[FilePath]) -> None`.
- **`GcsFileStorageProvider`** (`src/animus/providers/storage/file_storage/gcs/gcs_file_storage_provider.py`) — adaptador atual do GCS; ja gera upload URL e baixa arquivos, mas ainda nao implementa `remove_files(...)`.

## PubSub

- **`InngestBroker`** (`src/animus/pubsub/inngest/inngest_broker.py`) — adaptador atual de publicacao de eventos via Inngest.
- **`SendAccountVerificationEmailJob`** (`src/animus/pubsub/inngest/jobs/auth/send_account_verification_email_job.py`) — referencia de job sem acesso ao banco, acionado apenas por evento.
- **`SearchAnalysisPrecedentsJob`** (`src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`) — referencia de registro de job Inngest no contexto `intake`.

---

# 5. O que deve ser criado?

## Camada PubSub (Jobs Inngest)

- **Localizacao:** `src/animus/pubsub/inngest/jobs/intake/remove_petition_document_file_job.py` (**novo arquivo**)
- **Evento consumido:** `PetitionReplacedEvent.name` (`"intake/petition.replaced"`) com payload `{ petition_document_path: str }`
- **Dependencias:** `FileStorageProvider` concreto (`GcsFileStorageProvider` via instanciacao direta no job, seguindo o padrao de `SendAccountVerificationEmailJob`)
- **Passos (`step.run`):**
  - `normalize_payload` — normaliza `petition_document_path` para `str`
  - `remove_petition_document_file` — converte para `FilePath` e executa `file_storage_provider.remove_files([file_path])`
- **Idempotencia:** se o blob ja nao existir, o job deve encerrar com sucesso sem falha; retries do Inngest nao podem transformar ausencia do arquivo em erro terminal.

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/intake/use_cases/get_analysis_petition_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `PetitionsRepository`
- **Metodo principal:** `execute(analysis_id: str) -> PetitionDto` — busca a peticao atual da analise e retorna seu DTO; lanca `PetitionNotFoundError` se a analise nao tiver peticao persistida.
- **Fluxo resumido:** converter `analysis_id` para `Id` -> buscar `PetitionsRepository.find_by_analysis_id(...)` -> retornar `petition.dto`.

- **Localizacao:** `src/animus/core/intake/use_cases/get_petition_summary_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `PetitionSummariesRepository`
- **Metodo principal:** `execute(petition_id: str) -> PetitionSummaryDto` — busca o summary da peticao e retorna seu DTO; lanca `PetitionSummaryUnavailableError` se nao existir resumo para a peticao.
- **Fluxo resumido:** converter `petition_id` para `Id` -> buscar `PetitionSummariesRepository.find_by_petition_id(...)` -> retornar `petition_summary.dto`.

---

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/use_cases/create_petition_use_case.py`
- **Mudanca:** estender o construtor para receber `analisyses_repository: AnalisysesRepository` e `broker: Broker` alem de `petitions_repository: PetitionsRepository`; no `execute(analysis_id: str, uploaded_at: str, document: PetitionDocumentDto) -> PetitionDto`, buscar peticao existente da mesma analise, publicar `PetitionReplacedEvent`, remover a peticao anterior, atualizar a `Analysis` para `PETITION_UPLOADED` e entao adicionar a nova.
- **Justificativa:** o use case e o ponto correto para orquestrar substituicao de peticao e atualizacao de status mantendo o `core` independente de HTTP e infraestrutura.

- **Arquivo:** `src/animus/core/intake/interfaces/petitions_repository.py`
- **Mudanca:** adicionar os contratos `find_by_analysis_id(analysis_id: Id) -> Petition | None` e `remove(petition_id: Id) -> None`.
- **Justificativa:** o use case precisa consultar e remover a peticao atual sem depender de detalhes de SQLAlchemy.

- **Arquivo:** `src/animus/core/intake/domain/events/__init__.py`
- **Mudanca:** exportar `PetitionReplacedEvent` em `__all__`.
- **Justificativa:** estabilizar o import publico do evento para o wiring do job e do use case.

## Database

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petitions_repository.py`
- **Mudanca:** implementar `find_by_analysis_id(...)` com busca por `analysis_id` e `remove(...)` com delecao ORM (`session.delete(model)`) da `PetitionModel` carregada.
- **Justificativa:** a delecao ORM permite reaproveitar o `cascade='all, delete-orphan'` ja existente em `PetitionModel.summary`, removendo o `PetitionSummary` sem criar um fluxo de delecao paralelo.

- **Arquivo:** `src/animus/database/sqlalchemy/repositories/intake/__init__.py`
- **Mudanca:** manter o export do repositório atualizado caso a implementacao receba novos metodos publicos utilizados no restante do projeto.
- **Justificativa:** preservar consistencia dos imports agregados do modulo.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/create_petition_controller.py`
- **Mudanca:** injetar `broker: Broker` via `Depends(PubSubPipe.get_broker_from_request)` e instanciar `CreatePetitionUseCase` com `petitions_repository`, `analisyses_repository` e `broker`, sem alterar o `*Body` nem o `response_model`.
- **Justificativa:** o controller continua fino e passa a fornecer ao use case as dependencias necessarias para publicacao do evento e atualizacao de status da analise.

- **Arquivo:** `src/animus/rest/controllers/intake/get_analysis_petition_controller.py` (**novo arquivo**)
- **Mudanca:** criar controller `GET /analyses/{analysis_id}/petition`, `status_code=200`, `response_model=PetitionDto`, usando `IntakePipe.verify_analysis_by_account_from_request(...)` e `GetAnalysisPetitionUseCase`.
- **Justificativa:** a API ainda nao possui um endpoint singular para recuperar a peticao atual da analise; o fluxo precisa existir sem reaproveitar a listagem.

- **Arquivo:** `src/animus/rest/controllers/intake/get_petition_summary_controller.py` (**novo arquivo**)
- **Mudanca:** criar controller `GET /petitions/{petition_id}/summary`, `status_code=200`, `response_model=PetitionSummaryDto`, usando guard por ownership da peticao e `GetPetitionSummaryUseCase`.
- **Justificativa:** hoje so existe `POST /petitions/{petition_id}/summary`; falta o endpoint de consulta do resumo persistido.

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudanca:** exportar `GetAnalysisPetitionController` e `GetPetitionSummaryController`.
- **Justificativa:** manter o padrao de agregacao publica de controllers do contexto.

## Routers

- **Arquivo:** `src/animus/routers/intake/intake_router.py`
- **Mudanca:** registrar `GetAnalysisPetitionController.handle(router)` e `GetPetitionSummaryController.handle(router)`.
- **Justificativa:** anexar os novos endpoints ao modulo `intake`, mantendo o agrupamento por contexto.

## Providers

- **Arquivo:** `src/animus/providers/storage/file_storage/gcs/gcs_file_storage_provider.py`
- **Mudanca:** implementar `remove_files(file_paths: list[FilePath]) -> None` usando o cliente do GCS para remover os blobs correspondentes; blobs inexistentes devem ser ignorados.
- **Justificativa:** o port `FileStorageProvider` ja exige remocao de arquivos, e o novo job depende dessa operacao para evitar lixo no bucket.

## PubSub

- **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
- **Mudanca:** registrar `RemovePetitionDocumentFileJob.handle(inngest)` na lista de jobs do contexto `intake`.
- **Justificativa:** sem registro no composition root do Inngest, o evento publicado pelo `Broker` nao produz efeito.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/__init__.py`
- **Mudanca:** exportar `RemovePetitionDocumentFileJob`.
- **Justificativa:** manter o padrao de agregacao publica dos jobs do contexto.

---

# 7. O que deve ser removido?

**Nao aplicavel**.

---

# 8. Decisoes Tecnicas e Trade-offs

- **Decisao:** tratar a substituicao dentro de `CreatePetitionUseCase`.
- **Alternativas consideradas:** criar um novo `ReplacePetitionUseCase`; mover a logica para `CreatePetitionController`.
- **Motivo da escolha:** a substituicao e uma extensao direta da regra de criacao de peticao e depende de orquestracao de dominio, nao de transporte.
- **Impactos / trade-offs:** aumenta a responsabilidade do caso de uso atual, mas evita duplicacao de contrato HTTP e mantem o fluxo centrado no `core`.

- **Decisao:** atualizar `Analysis.status` para `PETITION_UPLOADED` dentro de `CreatePetitionUseCase` apos criacao/substituicao da peticao.
- **Alternativas consideradas:** manter status inalterado; atualizar status no controller.
- **Motivo da escolha:** o estado da analise apos upload de peticao e regra de dominio e deve ser consolidado no use case de criacao.
- **Impactos / trade-offs:** adiciona dependencia de `AnalisysesRepository` ao use case, mas garante consistencia do estado da analise no mesmo fluxo de dominio.

- **Decisao:** criar `GetAnalysisPetitionUseCase` e `GetPetitionSummaryUseCase` para os novos endpoints de leitura.
- **Alternativas consideradas:** consultar repositórios diretamente nos controllers; reaproveitar `ListAnalysisPetitionsUseCase` para derivar a peticao atual.
- **Motivo da escolha:** os controllers do projeto seguem o padrao de delegar ao `core`, e o endpoint singular deve expressar um contrato de leitura direto, sem acoplar a borda a detalhes de colecao.
- **Impactos / trade-offs:** adiciona dois casos de uso pequenos, mas preserva consistencia arquitetural.

- **Decisao:** adicionar um guard dedicado `verify_petition_by_account(...)` no `IntakePipe`.
- **Alternativas consideradas:** validar ownership do `petition_id` dentro do controller; consultar apenas `FilePath` como em `verify_petition_document_path_by_account(...)`.
- **Motivo da escolha:** o endpoint `GET /petitions/{petition_id}/summary` precisa de uma precondicao reutilizavel de acesso a peticao, nao apenas ao caminho do arquivo.
- **Impactos / trade-offs:** aumenta a superficie do `IntakePipe`, mas mantem a regra de acesso reutilizavel e os controllers finos.

- **Decisao:** adicionar `find_by_analysis_id(...)` e `remove(...)` em `PetitionsRepository`, sem criar `remove(...)` em `PetitionSummariesRepository`.
- **Alternativas consideradas:** remover `PetitionSummary` explicitamente por um novo metodo no repositorio de summaries; usar listagem ordenada existente para localizar a peticao atual.
- **Motivo da escolha:** `PetitionModel` ja possui relacao com `cascade='all, delete-orphan'`; usar delecao ORM da peticao e o menor ajuste consistente com a modelagem atual.
- **Impactos / trade-offs:** a implementacao concreta precisa evitar bulk delete para preservar o cascade ORM.

- **Decisao:** fazer a remocao do arquivo antigo de forma assincrona por `PetitionReplacedEvent` + job Inngest.
- **Alternativas consideradas:** excluir o arquivo sincronicamente dentro do use case; excluir via controller apos a resposta.
- **Motivo da escolha:** ja existe o padrao de eventos via `Broker` no projeto, e a exclusao fisica do arquivo e um efeito colateral de infraestrutura.
- **Impactos / trade-offs:** a publicacao do evento continua ocorrendo no fluxo da request, antes do commit final controlado pelo middleware, mantendo o mesmo trade-off de consistencia eventual ja adotado em outros fluxos orientados a evento.

- **Decisao:** atualizar apenas `Analysis.status` para `PETITION_UPLOADED` e preservar `analysis_precedents` ao substituir a peticao.
- **Alternativas consideradas:** manter status inalterado; resetar status para `WAITING_PETITION`; limpar precedentes e sinteses geradas.
- **Motivo da escolha:** o status deve refletir que existe peticao atual persistida sem ampliar escopo para reprocessamento dos dados derivados.
- **Impactos / trade-offs:** melhora a semantica de estado da analise, mantendo o risco conhecido de dados derivados representarem peticao anterior fora do escopo desta entrega.

- **Decisao:** manter os contratos HTTP atuais de upload e criacao de peticao.
- **Alternativas consideradas:** alterar endpoint de Signed URL para incorporar semantica de replace; criar endpoint dedicado de substituicao.
- **Motivo da escolha:** o ticket descreve correcao do fluxo interno, nao mudanca de API publica.
- **Impactos / trade-offs:** a semantica de substituicao continua sendo implicitamente disparada pelo mesmo `POST /intake/petitions` quando ja existe peticao para a analise.

---

# 9. Diagramas e Referencias

- **Fluxo de dados:**

```text
HTTP POST /intake/petitions
  -> IntakeRouter
  -> CreatePetitionController
  -> IntakePipe.verify_analysis_by_account_from_request(...)
  -> CreatePetitionUseCase.execute(analysis_id, uploaded_at, document)
      -> PetitionsRepository.find_by_analysis_id(analysis_id)
      -> [se existir]
         -> Broker.publish(PetitionReplacedEvent(old_document_path))
         -> PetitionsRepository.remove(old_petition_id)
            -> SQLAlchemy session.delete(PetitionModel)
            -> ORM cascade remove PetitionSummaryModel
      -> AnalisysesRepository.find_by_id(analysis_id)
      -> AnalisysesRepository.replace(analysis.status = PETITION_UPLOADED)
      -> PetitionsRepository.add(new_petition)
  -> Response 201 PetitionDto
```

```text
HTTP GET /intake/analyses/{analysis_id}/petition
  -> IntakeRouter
  -> GetAnalysisPetitionController
  -> IntakePipe.verify_analysis_by_account_from_request(...)
  -> GetAnalysisPetitionUseCase.execute(analysis_id)
      -> PetitionsRepository.find_by_analysis_id(analysis_id)
  -> Response 200 PetitionDto
```

```text
HTTP GET /intake/petitions/{petition_id}/summary
  -> IntakeRouter
  -> GetPetitionSummaryController
  -> IntakePipe.verify_petition_by_account(...)
  -> GetPetitionSummaryUseCase.execute(petition_id)
      -> PetitionSummariesRepository.find_by_petition_id(petition_id)
  -> Response 200 PetitionSummaryDto
```

- **Fluxo assincrono:**

```text
CreatePetitionUseCase
  -> Broker.publish(PetitionReplacedEvent)
  -> InngestBroker.send_sync(...)
  -> RemovePetitionDocumentFileJob
      -> step.run('normalize_payload')
      -> step.run('remove_petition_document_file')
      -> FileStorageProvider.remove_files([old_file_path])
      -> Google Cloud Storage delete blob
```

- **Referencias:**

- `src/animus/core/intake/use_cases/request_analysis_precedents_search_use_case.py` — exemplo de publicacao de evento a partir de use case.
- `src/animus/core/intake/use_cases/list_analysis_petitions_use_case.py` — exemplo de endpoint `GET` delegado a um `UseCase` de leitura.
- `src/animus/pubsub/inngest/jobs/auth/send_account_verification_email_job.py` — exemplo de job Inngest sem dependencia de banco.
- `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py` — exemplo de registro de job no contexto `intake`.
- `src/animus/database/sqlalchemy/models/intake/petition_model.py` — evidencia do cascade ORM entre `Petition` e `PetitionSummary`.
- `src/animus/rest/controllers/intake/create_petition_controller.py` — endpoint que aciona o caso de uso de criacao/substituicao.
- `src/animus/rest/controllers/intake/list_analysis_petitions_controller.py` — referencia de controller `GET` com guard de ownership da analise.
- `src/animus/rest/controllers/storage/generate_petition_upload_url_controller.py` — etapa anterior do fluxo de upload com path unico para a nova peticao.

---

# 10. Pendencias / Duvidas

**Sem pendencias**.

---

## Restricoes

- **Nao inclua testes automatizados na spec.**
- O `core` nao deve depender de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest` ou qualquer detalhe de infraestrutura — se a spec violar isso, corrija antes de escrever.
- Todos os caminhos citados devem existir no projeto **ou** estar explicitamente marcados como **novo arquivo**.
- **Nao invente** arquivos, metodos, contratos, schemas ou integracoes sem evidencia no PRD ou na codebase.
- Quando faltar informacao suficiente, registrar em **Pendencias / Duvidas** e usar a tool `question` se necessario.
- Toda referencia a codigo existente deve incluir caminho relativo real (`src/animus/...`).
- Se uma secao nao se aplicar, preencher explicitamente com **Nao aplicavel**.
- A spec deve ser consistente com os padroes da codebase (nomenclatura, organizacao de modulos, contratos e convencoes por camada).
- Schemas `*Body` de entrada sao sempre definidos **no arquivo do controller** que os utiliza — nunca em `validation/`. O repasse ao `UseCase` e via **named params** ou **`to_dto()`**, nunca conversao espalhada no corpo do endpoint.
