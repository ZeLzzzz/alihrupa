"""Markdown/TXT/DOCX → DOCX/PDF with bundled pandoc and Typst; no office suite needed (D-020)."""

import functools
import html
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

from alihrupa.docx_layout import SUBSTITUTES, Layout, page_number_only, read_layout
from alihrupa.errors import ConvertError, warn

NO_REMOTE = Path(__file__).with_name("no_remote.lua")
REMOTE_MARKER = "alihrupa-remote-image\t"

# Typst paper names per paper size (D-027). F4 has no Typst preset: it starts as A4 and gets its real size in to_pdf.
PAPERS = {"a4": "a4", "a5": "a5", "a3": "a3", "letter": "us-letter", "legal": "us-legal", "f4": "a4"}
F4_PAGE = "width: 215mm, height: 330mm,"
# The same sizes in mm, for DOCX → PDF where alihrupa sets the page itself.
PAPER_MM = {"a4": (210, 297), "a5": (148, 210), "a3": (297, 420), "letter": (215.9, 279.4), "legal": (215.9, 355.6), "f4": (215, 330)}
# What pandoc's template used for DOCX before D-029; still the fallback when the DOCX does not say.
DEFAULT_MARGIN = 31.75  # mm (1.25 in)
DEFAULT_SIZE = 11  # pt
WORD_LINE = 1.15  # Word's single line height as a multiple of the font size (Times New Roman and similar)
DESCENT = 0.2  # em below the baseline in each line box


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
    if any(has_text(xml) and not page_number_only(xml) for name, xml in extra.items() if "footer" in name):
        lost.append("footer")
    if "txbxContent" in body:
        lost.append("text box")
    if re.search(r'<w:cols\b[^>]*w:num="([2-9]|\d\d)"', body):
        lost.append("tata letak kolom")
    return lost


def to_docx(src: Path, dst: Path, fmt: str) -> None:
    pandoc(src, ["-t", "docx", "-o", str(dst.resolve())])


def set_f4(typ: Path) -> None:
    """Swap the paper preset in pandoc's page setup for F4 dimensions.

    A `#set page` inside the body would not work: pandoc's template always emits a title block first,
    so Typst would start a new page and leave an empty A4 page in front.
    """
    source = typ.read_text(encoding="utf-8")
    patched = source.replace("paper: paper,", F4_PAGE, 1)
    if patched == source:
        raise ConvertError("ukuran kertas F4 tidak bisa diatur dengan versi pandoc ini")
    typ.write_text(patched, encoding="utf-8")


@functools.cache
def installed_fonts() -> dict[str, str]:
    import typst

    return {f.lower(): f for f in typst.Fonts().families()}


def pick_font(name: str) -> str | None:
    """The DOCX font if installed, else a metric-compatible substitute (D-029), else None."""
    fonts = installed_fonts()
    for candidate in [name, *SUBSTITUTES.get(name.lower(), [])]:
        if candidate.lower() in fonts:
            return fonts[candidate.lower()]
    return None


def typst_str(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def docx_conf(layout: Layout, paper: str | None, font: str | None) -> str:
    """A replacement for the `conf` function of pandoc's Typst template, laid out like the DOCX.

    Pandoc's own `conf` always puts a title block before the text (pushing it about 1 cm down) and
    cannot take a page size that has no Typst preset.
    """
    width, height = PAPER_MM[paper] if paper else (layout.width or 210, layout.height or 297)
    top, right, bottom, left = layout.margins or (DEFAULT_MARGIN,) * 4
    size = layout.size or DEFAULT_SIZE
    # Like Word, every line box is one full line high, with the extra space above the text.
    rule, value = layout.line
    if rule == "auto":
        top_edge = f"{value * WORD_LINE - DESCENT:.4f}em"
    else:
        box = value if rule == "exact" else max(value, WORD_LINE * size)
        top_edge = f"{box - DESCENT * size:.3f}pt"
    font_rule = f"  set text(font: ({typst_str(font)},))\n" if font else ""
    return f"""#let conf(..args) = {{
  let a = args.named()
  set page(width: {width:.2f}mm, height: {height:.2f}mm,
    margin: (top: {top:.2f}mm, right: {right:.2f}mm, bottom: {bottom:.2f}mm, left: {left:.2f}mm),
    numbering: {'"1"' if layout.page_numbers else "none"})
  set text(lang: a.at("lang", default: "en"), size: {size}pt, top-edge: {top_edge}, bottom-edge: -{DESCENT}em,
    hyphenate: {"true" if layout.hyphenate else "false"}, overhang: false)
{font_rule}  set par(leading: 0pt, spacing: {layout.before + layout.after:.2f}pt, justify: {"true" if layout.justify else "false"})
  // Title paragraphs of the DOCX (Title/Subtitle styles), which pandoc moves out of the body
  if a.at("title", default: none) != none {{ align(center, text(weight: "bold", size: 1.5em, a.title)) }}
  if a.at("subtitle", default: none) != none {{ align(center, text(weight: "bold", size: 1.25em, a.subtitle)) }}
  let authors = a.at("authors", default: ())
  if authors != none and authors.len() > 0 {{ align(center, authors.map(x => x.name).join(", ")) }}
  if a.at("date", default: none) != none {{ align(center, a.date) }}
  if a.at("abstract", default: none) != none {{
    block(inset: 2em)[#text(weight: "semibold")[#a.at("abstract-title", default: [Abstract])] #h(1em) #a.abstract]
  }}
  args.pos().first()
}}
"""


def check_conf(typ: Path) -> None:
    """Make sure pandoc's template still lays out the body through `conf`, which docx_conf replaces."""
    if "#show: doc => conf(" not in typ.read_text(encoding="utf-8"):
        raise ConvertError("tata letak DOCX tidak bisa diterapkan dengan versi pandoc ini")


def to_pdf(src: Path, dst: Path, fmt: str, paper: str | None = None) -> None:
    import typst

    is_docx = src.suffix.lower() == ".docx"
    lost = lost_docx_parts(src) if is_docx else []
    with tempfile.TemporaryDirectory(prefix="alihrupa-") as tmp:
        work = Path(tmp)
        if is_docx:
            with zipfile.ZipFile(src) as z:
                layout = read_layout(z)
            font = pick_font(layout.font) if layout.font else None
            if layout.font and not font:
                warn(src, f"font {layout.font} tidak terpasang (begitu juga penggantinya), memakai font bawaan")
            (work / "conf.typ").write_text(docx_conf(layout, paper, font), encoding="utf-8")
            args = ["-H", "conf.typ"]
        else:
            args = ["-V", f"papersize={PAPERS[paper or 'a4']}"]
        # Relative media paths, so Typst can resolve them inside its root folder.
        pandoc(src, ["-t", "typst", "--standalone", *args, "--extract-media=media", "-o", "doc.typ"], cwd=work)
        if is_docx:
            check_conf(work / "doc.typ")
        elif paper == "f4":
            set_f4(work / "doc.typ")
        try:
            pdf = typst.compile(str(work / "doc.typ"), root=str(work))
        except Exception as e:  # noqa: BLE001 - typst raises its own error types; show the message
            raise ConvertError(f"gagal membuat PDF ({e})") from None
    dst.write_bytes(pdf)
    if lost:
        warn(src, f"tidak ikut ke PDF: {', '.join(lost)} (tata letak disusun ulang, lihat D-020)")
