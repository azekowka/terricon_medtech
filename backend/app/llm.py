"""Thin OpenAI chat-completions client (httpx). Returns None on any failure so
callers can fall back to the deterministic engine."""
from __future__ import annotations

import logging

import httpx

from .config import settings

logger = logging.getLogger("medservice.llm")


def available() -> bool:
    return bool(settings.openai_api_key)


def chat_completion(messages: list[dict], temperature: float = 0.3, max_tokens: int = 320) -> str | None:
    if not settings.openai_api_key:
        return None
    try:
        r = httpx.post(
            f"{settings.openai_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.openai_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=30.0,
        )
        if r.status_code != 200:
            logger.warning("OpenAI %s: %s", r.status_code, r.text[:200])
            return None
        return (r.json()["choices"][0]["message"]["content"] or "").strip() or None
    except Exception as exc:
        logger.warning("OpenAI call failed: %s", exc)
        return None
