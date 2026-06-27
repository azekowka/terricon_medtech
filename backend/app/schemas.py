"""Pydantic request/response schemas (request bodies + a few typed responses)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    sources: list[str] | None = Field(
        default=None, description="Source keys to run; null = seed source only"
    )
    include_live: bool = Field(default=False, description="Also run live web scrapers")


class SubscriptionCreate(BaseModel):
    email: str
    service_id: str
    clinic_id: str | None = None
    target_price_kzt: float | None = None


class ResolveUnmatched(BaseModel):
    service_id: str
    add_synonym: bool = True


class ChatTurn(BaseModel):
    role: str  # "user" | "bot"
    text: str


class ChatRequest(BaseModel):
    message: str
    locale: str = "ru"
    history: list[ChatTurn] = []


class ServiceOut(BaseModel):
    id: str
    code: str
    name: str
    category: str
    category_label: str | None = None
    synonyms: list[str] = []
    duration_days: int | None = None
    offers_count: int = 0
