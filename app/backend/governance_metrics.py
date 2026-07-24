"""Portfolio-wide governance, provenance, and business-value metrics.

Pure, read-only computation over the :class:`Store`. Every field is computed
under its own ``try/except`` with a safe default so this helper NEVER raises —
a partially-degraded store still yields a well-formed metrics document. This
powers a Responsible-AI / Executive view on the frontend.
"""

import contextlib

from .models.enums import DataSourceType
from .pipeline_value import estimate_pipeline_value

# Provenance buckets we report. Anything that isn't an explicit
# public_manual/live_grounded value is counted as synthetic.
_PROVENANCE_KEYS = (
    DataSourceType.LIVE_GROUNDED.value,
    DataSourceType.SYNTHETIC.value,
    DataSourceType.PUBLIC_MANUAL.value,
)


def _source_value(profile) -> str:
    """Normalize a profile's data_source_type to its string value."""
    raw = getattr(profile, "data_source_type", None)
    value = getattr(raw, "value", raw)
    return value if isinstance(value, str) else DataSourceType.SYNTHETIC.value


def compute_governance_metrics(store) -> dict:
    """Compute portfolio-wide governance metrics from the store.

    Read-only and fully defensive: each field falls back to a safe default on
    any error, so this function never raises.
    """
    try:
        profiles = list(store.list_profiles())
    except Exception:
        profiles = []

    total_profiles = len(profiles)

    provenance = {key: 0 for key in _PROVENANCE_KEYS}
    band_counts: dict[str, int] = {}
    scored_profiles = 0
    total_pipeline_value_eur = 0.0
    audit_event_count = 0
    live_citation_count = 0

    for profile in profiles:
        # -- provenance ---------------------------------------------------
        try:
            source = _source_value(profile)
            if source not in provenance:
                source = DataSourceType.SYNTHETIC.value
            provenance[source] += 1
        except Exception:
            provenance[DataSourceType.SYNTHETIC.value] += 1

        # -- latest score / band -----------------------------------------
        score = None
        try:
            latest = store.get_latest_score_record(profile.startup_id)
            score = latest[1] if latest else None
        except Exception:
            score = None

        try:
            if score is not None:
                scored_profiles += 1
                band_value = getattr(score.priority_band, "value", score.priority_band)
                band_key = band_value if isinstance(band_value, str) else "unscored"
            else:
                band_key = "unscored"
            band_counts[band_key] = band_counts.get(band_key, 0) + 1
        except Exception:
            band_counts["unscored"] = band_counts.get("unscored", 0) + 1

        # -- pipeline value (same estimator main.py uses) ----------------
        try:
            payment = store.get_payment_profile(profile.startup_id)
            pipeline_value = estimate_pipeline_value(
                annual_revenue_eur=profile.annual_revenue_eur,
                annual_cross_border_payment_value_eur=(
                    payment.annual_cross_border_payment_value_eur if payment else None
                ),
                priority_band=(
                    getattr(score.priority_band, "value", score.priority_band)
                    if score is not None
                    else None
                ),
            )
            total_pipeline_value_eur += pipeline_value.estimated_annual_bank_revenue_eur
        except Exception:
            pass

        # -- audit events (per-profile trail; summed) --------------------
        with contextlib.suppress(Exception):
            audit_event_count += len(store.get_audit_trail(profile.startup_id))

        # -- live citations ----------------------------------------------
        with contextlib.suppress(Exception):
            live_citation_count += len(getattr(profile, "source_citations", []) or [])

    # -- active weight version -------------------------------------------
    active_weight_version = None
    try:
        active = store.get_active_weight_config()
        if active is not None:
            active_weight_version = active.version_id
        else:
            configs = store.list_weight_configs()
            if configs:
                active_weight_version = configs[-1].version_id
    except Exception:
        active_weight_version = None

    # -- recommendations generated ---------------------------------------
    recommendations_generated = 0
    try:
        lister = getattr(store, "list_recommendations", None)
        if callable(lister):
            recommendations_generated = len(list(lister()))
        else:
            internal = getattr(store, "_recommendations", None)
            if internal is not None:
                recommendations_generated = len(internal)
    except Exception:
        recommendations_generated = 0

    return {
        "total_profiles": total_profiles,
        "scored_profiles": scored_profiles,
        "provenance": {
            "live_grounded": provenance[DataSourceType.LIVE_GROUNDED.value],
            "synthetic": provenance[DataSourceType.SYNTHETIC.value],
            "public_manual": provenance[DataSourceType.PUBLIC_MANUAL.value],
        },
        "band_counts": band_counts,
        "total_pipeline_value_eur": float(total_pipeline_value_eur),
        "audit_event_count": audit_event_count,
        "live_citation_count": live_citation_count,
        "active_weight_version": active_weight_version,
        "recommendations_generated": recommendations_generated,
        "human_approval_required": True,
    }
