"""SVG → PNG with resvg, which bundles its own renderer and never fetches remote resources."""

from pathlib import Path

import resvg_py

from conv.errors import ConvertError


def convert(src: Path, dst: Path, fmt: str) -> None:
    try:
        # resources_dir lets relative <image href="..."> paths resolve next to the SVG.
        png = resvg_py.svg_to_bytes(svg_path=str(src), resources_dir=str(src.parent))
    except ValueError as e:
        raise ConvertError(f"SVG tidak valid ({e})") from None
    dst.write_bytes(png)
