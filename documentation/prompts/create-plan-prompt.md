# Prompt: Criar Plano

**Objetivo principal** Criar um plano de implementacao a partir de um documento de spec tecnica.

## Entrada

- Caminho do arquivo do documento de spec tecnica.

## Diretrizes de execucao

1. **Decomposicao atomica**
   - Quebre o trabalho em **fases** e **tarefas**.
   - Cada **fase** deve representar uma etapa macro do plano.
   - Cada **tarefa** deve ser uma unidade de trabalho executavel, com resultado observavel.

2. **Mapa de dependencias (obrigatorio)**
   - Inclua uma tabela com as fases, suas dependencias e o que pode rodar em paralelo.

   | Fase | Objetivo | Depende de | Pode rodar em paralelo com |
   | --- | --- | --- | --- |
   | F1 | <definir> | - | - |
   | F2 | <definir> | F1 | - |

3. **Ordem de execucao (bottom-up)**
   - Defina as tarefas seguindo rigorosamente a hierarquia de dependencias, nesta ordem:
     1. **Core**: DTOs, structures, Entidades, Interfaces e Use Cases.
     2. **Drivers/Infra**: implementacoes de Repositories, Providers e PubSub.
     3. **API layer**: Middlewares, Pipes, Schemas, Controllers e Routers.

> ⚠️ **Regra** Se uma tarefa exige outra (ex: um Controller depende de um Use Case), a tarefa dependente deve aparecer depois e referenciar explicitamente a dependencia.

> ⚠️ **Regra** Não leia desnecessariamente os arquivos especificados na `spec`, pois a spec já foi validada.

## Saida esperada

- Uma lista de fases (com objetivo).
- Uma lista de tarefas por fase, com dependencias explicitas.
- A tabela de dependencias das fases.
