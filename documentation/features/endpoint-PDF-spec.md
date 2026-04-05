---
title: Endpoint de relatorio da analise para exportacao em PDF
prd: https://joaogoliveiragarcia.atlassian.net/wiki/x/AYAMAQ
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-50
status: closed
last_updated_at: 2026-04-04
---

# 1. Objetivo

Implementar o endpoint `GET /intake/analyses/{analysis_id}/report` para entregar, em uma unica resposta, os dados necessarios para geracao do PDF no mobile (`ANI-51`): `Analysis`, `Petition`, `PetitionSummary` e a lista de `AnalysisPrecedent` da analise com `is_chosen` e nivel de classificacao derivado de `applicability_percentage`. Tecnicamente, a entrega deve manter o padrao de controllers finos, concentrar a regra de agregacao no `core` e retornar erros consistentes com o contrato do ticket (`404` para analise inexistente e `403` para analise de outra conta).

---

# 2. Escopo

## 2.1 In-scope

- Criar `GetAnalysisReportUseCase` para agregar os dados do relatorio.
- Criar `GetAnalysisReportController` com rota `GET /analyses/{analysis_id}/report` no contexto `intake`.
- Registrar o novo controller no `IntakeRouter`.
- Ajustar `AnalysisReportDto` para retornar a lista de `AnalysisPrecedentDto` no lugar de `PrecedentDto` simples.
- Incluir no DTO de precedente um campo de classificacao (`classification_level`) para o consumo do PDF.
- Garantir contrato de erro: `404` quando `analysis_id` nao existir e `403` quando a analise nao pertencer ao `account_id` autenticado.

## 2.2 Out-of-scope

- Geracao/renderizacao de PDF no backend.
- Alterar o pipeline assincrono de busca/sintese de precedentes.
- Criar migration de banco ou alterar schema de `analysis_precedents`.
- Alterar regras de autenticacao (`AuthPipe`) ou middlewares globais.
- Introduzir novos providers, jobs Inngest ou eventos de dominio para este fluxo.

---

# 3. Requisitos

## 3.1 Funcionais

- O endpoint `GET /intake/analyses/{analysis_id}/report` deve retornar `200` com `AnalysisReportDto`.
- `AnalysisReportDto` deve conter:
  - `analysis: AnalysisDto`
  - `petition: PetitionDto`
  - `summary: PetitionSummaryDto`
  - `precedents: list[AnalysisPrecedentDto]`
- Cada item de `precedents` deve incluir `is_chosen` e `classification_level`.
- O `classification_level` deve ser derivado de `applicability_percentage` por regra deterministica no `UseCase`.
- O endpoint deve retornar `404` quando a analise nao existir (`AnalysisNotFoundError`).
- O endpoint deve retornar `403` quando a analise existir, mas pertencer a outra conta (`ForbiddenError`).
- O endpoint deve reutilizar os contratos atuais de leitura de peticao e resumo:
  - `PetitionNotFoundError` quando nao houver peticao para a analise.
  - `PetitionSummaryUnavailableError` quando nao houver resumo da peticao.

## 3.2 Nao funcionais

- **Performance:** fluxo deve ser somente leitura e sem IA no ciclo HTTP; a agregacao deve ocorrer com chamadas diretas aos repositórios ja existentes.
- **Seguranca:** autenticacao obrigatoria via `Bearer token` e validacao de ownership por `account_id`.
- **Observabilidade:** erros de dominio devem ser propagados para `AppErrorHandler`, preservando padrao de resposta HTTP do projeto.
- **Compatibilidade retroativa:** mudanca aditiva na API HTTP do contexto `intake`; sem impacto em endpoints existentes.

---

# 4. O que ja existe?

## Core

- **`AnalysisReportDto`** (`src/animus/core/intake/domain/structures/dtos/analysis_report_dto.py`) — contrato de relatorio ja existente, ainda modelado com `precedents: list[PrecedentDto]` e `chosen_precedent`.
- **`AnalysisPrecedentDto`** (`src/animus/core/intake/domain/structures/dtos/analysis_precedent_dto.py`) — DTO ja usado na listagem de precedentes; contem `is_chosen`, `applicability_percentage` e `synthesis`.
- **`AnalisysesRepository`** (`src/animus/core/intake/interfaces/analisyses_repository.py`) — porta para busca da analise por ID (`find_by_id`).
- **`PetitionsRepository`** (`src/animus/core/intake/interfaces/petitions_repository.py`) — porta para busca da peticao da analise (`find_by_analysis_id`).
- **`PetitionSummariesRepository`** (`src/animus/core/intake/interfaces/petition_summaries_repository.py`) — porta para busca do resumo por analise (`find_by_analysis_id`).
- **`AnalysisPrecedentsRepository`** (`src/animus/core/intake/interfaces/analysis_precedents_repository.py`) — porta para listagem de precedentes da analise (`find_many_by_analysis_id`).
- **`GetAnalysisUseCase`** (`src/animus/core/intake/use_cases/get_analysis_use_case.py`) — referencia de leitura por `analysis_id`, com validacao de ownership no `core`.
- **`AnalysisNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_not_found_error.py`) — erro de dominio mapeado para `404`.

## Database

- **`SqlalchemyAnalisysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`) — implementa lookup de analise por ID.
- **`SqlalchemyPetitionsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petitions_repository.py`) — implementa lookup de peticao por `analysis_id`.
- **`SqlalchemyPetitionSummariesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_summaries_repository.py`) — implementa lookup de summary por `analysis_id`.
- **`SqlalchemyAnalysisPrecedentsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analysis_precedents_repository.py`) — retorna precedentes ordenados por `applicability_percentage desc`.
- **`AnalysisPrecedentModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_precedent_model.py`) — persistencia de `is_chosen`, `applicability_percentage` e `synthesis`.

## REST

- **`GetAnalysisController`** (`src/animus/rest/controllers/intake/get_analysis_controller.py`) — referencia de endpoint `GET` por `analysis_id` com `AuthPipe` + `DatabasePipe`.
- **`ListAnalysisPrecedentsController`** (`src/animus/rest/controllers/intake/list_analysis_precedents_controller.py`) — referencia de retorno `list[AnalysisPrecedentDto]` no contexto `intake`.
- **`GetAnalysisPetitionController`** (`src/animus/rest/controllers/intake/get_analysis_petition_controller.py`) — referencia de leitura de peticao por analise.
- **`GetAnalysisStatusController`** (`src/animus/rest/controllers/intake/get_analysis_status_controller.py`) — referencia de endpoint de leitura simples no mesmo modulo.
- **`AppErrorHandler`** (`src/animus/rest/handlers/app_error_handler.py`) — tradutor global de erros de dominio para status HTTP (`404`, `403`, `409`, etc.).

## Routers

- **`IntakeRouter`** (`src/animus/routers/intake/intake_router.py`) — router agregador com prefixo `/intake` e registro dos controllers do contexto.

## Pipes

- **`AuthPipe.get_account_id_from_request`** (`src/animus/pipes/auth_pipe.py`) — resolve conta autenticada do token.
- **`DatabasePipe`** (`src/animus/pipes/database_pipe.py`) — expoe os repositórios concretos necessarios para o novo endpoint.

## Lacunas identificadas

- Nao existe `GetAnalysisReportUseCase` para agregacao do relatorio completo.
- Nao existe `GET /analyses/{analysis_id}/report` registrado no `IntakeRouter`.
- `AnalysisReportDto` atual nao representa o contrato esperado no ticket (lista de `AnalysisPrecedentDto` com classificacao).

---

# 5. O que deve ser criado?

## Camada Core (Use Cases)

- **Localizacao:** `src/animus/core/intake/use_cases/get_analysis_report_use_case.py` (**novo arquivo**)
- **Dependencias (ports injetados):** `AnalisysesRepository`, `PetitionsRepository`, `PetitionSummariesRepository`, `AnalysisPrecedentsRepository`
- **Metodo principal:** `execute(analysis_id: str, account_id: str) -> AnalysisReportDto` — agrega e retorna o relatorio completo da analise.
- **Fluxo resumido:**
  - normaliza `analysis_id` e `account_id` para `Id`
  - busca analise por `find_by_id`
  - valida ownership (`analysis.account_id == account_id`), levantando `ForbiddenError` em divergencia
  - busca peticao e resumo por `analysis_id`
  - busca precedentes vinculados por `analysis_id`
  - deriva `classification_level` para cada precedente
  - retorna `AnalysisReportDto`
- **Metodo auxiliar interno:** `_classify_precedent(applicability_percentage: float | None) -> str` — aplica regra de classificacao para `APPLICABLE`, `POSSIBLY_APPLICABLE` e `NOT_APPLICABLE`.

## Camada REST (Controllers)

- **Localizacao:** `src/animus/rest/controllers/intake/get_analysis_report_controller.py` (**novo arquivo**)
- **`*Body`:** **Nao aplicavel**.
- **Metodo HTTP e path:** `GET /analyses/{analysis_id}/report`
- **`status_code`:** `200`
- **`response_model`:** `AnalysisReportDto`
- **Dependencias injetadas via `Depends`:**
  - `account_id: Id` via `AuthPipe.get_account_id_from_request`
  - `analisyses_repository: AnalisysesRepository` via `DatabasePipe.get_analisyses_repository_from_request`
  - `petitions_repository: PetitionsRepository` via `DatabasePipe.get_petitions_repository_from_request`
  - `petition_summaries_repository: PetitionSummariesRepository` via `DatabasePipe.get_petition_summaries_repository_from_request`
  - `analysis_precedents_repository: AnalysisPrecedentsRepository` via `DatabasePipe.get_analysis_precedents_repository_from_request`
- **Fluxo:** path param + dependencies -> `GetAnalysisReportUseCase.execute(...)` -> resposta `200 AnalysisReportDto`.

---

# 6. O que deve ser modificado?

## Core

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/analysis_report_dto.py`
- **Mudanca:** substituir `precedents: list[PrecedentDto]` por `precedents: list[AnalysisPrecedentDto]`, mantendo `chosen_precedent: AnalysisPrecedentDto | None` no contrato atual.
- **Justificativa:** alinhar o contrato documentado a implementacao atual do endpoint, adicionando `classification_level` por item sem remover o campo agregado ja exposto pela API.

- **Arquivo:** `src/animus/core/intake/domain/structures/dtos/analysis_precedent_dto.py`
- **Mudanca:** adicionar `classification_level: str | None = None`.
- **Justificativa:** permitir transportar o nivel de classificacao no endpoint de relatorio sem quebrar os fluxos atuais que ainda nao preenchem esse campo.

- **Arquivo:** `src/animus/core/intake/domain/structures/analysis_report.py`
- **Mudanca:** ajustar a `Structure` para refletir o novo DTO (`precedents` como `AnalysisPrecedent`), mantendo o campo `chosen_precedent`.
- **Justificativa:** manter coerencia tipada entre `AnalysisReport` e `AnalysisReportDto` conforme o contrato implementado.

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudanca:** exportar `GetAnalysisReportUseCase`.
- **Justificativa:** manter o barrel de casos de uso do contexto `intake` atualizado.

## REST

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudanca:** exportar `GetAnalysisReportController`.
- **Justificativa:** manter o padrao de agregacao publica dos controllers do contexto.

## Routers

- **Arquivo:** `src/animus/routers/intake/intake_router.py`
- **Mudanca:** registrar `GetAnalysisReportController.handle(router)`.
- **Justificativa:** expor o novo endpoint no namespace `/intake` ja consolidado no projeto.

## Database

- **Arquivo:** **Nao aplicavel**.
- **Mudanca:** nenhuma alteracao de model, mapper ou repositorio concreto.
- **Justificativa:** os metodos necessarios ja existem e atendem ao fluxo de agregacao.

---

# 7. O que deve ser removido?

**Nao aplicavel**.

---

# 8. Decisoes Tecnicas e Trade-offs

- **Decisao:** retornar `precedents` como `list[AnalysisPrecedentDto]` no `AnalysisReportDto`, mantendo `chosen_precedent` por compatibilidade do contrato atual.
- **Alternativas consideradas:** remover `chosen_precedent` e depender apenas de `is_chosen` em cada item.
- **Motivo da escolha:** o endpoint atual ainda expoe `chosen_precedent`; manter o campo evita quebra de contrato enquanto adiciona `classification_level` por item.
- **Impactos / trade-offs:** mantem duplicidade temporaria entre `is_chosen` e `chosen_precedent`, em troca de compatibilidade com consumidores existentes.

- **Decisao:** derivar `classification_level` no `GetAnalysisReportUseCase`, sem persistir novo campo em banco.
- **Alternativas consideradas:** persistir classificacao na tabela `analysis_precedents`; calcular no controller.
- **Motivo da escolha:** classificacao e derivada de `applicability_percentage`, nao fonte primaria de dado; manter calculo no `core` preserva controller fino e evita migration.
- **Impactos / trade-offs:** regra fica centralizada e versionavel no dominio, mas qualquer mudanca de faixa exige deploy do backend.

- **Decisao:** ownership check no `UseCase` com `ForbiddenError` para garantir `403`.
- **Alternativas consideradas:** reutilizar somente `IntakePipe.verify_analysis_by_account_from_request(...)`; retornar `404` como em outros endpoints de analise.
- **Motivo da escolha:** ANI-50 exige explicitamente `403` para mismatch de conta, e o contrato esperado do use case ja inclui `account_id`.
- **Impactos / trade-offs:** comportamento de autorizacao deste endpoint difere de endpoints que mascaram ownership com `404`.

- **Decisao:** regra de classificacao proposta:
  - `>= 85.0` -> `APPLICABLE`
  - `>= 70.0 e < 85.0` -> `POSSIBLY_APPLICABLE`
  - `< 70.0` -> `NOT_APPLICABLE`
- **Alternativas consideradas:** seguir estritamente os intervalos textuais do PRD (`85-95`, `70-80`, `<60`) deixando faixas em aberto.
- **Motivo da escolha:** eliminacao de lacunas para garantir classificacao deterministica em 100% dos casos.
- **Impactos / trade-offs:** pode divergir da comunicacao textual original do PRD em faixas limiares; validacao com produto recomendada.

---

# 9. Diagramas e Referencias

- **Fluxo de dados:**

```text
HTTP GET /intake/analyses/{analysis_id}/report
  -> IntakeRouter
  -> GetAnalysisReportController
  -> AuthPipe.get_account_id_from_request
  -> GetAnalysisReportUseCase.execute(analysis_id, account_id)
       -> AnalisysesRepository.find_by_id(analysis_id)
       -> [None] AnalysisNotFoundError (404)
       -> [analysis.account_id != account_id] ForbiddenError (403)
       -> PetitionsRepository.find_by_analysis_id(analysis_id)
       -> PetitionSummariesRepository.find_by_analysis_id(analysis_id)
       -> AnalysisPrecedentsRepository.find_many_by_analysis_id(analysis_id)
       -> classify precedents by applicability_percentage
       -> AnalysisReportDto
  -> 200 JSON
```

- **Fluxo assincrono (se aplicavel):** **Nao aplicavel**.

- **Referencias:**
  - `src/animus/core/intake/use_cases/get_analysis_use_case.py`
  - `src/animus/core/intake/use_cases/list_analysis_precedents_use_case.py`
  - `src/animus/rest/controllers/intake/get_analysis_controller.py`
  - `src/animus/rest/controllers/intake/list_analysis_precedents_controller.py`
  - `src/animus/rest/controllers/intake/get_analysis_petition_controller.py`
  - `src/animus/routers/intake/intake_router.py`
  - `src/animus/pipes/database_pipe.py`
  - `src/animus/rest/handlers/app_error_handler.py`

---

# 10. Pendencias / Duvidas

- **Descricao da pendencia:** o PRD textual de RF-03 descreve faixas com lacunas (`60-69` e `81-84`) para classificacao de aplicabilidade.
- **Impacto na implementacao:** pode haver divergencia de interpretacao entre backend e produto nos limiares da classificacao exibida no PDF.
- **Acao sugerida:** validar com produto se os limiares propostos nesta spec (`>=85`, `>=70`, `<70`) estao corretos para ANI-50/ANI-51.

---

## Restricoes

- **Nao inclua testes automatizados na spec.**
- O `core` nao deve depender de `FastAPI`, `SQLAlchemy`, `Redis`, `Inngest` ou qualquer detalhe de infraestrutura.
- Todos os caminhos citados devem existir no projeto **ou** estar explicitamente marcados como **novo arquivo**.
- **Nao invente** arquivos, metodos, contratos, schemas ou integracoes sem evidencia no PRD/ticket e na codebase.
- Quando faltar informacao suficiente, registrar em **Pendencias / Duvidas** e usar a tool `question` se necessario.
- Toda referencia a codigo existente deve incluir caminho relativo real (`src/animus/...`).
- Se uma secao nao se aplicar, preencher explicitamente com **Nao aplicavel**.
- A spec deve ser consistente com os padroes atuais de nomenclatura e organizacao por camada.
- Schemas `*Body` de entrada devem permanecer no arquivo do controller que os utiliza; neste endpoint nao ha `*Body`.
