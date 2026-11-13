# Testes HTTP com Koh e Insomnia

Procedimento das fases B a E do fluxo obrigatório definido em `CLAUDE.md`.

## Pré-requisitos

- Node.js >= 22.19 e `koh-cli` (`koh --version` deve coincidir com `metadata.version` em `.agents/skills/koh/SKILL.md`).
- PostgreSQL local a correr (`docker compose up -d db`) e migrações aplicadas (`alembic upgrade head`).
- Backend a correr em `http://127.0.0.1:8000` (`uvicorn app.main:app --reload`).

Confirmar a disponibilidade antes de qualquer execução:

```bash
koh request run "Health Check" --project . --agent
```

Esperado: `statusCode` 200 e corpo `{"status":"ok","database":"ok"}`.

## Organização

- O projecto Insomnia é a raiz do repositório: cada ficheiro `.yaml` cuja primeira linha contém `insomnia.rest` é uma colecção.
- Uma colecção por módulo: `candidates.yaml` (CANDIDATES), e assim sucessivamente (`skills.yaml`, `companies.yaml`, ...).
- Nomes dos pedidos: `<Acção> - <Cenário>`, por exemplo `List Skills - page_size acima do máximo`.
- Variáveis no ambiente base da colecção: `base_url` com valor; tokens, emails, palavras-passe e identificadores de recursos sempre vazios no ficheiro.
- Usar sempre `--project . --agent` e identificar pedidos por id quando o nome for ambíguo.

## Autenticação segura

O Koh não suporta variáveis secretas e grava no YAML os cookies recebidos. Por isso:

1. Criar uma conta de teste efémera na própria execução, com palavra-passe gerada e mantida só numa variável da shell.
2. Extrair o `access_token` da resposta para outra variável da shell, sem o imprimir.
3. Passar o token a cada pedido com `--auth "bearer:$TOKEN"`; passar credenciais com `--body`.
4. No fim, desactivar a conta de teste (`DELETE /users/me`) e limpar o cookie jar.

```bash
P="--project . --agent"
BASE=http://127.0.0.1:8000/api/v1
EMAIL="koh-<modulo>-$(date +%s)@example.com"
PASS="$(node -e 'console.log(require("crypto").randomBytes(18).toString("base64url"))')"

REG=$(koh request run "Login - Candidate A" --url "$BASE/auth/register" \
  -H "Origin: http://localhost:5173" -H "Content-Type: application/json" \
  --body "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"role\":\"CANDIDATE\"}" \
  --max-body-bytes 8192 $P)
TOKEN=$(echo "$REG" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>console.log(JSON.parse(JSON.parse(s).data.body).access_token))')

koh request run "Get Candidate A Profile" --auth "bearer:$TOKEN" $P
```

Notas:
- `--max-body-bytes` é necessário para respostas acima de 512 bytes; sem ele o corpo não vem em linha.
- `-H` substitui todos os cabeçalhos guardados, por isso repetir `Content-Type` e `Origin` quando se usa.
- Os endpoints de sessão exigem `Origin: http://localhost:5173`.
- O access token dura 15 minutos; em execuções longas, repetir o login.
- Para testar papéis diferentes, criar uma segunda conta efémera com `"role":"COMPANY"`.

## Dependências entre pedidos e dados

- Executar pela ordem de dependência: preparação (conta, perfil, recursos), cenários, limpeza.
- Identificadores criados durante a execução são extraídos da resposta para variáveis da shell e passados com `--url`; não se gravam no ambiente.
- Os testes só tocam em dados criados pela própria execução. Nunca correr pedidos destrutivos sobre contas ou registos pré-existentes.

## Depois de cada execução

```bash
koh cookie clear --workspace <COLECÇÃO> --project . --agent
koh validate <colecção>.yaml --agent
git diff -- '*.yaml'
```

O `git diff` não pode mostrar tokens, cookies, palavras-passe nem emails de teste. Não imprimir a saída de `koh cookie list`, que contém o refresh token.

## Análise e relatório

Para cada pedido, comparar `statusCode` e `body` com o contrato do módulo. Falhas resolvem-se corrigindo a implementação, o contrato ou a configuração, e reexecutando; nunca ajustando a expectativa.

Registar em `docs/testing/reports/<módulo>.md` segundo `REPORT_TEMPLATE.md` e reflectir no Notion (Testes e Validação) apenas o que foi executado.

Estados usados nos relatórios:
- **Configurado** — existe a configuração ou documentação.
- **Executado** — o comando ou pedido foi efectivamente executado.
- **Aprovado** — a execução produziu o resultado esperado.
- **Não validado** — sem evidência suficiente; indicar o motivo.

## Limitações conhecidas

- No Windows, o Koh 0.4.1 escreve `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)` no stderr ao terminar. A resposta JSON no stdout está completa e é válida.
- `koh collection create` gera o ficheiro como `<nome>-wrk_<id>.yaml`; renomear para `<módulo>.yaml` logo a seguir (o Koh continua a reconhecê-lo).
- O Koh não encadeia pedidos nem faz asserções; a ordem, a extracção de valores e a verificação são feitas pela shell e por quem coordena a execução.
- Variáveis secretas e ambientes de pasta não são suportados pelo Koh.
- No Insomnia (uso manual), preencher credenciais num sub-ambiente privado, que não é sincronizado nem exportado; nunca no ambiente base.
