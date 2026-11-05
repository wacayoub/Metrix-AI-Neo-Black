#!/usr/bin/env python3
"""Render the project's NEO TV mark into deterministic launcher PNGs (Pillow)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'app/src/main/res'
ART = ROOT / 'artwork'
FONT = RES / 'font/raleway_light.ttf'


def background(size):
    w, h = size
    im = Image.new('RGB', size)
    pixels = im.load()
    for y in range(h):
        for x in range(w):
            t = .65*x/max(1, w-1) + .35*(1-y/max(1, h-1))
            pixels[x, y] = (int(3+3*t), int(19+28*t), int(35+44*t))
    return im


def mark(draw, x, y, scale):
    def box(a, b, c, d):
        return (x+a*scale, y+b*scale, x+c*scale, y+d*scale)
    draw.rounded_rectangle(box(24, 31, 84, 76), radius=7*scale, outline='#11B8EF', width=max(1, round(3*scale)))
    draw.line([box(44, 82, 64, 82)[:2], box(44, 82, 64, 82)[2:]], fill='#E9F0F8', width=max(1, round(3*scale)))
    draw.line([(x+54*scale, y+76*scale), (x+54*scale, y+81*scale)], fill='#E9F0F8', width=max(1, round(3*scale)))
    points = [(37, 65), (37, 42), (44, 42), (64, 58), (64, 42), (71, 42), (71, 65), (64, 65), (44, 49), (44, 65)]
    draw.polygon([(x+a*scale, y+b*scale) for a, b in points], fill='#E9F0F8')
    draw.polygon([(x+a*scale, y+b*scale) for a, b in [(44,42),(64,58),(64,65),(44,49)]], fill='#11B8EF')


def icon(size):
    im = background((size, size)); mark(ImageDraw.Draw(im), 0, 0, size/108)
    return im


def banner():
    im = background((1280, 720)); d = ImageDraw.Draw(im)
    # Same mark, with the brand name actually embedded in the TV banner.
    mark(d, 35, 122, 4.4)
    d.text((565, 165), 'METRIX', font=ImageFont.truetype(str(FONT), 60), fill='#E9F0F8')
    d.text((550, 230), 'NEO', font=ImageFont.truetype(str(FONT), 190), fill='#11B8EF', stroke_width=1)
    d.line((568, 470, 624, 470), fill='#11B8EF', width=5)
    d.text((650, 438), 'AI TV', font=ImageFont.truetype(str(FONT), 56), fill='#E9F0F8')
    return im


def main():
    ART.mkdir(exist_ok=True)
    square = icon(1280).convert('RGBA'); wide = banner()
    mask = Image.new('L', square.size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 1279, 1279), radius=240, fill=255)
    square.putalpha(mask)
    square.resize((512, 512), Image.Resampling.LANCZOS).save(ART/'launcher-icon.png', optimize=True)
    wide.save(ART/'launcher-banner.png', optimize=True)
    for density, ratio in [('mdpi', 1), ('hdpi', 1.5), ('xhdpi', 2), ('xxhdpi', 3), ('xxxhdpi', 4)]:
        target = RES / ('mipmap-'+density); target.mkdir(exist_ok=True)
        square.resize((int(80*ratio), int(80*ratio)), Image.Resampling.LANCZOS).save(target/'neo_launcher_icon.png', optimize=True)
        wide.resize((int(160*ratio), int(90*ratio)), Image.Resampling.LANCZOS).save(target/'neo_launcher_banner.png', optimize=True)
    (ART/'launcher-mark.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108">
<rect width="108" height="108" rx="20" fill="#031323"/>
<rect x="24" y="31" width="60" height="45" rx="7" fill="none" stroke="#11B8EF" stroke-width="3"/>
<path d="M44 82H64 M54 76V82" fill="none" stroke="#E9F0F8" stroke-width="3"/>
<path d="M37 65V42H44L64 58V42H71V65H64L44 49V65Z" fill="#E9F0F8"/>
<path d="M44 42L64 58V65L44 49Z" fill="#11B8EF"/></svg>''', encoding='utf-8')
    print('Launcher icon and banner exported in five densities.')


if __name__ == '__main__':
    main()
