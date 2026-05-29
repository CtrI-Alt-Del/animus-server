# Plano de Implementação: ANI-120 - Notificações push de conclusão de minutas com analysis_type

Este documento detalha o plano de execução para implementar notificações push de conclusão de minuta de petição inicial e minuta de sentença de 2ª instância, além de propagar `analysis_type` nas notificações de análise já contempladas pela spec.

## 1. Mapa de Dependências

| Fase | Objetivo | Depende de | Pode rodar em paralelo com |
| --- | --- | --- | --- |
| **F1 (Core)** | Evoluir eventos, port de push e use cases de notificação para trafegar `analysis_type` e cobrir os novos tipos de minuta. | - | - |
| **F2 (Drivers/Infra - Provider)** | Atualizar o adaptador OneSignal para implementar os contratos novos/alterados do `PushNotificationProvider`. | F1 | F3 |
| **F3 (Drivers/Infra - PubSub)** | Ajustar publishers, criar/corrigir jobs Inngest de notificação e registrar os jobs faltantes. | F1 | F2 |
| **F4 (API Layer / Fronteira HTTP)** | Confirmar ausência de mudanças em endpoints, schemas, pipes, controllers e routers. | F1 | F2, F3 |
| **F5 (Validação Operacional)** | Executar validações locais obrigatórias, incluindo migrações, sem adicionar testes automatizados ao plano. | F2, F3, F4 | - |

---

## 2. Detalhamento das Tarefas

### F1: Core (Eventos, Interfaces e Use Cases)

**Objetivo:** preparar contratos internos para que todo fluxo de notificação receba `analysis_type` a partir de `Analysis.type.dto`, mantendo o `core` sem dependência de OneSignal, Inngest, HTTP ou variáveis de ambiente.

- [ ] **T1.1: Criar evento de conclusão de minuta de sentença**
  - **Arquivo:** `src/animus/core/intake/domain/events/second_instance_judgment_draft_generation_finished_event.py`
  - **Ação:** Criar `SecondInstanceJudgmentDraftGenerationFinishedEvent` com `name = 'intake/judgment_draft.generation.finished'` e payload imutável contendo `analysis_id`, `account_id` e `analysis_type`.
  - **Resultado:** O domínio passa a ter um evento explícito para conclusão da geração da minuta de sentença.

- [ ] **T1.2: Exportar o novo evento de domínio**
  - **Arquivo:** `src/animus/core/intake/domain/events/__init__.py`
  - **Ação:** Adicionar `SecondInstanceJudgmentDraftGenerationFinishedEvent` aos exports públicos.
  - **Dependência:** T1.1
  - **Resultado:** Camadas externas conseguem importar o evento pelo módulo de eventos do domínio.

- [ ] **T1.3: Atualizar eventos existentes para carregar `analysis_type`**
  - **Arquivos:**
    - `src/animus/core/intake/domain/events/petition_draft_generation_finished_event.py`
    - `src/animus/core/intake/domain/events/precedents_search_finished_event.py`
    - `src/animus/core/intake/domain/events/petition_summary_finished_event.py`
    - `src/animus/core/intake/domain/events/case_summary_finished_event.py`
  - **Ação:** Adicionar `analysis_type: str` ao `_Payload` e ao construtor de cada evento.
  - **Resultado:** Todos os eventos consumidos por jobs de notificação podem carregar o tipo de análise sem consulta adicional ao banco.

- [ ] **T1.4: Evoluir o port `PushNotificationProvider`**
  - **Arquivo:** `src/animus/core/notification/interfaces/push_notification_provider.py`
  - **Ação:** Atualizar os métodos existentes para receber `analysis_type` e adicionar os métodos `send_petition_summary_finished_message(...)`, `send_petition_draft_finished_message(...)` e `send_second_instance_judgment_draft_finished_message(...)` conforme a spec.
  - **Dependência:** T1.3
  - **Resultado:** O contrato de push do `core` cobre todos os tipos de notificação exigidos pela ANI-120.

- [ ] **T1.5: Atualizar use cases de notificação existentes**
  - **Arquivos:**
    - `src/animus/core/notification/use_cases/send_case_summary_finished_notification_use_case.py`
    - `src/animus/core/notification/use_cases/send_petition_summary_finished_notification_use_case.py`
    - `src/animus/core/notification/use_cases/send_precedents_search_finished_notification_use_case.py`
  - **Ação:** Alterar `execute(...)` para receber `analysis_type` e repassar o valor ao método correto do provider; no resumo de petição, trocar a chamada para `send_petition_summary_finished_message(...)`.
  - **Dependência:** T1.4
  - **Resultado:** Notificações existentes preservam `type` e `analysis_id`, adicionando `analysis_type` e corrigindo o wiring de resumo de petição.

- [ ] **T1.6: Criar use case de notificação de minuta de petição**
  - **Arquivo:** `src/animus/core/notification/use_cases/send_petition_draft_finished_notification_use_case.py`
  - **Ação:** Criar `SendPetitionDraftFinishedNotificationUseCase.execute(account_id: Id, analysis_id: Id, analysis_type: str) -> None`, delegando para `send_petition_draft_finished_message(...)`.
  - **Dependência:** T1.4
  - **Resultado:** O `core` passa a expor o caso de uso específico para push de conclusão de minuta de petição.

- [ ] **T1.7: Criar use case de notificação de minuta de sentença**
  - **Arquivo:** `src/animus/core/notification/use_cases/send_judgment_draft_finished_notification_use_case.py`
  - **Ação:** Criar `SendJudgmentDraftFinishedNotificationUseCase.execute(account_id: Id, analysis_id: Id, analysis_type: str) -> None`, delegando para `send_second_instance_judgment_draft_finished_message(...)`.
  - **Dependência:** T1.4
  - **Resultado:** O `core` passa a expor o caso de uso específico para push de conclusão de minuta de sentença.

- [ ] **T1.8: Exportar os novos use cases de notificação**
  - **Arquivos:**
    - `src/animus/core/notification/use_cases/__init__.py`
    - `src/animus/core/notification/__init__.py`
  - **Ação:** Adicionar `SendPetitionDraftFinishedNotificationUseCase` e `SendJudgmentDraftFinishedNotificationUseCase` aos exports públicos.
  - **Dependências:** T1.6, T1.7
  - **Resultado:** A camada PubSub consegue importar os novos use cases pelos pontos públicos do módulo.

### F2: Drivers/Infra - Provider

**Objetivo:** traduzir os contratos do `PushNotificationProvider` para payloads OneSignal compatíveis com o mobile, incluindo `analysis_type` em `data`.

- [ ] **T2.1: Atualizar métodos existentes do OneSignal provider**
  - **Arquivo:** `src/animus/providers/notification/push_notification/one_signal/one_signal_push_notification_provider.py`
  - **Ação:** Alterar `send_case_summary_finished_message(...)` e `send_precedents_search_finished_message(...)` para receber `analysis_type` e incluí-lo no `data`.
  - **Dependência:** T1.4
  - **Resultado:** Notificações já registradas continuam compatíveis e passam a permitir deep link por tipo de análise.

- [ ] **T2.2: Implementar mensagem própria de resumo de petição**
  - **Arquivo:** `src/animus/providers/notification/push_notification/one_signal/one_signal_push_notification_provider.py`
  - **Ação:** Criar `send_petition_summary_finished_message(...)` com `data.type = 'petition_summary_finished'`, `analysis_id` e `analysis_type`.
  - **Dependência:** T1.4
  - **Resultado:** O provider deixa de reutilizar indevidamente a mensagem de resumo de caso.

- [ ] **T2.3: Implementar mensagens de conclusão de minutas**
  - **Arquivo:** `src/animus/providers/notification/push_notification/one_signal/one_signal_push_notification_provider.py`
  - **Ação:** Criar `send_petition_draft_finished_message(...)` com `data.type = 'petition_draft_finished'` e `send_second_instance_judgment_draft_finished_message(...)` com `data.type = 'judgment_draft_finished'`.
  - **Dependência:** T1.4
  - **Resultado:** O adaptador externo passa a suportar os dois novos eventos de conclusão de minuta.

### F3: Drivers/Infra - PubSub

**Objetivo:** garantir que publishers emitam `analysis_type`, que jobs de notificação normalizem o payload completo e que todos os jobs necessários estejam registrados no runtime Inngest.

- [ ] **T3.1: Propagar `analysis_type` no publisher de minuta de petição**
  - **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/generate_petition_draft_job.py`
  - **Ação:** Incluir `analysis_type` em `_GenerationResult`, retornar `analysis.type.dto` após persistir a minuta e publicar `PetitionDraftGenerationFinishedEvent(analysis_id=..., account_id=..., analysis_type=...)`.
  - **Dependência:** T1.3
  - **Resultado:** A conclusão da minuta de petição passa a carregar o payload necessário para notificação.

- [ ] **T3.2: Publicar evento de conclusão de minuta de sentença**
  - **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/generate_judgment_draft_job.py`
  - **Ação:** Fazer o step de persistência retornar `analysis_id`, `account_id` e `analysis_type`; após persistência bem-sucedida, publicar `SecondInstanceJudgmentDraftGenerationFinishedEvent(...)`.
  - **Dependências:** T1.1, T1.2
  - **Resultado:** A geração de minuta de sentença passa a disparar o evento consumido pela notificação push.

- [ ] **T3.3: Propagar `analysis_type` no publisher de busca de precedentes**
  - **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`
  - **Ação:** Obter `analysis.type.dto` junto com `account_id` e publicar `PrecedentsSearchFinishedEvent(..., analysis_type=...)`.
  - **Dependência:** T1.3
  - **Resultado:** A notificação de precedentes finalizados recebe o tipo de análise correto.

- [ ] **T3.4: Propagar `analysis_type` nos publishers de resumo de caso**
  - **Arquivos:**
    - `src/animus/pubsub/inngest/jobs/intake/summarize_first_instance_case_job.py`
    - `src/animus/pubsub/inngest/jobs/intake/summarize_case_assessment_case_job.py`
    - `src/animus/pubsub/inngest/jobs/intake/summarize_second_instance_case_job.py`
  - **Ação:** Incluir `analysis_type` no resultado de sumarização e publicar `CaseSummaryFinishedEvent(..., analysis_type=...)`.
  - **Dependência:** T1.3
  - **Resultado:** Todos os publishers do mesmo evento mantêm o contrato atualizado.

- [ ] **T3.5: Atualizar job de notificação de resumo de caso**
  - **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/send_case_summary_finished_notification_job.py`
  - **Ação:** Adicionar `analysis_type` ao payload normalizado e repassar para `SendCaseSummaryFinishedNotificationUseCase.execute(...)`.
  - **Dependências:** T1.5, T3.4
  - **Resultado:** O consumidor do evento atualizado usa o payload completo.

- [ ] **T3.6: Corrigir job de notificação de resumo de petição**
  - **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/send_petition_summary_finished_notification_job.py`
  - **Ação:** Trocar o import para `SendPetitionSummaryFinishedNotificationUseCase`, normalizar `analysis_type` e repassar para o use case específico.
  - **Dependências:** T1.5, T2.2
  - **Resultado:** O job passa a enviar a mensagem correta para resumo de petição.

- [ ] **T3.7: Atualizar job de notificação de precedentes**
  - **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/send_precedents_search_finished_notification_job.py`
  - **Ação:** Adicionar `analysis_type` ao payload normalizado e repassar para `SendPrecedentsSearchFinishedNotificationUseCase.execute(...)`.
  - **Dependências:** T1.5, T2.1, T3.3
  - **Resultado:** O consumidor de busca de precedentes passa a incluir o tipo de análise no push.

- [ ] **T3.8: Criar job de notificação de minuta de petição**
  - **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/send_petition_draft_finished_notification_job.py`
  - **Ação:** Criar job consumindo `PetitionDraftGenerationFinishedEvent.name`, com `fn_id = 'send-petition-draft-finished-notification'`, steps `normalize_payload` e `send_notification`.
  - **Dependências:** T1.6, T2.3, T3.1
  - **Resultado:** O evento de conclusão de minuta de petição passa a ter consumidor de push.

- [ ] **T3.9: Criar job de notificação de minuta de sentença**
  - **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/send_judgment_draft_finished_notification_job.py`
  - **Ação:** Criar job consumindo `SecondInstanceJudgmentDraftGenerationFinishedEvent.name`, com `fn_id = 'send-judgment-draft-finished-notification'`, steps `normalize_payload` e `send_notification`.
  - **Dependências:** T1.7, T2.3, T3.2
  - **Resultado:** O evento de conclusão de minuta de sentença passa a ter consumidor de push.

- [ ] **T3.10: Exportar jobs de notificação faltantes**
  - **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/__init__.py`
  - **Ação:** Exportar `SendPetitionSummaryFinishedNotificationJob`, `SendPetitionDraftFinishedNotificationJob` e `SendSecondInstanceJudgmentDraftFinishedNotificationJob`.
  - **Dependências:** T3.6, T3.8, T3.9
  - **Resultado:** Os jobs ficam disponíveis para registro centralizado.

- [ ] **T3.11: Registrar jobs de notificação no InngestPubSub**
  - **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
  - **Ação:** Importar e registrar `SendPetitionSummaryFinishedNotificationJob.handle(inngest)`, `SendPetitionDraftFinishedNotificationJob.handle(inngest)` e `SendSecondInstanceJudgmentDraftFinishedNotificationJob.handle(inngest)` em `register_notification_jobs(...)`.
  - **Dependência:** T3.10
  - **Resultado:** Os novos/corrigidos jobs passam a ser expostos ao runtime do Inngest.

### F4: API Layer / Fronteira HTTP

**Objetivo:** preservar o escopo definido: sem alterar endpoints HTTP, routers, pipes, middlewares, schemas de request/response ou contratos REST.

- [ ] **T4.1: Confirmar que a entrega não altera a API HTTP**
  - **Arquivos:** nenhum arquivo de API deve ser alterado.
  - **Ação:** Revisar o diff local para garantir que não houve mudanças em `src/animus/rest/`, `src/animus/routers/`, `src/animus/pipes/` ou `src/animus/validation/`.
  - **Dependência:** F1
  - **Resultado:** A camada HTTP permanece fora do escopo da ANI-120.

### F5: Validação Operacional

**Objetivo:** validar a consistência operacional e estática da implementação, sem incluir criação ou alteração de testes automatizados neste plano.

- [ ] **T5.1: Executar migrations no ambiente local**
  - **Comando:** `uv run alembic upgrade head`
  - **Ação:** Rodar o comando mesmo sem nova migration no escopo.
  - **Dependências:** F2, F3, F4
  - **Resultado:** Ambiente local confirma que a base está na head do Alembic.

- [ ] **T5.2: Executar checagem de estilo e análise estática**
  - **Comando:** `uv run poe codecheck`
  - **Ação:** Corrigir problemas de lint/format apontados pelo projeto.
  - **Dependência:** T5.1
  - **Resultado:** Código segue o padrão automatizado do repositório.

- [ ] **T5.3: Executar typecheck**
  - **Comando:** `uv run poe typecheck`
  - **Ação:** Corrigir incompatibilidades de assinatura causadas pela adição de `analysis_type`.
  - **Dependência:** T5.2
  - **Resultado:** Contratos atualizados ficam consistentes para o BasedPyright.

- [ ] **T5.4: Revisar manualmente os payloads de push**
  - **Ação:** Conferir que todos os payloads mantêm `type` e `analysis_id` e adicionam `analysis_type`, sem dados sensíveis.
  - **Dependência:** T5.3
  - **Resultado:** Contrato de deep link do mobile fica preservado e ampliado conforme a spec.

---

## 3. Ordem de Execução Recomendada (Bottom-Up)

1. **Core (F1):** T1.1 -> T1.2 -> T1.3 -> T1.4 -> T1.5 -> T1.6 -> T1.7 -> T1.8.
2. **Drivers/Infra - Provider (F2):** T2.1 -> T2.2 -> T2.3.
3. **Drivers/Infra - PubSub (F3):** T3.1 -> T3.2 -> T3.3 -> T3.4 -> T3.5 -> T3.6 -> T3.7 -> T3.8 -> T3.9 -> T3.10 -> T3.11.
4. **API Layer / Fronteira HTTP (F4):** T4.1.
5. **Validação Operacional (F5):** T5.1 -> T5.2 -> T5.3 -> T5.4.

---

## 4. Observações de Escopo

- A spec local prevalece sobre a nomenclatura genérica do Jira: reutilizar `PetitionDraftGenerationFinishedEvent` e criar `SecondInstanceJudgmentDraftGenerationFinishedEvent`, seguindo o padrão já existente na codebase.
- Não criar migrations, models, mappers, repositories, endpoints HTTP, routers, pipes ou schemas para esta entrega.
- Não incluir tarefas de criação ou alteração de testes automatizados neste plano, conforme regra do prompt de criação de plano.
- Validar com o mobile os valores exatos de `data.type` antes de concluir a implementação do provider, especialmente `petition_draft_finished`, `judgment_draft_finished` e `petition_summary_finished`.
