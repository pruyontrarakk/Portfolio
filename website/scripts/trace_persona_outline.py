#!/usr/bin/env python3
"""Edge-trace a portrait PNG into stroke-only SVG (Canny → contours → paths).

Requires: /usr/bin/python3 with opencv-python-headless, numpy, Pillow.
Set SRC to your reference PNG, then run to regenerate OUT_SVG.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

SRC = Path(
    "/Users/pruyontrarak/.cursor/projects/Users-pruyontrarak-Downloads-Portfolio-2/assets/269188_00_2x-229744b9-8285-4a7c-9dfc-5c6ae3b251b7.png"
)
OUT_SVG = Path(__file__).resolve().parent.parent / "assets" / "common" / "home-lily-traced.svg"
TARGET_W = 112


def main() -> None:
    if not SRC.exists():
        print("Source image missing:", SRC, file=sys.stderr)
        sys.exit(1)

    bgr = cv2.imread(str(SRC))
    if bgr is None:
        print("Could not read image", file=sys.stderr)
        sys.exit(1)

    h, w = bgr.shape[:2]
    scale = TARGET_W / w
    new_w = TARGET_W
    new_h = max(1, int(round(h * scale)))
    small = cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 5, 50, 50)
    edges = cv2.Canny(gray, 28, 84)

    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    min_len = max(10, int(0.024 * (new_w + new_h)))
    paths: list[str] = []
    for cnt in contours:
        if len(cnt) < 4:
            continue
        peri = cv2.arcLength(cnt, True)
        if peri < min_len:
            continue
        approx = cv2.approxPolyDP(cnt, 0.00135 * peri, True)
        pts = approx.reshape(-1, 2)
        if len(pts) < 2:
            continue
        segs = [f"M {pts[0][0]:.2f},{pts[0][1]:.2f}"]
        for x, y in pts[1:]:
            segs.append(f"L {x:.2f},{y:.2f}")
        d = " ".join(segs)
        paths.append(f'<path d="{d}" />')

    # Cap path count so SVG stays lightweight
    paths.sort(key=lambda s: s.count("L"), reverse=True)
    svg_inner = "\n            ".join(paths[:110])
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {new_w} {new_h}" width="{new_w}" height="{new_h}" fill="none" aria-hidden="true">
  <g stroke="#2d3e40" stroke-width="0.58" stroke-linecap="round" stroke-linejoin="round">
            {svg_inner}
  </g>
</svg>
"""
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.write_text(svg, encoding="utf-8")
    print("Wrote", OUT_SVG, "paths:", len(paths))


if __name__ == "__main__":
    main()
