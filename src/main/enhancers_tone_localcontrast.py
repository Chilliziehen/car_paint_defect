"""Tone (gamma) and local contrast (CLAHE) enhancers based on BaseImageEnhancer."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

from .enhancement import BaseImageEnhancer, EnhancementConfig, ImageLike


class GammaAdjustEnhancer(BaseImageEnhancer):
    """Adjust global gamma curve.

    A strength > 0 lightens the image (gamma < 1),
    a strength < 0 darkens it (gamma > 1).
    """

    def __init__(self, config: Optional[EnhancementConfig] = None, strength: float = 0.2) -> None:
        super().__init__(config=config)
        self.strength = strength

    def enhance(self) -> ImageLike:
        if self._image is None and self._image_path is None:
            raise RuntimeError("No image bound. Call bind_image() first.")

        img = self._image
        if img is None:
            img = cv2.imread(str(self._image_path), cv2.IMREAD_COLOR)
            if img is None:
                raise IOError(f"Failed to read image from {self._image_path!s}")

        # Map strength in [-1, 1] to gamma in [0.5, 2.0]
        s = max(-1.0, min(1.0, float(self.strength)))
        if s >= 0:
            gamma = 1.0 - 0.5 * s
        else:
            gamma = 1.0 - s  # s negative -> gamma > 1

        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)], dtype=np.uint8)
        return cv2.LUT(img, table)


class CLAHEEnhancer(BaseImageEnhancer):
    """Local contrast enhancement using CLAHE in LAB color space."""

    def __init__(self, config: Optional[EnhancementConfig] = None, strength: float = 1.0) -> None:
        super().__init__(config=config)
        self.strength = strength

    def enhance(self) -> ImageLike:
        if self._image is None and self._image_path is None:
            raise RuntimeError("No image bound. Call bind_image() first.")

        img = self._image
        if img is None:
            img = cv2.imread(str(self._image_path), cv2.IMREAD_COLOR)
            if img is None:
                raise IOError(f"Failed to read image from {self._image_path!s}")

        s = max(0.3, min(2.0, float(self.strength)))
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0 * s, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        merged = cv2.merge((cl, a, b))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

