# CANDIDATES — Especificação e implementação do MVP

## Responsabilidade
CANDIDATES gere o perfil do candidato, formação académica, experiência profissional, competências e visibilidade pública. AUTH cria apenas a conta base; o perfil é criado progressivamente na primeira utilização.

## Regras
- Todos os endpoints privados exigem role CANDIDATE.
- O perfil pertence sempre ao utilizador autenticado; nenhum endpoint aceita user_id do cliente.
- PUT /me cria ou atualiza o perfil de forma idempotente; PATCH /me altera apenas os campos enviados.
- GET /me é apenas leitura e responde 404 se o perfil ainda não existir. A criação explícita e progressiva ocorre através de PUT /me (ou de uma operação de escrita de dados do perfil).
- Experiência profissional é opcional.
- Disponibilidade é texto livre até 255 caracteres e não participa no critério de matching de disponibilidade enquanto não existir um formato estruturado.
- Perfis são públicos por padrão, mas o candidato pode desativar a visibilidade.
- Perfis privados e perfis pertencentes a contas inativas respondem 404 no endpoint público.
- O perfil público não expõe email, telefone, user_id, dados de autenticação ou candidaturas.
- Competências devem existir no catálogo SKILLS. A associação é única por candidato/competência.
- Proficiência aceita BEGINNER, INTERMEDIATE, ADVANCED ou EXPERT; pode ficar NULL quando não informada.

## Endpoints
| Método | Rota | Acesso |
|---|---|---|
| GET | /api/v1/candidates/me | Candidato autenticado |
| PUT | /api/v1/candidates/me | Candidato autenticado |
| PATCH | /api/v1/candidates/me | Candidato autenticado |
| PATCH | /api/v1/candidates/me/visibility | Candidato autenticado |
| GET/POST | /api/v1/candidates/me/experiences | Candidato autenticado |
| PATCH/DELETE | /api/v1/candidates/me/experiences/{id} | Proprietário |
| GET/POST | /api/v1/candidates/me/educations | Candidato autenticado |
| PATCH/DELETE | /api/v1/candidates/me/educations/{id} | Proprietário |
| GET/POST | /api/v1/candidates/me/skills | Candidato autenticado |
| PATCH/DELETE | /api/v1/candidates/me/skills/{skill_id} | Proprietário |
| GET | /api/v1/candidates/{candidate_id} | Público |

## Matching
Este módulo não calcula scores nem interpreta disponibilidade em texto livre. O worker de matching deverá ser integrado posteriormente; a atualização do perfil não executa cálculo síncrono.

## Segurança e trabalho futuro
- A rota pública usa UUID e devolve 404 para perfis ocultos/inativos. UUID não substitui rate limiting; adicionar limitação de pedidos e monitorização antes de disponibilizar publicamente em escala.
- Contactos privados só poderão ser expostos num fluxo explícito de consentimento.
- Não existe endpoint público de listagem/pesquisa de candidatos no MVP.
