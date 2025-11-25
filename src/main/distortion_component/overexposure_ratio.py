"""Over-exposure analyzer based on the ratio of saturated pixels.

Metric definition
-----------------
Over-exposure ratio = (# of over-exposed pixels) / (total # of pixels)

Over-exposed pixels are defined using a configurable threshold close to the
maximum possible intensity (e.g. 250 for 8-bit images).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

ImageLike = np.ndarray


@dataclass
class OverExposureResult:
    """Container for the over-exposure metric."""

    ratio: float
    threshold: float


class OverExposureAnalyzer:
    """Analyze over-exposure by measuring the ratio of saturated pixels."""

    def __init__(self, threshold: int = 250) -> None:
        self.threshold = threshold
        self._image: Optional[ImageLike] = None
        self._image_path: Optional[Path] = None
        self._result: Optional[OverExposureResult] = None

    def bind_image(self, image: Optional[ImageLike] = None, *, path: Optional[Union[str, Path]] = None) -> None:
        """Bind an image for over-exposure analysis."""

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

    def analyze(self) -> OverExposureResult:
        """Run over-exposure analysis on the bound image."""

        img = self.image
        if img.ndim == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        total = gray.size
        if total == 0:
            ratio = 0.0
        else:
            over = np.count_nonzero(gray >= self.threshold)
            ratio = float(over) / float(total)

        self._result = OverExposureResult(ratio=ratio, threshold=float(self.threshold))
        return self._result

    @property
    def result(self) -> Optional[OverExposureResult]:
        return self._result
