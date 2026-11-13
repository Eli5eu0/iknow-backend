# SKILLS — Especificação do MVP

## Responsabilidade
SKILLS expõe o catálogo centralizado de competências, usado por CANDIDATES e, futuramente, por OPPORTUNITIES e MATCHING.

## Regras aprovadas
- O catálogo é só de leitura através da API; não existem endpoints de criação, edição ou eliminação.
- A leitura exige utilizador autenticado e activo, com qualquer papel (CANDIDATE ou COMPANY).
- Paginação D05/D06: `page` (≥ 1, padrão 1) e `page_size` (1–100, padrão 20); resposta `{items, pagination}`.
- Ordenação apenas por `name` (`sort_by=name`), `sort_order` `asc` (padrão) ou `desc`.
- `q` pesquisa parcialmente no nome, sem distinguir maiúsculas; `%` e `_` são tratados literalmente.
- `category` filtra por igualdade exacta.
- Uma página além do fim devolve `200` com `items` vazio.

## Endpoints
| Método | Rota | Acesso | Resultado |
|---|---|---|---|
| GET | /api/v1/skills | Autenticado | 200 `{items: SkillRead[], pagination}`; 401; 422 |
| GET | /api/v1/skills/{skill_id} | Autenticado | 200 `SkillRead`; 401; 404; 422 |

## Povoamento do catálogo
`python -m app.db.seed_skills` lê `app/db/data/skills.json` e insere apenas as competências cujo slug e nome ainda não existem. Não altera nem elimina linhas existentes e pode ser executado repetidamente.

## Pendente
- Rate limiting (transversal, F11).
- Gestão administrativa do catálogo: sem endpoints definidos no contrato.
