# Regras da Camada AI

> 💡 Use este documento ao criar ou revisar implementacoes de `workflows`, `teams` e `toolkits` com Agno em `src/animus/ai/agno/`.

## Visao Geral

### Resumo da camada

| Aspecto | Diretriz |
|---|---|
| **Objetivo** | Concentrar implementacoes concretas de AI usando o framework Agno em `src/animus/ai/agno/`. |
| **Papel arquitetural** | Ser o adaptador de AI: implementar contratos `*Workflow` definidos no `core` usando agentes, times e ferramentas do Agno. |
| **Entrada principal** | Dados de dominio tipados (DTOs, structures) vindos de `use_cases` via `pipes`. |
| **Saida principal** | DTOs de dominio conforme o contrato `*Workflow` definido no `core`. |

### Responsabilidades principais

- Implementar interfaces `*Workflow` definidas em `core/{contexto}/interfaces/`.
- Compor `Teams` (classes com agentes como `@property`) especializados por dominio.
- Compor `Toolkits` (subclasses de `agno.tools.Toolkit`) especializados por dominio.
- Orquestrar a execucao de tarefas AI via `Workflows` que montam steps sequenciais e paralelos.

### Limites da camada

- Pode depender de `agno`, SDKs de LLM (Gemini, OpenAI etc.), `core`, `use_cases` e tipos de dominio.
- Nao deve depender de `FastAPI`, `SQLAlchemy`, `request`, `response` ou detalhes de HTTP.
- Nao deve conter regra de negocio — ela vive nos `use_cases` do `core`.
- A orquestracao de *quando* chamar o `workflow` pode ficar em um `UseCase` ou em uma borda fina (`controller`/job), mas a implementacao de *como* usar o LLM continua sendo responsabilidade do `Workflow`.

> ⚠️ Se um `workflow` esta decidindo regra de negocio de dominio, ele ultrapassou sua responsabilidade.

---

## Estrutura de Diretorios

### Mapa de pastas

```
src/animus/ai/agno/
├── teams/
│   ├── __init__.py
│   └── {dominio}_teams.py          # ex.: profiling_teams.py, intake_teams.py
├── toolkits/
│   ├── __init__.py
│   └── {dominio}_toolkit.py        # ex.: profiling_toolkit.py, intake_toolkit.py
└── workflows/
    └── {dominio}/
        ├── __init__.py
        └── agno_{nome}_workflow.py  # ex.: agno_generate_icebreaker_workflow.py
```

### Regras de organizacao e nomeacao

- `teams/` contem classes de agentes Agno, agrupadas por dominio de negocio.
- `toolkits/` contem subclasses de `agno.tools.Toolkit`, agrupadas por dominio de negocio.
- `workflows/` contem implementacoes concretas de `*Workflow`, organizadas em sub-pastas por dominio.
- Arquivos em `teams/` e `toolkits/` devem ser prefixados com o nome do dominio: `{dominio}_teams.py`, `{dominio}_toolkit.py`.
- Arquivos em `workflows/{dominio}/` devem ser prefixados com o framework: `agno_{nome}_workflow.py`.
- Classes devem seguir a convencao `Agno*Workflow`, `*Team`, `*Toolkit`.
- `__init__.py` deve expor apenas os contratos publicos do modulo.
- Nao especificar arquivos especificos, pois isso muda constantemente.

---

## Glossario arquitetural da camada

| Termo | Definicao |
|---|---|
| `Workflow` | Implementacao concreta de uma interface `*Workflow` do `core`. Monta e executa um `agno.Workflow` internamente no metodo `run()`. |
| `Team` | Classe que expoe agentes Agno como `@property`. Cada propriedade retorna um `Agent` configurado com modelo e instrucoes. |
| `Toolkit` | Subclasse de `agno.tools.Toolkit`. Registra ferramentas Python no construtor e pode chamar `use_cases` do `core`. |
| `Step` | Etapa interna do `agno.Workflow`. Pode ter `executor` (metodo Python) ou `agent` (agente Agno). |
| `Parallel` | Agrupador de `Steps` que devem executar concorrentemente dentro do `agno.Workflow`. |
| `session_state` | Dicionario de contexto compartilhado entre os `Steps` de um `agno.Workflow` durante a execucao. |
| `_StepNames` | `NamedTuple` interno ao `Workflow` que centraliza as constantes de nome de cada step, evitando strings magicas. |

---

## Padroes de Projeto

### Como os tres componentes se relacionam

```
Workflow
  ├── usa: _StepNames (constantes de nome)
  ├── usa: Team (instanciado no construtor)
  │    └── @property agent usa: Toolkit (passado via tools=[])
  ├── steps com executor (metodos Python) acessam session_state
  └── steps com agent delegam ao agente Agno
```

---

### Workflow

O `Workflow` concreto implementa a interface `*Workflow` do `core`. Ele monta um `agno.Workflow` *dentro* do metodo `run()`, definindo steps, contexto inicial (`session_state`) e orquestracao (sequencial ou paralela com `Parallel`).

**Regras:**

- Implementa exatamente o metodo definido na interface `*Workflow` do `core`.
- Recebe dependencias por injecao no construtor (ex.: `Repository`, `UseCase`).
- Instancia o `Team` no construtor; monta o `agno.Workflow` dentro de `run()`.
- Usa `_StepNames` como `NamedTuple` interno para evitar strings magicas nos nomes de steps.
- Steps com logica Python usam `executor=cast(StepExecutor, self._metodo)`.
- Steps que delegam ao LLM usam `agent=self._team.{agent_property}`.
- Passa o contexto inicial para os steps via `session_state={}`.
- Acessa `session_state` nos metodos de step via `run_context.session_state`.
- Sempre valida `run_context.session_state is None` antes de acessar valores.

**Exemplo:**

```python
from typing import NamedTuple, cast
from agno.run.base import RunContext
from agno.workflow.step import StepExecutor
from agno.workflow import Parallel, Step, StepInput, StepOutput, Workflow


class _StepNames(NamedTuple):
    GET_SENDER_HORSE: str = 'get-sender-horse'
    GET_RECIPIENT_HORSE: str = 'get-recipient-horse'
    GENERATE_ICEBREAKER: str = 'generate-icebreaker'


class AgnoGenerateIcebreakerWorkflow(GenerateIcebreakerWorkflow):
    def __init__(self, repository: HorsesRepository) -> None:
        self._repository = repository
        self._team = ProfilingTeam()
        self._step_names = _StepNames()

    def run(self, sender_id: str, recipient_id: str) -> str:
        workflow = Workflow(
            name='generate-icebreaker',
            steps=[
                Parallel(
                    Step(
                        name=self._step_names.GET_SENDER_HORSE,
                        executor=cast(StepExecutor, self._get_sender_horse_step),
                    ),
                    Step(
                        name=self._step_names.GET_RECIPIENT_HORSE,
                        executor=cast(StepExecutor, self._get_recipient_horse_step),
                    ),
                    name='fetch-horses',
                ),
                Step(
                    name=self._step_names.GENERATE_ICEBREAKER,
                    agent=self._team.icebreaker_agent,
                ),
            ],
            session_state={
                'sender_owner_id': sender_id,
                'recipient_owner_id': recipient_id,
            },
        )
        output = workflow.run(input='start')
        return str(output.content)

    def _get_sender_horse_step(
        self, _: StepInput, run_context: RunContext
    ) -> StepOutput:
        if run_context.session_state is None:
            raise AppError('Session state is required', 'Session state is required')
        owner_id = str(run_context.session_state.get('sender_owner_id'))
        toolkit = ProfilingToolkit(self._repository)
        result = toolkit.get_horse_tool(self._resolve_primary_horse_id(owner_id))
        return StepOutput(content=result)
```

---

### Team

O `Team` e uma classe simples cujos **agentes sao expostos como `@property`**. Cada propriedade retorna um `Agent` Agno configurado com modelo, instrucoes e, quando necessario, ferramentas.

**Regras:**

- Cada agente e uma `@property` que retorna uma nova instancia de `Agent` a cada acesso.
- Instrucoes devem ser declarativas e focadas no comportamento esperado do agente, nao em regra de negocio.
- Use `textwrap.dedent` para instrucoes multi-linha.
- O `Team` nao conhece `repository` nem `use_case` diretamente — esses sao responsabilidade do `Toolkit` ou do `Workflow`.

**Exemplo:**

```python
from textwrap import dedent
from agno.agent import Agent
from agno.models.google import Gemini


class ProfilingTeam:
    @property
    def icebreaker_agent(self) -> Agent:
        return Agent(
            name='Icebreaker Agent',
            description='An agent that generates icebreakers for conversations',
            instructions=dedent(
                """
                You are an expert in icebreaking conversations.
                You are given a sender and a recipient that are both horse owners.
                Generate a short, engaging icebreaker in PT-BR.
                Avoid robotic responses and use a friendly and natural tone.
                Avoid line breaks and keep the message short.
                """
            ),
            model=Gemini(id='gemini-2.5-flash'),
        )
```

---

### Toolkit

O `Toolkit` **estende `agno.tools.Toolkit`**. Registra as ferramentas no construtor via `tools=[self.metodo]` e pode receber `repository` ou `use_case` por injecao para executar operacoes de dominio.

**Regras:**

- Chama `super().__init__(name=..., tools=[self.metodo, ...])` no construtor.
- Cada ferramenta e um metodo da classe com **docstring obrigatoria** — o Agno usa a docstring para descrever a ferramenta ao LLM.
- A docstring deve ter secoes `Args` e `Returns` explicitas.
- Pode instanciar e chamar `use_cases` do `core` internamente.
- Nao deve conter logica de orquestracao de workflow nem chamadas HTTP.

**Exemplo:**

```python
from agno.tools import Toolkit
from animus.core.profiling.interfaces.repositories import HorsesRepository
from animus.core.profiling.use_cases.get_horse_use_case import GetHorseUseCase


class ProfilingToolkit(Toolkit):
    def __init__(self, repository: HorsesRepository) -> None:
        super().__init__(
            name='Profiling Toolkit',
            tools=[self.get_horse_tool],
        )
        self._repository = repository

    def get_horse_tool(self, horse_id: str) -> HorseDto:
        """
        Get a horse by its ID.
        Args:
            horse_id: The unique ID of the horse.
        Returns:
            Horse DTO.
        """
        use_case = GetHorseUseCase(self._repository)
        return use_case.execute(horse_id)
```

---

## Integracao com as demais camadas

### Como a camada AI se conecta ao resto do sistema

```
core/interfaces/*Workflow      ← define o contrato (Protocol)
ai/agno/workflows/             ← implementa o contrato
pipes/ai_pipe.py               ← instancia e injeta o Workflow via Depends(...)
rest/controllers/              ← recebe o Workflow injetado e delega
```

### Mapa de integracao

| Camada | Relacao com AI | Regra |
|---|---|---|
| `core` | Define `*Workflow` como `Protocol`; define DTOs de entrada e saida | O `core` nunca importa de `ai/agno`. |
| `pipes` | `AiPipe` instancia `Agno*Workflow` e injeta via `Depends(...)` | O `pipe` e o unico ponto de montagem do `Workflow` concreto. |
| `rest` | Controllers recebem o `Workflow` injetado e delegam | Controllers nao instanciam nada de AI diretamente. |
| `database` | Acessado pelo `repository` injetado no `Workflow` ou no `Toolkit` | `Workflow` e `Toolkit` nunca acessam banco diretamente. |

### Dependencias permitidas e proibidas

- `ai/agno` pode depender de: `core`, `agno`, SDKs de LLM, `use_cases`, tipos de dominio.
- `ai/agno` nao deve depender de: `FastAPI`, `SQLAlchemy`, `request`, `response`, `routers`, `rest`, `pipes`.

---

## Contrato do core para cada Workflow

Cada `Workflow` concreto deve ter um `Protocol` correspondente em `core/{dominio}/interfaces/`.

**Padrao de interface no core:**

```python
# core/{dominio}/interfaces/{nome}_workflow.py
class GenerateIcebreakerWorkflow(Protocol):
    def run(self, sender_id: str, recipient_id: str) -> str: ...
```

**Regras:**

- O nome da interface segue o padrao `{Acao}{Entidade}Workflow`.
- O metodo principal e sempre `run(...)`.
- A interface recebe tipos de dominio e retorna DTO ou tipo de dominio.
- Nao expoe detalhes de LLM, agentes ou framework na assinatura.

---

## Montagem via AiPipe

Toda instanciacao de `Workflow` concreto deve ocorrer no `AiPipe`, nunca diretamente em controllers ou jobs.

**Padrao no AiPipe:**

```python
# pipes/ai_pipe.py
class AiPipe:
    @staticmethod
    def get_generate_icebreaker_workflow(
        horses_repository: HorsesRepository = Depends(
            DatabasePipe.get_horses_repository_from_request
        ),
    ) -> GenerateIcebreakerWorkflow:
        return AgnoGenerateIcebreakerWorkflow(repository=horses_repository)
```

**Regras:**

- O `AiPipe` retorna sempre a interface do `core`, nunca a classe concreta.
- O `AiPipe` injeta os repositorios via `Depends(DatabasePipe.get_*_repository_from_request)`.
- Um metodo no `AiPipe` por `Workflow`.

---

## Checklist Rapido para Novos Workflows AI

- [ ] Existe interface `*Workflow` (`Protocol`) no `core/{dominio}/interfaces/` antes de implementar.
- [ ] O `Workflow` concreto esta em `src/animus/ai/agno/workflows/{dominio}/agno_{nome}_workflow.py`.
- [ ] O `Workflow` usa `_StepNames` como `NamedTuple` para centralizar nomes de steps.
- [ ] O `agno.Workflow` e montado *dentro* do `run()`, nao no construtor.
- [ ] Steps com logica Python usam `executor=cast(StepExecutor, self._metodo)`.
- [ ] Steps que delegam ao LLM usam `agent=self._team.{agent_property}`.
- [ ] O `Team` esta em `src/animus/ai/agno/teams/{dominio}_teams.py` com agentes como `@property`.
- [ ] O `Toolkit` (se necessario) esta em `src/animus/ai/agno/toolkits/{dominio}_toolkit.py` e estende `agno.tools.Toolkit`.
- [ ] Cada ferramenta do `Toolkit` tem **docstring completa** com secoes `Args` e `Returns`.
- [ ] O `AiPipe` tem um metodo dedicado que retorna a interface do `core`.
- [ ] Nenhum arquivo de `src/animus/ai/agno` importa `FastAPI`, `SQLAlchemy` ou detalhes de HTTP.

---

## ✅ O que DEVE conter

- Implementacoes concretas de interfaces `*Workflow` do `core`.
- `Teams` com agentes como `@property`, configurados com modelo, instrucoes e `textwrap.dedent`.
- `Toolkits` subclasses de `agno.tools.Toolkit` com ferramentas documentadas por docstring.
- `_StepNames` como `NamedTuple` para centralizar nomes de steps sem strings magicas.
- Injecao de `repository` ou `use_case` no construtor do `Workflow` e do `Toolkit`.
- Uso de `session_state` para compartilhar contexto entre steps paralelos.

## ❌ O que NUNCA deve conter

- Regra de negocio de dominio dentro do `Workflow`, `Team` ou `Toolkit`.
- Acesso direto a banco de dados ou `session` SQLAlchemy — use `repository` injetado.
- Imports de `FastAPI`, `request`, `response` ou mecanismos de transporte HTTP.
- Instanciacao de `Workflow` fora do `AiPipe`.
- Retorno de tipos nao definidos no `core` (ex: objetos internos do Agno expostos como contrato).
- Ferramentas do `Toolkit` sem docstring — o LLM depende delas para entender o que a ferramenta faz.
- `agno.Workflow` instanciado no construtor do `Workflow` concreto.
