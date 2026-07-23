"""Final cross-border opportunity score rollup and decision bands.

Formula and thresholds transcribed verbatim from doc §23.3 and §15.1B:

    final = revenue*0.25 + pain*0.15 + strategic_fit*0.15 + early_signal*0.15
          + rm_actionability*0.10 + data_quality*0.10 + control_feasibility*0.10

    >= 80  High priority   (AND revenue>=70, early_signal>=65, rm_actionability>=70)
    60-79  Monitor
    40-59  Validate
    < 40   No immediate action

Missing mandatory data is never silently treated as 0: if a sub-score reports
missing_data_flags, the final band can never be HIGH_PRIORITY even if the
weighted math clears 80 — it is forced to VALIDATE instead (doc: "if the final
score is high but data-quality or control feasibility is weak, the system
should recommend further validation rather than immediate outreach").
"""
from ..models.enums import PriorityBand
from ..models.scoring import ScoreRecord, SubScore
from ..models.weights import (
    FINAL_ROLLUP_WEIGHTS,
    HIGH_PRIORITY_MIN_EARLY_SIGNAL,
    HIGH_PRIORITY_MIN_FINAL,
    HIGH_PRIORITY_MIN_REVENUE,
    HIGH_PRIORITY_MIN_RM_ACTIONABILITY,
    MONITOR_MIN_FINAL,
    VALIDATE_MIN_FINAL,
)
from .builder import build_sub_score
from .context import ScoringContext, clamp
from . import control_feasibility, data_quality, early_signal, painpoint, revenue, rm_actionability, strategic_fit

_SUB_SCORE_MODULES = {
    "revenue_potential": revenue,
    "client_pain_point_intensity": painpoint,
    "strategic_fit": strategic_fit,
    "early_signal_detectability": early_signal,
    "rm_actionability": rm_actionability,
    "data_availability_explainability": data_quality,
    "control_implementation_feasibility": control_feasibility,
}


def compute_all_sub_scores(ctx: ScoringContext) -> dict[str, SubScore]:
    return {
        sub_score_type: build_sub_score(sub_score_type, module.DRIVER_FUNCTIONS, ctx)
        for sub_score_type, module in _SUB_SCORE_MODULES.items()
    }


def compute_final_score(sub_scores: dict[str, SubScore]) -> float:
    rollup_weights = FINAL_ROLLUP_WEIGHTS
    total = sum(sub_scores[key].score_value * rollup_weights[key] / 100 for key in rollup_weights)
    return clamp(total)


def determine_priority_band(final_score: float, sub_scores: dict[str, SubScore]) -> tuple[PriorityBand, dict]:
    revenue_score = sub_scores["revenue_potential"].score_value
    early_signal_score = sub_scores["early_signal_detectability"].score_value
    rm_score = sub_scores["rm_actionability"].score_value
    any_missing = any(s.missing_data_flags for s in sub_scores.values())

    detail = {
        "final_score": final_score,
        "revenue_potential": revenue_score,
        "early_signal_detectability": early_signal_score,
        "rm_actionability": rm_score,
        "any_missing_mandatory_data": any_missing,
    }

    high_priority_thresholds_met = (
        final_score >= HIGH_PRIORITY_MIN_FINAL
        and revenue_score >= HIGH_PRIORITY_MIN_REVENUE
        and early_signal_score >= HIGH_PRIORITY_MIN_EARLY_SIGNAL
        and rm_score >= HIGH_PRIORITY_MIN_RM_ACTIONABILITY
    )

    if high_priority_thresholds_met and any_missing:
        detail["reason"] = "Score qualifies for High priority but mandatory data is missing; forcing Validate."
        return PriorityBand.VALIDATE, detail

    if high_priority_thresholds_met:
        detail["reason"] = "All High-priority thresholds met."
        return PriorityBand.HIGH_PRIORITY, detail

    if final_score >= MONITOR_MIN_FINAL:
        detail["reason"] = "Final score in Monitor band, or a High-priority sub-threshold was missed."
        return PriorityBand.MONITOR, detail

    if final_score >= VALIDATE_MIN_FINAL:
        detail["reason"] = "Final score in Validate band."
        return PriorityBand.VALIDATE, detail

    detail["reason"] = "Final score below Validate threshold."
    return PriorityBand.NO_ACTION, detail


def score_startup(ctx: ScoringContext) -> ScoreRecord:
    sub_scores = compute_all_sub_scores(ctx)
    final_score = compute_final_score(sub_scores)
    band, detail = determine_priority_band(final_score, sub_scores)
    missing_flags = sorted({flag for s in sub_scores.values() for flag in s.missing_data_flags})

    return ScoreRecord(
        startup_id=ctx.profile.startup_id,
        sub_scores=list(sub_scores.values()),
        final_score=final_score,
        priority_band=band,
        weight_config_version=ctx.weight_config.version_id,
        missing_data_flags=missing_flags,
        threshold_detail=detail,
    )
