# PRD — RF 03: Sintese explicativa da relacao dos precedentes com o caso inicial

## Visao Geral

Esta entrega consolida o fluxo backend de busca assincrona de precedentes para uma analise ja resumida. O usuario pode iniciar a busca com filtros opcionais, acompanhar o andamento pelo status da analise, consultar as peticoes e os precedentes persistidos e registrar qual precedente foi escolhido ao final do fluxo.

## Itens Concluidos

- [x] Permitir iniciar a busca de precedentes de forma assincrona para uma analise existente.
- [x] Permitir filtros opcionais por tribunal e tipo de precedente, com limite configuravel entre 5 e 10 resultados.
- [x] Reutilizar o resumo da peticao como base semantica para a busca dos precedentes.
- [x] Persistir os precedentes encontrados na analise com percentual de aplicabilidade e sintese por precedente.
- [x] Permitir polling do status da analise durante o processamento assincrono.
- [x] Permitir consultar os precedentes persistidos da analise.
- [x] Permitir consultar as peticoes da analise junto com seus resumos quando existirem.
- [x] Permitir registrar um unico precedente como escolhido e encerrar o fluxo da analise.

## Fora do Escopo Desta Entrega

- [ ] Exportacao do precedente escolhido no PDF final.
- [ ] Agrupamento visual dos precedentes por nivel de classificacao na interface cliente.
- [ ] Edicao manual da sintese explicativa gerada para cada precedente.
- [ ] Busca fora da base nacional de precedentes utilizada pelo produto.

## O Que Mudou em Relacao Ao PRD Original

- O backend persiste `applicability_percentage` e a `synthesis` por precedente; a classificacao em "Aplicavel", "Possivelmente aplicavel" e "Nao aplicavel" fica derivada na superficie de leitura do cliente.
- O acompanhamento do processamento passou a acontecer por transicoes persistidas em `Analysis.status`, sem eventos publicos intermediarios para o cliente.
- O fluxo de busca foi materializado com endpoints de leitura auxiliares para status, peticoes da analise, precedentes persistidos e confirmacao da escolha final.
