"""REQ-001: converting a single PNG/JPG/WEBP image."""

import hashlib
import itertools

import pytest
from PIL import Image

from alihrupa.cli import main

FORMATS = {"png": "PNG", "jpg": "JPEG", "webp": "WEBP"}


def make_image(path, fmt="PNG", mode="RGB", size=(20, 10), color=(200, 30, 30)):
    Image.new(mode, size, color).save(path, fmt)
    return path


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(("src", "dst"), list(itertools.permutations(FORMATS, 2)))
def test_converts_every_raster_pair(tmp_path, capsys, src, dst):
    source = make_image(tmp_path / f"foto.{src}", FORMATS[src])
    before = checksum(source)

    assert main([str(source), dst]) == 0

    result = tmp_path / f"foto.{dst}"
    with Image.open(result) as im:
        assert im.format == FORMATS[dst]
        assert im.size == (20, 10)
    assert str(result) in capsys.readouterr().out
    assert checksum(source) == before  # G-003


@pytest.mark.parametrize("target", ["jpeg", "JPG", ".jpg"])
def test_target_format_spellings(tmp_path, target):
    source = make_image(tmp_path / "foto.png")
    assert main([str(source), target]) == 0
    ext = target.lower().lstrip(".")
    with Image.open(tmp_path / f"foto.{ext}") as im:
        assert im.format == "JPEG"


def test_uppercase_source_extension(tmp_path):
    source = make_image(tmp_path / "FOTO.JPEG", "JPEG")
    assert main([str(source), "png"]) == 0
    assert (tmp_path / "FOTO.png").is_file()


@pytest.mark.parametrize("src", ["png", "webp"])
def test_transparency_becomes_white_in_jpg(tmp_path, src):
    source = make_image(tmp_path / f"logo.{src}", FORMATS[src], mode="RGBA", color=(0, 0, 0, 0))
    assert main([str(source), "jpg"]) == 0
    with Image.open(tmp_path / "logo.jpg") as im:
        r, g, b = im.convert("RGB").getpixel((5, 5))
        assert min(r, g, b) > 245


def test_transparency_kept_in_webp(tmp_path):
    source = make_image(tmp_path / "logo.png", mode="RGBA", color=(0, 0, 0, 0))
    assert main([str(source), "webp"]) == 0
    with Image.open(tmp_path / "logo.webp") as im:
        assert im.convert("RGBA").getpixel((5, 5))[3] == 0


def test_exif_rotation_is_applied(tmp_path):
    source = tmp_path / "hp.jpg"
    exif = Image.Exif()
    exif[0x0112] = 6  # orientation: rotate 90° clockwise
    Image.new("RGB", (20, 10)).save(source, "JPEG", exif=exif)
    assert main([str(source), "png"]) == 0
    with Image.open(tmp_path / "hp.png") as im:
        assert im.size == (10, 20)


@pytest.mark.parametrize(("src", "dst"), list(itertools.permutations(FORMATS, 2)))
def test_exif_and_gps_are_not_copied(tmp_path, src, dst):
    """D-023: README promises that metadata such as GPS location does not leak into results."""
    exif = Image.Exif()
    exif[0x010F] = "MerekKamera"
    exif[0x8825] = {1: "S", 2: (6.0, 12.0, 0.0)}
    source = tmp_path / f"foto.{src}"
    Image.new("RGB", (20, 10), "red").save(source, FORMATS[src], exif=exif)
    assert main([str(source), dst]) == 0
    with Image.open(tmp_path / f"foto.{dst}") as im:
        assert not im.getexif()
        assert not im.info.get("exif")


def test_palette_png_with_transparency_to_jpg(tmp_path):
    source = tmp_path / "ikon.png"
    Image.new("RGBA", (8, 8), (0, 0, 0, 0)).convert("P").save(source, "PNG", transparency=0)
    assert main([str(source), "jpg"]) == 0


def test_unsupported_pair(tmp_path, capsys):
    source = make_image(tmp_path / "foto.png")
    assert main([str(source), "mp3"]) == 1
    assert "png → mp3 tidak didukung" in capsys.readouterr().err
    assert sorted(p.name for p in tmp_path.iterdir()) == ["foto.png"]


def test_missing_file(tmp_path, capsys):
    assert main([str(tmp_path / "tidak-ada.png"), "jpg"]) == 1
    err = capsys.readouterr().err
    assert "tidak-ada.png" in err and "tidak ditemukan" in err


def test_not_an_image(tmp_path, capsys):
    source = tmp_path / "palsu.png"
    source.write_bytes(b"ini bukan gambar")
    assert main([str(source), "jpg"]) == 1
    assert "palsu.png" in capsys.readouterr().err
    assert sorted(p.name for p in tmp_path.iterdir()) == ["palsu.png"]  # G-005


def test_truncated_image(tmp_path):
    source = make_image(tmp_path / "rusak.png", size=(200, 200))
    source.write_bytes(source.read_bytes()[:150])
    assert main([str(source), "jpg"]) == 1
    assert sorted(p.name for p in tmp_path.iterdir()) == ["rusak.png"]  # G-005


def test_same_format_does_nothing(tmp_path, capsys):
    source = make_image(tmp_path / "foto.png")
    before = checksum(source)
    assert main([str(source), "png"]) == 1
    assert "sudah dalam format png" in capsys.readouterr().err
    assert checksum(source) == before


def test_existing_destination_not_overwritten(tmp_path, capsys):
    source = make_image(tmp_path / "foto.png")
    existing = tmp_path / "foto.jpg"
    existing.write_bytes(b"punya pengguna")
    assert main([str(source), "jpg"]) == 1
    assert "sudah ada" in capsys.readouterr().err
    assert existing.read_bytes() == b"punya pengguna"  # G-002


def test_no_extension(tmp_path, capsys):
    source = make_image(tmp_path / "foto")
    assert main([str(source), "jpg"]) == 1
    assert "tidak dikenali" in capsys.readouterr().err


def test_help_lists_formats(capsys):
    with pytest.raises(SystemExit) as exit_:
        main(["--help"])
    assert exit_.value.code == 0
    out = capsys.readouterr().out
    assert "png" in out and "jpg" in out and "webp" in out
