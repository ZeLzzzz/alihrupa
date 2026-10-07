"""REQ-003: SVG → PNG."""

import pytest
from PIL import Image

from conv.cli import main

LOGO = """<svg xmlns="http://www.w3.org/2000/svg" width="40" height="30">
  <rect width="20" height="30" fill="red"/>
</svg>"""


def test_svg_to_png_keeps_size_and_transparency(tmp_path):
    source = tmp_path / "logo.svg"
    source.write_text(LOGO)
    assert main([str(source), "png"]) == 0
    with Image.open(tmp_path / "logo.png") as im:
        assert im.size == (40, 30)
        im = im.convert("RGBA")
        assert im.getpixel((5, 5))[:3] == (255, 0, 0)
        assert im.getpixel((30, 5))[3] == 0  # outside the rect stays transparent


def test_namespace_urls_are_not_reported_as_remote(tmp_path, capsys):
    source = tmp_path / "logo.svg"
    source.write_text(LOGO.replace("<svg ", '<svg xmlns:xlink="http://www.w3.org/1999/xlink" '))
    assert main([str(source), "png"]) == 0
    assert "peringatan" not in capsys.readouterr().err


@pytest.mark.parametrize("content", ["<svg", "bukan svg", ""])
def test_invalid_svg(tmp_path, capsys, content):
    source = tmp_path / "rusak.svg"
    source.write_text(content)
    assert main([str(source), "png"]) == 1
    assert "SVG tidak valid" in capsys.readouterr().err
    assert sorted(p.name for p in tmp_path.iterdir()) == ["rusak.svg"]


def test_remote_images_are_not_downloaded(tmp_path, capsys, http_server):
    base, requests = http_server
    source = tmp_path / "remote.svg"
    source.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        f'<rect width="10" height="10" fill="blue"/><image href="{base}/x.png" width="5" height="5"/></svg>'
    )
    assert main([str(source), "png"]) == 0  # G-001: renders without the remote image
    assert requests == []
    assert "1 sumber dari URL tidak diunduh" in capsys.readouterr().err


def test_relative_local_image_is_included(tmp_path):
    Image.new("RGB", (4, 4), (0, 255, 0)).save(tmp_path / "hijau.png")
    source = tmp_path / "pakai.svg"
    source.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4">'
        '<image href="hijau.png" width="4" height="4"/></svg>'
    )
    out = tmp_path / "out"
    assert main([str(source), "png", "-o", str(out)]) == 0
    with Image.open(out / "pakai.png") as im:
        assert im.convert("RGB").getpixel((2, 2)) == (0, 255, 0)


@pytest.mark.parametrize(("name", "target"), [("logo.svg", "jpg"), ("logo.svg", "webp"), ("foto.png", "svg")])
def test_other_svg_directions_unsupported(tmp_path, capsys, name, target):
    source = tmp_path / name
    source.write_text(LOGO)
    assert main([str(source), target]) == 1
    assert "tidak didukung" in capsys.readouterr().err
