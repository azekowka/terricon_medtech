"""Database bootstrap — builds everything FROM real parsed data (TZ 3.2).

No prepared dictionary file, no synthetic prices. On an empty DB we:
  1. load the scraped doctor / illness catalogs (real idoctor data, for /doctors
     and /lechenie), and
  2. run the full real parsing pipeline (collect real sources → build the services
     dictionary from the collected names → normalize prices).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from .parsers.pipeline import run_full
from .parsers.registry import LOCAL_SOURCES


def bootstrap_if_empty(db: Session) -> dict | None:
    """On first boot, populate doctors/illnesses and run the real pipeline."""
    from .doctors_loader import load_doctors
    from .illness_loader import load_illnesses
    from .models import Doctor, Illness, Price

    result: dict = {}

    # 1. scraped catalogs (real idoctor data) — power /doctors and /lechenie,
    #    and the idoctor price source derives clinics+visit prices from the same file.
    if db.query(Doctor).count() == 0:
        n_doctors = load_doctors(db)
        if n_doctors:
            result["doctors_loaded"] = n_doctors
    if db.query(Illness).count() == 0:
        n_ill = load_illnesses(db)
        if n_ill:
            result["illnesses_loaded"] = n_ill

    # 2. real parsing pipeline: collect → build dictionary → normalize
    if db.query(Price).count() == 0:
        result.update(run_full(db, LOCAL_SOURCES))

    return result or None
