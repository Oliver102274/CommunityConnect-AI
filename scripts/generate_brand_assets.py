"""Generate PNG brand assets (favicons + social preview) for CommunityConnect AI.

Draws the same shapes as frontend/assets/favicon.svg with Pillow.
Run from the project root:  python scripts/generate_brand_assets.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "frontend" / "assets"
DOCS = ROOT / "docs" / "images"

NAVY = (11, 37, 69)
NAVY_2 = (19, 49, 92)
TEAL = (15, 139, 141)
AQUA = (127, 224, 224)
WHITE = (255, 255, 255)


def draw_icon(size, rounded=True):
    """Render the 64x64 icon design at `size` px (supersampled)."""
    ss = 8
    s = size * ss / 64.0
    img = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def c(cx, cy, r, fill, outline=None, width=0):
        d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s],
                  fill=fill, outline=outline, width=int(width * s))

    if rounded:
        d.rounded_rectangle([0, 0, 64 * s, 64 * s], radius=14 * s, fill=NAVY)
    else:
        d.rectangle([0, 0, 64 * s, 64 * s], fill=NAVY)

    c(30, 27, 17, WHITE)
    d.polygon([(14.1 * s, 33 * s), (45.9 * s, 33 * s), (30 * s, 55 * s)], fill=WHITE)

    c(30, 22, 5.5, TEAL)
    d.pieslice([20.5 * s, 29 * s, 39.5 * s, 45 * s], 180, 360, fill=TEAL)

    d.polygon([(41 * s, 21 * s), (41.5 * s, 29 * s), (47 * s, 24 * s)], fill=AQUA,
              outline=NAVY, width=int(2.5 * s))
    c(49, 15, 10 + 1.25, NAVY)
    c(49, 15, 10 - 1.25, AQUA)
    for x in (45, 49, 53):
        c(x, 15, 1.7, NAVY)

    return img.resize((size, size), Image.LANCZOS)


def font(size, bold=False):
    names = ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_social_card():
    """1200x630 Open Graph / Twitter preview image."""
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), NAVY)
    d = ImageDraw.Draw(img)

    # vertical gradient navy -> slightly lighter navy
    for y in range(h):
        t = y / h
        col = tuple(int(NAVY[i] + (NAVY_2[i] - NAVY[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=col)
    # teal accent bar
    d.rectangle([0, h - 14, w, h], fill=TEAL)

    icon = draw_icon(220)
    img.paste(icon, (90, 150), icon)

    x = 350
    d.text((x, 170), "CommunityConnect", font=font(76, True), fill=WHITE)
    tw = d.textlength("CommunityConnect ", font=font(76, True))
    d.text((x + tw, 170), "AI", font=font(76, True), fill=AQUA)
    d.text((x, 275), "Connecting people to the help they need through AI.",
           font=font(34), fill=(220, 235, 245))
    d.text((x, 345), "Veteran support  •  Food assistance  •  Employment",
           font=font(28), fill=AQUA)
    d.text((x, 400), "Miami-Dade County  •  Powered by Snowflake Cortex AI",
           font=font(26), fill=(170, 190, 210))
    return img


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    for size in (16, 32, 48, 192, 512):
        draw_icon(size).save(ASSETS / f"favicon-{size}.png")
    draw_icon(180, rounded=False).save(ASSETS / "apple-touch-icon.png")
    draw_icon(48).save(ASSETS / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

    card = draw_social_card()
    card.save(ASSETS / "og-image.png", optimize=True)
    card.save(DOCS / "banner.png", optimize=True)
    print("Brand assets written to", ASSETS, "and", DOCS)


if __name__ == "__main__":
    main()
