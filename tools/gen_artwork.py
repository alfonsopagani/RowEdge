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

    # --- boat, rower and oar, painted as brush strokes: circles stamped along
    # curves, so every limb is rounded and tapered
    def bez(p0, p1, p2, t):
        u = 1 - t
        return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])

    def brush(p0, p1, p2, w0, w1, fill, t0=0.0, t1=1.0, grow=0.0):
        steps = 90
        for s in range(steps + 1):
            t = t0 + (t1 - t0) * s / steps
            x, y = P(*bez(p0, p1, p2, t))
            r = (w0 + (w1 - w0) * t + grow) * R
            dr.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def outlined(p0, p1, p2, w0, w1, fill):
        brush(p0, p1, p2, w0, w1, NAVY_DK, grow=ol)
        brush(p0, p1, p2, w0, w1, fill)

    ol = 0.017 * k                      # outline thickness, in units of R
    fat = 1.3 if simple else 1.0        # heavier figure at icon size

    # joints of the figure, at the catch: seated low in the boat, body swung
    # forward from the hips, arms long, knees up
    hip = (0.17, 0.465)
    back = (0.12, 0.275)                # control point: the curve of the back
    sh = (-0.055, 0.135)
    knee = (-0.13, 0.238)
    foot = (-0.33, 0.470)
    elbow = (-0.245, 0.250)
    hand = (-0.415, 0.262)

    # legs: thighs rise to the knees, shins drop to the stretcher
    brush(hip, (0.03, 0.285), knee, 0.066 * fat, 0.054 * fat, NAVY_DK)
    brush(knee, (-0.24, 0.310), foot, 0.050 * fat, 0.038 * fat, NAVY_DK)

    # neck first: the torso, drawn next, covers its base
    hc = (sh[0] - 0.075, sh[1] - 0.112)
    hr = 0.070 * fat
    outlined((sh[0] - 0.015, sh[1] - 0.015), (sh[0] - 0.045, sh[1] - 0.065), hc, 0.031 * fat, 0.031 * fat, SKIN)

    # torso in the club kit: narrow at the waist, broad at the shoulders,
    # white with a navy and a gold band across the chest
    tw0, tw1 = 0.064 * fat, 0.088 * fat
    outlined(hip, back, sh, tw0, tw1, WHITE)

    def band(ta, tb, fill, extra=0.0):
        pts = []
        for t, side in ((ta, 1), (tb, 1), (tb, -1), (ta, -1)):
            c = bez(hip, back, sh, t)
            d = bez(hip, back, sh, min(1.0, t + 0.02))
            e = bez(hip, back, sh, max(0.0, t - 0.02))
            tx, ty = d[0] - e[0], d[1] - e[1]
            ln = math.hypot(tx, ty)
            w = tw0 + (tw1 - tw0) * t + extra
            pts.append(P(c[0] - ty / ln * w * side, c[1] + tx / ln * w * side))
        dr.polygon(pts, fill=fill)

    band(0.56, 0.70, NAVY)
    band(0.70, 0.81, GOLD)
    # navy shorts with a straight waistline: hips and thighs read as one shape
    band(0.0, 0.25, NAVY_DK, ol)
    brush(hip, back, sh, tw0, tw1, NAVY_DK, t0=0.0, t1=0.05, grow=ol)

    # head in front of the torso, then the navy cap: dome tilted forward and a visor
    hx_, hy_ = P(*hc)
    r = (hr + ol) * R
    dr.ellipse([hx_ - r, hy_ - r, hx_ + r, hy_ + r], fill=NAVY_DK)
    r = hr * R
    dr.ellipse([hx_ - r, hy_ - r, hx_ + r, hy_ + r], fill=SKIN)
    x, y = hx_, hy_
    cr = (hr + ol * 1.2) * R
    dr.pieslice([x - cr, y - cr, x + cr, y + cr], 170, 350, fill=NAVY_DK)
    brush((hc[0] - hr * 0.80, hc[1] - hr * 0.18), (hc[0] - hr * 1.5, hc[1] - hr * 0.22),
          (hc[0] - hr * 2.05, hc[1] + hr * 0.08), 0.020 * fat, 0.012 * fat, NAVY_DK)

    # hull, drawn over the legs and hips: the rower sits inside the shell
    hx = 0.98 if simple else 1.22
    top = [bez((-hx, 0.462), (0.0, 0.392), (hx, 0.450), i / 40.0) for i in range(41)]
    bot = [bez((hx, 0.450), (0.0, 0.715), (-hx, 0.462), i / 40.0) for i in range(41)]
    hull = [P(*p) for p in top + bot]
    dr.polygon(hull, fill=WHITE)
    dr.line(hull + [hull[0]], fill=NAVY_DK, width=max(2, int(0.018 * R * k)), joint="curve")
    if not simple:
        stripe = [P(*bez((-0.93, 0.486), (0.0, 0.462), (0.93, 0.476), i / 40.0)) for i in range(41)]
        dr.line(stripe, fill=GOLD, width=max(2, int(0.022 * R)), joint="curve")

    # oar: straight shaft over the gunwale to a hatchet blade. Proportions of
    # a sculling hatchet: about twice as long as deep, shaft joining at the
    # top corner and running along the top edge, deepest a third of the way
    # out, narrower at the tip, rounded corners.
    bx = -0.80 if simple else -0.98
    neck = (bx + 0.25, 0.455)
    ux, uy = neck[0] - hand[0], neck[1] - hand[1]
    ul = math.hypot(ux, uy)
    ux, uy = ux / ul, uy / ul           # along the shaft, towards the tip
    vx, vy = -uy, ux                    # across the shaft, towards the water
    if vy < 0:
        vx, vy = -vx, -vy
    bl = 0.37 * (1.1 if simple else 1.0)        # blade length
    bh = 0.175 * (1.1 if simple else 1.0)       # depth at the broadest point

    def Bu(u, v):
        return (neck[0] + ux * u + vx * v, neck[1] + uy * u + vy * v)

    def seg(p0, p1, p2, n=10):
        return [P(*Bu(*bez(p0, p1, p2, i / float(n)))) for i in range(n + 1)]

    tipd = 0.76 * bh                    # depth at the tip
    blade = [P(*Bu(-0.05, -0.014)), P(*Bu(bl - 0.035, -0.022))]
    blade += seg((bl - 0.035, -0.022), (bl + 0.006, -0.022), (bl + 0.008, 0.016))      # top corner
    blade += seg((bl + 0.008, 0.016), (bl + 0.014, tipd * 0.5), (bl + 0.004, tipd - 0.03))  # tip
    blade += seg((bl + 0.004, tipd - 0.03), (bl + 0.002, tipd + 0.004), (bl - 0.035, tipd + 0.008))  # lower corner
    blade += seg((bl - 0.035, tipd + 0.008), (bl * 0.68, bh * 0.99), (bl * 0.36, bh))  # lower edge
    blade += seg((bl * 0.36, bh), (bl * 0.17, bh * 1.0), (bl * 0.10, bh * 0.48))       # heel
    blade += seg((bl * 0.10, bh * 0.48), (bl * 0.05, bh * 0.12), (-0.05, 0.014))       # sweep into the neck
    dr.polygon(blade, fill=WHITE)
    dr.line(blade + [blade[0]], fill=NAVY_DK, width=max(2, int(ol * R * 1.1)), joint="curve")
    spine = Bu(bl * 0.62, 0.0)
    brush(hand, ((hand[0] + spine[0]) / 2, (hand[1] + spine[1]) / 2), spine, 0.016 * fat, 0.008 * fat, NAVY_DK)

    # arm in front of torso and oar: a rounded shoulder tapering to the hand,
    # drawn as one shape (all outlines, then all fills) so the elbow shows no
    # inner contour
    arm_a = ((sh[0] + 0.012, sh[1] + 0.030), (-0.13, 0.212), elbow, 0.047 * fat, 0.031 * fat)
    arm_b = (elbow, (-0.33, 0.268), hand, 0.031 * fat, 0.027 * fat)
    for part in (arm_a, arm_b):
        brush(part[0], part[1], part[2], part[3], part[4], NAVY_DK, grow=ol)
    for part in (arm_a, arm_b):
        brush(part[0], part[1], part[2], part[3], part[4], SKIN)

    if not simple:
        # spray thrown up by the blade
        brush(Bu(bl * 0.85, -0.03), Bu(bl + 0.07, -0.13), Bu(bl + 0.17, -0.08), 0.013, 0.003, WHITE)
        brush(Bu(bl * 0.55, -0.04), Bu(bl * 0.75, -0.15), Bu(bl + 0.02, -0.17), 0.011, 0.003, WHITE)
        for u, v, sr in ((bl + 0.21, -0.03, 0.014), (bl + 0.08, -0.20, 0.010), (bl + 0.15, 0.04, 0.008)):
            px_, py_ = P(*Bu(u, v))
            dr.ellipse([px_ - sr * R, py_ - sr * R, px_ + sr * R, py_ + sr * R], fill=WHITE)

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
