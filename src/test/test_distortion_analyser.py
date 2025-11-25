"""Utility script/tests for the DistortionAnalyzer.

This script randomly selects 5 JPG images from the test set, analyzes
image distortion metrics, overlays the resulting distortion vector in
green text at the top-left corner of each image, and writes the results
into ``test_out/distortion``.
"""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import List

import cv2
import numpy as np

from src.main.distortion_analyser import DistortionAnalyzer


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_TEST_IMAGES = ROOT_DIR / "data" / "car_paint_defect" / "test" / "images"
OUTPUT_DIR = ROOT_DIR / "test_out" / "distortion"


def _list_test_images() -> List[Path]:
    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    if not DATA_TEST_IMAGES.exists():
        return []
    return sorted(
        p for p in DATA_TEST_IMAGES.iterdir() if p.is_file() and p.suffix.lower() in exts
    )


def _format_vector(names, vec: np.ndarray) -> str:
    parts = []
    for name, value in zip(names, vec.tolist()):
        parts.append(f"{name}={value:.3f}")
    return " | ".join(parts)


def process_random_images(num_images: int = 5) -> None:
    images = _list_test_images()
    if not images:
        raise RuntimeError(f"No test images found in {DATA_TEST_IMAGES!s}")

    if num_images > len(images):
        num_images = len(images)

    sampled = random.sample(images, num_images)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    analyzer = DistortionAnalyzer()
    names = analyzer.metrics_names()

    for img_path in sampled:
        img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if img is None:
            print(f"[WARN] Failed to read image: {img_path!s}")
            continue

        analyzer.bind_image(image=img)
        metrics = analyzer.analyze()
        vec = analyzer.metrics_vector()

        # Prepare multi-line green text for each component
        lines = [f"{name}={value:.3f}" for name, value in zip(names, vec.tolist())]

        # Draw green text lines at top-left corner (no solid background)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        color = (0, 255, 0)  # Green in BGR
        thickness = 1
        line_type = cv2.LINE_AA

        x = 5
        y = 5
        line_spacing = 4  # extra pixels between lines

        for line in lines:
            (text_w, text_h), baseline = cv2.getTextSize(line, font, font_scale, thickness)
            # Baseline for this line: advance y by text height
            y_line = y + text_h
            cv2.putText(img, line, (x, y_line), font, font_scale, color, thickness, line_type)
            # Next line starts below current
            y = y_line + line_spacing

        out_path = OUTPUT_DIR / img_path.name
        cv2.imwrite(str(out_path), img)
        print(f"Saved: {out_path!s}")


if __name__ == "__main__":
    process_random_images(num_images=5)
