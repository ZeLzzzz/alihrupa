"""The basic layout of a DOCX, so DOCX → PDF looks like the original (D-029, D-030).

Only what the DOCX itself records is read: page size and margins of the last section, and the font, size,
line spacing, paragraph spacing and alignment of the dominant body text. Anything missing or nonsensical
stays None, which means "keep alihrupa's previous default".
"""

import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
OFF = {"0", "false", "off"}

# Free fonts with the same metrics as common Microsoft fonts, so lines break in the same places (D-029).
SUBSTITUTES = {
    "times new roman": ["Liberation Serif", "Tinos"],
    "arial": ["Liberation Sans", "Arimo"],
    "calibri": ["Carlito"],
    "cambria": ["Caladea"],
    "courier new": ["Liberation Mono", "Cousine"],
}

PAGE_FIELD = re.compile(r'(?:w:instr="\s*PAGE\b|<w:instrText[^>]*>\s*PAGE\b)')


@dataclass
class Layout:
    width: float | None = None  # page, mm
    height: float | None = None
    margins: tuple[float, float, float, float] | None = None  # top, right, bottom, left, mm
    font: str | None = None
    size: float | None = None  # pt
    line: tuple[str, float] = ("auto", 1.0)  # ("auto", multiple) or ("exact" / "atLeast", pt)
    before: float = 0.0  # pt
    after: float = 0.0
    justify: bool = False  # Word's default alignment is left
    hyphenate: bool = False
    page_numbers: bool = False


def twips(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def mm(tw: int) -> float:
    return tw / 1440 * 25.4


def page_number_only(xml: str) -> bool:
    """A footer whose only text is a page number field (alihrupa renders that one itself)."""
    if not PAGE_FIELD.search(xml):
        return False
    text = "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", xml))
    return text.strip().isdigit() or not text.strip()


class Styles:
    """Paragraph style chains from styles.xml, ending in the document defaults."""

    def __init__(self, root: ET.Element | None):
        self.by_id: dict[str, ET.Element] = {}
        self.default: str | None = None
        self.ppr = self.rpr = None
        if root is None:
            return
        self.ppr = root.find(f"{W}docDefaults/{W}pPrDefault/{W}pPr")
        self.rpr = root.find(f"{W}docDefaults/{W}rPrDefault/{W}rPr")
        for style in root.iter(f"{W}style"):
            sid = style.get(f"{W}styleId")
            self.by_id[sid] = style
            if style.get(f"{W}type") == "paragraph" and style.get(f"{W}default") in ("1", "true", "on"):
                self.default = sid

    def chain(self, sid: str | None) -> list[ET.Element]:
        styles, seen = [], set()
        sid = sid or self.default
        while sid in self.by_id and sid not in seen:
            seen.add(sid)
            styles.append(self.by_id[sid])
            based = self.by_id[sid].find(f"{W}basedOn")
            sid = based.get(f"{W}val") if based is not None else None
        return styles


def find(levels: list[ET.Element | None], tag: str, attr: str) -> str | None:
    """The first value of tag/@attr from the most specific level that sets it."""
    for el in levels:
        child = el.find(f"{W}{tag}") if el is not None else None
        if child is not None and child.get(f"{W}{attr}") is not None:
            return child.get(f"{W}{attr}")
    return None


def is_heading(styles: list[ET.Element], ppr: ET.Element | None) -> bool:
    if any(el is not None and el.find(f"{W}outlineLvl") is not None for el in [ppr, *(s.find(f"{W}pPr") for s in styles)]):
        return True
    names = [(s.get(f"{W}styleId") or "").lower() for s in styles]
    names += [(s.find(f"{W}name").get(f"{W}val") or "").lower() for s in styles if s.find(f"{W}name") is not None]
    return any(n.startswith(("heading", "title", "subtitle")) for n in names)


def theme_fonts(root: ET.Element | None) -> dict[str, str]:
    fonts = {}
    if root is not None:
        for kind in ("major", "minor"):
            latin = root.find(f".//{A}{kind}Font/{A}latin")
            if latin is not None and latin.get("typeface"):
                fonts[kind] = latin.get("typeface")
    return fonts


def run_font(levels: list[ET.Element | None], theme: dict[str, str]) -> str | None:
    for el in levels:
        fonts = el.find(f"{W}rFonts") if el is not None else None
        if fonts is None:
            continue
        if fonts.get(f"{W}ascii"):
            return fonts.get(f"{W}ascii")
        kind = (fonts.get(f"{W}asciiTheme") or "")[:5]
        if kind in theme:
            return theme[kind]
    return None


def dominant(counter: Counter):
    return counter.most_common(1)[0][0] if counter else None


def read_section(body: ET.Element, layout: Layout) -> None:
    sect = body.find(f"{W}sectPr")
    if sect is None:
        return
    size = sect.find(f"{W}pgSz")
    if size is not None:
        w, h = twips(size.get(f"{W}w")), twips(size.get(f"{W}h"))
        if w and h and all(50 <= mm(v) <= 2000 for v in (w, h)):
            layout.width, layout.height = mm(w), mm(h)
    margin = sect.find(f"{W}pgMar")
    if margin is not None:
        values = [twips(margin.get(f"{W}{side}")) for side in ("top", "right", "bottom", "left")]
        width, height = layout.width or 210, layout.height or 297
        if all(v is not None and v >= 0 for v in values):
            top, right, bottom, left = (mm(v) for v in values)
            if left + right < width and top + bottom < height:
                layout.margins = (top, right, bottom, left)


def read_body_text(body: ET.Element, styles: Styles, theme: dict[str, str], layout: Layout) -> None:
    fonts, sizes, lines, gaps, aligns = Counter(), Counter(), Counter(), Counter(), Counter()
    for p in body.iter(f"{W}p"):
        text = "".join(t.text or "" for t in p.iter(f"{W}t"))
        if not text.strip():
            continue
        ppr = p.find(f"{W}pPr")
        style = ppr.find(f"{W}pStyle") if ppr is not None else None
        chain = styles.chain(style.get(f"{W}val") if style is not None else None)
        if is_heading(chain, ppr):
            continue
        plevels = [ppr, *(s.find(f"{W}pPr") for s in chain), styles.ppr]
        weight = len(text)

        aligns[find(plevels, "jc", "val") in ("both", "distribute")] += weight
        rule = find(plevels, "spacing", "lineRule") or "auto"
        line = twips(find(plevels, "spacing", "line"))
        if line and line > 0:
            lines[("auto", line / 240) if rule == "auto" else (rule, line / 20)] += weight
        else:
            lines[("auto", 1.0)] += weight
        before = twips(find(plevels, "spacing", "before")) or 0
        after = twips(find(plevels, "spacing", "after")) or 0
        gaps[(max(before, 0) / 20, max(after, 0) / 20)] += weight

        rlevels_tail = [*(s.find(f"{W}rPr") for s in chain), styles.rpr]
        for r in p.iter(f"{W}r"):
            rtext = "".join(t.text or "" for t in r.iter(f"{W}t"))
            if not rtext.strip():
                continue
            rlevels = [r.find(f"{W}rPr"), *rlevels_tail]
            font = run_font(rlevels, theme)
            if font:
                fonts[font] += len(rtext)
            size = twips(find(rlevels, "sz", "val"))
            if size and 2 <= size <= 3276:
                sizes[size / 2] += len(rtext)

    layout.font = dominant(fonts)
    layout.size = dominant(sizes)
    layout.line = dominant(lines) or layout.line
    layout.before, layout.after = dominant(gaps) or (0.0, 0.0)
    layout.justify = bool(dominant(aligns))


def read_layout(z: zipfile.ZipFile) -> Layout:
    """The layout of an opened DOCX. Unreadable parts are skipped, never fatal."""
    layout = Layout()

    def xml(name: str) -> ET.Element | None:
        try:
            return ET.fromstring(z.read(name))
        except (KeyError, ET.ParseError):
            return None

    doc = xml("word/document.xml")
    body = doc.find(f"{W}body") if doc is not None else None
    if body is None:
        return layout
    read_section(body, layout)
    read_body_text(body, Styles(xml("word/styles.xml")), theme_fonts(xml("word/theme/theme1.xml")), layout)

    settings = xml("word/settings.xml")
    hyphen = settings.find(f"{W}autoHyphenation") if settings is not None else None
    layout.hyphenate = hyphen is not None and hyphen.get(f"{W}val", "true").lower() not in OFF
    for name in z.namelist():
        if re.match(r"word/footer\d*\.xml$", name) and PAGE_FIELD.search(z.read(name).decode("utf-8", "replace")):
            layout.page_numbers = True
    return layout
