"""Markdown/TXT/DOCX → DOCX/PDF with bundled pandoc and Typst; no office suite needed (D-020)."""

import html
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

from alihrupa.errors import ConvertError, warn

NO_REMOTE = Path(__file__).with_name("no_remote.lua")
REMOTE_MARKER = "alihrupa-remote-image\t"


def read_text(src: Path) -> str:
    try:
        return src.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise ConvertError("file bukan teks UTF-8 yang valid") from None


def txt_as_html(text: str) -> str:
    """Plain text as HTML paragraphs, so pandoc keeps it literal instead of reading it as Markdown."""
    paragraphs = [p for p in re.split(r"\n\s*\n", text.strip()) if p]
    body = "".join(f"<p>{'<br>'.join(html.escape(line) for line in p.splitlines())}</p>" for p in paragraphs)
    return f"<html><body>{body}</body></html>"


def pandoc(src: Path, args: list[str], cwd: Path | None = None) -> None:
    """Run the bundled pandoc on src; Markdown/TXT are validated as UTF-8 and passed on stdin."""
    import pypandoc

    fmt = src.suffix.lower().lstrip(".")
    if fmt == "docx":
        cmd, stdin = ["-f", "docx", str(src.resolve())], None
    elif fmt == "txt":
        cmd, stdin = ["-f", "html"], txt_as_html(read_text(src))
    else:
        cmd, stdin = ["-f", "markdown"], read_text(src)
    cmd += [f"--resource-path={src.parent.resolve()}", f"--lua-filter={NO_REMOTE}", *args]
    result = subprocess.run(
        [pypandoc.get_pandoc_path(), *cmd], input=stdin, capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        reason = (result.stderr.strip().splitlines() or [f"pandoc exit {result.returncode}"])[-1]
        raise ConvertError(f"gagal membaca dokumen ({reason})")
    remote = [line for line in result.stderr.splitlines() if line.startswith(REMOTE_MARKER)]
    if remote:
        warn(src, f"{len(remote)} gambar dari URL tidak diunduh dan diganti keterangannya")


def has_text(xml: str) -> bool:
    """Whether a WordprocessingML part holds visible text (not just <w:tabs>, empty paragraphs, …)."""
    return any(t.strip() for t in re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", xml))


def lost_docx_parts(src: Path) -> list[str]:
    """Parts of a DOCX that pandoc drops without saying so."""
    try:
        with zipfile.ZipFile(src) as z:
            names = z.namelist()
            body = z.read("word/document.xml").decode("utf-8", "replace")
            extra = {n: z.read(n).decode("utf-8", "replace") for n in names if re.match(r"word/(header|footer)\d*\.xml$", n)}
    except (zipfile.BadZipFile, KeyError):
        raise ConvertError("bukan file DOCX yang valid") from None
    lost = []
    if any(has_text(xml) for name, xml in extra.items() if "header" in name):
        lost.append("header")
    if any(has_text(xml) for name, xml in extra.items() if "footer" in name):
        lost.append("footer")
    if "txbxContent" in body:
        lost.append("text box")
    if re.search(r'<w:cols\b[^>]*w:num="([2-9]|\d\d)"', body):
        lost.append("tata letak kolom")
    return lost


def to_docx(src: Path, dst: Path, fmt: str) -> None:
    pandoc(src, ["-t", "docx", "-o", str(dst.resolve())])


def to_pdf(src: Path, dst: Path, fmt: str) -> None:
    import typst

    lost = lost_docx_parts(src) if src.suffix.lower() == ".docx" else []
    with tempfile.TemporaryDirectory(prefix="alihrupa-") as tmp:
        work = Path(tmp)
        # Relative media paths, so Typst can resolve them inside its root folder.
        pandoc(src, ["-t", "typst", "--standalone", "-V", "papersize=a4", "--extract-media=media", "-o", "doc.typ"], cwd=work)
        try:
            pdf = typst.compile(str(work / "doc.typ"), root=str(work))
        except Exception as e:  # noqa: BLE001 - typst raises its own error types; show the message
            raise ConvertError(f"gagal membuat PDF ({e})") from None
    dst.write_bytes(pdf)
    if lost:
        warn(src, f"tidak ikut ke PDF: {', '.join(lost)} (tata letak disusun ulang, lihat D-020)")
