"""
Branded HTTP error pages (403 / 404 / 500).

These are registered as Starlette/FastAPI exception handlers on NiceGUI's
underlying application object, so any unmatched route or unhandled error returns
a friendly, on-brand page instead of a raw stack trace.
"""

import logging

from fastapi import Request
from fastapi.responses import HTMLResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("taskflow")

# Human-readable copy for the status codes we render explicitly.
_ERROR_COPY = {
    403: ("Access Denied", "You don't have permission to view this page."),
    404: ("Page Not Found", "The page you're looking for doesn't exist or has moved."),
    500: ("Something Went Wrong", "An unexpected error occurred. Please try again later."),
}


def _render(status_code: int) -> HTMLResponse:
    title, message = _ERROR_COPY.get(
        status_code, ("Error", "An unexpected error occurred.")
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{status_code} · {title} · TaskFlow</title>
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css" rel="stylesheet">
    <style>
        :root {{ --primary: #0f766e; --ink: #111827; --muted: #6b7280; }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0; min-height: 100vh; display: flex; align-items: center;
            justify-content: center; font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
            background: linear-gradient(135deg, #f0fdfa 0%, #f8fafc 100%); color: var(--ink);
        }}
        .card {{
            text-align: center; padding: 3rem 2.5rem; background: #fff; border-radius: 1rem;
            box-shadow: 0 10px 40px rgba(15, 118, 110, 0.12); max-width: 460px; width: 90%;
        }}
        .code {{ font-size: 5rem; font-weight: 800; color: var(--primary); line-height: 1; }}
        .icon {{ font-size: 3rem; color: var(--primary); margin-bottom: .5rem; }}
        h1 {{ font-size: 1.5rem; margin: .75rem 0 .5rem; }}
        p {{ color: var(--muted); margin: 0 0 1.75rem; }}
        a {{
            display: inline-block; padding: .75rem 1.75rem; background: var(--primary);
            color: #fff; text-decoration: none; border-radius: .5rem; font-weight: 600;
            transition: opacity .2s;
        }}
        a:hover {{ opacity: .9; }}
    </style>
</head>
<body>
    <div class="card">
        <i class="ri-error-warning-line icon"></i>
        <div class="code">{status_code}</div>
        <h1>{title}</h1>
        <p>{message}</p>
        <a href="/">Back to Home</a>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=status_code)


async def _http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Render a branded page for 403/404 (and fall back for other HTTP errors)."""
    if exc.status_code in (403, 404):
        return _render(exc.status_code)
    # Preserve default behaviour for other HTTP status codes.
    return HTMLResponse(content=str(exc.detail), status_code=exc.status_code)


async def _server_error_handler(request: Request, exc: Exception):
    """Render a branded 500 page and log the underlying error."""
    logger.exception("Unhandled server error at %s", request.url.path)
    return _render(500)


def register_error_pages(app) -> None:
    """Attach the error handlers to the given NiceGUI/FastAPI ``app``."""
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _server_error_handler)
