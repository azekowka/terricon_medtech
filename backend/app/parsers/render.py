"""Lazy, shared headless-browser fetch (Playwright) for JS / anti-bot sites.

Imported lazily so the app runs without Playwright installed — if it is missing
or the browser cannot launch, `fetch_rendered` simply returns None and the live
scraper falls back to its httpx result (fault tolerance, TZ 4). A single browser
is reused across requests within a process.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("medservice.render")

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 MedServicePriceBot/1.0"
)
_state: dict = {"pw": None, "browser": None, "failed": False}


def available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401

        return True
    except Exception:
        return False


def _ensure_browser():
    if _state["browser"] is not None:
        return _state["browser"]
    if _state["failed"]:
        return None
    try:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        _state["pw"], _state["browser"] = pw, browser
        return browser
    except Exception as exc:  # browser binary missing, etc.
        logger.warning("Playwright unavailable: %s", exc)
        _state["failed"] = True
        return None


def fetch_rendered(url: str, timeout_ms: int = 25000, wait_selector: str | None = None,
                   settle_ms: int = 1200) -> str | None:
    """Return fully-rendered HTML for `url`, or None on any failure."""
    browser = _ensure_browser()
    if browser is None:
        return None
    ctx = page = None
    try:
        ctx = browser.new_context(user_agent=_UA, locale="ru-RU",
                                  viewport={"width": 1366, "height": 900})
        page = ctx.new_page()
        page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
        if wait_selector:
            try:
                page.wait_for_selector(wait_selector, timeout=6000)
            except Exception:
                pass
        page.wait_for_timeout(settle_ms)
        return page.content()
    except Exception as exc:
        logger.info("render failed for %s: %s", url, exc)
        return None
    finally:
        try:
            if page:
                page.close()
            if ctx:
                ctx.close()
        except Exception:
            pass


def shutdown_render() -> None:
    try:
        if _state["browser"]:
            _state["browser"].close()
        if _state["pw"]:
            _state["pw"].stop()
    except Exception:
        pass
    _state["pw"] = _state["browser"] = None
