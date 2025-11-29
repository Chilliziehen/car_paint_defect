"""Denoising enhancers based on BaseImageEnhancer.

This module provides two concrete enhancers:

- DenoiseLightEnhancer  : light, edge-preserving denoising
- DenoiseStrongEnhancer : stronger non-local means denoising
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from .enhancement import BaseImageEnhancer, EnhancementConfig, ImageLike


class DenoiseLightEnhancer(BaseImageEnhancer):
    """Light denoising using bilateral filtering.

    Parameters
    ----------
    strength:
        Relative strength in [0, 1]. Higher means stronger denoising.
    """

    def __init__(self, config: Optional[EnhancementConfig] = None, strength: float = 0.5) -> None:
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

        # Map strength to sigmaColor/sigmaSpace for bilateralFilter
        s = max(0.1, min(1.0, float(self.strength)))
        sigma_color = 25 * s
        sigma_space = 25 * s
        denoised = cv2.bilateralFilter(img, d=0, sigmaColor=sigma_color, sigmaSpace=sigma_space)
        return denoised


class DenoiseStrongEnhancer(BaseImageEnhancer):
    """Stronger denoising using non-local means (fastNlMeansDenoisingColored)."""

    def __init__(self, config: Optional[EnhancementConfig] = None, strength: float = 0.8) -> None:
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

        # Map strength to the h parameter controlling filter strength
        h = 10 * max(0.1, min(1.0, float(self.strength)))
        denoised = cv2.fastNlMeansDenoisingColored(img, None, h, h, 7, 21)
        return denoised

