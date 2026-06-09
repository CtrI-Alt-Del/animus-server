---
title: Notificacoes push de conclusao de minutas com analysis_type
prd:
  - https://joaogoliveiragarcia.atlassian.net/wiki/x/AYDsAg
  - https://joaogoliveiragarcia.atlassian.net/wiki/x/AQDxAg
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-120
status: closed
last_updated_at: 2026-05-27
---

# 1. Objetivo

Estender o fluxo de notificacoes push do `animus-server` para avisar o usuario quando a geração de minuta de petição inicial (RF 07) ou minuta de sentenca de 2a instancia (RF 08) for concluida, e propagar `analysis_type` nas notificacoes push de eventos de analise que direcionam o mobile para uma tela especifica. A entrega deve preservar o isolamento do `core`, consumir eventos via `Inngest` e incluir `analysis_type` no `data` enviado pelo `PushNotificationProvider` para que o app construa o deep link correto por tipo de analise.

---

# 2. Escopo

## 2.1 In-scope

- Criar a notificação push de conclusao de **minuta de sentenca** para o fluxo RF 08.
- Criar a notificação push de conclusao de **minuta de petição inicial** para o fluxo RF 07.
- Incluir `analysis_type` nos payloads dos eventos de conclusao consumidos por jobs de notificação.
- Incluir `analysis_type` no `data` enviado ao OneSignal.
- Corrigir o fluxo existente de notificação de resumo de petição para usar o use case/provider especifico de resumo de petição, em vez de reutilizar a mensagem de resumo de caso.
- Corrigir a notificação existente de busca de precedentes para repassar `analysis_type`.
- Registrar os jobs de notificação faltantes em `InngestPubSub.register_notification_jobs(...)`.

## 2.2 Out-of-scope

- Alterar endpoints HTTP, routers, pipes ou schemas de resposta.
- Criar novos modelos, repositorios, mappers ou migracoes Alembic.
- Implementar edição, download ou exportação das minutas.
- Alterar regras de geração de minuta, busca de precedentes ou sumarização.
- Definir comportamento visual do deep link no mobile.
- Reestruturar a integração com OneSignal ou trocar o provedor de push.

---

# 3. Requisitos

## 3.1 Funcionais

- Ao concluir a geração de uma **minuta de petição inicial**, o sistema deve publicar um evento com `analysis_id`, `account_id` e `analysis_type`.
- Ao concluir a geração de uma **minuta de sentenca de 2a instancia**, o sistema deve publicar um evento com `analysis_id`, `account_id` e `analysis_type`.
- Ao consumir esses eventos, o sistema deve enviar push para o `account_id` da analise correspondente.
- O payload `data` de toda notificação contemplada nesta spec deve conter:
  - `type`: identificador do evento para o mobile.
  - `analysis_id`: ID da analise.
  - `analysis_type`: valor de `Analysis.type.dto`.
- A notificação de busca de precedentes finalizada deve passar a incluir `analysis_type`.
- A notificação de resumo de petição finalizado deve passar a incluir `analysis_type` e chamar `send_petition_summary_finished_message(...)`.

## 3.2 Nao funcionais

- **Compatibilidade retroativa:** manter `type` e `analysis_id` nos payloads de push existentes; apenas adicionar `analysis_type`.
- **Idempotencia:** jobs de notificação devem ser tolerantes a reentrega do `Inngest`; reenviar a mesma push em retry e aceitavel, mas o job nao deve persistir estado nem alterar dominio.
- **Seguranca:** `recipient_id` deve continuar sendo o `account_id` da analise/evento; nenhum dado sensivel deve ser incluido no push.
- **Observabilidade:** manter os `fn_id` dos jobs existentes e definir `fn_id` estavel para os novos jobs.
- **Limite arquitetural:** `core` continua sem conhecer OneSignal, `Inngest`, HTTP ou variaveis de ambiente.

---

# 4. O que ja existe?

## Core / Intake

- **`Analysis`** (`src/animus/core/intake/domain/entities/analysis.py`) - entidade ja possui `type: AnalysisType` e expoe `type=self.type.dto` no DTO; essa e a fonte do `analysis_type`.
- **`CaseSummaryFinishedEvent`** (`src/animus/core/intake/domain/events/case_summary_finished_event.py`) - evento de fim de resumo de caso com payload atual `analysis_id` e `account_id`.
- **`PetitionSummaryFinishedEvent`** (`src/animus/core/intake/domain/events/petition_summary_finished_event.py`) - evento exportado com payload atual `analysis_id` e `account_id`; nao foi encontrado publisher na codebase.
- **`PrecedentsSearchFinishedEvent`** (`src/animus/core/intake/domain/events/precedents_search_finished_event.py`) - evento publicado ao fim da busca/sintese de precedentes com `analysis_id` e `account_id`.
- **`PetitionDraftGenerationFinishedEvent`** (`src/animus/core/intake/domain/events/petition_draft_generation_finished_event.py`) - evento existente para fim da geração de minuta de petição, atualmente sem `analysis_type`.
- **`SecondInstanceJudgmentDraftGenerationTriggeredEvent`** (`src/animus/core/intake/domain/events/second_instance_judgment_draft_generation_event.py`) - evento de disparo da geração de minuta de sentenca; ainda nao ha evento equivalente de conclusao.

## Core / Notification

- **`PushNotificationProvider`** (`src/animus/core/notification/interfaces/push_notification_provider.py`) - port atual expoe `send_case_summary_finished_message(...)` e `send_precedents_search_finished_message(...)`, ambos sem `analysis_type`.
- **`SendCaseSummaryFinishedNotificationUseCase`** (`src/animus/core/notification/use_cases/send_case_summary_finished_notification_use_case.py`) - delega para `send_case_summary_finished_message(...)`.
- **`SendPetitionSummaryFinishedNotificationUseCase`** (`src/animus/core/notification/use_cases/send_petition_summary_finished_notification_use_case.py`) - existe, mas atualmente chama `send_case_summary_finished_message(...)`; precisa ser corrigido para mensagem propria.
- **`SendPrecedentsSearchFinishedNotificationUseCase`** (`src/animus/core/notification/use_cases/send_precedents_search_finished_notification_use_case.py`) - delega para `send_precedents_search_finished_message(...)`.

## Providers

- **`OneSignalPushNotificationProvider`** (`src/animus/providers/notification/push_notification/one_signal/one_signal_push_notification_provider.py`) - envia push via OneSignal com `data` contendo `type` e `analysis_id`; nao envia `analysis_type`.
- **`providers.notification.__init__`** (`src/animus/providers/notification/__init__.py`) - exporta `OneSignalPushNotificationProvider`.

## PubSub / Inngest

- **`SendCaseSummaryFinishedNotificationJob`** (`src/animus/pubsub/inngest/jobs/notification/send_case_summary_finished_notification_job.py`) - consome `CaseSummaryFinishedEvent`, normaliza `analysis_id` e `account_id`, e aciona `SendCaseSummaryFinishedNotificationUseCase`.
- **`SendPetitionSummaryFinishedNotificationJob`** (`src/animus/pubsub/inngest/jobs/notification/send_petition_summary_finished_notification_job.py`) - existe, mas importa `SendCaseSummaryFinishedNotificationUseCase`, nao normaliza `analysis_type`, nao esta exportado em `jobs/notification/__init__.py` e nao esta registrado no `InngestPubSub`.
- **`SendPrecedentsSearchFinishedNotificationJob`** (`src/animus/pubsub/inngest/jobs/notification/send_precedents_search_finished_notification_job.py`) - consome `PrecedentsSearchFinishedEvent`, sem `analysis_type`.
- **`InngestPubSub`** (`src/animus/pubsub/inngest/inngest_pubsub.py`) - registra `SendCaseSummaryFinishedNotificationJob` e `SendPrecedentsSearchFinishedNotificationJob`, mas nao registra `SendPetitionSummaryFinishedNotificationJob` nem jobs de minutas.
- **`GeneratePetitionDraftJob`** (`src/animus/pubsub/inngest/jobs/intake/generate_petition_draft_job.py`) - ja publica `PetitionDraftGenerationFinishedEvent` apos persistir a minuta, mas retorna apenas `analysis_id` e `account_id` no resultado de geração.
- **`GenerateSecondInstanceJudgmentDraftJob`** (`src/animus/pubsub/inngest/jobs/intake/generate_judgment_draft_job.py`) - persiste a minuta de sentenca, mas ainda nao publica evento de conclusao.
- **`SearchAnalysisPrecedentsJob`** (`src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`) - publica `PrecedentsSearchFinishedEvent` com `analysis_id` e `account_id`, mas nao carrega `analysis_type`.

---

# 5. O que deve ser criado?

## Camada Core (Eventos de Dominio)

- **Localização:** `src/animus/core/intake/domain/events/second_instance_judgment_draft_generation_finished_event.py` (**novo arquivo**)
- **Classe:** `SecondInstanceJudgmentDraftGenerationFinishedEvent`
- **`NAME`:** usar o padrao existente em atributo `name = 'intake/judgment_draft.generation.finished'`
- **Payload:** `_Payload(analysis_id: str, account_id: str, analysis_type: str)`
- **Construtor:** `__init__(analysis_id: str, account_id: str, analysis_type: str) -> None` - cria payload imutavel e chama `Event.__init__`.
- **Export:** adicionar em `src/animus/core/intake/domain/events/__init__.py`.

## Camada Core (Use Cases)

- **Localização:** `src/animus/core/notification/use_cases/send_petition_draft_finished_notification_use_case.py` (**novo arquivo**)
- **Dependencias:** `PushNotificationProvider`
- **Metodo principal:** `execute(account_id: Id, analysis_id: Id, analysis_type: str) -> None` - envia push de conclusao de minuta de petição pelo port.

- **Localização:** `src/animus/core/notification/use_cases/send_judgment_draft_finished_notification_use_case.py` (**novo arquivo**)
- **Dependencias:** `PushNotificationProvider`
- **Metodo principal:** `execute(account_id: Id, analysis_id: Id, analysis_type: str) -> None` - envia push de conclusao de minuta de sentenca pelo port.

- **Exports:** adicionar os dois use cases em:
  - `src/animus/core/notification/use_cases/__init__.py`
  - `src/animus/core/notification/__init__.py`

## Camada PubSub (Jobs Inngest)

- **Localização:** `src/animus/pubsub/inngest/jobs/notification/send_petition_draft_finished_notification_job.py` (**novo arquivo**)
- **Evento consumido:** `PetitionDraftGenerationFinishedEvent.name`
- **Payload esperado:** `analysis_id: str`, `account_id: str`, `analysis_type: str`
- **`fn_id`:** `send-petition-draft-finished-notification`
- **Passos (`step.run`):**
  - `normalize_payload` - converte os tres campos para `str`.
  - `send_notification` - executa `SendPetitionDraftFinishedNotificationUseCase` com `OneSignalPushNotificationProvider`.
- **Idempotencia:** sem escrita em banco; retry pode reenviar push.

- **Localização:** `src/animus/pubsub/inngest/jobs/notification/send_judgment_draft_finished_notification_job.py` (**novo arquivo**)
- **Evento consumido:** `SecondInstanceJudgmentDraftGenerationFinishedEvent.name`
- **Payload esperado:** `analysis_id: str`, `account_id: str`, `analysis_type: str`
- **`fn_id`:** `send-judgment-draft-finished-notification`
- **Passos (`step.run`):**
  - `normalize_payload` - converte os tres campos para `str`.
  - `send_notification` - executa `SendJudgmentDraftFinishedNotificationUseCase` com `OneSignalPushNotificationProvider`.
- **Idempotencia:** sem escrita em banco; retry pode reenviar push.

- **Exports e registro:**
  - Exportar os novos jobs em `src/animus/pubsub/inngest/jobs/notification/__init__.py`.
  - Registrar os novos jobs em `InngestPubSub.register_notification_jobs(...)`.

---

# 6. O que deve ser modificado?

## Camada Core (Eventos de Dominio)

- **Arquivo:** `src/animus/core/intake/domain/events/petition_draft_generation_finished_event.py`
- **Mudanca:** adicionar `analysis_type: str` ao `_Payload` e ao construtor `__init__(analysis_id: str, account_id: str, analysis_type: str) -> None`.
- **Justificativa:** o evento ja representa o fato de dominio correto; criar um segundo evento para o mesmo fato duplicaria contrato e consumidores.

- **Arquivo:** `src/animus/core/intake/domain/events/precedents_search_finished_event.py`
- **Mudanca:** adicionar `analysis_type: str` ao `_Payload` e ao construtor.
- **Justificativa:** a notificação de busca de precedentes precisa informar o tipo de analise ao mobile.

- **Arquivo:** `src/animus/core/intake/domain/events/petition_summary_finished_event.py`
- **Mudanca:** adicionar `analysis_type: str` ao `_Payload` e ao construtor.
- **Justificativa:** manter o contrato do evento alinhado ao job de notificação de resumo de petição.

- **Arquivo:** `src/animus/core/intake/domain/events/case_summary_finished_event.py`
- **Mudanca:** adicionar `analysis_type: str` ao `_Payload` e ao construtor se o fluxo existente de resumo de caso continuar enviando push via `SendCaseSummaryFinishedNotificationJob`.
- **Justificativa:** os jobs de sumarização existentes publicam este evento para mais de um tipo de analise; sem `analysis_type`, a notificação de resumo nao tem dados suficientes para deep link correto.

## Camada Core (Interfaces / Ports)

- **Arquivo:** `src/animus/core/notification/interfaces/push_notification_provider.py`
- **Mudanca:** atualizar/adicionar metodos:
  - `send_case_summary_finished_message(recipient_id: Id, analysis_id: Id, analysis_type: str) -> None`
  - `send_petition_summary_finished_message(recipient_id: Id, analysis_id: Id, analysis_type: str) -> None`
  - `send_precedents_search_finished_message(recipient_id: Id, analysis_id: Id, analysis_type: str) -> None`
  - `send_petition_draft_finished_message(recipient_id: Id, analysis_id: Id, analysis_type: str) -> None`
  - `send_second_instance_judgment_draft_finished_message(recipient_id: Id, analysis_id: Id, analysis_type: str) -> None`
- **Justificativa:** o port deve publicar todos os contratos de push usados pelo dominio de notificação e manter `analysis_type` explicito.

## Camada Core (Use Cases)

- **Arquivo:** `src/animus/core/notification/use_cases/send_case_summary_finished_notification_use_case.py`
- **Mudanca:** alterar `execute(account_id: Id, analysis_id: Id) -> None` para `execute(account_id: Id, analysis_id: Id, analysis_type: str) -> None` e repassar `analysis_type`.
- **Justificativa:** manter compatibilidade com o job atualmente registrado para `CaseSummaryFinishedEvent`.

- **Arquivo:** `src/animus/core/notification/use_cases/send_petition_summary_finished_notification_use_case.py`
- **Mudanca:** alterar `execute(account_id: Id, analysis_id: Id) -> None` para `execute(account_id: Id, analysis_id: Id, analysis_type: str) -> None` e chamar `send_petition_summary_finished_message(...)`.
- **Justificativa:** corrigir o comportamento atual, que usa a mensagem de resumo de caso para resumo de petição.

- **Arquivo:** `src/animus/core/notification/use_cases/send_precedents_search_finished_notification_use_case.py`
- **Mudanca:** alterar `execute(account_id: Id, analysis_id: Id) -> None` para `execute(account_id: Id, analysis_id: Id, analysis_type: str) -> None` e repassar `analysis_type`.
- **Justificativa:** o mobile precisa do tipo de analise ao receber a notificação.

## Camada Providers

- **Arquivo:** `src/animus/providers/notification/push_notification/one_signal/one_signal_push_notification_provider.py`
- **Mudanca:** atualizar metodos existentes e criar os metodos novos do port, incluindo `analysis_type` em `data`.
- **Payloads esperados:**
  - Resumo de caso: `{'type': 'case_summary_finished', 'analysis_id': analysis_id.value, 'analysis_type': analysis_type}`
  - Resumo de petição: `{'type': 'petition_summary_finished', 'analysis_id': analysis_id.value, 'analysis_type': analysis_type}`
  - Busca de precedentes: `{'type': 'precedents_search_finished', 'analysis_id': analysis_id.value, 'analysis_type': analysis_type}`
  - Minuta de petição: `{'type': 'petition_draft_finished', 'analysis_id': analysis_id.value, 'analysis_type': analysis_type}`
  - Minuta de sentenca: `{'type': 'judgment_draft_finished', 'analysis_id': analysis_id.value, 'analysis_type': analysis_type}`
- **Justificativa:** OneSignal e o adaptador externo responsavel por traduzir o contrato do port para o payload do mobile.

## Camada PubSub (Jobs Inngest)

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/generate_petition_draft_job.py`
- **Mudanca:** incluir `analysis_type` em `_GenerationResult`, retornar `analysis.type.dto` em `_generate_and_persist_petition_draft_sync(...)` e publicar `PetitionDraftGenerationFinishedEvent(analysis_id=..., account_id=..., analysis_type=...)`.
- **Justificativa:** a geração de minuta de petição ja possui o ponto correto de publicação apos persistencia bem-sucedida.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/generate_judgment_draft_job.py`
- **Mudanca:** fazer `_generate_and_persist_judgment_draft(...)` retornar `dict[str, str] | None` com `analysis_id`, `account_id` e `analysis_type`; apos o step de persistencia, publicar `SecondInstanceJudgmentDraftGenerationFinishedEvent(...)`.
- **Justificativa:** hoje a minuta de sentenca e persistida sem evento de conclusao, impedindo notificação push.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`
- **Mudanca:** obter `analysis_type` junto com `account_id` e publicar `PrecedentsSearchFinishedEvent(analysis_id=..., account_id=..., analysis_type=...)`.
- **Justificativa:** a notificação de busca de precedentes precisa do tipo de analise.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_first_instance_case_job.py`
- **Mudanca:** incluir `analysis_type` no resultado de sumarização e publicar `CaseSummaryFinishedEvent(..., analysis_type=...)`.
- **Justificativa:** este job publica evento consumido por notificação push e deve carregar o tipo da analise.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_case_assessment_case_job.py`
- **Mudanca:** incluir `analysis_type` no resultado de sumarização e publicar `CaseSummaryFinishedEvent(..., analysis_type=...)`.
- **Justificativa:** manter o mesmo contrato para todos os publishers de `CaseSummaryFinishedEvent`.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/intake/summarize_second_instance_case_job.py`
- **Mudanca:** incluir `analysis_type` no resultado de sumarização e publicar `CaseSummaryFinishedEvent(..., analysis_type=...)`.
- **Justificativa:** manter deep link correto para analises de 2a instancia.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/send_case_summary_finished_notification_job.py`
- **Mudanca:** adicionar `analysis_type` ao `_Payload`, normalizar `analysis_type` e repassar ao use case.
- **Justificativa:** compatibilizar consumidor com o evento atualizado.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/send_petition_summary_finished_notification_job.py`
- **Mudanca:** trocar import para `SendPetitionSummaryFinishedNotificationUseCase`, adicionar `analysis_type` ao `_Payload`, normalizar `analysis_type` e repassar ao use case.
- **Justificativa:** corrigir bug de wiring e habilitar o payload necessario ao deep link.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/send_precedents_search_finished_notification_job.py`
- **Mudanca:** adicionar `analysis_type` ao `_Payload`, normalizar `analysis_type` e repassar ao use case.
- **Justificativa:** compatibilizar consumidor com o evento atualizado.

- **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/__init__.py`
- **Mudanca:** exportar `SendPetitionSummaryFinishedNotificationJob`, `SendPetitionDraftFinishedNotificationJob` e `SendSecondInstanceJudgmentDraftFinishedNotificationJob`.
- **Justificativa:** permitir registro centralizado em `InngestPubSub`.

- **Arquivo:** `src/animus/pubsub/inngest/inngest_pubsub.py`
- **Mudanca:** importar e registrar:
  - `SendPetitionSummaryFinishedNotificationJob.handle(inngest)`
  - `SendPetitionDraftFinishedNotificationJob.handle(inngest)`
  - `SendSecondInstanceJudgmentDraftFinishedNotificationJob.handle(inngest)`
- **Justificativa:** jobs nao registrados nao serao expostos ao runtime do `Inngest`.

---

# 7. O que deve ser removido?

## Camada PubSub

- **Arquivo:** `src/animus/pubsub/inngest/jobs/notification/send_petition_summary_finished_notification_job.py`
- **Motivo da remoção:** remover apenas a dependencia incorreta de `SendCaseSummaryFinishedNotificationUseCase`.
- **Impacto esperado:** o job passa a acionar `SendPetitionSummaryFinishedNotificationUseCase`.

---

# 8. Decisoes Tecnicas e Trade-offs

- **Decisao:** reutilizar `PetitionDraftGenerationFinishedEvent` existente e criar `SecondInstanceJudgmentDraftGenerationFinishedEvent`.
- **Alternativas consideradas:** criar eventos `PetitionDraftGeneratedEvent` e `JudgmentDraftGeneratedEvent`, conforme nomes genericos do Jira.
- **Motivo da escolha:** a codebase ja usa o padrao `*GenerationTriggeredEvent` / `*GenerationFinishedEvent` para minutas; manter esse padrao reduz duplicidade e facilita descoberta.
- **Impactos / trade-offs:** o nome final diverge do texto do Jira, mas preserva consistencia local.

- **Decisao:** adicionar `analysis_type` aos eventos publicados, e nao buscar a analise dentro dos jobs de notificação.
- **Alternativas consideradas:** o job de notificação consultar `AnalysesRepository` para descobrir `analysis_type`.
- **Motivo da escolha:** o ticket pede propagação do valor desde o evento; jobs de notificação devem ser pequenos e sem acesso desnecessario a banco.
- **Impactos / trade-offs:** todos os publishers dos eventos atualizados precisam ser ajustados.

- **Decisao:** manter `analysis_type` como `str` nos eventos, use cases e provider.
- **Alternativas consideradas:** trafegar `AnalysisType` do dominio ate o provider.
- **Motivo da escolha:** o payload de evento e o `data` do push sao contratos serializaveis; `Analysis.type.dto` ja e o valor esperado pelo mobile.
- **Impactos / trade-offs:** validação semantica do valor fica na origem (`Analysis.type`), nao no provider.

- **Decisao:** registrar `SendPetitionSummaryFinishedNotificationJob` alem de corrigir sua implementação.
- **Alternativas consideradas:** remover o job por nao haver publisher encontrado.
- **Motivo da escolha:** o ticket trata esta notificação como existente/esperada, e a codebase ja possui evento, job e use case correspondentes, faltando wiring correto.
- **Impactos / trade-offs:** se o publisher continuar ausente, o registro nao tera efeito ate o evento ser publicado.

---

# 9. Diagramas e Referencias

## Fluxo de dados - minuta de petição

```text
GeneratePetitionDraftJob
  -> CreatePetitionDraftUseCase
  -> PostgreSQL (petition_drafts)
  -> PetitionDraftGenerationFinishedEvent { analysis_id, account_id, analysis_type }
  -> SendPetitionDraftFinishedNotificationJob
  -> SendPetitionDraftFinishedNotificationUseCase
  -> PushNotificationProvider
  -> OneSignalPushNotificationProvider
  -> OneSignal data { type, analysis_id, analysis_type }
```

## Fluxo de dados - minuta de sentenca

```text
GenerateSecondInstanceJudgmentDraftJob
  -> CreateSecondInstanceJudgmentDraftUseCase
  -> PostgreSQL (judgment_drafts)
  -> SecondInstanceJudgmentDraftGenerationFinishedEvent { analysis_id, account_id, analysis_type }
  -> SendSecondInstanceJudgmentDraftFinishedNotificationJob
  -> SendJudgmentDraftFinishedNotificationUseCase
  -> PushNotificationProvider
  -> OneSignalPushNotificationProvider
  -> OneSignal data { type, analysis_id, analysis_type }
```

## Fluxo de dados - notificacoes existentes corrigidas

```text
Publisher existente
  -> Event { analysis_id, account_id, analysis_type }
  -> NotificationJob.normalize_payload
  -> NotificationUseCase.execute(account_id, analysis_id, analysis_type)
  -> PushNotificationProvider.send_*_message(...)
  -> OneSignal data { type, analysis_id, analysis_type }
```

## Referencias

- `src/animus/core/intake/domain/entities/analysis.py`
- `src/animus/core/intake/domain/events/petition_draft_generation_finished_event.py`
- `src/animus/core/intake/domain/events/precedents_search_finished_event.py`
- `src/animus/core/notification/interfaces/push_notification_provider.py`
- `src/animus/core/notification/use_cases/send_petition_summary_finished_notification_use_case.py`
- `src/animus/providers/notification/push_notification/one_signal/one_signal_push_notification_provider.py`
- `src/animus/pubsub/inngest/jobs/intake/generate_petition_draft_job.py`
- `src/animus/pubsub/inngest/jobs/intake/generate_judgment_draft_job.py`
- `src/animus/pubsub/inngest/jobs/intake/search_analysis_precedents_job.py`
- `src/animus/pubsub/inngest/jobs/notification/send_petition_summary_finished_notification_job.py`
- `src/animus/pubsub/inngest/inngest_pubsub.py`

---

# 10. Pendencias / Duvidas

- **Descrição da pendencia:** confirmar com o mobile os valores exatos esperados em `data.type` para `petition_draft_finished`, `judgment_draft_finished` e `petition_summary_finished`.
- **Impacto na implementação:** se os valores divergirem, o push sera entregue, mas o app pode nao aplicar o deep link correto.
- **Ação sugerida:** validar com o responsavel do mobile antes de implementar os metodos do `OneSignalPushNotificationProvider`.

- **Descrição da pendencia:** nao foi encontrado publisher para `PetitionSummaryFinishedEvent`; existe evento, use case e job, mas o job nao esta registrado.
- **Impacto na implementação:** corrigir e registrar o job nao garante envio se nenhum fluxo publicar o evento.
- **Ação sugerida:** validar se a conclusao de resumo de petição deve publicar `PetitionSummaryFinishedEvent` em tarefa separada ou se o fluxo atual usa `CaseSummaryFinishedEvent` intencionalmente.

---

## Restricoes

- Nao incluir `FastAPI`, `SQLAlchemy`, `Inngest`, OneSignal ou `Env` dentro de arquivos do `core`.
- Nao adicionar testes automatizados neste documento de spec.
- Nao criar migracoes Alembic, models, mappers ou repositorios para esta tarefa.
- Nao alterar payloads existentes removendo `type` ou `analysis_id`; apenas adicionar `analysis_type`.
- Todo `analysis_type` propagado deve vir de `Analysis.type.dto`.
