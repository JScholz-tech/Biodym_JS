"""bioDYM SystemDefiner — FastAPI app factory.

The route handlers live in ``systemdefiner.routers.*``; shared helpers in
``deps`` (templates), ``forms`` (form parsing), ``cascades`` (config-wide
rename/purge/renumber), ``health`` (model health checks) and
``scenario_params`` (scenario/MC parameter catalog).

Routers are included in the exact order the routes were declared in the
original single-file app — Starlette matches routes in registration order
(e.g. ``POST /{name}/scenarios/new`` must precede
``POST /{name}/scenarios/{sname}``), and the route-inventory test pins this
order.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from systemdefiner.deps import _ctx, _error_page, _render_markdown, templates  # noqa: F401
from systemdefiner.storage import CaseStudyNotFound
from systemdefiner.routers import (
    compositions,
    elements,
    flows,
    io,
    processes,
    references,
    scenarios,
    studies,
    tcs,
)

app = FastAPI(title="bioDYM SystemDefiner")

_HERE = Path(__file__).parent
app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")


# ── Error handling ──────────────────────────────────────────────────────────
@app.exception_handler(CaseStudyNotFound)
async def _handle_case_study_not_found(request: Request, exc: CaseStudyNotFound):
    return _error_page(request, 404, str(exc))


@app.exception_handler(StarletteHTTPException)
async def _handle_http_exception(request: Request, exc: StarletteHTTPException):
    # Render a friendly page for browser navigation; keep the status code.
    return _error_page(request, exc.status_code, exc.detail or "Request error")


@app.exception_handler(Exception)
async def _handle_unhandled(request: Request, exc: Exception):
    # Last resort: show the cause instead of a bare "Internal Server Error".
    return _error_page(request, 500, f"{type(exc).__name__}: {exc}")


# ── Routers (original declaration order — do not reorder) ───────────────────
app.include_router(studies.router)
app.include_router(processes.router)
app.include_router(flows.router)
app.include_router(tcs.router)
app.include_router(scenarios.router)
app.include_router(references.router)
app.include_router(io.router)
app.include_router(elements.router)
app.include_router(scenarios.mc_router)
app.include_router(compositions.router)
app.include_router(flows.flow_data_router)


# ── Backwards-compatible re-exports ──────────────────────────────────────────
# Tests and external callers import these from systemdefiner.main.
from systemdefiner.cascades import (  # noqa: E402,F401
    _compact_process_ids,
    _delete_process_cascade,
    _next_flow_id,
    _process_name,
    _purge_flow_references,
    _rename_flow_id,
)
from systemdefiner.forms import (  # noqa: E402,F401
    _apply_extra_yaml,
    _g,
    _gf,
    _gi,
    _parse_bom_from_yaml,
    _parse_dsm,
    _parse_dsm_component,
    _parse_flowcap,
    _parse_fomp,
    _parse_lfg,
    _parse_tcs_from_yaml,
    _slug,
)
from systemdefiner.health import _UOM_OPTIONS, _model_health  # noqa: E402,F401
from systemdefiner.routers.elements import _rules_to_paths  # noqa: E402,F401
from systemdefiner.routers.flows import _input_flows  # noqa: E402,F401
from systemdefiner.scenario_params import (  # noqa: E402,F401
    _DIST_FIELDS,
    _MC_DISTRIBUTIONS,
    _MC_OPERATIONS,
    _SCENARIO_OPERATIONS,
    _SCENARIO_PARAM_TYPES,
    _build_scenario_params,
)
