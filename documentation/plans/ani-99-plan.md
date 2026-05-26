# Plano de Implementação: ANI-99 ([server] Endpoint de relatório da análise do advogado)

## Mapa de Dependências

| Fase | Objetivo | Depende de | Pode rodar em paralelo com |
| --- | --- | --- | --- |
| F1 | Setup Local | - | - |
| F2 | Camada Core | F1 | - |
| F3 | Camada REST | F2 | - |
| F4 | Revisão e Fechamento | F3 | - |

---

## Detalhamento das Tarefas

### Fase 1: Setup Local
**Objetivo:** Garantir que o ambiente local e o banco de dados estejam atualizados antes de iniciar o desenvolvimento.

- [ ] **Tarefa 1.1:** Executar a validação operacional e aplicar as migrações mais recentes no ambiente local executando o comando `uv run alembic upgrade head`.

### Fase 2: Camada Core
**Objetivo:** Adaptar e garantir o funcionamento do Use Case e das validações de regras de negócios no nível de domínio. Segundo a spec, as `Structures`, `DTOs` e as interfaces já existem, mas precisam ser garantidas no caso de uso.

- [ ] **Tarefa 2.1:** Analisar o arquivo `src/animus/core/intake/use_cases/get_case_assessment_analysis_report_use_case.py` (conforme especificado) para confirmar se ele já implementa adequadamente a injeção de `PetitionDraftsRepository` e a busca da minuta obrigatória.
- [ ] **Tarefa 2.2:** Se a implementação no `GetCaseAssessmentAnalysisReportUseCase` não corresponder exatamente ao fluxo da spec (incluindo o lançamento do `PetitionDraftUnavailableError` quando a minuta não for encontrada), ajustá-la e corrigir eventuais falhas tipadas apontadas pelo Ruff/Mypy.

### Fase 3: Camada REST e Integração
**Objetivo:** Ajustar o controller para expor corretamente a rota mapeada e injetar todas as dependências.

- [ ] **Tarefa 3.1:** Analisar o `src/animus/rest/controllers/intake/get_case_assessment_analysis_report_controller.py`.
- [ ] **Tarefa 3.2:** Confirmar se o decorator `@router.get` está mapeado exatamente para `/analyses/{analysis_id}/case-assessment-report` e se todas as injeções via `DatabasePipe` (incluindo o repositório `petition_drafts_repository`) estão corretas.
- [ ] **Tarefa 3.3:** Verificar se a estrutura de roteamento e a injeção em `src/animus/pipes/database_pipe.py` e `src/animus/routers/intake/analyses_router.py` estão alinhadas com a spec e funcionando, ajustando se necessário.

### Fase 4: Revisão e Fechamento
**Objetivo:** Realizar a verificação estática final do projeto para garantir que as alterações não introduziram regressões.

- [ ] **Tarefa 4.1:** Rodar verificações do projeto (linting, checagem de tipos com mypy/ruff) para atestar a integridade do que foi validado.
