from datetime import date

import pytest
from pydantic import ValidationError

from ..models.enums import DataSourceType
from ..models.profile import ExpansionSignal, PaymentProfile, StartupProfile


def test_negative_payment_value_rejected():
    with pytest.raises(ValidationError):
        PaymentProfile(
            startup_id="ST-X",
            annual_cross_border_payment_value_eur=-1,
            monthly_payment_count_inbound=0,
            monthly_payment_count_outbound=0,
        )


def test_negative_revenue_rejected():
    with pytest.raises(ValidationError):
        StartupProfile(
            startup_id="ST-X",
            name="X",
            sector="X",
            hq_country="Germany",
            growth_stage="Scaleup",
            funding_stage="Series A",
            annual_revenue_eur=-100,
        )


def test_non_iso_currency_rejected():
    with pytest.raises(ValidationError):
        PaymentProfile(
            startup_id="ST-X",
            annual_cross_border_payment_value_eur=1000,
            monthly_payment_count_inbound=1,
            monthly_payment_count_outbound=1,
            currencies=["EUR", "ZZZ"],
        )


def test_country_required_for_expansion_signal():
    with pytest.raises(ValidationError):
        ExpansionSignal(
            signal_id="SIG-X",
            startup_id="ST-X",
            signal_type="new_country_launch",
            country=None,
            signal_date=date(2026, 1, 1),
            source_type=DataSourceType.SYNTHETIC,
            source_label="test",
            confidence=0.9,
        )


def test_funding_event_signal_does_not_require_country():
    # funding_event is not in COUNTRY_REQUIRED_SIGNAL_TYPES
    signal = ExpansionSignal(
        signal_id="SIG-X",
        startup_id="ST-X",
        signal_type="funding_event",
        country=None,
        signal_date=date(2026, 1, 1),
        source_type=DataSourceType.SYNTHETIC,
        source_label="test",
        confidence=0.9,
    )
    assert signal.country is None


def test_synthetic_flag_defaults_true():
    profile = StartupProfile(
        startup_id="ST-X",
        name="X",
        sector="X",
        hq_country="Germany",
        growth_stage="Scaleup",
        funding_stage="Series A",
        annual_revenue_eur=1000,
    )
    assert profile.synthetic_flag is True
    assert profile.data_source_type == DataSourceType.SYNTHETIC
