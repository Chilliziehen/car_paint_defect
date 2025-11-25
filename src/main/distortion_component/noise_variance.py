"""Noise analyzer using image intensity variance as a proxy.

Metric definition
-----------------
Noise level ≈ Var(I)

In practice, more sophisticated methods can be used to separate noise from
structure, but global variance is a simple and fast proxy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

ImageLike = np.ndarray


@dataclass
class NoiseVarianceResult:
    """Container for the noise variance metric."""

    variance: float


class NoiseVarianceAnalyzer:
    """Analyze image noise using global intensity variance as a proxy."""

    def __init__(self) -> None:
        self._image: Optional[ImageLike] = None
        self._image_path: Optional[Path] = None
        self._result: Optional[NoiseVarianceResult] = None

    def bind_image(self, image: Optional[ImageLike] = None, *, path: Optional[Union[str, Path]] = None) -> None:
        """Bind an image for noise analysis."""

        if image is None and path is None:
            raise ValueError("Either 'image' or 'path' must be provided to bind_image().")

        self._image = image
        self._image_path = Path(path) if path is not None else None
        self._result = None

    @property
    def image(self) -> ImageLike:
        if self._image is None:
            if self._image_path is None:
                raise RuntimeError("No image bound. Call bind_image() first.")
            img = cv2.imread(str(self._image_path), cv2.IMREAD_COLOR)
            if img is None:
                raise IOError(f"Failed to read image from {self._image_path!s}")
            self._image = img
        return self._image

    def analyze(self) -> NoiseVarianceResult:
        """Run noise analysis on the currently bound image."""

        img = self.image
        if img.ndim == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        var = float(gray.var())
        self._result = NoiseVarianceResult(variance=var)
        return self._result

    @property
    def result(self) -> Optional[NoiseVarianceResult]:
        return self._result

