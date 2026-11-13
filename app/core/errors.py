"""Formato uniforme de erro (contrato §1.1, ADR-014).

Todas as respostas de erro JSON seguem:
    {"error": {"code", "message", "details", "request_id"}}
"""

import logging
from http import HTTPStatus
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic.json_schema import models_json_schema
from starlette.datastructures import MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("iknow.errors")

REQUEST_ID_HEADER = "X-Request-ID"

_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    410: "GONE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
}


def error_code_for_status(status_code: int) -> str:
    return _ERROR_CODES.get(status_code, "HTTP_ERROR")


class ValidationIssue(BaseModel):
    type: str
    loc: list[str | int]
    msg: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ValidationIssue] | None = None
    request_id: UUID


class ErrorResponse(BaseModel):
    error: ErrorBody


def build_error_content(
    request_id: str, status_code: int, message: str, details: list[dict] | None = None
) -> dict:
    return {
        "error": {
            "code": error_code_for_status(status_code),
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or str(uuid4())


def _phrase(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Error"


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
    headers = getattr(exc, "headers", None)
    if exc.status_code in {204, 304}:
        return Response(status_code=exc.status_code, headers=headers)
    message = exc.detail if isinstance(exc.detail, str) else _phrase(exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_content(_request_id(request), exc.status_code, message),
        headers=headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:
    # Os valores enviados ("input") e o contexto ("ctx") nunca são devolvidos.
    details = [
        {
            "type": str(issue["type"]),
            "loc": [part if isinstance(part, (str, int)) else str(part) for part in issue["loc"]],
            "msg": str(issue["msg"]),
        }
        for issue in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=build_error_content(
            _request_id(request), 422, "Request validation failed", details
        ),
    )


class RequestContextMiddleware:
    """Atribui um request_id a cada pedido e converte excepções não tratadas em 500.

    Fica dentro do middleware de CORS, para que a resposta 500 inclua os cabeçalhos CORS.
    O X-Request-ID enviado pelo cliente é ignorado.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            logger.exception(
                "Unhandled exception (request_id=%s) %s %s",
                request_id,
                scope.get("method"),
                scope.get("path"),
            )
            if response_started:
                raise
            response = JSONResponse(
                status_code=500,
                content=build_error_content(request_id, 500, "Internal server error"),
            )
            await response(scope, receive, send_with_request_id)


def custom_openapi(application: FastAPI) -> dict:
    """OpenAPI com o formato de erro uniforme no lugar do HTTPValidationError do FastAPI."""
    if application.openapi_schema:
        return application.openapi_schema

    schema = get_openapi(
        title=application.title,
        version=application.version,
        openapi_version=application.openapi_version,
        description=application.description,
        routes=application.routes,
        tags=application.openapi_tags,
        servers=application.servers,
    )
    components = schema.setdefault("components", {}).setdefault("schemas", {})
    for name in ("HTTPValidationError", "ValidationError"):
        components.pop(name, None)
    _, definitions = models_json_schema(
        [(ErrorResponse, "serialization")], ref_template="#/components/schemas/{model}"
    )
    components.update(definitions.get("$defs", {}))

    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            response = operation.get("responses", {}).get("422")
            if response is not None:
                response["description"] = "Validation error"
                response["content"] = {
                    "application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}
                }

    application.openapi_schema = schema
    return schema


def install_error_handling(application: FastAPI) -> None:
    """Regista handlers, middleware e OpenAPI. Chamar antes de adicionar o CORS."""
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_middleware(RequestContextMiddleware)
    application.openapi = lambda: custom_openapi(application)
