#!/usr/bin/env python3
"""Guarda anti-credenciais para colecções Insomnia e ficheiros a commitar.

Uso:
    python scripts/check_collections.py --staged      # versão em stage (usado pelo hook pre-commit)
    python scripts/check_collections.py               # colecções .yaml na raiz do repositório
    python scripts/check_collections.py ficheiro.yaml # ficheiros indicados

Regras (um achado bloqueia o commit):
    jwt                 sequência com forma de JWT, em qualquer ficheiro de texto
    cookie-jar          entradas no cookie jar de uma colecção
    variavel-sensivel   valor não vazio numa chave de token, palavra-passe, segredo, etc.
    cabecalho-sensivel  valor literal num cabeçalho Authorization, CSRF, Cookie ou semelhante
    corpo-pedido        palavra-passe, segredo ou token literal num corpo JSON
Emails fora dos domínios reservados geram apenas um aviso.

O script nunca imprime os valores encontrados, só o ficheiro, a linha, a regra e o nome da chave.
Valores de teste inofensivos são autorizados em scripts/collection_allowed_values.txt.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED_VALUES_FILE = Path(__file__).resolve().parent / "collection_allowed_values.txt"
MAX_FILE_BYTES = 2_000_000

JWT_RE = re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*")
SECRET_KEY_RE = re.compile(r"(token|password|passwd|secret|credential|api[_-]?key|refresh|csrf)", re.I)
SECRET_HEADER_RE = re.compile(r"(authorization|csrf|cookie|api[-_]?key|token)", re.I)
EMAIL_KEY_RE = re.compile(r"e-?mail", re.I)
KV_RE = re.compile(r"^(?P<indent>\s*)(?P<dash>-\s+)?(?P<key>[A-Za-z0-9_.-]+):\s*(?P<value>.*?)\s*$")
BODY_SECRET_RE = re.compile(
    r'"(?P<key>[A-Za-z0-9_]*(?:password|passwd|secret|token)[A-Za-z0-9_]*)"\s*:\s*"(?P<value>[^"]*)"',
    re.I,
)
BODY_EMAIL_RE = re.compile(r'"(?P<key>[A-Za-z0-9_]*e-?mail[A-Za-z0-9_]*)"\s*:\s*"(?P<value>[^"]*)"', re.I)
TEMPLATE_RE = re.compile(r"\{\{.*\}\}")
IGNORED_KEYS = {"description", "name", "url", "id", "type", "meta", "prefix"}
BLOCK_SCALAR_MARKERS = {"|", "|-", "|+", ">", ">-", ">+"}
RESERVED_EMAIL_DOMAINS = {"example.com", "example.org", "example.net", "localhost"}
RESERVED_EMAIL_SUFFIXES = (".test", ".invalid", ".example", ".localhost")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    detail: str
    blocking: bool = True

    def render(self) -> str:
        level = "ERRO " if self.blocking else "AVISO"
        suffix = f" {self.detail}" if self.detail else ""
        return f"{level} {self.path}:{self.line}  [{self.rule}]{suffix}"


def load_allowed_values(path: Path = ALLOWED_VALUES_FILE) -> set[str]:
    if not path.exists():
        return set()
    values = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            values.add(line)
    return values


def is_collection(text: str) -> bool:
    first_line = text.split("\n", 1)[0]
    return "insomnia.rest" in first_line


def _normalise(value: str) -> str:
    return value.strip().strip("'\"").strip()


def _is_empty_or_template(value: str) -> bool:
    return value == "" or value in BLOCK_SCALAR_MARKERS or bool(TEMPLATE_RE.search(value))


def _email_is_reserved(value: str) -> bool:
    if "@" not in value:
        return True
    domain = value.rsplit("@", 1)[1].strip().lower()
    return domain in RESERVED_EMAIL_DOMAINS or domain.endswith(RESERVED_EMAIL_SUFFIXES)


def check_text(
    label: str, text: str, allowed: set[str], *, collection: bool | None = None
) -> list[Finding]:
    """Analisa um ficheiro de texto e devolve os achados, sem nunca incluir valores."""
    findings: list[Finding] = []
    if collection is None:
        collection = is_collection(text)

    in_cookie_jar = False
    pending_secret_header: str | None = None

    for number, line in enumerate(text.splitlines(), start=1):
        if JWT_RE.search(line):
            findings.append(Finding(label, number, "jwt", ""))

        if not collection:
            continue

        if line and not line[0].isspace():
            in_cookie_jar = line.startswith("cookieJar:")
        if in_cookie_jar and re.match(r"^\s+-\s", line):
            findings.append(Finding(label, number, "cookie-jar", "entrada no cookie jar"))
            continue

        for match in BODY_SECRET_RE.finditer(line):
            value = _normalise(match.group("value"))
            if not _is_empty_or_template(value) and value not in allowed:
                findings.append(Finding(label, number, "corpo-pedido", match.group("key")))
        for match in BODY_EMAIL_RE.finditer(line):
            value = _normalise(match.group("value"))
            if not _is_empty_or_template(value) and not _email_is_reserved(value):
                findings.append(Finding(label, number, "email", match.group("key"), blocking=False))

        kv = KV_RE.match(line)
        if kv is None:
            continue
        key = kv.group("key")
        value = _normalise(kv.group("value"))

        if pending_secret_header is not None and key == "value":
            if not _is_empty_or_template(value) and value not in allowed:
                findings.append(Finding(label, number, "cabecalho-sensivel", pending_secret_header))
            pending_secret_header = None
            continue
        if kv.group("dash") and key == "name" and SECRET_HEADER_RE.search(value):
            pending_secret_header = value
            continue
        if kv.group("dash") and key == "name":
            pending_secret_header = None

        if key in IGNORED_KEYS or _is_empty_or_template(value):
            continue
        if SECRET_KEY_RE.search(key) and value not in allowed:
            findings.append(Finding(label, number, "variavel-sensivel", key))
        elif EMAIL_KEY_RE.search(key) and not _email_is_reserved(value):
            findings.append(Finding(label, number, "email", key, blocking=False))

    return findings


def _is_text(data: bytes) -> bool:
    return b"\x00" not in data[:8000]


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def staged_files() -> list[tuple[str, str]]:
    """Devolve (caminho, conteúdo em stage) dos ficheiros de texto adicionados ou alterados."""
    names = _git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    result = []
    for raw in names.split(b"\x00"):
        if not raw:
            continue
        path = raw.decode("utf-8", errors="replace")
        data = _git("show", f":{path}")
        if len(data) > MAX_FILE_BYTES or not _is_text(data):
            continue
        result.append((path, data.decode("utf-8", errors="replace")))
    return result


def working_tree_files(paths: list[str]) -> list[tuple[str, str]]:
    candidates = [Path(p) for p in paths] if paths else sorted(
        [*ROOT.glob("*.yaml"), *ROOT.glob("*.yml")]
    )
    result = []
    for path in candidates:
        data = path.read_bytes()
        if len(data) > MAX_FILE_BYTES or not _is_text(data):
            continue
        text = data.decode("utf-8", errors="replace")
        if not paths and not is_collection(text):
            continue
        result.append((path.name if not paths else str(path), text))
    return result


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Guarda anti-credenciais")
    parser.add_argument("paths", nargs="*", help="ficheiros a analisar (por omissão, colecções na raiz)")
    parser.add_argument("--staged", action="store_true", help="analisar a versão em stage do Git")
    args = parser.parse_args(argv)

    allowed = load_allowed_values()
    files = staged_files() if args.staged else working_tree_files(args.paths)

    findings: list[Finding] = []
    for label, text in files:
        findings.extend(check_text(label, text, allowed))

    for finding in findings:
        print(finding.render())

    blocking = [f for f in findings if f.blocking]
    if blocking:
        print(
            f"\nCommit bloqueado: {len(blocking)} achado(s) de credenciais ({len(files)} ficheiro(s) analisado(s)). "
            "Os valores não são mostrados.\n"
            "Mova credenciais para um sub-ambiente privado do Insomnia e limpe o cookie jar "
            "(koh cookie clear). Ver docs/testing/README.md.",
            file=sys.stderr,
        )
        return 1
    print(f"Guarda anti-credenciais: sem achados bloqueantes ({len(files)} ficheiro(s) analisado(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
