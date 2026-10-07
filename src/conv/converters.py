"""Which conversions exist, keyed by (source, target) format."""

from collections.abc import Callable
from pathlib import Path

from conv import images, svg

Converter = Callable[[Path, Path, str], None]

ALIASES = {"jpeg": "jpg"}

CONVERTERS: dict[tuple[str, str], Converter] = {
    **{(s, d): images.convert for s in images.RASTER for d in images.RASTER if s != d},
    ("svg", "png"): svg.convert,
}


def normalize(fmt: str) -> str:
    """'JPEG', '.jpg' and 'jpg' all mean the same format."""
    fmt = fmt.lower().lstrip(".")
    return ALIASES.get(fmt, fmt)


def supported_table() -> str:
    """One line per source format, for --help."""
    targets: dict[str, list[str]] = {}
    for s, d in CONVERTERS:
        targets.setdefault(s, []).append(d)
    return "\n".join(f"  {s:<5} → {', '.join(ds)}" for s, ds in targets.items())
