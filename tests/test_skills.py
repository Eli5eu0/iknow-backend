from uuid import UUID, uuid4

from app.db.seed_skills import seed_skills
from app.db.session import get_db
from app.models.skill import Skill

ORIGIN = "http://localhost:5173"
PASSWORD = "a-long-test-password-123"
URL = "/api/v1/skills"


def _register(client, email="candidate@example.com", role="CANDIDATE"):
    response = client.post(
        "/api/v1/auth/register",
        headers={"Origin": ORIGIN},
        json={"email": email, "password": PASSWORD, "role": role},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _db(client):
    return next(client.app.dependency_overrides[get_db]())


def _add_skills(client, entries):
    db = _db(client)
    try:
        skills = [Skill(name=name, slug=slug, category=category) for name, slug, category in entries]
        db.add_all(skills)
        db.commit()
        return {skill.slug: str(skill.id) for skill in skills}
    finally:
        db.close()


CATALOGUE = [
    ("Python", "python", "PROGRAMMING"),
    ("TypeScript", "typescript", "PROGRAMMING"),
    ("PostgreSQL", "postgresql", "DATABASE"),
    ("Docker", "docker", "DEVOPS"),
    ("Git", "git", None),
]


def test_skills_require_authentication(client):
    assert client.get(URL).status_code == 401
    assert client.get(f"{URL}/{uuid4()}").status_code == 401
    assert client.get(URL, headers={"Authorization": "Bearer not-a-token"}).status_code == 401


def test_both_roles_can_read_the_catalogue(client):
    ids = _add_skills(client, CATALOGUE)
    for email, role in (("c@example.com", "CANDIDATE"), ("e@example.com", "COMPANY")):
        headers = _register(client, email=email, role=role)
        assert client.get(URL, headers=headers).status_code == 200
        assert client.get(f"{URL}/{ids['python']}", headers=headers).status_code == 200


def test_deactivated_account_cannot_read_the_catalogue(client):
    headers = _register(client)
    assert client.delete("/api/v1/users/me", headers=headers).status_code == 202
    assert client.get(URL, headers=headers).status_code == 401


def test_empty_catalogue_returns_empty_page(client):
    response = client.get(URL, headers=_register(client))
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "pagination": {"page": 1, "page_size": 20, "total_items": 0, "total_pages": 0},
    }


def test_list_defaults_and_item_shape(client):
    _add_skills(client, CATALOGUE)
    body = client.get(URL, headers=_register(client)).json()
    assert body["pagination"] == {"page": 1, "page_size": 20, "total_items": 5, "total_pages": 1}
    assert [item["name"] for item in body["items"]] == [
        "Docker", "Git", "PostgreSQL", "Python", "TypeScript",
    ]
    assert set(body["items"][0]) == {"id", "name", "slug", "category"}
    assert body["items"][1]["category"] is None


def test_pagination_walks_all_pages(client):
    _add_skills(client, CATALOGUE)
    headers = _register(client)

    first = client.get(URL, headers=headers, params={"page": 1, "page_size": 2}).json()
    assert first["pagination"] == {"page": 1, "page_size": 2, "total_items": 5, "total_pages": 3}
    assert [item["name"] for item in first["items"]] == ["Docker", "Git"]

    last = client.get(URL, headers=headers, params={"page": 3, "page_size": 2}).json()
    assert [item["name"] for item in last["items"]] == ["TypeScript"]

    beyond = client.get(URL, headers=headers, params={"page": 4, "page_size": 2})
    assert beyond.status_code == 200
    assert beyond.json()["items"] == []
    assert beyond.json()["pagination"]["total_items"] == 5


def test_max_page_size_is_accepted(client):
    assert client.get(URL, headers=_register(client), params={"page_size": 100}).status_code == 200


def test_invalid_query_parameters_return_422(client):
    headers = _register(client)
    for params in (
        {"page": 0},
        {"page": -1},
        {"page": "abc"},
        {"page_size": 0},
        {"page_size": 101},
        {"sort_by": "slug"},
        {"sort_by": "id"},
        {"sort_order": "up"},
        {"q": ""},
        {"q": "x" * 101},
        {"category": ""},
        {"category": "x" * 81},
    ):
        assert client.get(URL, headers=headers, params=params).status_code == 422, params


def test_sort_order(client):
    _add_skills(client, CATALOGUE)
    body = client.get(
        URL, headers=_register(client), params={"sort_by": "name", "sort_order": "desc"}
    ).json()
    assert [item["name"] for item in body["items"]] == [
        "TypeScript", "Python", "PostgreSQL", "Git", "Docker",
    ]


def test_search_is_partial_and_case_insensitive(client):
    _add_skills(client, CATALOGUE)
    headers = _register(client)

    body = client.get(URL, headers=headers, params={"q": "O"}).json()
    assert [item["name"] for item in body["items"]] == ["Docker", "PostgreSQL", "Python"]
    assert body["pagination"]["total_items"] == 3

    assert client.get(URL, headers=headers, params={"q": "cobol"}).json()["items"] == []


def test_search_treats_wildcards_literally(client):
    _add_skills(client, CATALOGUE + [("100% Remote", "remote", None), ("C_Sharp", "c-sharp", None)])
    headers = _register(client)

    percent = client.get(URL, headers=headers, params={"q": "%"}).json()
    assert [item["name"] for item in percent["items"]] == ["100% Remote"]

    underscore = client.get(URL, headers=headers, params={"q": "_"}).json()
    assert [item["name"] for item in underscore["items"]] == ["C_Sharp"]


def test_category_filter_is_exact_and_combines_with_search(client):
    _add_skills(client, CATALOGUE)
    headers = _register(client)

    body = client.get(URL, headers=headers, params={"category": "PROGRAMMING"}).json()
    assert [item["name"] for item in body["items"]] == ["Python", "TypeScript"]

    assert client.get(URL, headers=headers, params={"category": "PROGRAM"}).json()["items"] == []

    combined = client.get(URL, headers=headers, params={"category": "PROGRAMMING", "q": "type"}).json()
    assert [item["name"] for item in combined["items"]] == ["TypeScript"]


def test_skill_detail(client):
    ids = _add_skills(client, CATALOGUE)
    headers = _register(client)

    found = client.get(f"{URL}/{ids['python']}", headers=headers)
    assert found.status_code == 200
    assert found.json() == {
        "id": ids["python"], "name": "Python", "slug": "python", "category": "PROGRAMMING",
    }

    missing = client.get(f"{URL}/{uuid4()}", headers=headers)
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Skill not found"}

    assert client.get(f"{URL}/not-a-uuid", headers=headers).status_code == 422


def test_catalogue_is_read_only(client):
    ids = _add_skills(client, CATALOGUE)
    headers = _register(client)
    assert client.post(URL, headers=headers, json={"name": "X", "slug": "x"}).status_code == 405
    for method in ("put", "patch", "delete"):
        assert getattr(client, method)(f"{URL}/{ids['python']}", headers=headers).status_code == 405


def test_listed_skill_can_be_added_to_candidate_profile(client):
    _add_skills(client, CATALOGUE)
    headers = _register(client)
    client.put("/api/v1/candidates/me", headers=headers, json={})

    skill = client.get(URL, headers=headers, params={"q": "python"}).json()["items"][0]
    added = client.post(
        "/api/v1/candidates/me/skills",
        headers=headers,
        json={"skill_id": skill["id"], "proficiency": "ADVANCED"},
    )
    assert added.status_code == 201
    assert added.json()["skill"] == skill


def test_seed_is_idempotent_and_preserves_existing_rows(client):
    existing = _add_skills(client, [("Python", "python", "LEGACY")])
    db = _db(client)
    try:
        assert seed_skills(db) == 9
        assert seed_skills(db) == 0
        python = db.get(Skill, UUID(existing["python"]))
        assert python.category == "LEGACY"
    finally:
        db.close()

    body = client.get(URL, headers=_register(client)).json()
    assert body["pagination"]["total_items"] == 10
