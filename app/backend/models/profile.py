from datetime import date, datetime, timezone

from pydantic import BaseModel, Field, field_validator, model_validator

from .enums import DataSourceType

ISO_CURRENCY_CODES = {
    "EUR", "USD", "GBP", "SGD", "CHF", "JPY", "AUD", "CAD", "SEK", "NOK",
    "DKK", "PLN", "CZK", "HUF", "HKD", "CNY", "INR", "AED", "ZAR", "BRL",
}


class StartupProfile(BaseModel):
    startup_id: str
    name: str
    sector: str
    hq_country: str
    current_countries: list[str] = Field(default_factory=list)
    target_countries: list[str] = Field(default_factory=list)
    growth_stage: str
    funding_stage: str
    annual_revenue_eur: float
    expansion_timeline_months: int | None = None
    synthetic_flag: bool = True
    data_source_type: DataSourceType = DataSourceType.SYNTHETIC
    # Public source URLs cited by Google Search grounding when this profile was
    # discovered live. Empty for synthetic/manual profiles.
    source_citations: list[str] = Field(default_factory=list)
    # One-line note on what public evidence backs the estimated figures, so a
    # discovered profile is never presented as if its numbers were confirmed.
    discovery_note: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("annual_revenue_eur")
    @classmethod
    def revenue_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("annual_revenue_eur cannot be negative")
        return v

    @field_validator("target_countries")
    @classmethod
    def target_countries_required_if_expansion(cls, v: list[str], info) -> list[str]:
        # doc §23.9: target country cannot be blank if an expansion signal exists.
        # Enforced at the profile+signal join in validation.py, not here in isolation.
        return v


# doc §23.9: "target country cannot be blank if expansion signal exists" — these
# signal types are inherently country-specific, so `country` is mandatory for them.
COUNTRY_REQUIRED_SIGNAL_TYPES = {"new_country_launch", "international_hiring", "foreign_customer_growth"}


class ExpansionSignal(BaseModel):
    signal_id: str
    startup_id: str
    signal_type: str  # e.g. new_country_launch, international_hiring, foreign_customer_growth,
    # supplier_expansion, funding_event
    country: str | None = None
    signal_date: date
    source_type: DataSourceType
    source_label: str
    confidence: float  # 0..1
    evidence_note: str = ""

    @field_validator("confidence")
    @classmethod
    def confidence_in_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0 and 1")
        return v

    @model_validator(mode="after")
    def country_required_for_expansion_signals(self) -> "ExpansionSignal":
        if self.signal_type in COUNTRY_REQUIRED_SIGNAL_TYPES and not self.country:
            raise ValueError(
                f"country cannot be blank for signal_type='{self.signal_type}' (doc §23.9)"
            )
        return self


class PaymentProfile(BaseModel):
    startup_id: str
    annual_cross_border_payment_value_eur: float
    monthly_payment_count_inbound: int
    monthly_payment_count_outbound: int
    currencies: list[str] = Field(default_factory=list)
    payment_corridors: list[str] = Field(default_factory=list)
    collection_model: str = ""
    expected_growth_rate: float = 0.0
    current_payment_provider: str = ""  # "fintech" | "bank" | "none"

    @field_validator("annual_cross_border_payment_value_eur")
    @classmethod
    def value_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("annual_cross_border_payment_value_eur cannot be negative")
        return v

    @field_validator("currencies")
    @classmethod
    def currencies_must_be_iso(cls, v: list[str]) -> list[str]:
        bad = [c for c in v if c.upper() not in ISO_CURRENCY_CODES]
        if bad:
            raise ValueError(f"non-ISO currency code(s): {bad}")
        return [c.upper() for c in v]


class PainPointProfile(BaseModel):
    startup_id: str
    payment_delay_issue: bool = False
    failed_payment_count_monthly: int = 0
    reconciliation_effort_hours_weekly: float = 0.0
    cash_visibility_gap: bool = False
    number_of_bank_accounts: int = 1
    number_of_providers: int = 1
    cost_pressure: bool = False
    cfo_urgency: bool = False
    provider_switch_risk: bool = False
