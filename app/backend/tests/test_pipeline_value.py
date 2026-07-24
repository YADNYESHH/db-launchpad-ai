from ..pipeline_value import estimate_pipeline_value


def test_high_priority_with_cross_border_produces_positive_estimate():
    result = estimate_pipeline_value(
        annual_revenue_eur=18_000_000,
        annual_cross_border_payment_value_eur=6_000_000,
        priority_band="high_priority",
    )
    assert result.estimated_annual_bank_revenue_eur > 0
    assert "indicative" in result.basis.lower()
    assert "not a revenue commitment" in result.basis.lower()


def test_band_multiplier_orders_totals_high_gt_monitor_gt_validate_gt_no_action():
    kwargs = dict(
        annual_revenue_eur=18_000_000,
        annual_cross_border_payment_value_eur=6_000_000,
    )
    high = estimate_pipeline_value(priority_band="high_priority", **kwargs)
    monitor = estimate_pipeline_value(priority_band="monitor", **kwargs)
    validate = estimate_pipeline_value(priority_band="validate", **kwargs)
    no_action = estimate_pipeline_value(priority_band="no_immediate_action", **kwargs)

    assert (
        high.estimated_annual_bank_revenue_eur
        > monitor.estimated_annual_bank_revenue_eur
        > validate.estimated_annual_bank_revenue_eur
        > no_action.estimated_annual_bank_revenue_eur
        > 0
    )


def test_none_cross_border_value_does_not_crash_and_is_treated_as_zero():
    with_none = estimate_pipeline_value(
        annual_revenue_eur=18_000_000,
        annual_cross_border_payment_value_eur=None,
        priority_band="monitor",
    )
    with_zero = estimate_pipeline_value(
        annual_revenue_eur=18_000_000,
        annual_cross_border_payment_value_eur=0,
        priority_band="monitor",
    )
    assert with_none.estimated_annual_bank_revenue_eur == with_zero.estimated_annual_bank_revenue_eur
    assert with_none.breakdown["payments_fx_fees"] == 0
    assert with_none.breakdown["cash_management_fees"] == 0


def test_breakdown_keys_present():
    result = estimate_pipeline_value(
        annual_revenue_eur=18_000_000,
        annual_cross_border_payment_value_eur=6_000_000,
        priority_band=None,
    )
    expected_keys = {
        "payments_fx_fees",
        "cash_management_fees",
        "deposit_net_interest",
        "band_probability_multiplier",
    }
    assert expected_keys == set(result.breakdown.keys())
    assert result.breakdown["band_probability_multiplier"] == 0.6


def test_deterministic_same_inputs_same_output():
    kwargs = dict(
        annual_revenue_eur=5_000_000,
        annual_cross_border_payment_value_eur=1_200_000,
        priority_band="validate",
    )
    r1 = estimate_pipeline_value(**kwargs)
    r2 = estimate_pipeline_value(**kwargs)
    assert r1 == r2
