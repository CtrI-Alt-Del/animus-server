# Regras da Camada Database

# Visao Geral

- Objetivo da camada
  - Implementar a persistencia da aplicacao em `src/animus/database/`, isolando detalhes de SQLAlchemy, sessao, modelos e mapeamento.
- Responsabilidades principais
  - Definir models ORM, mappers e repositories concretos aderentes aos contratos publicados pelo `core`.
  - Centralizar criacao de engine, `Session`, context managers e bootstrap de acesso ao banco.
  - Sustentar seeders e operacoes de persistencia sem contaminar as camadas de entrada com detalhes de SQL.
- Limites da camada
  - Pode depender de SQLAlchemy, configuracao de banco e tipos do `core` necessarios para mapeamento e implementacao de interfaces.
  - Nao deve concentrar regra de negocio, status code, contratos HTTP, controle de roteamento ou validacao de transporte.
  - Nao deve expor models ORM diretamente para `rest`, `websocket` ou clientes externos.

# Estrutura de Diretorios Globais

- Mapa de pastas relevantes
  - `src/animus/database/sqlalchemy/`
  - `src/animus/database/sqlalchemy/models/`
  - `src/animus/database/sqlalchemy/mappers/`
  - `src/animus/database/sqlalchemy/repositories/`
  - `src/animus/database/sqlalchemy/seeders/`
- Responsabilidade de cada diretorio
  - `sqlalchemy/`: configuracao de engine, session factory, base de acesso e exports da implementacao principal.
  - `sqlalchemy/models/<context>/`: representacao ORM das tabelas e relacionamentos por contexto.
  - `sqlalchemy/mappers/<context>/`: traducao entre models ORM e tipos de dominio do `core`.
  - `sqlalchemy/repositories/<context>/`: adaptadores concretos que implementam as portas de repositorio do `core`.
  - `sqlalchemy/seeders/`: carga inicial ou utilitarios de dados de suporte para ambiente de desenvolvimento.
- Regras de organizacao e nomeacao
  - A segmentacao por contexto deve acompanhar os bounded contexts do projeto (`auth`, `profiling`, `matching`, `conversation` e afins).
  - Models devem ficar separados de mappers e repositories; cada pasta tem uma responsabilidade unica.
  - Repositorios concretos devem seguir um prefixo explicito da tecnologia (`Sqlalchemy`) e mappers devem usar sufixo `Mapper`.
  - Nao especificar arquivos especificos, pois isso muda constantemente.

# Glossario arquitetural da camada

- `Engine`
  - Conexao base com o banco, criada uma vez e reutilizada pela camada.
- `Session`
  - Unidade de trabalho transacional usada por request HTTP, job assincrono ou fluxo WebSocket.
- `Model`
  - Representacao ORM da persistencia. Deve refletir schema e relacionamento, nao regra de negocio.
- `Mapper`
  - Tradutor entre `Model` e tipos do `core`. Deve concentrar a conversao dominio <-> persistencia.
- `Repository`
  - Adaptador concreto que implementa uma interface do `core` usando `Session` e SQLAlchemy.
- `Seeder`
  - Utilitario de preparacao de dados para ambientes controlados, sem substituir migrations ou regra de negocio.

# Padroes de Projeto

- Padroes arquiteturais aceitos
  - Repository Pattern para implementar portas do dominio.
  - Data Mapper para separar regras de conversao de regras de consulta e persistencia.
  - Session per Request e Session per Scope para isolar ciclo transacional em HTTP, jobs e WebSocket.
  - Ports and Adapters para manter `database` como adaptador de saida do `core`.
- Como aplicar cada padrao na camada
  - Cada repository deve implementar apenas o contrato do `core`, sem adicionar comportamento fora da semantica esperada.
  - Toda conversao entre ORM e dominio deve passar por mapper dedicado ou por uma estrategia equivalente concentrada na camada.
  - A sessao deve ser recebida de fora da camada: middleware em HTTP, context manager em jobs e composition root em WebSocket.
  - Alteracoes de schema devem ser refletidas em models, mappers e repositories de forma coerente e versionadas com migration fora deste documento.
- Quando evitar cada padrao
  - Nao usar repository para encapsular regra de negocio ou branching que deveria estar em `UseCase`.
  - Nao pular mapper para retornar ORM direto na borda so por conveniencia.
  - Nao abrir e fechar sessao dentro de metodos pequenos quando o escopo transacional ja e controlado por outra camada.

# Regras de Integracao com Outras Camadas

- Dependencias permitidas e proibidas
  - `database` pode importar entidades, DTOs, structures e interfaces do `core`.
  - `database` nao deve depender de `rest/controllers`, `routers` HTTP, `pipes` de borda ou `websocket/channels` para funcionar.
- Contratos/interface de comunicacao
  - Repositories concretos devem honrar exatamente as assinaturas e expectativas das interfaces do `core`.
  - Camadas externas devem receber tipos de dominio ou DTOs, nunca `Model` ORM como contrato publico.
  - Sessao e transacao sao contratos operacionais do adaptador, nao parte do dominio.
- Direcao de dependencia e limites de acoplamento
  - `rest` consome repositories via `DatabasePipe` e `Depends(...)`.
  - `pubsub` e `websocket` podem instanciar repositories concretos como composition root quando gerenciam sua propria sessao.
  - `core` nunca deve importar `database`, mesmo para consultas aparentemente simples.

# Checklist Rapido para Novas Features na Camada

- Itens objetivos de validacao antes de abrir PR
  - Existe model ORM adequado para o dado persistido ou a alteracao de schema foi refletida corretamente.
  - Existe mapper claro para traduzir entre persistencia e tipos do `core`.
  - O repository implementa uma interface existente do `core` ou a porta foi criada antes no dominio.
  - O ciclo de `Session` esta fora do repository e a integracao usa a estrategia correta para o fluxo.
  - A alteracao exige migration e o plano de evolucao de schema foi considerado.
- Criterios minimos de conformidade arquitetural
  - Nenhuma regra de negocio relevante foi movida do `core` para SQLAlchemy.
  - Nenhum controller ou channel depende de `Model` ORM como contrato de saida.
  - Os repositories continuam aderentes ao contrato do `core` apos a mudanca.
- Sinais de alerta para revisao tecnica
  - Repository chamando `commit()` ou `rollback()` por conta propria sem ser dono do escopo transacional.
  - Query retornando `Model` diretamente para a camada REST ou WebSocket.
  - Mapper ausente em um fluxo que precisa reconstruir entidade, DTO ou structure de dominio.

## ✅ O que DEVE conter
- Elementos obrigatorios da camada
  - Models, mappers e repositories organizados por contexto e por responsabilidade.
  - Implementacoes concretas aderentes aos contratos do `core`.
  - Infraestrutura de `Session` e engine centralizada dentro da camada.
- Praticas recomendadas
  - Nomear classes com `Sqlalchemy*Repository`, `*Model` e `*Mapper`.
  - Manter arquivos em `snake_case` e exports publicos em `__init__.py`.
  - Tratar conversoes de banco em um unico lugar, reduzindo duplicacao entre repositories.

## ❌ O que NUNCA deve conter
- Antipadroes e acoplamentos proibidos
  - Regras de negocio da aplicacao, validacoes de dominio ou decisao de fluxo HTTP.
  - Dependencia de `APIRouter`, `Request`, `WebSocket`, `Depends(...)` ou status code.
  - Exposicao de ORM como contrato publico da API.
- Responsabilidades que pertencem a outras camadas
  - Orquestracao de fluxo pertence ao `core` e as bordas de entrada.
  - Traducao para contrato HTTP pertence a `rest` e `validation`.
  - Publicacao de eventos e side effects externos pertencem a `pubsub` e `providers`.
  - Lançar erro de dominio no repository para ausencia de registro (ex.: `find_by_id`/`find_by_email` levantando `AccountNotFoundError`), em vez de retornar `None` conforme contrato da interface.
