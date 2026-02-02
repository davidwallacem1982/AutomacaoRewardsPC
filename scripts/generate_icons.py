from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

assets_dir = Path(__file__).parent.parent / "app" / "assets"
assets_dir.mkdir(parents=True, exist_ok=True)

icons_spec = {
    "start": "play",
    "calibrate": "gear",
    "auto": "loop",
    "remove": "trash",
    "export": "save",
    "import": "download",
    "undo": "undo",
    "stop": "stop",
}

# Define multiple styles (palette overrides)
styles = {
    "default": {},
    "modern": {
        "palette": {
            "start": "#1e90ff",
            "calibrate": "#5a6368",
            "auto": "#10a5b0",
            "remove": "#ffb84d",
            "export": "#4fc3f7",
            "import": "#4caf50",
            "undo": "#6c757d",
            "stop": "#e64a45",
        }
    },
    "soft": {
        "palette": {
            "start": "#8fb9ff",
            "calibrate": "#b0b6bb",
            "auto": "#8fe0e8",
            "remove": "#ffd39b",
            "export": "#bfe9ff",
            "import": "#b9e6b9",
            "undo": "#a7a7a7",
            "stop": "#ff9b9b",
        }
    },
}


def _svg_for_icon(kind: str, color: str) -> str:
    """Return a simple SVG string for the named icon using `color` for the background and white glyph."""
    import math

    if kind == "play":
        glyph = '<polygon points="35,25 35,75 75,50" fill="white"/>'
    elif kind == "gear":
        teeth = "".join(
            f'<circle cx="{50 + 36 * math.cos(t):.2f}" cy="{50 + 36 * math.sin(t):.2f}" r="6" fill="white"/>'
            for t in [i * math.pi / 3 for i in range(6)]
        )
        glyph = '<circle cx="50" cy="50" r="18" fill="white"/>' + teeth
    elif kind == "loop":
        glyph = (
            '<path d="M70,30 A20,20 0 1,0 50,30" fill="none" stroke="white" stroke-width="10" stroke-linecap="round" />'
            '<polygon points="70,30 78,30 70,38" fill="white"/>'
        )
    elif kind == "trash":
        glyph = (
            '<rect x="40" y="40" width="30" height="30" rx="3" fill="white"/>'
            '<rect x="35" y="30" width="40" height="8" rx="2" fill="white"/>'
        )
    elif kind == "save":
        glyph = (
            '<rect x="30" y="30" width="40" height="40" rx="4" fill="white"/>'
            '<rect x="40" y="40" width="20" height="20" fill="#cccccc"/>'
        )
    elif kind == "download":
        glyph = (
            '<rect x="30" y="40" width="40" height="20" rx="3" fill="white"/>'
            '<path d="M50 30 L50 55" stroke="white" stroke-width="6" stroke-linecap="round"/>'
            '<polygon points="42,47 50,55 58,47" fill="white"/>'
        )
    elif kind == "undo":
        glyph = (
            '<path d="M40 55 C35 45, 35 35, 55 35" stroke="white" stroke-width="8" fill="none" stroke-linecap="round" />'
            '<polygon points="40,45 30,50 40,55" fill="white"/>'
        )
    elif kind == "stop":
        glyph = '<rect x="35" y="35" width="30" height="30" rx="4" fill="white"/>'
    else:
        glyph = '<circle cx="50" cy="50" r="20" fill="white"/>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="18" fill="{color}"/>
  {glyph}
</svg>'''
    return svg


def _generate_png_from_svg(svg: str, out_path: Path, size: int):
    try:
        import cairosvg

        cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            write_to=str(out_path),
            output_width=size,
            output_height=size,
        )
        return True
    except Exception:
        return False


def _fallback_text_icon(name: str, color: str, out_path: Path, size: int):
    try:
        try:
            font = ImageFont.truetype("seguiemj.ttf", int(size * 0.6))
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", int(size * 0.6))
            except Exception:
                font = None

        img = Image.new("RGBA", (size, size), color)
        d = ImageDraw.Draw(img)
        char = name[0].upper()
        try:
            if font:
                bbox = d.textbbox((0, 0), char, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
            else:
                w = h = int(size * 0.6)
        except Exception:
            w = h = int(size * 0.6)

        d.text(((size - w) / 2, (size - h) / 2), char, font=font, fill="white")
        img.save(out_path)
        return True
    except Exception:
        return False


for style_name, style_cfg in styles.items():
    palette = style_cfg.get("palette", {})
    for name, kind in icons_spec.items():
        color = palette.get(name, "#2b8cff")
        for size in (28, 48):
            out = assets_dir / f"icon_{name}_{style_name}_{size}.png"
            svg = _svg_for_icon(kind, color)
            ok = _generate_png_from_svg(svg, out, size)
            if not ok:
                _fallback_text_icon(name, color, out, size)
            print("Wrote", out)

print("Icons generated in", assets_dir)
