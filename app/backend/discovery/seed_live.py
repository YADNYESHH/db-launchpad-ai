"""Live-first portfolio seeding.

Populates the store with REAL startups across several sectors by reusing the
existing grounded discovery pipeline (``run_discovery``). Honesty is paramount:
this never fabricates data. Real startups are persisted exactly as the
discovery/scoring pipeline produces them (flagged LIVE_GROUNDED with citations).
If a live discovery call fails or returns nothing (e.g. no GCP creds in CI),
the failure is recorded in ``reasons`` and the caller is expected to fall back
to the synthetic seed so the demo never breaks.
"""
from __future__ import annotations

import logging

from ..store import Store

logger = logging.getLogger(__name__)

# A small, cross-border-payments-relevant default sector list. Kept to a
# single sector by default so one "populate" click reliably completes well
# under Cloud Run's request timeout even if grounded calls need retries.
# Callers may pass more sectors explicitly (best run as several smaller
# requests, not one large one).
DEFAULT_SECTORS: list[str] = [
    "cross-border B2B payments",
]


def seed_live_portfolio(
    store: Store,
    actor: str,
    sectors: list[str] | None = None,
    per_sector: int = 2,
) -> dict:
    """Discover and persist real startups across ``sectors`` via ``run_discovery``.

    Fully defensive: any exception in a single sector is caught and recorded in
    ``reasons`` so one failing sector never aborts the rest. Returns a summary::

        {
            "added": int,           # number of newly-discovered real startups
            "sectors": list[str],   # sectors that were attempted
            "reasons": list[str],   # per-sector empty/failure explanations
            "live": bool,           # True if >= 1 real startup was added
        }
    """
    # Imported lazily so tests can monkeypatch this module's ``run_discovery``
    # reference, and so importing the module never triggers discovery imports.
    from ..orchestrator import run_discovery

    chosen = sectors or list(DEFAULT_SECTORS)
    limit = max(1, per_sector)

    added = 0
    reasons: list[str] = []

    for sector in chosen:
        try:
            result = run_discovery(store, sector, actor=actor, limit=limit)
        except Exception as exc:  # defensive: one sector must not abort the rest
            logger.exception("Live seed failed for sector %s", sector)
            reasons.append(f"{sector}: error - {exc}")
            continue

        discovered = (result or {}).get("discovered") or []
        newly_added = sum(1 for d in discovered if d.get("status") == "discovered")
        added += newly_added

        reason = (result or {}).get("reason")
        if reason:
            reasons.append(f"{sector}: {reason}")
        elif newly_added == 0:
            reasons.append(f"{sector}: no new startups added")

    return {
        "added": added,
        "sectors": chosen,
        "reasons": reasons,
        "live": added > 0,
    }
