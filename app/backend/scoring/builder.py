from ..models.enums import ConfidenceBand
from ..models.scoring import DriverScore, SubScore
from .context import ScoringContext, clamp

SUB_SCORE_LABELS = {
    "revenue_potential": "Revenue potential",
    "client_pain_point_intensity": "Client pain-point intensity",
    "strategic_fit": "Strategic fit",
    "early_signal_detectability": "Early-signal detectability",
    "rm_actionability": "RM actionability",
    "data_availability_explainability": "Data availability & explainability",
    "control_implementation_feasibility": "Control & implementation feasibility",
}


def build_sub_score(sub_score_type: str, driver_fns: dict, ctx: ScoringContext) -> SubScore:
    """Generic sub-score assembler: applies the versioned weight table for
    `sub_score_type`, calls each driver function, and rolls the weighted
    drivers up into a single 0-100 SubScore with full evidence/rationale.
    """
    driver_table = ctx.weight_config.sub_score_driver_tables[sub_score_type]
    driver_scores: list[DriverScore] = []
    missing_flags: list[str] = []
    total_weighted = 0.0

    for driver_name, weight in driver_table:
        fn = driver_fns.get(driver_name)
        if fn is None:
            raise KeyError(f"no driver function registered for '{driver_name}' in '{sub_score_type}'")
        result = fn(ctx)
        weighted = result.raw_score * weight / 100.0
        total_weighted += weighted
        driver_scores.append(
            DriverScore(
                driver_name=driver_name,
                weight=weight,
                raw_score=result.raw_score,
                weighted_score=weighted,
                rationale=result.rationale,
                missing_data=result.missing_data,
            )
        )
        if result.missing_data:
            missing_flags.append(driver_name)

    score_value = clamp(total_weighted)
    top_drivers = [
        d.driver_name for d in sorted(driver_scores, key=lambda d: d.weighted_score, reverse=True)[:3]
    ]

    if len(missing_flags) == 0:
        confidence = ConfidenceBand.HIGH
    elif len(missing_flags) <= 2:
        confidence = ConfidenceBand.MEDIUM
    else:
        confidence = ConfidenceBand.LOW

    label = SUB_SCORE_LABELS.get(sub_score_type, sub_score_type)
    rationale = (
        f"{label} scored {score_value:.1f}/100 for {ctx.profile.name}, "
        f"driven mainly by: {', '.join(top_drivers)}."
    )
    if missing_flags:
        rationale += f" Missing/incomplete data for: {', '.join(missing_flags)}."

    return SubScore(
        sub_score_type=sub_score_type,
        score_value=score_value,
        weight_config_version=ctx.weight_config.version_id,
        driver_scores=driver_scores,
        top_drivers=top_drivers,
        missing_data_flags=missing_flags,
        confidence_band=confidence,
        rationale=rationale,
    )
