# Tooling do Projeto

Este documento centraliza os comandos usados para validacao local do projeto Animus Server.

## Pre-requisito

Antes de executar qualquer validacao, instale as dependencias do projeto:

```bash
uv sync
```

## Execucao da aplicacao

Para executar a aplicacao em modo de desenvolvimento:

```bash
uv run poe dev
```

## Typecheck

Para executar a checagem estatica de tipos com BasedPyright:

```bash
uv run poe typecheck
```

## Codecheck

Para garantir padrao de formatacao e validacao estatica, execute:

```bash
uv run poe codecheck
```

## Testes

Para executar a suite de testes automatizados do projeto:

```bash
uv run poe test
```
