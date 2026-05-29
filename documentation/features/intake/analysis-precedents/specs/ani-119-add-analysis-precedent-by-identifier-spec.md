---
title: Endpoint para adicionar precedente manualmente a uma análise por identificador
prd: https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/17596417
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-119
status: open
last_updated_at: 2026-05-28
---

# 1. Objetivo

Implementar o fluxo manual para adicionar um precedente (da base Pangea) a uma análise existente utilizando seu identificador (`court`, `kind`, `number`), garantindo que o precedente seja inserido como escolhido (`is_chosen=True`) e com nível de aplicabilidade máximo (`APPLICABLE`). O endpoint será responsável por orquestrar a verificação do precedente, garantir a idempotência da relação e retornar o novo status da análise de forma síncrona.

---

# 2. Escopo

## 2.1 In-scope

- Criação do endpoint `POST /intake/analyses/{analysis_id}/precedents`.
- Implementação do caso de uso `AddAnalysisPrecedentByIdentifierUseCase` para orquestrar a verificação, inserção e idempotência.
- Configuração do nível de aplicabilidade `APPLICABLE` (via `applicability_level=2` no DTO) e estado `is_chosen=True` por padrão para inclusões manuais.
- Retorno de `AnalysisStatusDto` para o frontend.
- Refatoração/Remoção do antigo `CreateAnalysisPrecedentController` e `CreateAnalysisPrecedentUseCase` que não seguiam o contrato definido.

## 2.2 Out-of-scope

- Busca assíncrona ou vetorização de precedentes.
- Criação de precedentes que não existam na base Pangea.
- Modificação do fluxo de `choose/unchoose` já existente, apenas o seu reaproveitamento em caso de relações preexistentes.

---

# 3. Requisitos

## 3.1 Funcionais

- O endpoint deve receber `court`, `kind` e `number` no corpo da requisição e `analysis_id` na URL.
- O sistema deve validar se o precedente existe na base; caso não exista, retornar erro (`PrecedentNotFoundError`).
- O sistema deve verificar se a relação já existe:
  - Se existir: atualizar a relação para `is_chosen=True` (garantindo idempotência) e retornar o status da análise.
  - Se não existir: criar a relação com `is_chosen=True` e `applicability_level` equivalente a `APPLICABLE`.
- O endpoint deve retornar o status atualizado/atual da análise através de `AnalysisStatusDto`.

## 3.2 Não funcionais

- **Segurança:** A rota deve estar protegida por validação de token JWT e ownership da `Analysis` via `IntakePipe`.
- **Idempotência:** Múltiplas requisições com os mesmos parâmetros devem resultar no precedente como "escolhido", sem duplicar a relação ou falhar.

---

# 4. O que já existe?

## Camada Core

- **`AnalysisPrecedent`** (`src/animus/core/intake/domain/structures/analysis_precedent.py`) — Entidade que representa a relação; suporta criação via `AnalysisPrecedent.create(...)`.
- **`PrecedentIdentifier`** (`src/animus/core/intake/domain/structures/precedent_identifier.py`) — Value object do identificador composto do precedente.
- **`AnalysisPrecedentsRepository`** (`src/animus/core/intake/interfaces/analysis_precedents_repository.py`) — Port que define operações de banco para a relação, incluindo `find_by_analysis_id_and_precedent_id`, `choose_by_analysis_id_and_precedent_id` e `add_many_by_analysis_id`.
- **`PrecedentsRepository`** (`src/animus/core/intake/interfaces/precedents_repository.py`) — Port que inclui a busca `find_by_identifier`.
- **`PrecedentNotFoundError`** (`src/animus/core/intake/domain/errors/precedent_not_found_error.py`) — Erro de domínio já existente.

## Camada Database

- **`SqlalchemyAnalysisPrecedentsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analysis_precedents_repository.py`) — Implementação concreta contendo `add_many_by_analysis_id` e `choose_by_analysis_id_and_precedent_id`.

## Camada REST

- **`ChooseAnalysisPrecedentController`** (`src/animus/rest/controllers/intake/choose_analysis_precedent_controller.py`) — Controller que serve de base arquitetural para ownership e injeção de dependências.

---

# 5. O que deve ser criado?

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/add_analysis_precedent_by_identifier_use_case.py` (**novo arquivo**)
- **Dependências (ports injetados):** `AnalysisPrecedentsRepository`, `AnalisysesRepository`, `PrecedentsRepository`.
- **Método principal:** `execute(self, analysis_id: str, precedent_identifier_dto: PrecedentIdentifierDto) -> AnalysisStatusDto`
- **Fluxo resumido:**
  1. Validar existência da análise (se necessário para obter status final).
  2. Buscar precedente via `PrecedentsRepository.find_by_identifier`; levantar `PrecedentNotFoundError` se não existir.
  3. Verificar se a relação já existe via `AnalysisPrecedentsRepository.find_by_analysis_id_and_precedent_id`.
  4. Se existir: chamar `AnalysisPrecedentsRepository.choose_by_analysis_id_and_precedent_id`.
  5. Se não existir: criar DTO com `is_chosen=True` e `applicability_level=2` (APPLICABLE), instanciar via `AnalysisPrecedent.create` e persistir usando `AnalysisPrecedentsRepository.add_many_by_analysis_id` (com lista unitária).
  6. Buscar/retornar o status atualizado da análise como `AnalysisStatusDto`.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/add_analysis_precedent_by_identifier_controller.py` (**novo arquivo**)
- **`*Body`:** `AddAnalysisPrecedentByIdentifierBody` (Pydantic BaseModel contendo `court`, `kind`, `number` e método `to_dto() -> PrecedentIdentifierDto`).
- **Método HTTP e path:** `POST /analyses/{analysis_id}/precedents`
- **`status_code`:** 200 (pois suporta idempotência e alteração de estado se já existir).
- **`response_model`:** `AnalysisStatusDto`
- **Dependências injetadas via `Depends`:** `AuthPipe`, `DatabasePipe` (para repositories).
- **Fluxo:** `body.to_dto()` → `IntakePipe.verify_analysis_by_account_from_request` → `AddAnalysisPrecedentByIdentifierUseCase.execute()` → retorna a resposta.

---

# 6. O que deve ser modificado?

## Camada Core

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** Exportar `AddAnalysisPrecedentByIdentifierUseCase` no lugar de `CreateAnalysisPrecedentUseCase`.
- **Justificativa:** Reflete o novo nome e responsabilidade da funcionalidade manual.

## Camada Core (Erros)

- **Arquivo:** `src/animus/core/intake/domain/errors/__init__.py`
- **Mudança:** Adicionar a exportação de `PrecedentNotFoundError`.
- **Justificativa:** Consistência na exportação de erros de domínio da camada `intake`.

## Camada Routers

- **Arquivo:** `src/animus/routers/intake/analyses_router.py`
- **Mudança:** Registrar `AddAnalysisPrecedentByIdentifierController.handle(router)` em substituição ao antigo controller `CreateAnalysisPrecedentController`.
- **Justificativa:** Rotação do novo endpoint com o novo caminho e remoção do antigo.

---

# 7. O que deve ser removido?

## Camada Core

- **Arquivo:** `src/animus/core/intake/use_cases/create_analysis_precedent_use_case.py`
- **Motivo da remoção:** O novo use case `AddAnalysisPrecedentByIdentifierUseCase` cobre exatamente este escopo, com nomenclatura mais clara e comportamento ajustado ao RF 03.
- **Impacto esperado:** Atualizar imports nos testes associados e removê-los se substituídos completamente pelos novos testes.

## Camada REST

- **Arquivo:** `src/animus/rest/controllers/intake/create_analysis_precedent_controller.py`
- **Motivo da remoção:** Substituído pelo `AddAnalysisPrecedentByIdentifierController` que mapeia para o path correto `/analyses/{analysis_id}/precedents`.
- **Impacto esperado:** Renomear/refatorar os testes em `tests/rest/controllers/intake/test_create_analysis_precedent_controller.py`.

---

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** Reutilizar `add_many_by_analysis_id` com uma lista unitária em vez de criar um novo método `add` no repositório `AnalysisPrecedentsRepository`.
  - **Alternativas consideradas:** Adicionar método `add` para inserções unitárias.
  - **Motivo da escolha:** Evita poluir a interface do repositório, pois o caso de inserção de múltiplos precedentes (durante o processamento assíncrono) é o uso primário, e uma lista com um item funciona perfeitamente para inclusão avulsa.
  - **Impactos / trade-offs:** Nenhum impacto na performance, ganho de simplicidade na interface.
- **Decisão:** Forçar `applicability_level=2` (`APPLICABLE`) via DTO na inserção.
  - **Alternativas consideradas:** Enviar `similarity_score=100.0`.
  - **Motivo da escolha:** Evita acoplamento implícito com a regra de mapeamento de score para enumeração, inserindo diretamente o estado de negócio desejado conforme esperado para seleção manual.

---

# 9. Diagramas e Referências

**Fluxo de dados:**

```
POST /intake/analyses/{analysis_id}/precedents
  body: { court, kind, number }
→ AddAnalysisPrecedentByIdentifierController
    → AuthPipe.get_account_id_from_request(...)
    → IntakePipe.verify_analysis_by_account_from_request(analysis_id, account_id)
        → [404 se análise não existir ou não pertencer à conta]
→ AddAnalysisPrecedentByIdentifierUseCase.execute(analysis_id, precedent_identifier_dto)
    → PrecedentsRepository.find_by_identifier(identifier)
        → [PrecedentNotFoundError → 404 se não existir na base]
    → AnalysisPrecedentsRepository.find_by_analysis_id_and_precedent_id(analysis_id, precedent.id)
        → [relação já existe] → choose_by_analysis_id_and_precedent_id(...) 
        → [relação não existe] → AnalysisPrecedent.create(dto_com_applicability_2_e_chosen_true)
                               → AnalysisPrecedentsRepository.add_many_by_analysis_id([precedent])
    → AnalisysesRepository.find_by_id(analysis_id)
    → retorna AnalysisStatusDto(value=analysis.status.dto)
→ 200 AnalysisStatusDto
```

**Referências:**
- `src/animus/rest/controllers/intake/choose_analysis_precedent_controller.py` para injeção de dependência de `IntakePipe`.
- `tests/rest/controllers/intake/test_choose_analysis_precedent_controller.py` para a construção de testes semelhantes de identificador composto.

---

# 10. Pendências / Dúvidas

**Sem pendências**.
