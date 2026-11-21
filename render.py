#!/usr/bin/env python3
"""Render entry.png: one image summing up the world's news of
Friday 20 November 2026. Deterministic: no random, no time, no network,
fixed fonts. Run: python3 render.py  ->  entry.png beside this file.

Layout (1024x1024): navy header with the date, a dominant red lead
panel (roughly the top half), a 2x2 grid of four smaller stories, an
"also today" strip and a credit footer.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
PAPER = (247, 243, 234)
NAVY = (20, 33, 61)
NAVY_DARK = (13, 22, 42)
RED = (192, 57, 43)
RED_DARK = (160, 44, 32)
GOLD = (232, 184, 75)
INK = (26, 26, 26)
MUTED = (88, 88, 88)
WHITE = (255, 255, 255)
BORDER = (222, 214, 198)
PANEL = (255, 255, 255)
CREAM = (255, 244, 214)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def fb(size):
    return ImageFont.truetype(FONT_BOLD, size)


def fr(size):
    return ImageFont.truetype(FONT_REG, size)


def fit_font(draw, text, path, max_size, max_w):
    """Largest font size up to max_size whose text fits max_w on one line."""
    size = max_size
    while size > 10:
        fnt = ImageFont.truetype(path, size)
        if draw.textlength(text, font=fnt) <= max_w:
            return fnt
        size -= 1
    return ImageFont.truetype(path, 10)


def wrap(draw, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, fnt, fill, max_w, leading=None):
    """Draw wrapped text; return y just below the last line."""
    lh = leading or int(fnt.size * 1.28)
    for line in wrap(draw, text, fnt, max_w):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += lh
    return y


# ---------------------------------------------------------------- icons
def icon_kyiv_blast(d, x, y, w, h):
    """City skyline at night with a missile streak and a blast burst
    above it. Flat shapes in gold/white on the red lead panel."""
    base = y + h - 6
    # skyline: a row of dark-navy buildings of varied heights
    heights = [0.42, 0.62, 0.34, 0.78, 0.52, 0.66, 0.40]
    bw = w // len(heights)
    for i, frac in enumerate(heights):
        bx = x + i * bw + 2
        top = base - int(h * frac)
        d.rectangle([bx, top, bx + bw - 4, base], fill=NAVY_DARK)
        # a few lit windows
        for wy in range(top + 8, base - 6, 16):
            d.rectangle([bx + 4, wy, bx + 8, wy + 7], fill=GOLD)
    # missile streak: diagonal line with a small missile body
    mx0, my0 = x + w - 18, y + 6
    mx1, my1 = x + w - 118, y + 96
    d.line([(mx0, my0), (mx1, my1)], fill=WHITE, width=5)
    d.line([(mx0, my0), (mx0 - 16, my0 + 2)], fill=GOLD, width=3)
    d.ellipse([mx1 - 7, my1 - 7, mx1 + 7, my1 + 7], fill=GOLD)
    # blast starburst above the tallest building
    bx, by = x + w // 2 - 12, y + 34
    for ang in range(0, 360, 30):
        r = 34 if ang % 60 == 0 else 20
        x2 = bx + r * math.cos(math.radians(ang))
        y2 = by + r * math.sin(math.radians(ang))
        d.line([(bx, by), (x2, y2)], fill=GOLD, width=4)
    d.ellipse([bx - 12, by - 12, bx + 12, by + 12], fill=GOLD)
    d.ellipse([bx - 5, by - 5, bx + 5, by + 5], fill=WHITE)


def icon_flags_eu_uk(d, cx, cy, s, col):
    """EU flag (blue, ring of gold stars) beside a Union Jack."""
    fw, fh = s // 2 - 4, int((s // 2 - 4) * 0.62)
    # EU flag
    ex, ey = cx - s // 2, cy - fh // 2
    d.rectangle([ex, ey, ex + fw, ey + fh], fill=(0, 51, 153))
    for k in range(12):
        ang = math.radians(k * 30 - 90)
        sx = ex + fw // 2 + int(fw * 0.32 * math.cos(ang))
        sy = ey + fh // 2 + int(fh * 0.32 * math.sin(ang))
        d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=GOLD)
    # UK flag, simplified
    ux, uy = cx + 6, cy - fh // 2
    d.rectangle([ux, uy, ux + fw, uy + fh], fill=(0, 36, 125))
    d.line([(ux, uy), (ux + fw, uy + fh)], fill=WHITE, width=5)
    d.line([(ux + fw, uy), (ux, uy + fh)], fill=WHITE, width=5)
    d.line([(ux, uy), (ux + fw, uy + fh)], fill=(200, 16, 46), width=2)
    d.line([(ux + fw, uy), (ux, uy + fh)], fill=(200, 16, 46), width=2)
    d.rectangle([ux + fw // 2 - 3, uy, ux + fw // 2 + 3, uy + fh],
                fill=WHITE)
    d.rectangle([ux, uy + fh // 2 - 3, ux + fw, uy + fh // 2 + 3],
                fill=WHITE)
    d.rectangle([ux + fw // 2 - 1, uy, ux + fw // 2 + 1, uy + fh],
                fill=(200, 16, 46))
    d.rectangle([ux, uy + fh // 2 - 1, ux + fw, uy + fh // 2 + 1],
                fill=(200, 16, 46))


def icon_controller(d, cx, cy, s, col):
    """Game controller: rounded body, d-pad, buttons, sticks."""
    d.rounded_rectangle([cx - s // 2, cy - s // 5, cx + s // 2,
                         cy + s // 5], radius=s // 6, fill=col)
    d.polygon([(cx - s // 2 + 6, cy - s // 8),
               (cx - s // 2 - s // 10, cy + s // 4),
               (cx - s // 2 + s // 6, cy + s // 4)], fill=col)
    d.polygon([(cx + s // 2 - 6, cy - s // 8),
               (cx + s // 2 + s // 10, cy + s // 4),
               (cx + s // 2 - s // 6, cy + s // 4)], fill=col)
    # d-pad
    d.rectangle([cx - s // 3 - 4, cy - 4, cx - s // 3 + 4, cy + 4],
                fill=WHITE)
    d.rectangle([cx - s // 3 - 4 + 4, cy - 8, cx - s // 3 + 4 - 4,
                 cy + 8], fill=WHITE)
    # four buttons
    for dx, dy in ((s // 3, -6), (s // 3 + 10, 4), (s // 3 - 10, 4),
                   (s // 3, 14)):
        d.ellipse([cx + dx - 4, cy + dy - 4, cx + dx + 4, cy + dy + 4],
                  fill=GOLD)
    # sticks
    for sx in (cx - s // 8, cx + s // 8):
        d.ellipse([sx - 5, cy + s // 8 - 5, sx + 5, cy + s // 8 + 5],
                  fill=WHITE)


def icon_globe_leaf(d, cx, cy, s, col):
    """Globe with a green leaf and a red slash: fossil fuels dropped."""
    r = s // 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=4)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(214, 234, 248))
    # land blobs
    d.ellipse([cx - r + 6, cy - r + 8, cx - 4, cy - 2], fill=(46, 139, 87))
    d.ellipse([cx + 2, cy + 2, cx + r - 6, cy + r - 8],
              fill=(46, 139, 87))
    d.arc([cx - r, cy - r // 2, cx + r, cy + r // 2], 200, 340,
          fill=col, width=3)
    # red slash across the globe
    d.line([(cx - r + 4, cy + r - 4), (cx + r - 4, cy - r + 4)],
           fill=RED, width=6)


def icon_barrier(d, cx, cy, s, col):
    """Road barrier gate with a stop sign: a sealed border."""
    # two posts
    d.rectangle([cx - s // 2, cy - s // 6, cx - s // 2 + 6, cy + s // 2],
                fill=col)
    d.rectangle([cx + s // 2 - 6, cy - s // 6, cx + s // 2, cy + s // 2],
                fill=col)
    # striped barrier bar
    for i in range(6):
        x0 = cx - s // 2 + i * (s // 6)
        x1 = x0 + s // 6
        fill = RED if i % 2 == 0 else WHITE
        d.polygon([(x0, cy - s // 6), (x1, cy - s // 6),
                   (x1 - 8, cy), (x0 - 8, cy)], fill=fill)
    d.rectangle([cx - s // 2, cy - s // 6, cx + s // 2, cy], outline=col,
                width=2)
    # stop sign on top: a bold red disc with a white "!"
    r = s // 6
    d.ellipse([cx - r, cy - s // 2 - 2, cx + r, cy - s // 2 - 2 + 2 * r],
              fill=RED, outline=WHITE, width=2)
    d.text((cx - 6, cy - s // 2 + 2), "!", font=fb(22), fill=WHITE)


# ---------------------------------------------------------------- layout
PANELS = [
    ("BRUSSELS \u00b7 EUROPE", "EU\u2013UK STRIKE NEW DEALS",
     "Second post-Brexit summit: easier food trade, linked carbon "
     "markets, youth travel for 100,000.",
     icon_flags_eu_uk),
    ("GAMES \u00b7 RECORDS", "GTA 6 SMASHES $2.36BN",
     "24.6 million copies on day one \u2014 the biggest entertainment "
     "launch ever.",
     icon_controller),
    ("CLIMATE \u00b7 ANTALYA", "COP31 DRAFT DROPS FOSSIL FUELS",
     "On the talks' final day, the slimmed-down deal removes any call "
     "to phase out fossil fuels.",
     icon_globe_leaf),
    ("BALTICS \u00b7 SECURITY", "ESTONIA SEALS RUSSIAN BORDER",
     "All land crossings shut from 1 Dec after a GRU-linked sabotage "
     "plot against a drone maker.",
     icon_barrier),
]

ALSO = ("White House fires cyber chief after a week of tech outages  "
        "\u00b7  Gas blast kills 6 in Georgia  \u00b7  US auctions first "
        "deep-sea mining leases  \u00b7  Stocks fall a 5th day, "
        "Nikkei \u22124.8%")


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- header band
    d.rectangle([0, 0, W, 148], fill=NAVY)
    d.rectangle([0, 148, W, 154], fill=GOLD)
    d.text((48, 22), "T H E   W O R L D   I N   O N E   P I C T U R E",
           font=fb(25), fill=GOLD)
    date_fnt = fit_font(d, "FRIDAY 20 NOVEMBER 2026", FONT_BOLD, 64,
                        W - 96)
    d.text((48, 56), "FRIDAY 20 NOVEMBER 2026",
           font=date_fnt, fill=WHITE)

    # ---- lead panel: full-width red block, top half of the image
    lx, ly, lw, lh = 24, 168, W - 48, 362
    d.rounded_rectangle([lx, ly, lx + lw, ly + lh], radius=16, fill=RED)
    d.text((lx + 28, ly + 18), "LEAD STORY  \u00b7  KYIV  \u00b7  UKRAINE",
           font=fb(21), fill=GOLD)
    # pictogram: skyline + blast, left column
    icon_kyiv_blast(d, lx + 28, ly + 88, 240, 240)
    tx = lx + 300
    tw = lw - 300 - 28
    head1 = fit_font(d, "RUSSIA POUNDS", FONT_BOLD, 76, tw)
    d.text((tx, ly + 62), "RUSSIA POUNDS", font=head1, fill=WHITE)
    head2 = fit_font(d, "KYIV", FONT_BOLD, 76, tw)
    d.text((tx, ly + 62 + 84), "KYIV", font=head2, fill=WHITE)
    d.line([(tx, ly + 62 + 84 + 86), (tx + tw, ly + 62 + 84 + 86)],
           fill=GOLD, width=4)
    draw_wrapped(d, tx, ly + 62 + 84 + 104,
                 "Overnight barrage kills 8 after Putin vowed revenge "
                 "for the Crimea Bridge strikes.",
                 fr(24), CREAM, tw, leading=31)

    # ---- 2x2 grid of panels
    gx, gy = 24, 546
    cw, chh, gap = 480, 158, 14
    for i, (kick, head, body, icon) in enumerate(PANELS):
        col, row = i % 2, i // 2
        px = gx + col * (cw + gap)
        py = gy + row * (chh + gap)
        d.rounded_rectangle([px, py, px + cw, py + chh], radius=12,
                            fill=PANEL, outline=BORDER, width=2)
        icon(d, px + 52, py + chh // 2, 88, NAVY)
        tx = px + 108
        d.text((tx, py + 12), kick, font=fb(15), fill=RED)
        y = draw_wrapped(d, tx, py + 35, head, fb(24), INK,
                         cw - 108 - 16, leading=29)
        lines = wrap(d, body, fr(17), cw - 108 - 16)[:3]
        by = y + 3
        for line in lines:
            d.text((tx, by), line, font=fr(17), fill=MUTED)
            by += 21

    # ---- footer strip: more stories
    fy = 892
    d.rounded_rectangle([24, fy, W - 24, fy + 76], radius=10, fill=NAVY)
    d.text((40, fy + 8), "ALSO TODAY", font=fb(17), fill=GOLD)
    draw_wrapped(d, 40, fy + 31, ALSO, fr(16), WHITE, W - 80, leading=20)

    # ---- footer credit
    fy2 = 978
    d.text((24, fy2),
           "Compiled from wire reports \u00b7 All events happened or were "
           "first reported on 20 November 2026",
           font=fr(18), fill=MUTED)
    d.text((24, fy2 + 24), "20 NOV 2026  \u00b7  THE WORLD IN ONE PICTURE",
           font=fb(16), fill=NAVY)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "entry.png")
    img.save(out, format="PNG")
    print("wrote", out, img.size)


if __name__ == "__main__":
    main()
