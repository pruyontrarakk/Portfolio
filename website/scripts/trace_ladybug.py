#!/usr/bin/env python3
"""Edge-trace a ladybug photo into stroke-only SVG (same pipeline idea as trace_home_peony.py).

Finds the insect with a warm/red + not-yellow mask (works on yellow paper), runs
Canny on the full grayscale, keeps contours whose centroid lies inside a dilated bug
mask, then approxPolyDP → L-only paths. Output: floral-style ink (#242028), fill none.

Requires: opencv-python-headless, numpy

  python trace_ladybug.py
  python trace_ladybug.py /path/to/ladybug.png

Default source: assets/common/ladybug-source.png
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = REPO_ROOT / "assets" / "common" / "ladybug-traced.svg"
_DEFAULT_SRC = REPO_ROOT / "assets" / "common" / "ladybug-source.png"

TARGET_W = 168
STROKE = "#242028"
STROKE_W = "1.32"
MAX_PATHS = 160

# Photo legs are drawn separately in HTML; drop traced leg-only contours from SVG output.
_SKIP_PATH_D_PREFIXES: tuple[str, ...] = (
    "M 44.00,69.00",
    "M 117.00,81.00",
    "M 136.00,99.00",
    "M 127.00,68.00",
    "M 91.00,89.00",
    "M 69.00,66.00",
    "M 49.00,60.00",
    "M 72.00,59.00",
    "M 122.00,108.00",
    "M 119.00,121.00",
    "M 47.00,115.00",
    "M 73.00,68.00",
    "M 64.00,65.00",
    "M 100.00,10.00",
    "M 79.00,145.00",
    "M 50.00,128.00",
    "M 40.00,106.00",
    "M 51.00,55.00",
    "M 61.00,53.00",
    "M 73.00,31.00",
)


def _skip_leg_like_contour(cnt: np.ndarray, iw: int, ih: int) -> bool:
    """Heuristic: tangled mid-height blobs on far left/right (traced photo legs)."""
    m = cv2.moments(cnt)
    if m["m00"] == 0:
        return False
    cx = m["m10"] / m["m00"]
    cy = m["m01"] / m["m00"]
    n = len(cnt)
    area = abs(cv2.contourArea(cnt))
    if n < 50 or area < 400:
        return False
    mid_y = 0.22 * ih < cy < 0.78 * ih
    side = cx < 0.34 * iw or cx > 0.66 * iw
    if mid_y and side and area < 0.22 * iw * ih:
        return True
    return False


def _bug_region_mask(bgr: np.ndarray) -> np.ndarray:
    """255 ≈ ladybug (red shell, dark head/legs) — excludes bright yellow backgrounds."""
    B, G, R = cv2.split(bgr)
    r = R.astype(np.int16)
    g = G.astype(np.int16)
    b = B.astype(np.int16)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # Warm red shell (R ahead of G)
    warm = (r - g > 8) & (R > 55)
    # Dark paint (head, spots, legs) on light paper
    dark = gray.astype(np.int16) < 175
    # Yellow paper: high R+G, B clearly lower than both
    yellow = (R > 110) & (G > 110) & (b < r - 22) & (b < g - 22)
    fg = warm | (dark & ~yellow)
    m = fg.astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    m = cv2.dilate(m, k, iterations=3)
    return m


def _contour_on_bug(cnt: np.ndarray, bug_mask: np.ndarray) -> bool:
    """Centroid inside dilated bug mask and enough edge pixels lie on the bug."""
    m = cv2.moments(cnt)
    if m["m00"] == 0:
        return False
    cx = int(m["m10"] / m["m00"])
    cy = int(m["m01"] / m["m00"])
    h, w = bug_mask.shape[:2]
    if cx < 0 or cy < 0 or cx >= w or cy >= h:
        return False
    if bug_mask[cy, cx] == 0:
        return False
    core = cv2.erode(bug_mask, np.ones((5, 5), np.uint8), iterations=1)
    cm = np.zeros_like(bug_mask)
    cv2.drawContours(cm, [cnt], 0, 255, thickness=1)
    inter = int(np.count_nonzero((cm > 0) & (core > 0)))
    drawn = int(np.count_nonzero(cm > 0))
    if drawn < 1:
        return False
    return (inter / drawn) >= 0.28


def _bbox_of_contours(contours: list[np.ndarray], pad: int, w: int, h: int) -> tuple[int, int, int, int]:
    xs: list[int] = []
    ys: list[int] = []
    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        xs.extend([x, x + cw])
        ys.extend([y, y + ch])
    if not xs:
        return 0, 0, w, h
    x0 = max(0, min(xs) - pad)
    y0 = max(0, min(ys) - pad)
    x1 = min(w, max(xs) + pad)
    y1 = min(h, max(ys) + pad)
    return x0, y0, x1, y1


def main() -> None:
    ap = argparse.ArgumentParser(description="Trace ladybug PNG → ladybug-traced.svg")
    ap.add_argument(
        "src",
        nargs="?",
        type=Path,
        default=None,
        help="Source PNG (default: assets/common/ladybug-source.png)",
    )
    args = ap.parse_args()
    src = (args.src or _DEFAULT_SRC).expanduser().resolve()

    if not src.is_file():
        print("Source image missing:", src, file=sys.stderr)
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
    bug_mask = _bug_region_mask(small)

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 55, 55)

    edges = cv2.Canny(gray, 12, 38)
    if np.count_nonzero(edges) < 0.0025 * edges.size:
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag = cv2.magnitude(gx, gy)
        mag_u8 = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        _, edges = cv2.threshold(mag_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    min_len = max(6, int(0.009 * (new_w + new_h)))

    kept_cnts: list[np.ndarray] = []
    for cnt in contours:
        if len(cnt) < 4:
            continue
        peri = cv2.arcLength(cnt, True)
        if peri < min_len:
            continue
        if not _contour_on_bug(cnt, bug_mask):
            continue
        pts = cnt.reshape(-1, 2)
        ymin = int(pts[:, 1].min())
        xmean = float(pts[:, 0].mean())
        # Drop top-of-crop glints that sit mostly on the leaf margin (not the bug)
        if ymin <= 2 and xmean < 46.0:
            continue
        if ymin <= 2 and xmean > 94.0:
            continue
        if _skip_leg_like_contour(cnt, new_w, new_h):
            continue
        kept_cnts.append(cnt)

    if not kept_cnts:
        print("No contours passed bug mask; try a clearer photo.", file=sys.stderr)
        sys.exit(2)

    x0, y0, x1, y1 = _bbox_of_contours(kept_cnts, pad=10, w=new_w, h=new_h)
    cw = max(1, x1 - x0)
    ch = max(1, y1 - y0)

    paths: list[str] = []
    for cnt in kept_cnts:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.00135 * peri, True)
        pts = approx.reshape(-1, 2)
        if len(pts) < 2:
            continue
        pts = pts.astype(np.float64)
        pts[:, 0] -= x0
        pts[:, 1] -= y0
        segs = [f"M {pts[0][0]:.2f},{pts[0][1]:.2f}"]
        for px, py in pts[1:]:
            segs.append(f"L {px:.2f},{py:.2f}")
        d = " ".join(segs)
        paths.append(f'<path d="{d}" />')

    paths.sort(key=lambda s: s.count("L"), reverse=True)

    def _path_d_attr(p_el: str) -> str:
        m = re.search(r'd="([^"]*)"', p_el)
        return m.group(1).strip() if m else ""

    paths = [p for p in paths if not any(_path_d_attr(p).startswith(pre) for pre in _SKIP_PATH_D_PREFIXES)]
    kept_paths = paths[:MAX_PATHS]
    svg_inner = "\n            ".join(kept_paths)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw} {ch}" width="{cw}" height="{ch}" fill="none" aria-hidden="true">
  <g id="ladybug-trace" stroke="{STROKE}" stroke-width="{STROKE_W}" stroke-linecap="round" stroke-linejoin="round">
            {svg_inner}
  </g>
</svg>
"""
    OUT_SVG.parent.mkdir(parents=True, exist_ok=True)
    OUT_SVG.write_text(svg, encoding="utf-8")
    print(
        "Wrote",
        OUT_SVG,
        "from",
        src,
        "viewBox",
        f"0 0 {cw} {ch}",
        "paths:",
        len(kept_paths),
    )
    if kept_cnts:
        areas = [(cv2.contourArea(c), c) for c in kept_cnts]
        _, main_cnt = max(areas, key=lambda t: t[0])
        m = cv2.moments(main_cnt)
        if m["m00"] > 0:
            cx = m["m10"] / m["m00"] - x0
            cy = m["m01"] / m["m00"] - y0
            print(f"Hint: largest-shape centroid (trace space) ≈ ({cx:.1f}, {cy:.1f}) — align leg anchors nearby.")


if __name__ == "__main__":
    main()
