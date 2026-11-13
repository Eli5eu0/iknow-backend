# ERRORS — Formato uniforme de erro (ADR-014)

## Responsabilidade
Garante que toda a resposta de erro JSON sob `/api/v1` segue o contrato §1.1, incluindo erros do próprio framework (rota inexistente, método não permitido) e erros inesperados.

## Formato

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Skill not found",
    "details": null,
    "request_id": "uuid"
  }
}
```

| HTTP | `code` | `message` | `details` |
|---|---|---|---|
| 400 | `BAD_REQUEST` | texto da excepção | `null` |
| 401 | `UNAUTHORIZED` | texto da excepção; cabeçalho `WWW-Authenticate` preservado | `null` |
| 403 | `FORBIDDEN` | texto da excepção | `null` |
| 404 | `NOT_FOUND` | texto da excepção (`Not Found` em rotas inexistentes) | `null` |
| 405 | `METHOD_NOT_ALLOWED` | `Method Not Allowed` | `null` |
| 409 | `CONFLICT` | texto da excepção | `null` |
| 410 | `GONE` | texto da excepção | `null` |
| 422 de validação | `VALIDATION_ERROR` | `Request validation failed` | lista `[{type, loc, msg}]` |
| 422 de regra de negócio | `VALIDATION_ERROR` | texto da regra | `null` |
| 429 | `RATE_LIMITED` | texto da excepção (reservado ao rate limiting) | `null` |
| 500 | `INTERNAL_ERROR` | `Internal server error` | `null` |
| outros (por exemplo 503) | `HTTP_ERROR` | texto da excepção | `null` |

Regras:
- `details` do 422 de validação nunca inclui os valores enviados (`input`) nem o contexto (`ctx`).
- Um `detail` que não seja texto não é devolvido; usa-se a descrição padrão do código HTTP.
- Cabeçalhos definidos na excepção (por exemplo `WWW-Authenticate`, `Retry-After`) são preservados.
- As mensagens são técnicas e em inglês; o frontend mostra o texto em português escolhido pelo código HTTP.

## request_id
- UUID v4 gerado no servidor para cada pedido; um `X-Request-ID` enviado pelo cliente é ignorado.
- Devolvido no corpo dos erros e no cabeçalho `X-Request-ID` de todas as respostas.
- Nos erros 500, o traceback é registado no servidor (logger `iknow.errors`) com o mesmo `request_id`; nunca é devolvido ao cliente.

## Implementação
`app/core/errors.py`: handlers de `HTTPException` e `RequestValidationError`, middleware de contexto do pedido (dentro do CORS, para o 500 também levar cabeçalhos CORS), e OpenAPI com `ErrorResponse` no lugar de `HTTPValidationError`. Routers e services continuam a levantar `HTTPException` e não constroem o envelope à mão.

## Códigos específicos
Os códigos derivam do código HTTP. Códigos específicos por situação (por exemplo `EMAIL_ALREADY_REGISTERED`) não existem; se forem necessários, serão acrescentados de forma aditiva, sem alterar os códigos acima.
