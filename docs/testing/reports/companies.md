# Relatório de testes — COMPANIES

- **Data de execução:** 2026-11-13
- **Ambiente:** backend local (`http://127.0.0.1:8000`, uvicorn com recarregamento automático), PostgreSQL 16 local (Docker), Koh 0.4.1, Node 24.16, Windows
- **Colecção:** `companies.yaml` (COMPANIES, 22 pedidos)
- **Estado do código:** cópia de trabalho sobre `e75012c`; por commitar

## Resumo

| Verificação | Estado | Evidência |
|---|---|---|
| Pytest (suite completa) | Aprovado | 105 passed (75 anteriores + 30 em `tests/test_companies.py`) |
| Cenários HTTP via Koh | Aprovado | 36 execuções, 36 com o resultado esperado |
| Migração `b7d3f1a96c25` numa base temporária | Aprovado | ver abaixo |
| Migração aplicada à base local | Aprovado | 5 contas de empresa, 5 linhas criadas, `alembic current` na nova revisão |
| `alembic check` | Aprovado | Sem operações novas |
| Colecção sem credenciais | Aprovado | 0 JWT e 0 cookies; guarda anti-credenciais sem achados em `companies.yaml`, `errors.yaml` e `skills.yaml` |

Autenticação: duas contas de empresa e uma de candidato efémeras, registadas na execução; tokens, palavra-passe e `tax_id` só em variáveis da shell; as três contas foram desactivadas no fim. Cada resposta de erro foi verificada automaticamente contra o formato uniforme do ADR-014.

## Migração

Validada primeiro numa base de dados temporária (criada e removida no mesmo contentor), com dois utilizadores `COMPANY` (um activo, um inactivo) e um `CANDIDATE`:

| Passo | Resultado |
|---|---|
| `upgrade head` | 2 linhas criadas (as duas empresas), 0 para o candidato, `name` anulável, estado `NOT_SUBMITTED` |
| `downgrade -1` com empresas sem nome | Recusado com mensagem clara; nada é apagado |
| `downgrade -1` depois de preencher os nomes | `name` volta a `NOT NULL` |
| `upgrade head` outra vez | 2 linhas, sem duplicados |

Depois aplicada à base local.

## Cenários HTTP

| Endpoint | Cenário | Resultado esperado | Resultado obtido | Estado |
|---|---|---|---|---|
| POST /auth/register | Empresa A, empresa B e candidato | 201 | 201 nos três | Aprovado |
| GET /companies/me | Perfil acabado de criar | 200, `profile_completed` falso, 6 campos em falta, `NOT_SUBMITTED` | Como esperado | Aprovado |
| PATCH /companies/me | Guardar só o nome | 200, 5 campos em falta | Como esperado | Aprovado |
| GET /companies/{id} | Perfil incompleto, visto por candidato | 404 `Company not found` | Como esperado | Aprovado |
| PATCH /companies/me | `name` nulo | 422, `loc` `["body","name"]` | Como esperado | Aprovado |
| PATCH /companies/me | `city` em branco | 422, `loc` `["body","city"]` | Como esperado | Aprovado |
| PATCH /companies/me | `website` sem esquema | 422, `loc` `["body","website"]` | Como esperado | Aprovado |
| PATCH /companies/me | `verification_status` no corpo | 422 `extra_forbidden` | Como esperado | Aprovado |
| PATCH /companies/me | `user_id` no corpo | 422 `extra_forbidden` | Como esperado | Aprovado |
| GET /companies/me | Depois dos 422 | Dados inalterados | Inalterados | Aprovado |
| PATCH /companies/me | Completar o perfil | 200, completo, sem campos em falta, estado inalterado | Como esperado | Aprovado |
| GET /companies/me | Perfil completo | 200 | 200 | Aprovado |
| PATCH /companies/me | Corpo `{}` | 200, sem alterações | Como esperado | Aprovado |
| PATCH /companies/me | `website` nulo | 200, `website` nulo, continua completo | Como esperado | Aprovado |
| PATCH /companies/me | `tax_id` de outra empresa | 409 `Tax ID already registered` | Como esperado | Aprovado |
| PATCH /companies/me | `tax_id` próprio e nome | 200 | 200 | Aprovado |
| PATCH /companies/me | Reenviar o próprio `tax_id` | 200 | 200 | Aprovado |
| GET /companies/{id} | Candidato vê perfil completo | 200 com exactamente 7 campos, sem `tax_id`, `is_verified` falso | Como esperado | Aprovado |
| GET /companies/{id} | Outra empresa vê perfil completo | 200 | 200 | Aprovado |
| GET /companies/{id} | Empresa B incompleta | 404 | 404 | Aprovado |
| GET /companies/{id} | Inexistente | 404 | 404 | Aprovado |
| GET /companies/{id} | UUID inválido | 422, `loc` `["path","company_id"]` | Como esperado | Aprovado |
| GET /companies/{id} | Sem token | 401 | 401 | Aprovado |
| GET /companies/me | Candidato | 403 `Insufficient permissions` | Como esperado | Aprovado |
| PATCH /companies/me | Candidato | 403 | 403 | Aprovado |
| GET e PATCH /companies/me | Sem token | 401 | 401 e 401 | Aprovado |
| GET /companies/me | Token inválido | 401 | 401 | Aprovado |
| DELETE /users/me | Desactivar o dono | 202 | 202 | Aprovado |
| GET /companies/{id} | Dono desactivado | 404 | 404 | Aprovado |
| GET /companies/me | Conta desactivada | 401 | 401 | Aprovado |
| DELETE /users/me | Limpeza das outras duas contas | 202 | 202 e 202 | Aprovado |

## Problemas e correcções

- Nenhuma falha de implementação, contrato ou configuração nos testes HTTP.
- Um teste meu aceitava 404 ou 422 para `GET /companies/me/opportunities`; apertei-o para 404, que é o comportamento definido (o endpoint pertence ao módulo OPPORTUNITIES).
- O servidor local recarregou o código novo antes de eu aplicar a migração à base local; durante esse intervalo curto, registar uma conta de empresa teria falhado (nome obrigatório na base de dados). A migração foi aplicada logo a seguir à validação na base temporária.
- Em `companies.yaml`, o valor `example.com` aparece em dois sítios de propósito: o `website` válido (`https://example.com`) e o inválido (`example.com`, sem esquema) usado para provocar o 422. Não são credenciais.

## Não validado

- **Perfil público de empresa `VERIFIED` por HTTP real:** sem papel de administrador não há forma de uma empresa chegar a `VERIFIED`; coberto só pelo Pytest, que altera o estado directamente na base de dados.
- **Conflito simultâneo de `tax_id`:** coberto só pelo Pytest, que força o caminho em que a pré-verificação falha e a base de dados rejeita.
- **Frontend real** (onboarding e encaminhamento pós-login): não executado; falta `npm run gen:api`.
- **Migração com um grande volume de contas:** testada apenas com poucas linhas.
