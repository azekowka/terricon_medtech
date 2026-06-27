"""MedServicePrice.kz API — FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import settings
from .db import SessionLocal, init_db
from .routers import admin, clinics, doctors, history, map as map_router, meta, search, services, subscriptions
from .scheduler import shutdown_scheduler, start_scheduler
from .seeding import bootstrap_if_empty

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medservice")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        result = bootstrap_if_empty(db)
        if result:
            logger.info("Bootstrapped database: %s", result)
    finally:
        db.close()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="MedServicePrice.kz API",
    version=__version__,
    description="Агрегатор цен на медицинские услуги в Казахстане (хакатон MVP).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (meta, search, services, clinics, history, admin, subscriptions, doctors, map_router):
    app.include_router(r.router)


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok", "version": __version__}


@app.get("/", tags=["meta"])
def root():
    return {
        "service": "MedServicePrice.kz API",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/health",
    }
