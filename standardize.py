#!/usr/bin/env python3
"""
BoatCarpet pattern standardizer.

Input:  one CMC pattern image (jpg/png) + make + model + suggested year range
Output: clean.webp at TARGET_WIDTH px wide, pure-white bg, fresh "Make Model"
        caption baked at bottom, plus a sidecar metadata.json.

What it does:
  1. Crop off any existing caption (anything below the main pattern shape).
  2. Trim whitespace to the pattern's bounding box + uniform margin.
  3. Upscale to TARGET_WIDTH with Lanczos.
  4. Background-snap: pixels with gray >= 220 -> pure white. Lines kept
     with their anti-alias band intact (50-220 range untouched). Dark
     pixels <= 80 pulled to pure black for crispness.
  5. Bake fresh caption "Make Model" centered at bottom in sans-serif.
  6. Save as .webp at quality 95.
  7. Write sidecar .json with year range, source filename, etc.

Year verification (manufacturer lookup) is a separate step — this script
accepts a year range as input and records it. The web-lookup pass happens
in the wrapper that calls this.

CHANGELOG
  2026-05-16  Caption-crop fix. The old logic only inspected the single
              last ink-row run, so it removed only ONE caption line. CMC
              screenshots have TWO-line captions ("Make Model" / "2003 to
              2007 +-"), which left a garbled doubled caption baked into
              output. New logic finds the largest run (= the pattern body)
              and peels EVERY trailing caption-sized run (<= 9% of image
              height) below it. Verified end-to-end on Four Winns 190
              Horizon: clean single caption + correct flood-fill color.
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

TARGET_WIDTH = 1400
WHITE_THRESHOLD = 220   # gray >= this -> snap to pure white
BLACK_THRESHOLD = 80    # gray <= this -> snap to pure black
MARGIN_PCT = 0.04       # whitespace margin around pattern bbox
CAPTION_BAND_PCT = 0.10 # space reserved at bottom for fresh caption
CAPTION_FONT_PCT = 0.035 # caption font height as fraction of image width
WEBP_QUALITY = 95


@dataclass
class Metadata:
    make: str
    model: str
    slug: str
    year_range: str         # e.g. "2003-2007"
    cmc_filename: str       # original source filename
    verified_years: str     # manufacturer-verified range (filled by wrapper)
    generation_label: str   # optional human label (e.g. "Gen 2")
    manufacturer_source: str  # URL or note re: where years were verified


def slugify(make: str, model: str) -> str:
    s = f"{make}-{model}".lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def find_main_shape_bbox(arr: np.ndarray) -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) of the main pattern, excluding any
    bottom caption band.

    A pattern may contain multiple disconnected pieces stacked vertically
    (e.g., bow piece + cockpit piece). We keep ALL pattern pieces; we only
    drop a caption.

    Heuristic for caption detection: find contiguous runs of ink rows. The
    caption — if present — is the LAST (bottom-most) run, is short
    (~caption font height), and is separated from the run above it by a
    visible gap.
    """
    gray = arr.mean(axis=2) if arr.ndim == 3 else arr
    h, w = gray.shape
    row_has_ink = (gray < 180).any(axis=1)

    if not row_has_ink.any():
        return (0, 0, w, h)

    # Identify contiguous runs of ink rows
    runs = []
    in_run = False
    start = 0
    for i, ink in enumerate(row_has_ink):
        if ink and not in_run:
            in_run = True
            start = i
        elif not ink and in_run:
            in_run = False
            runs.append((start, i))
    if in_run:
        runs.append((start, len(row_has_ink)))

    if not runs:
        return (0, 0, w, h)

    # Determine which trailing runs are caption lines to drop.
    #
    # The pattern is the single LARGEST run (by far the tallest block of
    # ink). Captions are one or more SHORT text-line runs that sit BELOW
    # the pattern, each separated by a gap. CMC screenshots frequently
    # have a TWO-line caption ("Make Model" on line 1, "2003 to 2007 +-"
    # on line 2), so we must peel off *every* trailing caption-sized run,
    # not just the last one.
    #
    # Algorithm:
    #   1. Find the index of the largest run -> that's the pattern body.
    #   2. Everything after the pattern body that is short (one text line
    #      tall, < 9% of image height) is caption -> drop it.
    #   3. The kept region ends at the bottom of the last NON-caption run
    #      at or before the pattern body.
    top = runs[0][0]
    bottom = runs[-1][1]

    if len(runs) >= 2:
        # Index of the tallest run = the pattern shape.
        heights = [e - s for (s, e) in runs]
        body_idx = int(np.argmax(heights))

        # Walk runs AFTER the body; any short one is a caption line.
        # Stop keeping at the body's end, then extend only through runs
        # that are clearly NOT caption (tall enough to be pattern, e.g.
        # a detached small pattern piece would be unusual but we guard).
        CAPTION_MAX_H = h * 0.09  # one line of caption text

        last_keep_end = runs[body_idx][1]
        for idx in range(body_idx + 1, len(runs)):
            s, e = runs[idx]
            run_h = e - s
            if run_h <= CAPTION_MAX_H:
                # caption-sized: drop it (do not extend bottom)
                continue
            else:
                # a substantial run below the body — treat as real
                # pattern content (rare) and keep it
                last_keep_end = e
        bottom = last_keep_end

    # Horizontal bbox: use ink cols within the kept vertical span only
    sub = gray[top:bottom]
    col_has_ink_sub = (sub < 180).any(axis=0)
    if not col_has_ink_sub.any():
        return (0, top, w, bottom)
    left = int(np.argmax(col_has_ink_sub))
    right = int(w - np.argmax(col_has_ink_sub[::-1]))
    return (left, top, right, bottom)


def crop_with_margin(im: Image.Image, bbox: tuple[int, int, int, int],
                     margin_pct: float) -> Image.Image:
    l, t, r, b = bbox
    w_box = r - l
    h_box = b - t
    side = max(w_box, h_box)
    margin = int(side * margin_pct)
    W, H = im.size
    new_l = max(0, l - margin)
    new_t = max(0, t - margin)
    new_r = min(W, r + margin)
    new_b = min(H, b + margin)
    return im.crop((new_l, new_t, new_r, new_b))


def snap_levels(arr: np.ndarray) -> np.ndarray:
    """White-snap and black-snap, preserve anti-alias band."""
    out = arr.copy()
    gray = out.mean(axis=2) if out.ndim == 3 else out
    if out.ndim == 3:
        white_mask = gray >= WHITE_THRESHOLD
        black_mask = gray <= BLACK_THRESHOLD
        out[white_mask] = [255, 255, 255]
        out[black_mask] = [0, 0, 0]
    else:
        out[gray >= WHITE_THRESHOLD] = 255
        out[gray <= BLACK_THRESHOLD] = 0
    return out


def resize_to_width(im: Image.Image, target_w: int) -> Image.Image:
    w, h = im.size
    if w == target_w:
        return im
    new_h = int(round(h * target_w / w))
    return im.resize((target_w, new_h), Image.LANCZOS)


def load_font(size_px: int) -> ImageFont.FreeTypeFont:
    """Try common sans-serif faces; fall back to PIL default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size_px)
    return ImageFont.load_default()


def add_caption(im: Image.Image, caption: str) -> Image.Image:
    """Add a caption band at the bottom of the image with 'Make Model' text."""
    W, H = im.size
    band_h = int(W * CAPTION_BAND_PCT)
    font_px = int(W * CAPTION_FONT_PCT)
    font = load_font(font_px)

    canvas = Image.new("RGB", (W, H + band_h), (255, 255, 255))
    canvas.paste(im, (0, 0))
    draw = ImageDraw.Draw(canvas)

    # Center the text in the band
    bbox = draw.textbbox((0, 0), caption, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (W - text_w) // 2 - bbox[0]
    y = H + (band_h - text_h) // 2 - bbox[1]
    draw.text((x, y), caption, fill=(0, 0, 0), font=font)
    return canvas


def standardize(src_path: Path, make: str, model: str, year_range: str,
                out_dir: Path,
                generation_label: str = "",
                verified_years: str = "",
                manufacturer_source: str = "") -> tuple[Path, Path]:
    im = Image.open(src_path).convert("RGB")
    arr = np.array(im)

    # 1. Find main pattern bbox (drops bottom caption)
    bbox = find_main_shape_bbox(arr)

    # 2. Crop with margin
    cropped = crop_with_margin(im, bbox, MARGIN_PCT)

    # 3. Upscale BEFORE level-snap so anti-aliasing benefits from
    #    Lanczos's wider sample window
    upscaled = resize_to_width(cropped, TARGET_WIDTH)

    # 4. Snap background to pure white, lines to pure black
    snapped = Image.fromarray(snap_levels(np.array(upscaled)))

    # 5. Add fresh caption
    final = add_caption(snapped, f"{make} {model}")

    # 6. Save
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(make, model)
    out_img = out_dir / f"{slug}.webp"
    final.save(out_img, "WEBP", quality=WEBP_QUALITY, method=6)

    meta = Metadata(
        make=make,
        model=model,
        slug=slug,
        year_range=year_range,
        cmc_filename=src_path.name,
        verified_years=verified_years or year_range,
        generation_label=generation_label,
        manufacturer_source=manufacturer_source,
    )
    out_meta = out_dir / f"{slug}.json"
    out_meta.write_text(json.dumps(asdict(meta), indent=2))

    return out_img, out_meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path, help="Source CMC image (jpg/png)")
    ap.add_argument("--make", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--years", required=True,
                    help='e.g. "2003-2007" — CMC-suggested range')
    ap.add_argument("--out", type=Path, default=Path("./out"))
    ap.add_argument("--generation", default="")
    ap.add_argument("--verified-years", default="")
    ap.add_argument("--source-note", default="")
    args = ap.parse_args()

    out_img, out_meta = standardize(
        args.source, args.make, args.model, args.years,
        args.out,
        generation_label=args.generation,
        verified_years=args.verified_years,
        manufacturer_source=args.source_note,
    )
    print(f"  image:    {out_img}")
    print(f"  metadata: {out_meta}")


if __name__ == "__main__":
    main()
