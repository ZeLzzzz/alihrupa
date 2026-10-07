"""Which conversions exist, keyed by (source, target) format."""

from collections.abc import Callable
from pathlib import Path

from conv import documents, images, pdf, svg

Converter = Callable[[Path, Path, str], None]

ALIASES = {"jpeg": "jpg", "markdown": "md"}

CONVERTERS: dict[tuple[str, str], Converter] = {
    **{(s, d): images.convert for s in images.RASTER for d in images.RASTER if s != d},
    ("svg", "png"): svg.convert,
    ("pdf", "docx"): pdf.convert,
    ("docx", "pdf"): documents.to_pdf,
    ("md", "docx"): documents.to_docx,
    ("txt", "docx"): documents.to_docx,
    ("md", "pdf"): documents.to_pdf,
    ("txt", "pdf"): documents.to_pdf,
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
