"""Executor that maps EnhancementPlan to concrete BaseImageEnhancer instances."""

from __future__ import annotations

from typing import List

from .enhancement import BaseImageEnhancer, ImageLike
from .enhancement_strategy import EnhancementOpType, EnhancementPlan
from .enhancers_denoise import DenoiseLightEnhancer, DenoiseStrongEnhancer
from .enhancers_sharpen_deblur import (
    DeblurAggressiveEnhancer,
    DeblurEnhancer,
    SharpenLightEnhancer,
    SharpenMediumEnhancer,
)
from .enhancers_tone_localcontrast import CLAHEEnhancer, GammaAdjustEnhancer


def _make_enhancer_for_op(op_type: EnhancementOpType, strength: float = 1.0) -> BaseImageEnhancer:
    if op_type is EnhancementOpType.DENOISE_LIGHT:
        return DenoiseLightEnhancer(strength=strength)
    if op_type is EnhancementOpType.DENOISE_STRONG:
        return DenoiseStrongEnhancer(strength=strength)
    if op_type is EnhancementOpType.SHARPEN_LIGHT:
        return SharpenLightEnhancer(strength=strength)
    if op_type is EnhancementOpType.SHARPEN_MEDIUM:
        return SharpenMediumEnhancer(strength=strength)
    if op_type is EnhancementOpType.DEBLUR:
        return DeblurEnhancer(strength=strength)
    if op_type is EnhancementOpType.DEBLUR_AGGRESSIVE:
        return DeblurAggressiveEnhancer(strength=strength)
    if op_type is EnhancementOpType.GAMMA_INCREASE:
        return GammaAdjustEnhancer(strength=abs(strength))
    if op_type is EnhancementOpType.GAMMA_DECREASE:
        return GammaAdjustEnhancer(strength=-abs(strength))
    if op_type is EnhancementOpType.CLAHE:
        return CLAHEEnhancer(strength=strength)
    # MARK_AS_LOW_QUALITY and unknown ops: no-op enhancer
    return _NoOpEnhancer()


class _NoOpEnhancer(BaseImageEnhancer):
    def enhance(self) -> ImageLike:
        if self._image is None and self._image_path is None:
            raise RuntimeError("No image bound. Call bind_image() first.")
        if self._image is not None:
            return self._image
        import cv2

        img = cv2.imread(str(self._image_path), cv2.IMREAD_COLOR)
        if img is None:
            raise IOError(f"Failed to read image from {self._image_path!s}")
        return img


def apply_enhancement_plan(image: ImageLike, plan: EnhancementPlan) -> ImageLike:
    """Apply all operations in an EnhancementPlan sequentially to an image."""

    result: ImageLike = image
    for op in plan.ops:
        enhancer = _make_enhancer_for_op(op.type, strength=op.strength or 1.0)
        enhancer.bind_image(image=result)
        result = enhancer.enhance()
    return result
