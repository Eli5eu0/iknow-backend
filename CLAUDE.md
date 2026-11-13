# CLAUDE.md — Backend iKnow

Instruções permanentes para o Claude Code neste repositório. Lê este ficheiro antes de qualquer tarefa.

Referências:
- `README.md` — arranque local (Docker, Alembic, uvicorn, pytest).
- `docs/<MÓDULO>.md` — especificação de cada módulo implementado.
- `docs/testing/README.md` — procedimento detalhado de testes HTTP com Koh e Insomnia.
- `.agents/skills/koh/SKILL.md` — referência dos comandos do Koh CLI (ler antes de usar o Koh).
- Notion "iKnow — Project Hub" — roadmap, tarefas, decisões (ADR), testes e relatórios.

## 1. Regras inegociáveis

1. Não fazer commits, pushes nem merges sem autorização explícita.
2. Não executar operações destrutivas na base de dados; nunca `docker compose down -v`; não eliminar dados nem migrações.
3. Não alterar decisões arquitecturais nem contratos válidos sem aprovação. As decisões estão no Notion (05 — Decisões Técnicas).
4. Não inventar endpoints, campos, requisitos nem resultados de testes.
5. Não reimplementar módulos concluídos nem refactorizar fora do âmbito.
6. Nunca colocar palavras-passe, JWT, refresh tokens, cookies ou conteúdo de `.env` em ficheiros versionados, colecções Insomnia, logs, relatórios ou Notion.
7. Não desactivar mecanismos de segurança (CSRF, validação de Origin, autenticação) para facilitar testes.
8. Regras de negócio ficam nos services, não nos routers.
9. Erros seguem o formato uniforme do contrato §1.1 (`docs/ERRORS.md`). Routers e services levantam `HTTPException`; nunca construir o envelope `{error: ...}` à mão nem devolver `{detail: ...}` por outra via.

## 2. Fluxo obrigatório por módulo

Cada módulo novo passa por todas as fases, por ordem. As fases de planeamento e de contrato exigem aprovação do responsável antes da implementação.

- **Fase A — Implementação.** Analisar requisitos e dependências; fechar o contrato da API; implementar models, schemas, services, routers e migrações; criar testes Pytest.
- **Fase B — Colecção Insomnia.** Criar ou actualizar com o Koh a colecção do módulo (um ficheiro `<módulo>.yaml` na raiz, nome da colecção em maiúsculas). Cobrir: sucesso, validações, autenticação e autorização, recursos inexistentes, conflitos e estados inválidos, regras de negócio do módulo.
- **Fase C — Execução.** Executar os pedidos com `koh request run` contra o backend local, com o backend confirmado disponível. Um pedido só conta como testado depois de executado e de a resposta ter sido analisada.
- **Fase D — Análise e correcção.** Comparar código HTTP e corpo com o contrato; corrigir a implementação, o contrato ou a configuração; reexecutar o que foi afectado. Nunca alterar a expectativa de um teste só para o fazer passar.
- **Fase E — Validação final.** `pytest` completo, todos os cenários relevantes da colecção via Koh, `alembic check`, relatório em `docs/testing/reports/` e actualização do Notion.

Um módulo só é dado como concluído com as cinco fases comprovadas. O que não puder ser validado é registado como "Não validado", com o motivo.

## 3. Papéis das ferramentas

- Pytest valida o comportamento interno (SQLite em memória).
- Koh CLI executa os testes HTTP reais da colecção Insomnia contra backend + PostgreSQL locais.
- Insomnia mantém a organização visual dos pedidos e ambientes.

## 4. Credenciais nos testes HTTP

- As colecções guardam apenas marcadores (`{{ _.variavel }}`) com valor vazio no ambiente base.
- Tokens e credenciais são passados em tempo de execução (`--auth bearer:<token>`, `--body`), a partir de variáveis da shell que nunca são impressas.
- Usar contas de teste efémeras criadas na própria execução e desactivadas no fim; nunca contas reais.
- Depois de cada execução: `koh cookie clear` na colecção e confirmar com `git diff` que nenhum token ficou no YAML.

- Um hook `pre-commit` (`.githooks/pre-commit`, activado com `git config core.hooksPath .githooks`) corre `scripts/check_collections.py --staged` e bloqueia commits com JWT, cookies ou valores não vazios em variáveis de token, palavra-passe ou segredo nas colecções. Nunca usar `--no-verify` sem autorização; nunca acrescentar valores a `scripts/collection_allowed_values.txt` sem autorização. Credenciais reais ficam num sub-ambiente privado do Insomnia, nunca no ambiente base.
- Antes de qualquer `git add` de colecções, correr `python scripts/check_collections.py`.

Detalhes e comandos em `docs/testing/README.md`.

## 5. Registo de resultados

Um relatório por módulo em `docs/testing/reports/<módulo>.md`, segundo `docs/testing/REPORT_TEMPLATE.md`, com endpoint, cenário, resultado esperado, resultado obtido, estado e observações. No Notion, registar só testes efectivamente executados, distinguindo Configurado, Executado, Aprovado e Não validado.
