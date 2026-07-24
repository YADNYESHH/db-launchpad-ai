"""Maps a live-discovered startup into the scoring pipeline's models.

Honest-by-construction:
- The StartupProfile and ExpansionSignals come straight from public discovery.
- The PaymentProfile is *estimated* from public signals (revenue, number of
  markets) and flagged as an estimate in the discovery note. Estimation is
  explicit and conservative, never presented as confirmed client data.
- The PainPointProfile is deliberately NOT fabricated. Pain-point detail
  (failed payments, reconciliation effort, CFO urgency) is genuinely private
  and unknowable from public search, so it is left absent. The existing
  missing-data governance then correctly caps a discovered startup below
  high-priority until real client engagement fills that gap - which is the
  honest, defensible behaviour to demo on real companies.
"""
import re
import uuid
from datetime import datetime, timezone

from ..models.enums import DataSourceType
from ..models.profile import ExpansionSignal, PaymentProfile, StartupProfile
from .agent import DiscoveredStartup

# Rough public-signal currency inference by country (home currency for cross-border pairs).
_COUNTRY_CURRENCY = {
    "germany": "EUR", "austria": "EUR", "netherlands": "EUR", "france": "EUR",
    "ireland": "EUR", "spain": "EUR", "italy": "EUR", "portugal": "EUR",
    "united kingdom": "GBP", "uk": "GBP", "england": "GBP",
    "united states": "USD", "usa": "USD", "us": "USD",
    "singapore": "SGD", "switzerland": "CHF", "sweden": "SEK", "denmark": "DKK",
    "norway": "NOK", "poland": "PLN", "japan": "JPY", "australia": "AUD",
    "canada": "CAD", "india": "INR", "hong kong": "HKD", "china": "CNY", "uae": "AED",
}

# Estimated share of revenue that flows cross-border once a company is expanding.
_CROSS_BORDER_REVENUE_SHARE = 0.30


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:40] or "startup"


def _currencies_for(countries: list[str]) -> list[str]:
    currencies = ["EUR"]
    for c in countries:
        cur = _COUNTRY_CURRENCY.get(c.strip().lower())
        if cur and cur not in currencies:
            currencies.append(cur)
    return currencies


_VALID_SIGNAL_TYPES = {
    "new_country_launch", "international_hiring", "foreign_customer_growth",
    "supplier_expansion", "funding_event",
}
_COUNTRY_REQUIRED = {"new_country_launch", "international_hiring", "foreign_customer_growth"}


def to_models(
    discovered: DiscoveredStartup,
) -> tuple[StartupProfile, PaymentProfile | None, list[ExpansionSignal]]:
    startup_id = f"LIVE-{_slugify(discovered.name)}-{uuid.uuid4().hex[:6]}"
    created = datetime.now(timezone.utc)

    note = discovered.discovery_note or "Discovered via live public search; figures are conservative estimates."
    if "estimate" not in note.lower():
        note += " Financial figures are public estimates, not confirmed."

    profile = StartupProfile(
        startup_id=startup_id,
        name=discovered.name,
        sector=discovered.sector,
        hq_country=discovered.hq_country,
        current_countries=discovered.current_countries,
        target_countries=discovered.target_countries,
        growth_stage=discovered.growth_stage,
        funding_stage=discovered.funding_stage,
        annual_revenue_eur=discovered.estimated_annual_revenue_eur,
        expansion_timeline_months=discovered.expansion_timeline_months,
        synthetic_flag=False,
        data_source_type=DataSourceType.LIVE_GROUNDED,
        source_citations=discovered.source_citations,
        discovery_note=note,
        created_at=created,
    )

    signals: list[ExpansionSignal] = []
    for i, s in enumerate(discovered.expansion_signals):
        stype = str(s.get("signal_type", "")).strip()
        if stype not in _VALID_SIGNAL_TYPES:
            continue
        country = s.get("country") or None
        if stype in _COUNTRY_REQUIRED and not country:
            # Backfill from target markets so the record stays valid; skip if none.
            country = discovered.target_countries[0] if discovered.target_countries else None
            if not country:
                continue
        try:
            confidence = float(s.get("confidence", 0.6) or 0.6)
        except (TypeError, ValueError):
            confidence = 0.6
        confidence = min(1.0, max(0.0, confidence))
        signals.append(
            ExpansionSignal(
                signal_id=f"{startup_id}-SIG-{i + 1}",
                startup_id=startup_id,
                signal_type=stype,
                country=str(country).strip() if country else None,
                signal_date=created.date(),
                source_type=DataSourceType.LIVE_GROUNDED,
                source_label="Live public search (grounded)",
                confidence=confidence,
                evidence_note=str(s.get("evidence_note", "")).strip(),
            )
        )

    # Estimated payment profile from public signals only (revenue + market count).
    payment: PaymentProfile | None = None
    if discovered.estimated_annual_revenue_eur > 0:
        est_cross_border = discovered.estimated_annual_revenue_eur * _CROSS_BORDER_REVENUE_SHARE
        n_markets = max(1, len(discovered.current_countries) + len(discovered.target_countries))
        payment = PaymentProfile(
            startup_id=startup_id,
            annual_cross_border_payment_value_eur=round(est_cross_border, 2),
            monthly_payment_count_inbound=n_markets * 40,
            monthly_payment_count_outbound=n_markets * 15,
            currencies=_currencies_for(discovered.current_countries + discovered.target_countries),
            payment_corridors=[
                f"{discovered.hq_country[:2].upper()}-{c[:2].upper()}" for c in discovered.target_countries[:3]
            ],
            collection_model="Estimated from public expansion signals",
            expected_growth_rate=0.25,
            current_payment_provider="unknown",
        )

    return profile, payment, signals
