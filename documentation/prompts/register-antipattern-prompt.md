---
description: Registra um anti-padrão cometido durante a implementação no doc de rules da camada correspondente, para evitar reincidência nas próximas sessões.
---

# Prompt: Registrar Anti-padrão

**Objetivo:** Documentar um erro de implementação cometido pela IA no arquivo
de regras da camada correspondente, de forma clara e acionável — para que o
mesmo anti-padrão não se repita em sessões futuras.

---

## Entrada

- **Descrição do anti-padrão:** o que foi feito de errado e em qual contexto
  (texto livre, trecho de código, descrição do comportamento incorreto).
- **Camada afetada** (opcional): se já souber, informe a camada
  (`core`, `database`, `rest`, `routers`, `pipes`, `pubsub`, `testing`,
  `code-conventions`). Se não souber, o prompt identifica automaticamente.

---

## Diretrizes de Execução

### 1. Identificar o doc de rules correto

Leia `documentation/rules/rules.md` e, com base na descrição do anti-padrão,
identifique o arquivo de regras da camada afetada:

| Camada | Arquivo |
|---|---|
| Regra de negócio / domínio | `core-layer-rules.md` |
| Persistência / SQLAlchemy | `database-layer-rules.md` |
| Endpoint / contrato HTTP | `rest-layer-rules.md` |
| Roteamento / composição | `routers-layers-rules.md` |
| Injeção de dependência | `pipes-layer-rules.md` |
| Jobs assíncronos / eventos | `pubsub-layer-rules.md` |
| Testes | `testing-rules.md` |
| Estilo / nomeação / organização | `code-conventions-rules.md` |

Se o anti-padrão cruzar mais de uma camada, registre em todos os docs
relevantes.

### 2. Formatar a entrada do anti-padrão

Estruture o registro no seguinte formato antes de inserir no doc de rules:

```markdown
### ❌ Anti-padrão: <Título curto e descritivo>

**O que foi feito:**
<Descrição objetiva do erro cometido, com trecho de código se disponível.>

**Por que está errado:**
<Explicação do impacto arquitetural, violação de princípio ou risco gerado.>

**O que deve ser feito:**
<Descrição da abordagem correta, com trecho de código se possível.>
```

### 3. Inserir no doc de rules

Abra o arquivo de rules identificado no passo 1 e insira o registro:

- Localize a seção `## ❌ O que NUNCA deve conter` do doc. Essa seção existe
  em todos os docs de rules — nunca precisará ser criada.
- Acrescente o novo anti-padrão ao final da seção, sem remover entradas
  existentes.
- Mantenha o estilo e a linguagem do documento original.

### 4. Confirmar

Após inserir, exiba o trecho adicionado e confirme o caminho do arquivo
atualizado.

---

## Saída Esperada

- Doc de rules da camada atualizado com o novo anti-padrão registrado na seção
  `## ❌ O que NUNCA deve conter`.
- Exibição do trecho inserido para confirmação visual.

---

## Restrições

- **Não remova nem reescreva** entradas existentes no doc de rules.
- **Não generalize** o anti-padrão além do que foi descrito — registre exatamente
  o erro cometido, sem inferir problemas não observados.
- Se faltar contexto suficiente para identificar a camada ou descrever o
  "O que deve ser feito", use a tool `question` antes de escrever.---
description: Registra um anti-padrão cometido durante a implementação no doc de rules da camada correspondente, para evitar reincidência nas próximas sessões.
---

# Prompt: Registrar Anti-padrão

**Objetivo:** Documentar um erro de implementação cometido pela IA no arquivo
de regras da camada correspondente, de forma clara e acionável — para que o
mesmo anti-padrão não se repita em sessões futuras.

---

## Entrada

- **Descrição do anti-padrão:** o que foi feito de errado e em qual contexto
  (texto livre, trecho de código, descrição do comportamento incorreto).
- **Camada afetada** (opcional): se já souber, informe a camada
  (`core`, `database`, `rest`, `routers`, `pipes`, `pubsub`, `testing`,
  `code-conventions`). Se não souber, o prompt identifica automaticamente.

---

## Diretrizes de Execução

### 1. Identificar o doc de rules correto

Leia `documentation/rules/rules.md` e, com base na descrição do anti-padrão,
identifique o arquivo de regras da camada afetada:

| Camada | Arquivo |
|---|---|
| Regra de negócio / domínio | `core-layer-rules.md` |
| Persistência / SQLAlchemy | `database-layer-rules.md` |
| Endpoint / contrato HTTP | `rest-layer-rules.md` |
| Roteamento / composição | `routers-layers-rules.md` |
| Injeção de dependência | `pipes-layer-rules.md` |
| Jobs assíncronos / eventos | `pubsub-layer-rules.md` |
| Testes | `testing-rules.md` |
| Estilo / nomeação / organização | `code-conventions-rules.md` |

Se o anti-padrão cruzar mais de uma camada, registre em todos os docs
relevantes.

### 2. Formatar a entrada do anti-padrão

Estruture o registro no seguinte formato antes de inserir no doc de rules:

```markdown
### ❌ Anti-padrão: <Título curto e descritivo>

**O que foi feito:**
<Descrição objetiva do erro cometido, com trecho de código se disponível.>

**Por que está errado:**
<Explicação do impacto arquitetural, violação de princípio ou risco gerado.>

**O que deve ser feito:**
<Descrição da abordagem correta, com trecho de código se possível.>
```

### 3. Inserir no doc de rules

Abra o arquivo de rules identificado no passo 1 e insira o registro:

- Localize a seção `## ❌ O que NUNCA deve conter` do doc. Essa seção existe
  em todos os docs de rules — nunca precisará ser criada.
- Acrescente o novo anti-padrão ao final da seção, sem remover entradas
  existentes.
- Mantenha o estilo e a linguagem do documento original.

### 4. Confirmar

Após inserir, exiba o trecho adicionado e confirme o caminho do arquivo
atualizado.

---

## Saída Esperada

- Doc de rules da camada atualizado com o novo anti-padrão registrado na seção
  `## ❌ O que NUNCA deve conter`.
- Exibição do trecho inserido para confirmação visual.

---

## Restrições

- **Não remova nem reescreva** entradas existentes no doc de rules.
- **Não generalize** o anti-padrão além do que foi descrito — registre exatamente
  o erro cometido, sem inferir problemas não observados.
- Se faltar contexto suficiente para identificar a camada ou descrever o
  "O que deve ser feito", use a tool `question` antes de escrever.