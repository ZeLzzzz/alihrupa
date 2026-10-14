"""SVG → PNG with resvg, which bundles its own renderer and never fetches remote resources."""

import re
from pathlib import Path

import resvg_py

from alihrupa.errors import ConvertError, plural, warn

# href="https://…" or url(https://…) with any scheme except inline data: and local file:.
REMOTE_REF = re.compile(r"""(?:href\s*=\s*["']|url\(\s*["']?)\s*(?!data:|file:)[a-zA-Z][\w+.-]*:""")


def convert(src: Path, dst: Path, fmt: str) -> None:
    try:
        # resources_dir lets relative <image href="..."> paths resolve next to the SVG.
        png = resvg_py.svg_to_bytes(svg_path=str(src), resources_dir=str(src.parent))
    except ValueError as e:
        raise ConvertError(f"invalid SVG ({e})") from None
    dst.write_bytes(png)
    remote = REMOTE_REF.findall(src.read_text(encoding="utf-8", errors="replace"))
    if remote:
        warn(src, f"did not download {plural(len(remote), 'resource')} referenced by URL; left out")
