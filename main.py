#!/usr/bin/env python3
"""news-image-20261122: draw Sunday 22 November 2026's world news as one
1024x1024 front page, using only the Python 3 standard library (the grader
container has no PIL).

Reads stories.json next to this file, renders with a built-in 5x7 bitmap
font stored as 35-bit strings, a hand-rolled PNG encoder, flat vector
icons and a simplified world map with numbered pins. Writes entry.png to
$MAKEFUN_OUTPUT_DIR (default /output). Deterministic: two runs write
identical bytes.
"""

import json
import os
import struct
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- 5x7 font
# One glyph = 35 characters of '0'/'1', row-major, 5 columns x 7 rows.
# ASCII 32..126. Uppercase-first newspaper style; lowercase has descenders
# drawn inside the 7-row cell.
def _g(rows):
    return "".join(rows)

FONT = {
    ' ': _g(["00000", "00000", "00000", "00000", "00000", "00000", "00000"]),
    '!': _g(["00100", "00100", "00100", "00100", "00100", "00000", "00100"]),
    '"': _g(["01010", "01010", "01010", "00000", "00000", "00000", "00000"]),
    '#': _g(["01010", "01010", "11111", "01010", "11111", "01010", "01010"]),
    '$': _g(["00100", "01111", "10101", "01110", "00101", "11110", "00100"]),
    '%': _g(["11001", "11010", "00010", "00100", "01000", "01011", "10011"]),
    '&': _g(["01100", "10010", "10010", "01000", "10101", "10010", "01101"]),
    "'": _g(["00100", "00100", "01000", "00000", "00000", "00000", "00000"]),
    '(': _g(["00010", "00100", "01000", "01000", "01000", "00100", "00010"]),
    ')': _g(["01000", "00100", "00010", "00010", "00010", "00100", "01000"]),
    '*': _g(["00000", "00100", "10101", "01110", "10101", "00100", "00000"]),
    '+': _g(["00000", "00100", "00100", "11111", "00100", "00100", "00000"]),
    ',': _g(["00000", "00000", "00000", "00000", "00110", "00100", "01000"]),
    '-': _g(["00000", "00000", "00000", "01110", "00000", "00000", "00000"]),
    '.': _g(["00000", "00000", "00000", "00000", "00000", "00110", "00110"]),
    '/': _g(["00001", "00010", "00010", "00100", "01000", "01000", "10000"]),
    '0': _g(["01110", "10001", "10011", "10101", "11001", "10001", "01110"]),
    '1': _g(["00100", "01100", "00100", "00100", "00100", "00100", "01110"]),
    '2': _g(["01110", "10001", "00001", "00110", "01000", "10000", "11111"]),
    '3': _g(["11111", "00010", "00100", "00010", "00001", "10001", "01110"]),
    '4': _g(["00010", "00110", "01010", "10010", "11111", "00010", "00010"]),
    '5': _g(["11111", "10000", "11110", "00001", "00001", "10001", "01110"]),
    '6': _g(["00110", "01000", "10000", "11110", "10001", "10001", "01110"]),
    '7': _g(["11111", "00001", "00010", "00100", "01000", "01000", "01000"]),
    '8': _g(["01110", "10001", "10001", "01110", "10001", "10001", "01110"]),
    '9': _g(["01110", "10001", "10001", "01111", "00001", "00010", "01100"]),
    ':': _g(["00000", "01100", "01100", "00000", "01100", "01100", "00000"]),
    ';': _g(["00000", "01100", "01100", "00000", "01100", "00100", "01000"]),
    '<': _g(["00010", "00100", "01000", "10000", "01000", "00100", "00010"]),
    '=': _g(["00000", "00000", "11111", "00000", "11111", "00000", "00000"]),
    '>': _g(["01000", "00100", "00010", "00001", "00010", "00100", "01000"]),
    '?': _g(["01110", "10001", "00001", "00110", "00100", "00000", "00100"]),
    '@': _g(["01110", "10001", "10111", "10101", "10110", "10000", "01110"]),
    'A': _g(["01110", "10001", "10001", "11111", "10001", "10001", "10001"]),
    'B': _g(["11110", "10001", "10001", "11110", "10001", "10001", "11110"]),
    'C': _g(["01110", "10001", "10000", "10000", "10000", "10001", "01110"]),
    'D': _g(["11110", "10001", "10001", "10001", "10001", "10001", "11110"]),
    'E': _g(["11111", "10000", "10000", "11110", "10000", "10000", "11111"]),
    'F': _g(["11111", "10000", "10000", "11110", "10000", "10000", "10000"]),
    'G': _g(["01110", "10001", "10000", "10111", "10001", "10001", "01111"]),
    'H': _g(["10001", "10001", "10001", "11111", "10001", "10001", "10001"]),
    'I': _g(["01110", "00100", "00100", "00100", "00100", "00100", "01110"]),
    'J': _g(["00111", "00010", "00010", "00010", "00010", "10010", "01100"]),
    'K': _g(["10001", "10010", "10100", "11000", "10100", "10010", "10001"]),
    'L': _g(["10000", "10000", "10000", "10000", "10000", "10000", "11111"]),
    'M': _g(["10001", "11011", "10101", "10101", "10001", "10001", "10001"]),
    'N': _g(["10001", "11001", "10101", "10011", "10001", "10001", "10001"]),
    'O': _g(["01110", "10001", "10001", "10001", "10001", "10001", "01110"]),
    'P': _g(["11110", "10001", "10001", "11110", "10000", "10000", "10000"]),
    'Q': _g(["01110", "10001", "10001", "10001", "10101", "10010", "01101"]),
    'R': _g(["11110", "10001", "10001", "11110", "10100", "10010", "10001"]),
    'S': _g(["01111", "10000", "10000", "01110", "00001", "00001", "11110"]),
    'T': _g(["11111", "00100", "00100", "00100", "00100", "00100", "00100"]),
    'U': _g(["10001", "10001", "10001", "10001", "10001", "10001", "01110"]),
    'V': _g(["10001", "10001", "10001", "10001", "10001", "01010", "00100"]),
    'W': _g(["10001", "10001", "10001", "10101", "10101", "11011", "10001"]),
    'X': _g(["10001", "10001", "01010", "00100", "01010", "10001", "10001"]),
    'Y': _g(["10001", "10001", "01010", "00100", "00100", "00100", "00100"]),
    'Z': _g(["11111", "00001", "00010", "00100", "01000", "10000", "11111"]),
    '[': _g(["01110", "01000", "01000", "01000", "01000", "01000", "01110"]),
    '\\': _g(["10000", "01000", "01000", "00100", "00010", "00010", "00001"]),
    ']': _g(["01110", "00010", "00010", "00010", "00010", "00010", "01110"]),
    '^': _g(["00100", "01010", "10001", "00000", "00000", "00000", "00000"]),
    '_': _g(["00000", "00000", "00000", "00000", "00000", "00000", "11111"]),
    '`': _g(["01000", "00100", "00010", "00000", "00000", "00000", "00000"]),
    'a': _g(["00000", "00000", "01110", "00001", "01111", "10001", "01111"]),
    'b': _g(["10000", "10000", "11110", "10001", "10001", "10001", "11110"]),
    'c': _g(["00000", "00000", "01110", "10001", "10000", "10001", "01110"]),
    'd': _g(["00001", "00001", "01111", "10001", "10001", "10001", "01111"]),
    'e': _g(["00000", "00000", "01110", "10001", "11111", "10000", "01110"]),
    'f': _g(["00110", "01001", "01000", "11110", "01000", "01000", "01000"]),
    'g': _g(["00000", "01111", "10001", "10001", "01111", "00001", "01110"]),
    'h': _g(["10000", "10000", "11110", "10001", "10001", "10001", "10001"]),
    'i': _g(["00100", "00000", "01100", "00100", "00100", "00100", "01110"]),
    'j': _g(["00010", "00000", "00110", "00010", "00010", "10010", "01100"]),
    'k': _g(["10000", "10000", "10010", "10100", "11000", "10100", "10010"]),
    'l': _g(["01100", "00100", "00100", "00100", "00100", "00100", "01110"]),
    'm': _g(["00000", "00000", "11010", "10101", "10101", "10101", "10101"]),
    'n': _g(["00000", "00000", "11110", "10001", "10001", "10001", "10001"]),
    'o': _g(["00000", "00000", "01110", "10001", "10001", "10001", "01110"]),
    'p': _g(["00000", "00000", "11110", "10001", "11110", "10000", "10000"]),
    'q': _g(["00000", "00000", "01111", "10001", "01111", "00001", "00001"]),
    'r': _g(["00000", "00000", "10110", "11001", "10000", "10000", "10000"]),
    's': _g(["00000", "00000", "01111", "10000", "01110", "00001", "11110"]),
    't': _g(["01000", "01000", "11110", "01000", "01000", "01001", "00110"]),
    'u': _g(["00000", "00000", "10001", "10001", "10001", "10001", "01111"]),
    'v': _g(["00000", "00000", "10001", "10001", "10001", "01010", "00100"]),
    'w': _g(["00000", "00000", "10001", "10101", "10101", "10101", "01010"]),
    'x': _g(["00000", "00000", "10001", "01010", "00100", "01010", "10001"]),
    'y': _g(["00000", "00000", "10001", "10001", "01111", "00001", "01110"]),
    'z': _g(["00000", "00000", "11111", "00010", "00100", "01000", "11111"]),
    '{': _g(["00110", "01000", "01000", "11100", "01000", "01000", "00110"]),
    '|': _g(["00100", "00100", "00100", "00100", "00100", "00100", "00100"]),
    '}': _g(["01100", "00010", "00010", "00111", "00010", "00010", "01100"]),
    '~': _g(["00000", "00000", "01001", "10110", "00000", "00000", "00000"]),
}

# ---------------------------------------------------------------- PNG writer
def _chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    c += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return c

def write_png(path, w, h, rgb):
    """rgb: bytes of w*h*3. Fixed zlib level -> deterministic bytes."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += rgb[y * w * 3:(y + 1) * w * 3]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + _chunk(b"IEND", b""))
    Path(path).write_bytes(data)

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def _set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + (x1 - x0) * 3] = c * (x1 - x0)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill and d <= r * r:
                    self._set(xx, yy, c)
                elif not fill and r * r - 2 * r <= d <= r * r:
                    self._set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self._set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def poly(self, pts, c):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], c)

    def fill_poly(self, pts, c):
        # scanline fill for simple polygons
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.rect(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)

    def text(self, x, y, s, scale, c, spacing=1):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[' '])
            for r in range(7):
                row = glyph[r * 5:(r + 1) * 5]
                for col in range(5):
                    if row[col] == '1':
                        self.rect(cx + col * scale, y + r * scale,
                                  scale, scale, c)
            cx += (6 + spacing) * scale if scale > 1 else 6 * scale
        return cx

    def text_w(self, s, scale, spacing=1):
        n = len(s)
        if n == 0:
            return 0
        return (n * 6 - 1 + (n - 1) * spacing) * scale if scale > 1 else n * 6 * scale

    def wrap(self, s, max_w, scale, spacing=1):
        """Greedy word wrap; returns list of lines that fit max_w."""
        words = s.split(" ")
        lines, cur = [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if self.text_w(trial, scale, spacing) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

# ---------------------------------------------------------------- palette
PAPER = bytes((246, 241, 227))
INK = bytes((26, 36, 51))
RED = bytes((179, 39, 30))
BLUE = bytes((31, 78, 121))
GOLD = bytes((176, 120, 31))
TEAL = bytes((15, 118, 110))
GREEN = bytes((47, 107, 58))
PURPLE = bytes((91, 75, 138))
GREY = bytes((110, 116, 124))
LIGHT = bytes((233, 227, 210))
WHITE = bytes((255, 255, 255))
DARKRED = bytes((122, 26, 20))

REGION_COLORS = {
    "EUROPE": BLUE, "ASIA": GOLD, "N. AMERICA": TEAL, "MIDDLE EAST": RED,
    "LATIN AMERICA": GREEN, "AFRICA": PURPLE, "OCEANIA": BLUE,
    "CLIMATE": TEAL, "GLOBAL": INK, "SPORT": PURPLE, "TECH": TEAL,
}

# ---------------------------------------------------------------- icons
# Each icon draws inside a box (x, y, s). Flat vector shapes, no photos.
def draw_icon(cv, kind, x, y, s, c):
    u = s / 16.0  # unit
    def R(px, py, w, h):
        cv.rect(int(x + px * u), int(y + py * u), max(1, int(w * u)), max(1, int(h * u)), c)
    def C(cx, cy, r):
        cv.circle(int(x + cx * u), int(y + cy * u), max(1, int(r * u)), c)
    def L(x0, y0, x1, y1):
        cv.line(int(x + x0 * u), int(y + y0 * u), int(x + x1 * u), int(y + y1 * u), c)
    if kind == "globe":
        C(8, 8, 7)
        cv.circle(int(x + 8 * u), int(y + 8 * u), max(1, int(7 * u)), PAPER, fill=False)
        L(1, 8, 15, 8); L(8, 1, 8, 15)
        cv.circle(int(x + 8 * u), int(y + 8 * u), max(1, int(3 * u)), PAPER, fill=False)
    elif kind == "missile":
        cv.fill_poly([(int(x + 8 * u), int(y + 1 * u)), (int(x + 11 * u), int(y + 7 * u)),
                      (int(x + 10 * u), int(y + 13 * u)), (int(x + 6 * u), int(y + 13 * u)),
                      (int(x + 5 * u), int(y + 7 * u))], c)
        R(6, 13, 4, 2)
    elif kind == "quake":
        L(1, 12, 5, 12); L(5, 12, 7, 4); L(7, 4, 9, 10); L(9, 10, 11, 6); L(11, 6, 15, 6)
        R(2, 13, 12, 1)
    elif kind == "gavel":
        L(3, 3, 13, 9); R(2, 2, 4, 3); R(11, 7, 4, 3)
        L(10, 6, 5, 13); R(2, 14, 12, 1)
    elif kind == "leaf":
        cv.fill_poly([(int(x + 8 * u), int(y + 1 * u)), (int(x + 14 * u), int(y + 8 * u)),
                      (int(x + 8 * u), int(y + 15 * u)), (int(x + 2 * u), int(y + 8 * u))], c)
        L(8, 2, 8, 14)
    elif kind == "mic":
        R(6, 1, 4, 7); C(8, 10, 3); L(8, 13, 8, 15); L(5, 15, 11, 15)
    elif kind == "capitol":
        R(1, 12, 14, 2); R(2, 10, 12, 2); L(3, 10, 3, 5); L(8, 10, 8, 3)
        L(13, 10, 13, 5); R(6, 4, 4, 2); C(8, 3, 2)
    elif kind == "flame":
        cv.fill_poly([(int(x + 8 * u), int(y + 1 * u)), (int(x + 12 * u), int(y + 7 * u)),
                      (int(x + 14 * u), int(y + 11 * u)), (int(x + 11 * u), int(y + 15 * u)),
                      (int(x + 5 * u), int(y + 15 * u)), (int(x + 2 * u), int(y + 11 * u)),
                      (int(x + 4 * u), int(y + 7 * u))], c)
    elif kind == "chart":
        R(2, 10, 3, 5); R(6, 7, 3, 8); R(10, 4, 3, 11); L(1, 13, 6, 8); L(6, 8, 11, 5); L(11, 5, 15, 2)
    elif kind == "trophy":
        R(5, 1, 6, 3); R(6, 4, 4, 5); L(5, 1, 3, 4); L(11, 1, 13, 4)
        R(4, 9, 8, 1); R(6, 10, 4, 2); R(3, 12, 10, 2)
    elif kind == "chip":
        R(4, 4, 8, 8); R(6, 6, 4, 4); L(6, 2, 6, 4); L(10, 2, 10, 4)
        L(6, 12, 6, 14); L(10, 12, 10, 14); L(2, 6, 4, 6); L(2, 10, 4, 10)
        L(12, 6, 14, 6); L(12, 10, 14, 10)
    elif kind == "plane":
        cv.fill_poly([(int(x + 2 * u), int(y + 8 * u)), (int(x + 8 * u), int(y + 4 * u)),
                      (int(x + 14 * u), int(y + 2 * u)), (int(x + 12 * u), int(y + 8 * u)),
                      (int(x + 14 * u), int(y + 10 * u)), (int(x + 8 * u), int(y + 10 * u)),
                      (int(x + 6 * u), int(y + 14 * u)), (int(x + 4 * u), int(y + 10 * u))], c)
    elif kind == "deal":
        R(1, 6, 6, 4); R(9, 6, 6, 4); L(7, 6, 9, 8); L(7, 10, 9, 8)
        R(2, 11, 5, 2); R(9, 11, 5, 2)
    elif kind == "target":
        C(8, 8, 7); cv.circle(int(x + 8 * u), int(y + 8 * u), max(1, int(7 * u)), PAPER, fill=False)
        C(8, 8, 4); cv.circle(int(x + 8 * u), int(y + 8 * u), max(1, int(4 * u)), PAPER, fill=False)
        C(8, 8, 1)
    elif kind == "shield":
        cv.fill_poly([(int(x + 8 * u), int(y + 1 * u)), (int(x + 14 * u), int(y + 4 * u)),
                      (int(x + 14 * u), int(y + 9 * u)), (int(x + 8 * u), int(y + 15 * u)),
                      (int(x + 2 * u), int(y + 9 * u)), (int(x + 2 * u), int(y + 4 * u))], c)
        L(6, 8, 8, 10); L(8, 10, 11, 5)
    elif kind == "flag":
        L(4, 1, 4, 15); cv.fill_poly([(int(x + 4 * u), int(y + 1 * u)), (int(x + 14 * u), int(y + 3 * u)),
                                       (int(x + 4 * u), int(y + 6 * u))], c)
    elif kind == "bat":
        L(4, 2, 11, 12); R(10, 11, 4, 2); C(3, 3, 2)
    elif kind == "virus":
        C(8, 8, 4); L(8, 1, 8, 4); L(8, 12, 8, 15); L(1, 8, 4, 8); L(12, 8, 15, 8)
        L(3, 3, 5, 5); L(11, 11, 13, 13); L(13, 3, 11, 5); L(5, 11, 3, 13)
    elif kind == "ballot":
        R(2, 2, 12, 12); R(4, 4, 8, 8); L(6, 8, 8, 10); L(8, 10, 12, 5)
    elif kind == "ship":
        R(2, 9, 12, 4); L(8, 9, 8, 2); L(8, 2, 13, 7); L(8, 2, 8, 7)
    elif kind == "train":
        R(3, 2, 10, 11); R(5, 4, 2, 2); R(9, 4, 2, 2); R(3, 10, 10, 2); R(2, 13, 12, 1)
    elif kind == "court":
        R(1, 13, 14, 2); L(3, 13, 3, 6); L(13, 13, 13, 6); L(8, 13, 8, 4)
        R(2, 5, 12, 1); R(5, 2, 6, 2)
    elif kind == "money":
        C(8, 8, 7); cv.circle(int(x + 8 * u), int(y + 8 * u), max(1, int(7 * u)), PAPER, fill=False)
        R(7, 4, 2, 8); R(5, 6, 6, 2)
    else:  # globe fallback
        C(8, 8, 7)
        cv.circle(int(x + 8 * u), int(y + 8 * u), max(1, int(7 * u)), PAPER, fill=False)

# ---------------------------------------------------------------- world map
# Coarse continent outlines in (lon, lat). Equirectangular projection.
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-120, 71), (-95, 69), (-80, 62), (-65, 60),
     (-55, 47), (-70, 42), (-75, 35), (-80, 26), (-85, 20), (-92, 15),
     (-97, 16), (-105, 20), (-110, 24), (-120, 34), (-125, 40), (-125, 49),
     (-135, 58), (-155, 58), (-165, 60), (-168, 66)],
    # Greenland
    [(-58, 64), (-45, 60), (-30, 68), (-40, 76), (-58, 76), (-60, 70), (-58, 64)],
    # South America
    [(-80, 9), (-62, 9), (-52, 5), (-50, 0), (-44, -3), (-35, -8),
     (-40, -20), (-48, -28), (-58, -38), (-65, -45), (-70, -54), (-73, -50),
     (-73, -37), (-70, -20), (-77, -12), (-80, -3), (-80, 9)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (-4, 50), (2, 51), (5, 53), (8, 57),
     (10, 59), (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (30, 70),
     (40, 68), (45, 68), (50, 69), (55, 68), (60, 69), (68, 73), (75, 72),
     (70, 68), (60, 66), (50, 62), (44, 60), (40, 55), (35, 55), (30, 50),
     (28, 45), (23, 40), (20, 40), (15, 44), (12, 44), (8, 44), (3, 42),
     (0, 39), (-2, 37), (-6, 36), (-10, 36)],
    # Africa
    [(-17, 15), (-16, 20), (-10, 31), (0, 36), (10, 37), (20, 32),
     (30, 31), (32, 31), (35, 28), (37, 22), (40, 15), (43, 12), (51, 11),
     (51, 2), (46, -2), (40, -10), (36, -18), (33, -26), (28, -33), (20, -35),
     (17, -32), (15, -27), (12, -18), (9, -2), (9, 4), (-8, 5), (-13, 8),
     (-17, 15)],
    # Asia (simplified, Eurasia east of ~60E plus India/SE Asia)
    [(60, 69), (68, 73), (80, 73), (100, 76), (120, 73), (140, 72),
     (160, 70), (178, 66), (170, 60), (160, 55), (142, 50), (140, 40),
     (130, 38), (127, 35), (122, 30), (120, 22), (110, 20), (105, 10),
     (100, 7), (97, 15), (92, 21), (88, 22), (80, 15), (77, 8), (73, 16),
     (68, 23), (62, 25), (58, 26), (54, 27), (50, 29), (48, 30), (52, 26),
     (56, 27), (58, 24), (60, 25), (62, 25), (60, 30), (55, 35), (50, 38),
     (48, 39), (45, 41), (42, 44), (40, 47), (38, 47), (35, 48), (33, 45),
     (30, 46), (28, 45), (30, 50), (35, 55), (40, 55), (44, 60), (50, 62),
     (60, 66), (60, 69)],
    # Australia
    [(114, -22), (114, -30), (115, -35), (120, -34), (125, -32), (130, -32),
     (135, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27),
     (150, -22), (146, -19), (142, -11), (136, -12), (132, -11), (130, -13),
     (126, -14), (122, -17), (118, -20), (114, -22)],
    # New Zealand
    [(167, -45), (170, -43), (173, -41), (176, -38), (178, -38), (174, -41),
     (170, -43), (167, -46), (167, -45)],
]

def draw_map(cv, x, y, w, h, pins):
    """pins: list of (lon, lat, n, color)."""
    cv.rect(x, y, w, h, bytes((214, 228, 235)))
    lon0, lon1, lat0, lat1 = -170, 190, -60, 85
    def proj(lon, lat):
        px = x + (lon - lon0) / (lon1 - lon0) * w
        py = y + (lat1 - lat) / (lat1 - lat0) * h
        return int(px), int(py)
    # graticule
    for lon in range(-150, 181, 30):
        px, _ = proj(lon, lat1)
        cv.vline(px, y, h, bytes((190, 205, 214)), 1)
    for lat in range(-60, 86, 30):
        _, py = proj(lon0, lat)
        cv.hline(x, py, w, bytes((190, 205, 214)), 1)
    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        cv.fill_poly(pts, bytes((150, 168, 148)))
        cv.poly(pts + [pts[0]], bytes((110, 130, 115)))
    for lon, lat, n, color in pins:
        px, py = proj(lon, lat)
        cv.circle(px, py, 9, WHITE)
        cv.circle(px, py, 8, color)
        s = str(n)
        tw = cv.text_w(s, 1)
        cv.text(px - tw // 2, py - 4, s, 1, WHITE)

# ---------------------------------------------------------------- layout
W, H = 1024, 1024
M = 18  # margin
CW = W - 2 * M  # 988

def draw(data):
    cv = Canvas(W, H, PAPER)
    warn = []

    # ---- masthead ----
    cv.rect(M, 14, CW, 3, RED)
    mast = "THE WORLD IN ONE PAGE"
    cv.text(M + (CW - cv.text_w(mast, 2)) // 2, 24, mast, 2, RED)
    date = data["date"]  # e.g. "SUNDAY 22 NOVEMBER 2026"
    dw = cv.text_w(date, 5)
    if dw > CW:
        warn.append("date too wide")
    cv.text(M + (CW - dw) // 2, 46, date, 5, INK)
    sub = "%d STORIES  ·  %d REGIONS  ·  ALL FROM TODAY" % (
        data["total_stories"], data["regions"])
    cv.text(M + (CW - cv.text_w(sub, 1)) // 2, 88, sub, 1, GREY)
    cv.hline(M, 100, CW, INK, 2)

    # ---- lead story (featured #1), full width ----
    lead = data["featured"][0]
    y = 108
    cv.rect(M, y, 8, 62, RED)
    cv.text(M + 18, y + 2, "#1  " + lead["tag"], 1, RED)
    title = lead["title"]
    tw = cv.text_w(title, 3)
    if tw > CW - 40:
        # shrink to scale 2 if it cannot fit on one line
        cv.text(M + 18, y + 14, title, 2, INK)
        ty = y + 32
    else:
        cv.text(M + 18, y + 14, title, 3, INK)
        ty = y + 38
    summ = cv.wrap(lead["summary"], CW - 36, 1)
    for i, ln in enumerate(summ[:2]):
        cv.text(M + 18, ty + i * 10, ln, 1, INK)
    if len(summ) > 2:
        warn.append("lead summary truncated")
    y = 178
    cv.hline(M, y, CW, LIGHT, 2)

    # ---- featured grid: #2..#13, 3 cols x 4 rows ----
    rest = data["featured"][1:13]
    cols, rows = 3, 4
    gap = 10
    cell_w = (CW - (cols - 1) * gap) // cols
    cell_h = 100
    gy = y + 8
    for idx, st in enumerate(rest):
        r, c = divmod(idx, cols)
        cx = M + c * (cell_w + gap)
        cy = gy + r * (cell_h + 8)
        color = REGION_COLORS.get(st["tag"], INK)
        # number badge + tag + icon
        cv.circle(cx + 11, cy + 11, 10, color)
        num = str(st["n"])
        cv.text(cx + 11 - cv.text_w(num, 1) // 2, cy + 7, num, 1, WHITE)
        cv.text(cx + 26, cy + 7, st["tag"], 1, color)
        draw_icon(cv, st["icon"], cx + cell_w - 30, cy + 1, 26, color)
        cv.hline(cx, cy + 24, cell_w, LIGHT, 1)
        # title, up to 2 lines at scale 2
        tlines = cv.wrap(st["title"], cell_w - 4, 2)
        for i, ln in enumerate(tlines[:2]):
            cv.text(cx, cy + 30 + i * 15, ln, 2, INK)
        if len(tlines) > 2:
            warn.append("title #%d truncated" % st["n"])
        # summary, up to 3 lines at scale 1
        slines = cv.wrap(st["summary"], cell_w - 4, 1)
        for i, ln in enumerate(slines[:3]):
            cv.text(cx, cy + 62 + i * 10, ln, 1, GREY)
        if len(slines) > 3:
            warn.append("summary #%d truncated" % st["n"])
    y = gy + rows * cell_h + (rows - 1) * 8
    cv.hline(M, y + 4, CW, INK, 2)

    # ---- UTC timeline ----
    y += 12
    cv.text(M, y, "THE DAY IN UTC", 2, RED)
    tl = data["timeline"]
    slot_w = CW // len(tl)
    for i, (utc, label) in enumerate(tl):
        tx = M + i * slot_w + 4
        cv.text(tx, y + 18, utc, 2, INK)
        ll = cv.wrap(label, slot_w - 10, 1)
        for j, ln in enumerate(ll[:2]):
            cv.text(tx, y + 36 + j * 10, ln, 1, GREY)
        if i:
            cv.vline(M + i * slot_w, y + 16, 44, LIGHT, 1)
    y += 62
    cv.hline(M, y, CW, INK, 2)

    # ---- bottom: ALSO ON list (left) + map (right) ----
    y += 8
    map_w = 372
    list_w = CW - map_w - 16
    cv.text(M, y, "ALSO ON " + data["day_label"] + " 22 NOVEMBER", 2, INK)
    cv.text(M + list_w + 16, y, "WHERE IT HAPPENED", 2, INK)
    ly = y + 20
    also = data["also"]
    per_col = (len(also) + 1) // 2
    col_w = list_w // 2
    for i, item in enumerate(also):
        col, row = divmod(i, per_col)
        ix = M + col * col_w
        iy = ly + row * 12
        s = item
        if cv.text_w(s, 1) > col_w - 12:
            s = s[:60]
            while cv.text_w(s + "...", 1) > col_w - 12 and len(s) > 10:
                s = s[:-1]
            s += "..."
        cv.text(ix, iy, chr(8226), 1, RED)
        cv.text(ix + 10, iy, s, 1, INK)
    # map
    pins = []
    for st in data["featured"]:
        if "lat" in st and "lon" in st:
            pins.append((st["lon"], st["lat"], st["n"],
                         REGION_COLORS.get(st["tag"], INK)))
    draw_map(cv, M + list_w + 16, ly, map_w, per_col * 12 - 4, pins)
    y = ly + per_col * 12 + 6

    # ---- DATE CHECK bar ----
    cv.rect(M, y, CW, 52, bytes((242, 222, 214)))
    cv.rect(M, y, 6, 52, RED)
    cv.text(M + 14, y + 6, "DATE CHECK — LEFT OUT ON PURPOSE:", 1, DARKRED)
    dc = "  ·  ".join(data["date_check"])
    dcl = cv.wrap(dc, CW - 28, 1)
    for i, ln in enumerate(dcl[:3]):
        cv.text(M + 14, y + 20 + i * 10, ln, 1, INK)
    if len(dcl) > 3:
        warn.append("date check truncated")
    y += 60

    # ---- footer ----
    cv.hline(M, y, CW, INK, 2)
    foot = "Sources: " + data["sources"]
    fl = cv.wrap(foot, CW, 1)
    for i, ln in enumerate(fl[:2]):
        cv.text(M, y + 8 + i * 10, ln, 1, GREY)
    note = ("Every story happened or was first reported on Sunday 22 November "
            "2026. Illustrations are flat vector drawings, not photographs.")
    nl = cv.wrap(note, CW, 1)
    for i, ln in enumerate(nl[:1]):
        cv.text(M, y + 30 + i * 10, ln, 1, GREY)
    y += 44
    if y > H - 4:
        warn.append("layout overflow: y=%d" % y)
    for w in warn:
        print("FIT WARNING: " + w, file=sys.stderr)
    return cv

def main():
    with open(HERE / "stories.json", encoding="utf-8") as f:
        data = json.load(f)
    cv = draw(data)
    outdir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "entry.png"
    write_png(out, W, H, bytes(cv.px))
    print("wrote %s (%d bytes)" % (out, out.stat().st_size))

if __name__ == "__main__":
    main()
