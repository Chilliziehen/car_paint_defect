"""Test program for full enhancement pipeline.

- Randomly sample 10 images from data/car_paint_defect/test/images
- For each image:
  - Compute distortion metrics
  - Build enhancement plan based on CSV-driven strategy
  - Apply enhancement using concrete BaseImageEnhancer subclasses
  - Overlay distortion vector and enhancement ops as green text at top-left
  - Save result to test_out_enhance
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import List

import cv2
import numpy as np

from src.main.distortion_analyser import DistortionAnalyzer
from src.main.enhancement_strategy import EnhancementOpType, EnhancementPlanner
from src.main.enhancers_executor import apply_enhancement_plan


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_TEST_IMAGES = ROOT_DIR / "data" / "car_paint_defect" / "test" / "images"
OUTPUT_DIR = ROOT_DIR / "test_out_enhance"


def _list_test_images() -> List[Path]:
    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    if not DATA_TEST_IMAGES.exists():
        return []
    return sorted(p for p in DATA_TEST_IMAGES.iterdir() if p.is_file() and p.suffix.lower() in exts)


def _vector_lines(names, vec: np.ndarray):
    """Return one line per distortion component."""

    return [f"{n}={v:.3f}" for n, v in zip(names, vec.tolist())]


def _ops_text(plan) -> str:
    if not plan.ops:
        return "ops: (none)"
    type_names = []
    for op in plan.ops:
        name = op.type.name
        if op.type is EnhancementOpType.GAMMA_INCREASE:
            name += "+"
        elif op.type is EnhancementOpType.GAMMA_DECREASE:
            name += "-"
        type_names.append(name)
    return "ops: " + ",".join(type_names)


def _draw_overlay(img: np.ndarray, lines) -> np.ndarray:
    """Draw multi-line green text at top-left with transparent background."""

    out = img.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    color = (0, 255, 0)  # green
    thickness = 1
    line_type = cv2.LINE_AA

    x = 5
    y = 5
    line_spacing = 4

    for line in lines:
        (text_w, text_h), baseline = cv2.getTextSize(line, font, font_scale, thickness)
        y_line = y + text_h
        cv2.putText(out, line, (x, y_line), font, font_scale, color, thickness, line_type)
        y = y_line + line_spacing

    return out


def process_random_images(num_images: int = 10) -> None:
    images = _list_test_images()
    if not images:
        raise RuntimeError(f"No test images found in {DATA_TEST_IMAGES!s}")

    if num_images > len(images):
        num_images = len(images)

    sampled = random.sample(images, num_images)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    analyzer = DistortionAnalyzer()
    planner = EnhancementPlanner()

    metric_names = analyzer.metrics_names()

    for img_path in sampled:
        img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if img is None:
            print(f"[WARN] Failed to read image: {img_path!s}")
            continue

        analyzer.bind_image(image=img)
        metrics = analyzer.analyze()
        vec = analyzer.metrics_vector()

        plan = planner.build_plan(metrics)
        enhanced = apply_enhancement_plan(img, plan)

        # Build overlay text: one line per distortion component + one line for ops
        metric_lines = _vector_lines(metric_names, vec)
        ops_line = _ops_text(plan)
        overlay_lines = metric_lines + [ops_line]

        out_img = _draw_overlay(enhanced, overlay_lines)

        out_path = OUTPUT_DIR / img_path.name
        cv2.imwrite(str(out_path), out_img)
        print(f"Saved: {out_path!s}")


if __name__ == "__main__":
    process_random_images(num_images=10)
