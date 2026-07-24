"""Synthetic seed data: the NovaTrade AI GmbH profile from doc §23.1,
demo users for each of the 4 RBAC roles (§23.5), and weight config v1.
All data here is synthetic and clearly flagged as such end to end.
"""
from datetime import date, datetime, timezone

from passlib.context import CryptContext

from ..models import (
    ExpansionSignal,
    PainPointProfile,
    PaymentProfile,
    Role,
    StartupProfile,
    User,
    default_weight_config,
)
from ..models.enums import DataSourceType

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

NOVATRADE_ID = "ST-001"

# created_at is pinned (not datetime.now()) so every deterministic driver that
# reasons about "freshness relative to profile creation" (see
# scoring/early_signal.py::signal_freshness_and_recurrence) produces the exact
# same score regardless of what day this seed is loaded or tested.
NOVATRADE_PROFILE = StartupProfile(
    startup_id=NOVATRADE_ID,
    name="NovaTrade AI GmbH",
    sector="B2B SaaS supply-chain analytics",
    hq_country="Germany",
    current_countries=["Germany", "Austria", "Netherlands"],
    target_countries=["Singapore", "United Kingdom"],
    growth_stage="Scaleup",
    funding_stage="Series B",
    annual_revenue_eur=18_000_000,
    expansion_timeline_months=6,
    synthetic_flag=True,
    data_source_type=DataSourceType.SYNTHETIC,
    created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
)

NOVATRADE_PAYMENT_PROFILE = PaymentProfile(
    startup_id=NOVATRADE_ID,
    annual_cross_border_payment_value_eur=6_000_000,
    monthly_payment_count_inbound=320,
    monthly_payment_count_outbound=90,
    currencies=["EUR", "GBP", "SGD", "USD"],
    payment_corridors=["DE-SG", "DE-GB", "NL-GB"],
    collection_model="Direct invoicing + marketplace collections",
    expected_growth_rate=0.35,
    current_payment_provider="fintech",
)

NOVATRADE_PAIN_POINT_PROFILE = PainPointProfile(
    startup_id=NOVATRADE_ID,
    payment_delay_issue=True,
    failed_payment_count_monthly=14,
    reconciliation_effort_hours_weekly=15.0,
    cash_visibility_gap=True,
    number_of_bank_accounts=3,
    number_of_providers=2,
    cost_pressure=True,
    cfo_urgency=True,
    provider_switch_risk=True,
)

NOVATRADE_SIGNALS = [
    ExpansionSignal(
        signal_id="SIG-001",
        startup_id=NOVATRADE_ID,
        signal_type="new_country_launch",
        country="Singapore",
        signal_date=date(2026, 6, 1),
        source_type=DataSourceType.SYNTHETIC,
        source_label="Synthetic expansion plan",
        confidence=0.9,
        evidence_note="First invoices expected in Singapore within six months.",
    ),
    ExpansionSignal(
        signal_id="SIG-002",
        startup_id=NOVATRADE_ID,
        signal_type="new_country_launch",
        country="United Kingdom",
        signal_date=date(2026, 6, 1),
        source_type=DataSourceType.SYNTHETIC,
        source_label="Synthetic expansion plan",
        confidence=0.9,
        evidence_note="UK entity setup underway alongside Singapore launch.",
    ),
    ExpansionSignal(
        signal_id="SIG-003",
        startup_id=NOVATRADE_ID,
        signal_type="international_hiring",
        country="Singapore",
        signal_date=date(2026, 5, 15),
        source_type=DataSourceType.PUBLIC_MANUAL,
        source_label="Synthetic hiring announcement",
        confidence=0.75,
        evidence_note="Country manager role posted for Singapore APAC hub.",
    ),
    ExpansionSignal(
        signal_id="SIG-004",
        startup_id=NOVATRADE_ID,
        signal_type="foreign_customer_growth",
        country="United Kingdom",
        signal_date=date(2026, 5, 1),
        source_type=DataSourceType.PUBLIC_MANUAL,
        source_label="Synthetic customer reference",
        confidence=0.7,
        evidence_note="Two new UK enterprise customers signed in the last quarter.",
    ),
]

# ---------------------------------------------------------------------------
# Additional synthetic startups (ST-002..ST-006). Same pinned-created_at
# discipline as NovaTrade so every deterministic driver is reproducible. The
# numbers are tuned so the resulting final priority bands span all four bands
# (high_priority, monitor, validate, no_immediate_action).
# ---------------------------------------------------------------------------

# ST-002: PayFlux — high-priority FinTech/payments scaleup, strong on every axis.
PAYFLUX_ID = "ST-002"
PAYFLUX_PROFILE = StartupProfile(
    startup_id=PAYFLUX_ID,
    name="PayFlux Technologies SAS",
    sector="FinTech cross-border payments",
    hq_country="France",
    current_countries=["France", "Spain", "Ireland"],
    target_countries=["Singapore", "United Kingdom", "Netherlands"],
    growth_stage="Scaleup",
    funding_stage="Series C",
    annual_revenue_eur=28_000_000,
    expansion_timeline_months=5,
    synthetic_flag=True,
    data_source_type=DataSourceType.SYNTHETIC,
    created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
)
PAYFLUX_PAYMENT_PROFILE = PaymentProfile(
    startup_id=PAYFLUX_ID,
    annual_cross_border_payment_value_eur=9_500_000,
    monthly_payment_count_inbound=360,
    monthly_payment_count_outbound=160,
    currencies=["EUR", "GBP", "SGD", "USD"],
    payment_corridors=["FR-SG", "FR-GB", "ES-GB"],
    collection_model="Platform collections + direct invoicing",
    expected_growth_rate=0.42,
    current_payment_provider="fintech",
)
PAYFLUX_PAIN_POINT_PROFILE = PainPointProfile(
    startup_id=PAYFLUX_ID,
    payment_delay_issue=True,
    failed_payment_count_monthly=16,
    reconciliation_effort_hours_weekly=18.0,
    cash_visibility_gap=True,
    number_of_bank_accounts=4,
    number_of_providers=3,
    cost_pressure=True,
    cfo_urgency=True,
    provider_switch_risk=True,
)
PAYFLUX_SIGNALS = [
    ExpansionSignal(
        signal_id="SIG-101",
        startup_id=PAYFLUX_ID,
        signal_type="new_country_launch",
        country="Singapore",
        signal_date=date(2026, 6, 5),
        source_type=DataSourceType.SYNTHETIC,
        source_label="Synthetic expansion plan",
        confidence=0.92,
        evidence_note="APAC launch scoped with first flows into Singapore.",
    ),
    ExpansionSignal(
        signal_id="SIG-102",
        startup_id=PAYFLUX_ID,
        signal_type="new_country_launch",
        country="United Kingdom",
        signal_date=date(2026, 6, 5),
        source_type=DataSourceType.SYNTHETIC,
        source_label="Synthetic expansion plan",
        confidence=0.9,
        evidence_note="UK entity incorporated ahead of Q3 go-live.",
    ),
    ExpansionSignal(
        signal_id="SIG-103",
        startup_id=PAYFLUX_ID,
        signal_type="international_hiring",
        country="Singapore",
        signal_date=date(2026, 6, 1),
        source_type=DataSourceType.PUBLIC_MANUAL,
        source_label="Synthetic hiring announcement",
        confidence=0.85,
        evidence_note="Regional treasury and country-manager roles posted for APAC.",
    ),
    ExpansionSignal(
        signal_id="SIG-104",
        startup_id=PAYFLUX_ID,
        signal_type="foreign_customer_growth",
        country="United Kingdom",
        signal_date=date(2026, 5, 25),
        source_type=DataSourceType.PUBLIC_MANUAL,
        source_label="Synthetic customer reference",
        confidence=0.82,
        evidence_note="Several UK enterprise logos onboarded this quarter.",
    ),
]

# ST-003: VerdeGrid — monitor-band ClimateTech scaleup, solid but not top-tier.
VERDEGRID_ID = "ST-003"
VERDEGRID_PROFILE = StartupProfile(
    startup_id=VERDEGRID_ID,
    name="VerdeGrid Energy BV",
    sector="ClimateTech grid optimisation",
    hq_country="Netherlands",
    current_countries=["Netherlands", "Germany"],
    target_countries=["Denmark", "Sweden"],
    growth_stage="Scaleup",
    funding_stage="Series B",
    annual_revenue_eur=12_000_000,
    expansion_timeline_months=7,
    synthetic_flag=True,
    data_source_type=DataSourceType.SYNTHETIC,
    created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
)
VERDEGRID_PAYMENT_PROFILE = PaymentProfile(
    startup_id=VERDEGRID_ID,
    annual_cross_border_payment_value_eur=4_000_000,
    monthly_payment_count_inbound=150,
    monthly_payment_count_outbound=60,
    currencies=["EUR", "DKK", "SEK"],
    payment_corridors=["NL-DK", "NL-SE"],
    collection_model="Direct invoicing",
    expected_growth_rate=0.30,
    current_payment_provider="fintech",
)
VERDEGRID_PAIN_POINT_PROFILE = PainPointProfile(
    startup_id=VERDEGRID_ID,
    payment_delay_issue=True,
    failed_payment_count_monthly=8,
    reconciliation_effort_hours_weekly=10.0,
    cash_visibility_gap=True,
    number_of_bank_accounts=3,
    number_of_providers=2,
    cost_pressure=True,
    cfo_urgency=True,
    provider_switch_risk=True,
)
VERDEGRID_SIGNALS = [
    ExpansionSignal(
        signal_id="SIG-201",
        startup_id=VERDEGRID_ID,
        signal_type="new_country_launch",
        country="Denmark",
        signal_date=date(2026, 6, 1),
        source_type=DataSourceType.SYNTHETIC,
        source_label="Synthetic expansion plan",
        confidence=0.8,
        evidence_note="Nordic rollout beginning with Denmark.",
    ),
    ExpansionSignal(
        signal_id="SIG-202",
        startup_id=VERDEGRID_ID,
        signal_type="international_hiring",
        country="Sweden",
        signal_date=date(2026, 5, 20),
        source_type=DataSourceType.PUBLIC_MANUAL,
        source_label="Synthetic hiring announcement",
        confidence=0.7,
        evidence_note="Grid engineers being hired for the Swedish market.",
    ),
]

# ST-004: HelioHealth — validate-band HealthTech, moderate footprint and pain.
HELIOHEALTH_ID = "ST-004"
HELIOHEALTH_PROFILE = StartupProfile(
    startup_id=HELIOHEALTH_ID,
    name="HelioHealth Systems Oy",
    sector="HealthTech clinical workflow",
    hq_country="Sweden",
    current_countries=["Sweden"],
    target_countries=["Denmark"],
    growth_stage="Growth",
    funding_stage="Series A",
    annual_revenue_eur=5_000_000,
    expansion_timeline_months=12,
    synthetic_flag=True,
    data_source_type=DataSourceType.SYNTHETIC,
    created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
)
HELIOHEALTH_PAYMENT_PROFILE = PaymentProfile(
    startup_id=HELIOHEALTH_ID,
    annual_cross_border_payment_value_eur=1_600_000,
    monthly_payment_count_inbound=70,
    monthly_payment_count_outbound=20,
    currencies=["EUR", "DKK"],
    payment_corridors=["SE-DK"],
    collection_model="Direct invoicing",
    expected_growth_rate=0.18,
    current_payment_provider="fintech",
)
HELIOHEALTH_PAIN_POINT_PROFILE = PainPointProfile(
    startup_id=HELIOHEALTH_ID,
    payment_delay_issue=False,
    failed_payment_count_monthly=3,
    reconciliation_effort_hours_weekly=4.0,
    cash_visibility_gap=False,
    number_of_bank_accounts=2,
    number_of_providers=2,
    cost_pressure=True,
    cfo_urgency=False,
    provider_switch_risk=False,
)
HELIOHEALTH_SIGNALS = [
    ExpansionSignal(
        signal_id="SIG-301",
        startup_id=HELIOHEALTH_ID,
        signal_type="international_hiring",
        country="Denmark",
        signal_date=date(2026, 4, 10),
        source_type=DataSourceType.PUBLIC_MANUAL,
        source_label="Synthetic hiring announcement",
        confidence=0.6,
        evidence_note="Early clinical-partnerships role posted for Denmark.",
    ),
]

# ST-005: Quantumly — no-immediate-action DeepTech, tiny cross-border footprint.
QUANTUMLY_ID = "ST-005"
QUANTUMLY_PROFILE = StartupProfile(
    startup_id=QUANTUMLY_ID,
    name="Quantumly Labs GmbH",
    sector="DeepTech quantum sensing",
    hq_country="Germany",
    current_countries=["Germany"],
    target_countries=[],
    growth_stage="Early-stage",
    funding_stage="Seed",
    annual_revenue_eur=600_000,
    expansion_timeline_months=18,
    synthetic_flag=True,
    data_source_type=DataSourceType.SYNTHETIC,
    created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
)
QUANTUMLY_PAYMENT_PROFILE = PaymentProfile(
    startup_id=QUANTUMLY_ID,
    annual_cross_border_payment_value_eur=120_000,
    monthly_payment_count_inbound=6,
    monthly_payment_count_outbound=2,
    currencies=["EUR"],
    payment_corridors=[],
    collection_model="Grant-funded, minimal invoicing",
    expected_growth_rate=0.05,
    current_payment_provider="none",
)
QUANTUMLY_PAIN_POINT_PROFILE = PainPointProfile(
    startup_id=QUANTUMLY_ID,
    payment_delay_issue=False,
    failed_payment_count_monthly=0,
    reconciliation_effort_hours_weekly=1.0,
    cash_visibility_gap=False,
    number_of_bank_accounts=1,
    number_of_providers=1,
    cost_pressure=False,
    cfo_urgency=False,
    provider_switch_risk=False,
)
QUANTUMLY_SIGNALS = [
    ExpansionSignal(
        signal_id="SIG-401",
        startup_id=QUANTUMLY_ID,
        signal_type="funding_event",
        country=None,
        signal_date=date(2026, 1, 15),
        source_type=DataSourceType.PUBLIC_MANUAL,
        source_label="Synthetic funding note",
        confidence=0.4,
        evidence_note="Small seed extension closed earlier in the year.",
    ),
]

# ST-006: MercatoB2B — monitor-band B2B marketplace, mid-size and active.
MERCATO_ID = "ST-006"
MERCATO_PROFILE = StartupProfile(
    startup_id=MERCATO_ID,
    name="MercatoB2B Srl",
    sector="B2B marketplace",
    hq_country="Italy",
    current_countries=["Italy", "Spain"],
    target_countries=["United Kingdom", "Germany"],
    growth_stage="Scaleup",
    funding_stage="Series B",
    annual_revenue_eur=15_000_000,
    expansion_timeline_months=6,
    synthetic_flag=True,
    data_source_type=DataSourceType.SYNTHETIC,
    created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
)
MERCATO_PAYMENT_PROFILE = PaymentProfile(
    startup_id=MERCATO_ID,
    annual_cross_border_payment_value_eur=4_500_000,
    monthly_payment_count_inbound=180,
    monthly_payment_count_outbound=70,
    currencies=["EUR", "GBP", "USD"],
    payment_corridors=["IT-GB", "ES-GB"],
    collection_model="Marketplace collections",
    expected_growth_rate=0.28,
    current_payment_provider="fintech",
)
MERCATO_PAIN_POINT_PROFILE = PainPointProfile(
    startup_id=MERCATO_ID,
    payment_delay_issue=True,
    failed_payment_count_monthly=9,
    reconciliation_effort_hours_weekly=11.0,
    cash_visibility_gap=True,
    number_of_bank_accounts=3,
    number_of_providers=2,
    cost_pressure=True,
    cfo_urgency=False,
    provider_switch_risk=True,
)
MERCATO_SIGNALS = [
    ExpansionSignal(
        signal_id="SIG-501",
        startup_id=MERCATO_ID,
        signal_type="new_country_launch",
        country="United Kingdom",
        signal_date=date(2026, 5, 28),
        source_type=DataSourceType.SYNTHETIC,
        source_label="Synthetic expansion plan",
        confidence=0.78,
        evidence_note="UK marketplace launch scheduled within two quarters.",
    ),
    ExpansionSignal(
        signal_id="SIG-502",
        startup_id=MERCATO_ID,
        signal_type="foreign_customer_growth",
        country="Germany",
        signal_date=date(2026, 5, 10),
        source_type=DataSourceType.PUBLIC_MANUAL,
        source_label="Synthetic customer reference",
        confidence=0.68,
        evidence_note="German sellers joining the marketplace ahead of launch.",
    ),
]

# Every startup grouped as (profile, payment, pain, signals) so main.py can seed
# them in one idempotent loop. NovaTrade stays first so ST-001 remains the hero.
SEED_PROFILES = [
    (NOVATRADE_PROFILE, NOVATRADE_PAYMENT_PROFILE, NOVATRADE_PAIN_POINT_PROFILE, NOVATRADE_SIGNALS),
    (PAYFLUX_PROFILE, PAYFLUX_PAYMENT_PROFILE, PAYFLUX_PAIN_POINT_PROFILE, PAYFLUX_SIGNALS),
    (VERDEGRID_PROFILE, VERDEGRID_PAYMENT_PROFILE, VERDEGRID_PAIN_POINT_PROFILE, VERDEGRID_SIGNALS),
    (HELIOHEALTH_PROFILE, HELIOHEALTH_PAYMENT_PROFILE, HELIOHEALTH_PAIN_POINT_PROFILE, HELIOHEALTH_SIGNALS),
    (QUANTUMLY_PROFILE, QUANTUMLY_PAYMENT_PROFILE, QUANTUMLY_PAIN_POINT_PROFILE, QUANTUMLY_SIGNALS),
    (MERCATO_PROFILE, MERCATO_PAYMENT_PROFILE, MERCATO_PAIN_POINT_PROFILE, MERCATO_SIGNALS),
]

DEMO_USERS = [
    User(
        user_id="user-rm-1",
        email="anna.schmidt@launchpad.demo",
        name="Anna Schmidt",
        role=Role.RM,
        password_hash=_pwd.hash("demo1234"),
    ),
    User(
        user_id="user-po-1",
        email="priya.nair@launchpad.demo",
        name="Priya Nair",
        role=Role.PRODUCT_OWNER,
        password_hash=_pwd.hash("demo1234"),
    ),
    User(
        user_id="user-cr-1",
        email="wei.chen@launchpad.demo",
        name="Wei Chen",
        role=Role.CONTROL_REVIEWER,
        password_hash=_pwd.hash("demo1234"),
    ),
    User(
        user_id="user-admin-1",
        email="admin@launchpad.demo",
        name="Admin User",
        role=Role.ADMIN,
        password_hash=_pwd.hash("demo1234"),
    ),
]

DEFAULT_WEIGHT_CONFIG = default_weight_config(version_id="v1", owner="system")
