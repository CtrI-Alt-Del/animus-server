# Tooling do Projeto

Este documento centraliza os comandos usados para validação local do projeto Animus Server.

## Pre-requisito

Antes de executar qualquer validação, instale as dependencias do projeto:

```bash
uv sync
```

## Execução da aplicação

Para executar a aplicação em modo de desenvolvimento:

```bash
uv run poe dev
```

## Typecheck

Para executar a checagem estatica de tipos com BasedPyright:

```bash
uv run poe typecheck
```

## Codecheck

Para garantir padrao de formatação e validação estatica, execute:

```bash
uv run poe codecheck
```

## Testes

Para executar a suite de testes automatizados do projeto:

```bash
uv run poe test
```
