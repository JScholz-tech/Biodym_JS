"""Shared template/rendering dependencies for the SystemDefiner routers.

Kept in one place so every router renders through the same Jinja2 environment
(filters, globals) that used to live at the top of ``main.py``.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from systemdefiner import storage

_HERE = Path(__file__).parent

templates = Jinja2Templates(directory=_HERE / "templates")

# Available in every template (base.html shows the diagram band when present).
templates.env.globals["study_has_diagram"] = (
    lambda name: storage.diagram_path(name) is not None
)


def _render_markdown(text: str) -> str:
    """Render a study description as sanitized HTML from Markdown.

    Falls back to escaped plain text (with line breaks preserved) if the
    optional markdown/bleach libraries are unavailable.
    """
    text = (text or "").strip()
    if not text:
        return ""
    try:
        import markdown as _md
        import bleach as _bleach

        html = _md.markdown(text, extensions=["extra", "sane_lists", "nl2br"])
        allowed_tags = {
            "p",
            "br",
            "hr",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "strong",
            "em",
            "b",
            "i",
            "code",
            "pre",
            "blockquote",
            "a",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
        }
        allowed_attrs = {"a": ["href", "title"]}
        clean = _bleach.clean(
            html, tags=allowed_tags, attributes=allowed_attrs, strip=True
        )
        return _bleach.linkify(clean)
    except Exception:
        from markupsafe import escape

        return str(escape(text)).replace("\n", "<br>")


templates.env.filters["markdown"] = _render_markdown


def _error_page(request: Request, code: int, message: str):
    return templates.TemplateResponse(
        request,
        "error.html",
        {"code": code, "message": message},
        status_code=code,
    )


def _ctx(**kwargs) -> dict:
    return kwargs
