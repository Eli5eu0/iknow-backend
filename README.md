# iKnow Backend

Backend inicial da plataforma **iKnow**, construído com FastAPI, PostgreSQL, SQLAlchemy 2.0 e Alembic.

## Requisitos
- Python 3.11+
- PostgreSQL 15+
- Git

## Configuração local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edite `.env` e configure a ligação PostgreSQL. Depois execute:
```bash
alembic upgrade head
uvicorn app.main:app --reload
```

## Endpoints
- `GET /api/v1/health` — estado da API e ligação à base de dados.
- `GET /docs` — Swagger UI.
- `GET /redoc` — ReDoc.
- `GET /openapi.json` — contrato OpenAPI.

## Testes
```bash
pytest
```
Os testes usam SQLite em memória e não exigem PostgreSQL.

## Estrutura
```text
app/
  api/v1/endpoints/
  core/
  db/
tests/
alembic/
```

Esta é apenas a fundação técnica. Autenticação, perfis, empresas, oportunidades, candidaturas e correspondência serão implementados em etapas próprias, de acordo com as decisões de arquitectura aprovadas.

Não guardar segredos no repositório. O ficheiro `.env` é local; apenas `.env.example` deve ser versionado.
