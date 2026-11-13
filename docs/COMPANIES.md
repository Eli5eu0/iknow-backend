# COMPANIES — Especificação do MVP

## Responsabilidade
COMPANIES gere o perfil empresarial das contas `COMPANY` (D07). A conta é criada no registo e o perfil é preenchido depois, podendo ser guardado parcialmente. O backend calcula o estado de conclusão. A verificação empresarial (D08) é só de leitura aqui.

## Regras aprovadas
- `POST /auth/register` com `role=COMPANY` cria uma linha vazia em `companies` na mesma transacção. Candidatos não têm linha.
- A migração `b7d3f1a96c25` torna `companies.name` anulável e cria a linha em falta para as contas `COMPANY` já existentes (aditiva e idempotente; não apaga dados).
- Perfil completo: `name`, `legal_name`, `tax_id`, `description`, `city` e `country` preenchidos. `website` é opcional.
- `profile_completed` e `missing_fields` são calculados em cada resposta e nunca guardados. `missing_fields` segue a ordem acima.
- Actualização parcial: só os campos enviados mudam; `{}` devolve o perfil sem alterações. Texto é aparado; em branco ou `null` nos campos obrigatórios é `422`. `website` aceita `null` para ser apagado e, se enviado, tem de começar por `http://` ou `https://`.
- Campos desconhecidos são `422`, incluindo `verification_status`, `id`, `user_id` e `profile_completed`.
- `tax_id` é único (comparação por valor exacto, depois de aparado); duplicado é `409` (`Tax ID already registered`). Reenviar o próprio `tax_id` não é conflito. O formato não é validado porque o contrato não o define.
- Perfil público: só utilizadores autenticados, só perfis completos, só contas activas; caso contrário `404` (`Company not found`). Não expõe `tax_id`, `legal_name`, `user_id` nem o estado de verificação; `is_verified` é `true` só quando o estado é `VERIFIED`.
- A empresa de `/me` é sempre a do token; não há identificador no caminho.
- `GET /companies/me/opportunities` pertence ao módulo OPPORTUNITIES (decisão aprovada).

## Endpoints
| Método | Rota | Acesso | Resultado |
|---|---|---|---|
| GET | /api/v1/companies/me | Bearer, papel COMPANY | 200 `CompanyRead`; 401; 403; 404 |
| PATCH | /api/v1/companies/me | Bearer, papel COMPANY | 200 `CompanyRead`; 401; 403; 404; 409; 422 |
| GET | /api/v1/companies/{company_id} | Bearer, qualquer papel | 200 `CompanyPublicRead`; 401; 404; 422 |

## Encaminhamento no frontend
Depois do login, para contas `COMPANY`, o frontend faz `GET /companies/me`: se `profile_completed` for `false` segue para o onboarding, caso contrário para o painel. `/auth/me` não muda.

## Pendente
- Verificação por administrador (D08): sem papel ADMIN nem endpoints; sem ela nenhuma empresa chega a `VERIFIED`.
- Bloqueio de alteração de `tax_id` e `legal_name` durante a verificação: requisito a decidir com o fluxo D08.
- Rate limiting (transversal, F11).
- Formato do `tax_id`.
