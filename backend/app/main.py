import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openexec.agents import register_default_agents

from app.config import get_settings
from app.routers import agents, compare, dashboard, decisions, events, health
from app.services import orchestration


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Captures the running event loop once, at the only point guaranteed to
    # be on it, so the background-thread orchestration runner can safely
    # bridge into asyncio via loop.call_soon_threadsafe (see
    # app/services/orchestration.py and orchestration_events.py).
    orchestration.set_main_loop(asyncio.get_running_loop())
    register_default_agents()  # process-wide singleton registry; idempotent
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
