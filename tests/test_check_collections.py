import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_collections.py"
spec = importlib.util.spec_from_file_location("check_collections", SCRIPT)
guard = importlib.util.module_from_spec(spec)
sys.modules["check_collections"] = guard  # necessário para o @dataclass do script
spec.loader.exec_module(guard)

# Valores fabricados só para estes testes; nenhum é uma credencial real.
# Construído em tempo de execução: o ficheiro de testes não pode conter uma sequência com forma de JWT,
# senão o próprio guarda bloquearia o commit deste ficheiro.
FAKE_JWT = ".".join(["eyJ" + "fakeheader1", "eyJ" + "fakepayload1", "fakesignature1"])
FAKE_SECRET = "Zx-fake-secret-9"

HEADER = "type: collection.insomnia.rest/5.0\nname: DEMO\n"


def _collection(body: str) -> str:
    return HEADER + body


def _rules(text: str, allowed=frozenset()) -> list[str]:
    return [f.rule for f in guard.check_text("demo.yaml", text, set(allowed)) if f.blocking]


CLEAN = _collection(
    """collection:
  - url: "{{ _.base_url }}/auth/login"
    name: Login
    method: POST
    body:
      mimeType: application/json
      text: |-
        {
          "email": "{{ _.test_email }}",
          "password": "{{ _.test_password }}"
        }
    headers:
      - name: Origin
        value: http://localhost:5173
    authentication:
      type: bearer
      token: "{{ _.token }}"
      prefix: ""
cookieJar:
  name: Default Jar
  meta:
    id: jar_x
  cookies: []
environments:
  name: Base Environment
  data:
    base_url: http://127.0.0.1:8000/api/v1
    token: ""
    test_email: ""
    test_password: ""
    skill_id: 0bac8c13-30ab-427c-8233-bd529a5d0d88
"""
)


def test_clean_collection_has_no_findings():
    assert guard.check_text("demo.yaml", CLEAN, set()) == []


def test_jwt_is_detected_in_collection_and_in_any_text_file():
    assert "jwt" in _rules(_collection(f"environments:\n  data:\n    note: {FAKE_JWT}\n"))
    findings = guard.check_text("notes.md", f"Authorization: Bearer {FAKE_JWT}\n", set())
    assert [f.rule for f in findings] == ["jwt"]


def test_cookie_jar_entries_are_detected_even_with_empty_value():
    jar = "cookieJar:\n  name: Default Jar\n  cookies:\n    - id: abc\n      key: session\n      value: ''\n"
    assert _rules(_collection(jar)) == ["cookie-jar"]


def test_non_empty_sensitive_environment_values_are_detected():
    for key in ("token_candidate_a", "old_password", "new_password", "client_secret", "refresh_value", "api_key"):
        text = _collection(f"environments:\n  data:\n    {key}: {FAKE_SECRET}\n")
        assert _rules(text) == ["variavel-sensivel"], key


def test_templates_and_empty_values_are_accepted():
    for value in ('""', "''", "", '"{{ _.token }}"', "'{{ _.old_password }}'"):
        text = _collection(f"environments:\n  data:\n    old_password: {value}\n")
        assert _rules(text) == [], value


def test_literal_secrets_in_request_bodies_are_detected():
    body = f'collection:\n  - name: x\n    body:\n      text: |-\n        {{"email": "a@example.com", "password": "{FAKE_SECRET}"}}\n'
    assert _rules(_collection(body)) == ["corpo-pedido"]
    for key in ("current_password", "new_password", "access_token", "client_secret"):
        text = _collection(f'collection:\n  - name: x\n    body:\n      text: \'{{"{key}": "{FAKE_SECRET}"}}\'\n')
        assert _rules(text) == ["corpo-pedido"], key


def test_template_values_in_bodies_are_accepted():
    body = '        {"password": "{{ _.test_password }}", "token": ""}\n'
    assert _rules(_collection("collection:\n  - name: x\n    body:\n      text: |-\n" + body)) == []


def test_sensitive_header_values_are_detected_but_other_headers_are_not():
    risky = "headers:\n  - name: X-CSRF-Token\n    value: abc123fake\n  - name: Origin\n    value: http://localhost:5173\n"
    assert _rules(_collection(risky)) == ["cabecalho-sensivel"]
    safe = "headers:\n  - name: X-CSRF-Token\n    value: '{{ _.csrf }}'\n  - name: Origin\n    value: http://localhost:5173\n"
    assert _rules(_collection(safe)) == []


def test_request_named_with_token_does_not_cause_false_positive():
    text = _collection("collection:\n  - url: x\n    name: List Skills - Invalid Token\n    headers:\n      - name: Origin\n        value: http://localhost:5173\n")
    assert _rules(text) == []


def test_allowed_values_are_accepted_only_when_listed():
    text = _collection(
        'collection:\n  - name: x\n    body:\n      text: \'{"password": "short"}\'\n    authentication:\n      type: bearer\n      token: not-a-valid-token\n'
    )
    assert _rules(text) == ["corpo-pedido", "variavel-sensivel"]
    assert _rules(text, allowed={"short", "not-a-valid-token"}) == []


def test_real_looking_email_is_only_a_warning():
    text = _collection("environments:\n  data:\n    candidate_a_email: person@company.io\n    test_email: a@example.com\n")
    findings = guard.check_text("demo.yaml", text, set())
    assert [(f.rule, f.blocking) for f in findings] == [("email", False)]


def test_non_collection_yaml_is_only_checked_for_jwt():
    text = "services:\n  db:\n    password: something-not-checked\n"
    assert guard.check_text("docker.yaml", text, set()) == []


def test_findings_never_include_values():
    text = _collection(
        f"environments:\n  data:\n    old_password: {FAKE_SECRET}\n    note: {FAKE_JWT}\n"
        f'collection:\n  - name: x\n    body:\n      text: \'{{"password": "{FAKE_SECRET}"}}\'\n'
    )
    rendered = "\n".join(f.render() for f in guard.check_text("demo.yaml", text, set()))
    assert rendered
    assert FAKE_SECRET not in rendered and FAKE_JWT not in rendered and "eyJ" not in rendered


def test_allowed_values_file_only_contains_known_harmless_values():
    allowed = guard.load_allowed_values()
    assert allowed == {"short", "not-a-valid-token", "not-the-current-password", "another-long-password-1"}


def _git(repo: Path, *args: str):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _run_staged(repo: Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--staged"], cwd=repo, capture_output=True, text=True
    )


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    return tmp_path


def test_staged_mode_blocks_bad_collection_and_reads_the_index_not_the_working_tree(repo):
    bad = CLEAN.replace('token: ""', f"token: {FAKE_SECRET}")
    (repo / "demo.yaml").write_text(bad, encoding="utf-8")
    _git(repo, "add", "demo.yaml")

    blocked = _run_staged(repo)
    assert blocked.returncode == 1
    assert "[variavel-sensivel] token" in blocked.stdout
    assert FAKE_SECRET not in blocked.stdout + blocked.stderr

    # Limpar só a cópia de trabalho não resolve: o que conta é o que está em stage.
    (repo / "demo.yaml").write_text(CLEAN, encoding="utf-8")
    assert _run_staged(repo).returncode == 1

    _git(repo, "add", "demo.yaml")
    assert _run_staged(repo).returncode == 0


def test_staged_mode_ignores_unstaged_and_binary_files_and_catches_jwt_in_any_file(repo):
    (repo / "unstaged.yaml").write_text(_collection(f"environments:\n  data:\n    token: {FAKE_SECRET}\n"))
    (repo / "image.bin").write_bytes(b"\x00\x01" + FAKE_JWT.encode())
    (repo / "notes.txt").write_text(f"token: {FAKE_JWT}\n")
    _git(repo, "add", "image.bin", "notes.txt")

    result = _run_staged(repo)
    assert result.returncode == 1
    assert "notes.txt:1  [jwt]" in result.stdout
    assert "unstaged.yaml" not in result.stdout and "image.bin" not in result.stdout
