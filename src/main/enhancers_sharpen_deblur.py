"""Sharpening and deblurring enhancers based on BaseImageEnhancer."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np

from .enhancement import BaseImageEnhancer, EnhancementConfig, ImageLike


class SharpenLightEnhancer(BaseImageEnhancer):
    """Light sharpening using unsharp masking with small radius."""

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

        s = max(0.1, min(1.0, float(self.strength)))
        blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=1.0)
        sharpened = cv2.addWeighted(img, 1 + s, blurred, -s, 0)
        return sharpened


class SharpenMediumEnhancer(BaseImageEnhancer):
    """Medium sharpening with stronger unsharp masking."""

    def __init__(self, config: Optional[EnhancementConfig] = None, strength: float = 0.7) -> None:
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

        s = max(0.1, min(1.5, float(self.strength)))
        blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=1.5)
        sharpened = cv2.addWeighted(img, 1 + s, blurred, -s, 0)
        return sharpened


class DeblurEnhancer(BaseImageEnhancer):
    """Moderate deblurring using simple Laplacian sharpening kernel."""

    def __init__(self, config: Optional[EnhancementConfig] = None, strength: float = 0.6) -> None:
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

        s = max(0.1, min(1.0, float(self.strength)))
        kernel = np.array([[0, -1, 0], [-1, 5 + s, -1], [0, -1, 0]], dtype=np.float32)
        deblurred = cv2.filter2D(img, -1, kernel)
        return deblurred


class DeblurAggressiveEnhancer(BaseImageEnhancer):
    """Aggressive deblurring; may introduce artifacts, use with care."""

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

        s = max(0.5, min(2.0, float(self.strength)))
        kernel = np.array([[0, -1, 0], [-1, 5 + 2 * s, -1], [0, -1, 0]], dtype=np.float32)
        deblurred = cv2.filter2D(img, -1, kernel)
        return deblurred

