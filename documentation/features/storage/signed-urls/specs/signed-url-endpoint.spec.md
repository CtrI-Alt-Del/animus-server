---
title: Endpoint para Geração de Signed URL
prd: documentation/features/storage/signed-urls/prd.md
ticket: https://joaogoliveiragarcia.atlassian.net/browse/ANI-44
status: open
last_updated_at: 2026-03-31
---

# 1. Objetivo

Implementar um endpoint `POST /storage/analyses/{analysis_id}/petitions/upload` que retorna uma Signed URL para upload de arquivos no Google Cloud Storage. O objetivo funcional é permitir o upload seguro de petições diretamente pelo cliente, mantendo o controle de acesso granular.

---

# 2. Escopo

## 2.1 In-scope

- Desenvolvimento do endpoint HTTP.
- Geração de Signed URL usando Google Cloud Storage.
- Verificação de permissões para associar a URL à análise correta.
- Suporte para arquivos PDF e DOCX.

## 2.2 Out-of-scope

- Persistência de metadados do arquivo no banco de dados (será realizada após o upload).
- Implementação de outro tipo de storage provider além do Google Cloud Storage.
- Funcionalidades de processamento de arquivos após o upload.

---

# 3. Requisitos

## 3.1 Funcionais

- O endpoint deve receber:
  - `analysis_id` (path param): ID da análise associada ao arquivo.
  - `filename` (body param): Nome do arquivo sendo enviado.

- Validar permissões do usuário:
  - Usuário deve ser o criador da análise ou ter permissão explícita.

- O retorno deve incluir:
  - A Signed URL com validade configurável (default: 15 min).
  - Headers obrigatórios a serem usados no upload.

## 3.2 Não funcionais

- **Segurança:**
  - O link deve expirar automaticamente após o período configurado.
  - Apenas operações PUT para o arquivo especificado.

- **Performance:**
  - Tempo máximo de resposta: 300 ms sob carga típica.

- **Observabilidade:**
  - Registrar tentativa de geração de Signed URL para auditoria.

---

# 4. O que já existe?

## Core

- **`SignedUrlProvider`** (`src/animus/providers/storage/signed_url_provider.py`) — *Interface para geração de Signed URLs em storage providers.*

## Database

- **`AnalysisModel`** (`src/animus/database/models/analysis_model.py`) — *Tabela de análises, associada aos arquivos.*

---

# 5. O que deve ser criado?

## Camada Providers

- **Localização:** `src/animus/providers/storage/google_signed_url_provider.py` (**novo arquivo**)
- **Interface implementada:** `SignedUrlProvider`
- **Biblioteca utilizada:** `google-cloud-storage`
- **Métodos:**
  - `generate_upload_url(bucket: str, object_name: str, expiration: int) -> str`
    - Gera uma Signed URL válida para operações PUT em um objeto do bucket.

## Camada REST

- **Localização:** `src/animus/rest/controllers/storage_controller.py` (**novo arquivo**)
- **Métodos:**
  - `create_signed_url(analysis_id: str, filename: str) -> SignedUrlResponse`
    - Valida permissões e delega geração de Signed URL ao Provider.

## Camada Validation

- **Localização:** `src/animus/validation/storage/`
- **Tipo:** `SignedUrlResponse`
- **Atributos:**
    - `url: str`
    - `headers: dict`

---

# 6. O que deve ser modificado?

## Routers

- **Arquivo:** `src/animus/routers/storage_router.py`
- **Mudança:** Registrar o novo controller `StorageController` no router de storage.

---

# 7. O que deve ser removido?

**Não aplicável**.

---

# 8. Decisões Técnicas e Trade-offs

- **Decisão:** Utilizar `google-cloud-storage` como SDK para geração das Signed URLs.
  - **Alternativas consideradas:** boto3 (AWS), implementação customizada.
  - **Motivo da escolha:** Simplifica integração, apropriado aos requisitos do projeto.

- **Decisão:** Gerar links com validade padrão de 15 minutos.
  - **Alternativas consideradas:** 5min, 60min.
  - **Motivo da escolha:** Equilíbrio entre segurança e usabilidade.

---

# 9. Diagramas e Referências

- **Fluxo de dados:**

```plaintext
Client → HTTP POST /storage/analyses/{analysis_id}/petitions/upload
    → Controller → Provider → Google Cloud Storage
    → Response: Signed URL + Headers
```

- **Arquivo de referência:** `src/animus/rest/controllers/auth_controller.py` — *Exemplo de validações e resposta padrão.*

---

# 10. Pendências / Dúvidas

- **Descrição:** Validade configurável da URL deve ser exponenciada para mais casos de uso?
  - **Impacto:** Pode gerar necessidade de contratos dinâmicos no Provider.
  - **Ação sugerida:** Validar com time de produto antes de encerrar SPEC.

