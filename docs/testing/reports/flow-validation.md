# Relatório de testes — validação do fluxo Koh/Insomnia

- **Data de execução:** 2026-11-13
- **Ambiente:** backend local (`http://127.0.0.1:8000`), PostgreSQL 16 local (Docker), Koh 0.4.1, Node 24.16, Windows
- **Colecção:** `candidates.yaml` (CANDIDATES), existente
- **Objectivo:** comprovar que o fluxo de execução HTTP via Koh está operacional. Não é a validação de um módulo.

## Resumo

| Verificação | Estado | Evidência |
|---|---|---|
| Backend disponível | Aprovado | `GET /health` → 200 `{"status":"ok","database":"ok"}` |
| Cenários HTTP via Koh | Aprovado | 12 executados, 12 com o resultado esperado |
| Autenticação reutilizada sem gravar tokens | Aprovado | Token em variável da shell, passado com `--auth` |
| Colecção sem credenciais após a execução | Aprovado | `grep` de tokens, cookie e email de teste → 0 ocorrências; `koh validate` válido |
| Pytest (suite completa) | Aprovado | 39 passed (reexecutado depois das alterações desta tarefa) |

## Cenários HTTP

| Endpoint | Cenário | Resultado esperado | Resultado obtido | Estado | Observações |
|---|---|---|---|---|---|
| GET /health | Disponibilidade | 200, API e BD ok | 200 `{"status":"ok","database":"ok"}` | Aprovado | |
| GET /candidates/me | Sem token | 401 | 401 `Invalid or expired access token` | Aprovado | `--auth none` |
| GET /candidates/me | Token inválido | 401 | 401 `Invalid or expired access token` | Aprovado | |
| POST /auth/register | Conta de teste efémera | 201 com `access_token` | 201, utilizador CANDIDATE activo | Aprovado | Pedido de login com `--url` e `--body` em runtime |
| POST /auth/login | Credenciais válidas | 200 com `access_token` | 200 | Aprovado | Credenciais só em variáveis da shell |
| POST /auth/login | Sem cabeçalho Origin | 403 | 403 `Untrusted request origin` | Aprovado | Validação de Origin activa |
| GET /candidates/me | Autenticado, sem perfil | 404 | 404 `Candidate profile not found` | Aprovado | |
| PUT /candidates/me | Criar perfil | 200 com o perfil | 200, `is_public: true` | Aprovado | Corpo guardado na colecção |
| GET /candidates/me | Ler perfil criado | 200 | 200, mesmo `id` | Aprovado | |
| POST /candidates/me/educations | `end_date` anterior a `start_date` | 422 | 422 `end_date must be on or after start_date` | Aprovado | |
| DELETE /users/me | Limpeza da conta de teste | 202 | 202, remoção agendada a 30 dias | Aprovado | Pedido existente com `--method` e `--url` |
| GET /candidates/me | Token de conta desactivada | 401 | 401 | Aprovado | |

## Problemas e correcções

- A colecção tinha uma palavra-passe no corpo do login, um refresh token no cookie jar e um access token no ambiente. Substituídos por marcadores com valor vazio através do Koh.
- O Koh grava no YAML o cookie de refresh a cada login. O procedimento passa a incluir `koh cookie clear` no fim de cada execução.
- O Koh 0.4.1 escreve uma asserção do libuv no stderr ao terminar em Windows; não afecta a resposta.

## Não validado

- Execução dos 20 pedidos da colecção CANDIDATES tal como estão guardados: vários dependem de identificadores fixos no ambiente (`experience_id`, `education_id`, `skill_id`, `candidate_id`) que pertencem a outra conta.
- Fluxos com cookie e CSRF (`/auth/refresh`, `/auth/logout`): a colecção não tem esses pedidos.
- Colecção e execução via Koh para o módulo SKILLS: ainda não existem.
