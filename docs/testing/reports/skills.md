# Relatório de testes — SKILLS

- **Data de execução:** 2026-11-13
- **Ambiente:** backend local (`http://127.0.0.1:8000`), PostgreSQL 16 local (Docker) com 10 competências no catálogo, Koh 0.4.1, Node 24.16, Windows
- **Colecção:** `skills.yaml` (SKILLS), 24 pedidos
- **Estado do código:** cópia de trabalho sobre `e28810d`, módulo SKILLS por commitar

## Resumo

| Verificação | Estado | Evidência |
|---|---|---|
| Pytest (suite completa) | Aprovado | 39 passed (16 do módulo) |
| Cenários HTTP via Koh | Aprovado | 33 execuções, 33 com o resultado esperado |
| `alembic check` | Aprovado | Sem operações novas |
| Colecção sem credenciais após a execução | Aprovado | 0 ocorrências de tokens, cookies ou emails de teste em `skills.yaml` e `candidates.yaml`; `koh validate` válido |

Autenticação: duas contas de teste efémeras (CANDIDATE e COMPANY) registadas na execução, tokens mantidos em variáveis da shell e passados com `--auth`; ambas desactivadas no fim.

## Cenários HTTP

| Endpoint | Cenário | Resultado esperado | Resultado obtido | Estado | Observações |
|---|---|---|---|---|---|
| GET /health | Disponibilidade | 200 | 200 `{"status":"ok","database":"ok"}` | Aprovado | Colecção CANDIDATES |
| POST /auth/register | Conta de teste CANDIDATE | 201 | 201 | Aprovado | Preparação |
| POST /auth/register | Conta de teste COMPANY | 201 | 201 | Aprovado | Preparação |
| GET /skills | Valores por omissão | 200, página 1, 20 por página, ordem por nome | 200, `total_items` 10, `total_pages` 1, 10 itens por ordem alfabética | Aprovado | |
| GET /skills | `page=2&page_size=3` | 200, itens 4 a 6 | 200, `total_pages` 4, HTML e CSS, JavaScript, PostgreSQL | Aprovado | |
| GET /skills | Página além do fim (`page=99`) | 200, `items` vazio | 200, `items` vazio, `total_items` 10 | Aprovado | |
| GET /skills | `page_size=100` (máximo) | 200 | 200, 10 itens | Aprovado | |
| GET /skills | `q=SCRIPT` | 200, pesquisa parcial sem distinguir maiúsculas | 200, JavaScript e TypeScript | Aprovado | |
| GET /skills | `category=DATABASE` | 200, igualdade exacta | 200, PostgreSQL e SQL | Aprovado | |
| GET /skills | `q=type&category=PROGRAMMING` | 200, filtros combinados | 200, TypeScript | Aprovado | |
| GET /skills | `sort_order=desc` | 200, ordem inversa | 200, TypeScript ... Docker | Aprovado | |
| GET /skills | `q=cobol` (sem resultados) | 200, vazio | 200, `total_items` 0, `total_pages` 0 | Aprovado | |
| GET /skills | `q=%` (wildcard literal) | 200, vazio | 200, `total_items` 0 | Aprovado | Não devolve o catálogo inteiro |
| GET /skills | `page=0` | 422 | 422, `page` ≥ 1 | Aprovado | |
| GET /skills | `page_size=101` | 422 | 422, `page_size` ≤ 100 | Aprovado | |
| GET /skills | `sort_by=slug` | 422 | 422, só `name` | Aprovado | |
| GET /skills | `sort_order=up` | 422 | 422, só `asc` ou `desc` | Aprovado | |
| GET /skills | `q` vazio | 422 | 422, mínimo 1 carácter | Aprovado | |
| GET /skills | Sem token | 401 | 401 `Invalid or expired access token` | Aprovado | |
| GET /skills | Token inválido | 401 | 401 | Aprovado | |
| GET /skills/{skill_id} | Existente | 200 `SkillRead` | 200 `{id, name: Python, slug: python, category: PROGRAMMING}` | Aprovado | Id obtido de `GET /skills` |
| GET /skills/{skill_id} | Inexistente | 404 | 404 `Skill not found` | Aprovado | |
| GET /skills/{skill_id} | UUID inválido | 422 | 422 | Aprovado | |
| GET /skills/{skill_id} | Sem token | 401 | 401 | Aprovado | |
| POST /skills | Catálogo só de leitura | 405 | 405 `Method Not Allowed` | Aprovado | |
| GET /skills | Papel COMPANY | 200 | 200, 10 itens | Aprovado | |
| GET /skills/{skill_id} | Papel COMPANY | 200 | 200 | Aprovado | |
| PUT /candidates/me | Preparar perfil | 200 | 200 | Aprovado | Colecção CANDIDATES |
| POST /candidates/me/skills | Associar competência com id vindo de `GET /skills` | 201 | 201, `skill.name` Python | Aprovado | Integração SKILLS → CANDIDATES |
| POST /candidates/me/skills | Mesma competência outra vez | 409 | 409 `Skill already added to candidate profile` | Aprovado | |
| DELETE /users/me | Limpeza da conta CANDIDATE | 202 | 202 | Aprovado | |
| DELETE /users/me | Limpeza da conta COMPANY | 202 | 202 | Aprovado | |
| GET /skills | Token de conta desactivada | 401 | 401 | Aprovado | |

## Problemas e correcções

Nenhuma falha de implementação, contrato ou configuração. Não foi alterado código do módulo nesta fase.

## Não validado

- Catálogo vazio por HTTP real: o PostgreSQL local tem 10 competências e esvaziá-lo seria destrutivo. Coberto pelo Pytest (`test_empty_catalogue_returns_empty_page`).
- Pesquisa com `_` literal e nomes com `%` por HTTP real: o catálogo local não tem nomes com esses caracteres. Coberto pelo Pytest (`test_search_treats_wildcards_literally`).
- Token expirado (15 minutos): não se esperou pela expiração.
