"""REQ-009: paper size of PDF results (-p/--paper)."""

import docx
import pymupdf
import pytest

from alihrupa.cli import main
from alihrupa.documents import set_f4
from alihrupa.errors import ConvertError

MM = {"a4": (210, 297), "a5": (148, 210), "a3": (297, 420), "letter": (216, 279), "legal": (216, 356), "f4": (215, 330)}

LONG = "# Laporan\n\n" + "\n\n".join(f"Paragraf {i} dengan isi yang cukup panjang untuk mengisi halaman." for i in range(120))


def page_sizes(path):
    with pymupdf.open(path) as doc:
        return {(round(p.rect.width / 72 * 25.4), round(p.rect.height / 72 * 25.4)) for p in doc}


def blank_pages(path):
    with pymupdf.open(path) as doc:
        return [p.number for p in doc if not p.get_text().strip()]


def page_count(path):
    with pymupdf.open(path) as doc:
        return doc.page_count


@pytest.fixture
def md(tmp_path):
    src = tmp_path / "catatan.md"
    src.write_text(LONG, encoding="utf-8")
    return src


# AC-1: F4 for every page, from DOCX, Markdown and TXT
def test_f4_every_page_from_markdown(md):
    assert main([str(md), "pdf", "-p", "f4"]) == 0
    out = md.with_suffix(".pdf")
    assert page_count(out) > 1
    assert page_sizes(out) == {MM["f4"]}
    assert blank_pages(out) == []


def test_f4_from_docx(tmp_path):
    src = tmp_path / "laporan.docx"
    d = docx.Document()
    d.add_paragraph("Isi laporan.")
    d.save(src)
    assert main([str(src), "pdf", "-p", "f4"]) == 0
    assert page_sizes(tmp_path / "laporan.pdf") == {MM["f4"]}


def test_f4_from_txt(tmp_path):
    src = tmp_path / "teks.txt"
    src.write_text("baris satu\nbaris dua\n", encoding="utf-8")
    assert main([str(src), "pdf", "-p", "f4"]) == 0
    assert page_sizes(tmp_path / "teks.pdf") == {MM["f4"]}


# AC-2: every size, long option, upper case
@pytest.mark.parametrize("size", ["a4", "a5", "a3", "letter", "legal"])
def test_each_size(md, size):
    assert main([str(md), "pdf", "--paper", size]) == 0
    assert page_sizes(md.with_suffix(".pdf")) == {MM[size]}
    assert blank_pages(md.with_suffix(".pdf")) == []


def test_upper_case_size(md):
    assert main([str(md), "pdf", "-p", "F4"]) == 0
    assert page_sizes(md.with_suffix(".pdf")) == {MM["f4"]}


# AC-3: default stays A4
def test_default_is_a4(md):
    assert main([str(md), "pdf"]) == 0
    assert page_sizes(md.with_suffix(".pdf")) == {MM["a4"]}


# AC-4: unknown size → message with the choices, exit 2, nothing written
def test_unknown_size(md, capsys):
    with pytest.raises(SystemExit) as e:
        main([str(md), "pdf", "-p", "b5"])
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "b5" in err
    for size in MM:
        assert size in err
    assert sorted(p.name for p in md.parent.iterdir()) == ["catatan.md"]


# AC-5: --paper with a non-PDF target → exit 2, nothing converted
def test_paper_without_pdf_target(tmp_path, capsys):
    from PIL import Image

    src = tmp_path / "foto.png"
    Image.new("RGB", (4, 4), "red").save(src)
    with pytest.raises(SystemExit) as e:
        main([str(src), "jpg", "-p", "f4"])
    assert e.value.code == 2
    assert "hanya untuk hasil PDF" in capsys.readouterr().err
    assert sorted(p.name for p in tmp_path.iterdir()) == ["foto.png"]


# AC-6: --help lists the option and its sizes
def test_help_lists_sizes(capsys):
    with pytest.raises(SystemExit):
        main(["--help"])
    out = capsys.readouterr().out
    assert "--paper" in out
    for size in MM:
        assert size in out


# F4 relies on pandoc's page setup; a pandoc that changes it must fail loudly, not fall back to A4
def test_f4_unknown_template_fails(tmp_path):
    typ = tmp_path / "doc.typ"
    typ.write_text('#set page(paper: "a4")\nhalo', encoding="utf-8")
    with pytest.raises(ConvertError, match="F4"):
        set_f4(typ)
