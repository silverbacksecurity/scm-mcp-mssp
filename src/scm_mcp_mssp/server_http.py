"""
HTTP/SSE transport server for Copilot Studio and remote MCP clients.

Wraps the same FastMCP instance as the stdio server but exposes it over
HTTP with Server-Sent Events (SSE) transport, making it compatible with:

  - Microsoft Copilot Studio (Settings → AI → MCP Servers)
  - Any MCP client that supports SSE transport
  - Azure Container Apps / App Service deployments

Auth modes (SCM_MCP_HTTP_AUTH_MODE):
  apikey  — X-API-Key header or ?api_key= query param (default)
  entra   — Azure AD / Entra ID Bearer JWT (validates aud + iss)
  none    — No auth (dev/localhost only — never expose publicly)

Env vars:
  SCM_MCP_HTTP_HOST           Bind address (default 0.0.0.0 for containers)
  SCM_MCP_HTTP_PORT           TCP port (default 8080)
  SCM_MCP_HTTP_API_KEY        Required for apikey mode
  SCM_MCP_HTTP_AUTH_MODE      apikey | entra | none  (default: apikey)
  SCM_MCP_HTTP_ENTRA_TENANT   Entra tenant ID (entra mode)
  SCM_MCP_HTTP_ENTRA_AUDIENCE App ID / client ID expected in 'aud' claim
  SCM_MCP_HTTP_ALLOWED_ORIGINS CORS origins, comma-separated (default: *)
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable

import jwt
import uvicorn
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from .server import create_server
from .utils.logging import get_logger

logger = get_logger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────

# Default 0.0.0.0 so the server is reachable inside a container; override with
# SCM_MCP_HTTP_HOST=127.0.0.1 for local-only binding.
_HOST = os.getenv("SCM_MCP_HTTP_HOST", "0.0.0.0")  # nosec B104
_PORT = int(os.getenv("SCM_MCP_HTTP_PORT", "8080"))
_AUTH_MODE = os.getenv("SCM_MCP_HTTP_AUTH_MODE", "apikey").lower()
_API_KEY = os.getenv("SCM_MCP_HTTP_API_KEY", "")
_ENTRA_TENANT = os.getenv("SCM_MCP_HTTP_ENTRA_TENANT", "")
_ENTRA_AUDIENCE = os.getenv("SCM_MCP_HTTP_ENTRA_AUDIENCE", "")
_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("SCM_MCP_HTTP_ALLOWED_ORIGINS", "*").split(",") if o.strip()
]

# Entra JWKS URI — fetched once at startup
_JWKS_CLIENT: jwt.PyJWKClient | None = None


def _get_jwks_client() -> jwt.PyJWKClient:
    global _JWKS_CLIENT
    if _JWKS_CLIENT is None:
        jwks_uri = f"https://login.microsoftonline.com/{_ENTRA_TENANT}/discovery/v2.0/keys"
        _JWKS_CLIENT = jwt.PyJWKClient(jwks_uri)
    return _JWKS_CLIENT


def _validate_entra_token(token: str) -> bool:
    """Validate an Entra ID Bearer JWT. Returns True if valid."""
    if not _ENTRA_TENANT or not _ENTRA_AUDIENCE:
        logger.warning("entra_auth_misconfigured")
        return False
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=_ENTRA_AUDIENCE,
            issuer=f"https://login.microsoftonline.com/{_ENTRA_TENANT}/v2.0",
        )
        return True
    except jwt.ExpiredSignatureError:
        logger.warning("entra_token_expired")
    except jwt.InvalidTokenError as exc:
        logger.warning("entra_token_invalid", error=str(exc))
    return False


# ─── Auth middleware ──────────────────────────────────────────────────────────


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Validate inbound requests before passing to the MCP SSE handler.

    Supports:
      - apikey: X-API-Key header or ?api_key= query param
      - entra:  Authorization: Bearer <Entra ID JWT>
      - none:   Always allow (dev only)
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Health-check endpoint is always public
        if request.url.path in ("/health", "/healthz"):
            return await call_next(request)

        if _AUTH_MODE == "none":
            return await call_next(request)

        if _AUTH_MODE == "apikey":
            provided = request.headers.get("X-API-Key") or request.query_params.get("api_key")
            if not _API_KEY:
                logger.error("apikey_auth_no_key_configured")
                return JSONResponse(
                    {"error": "Server misconfigured — SCM_MCP_HTTP_API_KEY not set"},
                    status_code=500,
                )
            if provided != _API_KEY:
                logger.warning("apikey_auth_failed", path=request.url.path)
                return JSONResponse(
                    {"error": "Unauthorized — invalid or missing X-API-Key"},
                    status_code=401,
                )
            return await call_next(request)

        if _AUTH_MODE == "entra":
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    {"error": "Unauthorized — Bearer token required"},
                    status_code=401,
                )
            token = auth_header[len("Bearer ") :]
            if not _validate_entra_token(token):
                return JSONResponse(
                    {"error": "Unauthorized — invalid Entra ID token"},
                    status_code=401,
                )
            return await call_next(request)

        return JSONResponse(
            {"error": f"Unknown auth mode: {_AUTH_MODE}"},
            status_code=500,
        )


# ─── App factory ─────────────────────────────────────────────────────────────


def create_http_app() -> Starlette:
    """Build the Starlette ASGI app: auth + CORS + MCP SSE handler + /health."""
    mcp = create_server()
    sse = mcp.sse_app()

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "server": "scm-mcp-mssp"})

    app = Starlette(
        routes=[
            Route("/health", health),
            Route("/healthz", health),
            Mount("/", app=sse),
        ]
    )

    # CORS — required for browser-based Copilot Studio flows
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_ALLOWED_ORIGINS,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "X-API-Key", "Content-Type"],
    )

    # Auth — outermost middleware so it runs first
    app.add_middleware(AuthMiddleware)

    return app


def main() -> None:
    if _AUTH_MODE == "apikey" and not _API_KEY:
        raise SystemExit(
            "ERROR: SCM_MCP_HTTP_API_KEY must be set when SCM_MCP_HTTP_AUTH_MODE=apikey.\n"
            'Generate one with:  python -c "import secrets; print(secrets.token_urlsafe(32))"\n'
            "Then set:           export SCM_MCP_HTTP_API_KEY=<value>"
        )
    if _AUTH_MODE == "entra" and (not _ENTRA_TENANT or not _ENTRA_AUDIENCE):
        raise SystemExit(
            "ERROR: SCM_MCP_HTTP_ENTRA_TENANT and SCM_MCP_HTTP_ENTRA_AUDIENCE must be set "
            "when SCM_MCP_HTTP_AUTH_MODE=entra."
        )

    logger.info(
        "http_server_starting",
        host=_HOST,
        port=_PORT,
        auth_mode=_AUTH_MODE,
        origins=_ALLOWED_ORIGINS,
    )

    app = create_http_app()
    uvicorn.run(app, host=_HOST, port=_PORT, log_level="warning")
