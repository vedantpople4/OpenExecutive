import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openexec.agents import register_default_agents
from openexec.ai.client import resolve_settings_path

from app.config import get_settings
from app.routers import agents, compare, dashboard, decisions, events, health
from app.services import orchestration


logger = logging.getLogger(__name__)


def probe_settings(app: FastAPI) -> None:
    """Resolve the LLM config file the agents will need at run time.

    register_default_agents() registers classes, not instances, so no AIClient
    is constructed until minutes into a run. Without this probe a bad
    WorkingDirectory surfaces as a full deliberation of fallback stub reports
    instead of a boot failure.

    Warns by default so the API still serves history and dashboard endpoints
    when the LLM is misconfigured; set OPENEXEC_REQUIRE_SETTINGS=1 (as the
    systemd unit should) to make it fatal instead.
    """
    settings = get_settings()
    path = resolve_settings_path(settings.settings_file).resolve()
    found = path.exists()
    app.state.settings_path = str(path)
    app.state.settings_found = found

    if found:
        logger.info("LLM settings found at %s", path)
        return

    message = (
        f"LLM settings not found at {path} — agents will fall back to stub "
        f"reports. Set OPENEXEC_SETTINGS_PATH to the real file."
    )
    if settings.require_settings:
        raise RuntimeError(message)
    logger.warning(message)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Captures the running event loop once, at the only point guaranteed to
    # be on it, so the background-thread orchestration runner can safely
    # bridge into asyncio via loop.call_soon_threadsafe (see
    # app/services/orchestration.py and orchestration_events.py).
    orchestration.set_main_loop(asyncio.get_running_loop())
    register_default_agents()  # process-wide singleton registry; idempotent
    probe_settings(app)
    yield


app = FastAPI(title="OpenExec API", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(agents.router)
app.include_router(decisions.router)
app.include_router(compare.router)
app.include_router(dashboard.router)
app.include_router(events.router)
