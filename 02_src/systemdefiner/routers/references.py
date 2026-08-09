"""Zotero integration + reference management routes.

Moved verbatim from ``main.py``.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from systemdefiner import storage
from systemdefiner.deps import _ctx, templates
from systemdefiner.models.config_schema import ReferenceEntry

router = APIRouter()

_ZOTERO_BASE = "http://localhost:23119"
_ZOTERO_RPC = f"{_ZOTERO_BASE}/better-bibtex/json-rpc"
_ZOTERO_PING = f"{_ZOTERO_BASE}/connector/ping"
# Documented Better BibTeX readiness probe — no side effects, no picker opened.
_BBT_PROBE = f"{_ZOTERO_BASE}/better-bibtex/cayw?probe=probe"

BBT_XPI_URL = "https://github.com/retorquere/zotero-better-bibtex/releases/latest"
BBT_DOCS_URL = "https://retorque.re/zotero-better-bibtex/installation/"
ZOTERO_DOWNLOAD_URL = "https://www.zotero.org/download/"


def _probe(url: str, timeout: float = 1.5) -> bool:
    """True when *url* answers with a 2xx/3xx inside *timeout* seconds."""
    try:
        import httpx

        return httpx.get(url, timeout=timeout).status_code < 400
    except Exception:
        return False


def _zotero_search(query: str) -> list[dict]:
    """Query local Better BibTeX JSON-RPC. Returns [] when Zotero is not running."""
    try:
        import httpx

        r = httpx.post(
            _ZOTERO_RPC,
            json={
                "jsonrpc": "2.0",
                "method": "item.search",
                "params": {"terms": query},
                "id": 1,
            },
            timeout=3.0,
        )
        data = r.json()
        return data.get("result", []) or []
    except Exception:
        return []


def _fmt_authors(item: dict) -> str:
    authors = item.get("author", [])
    if not authors:
        return ""
    if len(authors) == 1:
        return authors[0].get("family", "")
    if len(authors) == 2:
        return f"{authors[0].get('family', '')} & {authors[1].get('family', '')}"
    return f"{authors[0].get('family', '')} et al."


def _fmt_year(item: dict) -> str:
    issued = item.get("issued", {})
    parts = issued.get("date-parts", [[]])[0]
    return str(parts[0]) if parts else ""


def _item_to_ref(item: dict, note: str = "") -> "ReferenceEntry":
    return ReferenceEntry(
        cite_key=item.get("citekey") or item.get("citation-key", ""),
        title=item.get("title", ""),
        authors=_fmt_authors(item),
        year=_fmt_year(item),
        item_type=item.get("type", ""),
        doi=item.get("DOI", ""),
        note=note,
    )


@router.get("/api/zotero/search")
async def zotero_search(q: str = ""):
    if not q.strip():
        return []
    items = _zotero_search(q.strip())
    return [
        {
            "cite_key": it.get("citekey") or it.get("citation-key", ""),
            "title": it.get("title", ""),
            "authors": _fmt_authors(it),
            "year": _fmt_year(it),
            "item_type": it.get("type", ""),
            "doi": it.get("DOI", ""),
        }
        for it in items
        if it.get("citekey") or it.get("citation-key")
    ]


@router.get("/api/zotero/status")
async def zotero_status():
    """Report whether the Zotero link is usable, and what is missing if not.

    Three states the setup panel renders differently:
      ``ready``       Zotero running + Better BibTeX answering  -> search works
      ``no_bbt``      Zotero running, Better BibTeX absent      -> install the plugin
      ``no_zotero``   nothing on port 23119                     -> start/install Zotero
    """
    import asyncio

    zotero, bbt = await asyncio.gather(
        asyncio.to_thread(_probe, _ZOTERO_PING),
        asyncio.to_thread(_probe, _BBT_PROBE),
    )
    # BBT answering implies Zotero is up even if the connector endpoint is off.
    zotero = zotero or bbt

    if bbt:
        state, message = "ready", "Zotero link active — Better BibTeX is answering."
    elif zotero:
        state, message = (
            "no_bbt",
            "Zotero is running, but the Better BibTeX plugin is not installed "
            "(or Zotero needs a restart after installing it).",
        )
    else:
        state, message = (
            "no_zotero",
            "Nothing answering on localhost:23119 — Zotero does not appear to be running.",
        )

    return {
        "state": state,
        "zotero": zotero,
        "bbt": bbt,
        "message": message,
        "port": 23119,
        "xpi_url": BBT_XPI_URL,
        "docs_url": BBT_DOCS_URL,
        "zotero_url": ZOTERO_DOWNLOAD_URL,
    }


@router.get("/{name}/references")
async def references_get(request: Request, name: str, saved: bool = False):
    if not storage.case_study_exists(name):
        raise HTTPException(404)
    cfg = storage.load_case_study(name)
    return templates.TemplateResponse(
        request,
        "references.html",
        _ctx(cfg=cfg, saved=saved),
    )


@router.post("/{name}/references/add")
async def references_add(request: Request, name: str):
    form = await request.form()
    cfg = storage.load_case_study(name)
    cite_key = (form.get("cite_key") or "").strip()
    if not cite_key:
        raise HTTPException(400, "cite_key is required")
    if any(r.cite_key == cite_key for r in cfg.references):
        return RedirectResponse(f"/{name}/references?saved=1", status_code=303)
    cfg.references.append(
        ReferenceEntry(
            cite_key=cite_key,
            title=(form.get("title") or "").strip(),
            authors=(form.get("authors") or "").strip(),
            year=(form.get("year") or "").strip(),
            item_type=(form.get("item_type") or "").strip(),
            doi=(form.get("doi") or "").strip(),
            note=(form.get("note") or "").strip(),
        )
    )
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/references?saved=1", status_code=303)


@router.post("/{name}/references/note")
async def references_note(request: Request, name: str):
    """Update the note on an existing reference."""
    form = await request.form()
    cfg = storage.load_case_study(name)
    cite_key = (form.get("cite_key") or "").strip()
    note = (form.get("note") or "").strip()
    for ref in cfg.references:
        if ref.cite_key == cite_key:
            ref.note = note
            break
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/references?saved=1", status_code=303)


@router.post("/{name}/references/delete")
async def references_delete(request: Request, name: str):
    form = await request.form()
    cfg = storage.load_case_study(name)
    cite_key = (form.get("cite_key") or "").strip()
    cfg.references = [r for r in cfg.references if r.cite_key != cite_key]
    storage.save_case_study(cfg)
    return RedirectResponse(f"/{name}/references", status_code=303)
