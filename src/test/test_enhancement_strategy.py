"""Unit tests for the CSV-driven enhancement strategy logic."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from src.main.distortion_analyser import DistortionMetrics
from src.main.enhancement_strategy import (
    EnhancementOpType,
    EnhancementPlanner,
    SharpnessCriteria,
    SharpnessLevel,
)


def _make_metrics(sharpness: float, noise: float, illum: float, overexp: float = 0.0) -> DistortionMetrics:
    return DistortionMetrics(
        sharpness=sharpness,
        noise_variance=noise,
        illumination_uniformity=illum,
        overexposure_ratio=overexp,
    )


def test_sharpness_classification_uses_csv(tmp_path: Path) -> None:
    # Create a temporary CSV with simple, non-overlapping rules
    csv_path = tmp_path / "sharpness_criteria.csv"
    csv_path.write_text(
        "Sharpness_Level,Lower_Bound,Upper_Bound\n"
        "Clear,25,9999\n"
        "Slight_Blur,15,25\n"
        "Moderate_Blur,8,15\n"
        "Heavy_Blur,0,8\n",
        encoding="utf-8",
    )

    criteria = SharpnessCriteria(csv_path=csv_path)

    assert criteria.classify(30.0) is SharpnessLevel.CLEAR
    assert criteria.classify(20.0) is SharpnessLevel.SLIGHT_BLUR
    assert criteria.classify(10.0) is SharpnessLevel.MODERATE_BLUR
    assert criteria.classify(3.0) is SharpnessLevel.HEAVY_BLUR


def test_build_plan_for_clear_level() -> None:
    planner = EnhancementPlanner()

    # Clear, good illumination (low unevenness), low contrast (illum low)
    metrics = _make_metrics(sharpness=30.0, noise=0.1, illum=0.1)
    plan = planner.build_plan(metrics)

    assert plan.sharpness_level in (SharpnessLevel.CLEAR, SharpnessLevel.SLIGHT_BLUR)
    # Should contain at least CLAHE due to low contrast proxy
    op_types = [op.type for op in plan.ops]
    assert EnhancementOpType.CLAHE in op_types


def test_build_plan_for_heavy_blur_marks_low_quality() -> None:
    planner = EnhancementPlanner()

    # Very low sharpness should be heavy blur
    metrics = _make_metrics(sharpness=1.0, noise=0.2, illum=0.3)
    plan = planner.build_plan(metrics)

    assert plan.sharpness_level is SharpnessLevel.HEAVY_BLUR

    op_types = [op.type for op in plan.ops]
    assert EnhancementOpType.MARK_AS_LOW_QUALITY in op_types
    assert EnhancementOpType.DEBLUR_AGGRESSIVE in op_types


if __name__ == "__main__":
    # Simple manual sanity run
    planner = EnhancementPlanner()
    metrics = _make_metrics(sharpness=18.0, noise=0.6, illum=0.4)
    plan = planner.build_plan(metrics)
    print("Sharpness level:", plan.sharpness_level)
    print("Quality penalty:", plan.quality_penalty)
    print("Ops:", [op.type for op in plan.ops])
