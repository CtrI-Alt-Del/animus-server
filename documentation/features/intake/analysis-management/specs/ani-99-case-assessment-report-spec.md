---
title: "[server] Endpoint de relatório da análise do advogado"
prd: ../prd.md
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-99
status: open
last_updated_at: 2026-05-15
---

# 1. Objetivo

Evoluir e consolidar o endpoint de relatório da análise para o perfil **Advogado** (`CASE_ASSESSMENT`), garantindo que a resposta agregue todos os dados persistidos necessários para o consumo do mobile e exportação de PDF, incluindo o resumo do caso, a lista de precedentes ordenados e a minuta de petição inicial (`PetitionDraft`).

---

# 2. Escopo

## 2.1 In-scope

- Endpoint `GET /intake/analyses/{analysis_id}/case-assessment-report`.
- Caso de uso `GetCaseAssessmentAnalysisReportUseCase` para agregação de dados.
- Integração com `PetitionDraftsRepository` para inclusão da minuta no relatório.
- Garantia de que todos os campos necessários para o **RF 06** (Exportação) e **RF 07** (Melhorias para Advogado) estejam presentes no DTO.

## 2.2 Out-of-scope

- Geração automática da minuta de petição (responsabilidade do `ANI-93`).
- Geração automática do resumo do caso (responsabilidade do `ANI-77`).
- Fluxos de relatório para Juiz (`SECOND_INSTANCE`) ou Primeira Instância (`FIRST_INSTANCE`).

---

# 3. Requisitos

## 3.1 Funcionais

- **Agregação Completa:** O relatório deve conter a análise, o documento base, o resumo do caso (`CaseSummary`), a lista de precedentes (`AnalysisPrecedent`) e a minuta (`PetitionDraft`).
- **Minuta Obrigatória:** Para o fluxo de Advogado, a existência da minuta é mandatória para a conclusão do relatório. Caso não exista, deve retornar erro específico.
- **Justificativa de Aderência:** Cada precedente no relatório deve conter o campo `synthesis` preenchido.
- **Snapshot de Filtros:** O relatório deve refletir os filtros aplicados na busca que gerou os precedentes.

## 3.2 Não funcionais

- **Idempotência:** O endpoint é de leitura (`GET`) e não deve alterar o estado do banco ou disparar novas gerações de IA.
- **Segurança:** Apenas o proprietário da análise pode acessar o relatório.
- **Performance:** A agregação deve ser feita via consultas eficientes nos repositórios SQL.

---

# 4. O que já existe?

## Camada Core (Structures / DTOs)

- **`CaseAssessmentAnalysisReport`** (`src/animus/core/intake/domain/structures/case_assessment_analysis_report.py`) — Agregado de domínio para o relatório do advogado.
- **`CaseAssessmentAnalysisReportDto`** (`src/animus/core/intake/domain/structures/dtos/case_assessment_analysis_report_dto.py`) — Contrato de saída para o endpoint.
- **`PetitionDraft`** (`src/animus/core/intake/domain/structures/petition_draft.py`) — Estrutura da minuta.

## Camada Core (Interfaces)

- **`PetitionDraftsRepository`** (`src/animus/core/intake/interfaces/petition_drafts_repository.py`) — Port para acesso à minuta.
- **`AnalisysesRepository`** (`src/animus/core/intake/interfaces/analisyses_repository.py`) — Port para acesso à análise.

## Camada Database

- **`SqlalchemyPetitionDraftsRepository`** (`src/animus/database/sqlalchemy/repositories/intake/sqlalchemy_petition_drafts_repository.py`) — Implementação concreta.

---

# 5. O que deve ser criado?

## Camada Core (Erros de Domínio)

- **Localização:** `src/animus/core/intake/domain/errors/`
- **`PetitionDraftUnavailableError`** — Levantado quando a minuta obrigatória não for encontrada para a análise. (**Já existe no código, mas deve ser formalizado na spec**).

---

# 6. O que deve ser modificado?

## Camada Core (Use Cases)

- **Arquivo:** `src/animus/core/intake/use_cases/get_case_assessment_analysis_report_use_case.py`
- **Mudança:** Garantir a injeção do `PetitionDraftsRepository` e a lógica de busca e agregação da minuta.
- **Fluxo:**
    1. Busca `Analysis` por ID.
    2. Valida ownership (`account_id`).
    3. Busca `AnalysisDocument`.
    4. Busca `CaseSummary`.
    5. Busca `PetitionDraft`. Se `None`, lança `PetitionDraftUnavailableError`.
    6. Busca lista de `AnalysisPrecedent`.
    7. Retorna `CaseAssessmentAnalysisReport.dto`.

## Camada REST (Controllers)

- **Arquivo:** `src/animus/rest/controllers/intake/get_case_assessment_analysis_report_controller.py`
- **Mudança:** Garantir que o endpoint esteja registrado no path correto e injete todas as dependências necessárias via `DatabasePipe`.
- **Path:** `GET /analyses/{analysis_id}/case-assessment-report` (dentro do prefixo `/intake`).

---

# 7. O que deve ser removido?

**Não aplicável.**

---

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** Uso de `CaseAssessment` em vez de `Lawyer`.
- **Motivo da escolha:** Padronização do domínio `intake` iniciada no `ANI-70`, onde os nomes das análises seguem o contexto processual (`CaseAssessment`, `FirstInstance`, `SecondInstance`) em vez do perfil do usuário, permitindo maior flexibilidade futura.
- **Impacto:** O ticket Jira ANI-99 refere-se a "Lawyer Report", mas a implementação usa `CaseAssessmentReport`.

- **Decisão:** Minuta (`PetitionDraft`) obrigatória.
- **Motivo da escolha:** O fluxo de Advogado (RF 07) culmina na entrega da estrutura da petição. Sem ela, o relatório de análise inicial para advogado é considerado incompleto.

---

# 9. Diagramas e Referências

### Fluxo de Dados

```text
HTTP GET /intake/analyses/{id}/case-assessment-report
  -> GetCaseAssessmentAnalysisReportController
    -> GetCaseAssessmentAnalysisReportUseCase
      -> AnalisysesRepository.find_by_id()
      -> AnalysisDocumentsRepository.find_by_analysis_id()
      -> CaseSummariesRepository.find_by_analysis_id()
      -> PetitionDraftsRepository.find_by_analysis_id()
      -> AnalysisPrecedentsRepository.find_many_by_analysis_id()
    <- CaseAssessmentAnalysisReportDto
<- HTTP 200 JSON
```

### Referências
- `src/animus/core/intake/use_cases/get_second_instance_analysis_report_use_case.py` (Referência para fluxo do Juiz).

---

# 10. Pendências / Dúvidas

**Sem pendências.**
