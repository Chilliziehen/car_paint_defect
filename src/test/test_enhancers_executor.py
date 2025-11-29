"""Smoke test for applying an EnhancementPlan using concrete enhancers."""

from __future__ import annotations

from pathlib import Path

import cv2

from src.main.distortion_analyser import DistortionAnalyzer
from src.main.enhancement_strategy import EnhancementPlanner
from src.main.enhancers_executor import apply_enhancement_plan


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    sample_dir = root / "data" / "car_paint_defect" / "test" / "images"
    images = sorted(p for p in sample_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if not images:
        raise SystemExit(f"No images found in {sample_dir!s}")

    img_path = images[0]
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"Failed to read {img_path!s}")

    analyzer = DistortionAnalyzer()
    analyzer.bind_image(image=img)
    metrics = analyzer.analyze()

    planner = EnhancementPlanner()
    plan = planner.build_plan(metrics)

    enhanced = apply_enhancement_plan(img, plan)

    out_dir = root / "test_out" / "enhancement"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / img_path.name
    cv2.imwrite(str(out_path), enhanced)
    print(f"Saved enhanced image to {out_path!s}")


if __name__ == "__main__":
    main()

