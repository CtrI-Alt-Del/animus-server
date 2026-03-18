# Regras de Convenções de Código

Este documento define as ferramentas e práticas obrigatórias para garantir consistência no ambiente de desenvolvimento e na base de código.

## Tooling Geral

O projeto adota um conjunto estrito de ferramentas para garantir reprodutibilidade e qualidade. O uso dessas ferramentas é mandatório.

### Gerenciamento de Dependências e Ambiente
- **Ferramenta:** `uv`
- **Regra:** Não use `pip` ou `virtualenv` diretamente. Use `uv` para gerenciar o ambiente virtual e dependências.
- **Lockfile:** O arquivo `uv.lock` deve ser sempre commitado e mantido atualizado.
- **Comandos:**
  - Instalar: `uv sync --group dev`
  - Adicionar lib: `uv add <lib>` (ou `uv add --dev <lib>`)
  - Executar: `uv run <comando>`

### Scripts e Automação
- **Ferramenta:** `poethepoet` (task runner)
- **Regra:** Todas as tarefas recorrentes (testes, lint, migrations) devem ser encapsuladas como tasks no `pyproject.toml`.
- **Uso:** Execute via `poe <task>`.
- **Proibição:** Evite criar scripts shell (`.sh`) soltos na raiz se a tarefa puder ser definida como uma task do Poe.

### Qualidade de Código (Linting e Formatação)
- **Ferramenta:** `ruff`
- **Regra:** O código deve estar formatado e lintado de acordo com as regras do `ruff` configuradas em `pyproject.toml`.
- **CI/CD:** O pipeline falhará se `ruff check` ou `ruff format --check` reportarem erros.
- **Task:** Use `poe codecheck` para aplicar correções automáticas e verificar a formatação.

### Checagem Estática de Tipos
- **Ferramenta:** `pyright`
- **Regra:** Todo código novo deve passar na checagem estática de tipos.
- **Tipagem:** Utilize type hints explícitos. Evite `Any` a menos que estritamente necessário.
- **Task:** Use `poe typecheck`.

## Organização de Imports

A ordem das importações deve respeitar a seguinte hierarquia, com cada grupo separado por uma linha em branco:

1. **Standard Library:** Pacotes nativos do Python (ex: `os`, `sys`, `datetime`).
2. **Third Party:** Bibliotecas de terceiros (ex: `fastapi`, `sqlalchemy`, `pydantic`).
3. **First Party:** Módulos do projeto (ex: `animus.core`, `animus.rest`).

**Exemplo:**
```python
import os
from datetime import datetime

from fastapi import APIRouter

from animus.core.domain import Horse
```

### Observação sobre Tooling Específico
Ferramentas específicas de domínio (como `alembic` para banco de dados ou `pytest` para testes) estão detalhadas nos seus respectivos arquivos de regras:
- `documentation/rules/database-layer-rules.md`
- `documentation/rules/testing-rules.md`
- `documentation/rules/rest-layer-rules.md`
