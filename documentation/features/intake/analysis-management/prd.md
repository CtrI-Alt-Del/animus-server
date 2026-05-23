# PRD - Intake / Analysis Management

## Objetivo

Consolidar o fluxo de analise inicial para diferentes contextos processuais, permitindo que cada analise tenha tipo, status, documento principal, resumo estruturado e relatorio final coerentes com o trabalho do usuario.

## Itens concluidos

- [x] A criacao de analise agora recebe o tipo da analise e inicia o fluxo em `WAITING_DOCUMENT_UPLOAD`.
- [x] O documento principal da analise passou a ser tratado como artefato proprio da analise, sem depender do agregado legado de `Petition`.
- [x] O resumo estruturado do caso passou a ser persistido e consultado por `analysis_id` como `CaseSummary`.
- [x] Foram adicionados endpoints dedicados para upload/leitura de documento e request/leitura de resumo do caso no fluxo centrado em `analysis`.
- [x] Os relatorios finais passaram a ser separados por tipo de analise: `case-assessment`, `first-instance` e `second-instance`.
- [x] O dominio agora diferencia tipos e status de analise para suportar fluxos distintos de advogado e magistrado.
- [x] Os contratos persistidos de `PetitionDraft` e `SecondInstanceJudgmentDraft` foram preparados para as entregas assíncronas futuras.
- [x] A minuta estruturada de sentenca de segunda instancia pode ser consultada pelo dono da analise quando ja estiver disponivel.
- [x] O processamento assíncrono e as notificacoes do resumo do caso foram renomeados para refletir `case_summary`.

## Valor entregue

- O produto passa a representar melhor o ciclo real de trabalho juridico, separando analises consultivas, de primeira instancia e de segunda instancia.
- O back-end fica pronto para habilitar minutas e rascunhos especificos por tipo de analise sem retrabalho estrutural.
- O cliente pode consultar status e relatorios mais precisos, reduzindo ambiguidade no acompanhamento do processamento.

## Pendencias conhecidas fora deste escopo

- Geracao automatica de `PetitionDraft` permanece dependente do `ANI-93`.
- Geracao automatica de `SecondInstanceJudgmentDraft` permanece dependente do `ANI-94`.

## Divergencias consolidadas em relacao ao planejamento original

- O modulo nao tinha PRD local versionado no repositorio; este documento passa a registrar o escopo realmente entregue para fechar a feature no codigo.
