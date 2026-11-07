#!/usr/bin/env python3
"""Generate LUMEEI AI Mind branding PNGs for the Flutter module."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parents[1] / "assets" / "branding"


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def grad_color(t: float) -> tuple[int, int, int, int]:
    c0 = (0, 229, 255)
    c1 = (155, 92, 255)
    return (lerp(c0[0], c1[0], t), lerp(c0[1], c1[1], t), lerp(c0[2], c1[2], t), 255)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    w = h = 1024
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))

    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((280, 180, 744, 620), fill=(0, 180, 255, 55))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    cx, cy = 512, 380

    for side in (-1, 1):
        ex = cx + side * 175
        for i in range(36):
            t = i / 35
            col = grad_color(0.15 + 0.7 * t)
            r = 50 - i * 0.3
            draw.ellipse(
                (ex - r, cy - 8 - r * 0.15, ex + r, cy + 68 + r * 0.15),
                outline=col,
                width=3,
            )

    cap = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pts = [
        (cx - 170, cy - 145),
        (cx + 170, cy - 145),
        (cx + 145, cy - 95),
        (cx - 145, cy - 95),
    ]
    for x in range(cx - 170, cx + 170):
        t = (x - (cx - 170)) / 340
        ImageDraw.Draw(cap).line([(x, cy - 145), (x, cy - 95)], fill=grad_color(t), width=1)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    cap.putalpha(mask)
    img = Image.alpha_composite(img, cap)
    draw = ImageDraw.Draw(img)
    draw.line([(cx + 100, cy - 120), (cx + 145, cy - 40)], fill=(155, 92, 255, 255), width=6)
    draw.ellipse((cx + 135, cy - 50, cx + 165, cy - 20), fill=(155, 92, 255, 255))

    draw.rounded_rectangle(
        (cx - 150, cy - 70, cx + 150, cy + 110),
        radius=55,
        fill=(255, 255, 255, 255),
    )
    draw.polygon(
        [(cx + 5, cy + 100), (cx + 45, cy + 100), (cx + 20, cy + 160)],
        fill=(255, 255, 255, 255),
    )
    draw.arc((cx - 85, cy - 10, cx - 25, cy + 40), start=20, end=160, fill=(0, 229, 255, 255), width=10)
    draw.arc((cx + 25, cy - 10, cx + 85, cy + 40), start=20, end=160, fill=(0, 229, 255, 255), width=10)

    try:
        font_big = ImageFont.truetype("arialbd.ttf", 110)
        font_small = ImageFont.truetype("arial.ttf", 42)
    except OSError:
        font_big = ImageFont.load_default()
        font_small = font_big

    text = "LUMEEI"
    bbox = draw.textbbox((0, 0), text, font=font_big)
    tw = bbox[2] - bbox[0]
    tx = (w - tw) // 2
    ty = 620
    draw.text((tx, ty), text, font=font_big, fill=(255, 255, 255, 255))
    draw.ellipse((tx + tw - 28, ty + 12, tx + tw - 4, ty + 36), fill=(80, 140, 255, 255))

    sub = "AI MIND"
    sb = draw.textbbox((0, 0), sub, font=font_small)
    sw = sb[2] - sb[0]
    sx = (w - sw) // 2
    sy = 750
    for i, ch in enumerate(sub):
        t = i / max(1, len(sub) - 1)
        prefix_w = draw.textbbox((0, 0), sub[:i], font=font_small)[2]
        draw.text((sx + prefix_w, sy), ch, font=font_small, fill=grad_color(t))
    draw.line((sx - 90, sy + 22, sx - 20, sy + 22), fill=grad_color(0.1), width=3)
    draw.line((sx + sw + 20, sy + 22, sx + sw + 90, sy + 22), fill=grad_color(0.9), width=3)

    icon = img.crop((220, 140, 804, 600)).resize((512, 512), Image.Resampling.LANCZOS)
    fab = Image.new("RGBA", (512, 512), (0, 0, 0, 255))
    fab.paste(icon, (0, 0), icon)

    logo_path = OUT / "lumeei_ai_mind_logo.png"
    icon_path = OUT / "lumeei_ai_mind_icon.png"
    img.save(logo_path)
    fab.save(icon_path)
    print(f"wrote {logo_path} ({logo_path.stat().st_size})")
    print(f"wrote {icon_path} ({icon_path.stat().st_size})")


if __name__ == "__main__":
    main()
