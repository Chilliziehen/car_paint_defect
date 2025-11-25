"""High-level image distortion analyzer.

This module aggregates several low-level distortion metrics into a single
analyzer that can be used to assess image quality issues on car paint
inspection images.

Supported distortion metrics
----------------------------
- Blur / sharpness      : Sharpness = Var(∇² I)
- Noise level           : Global intensity variance
- Illumination uneven   : U = σ_L / μ_L
- Over-exposure         : Over-exposed pixel ratio
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

import numpy as np

from .distortion_component.blur_sharpness import BlurSharpnessAnalyzer
from .distortion_component.noise_variance import NoiseVarianceAnalyzer
from .distortion_component.illumination_uniformity import (
    IlluminationUniformityAnalyzer,
)
from .distortion_component.overexposure_ratio import OverExposureAnalyzer

ImageLike = np.ndarray


@dataclass
class DistortionMetrics:
    """All supported distortion metrics for a single image."""

    sharpness: float
    noise_variance: float
    illumination_uniformity: float
    overexposure_ratio: float

    def as_vector(self) -> np.ndarray:
        """Return metrics as a 1D numpy vector in a fixed order."""

        return np.array(
            [
                self.sharpness,
                self.noise_variance,
                self.illumination_uniformity,
                self.overexposure_ratio,
            ],
            dtype=float,
        )

    def as_dict(self) -> Dict[str, float]:
        """Return metrics as a plain dictionary."""

        return asdict(self)


class DistortionAnalyzer:
    """High-level image distortion analyzer.

    Usage pattern
    -------------
    1. Create an instance (optionally reusing it across images).
    2. Bind an image via :meth:`bind_image`.
    3. Call :meth:`analyze` to compute all supported distortion metrics.
    4. Access metrics via :attr:`metrics` or :meth:`metrics_vector`.
    """

    def __init__(self, *, overexposure_threshold: int = 250) -> None:
        self._image: Optional[ImageLike] = None
        self._image_path: Optional[Path] = None

        # Component analyzers
        self._blur_analyzer = BlurSharpnessAnalyzer()
        self._noise_analyzer = NoiseVarianceAnalyzer()
        self._illum_analyzer = IlluminationUniformityAnalyzer()
        self._overexp_analyzer = OverExposureAnalyzer(threshold=overexposure_threshold)

        self._metrics: Optional[DistortionMetrics] = None

    # ------------------------------------------------------------------
    # Image binding
    # ------------------------------------------------------------------
    def bind_image(self, image: Optional[ImageLike] = None, *, path: Optional[Union[str, Path]] = None) -> None:
        """Bind an image on which distortion analysis will be performed."""

        if image is None and path is None:
            raise ValueError("Either 'image' or 'path' must be provided to bind_image().")

        self._image = image
        self._image_path = Path(path) if path is not None else None
        self._metrics = None

    @property
    def image_source(self) -> Optional[Union[ImageLike, Path]]:
        """Return the currently bound image object or path (for inspection)."""

        if self._image is not None:
            return self._image
        return self._image_path

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def analyze(self) -> DistortionMetrics:
        """Run all component analyzers on the currently bound image."""

        if self._image is not None:
            img_arg = {"image": self._image}
        elif self._image_path is not None:
            img_arg = {"path": self._image_path}
        else:
            raise RuntimeError("No image bound. Call bind_image() first.")

        # Propagate binding to all components
        self._blur_analyzer.bind_image(**img_arg)
        self._noise_analyzer.bind_image(**img_arg)
        self._illum_analyzer.bind_image(**img_arg)
        self._overexp_analyzer.bind_image(**img_arg)

        blur_res = self._blur_analyzer.analyze()
        noise_res = self._noise_analyzer.analyze()
        illum_res = self._illum_analyzer.analyze()
        overexp_res = self._overexp_analyzer.analyze()

        self._metrics = DistortionMetrics(
            sharpness=blur_res.sharpness,
            noise_variance=noise_res.variance,
            illumination_uniformity=illum_res.uniformity,
            overexposure_ratio=overexp_res.ratio,
        )
        return self._metrics

    # ------------------------------------------------------------------
    # Metrics accessors
    # ------------------------------------------------------------------
    @property
    def metrics(self) -> Optional[DistortionMetrics]:
        """Return the most recent set of metrics, if available."""

        return self._metrics

    def metrics_vector(self) -> np.ndarray:
        """Return the distortion metrics as a fixed-order 1D vector.

        Raises
        ------
        RuntimeError
            If :meth:`analyze` has not been called yet.
        """

        if self._metrics is None:
            raise RuntimeError("No metrics available. Call analyze() first.")
        return self._metrics.as_vector()

    def metrics_names(self) -> Sequence[str]:
        """Names of metrics in the same order as :meth:`metrics_vector`."""

        return [
            "sharpness",
            "noise_variance",
            "illumination_uniformity",
            "overexposure_ratio",
        ]

