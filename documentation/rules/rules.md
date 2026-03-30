# Regras do Projeto

**Objetivo do documento:** reduzir contexto desnecessário e ler apenas as regras certas para cada tipo de tarefa. Use este documento como porta de entrada antes de consultar os demais arquivos em `documentation/rules/`.

## Ordem Recomendada de Leitura

1. Comece por este arquivo (`rules.md`).
2. Leia apenas os documentos acionados pelo tipo de mudança.
3. Se a tarefa crescer de escopo, desbloqueie o próximo documento necessário.
4. Em caso de dúvida entre duas camadas, leia primeiro a regra geral da camada e depois a regra específica de teste.

---

## `code-conventions-rules.md`

### Quando ler

- **SEMPRE** que realizar qualquer alteração ou escrita de código.
- Antes de executar tarefas de validação (`poe codecheck` ou `poe typecheck`).
- Ao padronizar estilo de código em features novas ou refactors.
- Ao revisar consistência de nomenclatura e organização de arquivos.
- Ao preparar PR com mudanças amplas para evitar divergência de estilo.

### Instruções práticas

- Siga convenções de nomes do projeto (arquivos, classes, sufixos de papel).
- Preserve estrutura de módulos e exports públicos (`__init__.py` / `__all__`).
- Priorize legibilidade e consistência com o padrão já existente.
- Evite introduzir padrão novo sem necessidade arquitetural clara.

---

## `core-layer-rules.md`

### Quando ler

- Ao criar/alterar **entidades**, **structures**, **DTOs**, **erros de domínio** ou **use cases**.
- Ao revisar limites arquiteturais entre `core` e outras camadas.
- Ao validar dependência correta entre `core`, `rest` e `database`.

### Instruções práticas

- Mantenha o `core` puro: sem FastAPI, ORM, SQL, sessão, env var ou HTTP.
- Centralize regra de negócio em entidades/structures/use cases.
- Use interfaces (ports) para dependências externas.
- Garanta convenções de nome: `*UseCase`, `*Dto`, `*Repository`, `execute(...)`.

---

## `database-layer-rules.md`

### Quando ler

- Ao criar/alterar **models**, **mappers**, **repositórios SQLAlchemy** ou sessão DB.
- Ao integrar persistência nova com interfaces do `core`.
- Ao ajustar fluxo de transação por request (`middleware` + `Session`).

### Instruções práticas

- Implemente apenas persistência e mapeamento; sem regra de negócio.
- Respeite exatamente o contrato das interfaces definidas no `core`.
- Use `mapper` para tradução domínio <-> ORM; não exponha ORM para bordas.
- Não espalhe `commit`/`rollback` em repositórios; ciclo transacional fica no `middleware`.

---

## `rest-layer-rules.md`

### Quando ler

- Ao criar/alterar **controllers**, **rotas** e **contratos HTTP**.
- Ao mexer em integração com schema de validação ou `response_model`.
- Ao conectar endpoint a use case e repositório concreto.

### Instruções práticas

- Mantenha controller fino: valida/adapta/delega, sem regra de negócio.
- Defina `status_code` e `response_model` explícitos nos endpoints.
- Converta entrada para DTO antes de chamar use case.
- Use dependência de `Session` por `Depends(...)` e sem controlar transação no controller.

---

## `routers-layers-rules.md`

### Quando ler

- Ao criar/alterar **routers** e organização de rotas por módulo.
- Ao definir `prefix`, `tags` e hierarquia de sub-routers.
- Ao integrar novos routers no composition root (`app.py`).

### Instruções práticas

- **Router = composição**, **Controller = endpoint**.
- Defina routers como classes com método estático `register() -> APIRouter`.
- Agrupe por contexto: um router por módulo (ex: `AuthRouter`, `ProfilingRouter`).
- Não declare funções `@router.get/post/...` diretamente no router; use `Controller.handle(router)`.

---

## `pipes-layer-rules.md`

### Quando ler

- Ao criar/alterar **pipes** (provedores de dependência para FastAPI).
- Ao injetar repositórios, providers, `Broker` ou validar uploads.
- Ao criar novo `Depends(...)` reutilizável em controllers.

### Instruções práticas

- Pipes são **dependency providers**, não pipeline de processamento.
- Retorne interfaces do `core` sempre que possível (ex: `HorsesRepository`, `Broker`).
- Use `request.state` para obter recursos criados por middlewares.
- Não contenha regras de negócio, lógica HTTP ou transações.

---

## `pubsub-layer-rules.md`

### Quando ler

- Ao criar/alterar **jobs assíncronos** com `Inngest`.
- Ao publicar eventos de domínio via `Broker`.
- Ao implementar processamento orientado a eventos.

### Instruções práticas

- Camada de **orquestração**: validar payload, abrir recursos, executar `UseCase`.
- Não contenha regra de negócio; delegue para o `core`.
- Jobs devem ser **idempotentes** e usar `Job.sqlalchemy_session()` para transação.
- Publique eventos via porta `Broker`, não diretamente com SDK do `Inngest`.

---

## `ai-layer-rules.md`

### Quando ler

- Ao criar/alterar **Workflows**, **Teams** ou **Toolkits** Agno em `src/animus/ai/agno/`.
- Ao implementar uma interface `*Workflow` do `core` usando LLM (Gemini, OpenAI etc.).
- Ao adicionar novo agente, nova ferramenta ou novo domínio na camada AI.
- Ao montar ou alterar o wiring de `Workflow` no `AiPipe`.

### Instruções práticas

- **Workflow** monta o `agno.Workflow` dentro do `run()`, não no construtor.
- Use `_StepNames` como `NamedTuple` para centralizar nomes de steps; evite strings mágicas.
- **Team** expõe agentes como `@property`; use `textwrap.dedent` para instruções multi-linha.
- **Toolkit** estende `agno.tools.Toolkit`; toda ferramenta exige docstring com `Args` e `Returns`.
- Toolkit pode chamar `UseCase` internamente — é o ponto de acoplamento controlado com o domínio.
- Toda instanciação de `Workflow` concreto ocorre no `AiPipe`; retorne sempre a interface do `core`.

---

## `testing-rules.md`

### Quando ler

- Ao criar/alterar testes e precisar decidir rapidamente qual padrão aplicar.
- Ao trabalhar em PR que mistura testes de `core` e `rest`.
- Ao revisar cobertura mínima esperada por tipo de teste.

### Instruções práticas

- Use como índice de decisão para direcionar a estratégia de teste.
- Aplique nomenclatura e estrutura AAA de forma consistente.
- Garanta cenários de sucesso e falha relevantes para cada unidade testada.
- Se envolver testes específicos de use case/controller, complemente com as regras especializadas correspondentes.

---

## Regra de Acionamento Rápido

| Tipo de Mudança | Documento Principal |
|---|---|
| Regra de negócio | `core-layer-rules.md` |
| Persistência/SQLAlchemy | `database-layer-rules.md` |
| Endpoint/contrato HTTP | `rest-layer-rules.md` |
| Roteamento/composição de módulos | `routers-layers-rules.md` |
| Injeção de dependência | `pipes-layer-rules.md` |
| Jobs assíncronos/eventos | `pubsub-layer-rules.md` |
| Workflows, agentes e ferramentas AI (Agno) | `ai-layer-rules.md` |
| Testes (índice geral) | `testing-rules.md` |
| Estilo/nomeação/organização | `code-conventions-rules.md` |