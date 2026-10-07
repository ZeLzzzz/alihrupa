"""PDF → DOCX with pdf2docx (PyMuPDF, AGPL-3.0; see D-017)."""

import io
import logging
from pathlib import Path

from alihrupa.errors import ConvertError, warn


class _ErrorCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.ERROR)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


def _load():
    """Import pdf2docx lazily (it is slow) and stop it from writing to stdout/stderr."""
    import pymupdf

    pymupdf.set_messages(stream=io.StringIO())  # pdf2docx's `import fitz` prints a deprecation notice to stdout
    pymupdf.TOOLS.mupdf_display_errors(False)
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    from pdf2docx import Converter  # calls logging.basicConfig(level=INFO) on import

    for h in root.handlers:
        if h not in handlers:
            root.removeHandler(h)
    root.setLevel(level)
    return pymupdf, Converter


def convert(src: Path, dst: Path, fmt: str) -> None:
    pymupdf, Converter = _load()
    try:
        with pymupdf.open(src) as doc:
            if doc.needs_pass:
                raise ConvertError("PDF terenkripsi/berpassword, tidak bisa dibuka")
            scanned = not any(page.get_text().strip() for page in doc)
    except (pymupdf.FileDataError, RuntimeError) as e:
        raise ConvertError(f"PDF rusak atau tidak bisa dibaca ({e})") from None

    # pdf2docx skips pages it cannot parse and only logs it; collect those so nothing is dropped silently.
    collector = _ErrorCollector()
    logging.getLogger().addHandler(collector)
    try:
        converter = Converter(str(src))
        try:
            converter.convert(str(dst))
        finally:
            converter.close()
    except Exception as e:  # noqa: BLE001 - any library failure becomes a per-file error
        raise ConvertError(f"gagal mengonversi PDF ({e})") from None
    finally:
        logging.getLogger().removeHandler(collector)

    if scanned:
        warn(src, "PDF tidak punya lapisan teks (hasil scan?); isi DOCX berupa gambar karena OCR belum didukung")
    if collector.messages:
        warn(src, f"sebagian isi gagal dikonversi dan dilewati: {'; '.join(collector.messages)}")
