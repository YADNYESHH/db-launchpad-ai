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
