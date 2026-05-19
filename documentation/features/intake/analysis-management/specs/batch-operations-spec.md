---
title: ANI-66 - Operações em lote para movimentação e arquivamento de análises
prd: documentation/features/intake/analysis-management/prd.md
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-66
status: open
last_updated_at: 2026-04-29
---

# 1. Objetivo

Implementar suporte a operações em lote no `animus-server` para permitir que o usuário mova múltiplas análises para uma pasta (ou remova de uma pasta) e arquive múltiplas análises em uma única requisição. A implementação deve garantir atomicidade (falha total se um item for inválido ou de outro dono), validação rigorosa de ownership e consistência com os padrões de persistência e contratos de domínio existentes.

---

# 2. Escopo

## 2.1 In-scope

- Criar `MoveAnalysesToFolderUseCase` para movimentação em lote.
- Evoluir `ArchiveAnalysisUseCase` para `ArchiveAnalysesUseCase`, suportando processamento em lote.
- Criar `MoveAnalysesToFolderController` com rota `PATCH /intake/analyses/folder`.
- Evoluir `ArchiveAnalysisController` para `ArchiveAnalysesController` com rota `PATCH /intake/analyses/archive`.
- Adicionar método `move_to_folder` na entidade `Analysis`.
- Garantir que a movimentação para `folder_id = null` seja tratada como "Sem pasta".
- Validar ownership de todas as análises do lote e da pasta de destino.

## 2.2 Out-of-scope

- Criação, renomeação ou exclusão de pastas (já existem no módulo `library`).
- Alteração no schema de banco de dados (colunas `folder_id` e `is_archived` já existem).
- Operações de exclusão definitiva (destrutiva) de análises.
- Interface de usuário (mobile).

---

# 3. Requisitos

## 3.1 Funcionais

- O usuário deve conseguir mover uma lista de `analysis_ids` para uma `folder_id` (UUID ou `null`).
- O usuário deve conseguir arquivar uma lista de `analysis_ids`.
- **Atomicidade:** Se qualquer `analysis_id` não existir ou pertencer a outra conta, a operação inteira deve falhar com `AnalysisNotFoundError`.
- **Validação de Pasta:** Se `folder_id` for fornecido, ele deve existir e pertencer à conta autenticada; caso contrário, lançar `FolderNotFoundError`.
- **Ownership:** Apenas análises e pastas do `account_id` autenticado podem ser manipuladas.
- **Idempotência:** Mover uma análise para a pasta onde ela já está ou arquivar uma análise já arquivada deve ser considerado sucesso.

## 3.2 Não funcionais

- **Segurança:** Autenticação obrigatória e validação de ownership em todos os itens do lote.
- **Consistência Transacional:** O commit deve ocorrer apenas ao final do request bem-sucedido (garantido pelo middleware de `Session`).
- **Performance:** Carregamento individual por ID é aceitável para lotes pequenos (padrão mobile); para ganhos de performance, utilizar os métodos de repositório existentes.
- **Compatibilidade:** Manter o `AnalysisDto` como formato de resposta.

---

# 4. O que já existe?

## Core

- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) — entidade que possui `folder_id` e `is_archived`.
- **`Folder`** (`src/animus/core/library/domain/entities/folder.py`) — entidade de pasta.
- **`AnalisysesRepository`** (`src/animus/core/intake/interfaces/analisyses_repository.py`) — possui `find_by_id` e `replace`.
- **`FoldersRepository`** (`src/animus/core/library/interfaces/folders_repository.py`) — possui `find_by_id`.
- **`ArchiveAnalysisUseCase`** (`src/animus/core/intake/use_cases/archive_analysis_use_case.py`) — será evoluído para lote.
- **`AnalysisNotFoundError`** (`src/animus/core/intake/domain/errors/analysis_not_found_error.py`) — erro lançado em falha de ownership ou existência.
- **`FolderNotFoundError`** (`src/animus/core/library/domain/errors/folder_not_found_error.py`) — erro para pasta inválida.

## Database

- **`AnalysisModel`** (`src/animus/database/sqlalchemy/models/intake/analysis_model.py`) — mapeia `folder_id` e `is_archived`.
- **`SqlalchemyAnalisysesRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_analisyses_repository.py`) — implementação de persistência.

## REST

- **`ArchiveAnalysisController`** (`src/animus/rest/controllers/intake/archive_analysis_controller.py`) — será substituído pelo novo controller de lote.

---

# 5. O que deve ser criado?

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/intake/use_cases/move_analyses_to_folder_use_case.py` (**novo arquivo**)
- **Dependências:** `AnalisysesRepository`, `FoldersRepository`
- **Método principal:** `execute(account_id: str, analysis_ids: list[str], folder_id: str | None) -> list[AnalysisDto]`
- **Fluxo resumido:**
  1. Normalizar `account_id` e `folder_id`.
  2. Se `folder_id` não for `None`, validar existência e ownership da pasta via `FoldersRepository`. Lançar `FolderNotFoundError` em falha.
  3. Para cada `analysis_id` em `analysis_ids`:
     - Buscar análise.
     - Validar ownership. Lançar `AnalysisNotFoundError` em falha.
     - Acumular em lista temporária.
  4. Para cada análise validada:
     - Chamar `analysis.move_to_folder(normalized_folder_id)`.
     - Chamar `repository.replace(analysis)`.
  5. Retornar lista de DTOs das análises atualizadas.

- **Localização:** `src/animus/core/intake/use_cases/archive_analyses_use_case.py` (**novo arquivo** ou renomear anterior)
- **Dependências:** `AnalisysesRepository`
- **Método principal:** `execute(account_id: str, analysis_ids: list[str]) -> list[AnalysisDto]`
- **Fluxo resumido:**
  1. Para cada `analysis_id`: buscar e validar ownership. Lançar `AnalysisNotFoundError` em falha.
  2. Para cada análise válida: chamar `analysis.archive()` e `repository.replace(analysis)`.
  3. Retornar lista de DTOs.

## Camada REST (Controllers)

- **Localização:** `src/animus/rest/controllers/intake/move_analyses_to_folder_controller.py` (**novo arquivo**)
- **`_Body`**: 
  - `analysis_ids: list[str]`
  - `folder_id: str | None`
- **Método HTTP e path:** `PATCH /intake/analyses/folder`
- **`status_code`**: `200`
- **`response_model`**: `list[AnalysisDto]`
- **Dependências:** `AuthPipe`, `DatabasePipe` (Analisyses e Folders)
- **Fluxo:** `Body` -> `UseCase.execute(...)` -> Resposta.

- **Localização:** `src/animus/rest/controllers/intake/archive_analyses_controller.py` (**novo arquivo**, substituindo `archive_analysis_controller.py`)
- **`_Body`**:
  - `analysis_ids: list[str]`
- **Método HTTP e path:** `PATCH /intake/analyses/archive`
- **`status_code`**: `200`
- **`response_model`**: `list[AnalysisDto]`
- **Fluxo:** `Body` -> `UseCase.execute(...)` -> Resposta.

---

# 6. O que deve ser modificado?

## Camada Core (Entidades)

- **Arquivo:** `src/animus/core/intake/domain/entities/analysis.py`
- **Mudança:** Adicionar método `move_to_folder(self, folder_id: Id | None) -> None`.
- **Justificativa:** Encapsular a alteração de estado da pasta na entidade de domínio.

## Camada Core (Use Cases)

- **Arquivo:** `src/animus/core/intake/use_cases/__init__.py`
- **Mudança:** Exportar os novos Use Cases e remover referências ao Use Case de arquivamento único, se deletado.

## Camada REST (Controllers)

- **Arquivo:** `src/animus/rest/controllers/intake/__init__.py`
- **Mudança:** Exportar novos controllers e remover o antigo.

## Camada Routers

- **Arquivo:** `src/animus/routers/intake/intake_router.py`
- **Mudança:** Registrar os novos controllers e remover o registro do `ArchiveAnalysisController`.

---

# 7. O que deve ser removido?

## Camada Core (Use Cases)

- **Arquivo:** `src/animus/core/intake/use_cases/archive_analysis_use_case.py`
- **Motivo da remoção:** Substituído pela versão em lote `ArchiveAnalysesUseCase`.
- **Impacto esperado:** Necessário atualizar o router.

## Camada REST (Controllers)

- **Arquivo:** `src/animus/rest/controllers/intake/archive_analysis_controller.py`
- **Motivo da remoção:** Substituído por `ArchiveAnalysesController`.

---

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** Manter loops de `find_by_id` e `replace` individuais nos Use Cases.
  - **Alternativas:** Criar `find_many_by_ids` e `replace_many` no repositório.
  - **Motivo da escolha:** O volume de análises em um lote mobile (seleção manual) é tipicamente baixo (< 50). Os métodos existentes já garantem a atomicidade via transação da `Session` e simplificam a implementação inicial sem poluir a interface do repositório desnecessariamente.
  - **Impactos:** N+1 queries de busca e N updates, o que é aceitável para este volume e contexto.

- **Decisão:** Lote Atômico Estrito.
  - **Alternativas:** Processamento parcial com lista de sucessos/erros.
  - **Motivo da escolha:** Requisito explícito do PRD/Jira para simplificar o estado na UI mobile em caso de erro.
  - **Impactos:** Se um ID estiver errado, nada é processado.

- **Decisão:** Reuso de `AnalysisNotFoundError` para falhas de ownership.
  - **Alternativas:** Criar `AnalysisForbiddenError`.
  - **Motivo da escolha:** Padrão já estabelecido no projeto (ex.: `RenameAnalysisUseCase`) para não vazar a existência de recursos de outros usuários.

---

# 9. Diagramas e Referências

- **Fluxo de dados (Movimentação):**

```text
PATCH /intake/analyses/folder { analysis_ids, folder_id }
  -> MoveAnalysesToFolderController
  -> MoveAnalysesToFolderUseCase.execute
     -> FoldersRepository.find_by_id (se folder_id != None)
     -> loop analysis_ids:
        -> AnalisysesRepository.find_by_id
        -> validation (ownership)
     -> loop validated_analyses:
        -> analysis.move_to_folder
        -> AnalisysesRepository.replace
  -> 200 list[AnalysisDto]
```

- **Referências:**
  - `src/animus/core/intake/use_cases/rename_analysis_use_case.py` (validação de ownership)
  - `src/animus/core/intake/domain/entities/analysis.py` (propriedades da entidade)

---

# 10. Pendências / Dúvidas

**Sem pendências**.

---

## Restrições

- **Não inclua testes automatizados na spec.**
- O `core` não deve depender de infraestrutura.
- Todos os caminhos citados devem existir ou estar marcados como **novo arquivo**.
- A spec deve ser consistente com os padrões da codebase.
