"""Illumination uniformity analyzer.

Metric definition
-----------------
U = σ_L / μ_L

Where L is the luminance (grayscale intensity), σ_L is its standard
deviation and μ_L is its mean. A higher value indicates more uneven
illumination across the image.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

ImageLike = np.ndarray


@dataclass
class IlluminationUniformityResult:
    """Container for the illumination uniformity metric."""

    uniformity: float


class IlluminationUniformityAnalyzer:
    """Analyze illumination unevenness using σ_L / μ_L on luminance."""

    def __init__(self) -> None:
        self._image: Optional[ImageLike] = None
        self._image_path: Optional[Path] = None
        self._result: Optional[IlluminationUniformityResult] = None

    def bind_image(self, image: Optional[ImageLike] = None, *, path: Optional[Union[str, Path]] = None) -> None:
        """Bind an image for illumination uniformity analysis."""

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

    def analyze(self) -> IlluminationUniformityResult:
        """Run illumination uniformity analysis on the bound image."""

        img = self.image
        if img.ndim == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        mean = float(gray.mean())
        std = float(gray.std())
        if mean == 0.0:
            uniformity = float("inf") if std > 0 else 0.0
        else:
            uniformity = std / mean
        self._result = IlluminationUniformityResult(uniformity=uniformity)
        return self._result

    @property
    def result(self) -> Optional[IlluminationUniformityResult]:
        return self._result

