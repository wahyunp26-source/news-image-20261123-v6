#!/usr/bin/env python3
"""news-image-20261123 v6 — one-day world news front page, pure stdlib.

Renders Monday 23 November 2026 as a classic newspaper front page
(1024x1024 PNG) using REAL typefaces: glyphs are blitted from atlas PNGs
built in the builder session from the open-source Liberation fonts
(see gen_fonts.py). No PIL, no network, no randomness at runtime:
running main.py twice writes byte-identical entry.png.

Usage: python3 main.py  ->  writes /output/entry.png if /output exists,
else ./entry.png (local preview).
"""

import base64
import json
import math
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- PNG I/O

def _chunk(ctype, data):
    c = struct.pack(">I", len(data)) + ctype + data
    return c + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)


def png_encode_rgb(w, h, rgb):
    """rgb: bytes/bytearray of w*h*3. Returns PNG bytes (filter 0 rows)."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
        + _chunk(b"IEND", b"")
    )


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def png_decode_gray(path):
    """Decode an 8-bit grayscale non-interlaced PNG. Returns (w, h, rows).

    rows: list of bytes, one per scanline, each w bytes (0..255 alpha).
    """
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, idat, w, h, bitdepth, ctype = 8, b"", 0, 0, 0, 0
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype_b = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if ctype_b == b"IHDR":
            w, h, bitdepth, ctype = struct.unpack(">IIBB", body[:10])
        elif ctype_b == b"IDAT":
            idat += body
        elif ctype_b == b"IEND":
            break
        pos += 12 + ln
    assert bitdepth == 8 and ctype == 0, "expected 8-bit grayscale PNG"
    raw = zlib.decompress(idat)
    rows = []
    prev = bytearray(w)
    off = 0
    for _ in range(h):
        ftype = raw[off]
        off += 1
        line = bytearray(raw[off:off + w])
        off += w
        if ftype == 0:
            pass
        elif ftype == 1:
            for i in range(1, w):
                line[i] = (line[i] + line[i - 1]) & 0xFF
        elif ftype == 2:
            for i in range(w):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:
            for i in range(w):
                left = line[i - 1] if i else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(w):
                a = line[i - 1] if i else 0
                b = prev[i]
                c = prev[i - 1] if i else 0
                line[i] = (line[i] + _paeth(a, b, c)) & 0xFF
        else:
            raise ValueError("bad PNG filter %d" % ftype)
        rows.append(bytes(line))
        prev = line
    return w, h, rows


# ---------------------------------------------------------------- Canvas

CREAM = (247, 242, 231)
PAPER = (250, 246, 236)
NAVY = (26, 35, 64)
NAVY2 = (38, 52, 96)
RED = (179, 35, 27)
RED2 = (200, 60, 45)
INK = (30, 30, 34)
GREY = (110, 105, 95)
LGREY = (200, 194, 182)
WHITE = (255, 255, 255)
SKY = (198, 220, 232)
SKY2 = (168, 198, 220)
TEAL = (32, 96, 104)
SEA = (24, 68, 88)
DUSK = (232, 122, 54)
DUSK2 = (242, 166, 84)
GOLD = (232, 178, 62)
GREEN = (46, 110, 62)
BROWN = (122, 82, 52)
TAN = (214, 186, 138)


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return tuple(self.px[i:i + 3])

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def ellipse(self, cx, cy, rx, ry, c):
        # filled ellipse, scanline
        for yy in range(cy - ry, cy + ry + 1):
            if yy < 0 or yy >= self.h:
                continue
            t = (yy - cy) / float(ry) if ry else 0.0
            if abs(t) > 1:
                continue
            dx = int(rx * math.sqrt(1 - t * t))
            self.rect(cx - dx, yy, 2 * dx + 1, 1, c)

    def circle(self, cx, cy, r, c):
        self.ellipse(cx, cy, r, r, c)

    def ring(self, cx, cy, r, c, t=1):
        for yy in range(cy - r - t, cy + r + t + 1):
            for xx in range(cx - r - t, cx + r + t + 1):
                d = math.hypot(xx - cx, yy - cy)
                if r - t <= d <= r + t:
                    self.set(xx, yy, c)

    def poly(self, pts, c):
        # filled polygon, scanline
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for yy in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    if y1 != y0:
                        xs.append(x0 + (yy - y0) * (x1 - x0) / float(y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(math.ceil(xs[i])), yy,
                          max(0, int(xs[i + 1]) - int(math.ceil(xs[i]))), 1, c)

    def blend(self, x, y, c, a):
        """Blend colour c over pixel (x, y) with alpha a (0..255)."""
        if a <= 0 or not (0 <= x < self.w and 0 <= y < self.h):
            return
        if a >= 255:
            self.set(x, y, c)
            return
        i = (y * self.w + x) * 3
        b = self.px
        b[i] = (c[0] * a + b[i] * (255 - a)) // 255
        b[i + 1] = (c[1] * a + b[i + 1] * (255 - a)) // 255
        b[i + 2] = (c[2] * a + b[i + 2] * (255 - a)) // 255


# ---------------------------------------------------------------- Text (atlas)

_ATLASES = {}


def load_atlas(name):
    if name in _ATLASES:
        return _ATLASES[name]
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "atlas_" + name)
    w, h, rows = png_decode_gray(base + ".png")
    with open(base + ".meta") as f:
        meta = json.loads(zlib.decompress(base64.b64decode(f.read().strip())))
    atlas = (w, h, rows, meta)
    _ATLASES[name] = atlas
    return atlas


def text_width(text, atlas_name):
    _, _, _, meta = load_atlas(atlas_name)
    chars, kern = meta["chars"], meta["kern"]
    total, prev = 0.0, None
    for ch in text:
        if prev is not None:
            total += kern.get(prev + ch, 0.0)
        total += chars.get(ch, chars["?"])[4]
        prev = ch
    return total


def draw_text(cv, x, baseline, text, atlas_name, color, align="left"):
    """Draw text with baseline at y; align left/center/right around x."""
    _, _, rows, meta = load_atlas(atlas_name)
    chars, kern = meta["chars"], meta["kern"]
    w = text_width(text, atlas_name)
    if align == "center":
        x = x - w / 2.0
    elif align == "right":
        x = x - w
    px, prev = float(x), None
    for ch in text:
        if prev is not None:
            px += kern.get(prev + ch, 0.0)
        cell = chars.get(ch)
        if cell is None:
            cell = chars["?"]
        ax, ay, gw, gh, adv, dx, dy = cell
        if gw and gh:
            gx = int(round(px + dx))
            gy = int(round(baseline + dy))
            for row in range(gh):
                rowdata = rows[ay + row]
                yy = gy + row
                if yy < 0 or yy >= cv.h:
                    continue
                for col in range(gw):
                    a = rowdata[ax + col]
                    if a:
                        cv.blend(gx + col, yy, color, a)
        px += adv
        prev = ch
    return w


class WrapError(Exception):
    pass


def wrap_text(text, atlas_name, max_w, max_lines):
    """Word-boundary wrap only. Raises WrapError if a single word is too
    wide or the text needs more than max_lines lines. Never splits a word."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, atlas_name) <= max_w:
            cur = trial
        else:
            if not cur:
                raise WrapError("word too wide: %r in %s" % (word, atlas_name))
            lines.append(cur)
            cur = word
            if text_width(cur, atlas_name) > max_w:
                raise WrapError("word too wide: %r in %s" % (word, atlas_name))
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        raise WrapError("needs %d lines, max %d: %r"
                        % (len(lines), max_lines, text))
    # Widow control: never leave a bare "(Source)" alone on the last line.
    # Pull the previous line's last word down, if it still fits.
    if len(lines) > 1:
        import re as _re
        if _re.fullmatch(r"\([^)]*\)", lines[-1]):
            prev_words = lines[-2].split(" ")
            if len(prev_words) > 1:
                moved = prev_words[-1] + " " + lines[-1]
                if text_width(moved, atlas_name) <= max_w:
                    lines[-2] = " ".join(prev_words[:-1])
                    lines[-1] = moved
    return lines


def draw_wrapped(cv, x, y_top, text, atlas_name, color, max_w, max_lines,
                 line_h, align="left"):
    lines = wrap_text(text, atlas_name, max_w, max_lines)
    _, _, _, meta = load_atlas(atlas_name)
    ascent = meta["ascent"]
    for i, line in enumerate(lines):
        baseline = y_top + ascent + i * line_h
        draw_text(cv, x, baseline, line, atlas_name, color, align)
    return lines


# ---------------------------------------------------------------- Scenes
# All scenes are flat vector, drawn with the canvas primitives.
# Each takes the top-left corner and size of its box.

def _fig(cv, x, y, s, suit, skin=(232, 196, 160)):
    """Small seated delegate figure, s = height in px."""
    hw = max(2, s // 5)
    cv.circle(x, y - s + hw, hw, skin)            # head
    cv.poly([(x - hw - 1, y), (x + hw + 1, y),
             (x + hw, y - s + 2 * hw), (x - hw, y - s + 2 * hw)], suit)


def scene_cop31(cv, x, y, w, h):
    cv.rect(x, y, w, h, (216, 228, 236))          # pale hall
    cv.rect(x, y, w, 26, (188, 204, 220))         # ceiling band
    for i in range(4):                            # windows
        wx = x + 14 + i * (w - 28) // 4
        cv.rect(wx, y + 34, (w - 28) // 4 - 12, 62, (240, 244, 248))
        cv.rect(wx, y + 34, (w - 28) // 4 - 12, 6, (150, 170, 190))
        cv.circle(wx + 16, y + 56, 7, GOLD)       # sun through window
    cv.rect(x, y + h - 26, w, 26, (146, 110, 74))  # table
    cv.rect(x, y + h - 30, w, 4, (110, 80, 52))
    suits = [(38, 52, 96), (90, 40, 44), (46, 96, 62), (120, 70, 30), (60, 60, 70)]
    for i, s in enumerate(suits):
        _fig(cv, x + 34 + i * 56, y + h - 30, 30, s)
    cv.circle(x + 26, y + h - 44, 13, (96, 160, 200))  # globe
    cv.ellipse(x + 26, y + h - 44, 13, 5, (60, 120, 170))
    cv.vline(x + 26, y + h - 58, 15, (90, 90, 90))
    cv.circle(x + w - 34, y + 52, 12, WHITE)      # clock
    cv.ring(x + w - 34, y + 52, 12, INK)
    cv.line(x + w - 34, y + 52, x + w - 34, y + 44, INK)
    cv.line(x + w - 34, y + 52, x + w - 28, y + 56, INK)
    cv.rect(x + w - 52, y + 40, 5, 34, (200, 200, 200))  # thermometer
    cv.rect(x + w - 52, y + 58, 5, 16, RED)
    cv.circle(x + w - 49, y + 76, 5, RED)


def scene_dymer(cv, x, y, w, h):
    cv.rect(x, y, w, h, (14, 20, 44))             # night
    cv.circle(x + w - 44, y + 24, 11, (240, 236, 210))  # moon
    cv.circle(x + w - 48, y + 21, 9, (14, 20, 44))
    for i in range(14):                           # stars
        sx = x + 8 + (i * 37) % (w - 16)
        sy = y + 6 + (i * 23) % 34
        cv.set(sx, sy, (220, 220, 200))
    cv.poly([(x + w - 120, y + h), (x + w - 30, y + 18),
             (x + w - 18, y + 22), (x + w - 88, y + h)], (232, 226, 190))  # beam
    bw = [86, 64, 104]
    bx = [x + 12, x + 112, x + 196]
    for bxx, bww in zip(bx, bw):
        cv.rect(bxx, y + 62, bww, h - 62, (24, 32, 62))   # buildings
        for r in range(4):
            for c in range(bww // 18):
                lit = (r * 3 + c) % 3 != 0
                cv.rect(bxx + 8 + c * 18, y + 70 + r * 18, 9, 11,
                        GOLD if lit else (44, 54, 90))
    cv.poly([(x + 150, y + 30), (x + 162, y + 36), (x + 150, y + 42),
             (x + 140, y + 36)], (150, 150, 150))  # drone
    cv.circle(x + 150, y + 36, 3, (90, 90, 90))
    cv.poly([(x + 120, y + 130), (x + 150, y + 118), (x + 170, y + 130),
             (x + 150, y + 140)], (60, 60, 70))   # debris
    cv.circle(x + 250, y + 120, 5, (200, 90, 40))  # fire glow


def scene_gulf(cv, x, y, w, h):
    cv.rect(x, y, w, 62, (240, 140, 60))          # dusk sky
    cv.rect(x, y + 62, w, 26, (232, 110, 60))
    cv.circle(x + w - 60, y + 40, 26, (250, 210, 120))  # sun
    cv.rect(x, y + 88, w, h - 88, (18, 74, 96))   # sea
    cv.rect(x, y + 88, w, 4, (40, 110, 130))
    cv.poly([(x + 30, y + 108), (x + 250, y + 108), (x + 238, y + 128),
             (x + 44, y + 128)], (20, 26, 44))    # tanker hull
    cv.rect(x + 52, y + 92, 34, 16, (200, 60, 40))
    cv.rect(x + 92, y + 92, 34, 16, (60, 140, 80))
    cv.rect(x + 132, y + 92, 34, 16, (230, 180, 60))
    cv.rect(x + 172, y + 92, 34, 16, (220, 220, 220))
    cv.rect(x + 250, y + 96, 14, 12, (30, 30, 40))  # bridge
    cv.line(x + 60, y + 30, x + 92, y + 62, (255, 240, 200))  # missile
    cv.line(x + 120, y + 22, x + 140, y + 58, (255, 240, 200))
    cv.circle(x + 92, y + 62, 3, (255, 220, 120))
    cv.circle(x + 140, y + 58, 3, (255, 220, 120))
    cv.ellipse(x + 210, y + 118, 16, 4, (120, 150, 160))  # wake
    cv.ellipse(x + 90, y + 130, 20, 4, (120, 150, 160))


def scene_ship(cv, x, y, w, h):
    cv.rect(x, y, w, h, (150, 170, 185))
    cv.rect(x, y + h - 22, w, 22, (70, 100, 125))
    cv.poly([(x + 30, y + h - 22), (x + w - 30, y + h - 22),
             (x + w - 48, y + h - 8), (x + 48, y + h - 8)], (140, 40, 36))
    cv.rect(x + 60, y + h - 40, 60, 18, (160, 50, 44))
    cv.poly([(x + 120, y + 8), (x + 128, y + 22), (x + 112, y + 22)], (240, 120, 30))
    cv.ellipse(x + 108, y + 4, 14, 8, (250, 180, 60))
    cv.ellipse(x + 140, y + 14, 10, 6, (200, 200, 200))


def scene_strike(cv, x, y, w, h):
    cv.rect(x, y, w, h, (120, 118, 112))
    cv.rect(x + 20, y + 18, 60, h - 18, (70, 70, 76))
    cv.rect(x + 92, y + 28, 56, h - 28, (84, 84, 90))
    for r in range(3):
        for c in range(3):
            cv.rect(x + 28 + c * 18, y + 26 + r * 14, 8, 8,
                    GOLD if (r + c) % 2 else (40, 40, 48))
    cv.poly([(x + 120, y + 6), (x + 132, y + 20), (x + 110, y + 20)], (240, 120, 30))
    cv.ellipse(x + 104, y + 2, 16, 9, (250, 180, 60))
    cv.ellipse(x + 140, y + 16, 14, 8, (190, 190, 190))


def scene_boat(cv, x, y, w, h):
    cv.rect(x, y, w, h, (140, 190, 210))
    cv.rect(x, y + 34, w, h - 34, (40, 110, 150))
    cv.poly([(x + 40, y + 30), (x + 150, y + 30), (x + 138, y + 48),
             (x + 52, y + 48)], (120, 80, 50))
    cv.rect(x + 88, y + 16, 6, 16, (90, 60, 40))
    for i in range(4):
        cv.ellipse(x + 10 + i * 44, y + h - 12, 18, 4, (200, 225, 240))
    cv.circle(x + 150, y + 14, 9, GOLD)


def scene_space(cv, x, y, w, h):
    cv.rect(x, y, w, h, (10, 12, 28))
    for i in range(12):
        cv.set(x + 6 + (i * 53) % (w - 12), y + 4 + (i * 29) % (h - 8), WHITE)
    cv.circle(x + w - 44, y + h - 22, 15, (210, 110, 50))
    cv.circle(x + w - 48, y + h - 26, 4, (170, 80, 30))
    cv.circle(x + w - 38, y + h - 16, 3, (170, 80, 30))
    cv.ellipse(x + 30, y + 12, 46, 14, (120, 120, 130))
    cv.rect(x + 60, y + 22, 26, 8, (200, 200, 210))
    cv.poly([(x + 86, y + 22), (x + 104, y + 26), (x + 86, y + 30)], GOLD)
    cv.rect(x + 30, y + 20, 10, 12, (160, 160, 170))


def scene_van(cv, x, y, w, h):
    cv.rect(x, y, w, h, (150, 148, 142))
    cv.rect(x, y + h - 14, w, 14, (90, 88, 84))
    cv.rect(x + 34, y + 22, 100, 26, (240, 240, 240))
    cv.rect(x + 134, y + 26, 26, 22, (200, 210, 220))
    cv.circle(x + 56, y + h - 12, 9, (30, 30, 34))
    cv.circle(x + 140, y + h - 12, 9, (30, 30, 34))
    cv.rect(x + 44, y + 28, 22, 14, (90, 140, 90))
    cv.ellipse(x + 150, y + 6, 12, 7, (180, 180, 180))


def scene_desert(cv, x, y, w, h):
    cv.rect(x, y, w, 30, (250, 220, 150))
    cv.circle(x + w - 26, y + 16, 10, GOLD)
    cv.poly([(x, y + 34), (x + 60, y + 14), (x + 120, y + 34)], (190, 150, 100))
    cv.rect(x, y + 34, w, h - 34, (220, 180, 110))
    cv.rect(x + 96, y + 40, 64, 12, (180, 40, 36))
    cv.circle(x + 112, y + h - 10, 7, (30, 30, 34))
    cv.circle(x + 144, y + h - 10, 7, (30, 30, 34))


def scene_power(cv, x, y, w, h):
    cv.rect(x, y, w, h, (16, 22, 48))
    for i in range(6):
        cv.set(x + 8 + (i * 41) % (w - 16), y + 6 + (i * 17) % 20, WHITE)
    cv.rect(x + 20, y + 34, 44, h - 34, (30, 36, 66))
    cv.rect(x + 96, y + 26, 44, h - 26, (30, 36, 66))
    for r in range(3):
        cv.rect(x + 26, y + 40 + r * 10, 8, 6, GOLD if r % 2 else (50, 56, 90))
        cv.rect(x + 102, y + 34 + r * 10, 8, 6, (50, 56, 90))
    cv.line(x + 42, y + 8, x + 88, y + 34, (140, 140, 150))
    cv.line(x + 118, y + 8, x + 88, y + 34, (140, 140, 150))
    cv.line(x + 88, y + 34, x + 88, y + 8, (140, 140, 150))
    cv.circle(x + 88, y + 8, 3, GOLD)


def scene_chart(cv, x, y, w, h):
    cv.rect(x, y, w, h, (12, 16, 34))
    for i in range(4):
        cv.hline(x + 8, y + 12 + i * 13, w - 16, (40, 46, 70))
    pts = [(x + 12, y + 46), (x + 50, y + 34), (x + 88, y + 40),
           (x + 126, y + 20), (x + 164, y + 28)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], (80, 200, 120))
    cv.circle(x + 126, y + 20, 4, (80, 200, 120))
    cv.ring(x + 140, y + 44, 12, (220, 220, 220), 2)
    cv.line(x + 140, y + 44, x + 150, y + 54, (220, 220, 220))


def scene_hospital(cv, x, y, w, h):
    cv.rect(x, y, w, h, (235, 240, 235))
    cv.rect(x, y + 30, w, h - 30, (210, 225, 215))
    cv.rect(x + 60, y + 8, 60, 60, WHITE)
    cv.rect(x + 82, y + 18, 16, 40, (40, 140, 80))
    cv.rect(x + 70, y + 30, 40, 16, (40, 140, 80))
    cv.rect(x + 20, y + h - 18, 60, 10, (90, 120, 140))
    cv.rect(x + 120, y + h - 18, 44, 10, (90, 120, 140))


def scene_sub(cv, x, y, w, h):
    cv.rect(x, y, w, h, (16, 40, 66))
    cv.ellipse(x + 30, y + 26, 62, 12, (24, 28, 40))
    cv.rect(x + 84, y + 16, 22, 12, (24, 28, 40))
    cv.rect(x + 30, y + 30, 8, 14, (24, 28, 40))
    cv.circle(x + w - 30, y + 14, 8, GOLD)
    for i in range(3):
        cv.ellipse(x + 12 + i * 56, y + h - 10, 16, 3, (120, 160, 180))


# ---------------------------------------------------------------- Content

HEROES = [
    dict(flag="COP31: NO DEAL", flag2="~200 nations", chip="Summit president",
         scene=scene_cop31, kicker="1  ANTALYA, TURKEY \u2014 CLIMATE",
         headline="COP31 climate talks collapse",
         deck="194 nations reject the Antalya Pact; the longest COP ever fails. (CNN, Reuters)"),
    dict(flag="DYMER: 14 MISSING", flag2="14 missing", chip="Zelenskyy",
         scene=scene_dymer, kicker="2  KYIV REGION, UKRAINE \u2014 WAR",
         headline="Drone hits flats in Dymer, 14 missing",
         deck="Five-storey block collapses, 186 drones fired, 161 shot down. (Reuters)"),
    dict(flag="GULF: 25 HIT", flag2="25 tankers", chip="Bahrain govt",
         scene=scene_gulf, kicker="3  MANAMA, BAHRAIN \u2014 IRAN WAR",
         headline="Iran strikes US bases in Bahrain",
         deck="Radars hit at al-Riffa and Awali; 25 tankers struck in a week. (Al Jazeera)"),
]

MIDS = [
    dict(flag="SHIP ABLAZE", scene=scene_ship, kicker="GULF OF FINLAND",
         headline="Russian cargo ship burns",
         deck="Drone strike, 16 crew escape. (BBC)"),
    dict(flag="2 DEAD, 60 HURT", scene=scene_strike, kicker="KRYVYI RIH, UKRAINE",
         headline="Strike hits Zelenskyy's city",
         deck="Two killed, 60 hurt in Russian strike. (Al Jazeera)"),
    dict(flag="24 DEAD", scene=scene_boat, kicker="BAYELSA, NIGERIA",
         headline="Mourners' boat capsizes",
         deck="Niger boat sinks, 24 dead. (AP)"),
    dict(flag="8 YEARS ON", scene=scene_space, kicker="SPACE",
         headline="BepiColombo reaches Mercury",
         deck="BepiColombo arrives after eight years. (ESA)"),
    dict(flag="3 KILLED", scene=scene_van, kicker="GAZA",
         headline="Strike hits food aid vehicle",
         deck="Three Palestinians die in an air attack. (Al Jazeera)"),
    dict(flag="11 DEAD", scene=scene_desert, kicker="SINALOA, MEXICO",
         headline="El Chapo Isidro caught, 11 killed",
         deck="Cartel leader held in bloody raid in Guasave. (AP)"),
    dict(flag="POWER CUTS", scene=scene_power, kicker="TEHRAN, IRAN",
         headline="Iran to ration electricity",
         deck="War damaged the energy grid. (Straits Times)"),
    dict(flag="SEC PROBE", scene=scene_chart, kicker="WASHINGTON",
         headline="Nvidia faces US probe",
         deck="SEC inquiry at an early stage. (Straits Times)"),
    dict(flag="BOLSONARO: ICU", scene=scene_hospital, kicker="BRASILIA, BRAZIL",
         headline="Bolsonaro in intensive care",
         deck="Ex-president stable in hospital. (Reuters)"),
    dict(flag="AUKUS ROW", scene=scene_sub, kicker="CANBERRA",
         headline="Marles rejects US AUKUS report",
         deck="He says the budget number is wrong. (Reuters)"),
]

BRIEFS = [
    "US: FBI crime database hacked (AP)",
    "US: Stocks slide on AI fears (Reuters)",
    "PERU: 6.7 quake hits Sacred Valley (AP)",
    "SOUTH SUDAN: 45 killed in attacks (AP)",
    "UKRAINE: 2,700 drones this week (Kyiv Ind.)",
    "POLAND: NATO talks on incursions (Reuters)",
    "CLIMATE: 90 nations sign power pledge (Reuters)",
    "NETANYAHU: Unity talks (Israel)",
    "CRIMEA BRIDGE: Blast footage (Reuters)",
    "ITALY: Ex-police chief dead (ANSA)",
    "ZANZIBAR: Fire hits six hotels (BBC)",
    "WEST BANK: 12 vehicles burned (AP)",
    "TRUMP: India needs US OK (Reuters)",
    "BALTIC: Blasts near base (Reuters)",
    "KUTCHER: AI bet pays 7B (Bloomberg)",
    "JERUSALEM: Likud invited to talks (ST)",
    "ETHIOPIA: Strikes hit Tigray (Reuters)",
    "S. KOREA: Minister quits (Yonhap)",
    "INDONESIA: 37 missing in fire (AP)",
    "LIVERPOOL: Liverpool win 4-0 (BBC)",
    "LAS VEGAS: Verstappen wins (F1)",
    "CULTURE: Van Gogh record 173.6M (AP)",
]

STATS = [
    ("~200", "NATIONS AT THE COP31 TALKS"),
    ("2 DAYS", "OVERTIME AT COP31"),
    ("25", "TANKERS HIT IN 7 DAYS"),
    ("186", "DRONES FIRED OVERNIGHT"),
    ("14", "MISSING IN DYMER"),
    ("4", "US BASES TARGETED"),
]

REGIONS = [
    ("EUROPE 11", NAVY2, 295),
    ("MIDDLE EAST 6", RED, 166),
    ("AMERICAS 8", GREEN, 220),
    ("ASIA-PACIFIC 4", (168, 130, 50), 116),
    ("AFRICA 4", DUSK, 111),
    ("WORLD 2", (70, 70, 78), 60),
]

# Dotted world map: '#' = land dot. Grid 76 cols x 12 rows over the map box.
MAP_ROWS = [
    "............................................................................",
    "..######......####......................######..##########..................",
    "..##########..####......................########..############..............",
    "...#########...##.........................#######...##########...............",
    "....#######...............................######....########................",
    ".....#####...###............................####......######.................",
    "......###....#####...........................###.......####...##.............",
    ".......##.....####............................##........##....###............",
    "..............###.............................................##............",
    "...............##............................................................",
    "............................................................................",
    "............................................................................",
]

# Pin positions (col, row) on the map grid for the 13 pictured stories.
PINS = [(8, 2), (39, 2), (46, 3), (38, 1), (41, 3), (40, 5), (52, 3),
        (38, 4), (13, 6), (48, 4), (20, 4), (44, 2), (66, 5)]


# ---------------------------------------------------------------- Layout

def draw_banner(cv, y, h, left, right):
    cv.rect(0, y, W, h, NAVY)
    draw_text(cv, 28, y + h // 2 + 5, left, "sans_b13", WHITE)
    draw_text(cv, W - 28, y + h // 2 + 5, right, "sans_b13", WHITE, "right")


def draw_chip(cv, x, y, text, bg, fg, atlas="sans_b13", pad=6, h=18):
    w = int(text_width(text, atlas)) + 2 * pad
    cv.rect(x, y, w, h, bg)
    draw_text(cv, x + pad, y + h // 2 + 5, text, atlas, fg)
    return w


def draw_hero(cv, x, y, w, hero):
    scene_h = 150
    hero["scene"](cv, x, y, w, scene_h)
    draw_chip(cv, x, y, hero["flag"], RED, WHITE)
    f2w = int(text_width(hero["flag2"], "sans_b13")) + 12
    cv.rect(x + w - f2w, y, f2w, 18, WHITE)
    draw_text(cv, x + w - f2w + 6, y + 13, hero["flag2"], "sans_b13", NAVY)
    cw = draw_chip(cv, x, y + scene_h - 18, hero["chip"], (20, 20, 26), WHITE,
                   atlas="sans_r11", pad=5)
    ky = y + scene_h + 18
    draw_text(cv, x, ky, hero["kicker"], "sans_b13", RED)
    draw_wrapped(cv, x, ky + 6, hero["headline"], "serif_b30", NAVY,
                 w, 2, 33)
    draw_wrapped(cv, x, ky + 6 + 2 * 33 + 4, hero["deck"], "sans_r12", INK,
                 w, 2, 15)


def draw_mid(cv, x, y, w, mid, num):
    scene_h = 64
    mid["scene"](cv, x, y, w, scene_h)
    draw_chip(cv, x, y, mid["flag"], RED, WHITE, h=16)
    n = str(num)
    nw = int(text_width(n, "sans_b13")) + 10
    cv.circle(x + w - 10, y + 10, 10, WHITE)
    draw_text(cv, x + w - 10, y + 14, n, "sans_b13", RED, "center")
    ky = y + scene_h + 15
    draw_text(cv, x, ky, mid["kicker"], "sans_b13", RED)
    draw_wrapped(cv, x, ky + 4, mid["headline"], "serif_b19", NAVY,
                 w, 2, 21)
    draw_wrapped(cv, x, ky + 4 + 2 * 21 + 2, mid["deck"], "sans_r11", INK,
                 w, 2, 13)


def draw_map(cv, x, y, w, h):
    cell = 6
    for r, row in enumerate(MAP_ROWS):
        for c, ch in enumerate(row):
            if ch == "#":
                cx = x + c * cell + 3
                cy = y + r * cell + 3
                cv.circle(cx, cy, 2, (120, 130, 150))
    for i, (c, r) in enumerate(PINS, 1):
        cx = x + c * cell + 3
        cy = y + r * cell + 3
        cv.circle(cx, cy, 4, RED)


def build():
    cv = Canvas(W, H, CREAM)
    draw_banner(cv, 0, 24, "THE WORLD IN ONE DAY",
                "35 STORIES \u00b7 6 REGIONS \u00b7 EVERY ONE DATED MONDAY 23 NOVEMBER 2026")

    # Masthead
    draw_text(cv, 28, 94, "Monday 23 November 2026", "serif_b72", NAVY)
    draw_text(cv, 28, 122,
              "COP31 collapses with no deal \u00b7 Iran hits US bases in Bahrain "
              "\u00b7 Drone kills one in Dymer", "serif_bi20", RED)
    cv.hline(28, 130, 968, NAVY)
    cv.hline(28, 133, 968, NAVY)

    # Stat strip
    col_w = 968 // 6
    for i, (num, cap) in enumerate(STATS):
        cx = 28 + i * col_w
        if i:
            cv.vline(cx - 8, 142, 52, LGREY)
        draw_text(cv, cx + col_w // 2, 172, num, "serif_b40", RED, "center")
        draw_text(cv, cx + col_w // 2, 190, cap, "sans_r11", NAVY, "center")

    # Region bar
    rx = 28
    for label, color, rw in REGIONS:
        cv.rect(rx, 202, rw, 22, color)
        draw_text(cv, rx + rw // 2, 217, label, "sans_b13", WHITE, "center")
        rx += rw

    # Heroes
    for i, hero in enumerate(HEROES):
        draw_hero(cv, 28 + i * (312 + 16), 232, 312, hero)
    cv.hline(28, 514, 968, NAVY)

    # Mids, two rows of five
    mw = (968 - 4 * 12) // 5
    for row in range(2):
        for col in range(5):
            idx = row * 5 + col
            draw_mid(cv, 28 + col * (mw + 12), 522 + row * 160, mw,
                     MIDS[idx], idx + 4)
    cv.hline(28, 842, 968, NAVY)

    # Bottom: map + briefs
    draw_text(cv, 28, 858, "WHERE IT HAPPENED", "sans_b13", NAVY)
    draw_text(cv, 500, 858, "ALSO ON MONDAY 23 NOVEMBER \u2014 22 MORE STORIES",
              "sans_b13", NAVY)
    draw_map(cv, 28, 866, 460, 70)
    for i, brief in enumerate(BRIEFS):
        col = i // 11
        row = i % 11
        bx = 500 + col * 252
        by = 872 + row * 11
        draw_text(cv, bx, by, "%d  %s" % (14 + i, brief), "serif_r11", INK)

    # DATE CHECK box
    cv.rect(28, 940, 460, 62, PAPER)
    cv.rect(28, 940, 460, 2, RED)
    cv.rect(28, 1000, 460, 2, RED)
    cv.rect(28, 940, 2, 62, RED)
    cv.rect(486, 940, 2, 62, RED)
    draw_text(cv, 38, 956, "DATE CHECK", "sans_b13", RED)
    draw_wrapped(cv, 38, 960,
                 "Wires read up to 06:00 UTC, Monday 23 November 2026. Every story "
                 "was reported or developing on 22\u201323 November.",
                 "sans_r11", INK, 440, 2, 13)
    draw_wrapped(cv, 38, 986,
                 "Left out: the Shenzhen summit (19 Nov); the Kerch Bridge strikes.",
                 "sans_r11", INK, 440, 1, 13)

    draw_text(cv, 500, 999,
              "Sources: CNN \u00b7 Reuters \u00b7 AP \u00b7 Al Jazeera \u00b7 BBC \u00b7 "
              "The Times \u00b7 AFP \u00b7 Straits Times \u00b7 Kyiv Independent",
              "sans_r11", GREY)
    draw_banner(cv, 1004, 20, "THE WORLD IN ONE DAY",
                "MONDAY 23 NOVEMBER 2026 \u00b7 ONE PAGE")
    return cv


def main():
    cv = build()
    data = png_encode_rgb(W, H, cv.px)
    outdir = "/output" if os.path.isdir("/output") else "."
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    import hashlib
    print("wrote %s %d bytes sha256 %s"
          % (path, len(data), hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
