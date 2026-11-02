"""Scene cards (English captions) and the thumbnail, drawn with Pillow."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]

PALETTES = {
    "ai-tools": ((18, 24, 64), (88, 60, 200), (255, 214, 10)),
    "ai-learning": ((8, 58, 72), (20, 150, 140), (255, 255, 255)),
    "stock-basics": ((20, 40, 30), (30, 120, 80), (255, 200, 60)),
}


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def gradient(size: tuple[int, int], top: tuple, bottom: tuple) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    px = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        px.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return img


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int, start: int, minimum: int = 40):
    """Largest font size whose wrapped text fits the box."""
    size = start
    while True:
        fnt = font(size)
        lines = wrap(draw, text, fnt, max_width)
        line_h = int(size * 1.25)
        if len(lines) * line_h <= max_height or size <= minimum:
            return fnt, lines, line_h
        size -= 4


def render_card(scene: dict, index: int, total: int, category: str, cfg: dict, out: Path, footer: str = "") -> None:
    w, h = cfg["video"]["width"], cfg["video"]["height"]
    top, bottom, accent = PALETTES.get(category, PALETTES["ai-tools"])
    img = gradient((w, h), top, bottom)
    d = ImageDraw.Draw(img, "RGBA")

    # decorative shapes give each scene a slightly different look
    shift = (index * 173) % 600
    d.ellipse([-200 + shift, 1300 - shift // 2, 500 + shift, 2000 - shift // 2], fill=(255, 255, 255, 22))
    d.ellipse([w - 450 - shift // 3, 150 + shift // 4, w + 250 - shift // 3, 850 + shift // 4], fill=(255, 255, 255, 18))

    d.text((70, 90), cfg["channel"]["name"].upper(), font=font(46), fill=accent)
    # progress bar
    d.rounded_rectangle([70, 170, w - 70, 190], radius=10, fill=(255, 255, 255, 60))
    d.rounded_rectangle([70, 170, 70 + int((w - 140) * index / total), 190], radius=10, fill=accent)

    d.rounded_rectangle([70, 300, 250, 400], radius=50, fill=accent)
    d.text((160, 350), f"{index}/{total}", font=font(52), fill=(20, 20, 30), anchor="mm")

    box_w, box_h = w - 160, 900
    fnt, lines, line_h = fit_text(d, scene["on_screen_text"], box_w, box_h, start=110)
    y = 560 + (box_h - len(lines) * line_h) // 2
    for line in lines:
        d.text((w // 2 + 4, y + 4), line, font=fnt, fill=(0, 0, 0, 120), anchor="ma")
        d.text((w // 2, y), line, font=fnt, fill=(255, 255, 255), anchor="ma")
        y += line_h

    if footer:
        ffnt, flines, fl_h = fit_text(d, footer, w - 140, 200, start=34, minimum=24)
        fy = h - 120 - len(flines) * fl_h
        for line in flines:
            d.text((w // 2, fy), line, font=ffnt, fill=(255, 255, 255, 210), anchor="ma")
            fy += fl_h

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")


def render_thumbnail(text: str, category: str, channel_name: str, out: Path) -> None:
    w, h = 1280, 720
    top, bottom, accent = PALETTES.get(category, PALETTES["ai-tools"])
    img = gradient((w, h), top, bottom)
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([w - 500, -150, w + 150, 500], fill=(255, 255, 255, 28))
    d.rectangle([0, 0, 28, h], fill=accent)
    fnt, lines, line_h = fit_text(d, text, w - 200, 460, start=170, minimum=70)
    y = (h - len(lines) * line_h) // 2 - 10
    for line in lines:
        d.text((100 + 5, y + 5), line, font=fnt, fill=(0, 0, 0, 140))
        d.text((100, y), line, font=fnt, fill=(255, 255, 255))
        y += line_h
    d.text((100, h - 90), channel_name.upper(), font=font(44), fill=accent)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, "JPEG", quality=88)
