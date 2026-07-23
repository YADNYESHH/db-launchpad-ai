from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

# Driver weight tables transcribed verbatim from the LaunchPad AI concept document
# (pp. 14-23). Every list of (driver_name, weight) sums to 100.
#
# NOTE on control_implementation_feasibility: the document names this as a final
# rollup component (§21, §23.3, weight 10%) and describes what it should assess
# ("KYC feasibility, data-permission constraints, product suitability, human
# approval requirement, operational readiness") but does not publish a full
# 100-point driver breakdown table the way it does for the other six sub-scores.
# This 5-driver table is our deterministic, documented gap-fill (see plan §Gap 6/7);
# it is versioned and editable like every other weight table, not hardcoded logic.
REVENUE_POTENTIAL_DRIVERS = [
    ("estimated_annual_cross_border_payment_value", 18),
    ("payment_frequency_and_repeatability", 12),
    ("operating_account_stickiness", 12),
    ("deposit_and_liquidity_value", 10),
    ("cash_management_product_attach_rate", 10),
    ("fx_adjacency_from_payment_corridors", 10),
    ("trade_and_working_capital_adjacency", 8),
    ("client_growth_velocity", 8),
    ("competitive_displacement_risk", 6),
    ("implementation_feasibility", 6),
]

CLIENT_PAIN_POINT_DRIVERS = [
    ("payment_delay_impact", 18),
    ("cash_visibility_pain", 16),
    ("reconciliation_burden", 14),
    ("cost_and_fee_pressure", 12),
    ("operational_scalability_constraint", 14),
    ("board_or_cfo_urgency", 14),
    ("risk_of_client_churn_or_provider_switch", 12),
]

STRATEGIC_FIT_DRIVERS = [
    ("corporate_bank_product_depth", 20),
    ("global_hausbank_alignment", 18),
    ("sme_midcap_scaleup_relevance", 15),
    ("payments_scale_and_platform_strategy_fit", 15),
    ("cross_divisional_monetisation_potential", 12),
    ("coverage_model_fit", 10),
    ("brand_and_relationship_advantage", 10),
]

EARLY_SIGNAL_DRIVERS = [
    ("expansion_announcement_visibility", 18),
    ("international_hiring_signal", 14),
    ("foreign_customer_growth_signal", 14),
    ("supplier_and_procurement_signal", 12),
    ("funding_and_growth_event_timing", 12),
    ("timing_window_before_client_decision", 15),
    ("signal_freshness_and_recurrence", 15),
]

DATA_QUALITY_DRIVERS = [
    ("source_reliability", 18),
    ("completeness_of_required_fields", 16),
    ("consistency_across_signals", 14),
    ("evidence_traceability", 14),
    ("freshness_of_data", 12),
    ("explainability_of_score_drivers", 14),
    ("permission_and_governance_readiness", 12),
]

RM_ACTIONABILITY_DRIVERS = [
    ("clarity_of_next_best_action", 20),
    ("quality_of_conversation_prompts", 16),
    ("product_conversation_readiness", 14),
    ("timing_urgency_for_outreach", 14),
    ("evidence_confidence_for_rm_trust", 12),
    ("workflow_integration_potential", 12),
    ("action_outcome_measurability", 12),
]

CONTROL_FEASIBILITY_DRIVERS = [
    ("kyc_and_onboarding_feasibility", 25),
    ("data_permission_and_classification_readiness", 20),
    ("product_suitability_and_approval_readiness", 20),
    ("human_approval_workflow_readiness", 20),
    ("operational_delivery_complexity", 15),
]

SUB_SCORE_DRIVER_TABLES = {
    "revenue_potential": REVENUE_POTENTIAL_DRIVERS,
    "client_pain_point_intensity": CLIENT_PAIN_POINT_DRIVERS,
    "strategic_fit": STRATEGIC_FIT_DRIVERS,
    "early_signal_detectability": EARLY_SIGNAL_DRIVERS,
    "data_availability_explainability": DATA_QUALITY_DRIVERS,
    "rm_actionability": RM_ACTIONABILITY_DRIVERS,
    "control_implementation_feasibility": CONTROL_FEASIBILITY_DRIVERS,
}

# Final rollup weights, doc §23.3 (must sum to 100).
FINAL_ROLLUP_WEIGHTS = {
    "revenue_potential": 25,
    "client_pain_point_intensity": 15,
    "strategic_fit": 15,
    "early_signal_detectability": 15,
    "rm_actionability": 10,
    "data_availability_explainability": 10,
    "control_implementation_feasibility": 10,
}

# Decision bands, doc §23.3 + §15.1B.
HIGH_PRIORITY_MIN_FINAL = 80
MONITOR_MIN_FINAL = 60
VALIDATE_MIN_FINAL = 40
HIGH_PRIORITY_MIN_REVENUE = 70
HIGH_PRIORITY_MIN_EARLY_SIGNAL = 65
HIGH_PRIORITY_MIN_RM_ACTIONABILITY = 70


class DriverWeight(BaseModel):
    """A single (driver_name, weight) pair. Modeled as an object rather than
    a tuple because Firestore does not support nested arrays (an array of
    (name, weight) tuples serializes as an array-of-arrays, which Firestore
    rejects with 'contains an invalid nested entity')."""

    name: str
    weight: float


class WeightConfig(BaseModel):
    version_id: str
    owner: str
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_date: Optional[datetime] = None
    active: bool = True
    change_reason: str = "Initial version transcribed from LaunchPad AI concept document."
    sub_score_driver_tables: dict[str, list[DriverWeight]] = Field(
        default_factory=lambda: {
            k: [DriverWeight(name=name, weight=weight) for name, weight in v]
            for k, v in SUB_SCORE_DRIVER_TABLES.items()
        }
    )
    final_rollup_weights: dict[str, float] = Field(
        default_factory=lambda: dict(FINAL_ROLLUP_WEIGHTS)
    )


def default_weight_config(version_id: str = "v1", owner: str = "system") -> WeightConfig:
    return WeightConfig(version_id=version_id, owner=owner, approved_date=datetime.now(timezone.utc))
