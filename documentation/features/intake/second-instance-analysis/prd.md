# PRD - Intake / Second Instance Analysis

## Objetivo

Entregar o processamento assíncrono da petição inicial dentro dos autos completos de análises de segunda instância, permitindo que o produto gere `CaseSummary` mais aderente ao contexto recursal sem alterar o contrato HTTP já usado pelo app.

## Itens concluídos

- [x] O request de resumo de caso para `SECOND_INSTANCE` passou a disparar um fluxo assíncrono específico de extração da petição inicial.
- [x] O sistema passou a persistir cache dos limites da petição extraída por `analysis_id`, evitando reprocessamento desnecessário.
- [x] A leitura de PDF foi estendida para contar páginas e extrair apenas o intervalo relevante da petição inicial.
- [x] Foram adicionados workflows de AI específicos para localizar a petição inicial e resumir o caso com foco recursal.
- [x] O job assíncrono de segunda instância passou a publicar `CaseSummaryFinishedEvent` apenas após concluir a sumarização com sucesso.
- [x] O fluxo passou a diferenciar ausência de petição inicial (`PETITION_NOT_FOUND`) de falha técnica (`FAILED`) para melhorar observabilidade e UX.
- [x] A persistência foi preparada com a nova tabela `extracted_petitions`, vinculada ao ciclo de vida da análise.

## Valor entregue

- O resumo de segunda instância passa a considerar a peça processual correta dentro dos autos, aumentando a qualidade do contexto usado nas etapas seguintes do produto.
- O tempo e o custo de reprocessamento diminuem em reexecuções, graças ao cache persistido dos limites da petição.
- O acompanhamento do processamento fica mais claro para o cliente, com status distintos para falha técnica e para ausência de petição identificável.

## Pendências conhecidas fora deste escopo

- Não há confirmação ou correção manual, pelo usuário, das páginas extraídas da petição inicial.
- O fluxo continua dependente de PDFs com camada textual legível; OCR segue fora deste escopo.
- O request de processamento continua sendo uma ação separada do upload do documento principal.

## Divergências consolidadas em relação ao planejamento original

- O módulo não tinha PRD local versionado no repositório; este documento passa a registrar o escopo realmente entregue para fechar a feature no código.
- A implementação usa o diretório `src/animus/ai/agno/squads/` como composição dos agentes, em vez do diretório `teams/` citado na spec original, sem alterar o comportamento entregue.
