from ..models.enums import PriorityBand
from ..models.weights import FINAL_ROLLUP_WEIGHTS
from ..scoring import compute_final_score, score_startup


def test_scoring_is_deterministic(novatrade_ctx):
    """Same input must always produce the exact same output."""
    r1 = score_startup(novatrade_ctx)
    r2 = score_startup(novatrade_ctx)
    assert r1.final_score == r2.final_score
    assert r1.priority_band == r2.priority_band
    for s1, s2 in zip(r1.sub_scores, r2.sub_scores):
        assert s1.score_value == s2.score_value
        assert s1.driver_scores == s2.driver_scores


def test_rollup_weights_sum_to_100():
    assert sum(FINAL_ROLLUP_WEIGHTS.values()) == 100


def test_every_sub_score_driver_table_sums_to_100(novatrade_ctx):
    for sub_score_type, table in novatrade_ctx.weight_config.sub_score_driver_tables.items():
        total = sum(dw.weight for dw in table)
        assert total == 100, f"{sub_score_type} driver weights sum to {total}, not 100"


def test_final_score_matches_manual_rollup_math(novatrade_ctx):
    record = score_startup(novatrade_ctx)
    by_type = {s.sub_score_type: s.score_value for s in record.sub_scores}
    manual = sum(by_type[k] * w / 100 for k, w in FINAL_ROLLUP_WEIGHTS.items())
    assert round(record.final_score, 6) == round(manual, 6)
    assert record.final_score == compute_final_score({s.sub_score_type: s for s in record.sub_scores})


def test_novatrade_is_high_priority_end_to_end(novatrade_ctx):
    """This is the doc's own worked example (§ Worked Rating Example): a
    well-populated, clearly expanding synthetic startup should clear the
    High-priority bar with no missing mandatory data.
    """
    record = score_startup(novatrade_ctx)
    assert record.missing_data_flags == []
    assert record.priority_band == PriorityBand.HIGH_PRIORITY
    assert record.final_score >= 80


def test_every_sub_score_has_rationale_and_top_drivers(novatrade_ctx):
    record = score_startup(novatrade_ctx)
    for sub in record.sub_scores:
        assert sub.rationale
        assert len(sub.top_drivers) > 0
        for driver in sub.driver_scores:
            assert driver.rationale


def test_missing_mandatory_data_never_silently_scored_as_zero_and_blocks_high_priority(empty_ctx):
    """No payment/pain/signal data at all: every dependent driver must flag
    missing_data=True (not just silently return 0), and the record can never
    reach High priority regardless of what the raw weighted math says.
    """
    record = score_startup(empty_ctx)
    assert record.missing_data_flags, "expected missing-data flags when no data is on file"
    assert record.priority_band != PriorityBand.HIGH_PRIORITY


def test_high_priority_requires_all_named_sub_thresholds(novatrade_ctx):
    """Even if final_score >= 80, doc §15.1B requires revenue>=70,
    early_signal>=65 and rm_actionability>=70 individually."""
    record = score_startup(novatrade_ctx)
    by_type = {s.sub_score_type: s.score_value for s in record.sub_scores}
    if record.priority_band == PriorityBand.HIGH_PRIORITY:
        assert by_type["revenue_potential"] >= 70
        assert by_type["early_signal_detectability"] >= 65
        assert by_type["rm_actionability"] >= 70


def test_priority_band_thresholds_are_monotonic():
    from ..models.weights import (
        HIGH_PRIORITY_MIN_FINAL,
        MONITOR_MIN_FINAL,
        VALIDATE_MIN_FINAL,
    )

    assert HIGH_PRIORITY_MIN_FINAL > MONITOR_MIN_FINAL > VALIDATE_MIN_FINAL > 0
