#!/usr/bin/env python3
"""Generate the PS5 512x512 icon from the existing Vynx logo.

The source artwork is only resampled and centered; no AI generation, tracing,
or stylistic changes are applied.
"""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "icon-source.png"
OUTPUT = ROOT / "assets" / "icon0.png"
SIZE = 512
PADDING = 28


def main():
    with Image.open(SOURCE) as source:
        image = source.convert("RGBA")
        image.thumbnail((SIZE - PADDING * 2, SIZE - PADDING * 2), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (SIZE, SIZE), (7, 5, 13, 255))
        x = (SIZE - image.width) // 2
        y = (SIZE - image.height) // 2
        canvas.alpha_composite(image, (x, y))
        canvas.convert("RGB").save(OUTPUT, "PNG", optimize=True)

    print(f"Generated {OUTPUT.relative_to(ROOT)} ({SIZE}x{SIZE}, PNG)")


if __name__ == "__main__":
    main()
