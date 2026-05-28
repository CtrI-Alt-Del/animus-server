# Plano de Implementação: ANI-119 - Adicionar precedente manualmente a uma análise por identificador

## Mapa de Dependências

| Fase | Objetivo | Depende de | Pode rodar em paralelo com |
| --- | --- | --- | --- |
| F1 | Limpeza e Validação de Banco | - | - |
| F2 | Implementação do Core | F1 | - |
| F3 | Implementação da Camada API | F2 | - |

---

## Fases e Tarefas

### Fase 1: Limpeza e Validação de Banco
Nesta fase, removemos os artefatos antigos que não seguem mais o contrato e garantimos que o banco de dados local esteja atualizado (conforme exigido pela diretriz de execução).

- **Tarefa 1.1:** Remover o caso de uso antigo `src/animus/core/intake/use_cases/create_analysis_precedent_use_case.py`.
- **Tarefa 1.2:** Remover o controller antigo `src/animus/rest/controllers/intake/create_analysis_precedent_controller.py`.
- **Tarefa 1.3:** Executar validação operacional no ambiente local rodando o comando: `uv run alembic upgrade head`.

### Fase 2: Implementação do Core
Nesta fase, criamos e expomos a lógica de negócios para adicionar um precedente manualmente, garantindo idempotência.

- **Tarefa 2.1:** Modificar o arquivo `src/animus/core/intake/domain/errors/__init__.py` para incluir a exportação de `PrecedentNotFoundError`.
- **Tarefa 2.2:** Criar o arquivo `src/animus/core/intake/use_cases/add_analysis_precedent_by_identifier_use_case.py` implementando o `AddAnalysisPrecedentByIdentifierUseCase`.
  - Injetar dependências: `AnalysisPrecedentsRepository`, `AnalisysesRepository`, `PrecedentsRepository`.
  - Implementar o método `execute` seguindo o fluxo especificado (validação, busca, criação ou atualização via `choose_by_analysis_id_and_precedent_id`).
- **Tarefa 2.3:** Modificar `src/animus/core/intake/use_cases/__init__.py` para exportar o novo `AddAnalysisPrecedentByIdentifierUseCase` e remover a referência do use case excluído.

### Fase 3: Implementação da Camada API
Nesta fase, implementamos os contratos de entrada e saída HTTP conectando-os ao Core Layer recém-desenvolvido.

- **Tarefa 3.1:** Criar o arquivo `src/animus/rest/controllers/intake/add_analysis_precedent_by_identifier_controller.py`.
  - Implementar Pydantic model `AddAnalysisPrecedentByIdentifierBody` contendo `court`, `kind`, `number` e seu respectivo mapeamento para DTO.
  - Implementar o `AddAnalysisPrecedentByIdentifierController` retornando status 200 e chamando o pipeline de ownership (`IntakePipe.verify_analysis_by_account_from_request`).
- **Tarefa 3.2:** Modificar `src/animus/routers/intake/analyses_router.py`.
  - Remover a referência e o registro para o antigo controller (`CreateAnalysisPrecedentController`).
  - Registrar a nova rota `POST /analyses/{analysis_id}/precedents` apontando para o `AddAnalysisPrecedentByIdentifierController.handle`.