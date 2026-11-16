"""Aplicação FastAPI da Caderneta."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import (
    alunos,
    anotacoes,
    auth,
    autorizacoes,
    avisos,
    boletim,
    calendario,
    convites,
    desligados,
    diario,
    downloads,
    escola,
    historico,
    historico_escolar,
    importacao,
    impressao,
    mensagens,
    notificacoes,
    push,
    titular,
    turmas,
)

ROTEADORES = (
    auth,
    convites,
    escola,
    turmas,
    alunos,
    importacao,
    diario,
    boletim,
    avisos,
    autorizacoes,
    mensagens,
    notificacoes,
    calendario,
    impressao,
    downloads,
    historico,
    anotacoes,
    historico_escolar,
    push,
    desligados,
    titular,
)
METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS"}
CSRF_HEADER = "x-caderneta"


def create_app() -> FastAPI:
    s = get_settings()
    docs = "/api/docs" if s.env != "prod" else None
    app = FastAPI(
        title="Caderneta API",
        version="0.1.0",
        docs_url=docs,
        redoc_url=None,
        openapi_url="/api/openapi.json" if docs else None,
    )

    @app.middleware("http")
    async def protecoes(request: Request, call_next):
        # CSRF: navegadores não enviam cabeçalhos customizados entre origens sem preflight CORS,
        # e esta API não habilita CORS. Junto com SameSite=Lax, bloqueia requisições forjadas.
        if request.method not in METODOS_SEGUROS and request.headers.get(CSRF_HEADER) != "1":
            return JSONResponse({"detail": "Requisição recusada (CSRF)."}, 403)
        response = await call_next(request)
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        if "json" in response.headers.get("content-type", ""):  # respostas da API não carregam nada: CSP vazia
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        if get_settings().cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

    @app.get("/api/saude", tags=["infra"])
    def saude():
        return {"ok": True}

    for r in ROTEADORES:
        app.include_router(r.router, prefix="/api")
    return app


app = create_app()
