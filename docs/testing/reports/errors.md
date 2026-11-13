# Relatório de testes — ERRORS (ADR-014, formato uniforme de erro)

- **Data de execução:** 2026-11-13
- **Ambiente:** backend local (`http://127.0.0.1:8000`, uvicorn com recarregamento automático), PostgreSQL 16 local (Docker), Koh 0.4.1, Node 24.16, Windows
- **Colecção:** `errors.yaml` (ERRORS, 13 pedidos). Reexecutados também `skills.yaml` e `candidates.yaml`.
- **Estado do código:** cópia de trabalho sobre `e75012c`; ADR-014 por commitar

## Resumo

| Verificação | Estado | Evidência |
|---|---|---|
| Pytest (suite completa) | Aprovado | 59 passed (39 anteriores + 20 em `tests/test_errors.py`) |
| Cenários HTTP via Koh | Aprovado | 60 execuções, 60 com o resultado esperado (ERRORS 17, SKILLS 32, CANDIDATES 11) |
| `alembic check` | Aprovado | Sem operações novas (sem alterações de base de dados) |
| Geração de tipos do frontend a partir do novo OpenAPI | Aprovado | `openapi-typescript` gerou `ErrorResponse`, `ErrorBody` e `ValidationIssue`; `HTTPValidationError` já não existe. Gerado só para ficheiro temporário; o frontend não foi alterado |
| Testes unitários do frontend sobre o formato de erro | Aprovado | 23 passed em `src/shared/api` e `src/shared/utils`; executados sem alterações ao frontend |
| Colecções sem credenciais após a execução | Aprovado | 0 ocorrências de tokens, cookies e emails de teste em `candidates.yaml`, `skills.yaml` e `errors.yaml`; `koh validate` válido |

Cada resposta de erro foi verificada automaticamente: um único campo `error` com exactamente `code`, `message`, `details` e `request_id`; `code` esperado; `request_id` igual ao cabeçalho `X-Request-ID`; ausência de `input` e `ctx`; `WWW-Authenticate: Bearer` nos 401. Todas as respostas de sucesso trazem `X-Request-ID` e nenhuma contém `error`.

## Cenários HTTP novos (ERRORS)

| Endpoint | Cenário | Resultado esperado | Resultado obtido | Estado | Observações |
|---|---|---|---|---|---|
| GET /does-not-exist | Rota inexistente | 404 `NOT_FOUND` | 404 `NOT_FOUND` `Not Found` | Aprovado | Erro do framework já no formato uniforme |
| POST /health | Método não permitido | 405 `METHOD_NOT_ALLOWED` | 405 | Aprovado | |
| GET /skills | Sem token | 401 `UNAUTHORIZED`, `WWW-Authenticate: Bearer` | 401, cabeçalho presente | Aprovado | |
| POST /auth/login | Sem cabeçalho Origin | 403 `FORBIDDEN` | 403 `Untrusted request origin` | Aprovado | |
| GET /candidates/me | Token de empresa | 403 `FORBIDDEN` | 403 `Insufficient permissions` | Aprovado | Papel errado |
| GET /skills/{id} | Competência inexistente | 404 `NOT_FOUND` | 404 `Skill not found` | Aprovado | |
| POST /auth/register | Email duplicado | 409 `CONFLICT` | 409 `Email already registered` | Aprovado | |
| POST /auth/register | Palavra-passe curta | 422 `VALIDATION_ERROR`, `details` com `loc` `["body","password"]` | 422, `details` só com `type`, `loc`, `msg` | Aprovado | O valor enviado não aparece na resposta |
| GET /skills | `page=0` | 422, `loc` `["query","page"]` | 422 | Aprovado | |
| GET /skills/not-a-uuid | UUID inválido | 422, `loc` `["path","skill_id"]` | 422 | Aprovado | |
| PATCH /users/me/password | Palavra-passe actual errada | 400 `BAD_REQUEST` | 400 `Current password is incorrect` | Aprovado | |
| GET /skills | Token de conta desactivada | 401 `UNAUTHORIZED` | 401 | Aprovado | |
| DELETE /users/me | Limpeza das duas contas de teste | 202 | 202 e 202 | Aprovado | |

## Reexecução dos módulos existentes com o novo formato

| Colecção | Execuções | Resultado |
|---|---|---|
| SKILLS | 32 (listagens, paginação, filtros, 422, 401, detalhe, 405, papel COMPANY, integração com candidatos, limpeza) | 32 aprovadas |
| CANDIDATES | 11 (401, registo, login, 403 sem Origin, 404 sem perfil, PUT/GET perfil, 422 em datas, limpeza, 401 após desactivar) | 11 aprovadas |
| ERRORS | 17 | 17 aprovadas |

## Problemas e correcções

- Um teste meu (`test_forbidden_for_wrong_role`) aceitava 403 ou 422 e só verificava o formato num dos casos. Reescrevi-o com um caso de 403 real (empresa em `GET /candidates/me`) antes de o dar como válido. Outro teste verificava o valor enviado com uma comparação frágil e foi substituído por uma verificação directa.
- O teste de `test_skills.py` que comparava o corpo antigo `{"detail": ...}` foi actualizado para o novo formato. É a mudança de contrato aprovada, não uma expectativa ajustada para um erro.
- O primeiro comando de criação da colecção ERRORS falhou por um erro meu (ficheiro com nome em minúsculas e falta de `--workspace`): os pedidos não foram criados. Confirmei que nenhuma outra colecção foi alterada (chaves dos ambientes de CANDIDATES e SKILLS inalteradas) e repeti o procedimento. Regra acrescentada a `docs/testing/README.md`.
- O meu verificador imprimiu os primeiros 120 caracteres das respostas de registo e login, que incluem o início do JWT (cabeçalho e parte do conteúdo, sem a assinatura). Eram contas de teste efémeras, já desactivadas. A saída foi apagada e o verificador corrigido para ocultar `access_token` e `csrf_token`.

## Não validado

- **Erro 500 por HTTP real:** não há forma segura de o provocar no backend local. Coberto só pelo Pytest, que confirma estrutura, ausência de fuga de informação, `request_id` nos logs e cabeçalhos CORS.
- **Erro 429:** o rate limiting não existe; o código está reservado e testado só ao nível do handler.
- **Frontend real contra o novo formato:** não foi executado. O frontend aceita os dois formatos e os seus testes unitários do formato do contrato foram executados, mas nenhum usa respostas reais do backend. Falta correr `npm run gen:api` e uma verificação no browser.
- **Códigos 410 e 503 por HTTP real:** cobertos só pelo Pytest.
