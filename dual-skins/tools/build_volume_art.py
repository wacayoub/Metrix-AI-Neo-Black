"""Build the native-size PNG artwork for the MetrixNEO volume styles."""

import argparse
import io
import sys
from math import sin
from pathlib import Path

from cairosvg import svg2png
from PIL import Image, ImageChops, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))
from Components.MetrixNEO.volume_display import TRACK_HEIGHT, TRACK_WIDTH, TRACK_X, TRACK_Y, LENS_TIP_WIDTH

PANEL_SIZE = (460, 64)
DIGITS_SIZE = (56, 42)
TRACK_SIZE = (TRACK_WIDTH, TRACK_HEIGHT)


def svg(size, shapes, definitions=""):
    width, height = size
    document = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
        f"<defs>{definitions}</defs>{shapes}</svg>"
    )
    png = svg2png(bytestring=document.encode(), output_width=width * 2, output_height=height * 2)
    return Image.open(io.BytesIO(png)).convert("RGBA").resize(size, Image.Resampling.LANCZOS)


def gradient(name, colors, horizontal=False):
    end = 'x2="100%" y2="0%"' if horizontal else 'x2="0%" y2="100%"'
    stops = "".join(
        f'<stop offset="{offset}" stop-color="{color}" stop-opacity="{opacity}"/>'
        for offset, color, opacity in colors
    )
    return f'<linearGradient id="{name}" x1="0%" y1="0%" {end}>{stops}</linearGradient>'


def rounded_track(paint, y=12, height=8, radius=4):
    return f'<rect x="66" y="{TRACK_Y + y}" width="{TRACK_WIDTH}" height="{height}" rx="{radius}" fill="{paint}"/>'


def glass_panel(shape, colors, edge, details):
    glass = gradient("glass", colors)
    rim = gradient("rim", [(0, edge, .68), (.45, edge, .18), (1, edge, .56)])
    outline = f'<path d="{shape}"/>'
    clip = f'<clipPath id="shell">{outline}</clipPath>'
    shapes = (
        f'<path d="{shape}" fill="url(#glass)"/>'
        f'<g clip-path="url(#shell)">{details}</g>'
        f'<path d="{shape}" fill="none" stroke="url(#rim)" stroke-width="1"/>'
    )
    return svg(PANEL_SIZE, shapes, glass + rim + clip)


def thin_fill(top, bottom, radius=4):
    light = gradient("light", [(0, top, 1), (1, bottom, 1)])
    return svg(TRACK_SIZE, f'<rect y="12" width="{TRACK_WIDTH}" height="8" rx="{radius}" fill="url(#light)"/>', light)


def dots(paint, x=0, y=0):
    return "".join(
        f'<circle cx="{x + col * 5 + 2.5}" cy="{y + row * 4.5 + 7}" r="1.05" fill="{paint}"/>'
        for col in range(63) for row in range(5)
    )


def build_panels():
    rounded = "M12 1 H448 Q459 1 459 12 V52 Q459 63 448 63 H12 Q1 63 1 52 V12 Q1 1 12 1 Z"
    navy = [(0, "#19364f", .88), (.45, "#091a2d", .88), (1, "#0a2435", .87)]
    track = rounded_track("#254256")

    yield "liquid", glass_panel(rounded, navy, "#70dcee", track + """
        <path d="M1 54 Q57 62 119 54 T241 54 T357 54 T459 51 V63 H1 Z" fill="#087e93" fill-opacity=".45"/>
        <path d="M1 54 Q57 62 119 54 T241 54 T357 54 T459 51" fill="none" stroke="#63e8f4" stroke-opacity=".65" stroke-width=".7"/>
    """), thin_fill("#77fff4", "#04c6ca")

    prism = "M16 1 H459 V48 L444 63 H1 V16 Z"
    yield "prism", glass_panel(prism, navy, "#a4e9fd", """
        <path d="M16 2 H292 L222 32 Z" fill="#20e0eb" fill-opacity=".30"/>
        <path d="M1 16 L16 2 L222 32 L1 61 Z" fill="#037c97" fill-opacity=".42"/>
        <path d="M1 61 L222 32 L444 62 Z" fill="#00bfd5" fill-opacity=".18"/>
        <path d="M222 32 L458 2 L458 48 Z" fill="#c0efff" fill-opacity=".10"/>
        <path d="M16 2 L222 32 L458 2 M1 61 L222 32 L444 62" fill="none" stroke="#69e9f4" stroke-opacity=".38" stroke-width=".75"/>
        <path d="M382 1.5 H419" stroke="#ffe1b2" stroke-opacity=".88"/>
    """ + rounded_track("#30485a", radius=1)), thin_fill("#76fcff", "#09bccc", radius=1)

    dot_gradient = gradient("dots", [(0, "#ca71fd", 1), (.45, "#8271ff", 1), (1, "#00f5ef", 1)], True)
    # Keep the gradient in panel coordinates, across the whole dot field.
    color = svg(TRACK_SIZE, '<rect width="318" height="32" fill="url(#dots)"/>', dot_gradient)
    color.putalpha(svg(TRACK_SIZE, dots("#ffffff")).getchannel("A"))
    yield "matrix", glass_panel(rounded, navy, "#746df4", dots("#233651", TRACK_X, TRACK_Y)), color

    fold = [(0, "#23483e", .92), (.53, "#10332e", .92), (1, "#082523", .90)]
    yield "fold", glass_panel(rounded, fold, "#7cecca", """
        <path d="M280 1 H459 V63 H217 Z" fill="#071b26" fill-opacity=".65"/>
        <path d="M250 1 H280 L217 63 H190 Z" fill="#50ffb7" fill-opacity=".20"/>
        <path d="M280 1 L217 63" stroke="#9dffdb" stroke-opacity=".87" stroke-width="1.2"/>
    """ + rounded_track("#31544f")), thin_fill("#91ffd0", "#24d894")

    lens = "M2 12 Q20 2 75 2 H385 Q440 2 458 12 Q448 32 458 52 Q440 62 385 62 H75 Q20 62 2 52 Q12 32 2 12 Z"
    yield "lens", glass_panel(lens, navy, "#8ce8ff", """
        <path d="M3 13 Q29 5 75 5 H386 Q432 5 457 13 M3 51 Q29 59 75 59 H386 Q432 59 457 51" fill="none" stroke="#54cafa" stroke-opacity=".36"/>
    """ + rounded_track("#0b2b42", y=5, height=22, radius=11)), lens_fill(TRACK_WIDTH)


def lens_fill(width, cap=False):
    fluid = gradient("fluid", [(0, "#40f4f0", .99), (.3, "#078d9c", .98),
                              (.68, "#047588", .98), (1, "#27f1df", .99)])
    if cap:
        shape = '<path d="M0 5 H2 C8 5 11.5 9.5 11.5 16 S8 27 2 27 H0 Z" fill="url(#fluid)"/><path d="M2 5 C8 5 11.5 9.5 11.5 16 S8 27 2 27" fill="none" stroke="#84fffa" stroke-width=".9"/>'
    else:
        shape = f'<path d="M0 5 H{width} V27 H0 Z" fill="url(#fluid)"/>'
    return svg((width, TRACK_HEIGHT), shape, fluid)


def digits(value, font, liquid=False):
    image = Image.new("RGBA", DIGITS_SIZE)
    draw = ImageDraw.Draw(image)
    text = str(value)
    bounds = font.getbbox(text)
    left = DIGITS_SIZE[0] - bounds[2]
    top = (DIGITS_SIZE[1] - bounds[3] - bounds[1]) // 2
    draw.text((left, top), text, font=font, fill="#f5fafd")
    if not liquid or not value:
        return image
    mask = Image.new("L", DIGITS_SIZE)
    surface = top + bounds[3] - (bounds[3] - bounds[1]) * value / 100
    points = [(x, surface + .8 * sin(x / 4)) for x in range(DIGITS_SIZE[0])]
    ImageDraw.Draw(mask).polygon(points + [(55, 42), (0, 42)], fill=255)
    tint = svg(DIGITS_SIZE, '<rect width="56" height="42" fill="url(#tint)"/>',
               gradient("tint", [(0, "#7efafa", 1), (1, "#00cccd", 1)]))
    ImageDraw.Draw(tint).line(points, fill="#c4ffff", width=1)
    tint.putalpha(ImageChops.multiply(mask, image.getchannel("A")))
    image.alpha_composite(tint)
    return image


def build(output, originals, font_path):
    font = ImageFont.truetype(font_path, 28)
    speaker = Image.open(originals / "volume-speaker.png").convert("RGBA").resize((32, 32), Image.Resampling.LANCZOS)
    length = round(TRACK_WIDTH * .60)

    for style, panel, fill in build_panels():
        folder = output / style
        folder.mkdir(parents=True, exist_ok=True)
        panel.save(folder / "panel.png", optimize=True)
        fill.save(folder / "fill.png", optimize=True)
        preview = panel.copy()
        if style == "lens":
            tip = lens_fill(LENS_TIP_WIDTH, cap=True)
            tip.save(folder / "tip.png", optimize=True)
            preview.alpha_composite(fill.crop((0, 0, length - LENS_TIP_WIDTH, TRACK_HEIGHT)), (TRACK_X, TRACK_Y))
            preview.alpha_composite(tip, (TRACK_X + length - LENS_TIP_WIDTH, TRACK_Y))
        else:
            preview.alpha_composite(fill.crop((0, 0, length, TRACK_HEIGHT)), (TRACK_X, TRACK_Y))
        preview.alpha_composite(speaker, (18, 16))
        preview.alpha_composite(digits(60, font, liquid=style == "liquid"), (390, 11))
        preview.save(folder / "preview.png", optimize=True)

    digit_dir = output / "liquid" / "digits"
    digit_dir.mkdir(exist_ok=True)
    for value in range(101):
        digits(value, font, liquid=True).save(digit_dir / f"{value}.png", optimize=True)

    folder = output / "classic"
    folder.mkdir(exist_ok=True)
    classic = Image.open(originals / "volume-panel.png").convert("RGBA").resize(PANEL_SIZE, Image.Resampling.LANCZOS)
    thumb = Image.open(originals / "volume-thumb.png").convert("RGBA").resize((18, 18), Image.Resampling.LANCZOS)
    fill = Image.open(originals / "volume-gradient.png").convert("RGBA").resize((TRACK_WIDTH, 8), Image.Resampling.LANCZOS)
    ImageDraw.Draw(classic).rectangle((66, 28, 383, 35), fill="#23354c")
    classic.alpha_composite(fill.crop((0, 0, length, 8)), (66, 28))
    classic.alpha_composite(thumb, (66 + length - 9, 23))
    classic.alpha_composite(speaker, (18, 16))
    classic.alpha_composite(digits(60, font), (390, 11))
    classic.save(folder / "preview.png", optimize=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("originals", type=Path, help="Folder with the original volume PNGs")
    parser.add_argument("font", type=Path)
    args = parser.parse_args()
    build(args.output, args.originals, args.font)
