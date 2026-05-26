---
title: Relatório de falhas encontradas na suíte de testes
status: concluido
last_updated_at: 2026-05-26
---

# Relatório de Falhas Encontradas

Este documento consolida as falhas encontradas durante a execução da suíte de testes e os arquivos alterados para resolvê-las.

---

## 1. Trigger de sumarização de CASE_ASSESSMENT retornava 404

### Teste com erro

`tests/rest/controllers/intake/test_trigger_case_assessment_case_summarization_controller.py::TestTriggerCaseAssessmentCaseSummarizationController::test_should_return_202_publish_event_and_update_analysis_status`

### Erro observado

```text
assert response.status_code == 202
E   assert 404 == 202
```

### Onde estava o erro

O controller estava registrando a rota:

```text
/intake/analyses/{analysis_id}/case-summaries/case-assessment
```

mas o teste, a arquitetura e o spec esperavam:

```text
/intake/analyses/{analysis_id}/case-assessment-case-summaries
```

Também havia divergência no nome do evento publicado para `CASE_ASSESSMENT`: o código usava `intake/case_assessment.case_summarization.triggered`, enquanto o contrato esperado era `intake/case_assessment.case_summary.triggered`.

### Arquivos alterados

* `src/animus/rest/controllers/intake/trigger_case_assessment_case_summarization_controller.py`
* `src/animus/core/intake/domain/events/case_assessment_case_summary_triggered_event.py`
* `rest-client/intake/analyses.rest`

---

## 2. Trigger de sumarização de primeira instância retornava 405

### Teste com erro

`tests/rest/controllers/intake/test_trigger_case_summary_controller.py::TestTriggerFirstInstanceCaseSummarizationController::test_should_return_202_publish_event_and_update_analysis_status`

### Erro observado

```text
assert response.status_code == 202
E   assert 405 == 202
```

### Onde estava o erro

O teste chamava:

```text
POST /intake/analyses/{analysis_id}/case-summaries
```

mas o controller estava registrando o `POST` em:

```text
/intake/analyses/{analysis_id}/case-summaries/first-instance
```

Como já existia `GET /intake/analyses/{analysis_id}/case-summaries`, o `POST` no path esperado chegava em uma rota existente, mas sem método `POST`, resultando em `405 Method Not Allowed`.

### Arquivos alterados

* `src/animus/rest/controllers/intake/trigger_first_instance_case_summarization_controller.py`
* `rest-client/intake/analyses.rest`

---

## 3. Trigger de sumarização de primeira instância publicava evento divergente

### Teste com erro

`tests/rest/controllers/intake/test_trigger_case_summary_controller.py::TestTriggerFirstInstanceCaseSummarizationController::test_should_return_202_publish_event_and_update_analysis_status`

### Erro observado

```text
assert fake_inngest_client.sent_events[0].name == 'intake/case_summary.triggered'
E   AssertionError: assert 'intake/first.instance.case.summary.triggered' == 'intake/case_summary.triggered'
```

### Onde estava o erro

O evento de primeira instância estava com o nome:

```text
intake/first.instance.case.summary.triggered
```

mas o contrato esperado pelo teste e pela documentação do fluxo geral era:

```text
intake/case_summary.triggered
```

### Arquivos alterados

* `src/animus/core/intake/domain/events/first_instance_summarization_triggered_event.py`
* `tests/pubsub/inngest/jobs/intake/test_summarize_case_job.py`

Observação: o teste de job foi alterado para usar `FistInstanceCaseSummarizationTriggeredEvent.name` em vez de manter o nome antigo hardcoded.

---

## 4. Trigger de extração de petição de segunda instância retornava 404

### Teste com erro

`tests/rest/controllers/intake/test_trigger_petition_extraction_controller.py::TestSecondInstanceCaseSummarizationController::test_should_return_202_publish_event_and_update_analysis_status`

### Erro observado

```text
assert response.status_code == 202
E   assert 404 == 202
```

### Onde estava o erro

O teste chamava:

```text
POST /intake/analyses/{analysis_id}/petition-extraction
```

mas o controller estava registrando a rota em:

```text
/intake/analyses/{analysis_id}/case-summaries/second-instance
```

Também havia divergência no nome do evento: o teste esperava `intake/petition.extraction.triggered`, enquanto o código usava `intake/second.instance.case.summary.triggered`.

Durante essa correção também foi removido um `print(...)` de debug do use case.

### Arquivos alterados

* `src/animus/rest/controllers/intake/trigger_second_instance_case_summarization_controller.py`
* `src/animus/core/intake/domain/events/secod_instance_summarization_triggered_event.py`
* `src/animus/core/intake/use_cases/trigger_second_instance_case_summarization_use_case.py`
* `rest-client/intake/analyses.rest`

---

## 5. Trigger de geração de minuta de julgamento publicava evento divergente

### Teste com erro

`tests/rest/controllers/intake/test_trigger_second_instance_judgment_draft_generation_controller.py::TestTriggerSecondInstanceJudgmentDraftGenerationController::test_should_return_202_when_there_is_at_least_one_chosen_precedent`

### Erro observado

```text
assert fake_inngest_client.sent_events[0].name == 'intake/judgment_draft.generation.triggered'
E   AssertionError: assert 'intake/second.instance.judgment_draft.generation.triggered' == 'intake/judgment_draft.generation.triggered'
```

### Onde estava o erro

O evento de geração de minuta de julgamento de segunda instância estava com o nome:

```text
intake/second.instance.judgment_draft.generation.triggered
```

mas o teste e o spec do fluxo esperavam:

```text
intake/judgment_draft.generation.triggered
```

O job Inngest já consumia `SecondInstanceJudgmentDraftGenerationTriggeredEvent.name`, então alterar a constante manteve o produtor e o consumidor alinhados.

### Arquivos alterados

* `src/animus/core/intake/domain/events/second_instance_judgment_draft_generation_event.py`

---

# Validação Final

A suíte completa foi executada sem parar na primeira falha com:

```powershell
uv run pytest --tb=short -q
```

Resultado final:

```text
335 passed, 1 warning
```
