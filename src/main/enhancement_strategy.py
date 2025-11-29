"""CSV-driven enhancement strategy selection based on distortion metrics.

This module reads sharpness criteria from a CSV file and builds an
image enhancement plan based on the distortion metrics produced by
:mod:`distortion_analyser`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional

import csv

from .distortion_analyser import DistortionMetrics

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# Path to the sharpness criteria CSV, relative to project root.
_ROOT_DIR = Path(__file__).resolve().parents[2]
SHARPNESS_CRITERIA_CSV = _ROOT_DIR / "models" / "distortion_standards" / "sharpness_criteria.csv"

# Brightness / contrast thresholds (heuristic placeholders)
TH_BRIGHT_LOW = 0.35
TH_BRIGHT_HIGH = 0.65
TH_CONTRAST_LOW = 0.25

# Quality penalty defaults per sharpness level
QUALITY_PENALTY_DEFAULT: Dict[str, float] = {
    "Clear": 1.0,
    "Slight_Blur": 0.95,
    "Moderate_Blur": 0.75,
    "Heavy_Blur": 0.4,
}

# Noise thresholds (heuristic) to distinguish high vs low noise
TH_NOISE_HIGH = 0.5


# ---------------------------------------------------------------------------
# Core domain types
# ---------------------------------------------------------------------------


class SharpnessLevel(str, Enum):
    CLEAR = "Clear"
    SLIGHT_BLUR = "Slight_Blur"
    MODERATE_BLUR = "Moderate_Blur"
    HEAVY_BLUR = "Heavy_Blur"


@dataclass
class SharpnessRule:
    """Configuration entry representing one sharpness interval."""

    level: SharpnessLevel
    lower_bound: float
    upper_bound: float
    description: str = ""


class EnhancementOpType(Enum):
    DENOISE_LIGHT = auto()
    DENOISE_STRONG = auto()
    SHARPEN_LIGHT = auto()
    SHARPEN_MEDIUM = auto()
    DEBLUR = auto()
    DEBLUR_AGGRESSIVE = auto()
    GAMMA_INCREASE = auto()
    GAMMA_DECREASE = auto()
    CLAHE = auto()
    MARK_AS_LOW_QUALITY = auto()


@dataclass
class EnhancementOp:
    type: EnhancementOpType
    strength: Optional[float] = None


@dataclass
class EnhancementPlan:
    sharpness_level: SharpnessLevel
    ops: List[EnhancementOp]
    quality_penalty: float


# ---------------------------------------------------------------------------
# Sharpness criteria loading and classification
# ---------------------------------------------------------------------------


class SharpnessCriteria:
    """Loads and classifies sharpness scores based on a CSV file."""

    def __init__(self, csv_path: Path = SHARPNESS_CRITERIA_CSV) -> None:
        self.csv_path = csv_path
        self._rules: List[SharpnessRule] = []
        self._loaded = False

    @property
    def rules(self) -> List[SharpnessRule]:
        if not self._loaded:
            self._load()
        return self._rules

    def _load(self) -> None:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Sharpness criteria CSV not found: {self.csv_path!s}")

        rules: List[SharpnessRule] = []
        with self.csv_path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            required = {"Sharpness_Level", "Lower_Bound", "Upper_Bound"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"Missing required columns in CSV: {missing!r}")

            for row in reader:
                level_str = row["Sharpness_Level"].strip()
                try:
                    level = SharpnessLevel(level_str)
                except ValueError:
                    # Skip unknown levels
                    continue

                try:
                    lower = float(row["Lower_Bound"])
                    upper = float(row["Upper_Bound"])
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Invalid bounds in CSV row: {row!r}") from exc

                desc = row.get("Description", "").strip()
                rules.append(SharpnessRule(level=level, lower_bound=lower, upper_bound=upper, description=desc))

        # Sort by interval width so that narrower ranges are matched first
        rules.sort(key=lambda r: (r.upper_bound - r.lower_bound, r.lower_bound))

        self._rules = rules
        self._loaded = True

    def classify(self, sharpness_score: float) -> SharpnessLevel:
        """Classify a sharpness score to a level.

        Strategy:
        - Narrowest interval match wins.
        - If nothing matches, default to HEAVY_BLUR (conservative).
        """

        for rule in self.rules:
            if rule.lower_bound <= sharpness_score <= rule.upper_bound:
                return rule.level

        return SharpnessLevel.HEAVY_BLUR


# ---------------------------------------------------------------------------
# Enhancement plan builder
# ---------------------------------------------------------------------------


class EnhancementPlanner:
    """Builds enhancement plans from distortion metrics and CSV rules."""

    def __init__(self, criteria: Optional[SharpnessCriteria] = None) -> None:
        self.criteria = criteria or SharpnessCriteria()

    def classify_sharpness(self, sharpness_score: float) -> SharpnessLevel:
        return self.criteria.classify(sharpness_score)

    def build_plan(self, metrics: DistortionMetrics) -> EnhancementPlan:
        """Build an enhancement plan for the given distortion metrics."""

        level = self.classify_sharpness(metrics.sharpness)

        # Heuristic proxies (can be replaced by explicit brightness/contrast metrics later)
        brightness_proxy = max(0.0, min(1.0, 1.0 - float(metrics.illumination_uniformity)))
        contrast_proxy = max(0.0, min(1.0, float(metrics.illumination_uniformity)))
        noise_proxy = float(metrics.noise_variance)

        ops: List[EnhancementOp] = []
        quality_penalty = QUALITY_PENALTY_DEFAULT.get(level.value, 1.0)

        if level is SharpnessLevel.CLEAR:
            # No sharpening/deblurring; only mild tone/local contrast corrections
            if brightness_proxy < TH_BRIGHT_LOW:
                ops.append(EnhancementOp(EnhancementOpType.GAMMA_INCREASE, strength=0.2))
            elif brightness_proxy > TH_BRIGHT_HIGH:
                ops.append(EnhancementOp(EnhancementOpType.GAMMA_DECREASE, strength=0.2))

            if contrast_proxy < TH_CONTRAST_LOW:
                ops.append(EnhancementOp(EnhancementOpType.CLAHE, strength=1.0))

        elif level is SharpnessLevel.SLIGHT_BLUR:
            if noise_proxy > TH_NOISE_HIGH:
                ops.append(EnhancementOp(EnhancementOpType.DENOISE_LIGHT, strength=0.5))
            ops.append(EnhancementOp(EnhancementOpType.SHARPEN_LIGHT, strength=0.5))

            if contrast_proxy < TH_CONTRAST_LOW:
                ops.append(EnhancementOp(EnhancementOpType.CLAHE, strength=1.0))

        elif level is SharpnessLevel.MODERATE_BLUR:
            if noise_proxy > TH_NOISE_HIGH:
                ops.append(EnhancementOp(EnhancementOpType.DENOISE_STRONG, strength=0.8))

            ops.append(EnhancementOp(EnhancementOpType.DEBLUR, strength=0.6))
            ops.append(EnhancementOp(EnhancementOpType.SHARPEN_MEDIUM, strength=0.7))

            if contrast_proxy < TH_CONTRAST_LOW:
                ops.append(EnhancementOp(EnhancementOpType.CLAHE, strength=1.0))

            if brightness_proxy < TH_BRIGHT_LOW:
                ops.append(EnhancementOp(EnhancementOpType.GAMMA_INCREASE, strength=0.2))
            elif brightness_proxy > TH_BRIGHT_HIGH:
                ops.append(EnhancementOp(EnhancementOpType.GAMMA_DECREASE, strength=0.2))

        elif level is SharpnessLevel.HEAVY_BLUR:
            ops.append(EnhancementOp(EnhancementOpType.MARK_AS_LOW_QUALITY))
            ops.append(EnhancementOp(EnhancementOpType.DEBLUR_AGGRESSIVE, strength=1.0))

        return EnhancementPlan(sharpness_level=level, ops=ops, quality_penalty=quality_penalty)

