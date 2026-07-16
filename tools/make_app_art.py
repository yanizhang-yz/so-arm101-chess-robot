#!/usr/bin/env python
"""Generate Kid Chess' iOS app icon and launch splash — no network, no alpha.

App Store rule: the 1024 icon must be a flat PNG with NO alpha channel and no
pre-rounded corners (Apple masks the corners). We render everything at 4x on a
transparent layer for smooth edges, composite onto an OPAQUE candy background,
downscale with Lanczos, then save as RGB so the final PNG carries no alpha.

Run: .venv/bin/python tools/make_app_art.py   (or: npm run ios:icons)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ICONSET = ROOT / "ios/App/App/Assets.xcassets/AppIcon.appiconset"
SPLASHSET = ROOT / "ios/App/App/Assets.xcassets/Splash.imageset"
FONT = "/Library/Fonts/Arial Unicode.ttf"

PINK = (255, 93, 162)      # --accent
DEEP = (214, 51, 120)
INK = (74, 51, 85)         # --ink
KNIGHT = "♞"          # ♞ black chess knight — the game's "horsey"


def gradient(size: int, top: tuple, mid: tuple, bot: tuple) -> Image.Image:
    """A smooth vertical 3-stop candy gradient as an opaque RGB image."""
    t = np.linspace(0.0, 1.0, size)[:, None]
    top, mid, bot = (np.array(c, float) for c in (top, mid, bot))
    lo = top + (mid - top) * (t / 0.5).clip(0, 1)
    hi = mid + (bot - mid) * ((t - 0.5) / 0.5).clip(0, 1)
    col = np.where(t < 0.5, lo, hi)                      # (size,3)
    row = np.repeat(col[:, None, :], size, axis=1)       # (size,size,3)
    return Image.fromarray(row.round().astype("uint8"), "RGB")


def star(draw: ImageDraw.ImageDraw, cx, cy, r, fill):
    """A little 4-point sparkle."""
    pts = []
    for i in range(8):
        ang = np.pi / 4 * i
        rad = r if i % 2 == 0 else r * 0.34
        pts.append((cx + rad * np.sin(ang), cy - rad * np.cos(ang)))
    draw.polygon(pts, fill=fill)


def make_icon(px: int) -> Image.Image:
    s = px * 4                                            # supersample
    img = gradient(s, (255, 158, 203), (255, 122, 163), (255, 183, 108))
    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # soft white disc behind the piece
    m = s * 0.26
    d.ellipse([m, m, s - m, s - m], fill=(255, 255, 255, 235))
    # the knight glyph, centered on the disc (nudged up so its base sits inside)
    font = ImageFont.truetype(FONT, int(s * 0.42))
    box = d.textbbox((0, 0), KNIGHT, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    d.text((s / 2 - tw / 2 - box[0], s * 0.46 - th / 2 - box[1]), KNIGHT,
           font=font, fill=PINK + (255,))
    # sparkles
    for cx, cy, r in [(0.24, 0.26, 0.05), (0.78, 0.22, 0.035), (0.75, 0.74, 0.045)]:
        star(d, cx * s, cy * s, r * s, (255, 255, 255, 235))
    img.paste(layer, (0, 0), layer)
    return img.resize((px, px), Image.LANCZOS).convert("RGB")


def make_splash(px: int) -> Image.Image:
    s = px  # splash is already large; one pass with a big font is smooth enough
    img = gradient(s, (255, 214, 232), (255, 243, 196), (196, 245, 225))
    layer = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    font = ImageFont.truetype(FONT, int(s * 0.30))
    box = d.textbbox((0, 0), KNIGHT, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    d.text((s / 2 - tw / 2 - box[0], s * 0.36 - th / 2 - box[1]), KNIGHT,
           font=font, fill=PINK + (255,))
    # "Kid Chess" wordmark under the horsey
    wf = ImageFont.truetype(FONT, int(s * 0.085))
    word = "Kid Chess"
    wb = d.textbbox((0, 0), word, font=wf)
    ww = wb[2] - wb[0]
    d.text((s / 2 - ww / 2 - wb[0], s * 0.60), word, font=wf, fill=INK + (255,))
    img.paste(layer, (0, 0), layer)
    return img.convert("RGB")


def main() -> None:
    icon = make_icon(1024)
    icon.save(ICONSET / "AppIcon-512@2x.png")
    print(f"wrote {ICONSET/'AppIcon-512@2x.png'}  ({icon.size[0]}x{icon.size[1]}, mode={icon.mode})")

    splash = make_splash(2732)
    for name in ("splash-2732x2732.png", "splash-2732x2732-1.png", "splash-2732x2732-2.png"):
        splash.save(SPLASHSET / name)
    print(f"wrote 3x {SPLASHSET/'splash-2732x2732*.png'}  ({splash.size[0]}x{splash.size[1]}, mode={splash.mode})")


if __name__ == "__main__":
    main()
