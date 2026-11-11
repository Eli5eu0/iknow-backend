# iKnow Backend

Backend da plataforma **iKnow**, construído com FastAPI, PostgreSQL, SQLAlchemy 2.0 e Alembic.

## Requisitos
- Python 3.11+
- Docker Desktop (com Docker Compose) ou Docker Engine + Compose
- Git

## 1. Configurar o ambiente

```bash
cp .env.example .env
```

O ficheiro `.env` contém credenciais exclusivamente locais para desenvolvimento. Altere-as se a porta, utilizador ou password já estiverem em uso. Nunca use estes valores em produção.

## 2. Iniciar PostgreSQL

Na raiz do repositório:

```bash
docker compose up -d db
docker compose ps
```

O serviço usa PostgreSQL 16 e guarda os dados num volume Docker persistente.

## 3. Instalar dependências e executar migrações

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
alembic current
alembic check
```

As migrações criam o esquema de domínio e adicionam o hash CSRF associado às sessões de refresh.

## 4. Executar a API

```bash
uvicorn app.main:app --reload
```

- `GET /api/v1/health` — estado da API e da base de dados.
- `GET /docs` — Swagger UI.
- `GET /redoc` — ReDoc.
- `GET /openapi.json` — contrato OpenAPI.

## 5. Autenticação

Todos os endpoints de autenticação estão sob `/api/v1/auth`.

| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/register` | Registar utilizador candidato ou empresa |
| POST | `/login` | Autenticar e criar sessão |
| GET | `/csrf` | Recuperar token CSRF da sessão atual |
| POST | `/refresh` | Renovar access token e rodar refresh token |
| POST | `/logout` | Revogar a família de refresh tokens |
| GET | `/me` | Consultar o utilizador autenticado |

### Regras de segurança

- Passwords são armazenadas com Argon2id.
- Access token JWT: 15 minutos; enviado no corpo JSON e usado como Bearer token.
- Refresh token opaco: 7 dias; enviado apenas em cookie HttpOnly.
- O refresh token é armazenado na base de dados apenas como SHA-256 hash e rodado em cada renovação.
- A reutilização de um refresh token revogado revoga a família de tokens.
- O token CSRF é associado à sessão, devolvido no JSON e enviado pelo frontend no cabeçalho `X-CSRF-Token` nas operações de refresh e logout.
- O frontend deve manter access token e CSRF token apenas em memória, nunca em localStorage ou sessionStorage.
- Os endpoints que criam ou alteram sessões validam Origin/Referer contra a allowlist CORS.
- CORS usa origens explícitas e credenciais; não configurar wildcard.
- Em produção, configurar `APP_ENV=production`, `JWT_SECRET_KEY` com pelo menos 32 caracteres aleatórios e `AUTH_COOKIE_SECURE=true` por HTTPS.

Após recarregar a aplicação, o frontend pode chamar `GET /api/v1/auth/csrf` com credenciais incluídas para recuperar o token CSRF da sessão HttpOnly existente.

## 6. Testes

```bash
pytest
```

Os testes usam SQLite em memória e não exigem PostgreSQL activo.

## Estrutura

```text
app/
  api/
    deps.py
    v1/endpoints/
  core/
  db/
  models/
  schemas/
alembic/
  versions/
tests/
```

Não guardar segredos no repositório. O ficheiro `.env` é local; apenas `.env.example` deve ser versionado.
