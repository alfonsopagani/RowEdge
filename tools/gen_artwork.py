"""RemoEdge artwork: home screens, launcher icons and the README badge.

usage: python tools/gen_artwork.py <out dir> [--preview]

Everything is drawn with Pillow at 4x and scaled down. Copy the results to:
  home_540.png  246x322  -> resources/drawables/home_screen.png
  home_1040.png 282x470  -> resources-rectangle-282x470/drawables/home_screen.png
  home_1050.png 480x800  -> resources-rectangle-480x800/drawables/home_screen.png
  icon_35/40/68.png      -> launcher_icon.png in the same three folders
  badge.png (1024x1024, transparent) -> images/RoundBage.png

The lettering uses the DejaVu Sans Condensed font installed with the Connect
IQ SDK. --preview also writes contact sheets with the app's text overlay
approximated in Arial (Windows font path).
"""
import sys, os, math
from PIL import Image, ImageDraw, ImageFont

out_dir = sys.argv[1]
preview = "--preview" in sys.argv
SS = 4

NAVY = (0, 60, 124)
NAVY_DK = (0, 38, 86)
GOLD = (252, 184, 0)
WHITE = (255, 255, 255)
WATER = (36, 110, 190)
WATER_LT = (120, 175, 230)
SKIN = (233, 190, 152)
FONT = os.path.join(os.environ["APPDATA"], "Garmin", "ConnectIQ", "Fonts",
                    "DejaVuSans_Cd_SemiBold_WGL4.ttf")


def sheared_text(text, px, fill, stroke, stroke_w, shear=0.22):
    """Render text and slant it (the open font has no italic)."""
    f = ImageFont.truetype(FONT, px)
    tmp = Image.new("RGBA", (10, 10))
    l, t, r, b = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=f, stroke_width=stroke_w)
    pad = stroke_w + 4
    w, h = r - l + 2 * pad, b - t + 2 * pad
    im = Image.new("RGBA", (w + int(h * shear) + 2, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - l + int(h * shear), pad - t), text, font=f, fill=fill,
                            stroke_width=stroke_w, stroke_fill=stroke)
    im = im.transform(im.size, Image.AFFINE, (1, shear, -h * shear, 0, 1, 0), Image.BICUBIC)
    return im.crop(im.getchannel("A").getbbox())


def draw_badge(im, cx, cy, R, wordmark=True, simple=False):
    """Draw the badge on RGBA image 'im'. R is the outer ring radius in pixels.

    simple=True is the launcher-icon variant: no gauge ticks, no lettering,
    thicker strokes, boat kept inside the ring.
    """
    W, H = im.size
    dr = ImageDraw.Draw(im)
    k = 1.8 if simple else 1.0          # stroke weight

    def P(ux, uy):
        return (cx + ux * R, cy + uy * R)

    def circle(r, **kw):
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], **kw)

    circle(R * 1.00, fill=GOLD)
    circle(R * (0.90 if simple else 0.93), fill=NAVY_DK)
    disc = 0.84 if simple else 0.88
    circle(R * disc, fill=WHITE)

    # --- inside the disc (clipped)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    wy = cy + 0.47 * R
    ld.rectangle([cx - R, wy, cx + R, cy + R], fill=WATER)
    if not simple:
        for n, (off, amp) in enumerate(((0.10, 0.018), (0.22, 0.016), (0.34, 0.014))):
            pts = []
            for i in range(0, 101):
                x = cx - R + 2 * R * i / 100
                y = wy + off * R + math.sin(i / 100 * math.pi * 6 + n * 1.3) * amp * R
                pts.append((x, y))
            ld.line(pts, fill=WATER_LT, width=max(2, int(0.012 * R)))

    # speed gauge
    g_r = 0.36 * R
    gcx, gcy = cx, cy - 0.47 * R
    gbox = [gcx - g_r, gcy - g_r, gcx + g_r, gcy + g_r]
    gw = max(3, int(0.06 * R * k))
    ld.arc(gbox, 180, 360, fill=NAVY, width=gw)
    ld.arc(gbox, 305, 360, fill=GOLD, width=gw)
    if not simple:
        for a in range(195, 350, 22):
            ra = math.radians(a)
            ld.line([(gcx + math.cos(ra) * g_r * 0.66, gcy + math.sin(ra) * g_r * 0.66),
                     (gcx + math.cos(ra) * g_r * 0.82, gcy + math.sin(ra) * g_r * 0.82)],
                    fill=NAVY, width=max(2, int(0.014 * R)))
    na = math.radians(305)
    ld.line([(gcx, gcy), (gcx + math.cos(na) * g_r * 0.80, gcy + math.sin(na) * g_r * 0.80)],
            fill=NAVY, width=max(3, int(0.03 * R * k)))
    r0 = 0.07 * R
    ld.ellipse([gcx - r0, gcy - r0, gcx + r0, gcy + r0], fill=NAVY)

    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse([cx - R * disc, cy - R * disc, cx + R * disc, cy + R * disc], fill=255)
    im.paste(layer, (0, 0), Image.composite(layer.getchannel("A"), Image.new("L", (W, H), 0), mask))
    dr = ImageDraw.Draw(im)

    # --- boat (over the ring), rower, one oar
    hull_y = 0.44
    hx = 0.98 if simple else 1.22
    hull = [P(-hx, hull_y - 0.01), P(-0.7, hull_y - 0.045), P(0.7, hull_y - 0.045), P(hx, hull_y - 0.01),
            P(0.7, hull_y + 0.055), P(-0.7, hull_y + 0.055)]
    dr.polygon(hull, fill=WHITE)
    dr.line(hull + [hull[0]], fill=NAVY_DK, width=max(2, int(0.018 * R * k)), joint="curve")
    if not simple:
        dr.line([P(-0.95, hull_y + 0.012), P(0.95, hull_y + 0.012)], fill=GOLD, width=max(2, int(0.02 * R)))

    hip, sh = (0.12, 0.38), (-0.01, 0.10)
    knee, foot = (-0.20, 0.25), (-0.40, 0.385)
    hand = (-0.36, 0.22)
    dr.line([P(*hip), P(*knee), P(*foot)], fill=NAVY_DK, width=int(0.085 * R * (1.25 if simple else 1)),
            joint="curve")
    tw = 0.085 * (1.25 if simple else 1)
    dx, dy = sh[0] - hip[0], sh[1] - hip[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln * tw, dx / ln * tw

    def tor(t0, t1):
        a = (hip[0] + dx * t0, hip[1] + dy * t0)
        c = (hip[0] + dx * t1, hip[1] + dy * t1)
        return [P(a[0] - nx, a[1] - ny), P(a[0] + nx, a[1] + ny), P(c[0] + nx, c[1] + ny), P(c[0] - nx, c[1] - ny)]

    # torso in the club kit: white with a navy and a gold band
    dr.polygon(tor(0.0, 1.0), fill=WHITE)
    dr.polygon(tor(0.40, 0.56), fill=NAVY)
    dr.polygon(tor(0.56, 0.68), fill=GOLD)
    body = tor(0.0, 1.0)
    dr.line(body + [body[0]], fill=NAVY_DK, width=max(2, int(0.016 * R * k)), joint="curve")
    hc = P(sh[0] - 0.035, sh[1] - 0.10)
    hr = 0.072 * R * (1.2 if simple else 1)
    dr.ellipse([hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr], fill=SKIN, outline=NAVY_DK,
               width=max(2, int(0.016 * R * k)))
    dr.pieslice([hc[0] - hr, hc[1] - hr, hc[0] + hr, hc[1] + hr], 180, 360, fill=NAVY_DK)
    dr.line([P(sh[0], sh[1] + 0.06), P(*hand)], fill=SKIN, width=int(0.055 * R * (1.3 if simple else 1)))
    bx = -0.80 if simple else -0.98
    blade = P(bx, 0.56)
    dr.line([P(*hand), blade], fill=NAVY_DK, width=max(3, int(0.03 * R * k)))
    dr.ellipse([blade[0] - 0.13 * R, blade[1] - 0.045 * R, blade[0] + 0.13 * R, blade[1] + 0.045 * R],
               fill=GOLD, outline=NAVY_DK, width=max(2, int(0.014 * R * k)))
    if not simple:
        for sx, sy, sr in ((-1.10, 0.47, 0.030), (-1.00, 0.44, 0.022), (-0.90, 0.47, 0.018)):
            p = P(sx, sy)
            dr.ellipse([p[0] - sr * R, p[1] - sr * R, p[0] + sr * R, p[1] + sr * R], fill=WHITE)

    # --- wordmark banner across the badge
    by0, by1 = cy - 0.47 * R, cy - 0.13 * R
    if simple:
        by0, by1 = cy - 0.44 * R, cy - 0.16 * R
    sk = 0.10 * R
    half = 0.99 if simple else 1.16
    bx0, bx1 = cx - half * R, cx + half * R
    banner = [(bx0 + sk, by0), (bx1 + sk, by0), (bx1 - sk, by1), (bx0 - sk, by1)]
    if not simple:
        dr.polygon([(x + 0.03 * R, y + 0.035 * R) for x, y in banner], fill=GOLD)
    dr.polygon(banner, fill=NAVY_DK)
    dr.line(banner + [banner[0]], fill=WHITE, width=max(2, int(0.022 * R * k)), joint="curve")
    if wordmark:
        px = int((by1 - by0) * 0.86)
        while True:
            tx = sheared_text("RemoEdge", px, WHITE, NAVY_DK, max(1, px // 40))
            if tx.width <= (bx1 - bx0) * 0.86 and tx.height <= (by1 - by0) * 0.80:
                break
            px -= 4
        im.alpha_composite(tx, (int(cx - tx.width / 2), int((by0 + by1) / 2 - tx.height / 2)))
    elif simple:
        # a gold stripe stands in for the lettering at icon size
        m = (by0 + by1) / 2
        t = (by1 - by0) * 0.16
        dr.polygon([(bx0 + 0.22 * R, m - t), (bx1 - 0.10 * R, m - t), (bx1 - 0.22 * R, m + t), (bx0 + 0.10 * R, m + t)],
                   fill=GOLD)


def draw_home(w, h):
    W, H = w * SS, h * SS
    tall = h > 400
    im = Image.new("RGBA", (W, H), NAVY)
    dr = ImageDraw.Draw(im)
    for y in range(H):                  # darker at the top, where the app writes its text
        t = min(1.0, y / (H * 0.6))
        dr.line([(0, y), (W, y)], fill=tuple(round(NAVY_DK[i] + (NAVY[i] - NAVY_DK[i]) * t) for i in range(3)))
    if tall:
        R, cy = W * 0.375, H * 0.70
    else:
        R, cy = W * 0.345, H * 0.685
    draw_badge(im, W / 2, cy, R)
    return im.resize((w, h), Image.LANCZOS).convert("RGB")


def draw_icon(px, bg=NAVY_DK):
    S = px * 8
    im = Image.new("RGBA", (S, S), bg + (255,))
    draw_badge(im, S / 2, S / 2, S * 0.47, wordmark=False, simple=True)
    return im.resize((px, px), Image.LANCZOS).convert("RGB")


def draw_readme_badge(px=1024):
    S = px * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw_badge(im, S / 2, S / 2, S * 0.385)
    return im.resize((px, px), Image.LANCZOS)


DEV = {"1050": ((480, 800), 61, 21), "1040": ((282, 470), 37, 13), "540": ((246, 322), 27, 15)}
pv = []
for key, ((w, h), hint, xt) in DEV.items():
    im = draw_home(w, h)
    im.save(os.path.join(out_dir, f"home_{key}.png"))
    if preview:
        tall = h > 400
        p = im.copy()
        dr = ImageDraw.Draw(p)
        f = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(hint * 0.78))
        empty_h = h * 48 // 100 if tall else h * 34 // 100
        ty = max((empty_h - (hint * 2 + 6)) // 2, 5)
        for text, col in (("START to row", "white"),
                          ("Tap to configure" if tall else "MENU to configure", "white"),
                          ("Lap to exit", (255, 170, 0))):
            tw = dr.textlength(text, font=f)
            dr.text(((w - tw) / 2, ty), text, font=f, fill=col)
            ty += hint + 4
        dr.text((3, h - 18), "v1.0", font=ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(xt * 0.8)),
                fill=(170, 170, 170))
        pv.append(p)

icons = {}
for px in (35, 40, 68):
    icons[px] = draw_icon(px)
    icons[px].save(os.path.join(out_dir, f"icon_{px}.png"))
badge = draw_readme_badge()
badge.save(os.path.join(out_dir, "badge.png"))

if preview:
    Wt = sum(i.width for i in pv) + 10 * (len(pv) + 1)
    sheet = Image.new("RGB", (Wt, max(i.height for i in pv) + 20), (40, 40, 40))
    x = 10
    for i in pv:
        sheet.paste(i, (x, 10))
        x += i.width + 10
    sheet.save(os.path.join(out_dir, "sheet_home.png"))
    # icons: actual size and enlarged 4x, plus the README badge on white and on dark
    s2 = Image.new("RGB", (980, 420), (40, 40, 40))
    x = 10
    for px in (35, 40, 68):
        s2.paste(icons[px], (x, 10))
        s2.paste(icons[px].resize((px * 4, px * 4), Image.NEAREST), (x, 100))
        x += px * 4 + 20
    b = badge.resize((300, 300), Image.LANCZOS)
    for bgc, bx in (((255, 255, 255), 640),):
        tile = Image.new("RGBA", (300, 300), bgc + (255,))
        tile.alpha_composite(b)
        s2.paste(tile.convert("RGB"), (bx, 60))
    s2.save(os.path.join(out_dir, "sheet_icons.png"))
print("ok")
