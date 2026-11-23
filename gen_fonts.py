#!/usr/bin/env python3
"""Build-time font atlas generator for news-image-20261123 v6.

Renders glyphs from real open-source system fonts (Liberation family) with
PIL/FreeType and packs them into grayscale atlas PNGs plus compact metrics
blobs (zlib+base64). Runs ONLY in the builder session; the entry's main.py is
pure stdlib and blits glyphs from these atlases at runtime (no PIL there).

Atlas files written into this directory:
  atlas_<name>.png   grayscale 'L' PNG, glyph ink in white on black
  atlas_<name>.meta  one line: zlib+base64 of the metrics JSON

Metrics JSON: {"size": px, "ascent": px, "descent": px,
  "chars": {ch: [ax, ay, w, h, adv, dx, dy]}, "kern": {"AB": delta, ...}}
  ax,ay = top-left of the glyph cell inside the atlas; w,h = ink size;
  adv = advance width (float, 0.1px); dx = left bearing (ink left - origin);
  dy = ink top - baseline (negative = above baseline).
  kern deltas are in px (float, 0.1px), measured as
  getlength(a+b) - getlength(a) - getlength(b); only |delta| >= 0.5 kept.
"""

import base64
import json
import os
import sys
import zlib

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = "/usr/share/fonts/truetype/liberation"

# (atlas name, font file, pixel size)
ATLASES = [
    ("serif_b72", "LiberationSerif-Bold.ttf", 72),      # masthead
    ("serif_b40", "LiberationSerif-Bold.ttf", 40),      # stat numbers
    ("serif_b30", "LiberationSerif-Bold.ttf", 30),      # hero headlines
    ("serif_b19", "LiberationSerif-Bold.ttf", 19),      # mid headlines
    ("serif_bi20", "LiberationSerif-BoldItalic.ttf", 20),  # sub-headline
    ("serif_r11", "LiberationSerif-Regular.ttf", 11),   # briefs
    ("sans_b13", "LiberationSans-Bold.ttf", 13),        # kickers/flags/headers
    ("sans_r12", "LiberationSans-Regular.ttf", 12),     # decks
    ("sans_r11", "LiberationSans-Regular.ttf", 11),     # captions/sources
]

CHARSET = "".join(chr(c) for c in range(32, 127)) + "\u2014\u00b7\u2019\u2026\u00b0\u00d7"
# ASCII printable + em dash, middot, right quote, ellipsis, degree, multiply


def build_atlas(name, font_path, size):
    font = ImageFont.truetype(font_path, size)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent
    pad = 12
    tmp_w, tmp_h = 220, line_h + 2 * pad + 8

    cells = {}  # ch -> (ink Image, dx, dy, adv)
    for ch in CHARSET:
        adv = round(font.getlength(ch), 1)
        if ch == " ":
            cells[ch] = (None, 0, 0, adv)
            continue
        tmp = Image.new("L", (tmp_w, tmp_h), 0)
        d = ImageDraw.Draw(tmp)
        d.text((pad, pad), ch, font=font, fill=255)
        bbox = tmp.getbbox()
        if bbox is None:
            cells[ch] = (None, 0, 0, adv)
            continue
        x0, y0, x1, y1 = bbox
        ink = tmp.crop(bbox)
        dx = x0 - pad                    # ink left relative to origin
        dy = y0 - (pad + ascent)         # ink top relative to baseline
        cells[ch] = (ink, dx, dy, adv)

    # Kerning: measure every ordered pair, keep |delta| >= 0.5 px.
    kern = {}
    for a in CHARSET:
        la = font.getlength(a)
        for b in CHARSET:
            delta = font.getlength(a + b) - la - font.getlength(b)
            if abs(delta) >= 0.5:
                kern[a + b] = round(delta, 1)

    # Shelf-pack glyphs by height (tallest first), 2 px gutters.
    order = sorted(
        (ch for ch, (ink, _, _, _) in cells.items() if ink is not None),
        key=lambda c: (-cells[c][0].height, c),
    )
    atlas_w = 512
    gutter = 2
    shelves = []  # (y, height)
    pos = {}
    x = y = 0
    shelf_h = 0
    for ch in order:
        ink = cells[ch][0]
        w, h = ink.size
        if x + w > atlas_w:
            y += shelf_h + gutter
            x = 0
            shelf_h = 0
        pos[ch] = (x, y)
        x += w + gutter
        shelf_h = max(shelf_h, h)
    atlas_h = y + shelf_h + gutter
    atlas = Image.new("L", (atlas_w, atlas_h), 0)
    chars = {}
    for ch in CHARSET:
        ink, dx, dy, adv = cells[ch]
        if ink is None:
            chars[ch] = [0, 0, 0, 0, adv, 0, 0]
        else:
            ax, ay = pos[ch]
            atlas.paste(ink, (ax, ay))
            chars[ch] = [ax, ay, ink.width, ink.height, adv, dx, dy]

    atlas.save(f"atlas_{name}.png")
    meta = {
        "size": size,
        "ascent": ascent,
        "descent": descent,
        "chars": chars,
        "kern": kern,
    }
    blob = base64.b64encode(zlib.compress(json.dumps(meta).encode(), 9)).decode()
    with open(f"atlas_{name}.meta", "w") as f:
        f.write(blob + "\n")
    png_b = os.path.getsize(f"atlas_{name}.png")
    meta_b = os.path.getsize(f"atlas_{name}.meta")
    print(f"{name}: atlas {atlas_w}x{atlas_h} {png_b} B, meta {meta_b} B, "
          f"kern pairs {len(kern)}, ascent {ascent} descent {descent}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    for name, fname, size in ATLASES:
        build_atlas(name, os.path.join(FONT_DIR, fname), size)
    total = sum(
        os.path.getsize(f)
        for f in os.listdir(".")
        if f.startswith("atlas_")
    )
    print(f"TOTAL atlas bytes: {total}")


if __name__ == "__main__":
    main()
