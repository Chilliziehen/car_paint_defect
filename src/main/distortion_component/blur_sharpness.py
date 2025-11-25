"""Blur (sharpness) analyzer based on Laplacian variance.

Metric definition
-----------------
Sharpness = Var(∇² I)

Where ∇² I is the Laplacian of the image intensity. A larger variance
indicates a sharper image; a smaller value suggests blur.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

ImageLike = np.ndarray


@dataclass
class BlurSharpnessResult:
    """Container for the sharpness metric.

    Attributes
    ----------
    sharpness: float
        Variance of the Laplacian response, higher is sharper.
    """

    sharpness: float


class BlurSharpnessAnalyzer:
    """Analyze image blur using Laplacian variance as a sharpness metric."""

    def __init__(self) -> None:
        self._image: Optional[ImageLike] = None
        self._image_path: Optional[Path] = None
        self._result: Optional[BlurSharpnessResult] = None

    # ------------------------------------------------------------------
    # Image binding
    # ------------------------------------------------------------------
    def bind_image(self, image: Optional[ImageLike] = None, *, path: Optional[Union[str, Path]] = None) -> None:
        """Bind an image for blur / sharpness analysis.

        Parameters
        ----------
        image:
            BGR or RGB image as a ``numpy.ndarray`` with shape (H, W, C) or
            grayscale (H, W).
        path:
            Path to an image file. When provided and ``image`` is None, the
            image will be loaded from disk in BGR format.
        """

        if image is None and path is None:
            raise ValueError("Either 'image' or 'path' must be provided to bind_image().")

        self._image = image
        self._image_path = Path(path) if path is not None else None
        self._result = None

    @property
    def image(self) -> ImageLike:
        """Return the bound image, loading from disk if necessary."""

        if self._image is None:
            if self._image_path is None:
                raise RuntimeError("No image bound. Call bind_image() first.")
            img = cv2.imread(str(self._image_path), cv2.IMREAD_COLOR)
            if img is None:
                raise IOError(f"Failed to read image from {self._image_path!s}")
            self._image = img
        return self._image

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def analyze(self) -> BlurSharpnessResult:
        """Run sharpness analysis on the currently bound image."""

        img = self.image
        if img.ndim == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        lap = cv2.Laplacian(gray, ddepth=cv2.CV_64F)
        var_lap = float(lap.var())
        self._result = BlurSharpnessResult(sharpness=var_lap)
        return self._result

    @property
    def result(self) -> Optional[BlurSharpnessResult]:
        """Most recent analysis result, if available."""

        return self._result

