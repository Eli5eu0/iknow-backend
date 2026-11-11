# USERS — Especificação do MVP

## Responsabilidade
USERS gere a conta base (users). AUTH autentica e emite sessões; CANDIDATES e COMPANIES gerem os respetivos dados de perfil.

## Regras aprovadas
- Email e role são imutáveis através de USERS.
- Dados pessoais específicos pertencem aos módulos CANDIDATES e COMPANIES.
- A palavra-passe pode ser alterada mediante confirmação da palavra-passe atual.
- A desativação é imediata e revoga todas as sessões de refresh.
- A conta pode ser recuperada durante 30 dias mediante email e palavra-passe.
- Após o prazo, a conta fica elegível para eliminação ou anonimização por um worker; esta migração não executa eliminação física.

## Endpoints
| Método | Rota | Acesso | Resultado |
|---|---|---|---|
| GET | /api/v1/users/me | Bearer | Dados da própria conta |
| PATCH | /api/v1/users/me/password | Bearer | Altera palavra-passe e revoga refresh sessions |
| DELETE | /api/v1/users/me | Bearer | Desativa e agenda remoção para +30 dias |
| POST | /api/v1/users/recover | Credenciais | Recupera conta dentro do prazo |

## Modelo
users.deletion_requested_at regista quando a desativação foi pedida.
users.deletion_scheduled_at regista o limite de recuperação e permite ao futuro worker localizar contas expiradas.

## Limitações e trabalho futuro
- O endpoint de recuperação baseado em email/palavra-passe precisa de rate limiting e monitorização de tentativas antes de exposição pública.
- O envio de aviso de desativação e recuperação depende do módulo NOTIFICATIONS.
- O processamento após 30 dias depende do módulo WORKERS e de uma política de retenção/anonimização aprovada.
- A eliminação/anonimização deve preservar integridade referencial e obrigações legais; não é executada por este módulo.
- Não existe endpoint genérico para editar email, role, dados de candidato ou empresa.
