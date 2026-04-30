---
title: "[server] Notificar conclusão da análise de petição e da busca de precedentes"
prd: https://joaogoliveiragarcia.atlassian.net/wiki/spaces/ANM/pages/131218/Requisitos+do+produto
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-64
status: open
last_updated_at: 2026-04-22
---

# 1. Objetivo (Obrigatório)

Implementar os gatilhos de conclusão e os fluxos assíncronos necessários no `animus-server` para notificar o usuário quando a análise da petição estiver pronta e quando a busca/síntese de precedentes for finalizada. A integração ocorrerá via eventos de domínio publicados pelos jobs de `intake` e consumidos por novos jobs no contexto de `notification`, garantindo desacoplamento e consistência arquitetural.

---

# 2. Escopo (Obrigatório)

## 2.1 In-scope

- Criação de eventos de domínio: `PetitionSummaryFinishedEvent` e `PrecedentsSearchFinishedEvent`.
- Publicação destes eventos nos pontos de conclusão bem-sucedida dos jobs `SummarizePetitionJob` e `SearchAnalysisPrecedentsJob`.
- Criação de use cases de notificação: `SendPetitionSummaryFinishedNotificationUseCase` e `SendPrecedentsSearchFinishedNotificationUseCase`.
- Criação de jobs de notificação no Inngest: `SendPetitionSummaryFinishedNotificationJob` e `SendPrecedentsSearchFinishedNotificationJob`.
- Registro dos novos jobs no orquestrador `InngestPubSub`.

## 2.2 Out-of-scope

- Implementação do `PushNotificationProvider` concreto (OneSignal) — assumido como parte do `ANI-84`.
- Implementação de `PushNotificationMessage` structure — assumido como parte do `ANI-84`.
- Alterações no frontend para exibição das notificações.
- Notificações para estados de erro ou intermediários.

---

# 3. Requisitos (Obrigatório)

## 3.1 Funcionais

- O usuário deve ser notificado via push quando a análise inicial da petição for concluída com sucesso.
- O usuário deve ser notificado via push quando a busca e síntese de precedentes for finalizada com sucesso.
- As notificações devem ser enviadas apenas para a conta dona da análise.
- O fluxo não deve disparar notificações em caso de falha no processamento.

## 3.2 Não funcionais

- **Idempotência:** Os jobs de notificação devem ser seguros para re-execução, evitando notificações duplicadas quando possível.
- **Desacoplamento:** O contexto `intake` não deve conhecer detalhes de transporte de notificação; a comunicação deve ser via eventos.
- **Resiliência:** Se a análise ou conta associada não existir mais no momento do disparo, o job deve encerrar sem erros.

---

# 4. O que já existe? (Obrigatório)

## Camada Core (Use Cases)

- **`CreatePetitionSummaryUseCase`** (`src/animus/core/intake/use_cases/create_petition_summary_use_case.py`) — atualiza o status para `PETITION_ANALYZED`.
- **`CreateAnalysisPrecedentsUseCase`** (`src/animus/core/intake/use_cases/create_analysis_precedents_use_case.py`) — atualiza o status para `WAITING_PRECEDENT_CHOISE`.

## Camada Core (Interfaces)

- **`PushNotificationProvider`** (`src/animus/core/notification/interfaces/push_notification_provider.py`) — interface de envio de notificações push.

## Camada PubSub (Jobs)

- **`SummarizePetitionJob`** (`src/animus/pubsub/inngest/jobs/intake/summarize_petition_job.py`) — job que orquestra a sumarização.
- **`SearchAnalysisPrecedentsJob`** (`src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`) — job que orquestra a busca e síntese.

---

# 5. O que deve ser criado? (Depende da tarefa)

## Camada Core (Eventos de Domínio)

- **Localização:** `src/animus/core/intake/domain/events/petition_summary_finished_event.py` (**novo arquivo**)
- **`NAME`:** `"intake/petition_summary.finished"`
- **Payload:** `analysis_id: Id`

- **Localização:** `src/animus/core/intake/domain/events/precedents_search_finished_event.py` (**novo arquivo**)
- **`NAME`:** `"intake/precedents_search.finished"`
- **Payload:** `analysis_id: Id`
- **Nota:** Substitui semanticamente o `SynthesisGenerationEndedEvent`.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/notification/use_cases/send_petition_summary_finished_notification_use_case.py` (**novo arquivo**)
- **Dependências:** `PushNotificationProvider`
- **Método principal:** `execute(account_id: Id, analysis_id: Id) -> None` — delega ao provider o envio da mensagem.

- **Localização:** `src/animus/core/notification/use_cases/send_precedents_search_finished_notification_use_case.py` (**novo arquivo**)
- **Dependências:** `PushNotificationProvider`
- **Método principal:** `execute(account_id: Id, analysis_id: Id) -> None` — delega ao provider o envio da mensagem.

## Camada PubSub (Jobs Inngest)

- **Localização:** `src/animus/pubsub/inngest/jobs/notification/send_petition_summary_finished_notification_job.py` (**novo arquivo**)
- **Evento consumido:** `PetitionSummaryFinishedEvent.NAME`
- **Fluxo:** Recebe `analysis_id` -> Resolve `account_id` via `AnalisysesRepository` -> Chama `SendPetitionSummaryFinishedNotificationUseCase`.

- **Localização:** `src/animus/pubsub/inngest/jobs/notification/send_precedents_search_finished_notification_job.py` (**novo arquivo**)
- **Evento consumido:** `PrecedentsSearchFinishedEvent.NAME`
- **Fluxo:** Recebe `analysis_id` -> Resolve `account_id` via `AnalisysesRepository` -> Chama `SendPrecedentsSearchFinishedNotificationUseCase`.

---

# 6. O que deve ser modificado? (Depende da tarefa)

## Camada Core (Eventos)

- **Arquivo:** `src/animus/core/intake/domain/events/__init__.py`
- **Mudança:** Exportar os novos eventos e remover `SynthesisGenerationEndedEvent` se for substituído.

## Camada PubSub (Jobs)

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_petition_job.py`
- **Mudança:** Injetar `Broker` no executor ou usar via `PubSubPipe` (depende da implementação do job) para publicar `PetitionSummaryFinishedEvent` após a conclusão do workflow com sucesso.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`
- **Mudança:** Publicar `PrecedentsSearchFinishedEvent` após a conclusão bem-sucedida do passo de síntese.

## Camada PubSub (Orquestração)

- **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
- **Mudança:** Adicionar os novos jobs de notificação ao método `register_notification_jobs`.

---

# 7. O que deve ser removido? (Depende da tarefa)

## Camada Core (Eventos)

- **Arquivo:** `src/animus/core/intake/domain/events/synthesis_generation_ended_event.py`
- **Motivo da remoção:** Substituído por `PrecedentsSearchFinishedEvent` para consistência de nomenclatura.

---

# 8. Decisões Técnicas e Trade-offs (Obrigatório)

- **Decisão:** Substituir `SynthesisGenerationEndedEvent` por `PrecedentsSearchFinishedEvent`.
- **Alternativas consideradas:** Manter o nome atual.
- **Motivo da escolha:** Melhorar a semântica e alinhar com `PetitionSummaryFinishedEvent`, indicando o fim de uma etapa macro do processo de intake.

- **Decisão:** Realizar a resolução de `account_id` no Job de notificação.
- **Alternativas consideradas:** Incluir `account_id` no payload do evento original.
- **Motivo da escolha:** Mantém o payload do evento enxuto (apenas a entidade principal impactada) e permite que o job de notificação resolva o destinatário atualizado no momento do disparo.

---

# 9. Diagramas e Referências (Obrigatório)

## Fluxo de Notificação

```text
[SummarizePetitionJob]
      |
      v
(Publica PetitionSummaryFinishedEvent)
      |
      v
[SendPetitionSummaryFinishedNotificationJob] (Inngest)
      |
      +--> [AnalisysesRepository.find_by_id] (Resolve AccountId)
      |
      v
[SendPetitionSummaryFinishedNotificationUseCase]
      |
      v
[PushNotificationProvider.send]
```

## Referências na Codebase

- `src/animus/pubsub/inngest/jobs/auth/send_account_verification_email_job.py` (Referência para jobs de notificação)
- `src/animus/core/intake/domain/events/petition_summary_requested_event.py` (Referência para eventos de intake)

---

# 10. Pendências / Dúvidas (Quando aplicável)

- **Dependência ANI-84:** Verificou-se que `PushNotificationMessage` e a implementação concreta do `PushNotificationProvider` (OneSignal) não estão presentes na `main`. A implementação desta spec assume que estas estruturas serão providas conforme o ticket `ANI-84`.
- **Injeção de Broker nos Jobs:** Validar se os jobs de `intake` devem receber o `Broker` via injeção de dependência manual (já que rodam fora do request context) ou via `Sqlalchemy` utility similar aos repositórios.

---
