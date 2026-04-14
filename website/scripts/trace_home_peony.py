#!/usr/bin/env python3
"""Edge-trace the home hero peony PNG into stroke-only SVG (Canny → contours).

Requires: opencv-python-headless, numpy (same as trace_persona_outline.py).
Set SRC to your peony PNG, then run to regenerate OUT_SVG.

Default SRC looks for the asset next to this repo under .cursor/projects/…;
override with: python trace_home_peony.py /path/to/peony.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = REPO_ROOT / "assets" / "common" / "home-peony-traced.svg"

# Cursor chat image drop (same pattern as trace_persona_outline.py)
_DEFAULT_CURSOR_ASSET = (
    Path.home()
    / ".cursor"
    / "projects"
    / "Users-pruyontrarak-Downloads-Portfolio-2"
    / "assets"
    / "image-8e0f94ca-ccc2-4f19-95d7-632f8e69966d.png"
)
# Fallback: raw PNG committed by sync script / manual copy
_FALLBACK_REPO_PNG = REPO_ROOT / "assets" / "common" / "home-peony.png"

TARGET_W = 170
# Darker forest green (matches hero text family); reads clearly on pink
STROKE = "#1a2f28"
# Thin at large CSS scale; nudge up if you regenerate at higher TARGET_W
STROKE_W = "0.34"


def _default_src() -> Path:
    if _DEFAULT_CURSOR_ASSET.is_file():
        return _DEFAULT_CURSOR_ASSET
    if _FALLBACK_REPO_PNG.is_file():
        return _FALLBACK_REPO_PNG
    return _DEFAULT_CURSOR_ASSET


def main() -> None:
    ap = argparse.ArgumentParser(description="Trace peony PNG → home-peony-traced.svg")
    ap.add_argument(
        "src",
        nargs="?",
        type=Path,
        default=None,
        help="Source peony PNG (defaults: Cursor asset or assets/common/home-peony.png)",
    )
    args = ap.parse_args()
    src = (args.src or _default_src()).expanduser().resolve()

    if not src.is_file():
        print("Source image missing:", src, file=sys.stderr)
        print("Pass a path: python trace_home_peony.py /path/to/peony.png", file=sys.stderr)
        sys.exit(1)

    bgr = cv2.imread(str(src))
    if bgr is None:
        print("Could not read image", src, file=sys.stderr)
        sys.exit(1)

    h, w = bgr.shape[:2]
    scale = TARGET_W / w
    new_w = TARGET_W
    new_h = max(1, int(round(h * scale)))
    small = cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 60, 60)
    # Soft subject + white backdrop: gentler Canny + fallback Sobel magnitude
    edges = cv2.Canny(gray, 12, 40)
    if np.count_nonzero(edges) < 0.004 * edges.size:
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(gx, gy)
        mag_u8 = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        _, edges = cv2.threshold(mag_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    min_len = max(8, int(0.014 * (new_w + new_h)))
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

    paths.sort(key=lambda s: s.count("L"), reverse=True)
    max_paths = 160
    svg_inner = "\n            ".join(paths[:max_paths])
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {new_w} {new_h}" width="{new_w}" height="{new_h}" fill="none" aria-hidden="true">
  <g stroke="{STROKE}" stroke-width="{STROKE_W}" stroke-linecap="round" stroke-linejoin="round">
            {svg_inner}
  </g>
</svg>
"""
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.write_text(svg, encoding="utf-8")
    print("Wrote", OUT_SVG, "from", src, "paths kept:", min(len(paths), max_paths))


if __name__ == "__main__":
    main()
