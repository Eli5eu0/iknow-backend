"""Povoa o catálogo de competências de forma idempotente.

Uso: python -m app.db.seed_skills

Insere apenas as competências cujo slug e nome ainda não existem. Nunca altera
nem elimina linhas existentes.
"""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.skill import Skill

DATA_FILE = Path(__file__).parent / "data" / "skills.json"


def seed_skills(db: Session, entries: list[dict] | None = None) -> int:
    if entries is None:
        entries = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    existing_slugs = set(db.scalars(select(Skill.slug)))
    existing_names = set(db.scalars(select(Skill.name)))
    inserted = 0
    for entry in entries:
        if entry["slug"] in existing_slugs or entry["name"] in existing_names:
            continue
        db.add(Skill(name=entry["name"], slug=entry["slug"], category=entry.get("category")))
        existing_slugs.add(entry["slug"])
        existing_names.add(entry["name"])
        inserted += 1
    db.commit()
    return inserted


def main() -> None:
    import app.models  # noqa: F401 - regista todas as tabelas ORM
    from app.db.session import get_session_factory

    with get_session_factory()() as db:
        inserted = seed_skills(db)
    print(f"Competências inseridas: {inserted}")


if __name__ == "__main__":
    main()
