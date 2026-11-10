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

O serviço usa PostgreSQL 16, expõe a porta 5432 e guarda os dados num volume Docker persistente. O Docker Compose lê as variáveis definidas no ficheiro `.env`.

Para acompanhar a inicialização:

```bash
docker compose logs -f db
```

Depois configure o backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No Windows PowerShell, active o ambiente com `.venv\\Scripts\\Activate.ps1`.

## 3. Executar a API

```bash
uvicorn app.main:app --reload
```

Endpoints:
- `GET /api/v1/health` — verifica a ligação à base de dados.
- `GET /docs` — Swagger UI.
- `GET /redoc` — ReDoc.
- `GET /openapi.json` — contrato OpenAPI.

A verificação de saúde deve responder com `{"status":"ok","database":"ok"}` quando a API consegue executar uma consulta à base de dados.

## 4. Testes

```bash
pytest
```

Os testes usam SQLite em memória e não exigem que o PostgreSQL esteja activo.

## Parar a base de dados

```bash
docker compose down
```

Para apagar também os dados persistidos (operação irreversível):

```bash
docker compose down -v
```

## Estrutura

```text
app/
  api/v1/endpoints/
  core/
  db/
alembic/
  versions/
tests/
docker-compose.yml
```

Esta etapa prepara o PostgreSQL local e a ligação da aplicação. A criação dos modelos de domínio e da primeira migração será a etapa seguinte. Autenticação, perfis, empresas, oportunidades, candidaturas e correspondência serão implementados progressivamente, seguindo as decisões de arquitectura aprovadas.

Não guardar segredos no repositório. O ficheiro `.env` é local; apenas `.env.example` deve ser versionado.
