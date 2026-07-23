"""Early-Signal Detectability driver functions (doc pp. 17-18).

Signal-based drivers: absence of *that specific signal type* is a genuine,
valid low score (not missing data). Only a fully empty `ctx.signals` list
(no signal ingestion happened at all) is treated as missing data.
"""
from .context import ScoringContext, DriverResult, clamp


def _avg_confidence(ctx: ScoringContext, signal_type: str) -> float:
    matches = ctx.signals_of_type(signal_type)
    if not matches:
        return 0.0
    return sum(s.confidence for s in matches) / len(matches)


def expansion_announcement_visibility(ctx: ScoringContext) -> DriverResult:
    if not ctx.signals:
        return DriverResult(0, "No signal data ingested for this startup.", missing_data=True)
    conf = _avg_confidence(ctx, "new_country_launch")
    n = len(ctx.signals_of_type("new_country_launch"))
    return DriverResult(clamp(conf * 100), f"{n} expansion-announcement signal(s), avg confidence {conf:.2f}.")


def international_hiring_signal(ctx: ScoringContext) -> DriverResult:
    if not ctx.signals:
        return DriverResult(0, "No signal data ingested for this startup.", missing_data=True)
    conf = _avg_confidence(ctx, "international_hiring")
    n = len(ctx.signals_of_type("international_hiring"))
    return DriverResult(clamp(conf * 100), f"{n} international-hiring signal(s), avg confidence {conf:.2f}.")


def foreign_customer_growth_signal(ctx: ScoringContext) -> DriverResult:
    if not ctx.signals:
        return DriverResult(0, "No signal data ingested for this startup.", missing_data=True)
    conf = _avg_confidence(ctx, "foreign_customer_growth")
    n = len(ctx.signals_of_type("foreign_customer_growth"))
    return DriverResult(clamp(conf * 100), f"{n} foreign-customer-growth signal(s), avg confidence {conf:.2f}.")


def supplier_and_procurement_signal(ctx: ScoringContext) -> DriverResult:
    if not ctx.signals:
        return DriverResult(0, "No signal data ingested for this startup.", missing_data=True)
    conf = _avg_confidence(ctx, "supplier_expansion")
    n = len(ctx.signals_of_type("supplier_expansion"))
    return DriverResult(clamp(conf * 100), f"{n} supplier/procurement signal(s), avg confidence {conf:.2f}.")


def funding_and_growth_event_timing(ctx: ScoringContext) -> DriverResult:
    funding_signals = ctx.signals_of_type("funding_event")
    if funding_signals:
        conf = _avg_confidence(ctx, "funding_event")
        return DriverResult(clamp(conf * 100), f"{len(funding_signals)} funding-event signal(s).")
    priority_stages = {"seed", "series a", "series b", "series c"}
    score = 60 if ctx.profile.funding_stage.lower() in priority_stages else 30
    return DriverResult(score, f"No funding-event signal; using funding_stage='{ctx.profile.funding_stage}' as proxy.")


def timing_window_before_client_decision(ctx: ScoringContext) -> DriverResult:
    months = ctx.profile.expansion_timeline_months
    if months is None:
        return DriverResult(0, "No expansion timeline on file.", missing_data=True)
    if months < 2:
        score = 40  # decision may already be locked in
    elif 2 <= months <= 9:
        score = 90  # a real window to engage before the decision
    else:
        score = 60  # far out, lower urgency
    return DriverResult(score, f"Expansion timeline of {months} months before go-live.")


def signal_freshness_and_recurrence(ctx: ScoringContext) -> DriverResult:
    if not ctx.signals:
        return DriverResult(0, "No signal data ingested for this startup.", missing_data=True)
    # Deterministic freshness proxy: recency of each signal relative to the
    # profile's own created_at (not wall-clock "now"), so the score does not
    # silently drift as real-world time passes while the record is unchanged.
    ref_date = ctx.profile.created_at.date()
    ages_days = [(ref_date - s.signal_date).days for s in ctx.signals]
    avg_age = sum(ages_days) / len(ages_days)
    score = clamp(100 - avg_age)  # loses ~1 point per day of average age, floored at 0
    return DriverResult(
        score, f"{len(ctx.signals)} signals, average age {avg_age:.0f} days relative to profile creation."
    )


DRIVER_FUNCTIONS = {
    "expansion_announcement_visibility": expansion_announcement_visibility,
    "international_hiring_signal": international_hiring_signal,
    "foreign_customer_growth_signal": foreign_customer_growth_signal,
    "supplier_and_procurement_signal": supplier_and_procurement_signal,
    "funding_and_growth_event_timing": funding_and_growth_event_timing,
    "timing_window_before_client_decision": timing_window_before_client_decision,
    "signal_freshness_and_recurrence": signal_freshness_and_recurrence,
}
