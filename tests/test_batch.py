"""REQ-002: output location, overwriting and batches."""

from PIL import Image

from conv.cli import main


def make_png(path):
    Image.new("RGB", (8, 8), "red").save(path, "PNG")
    return path


def test_batch_converts_all_and_summarises(tmp_path, capsys):
    files = [make_png(tmp_path / f"{n}.png") for n in "abc"]
    assert main([*map(str, files), "jpg"]) == 0
    assert all((tmp_path / f"{n}.jpg").is_file() for n in "abc")
    assert "3 berhasil, 0 gagal" in capsys.readouterr().err


def test_single_file_has_no_summary(tmp_path, capsys):
    assert main([str(make_png(tmp_path / "a.png")), "jpg"]) == 0
    assert "Selesai" not in capsys.readouterr().err


def test_output_folder_is_created(tmp_path):
    source = make_png(tmp_path / "a.png")
    out = tmp_path / "hasil" / "baru"
    assert main([str(source), "webp", "-o", str(out)]) == 0
    assert (out / "a.webp").is_file()
    assert not (tmp_path / "a.webp").exists()


def test_output_folder_that_is_a_file(tmp_path, capsys):
    source = make_png(tmp_path / "a.png")
    blocker = tmp_path / "hasil"
    blocker.write_text("x")
    assert main([str(source), "jpg", "-o", str(blocker)]) == 1
    assert "tidak bisa membuat folder" in capsys.readouterr().err


def test_existing_file_skipped_and_counted_as_failed(tmp_path, capsys):
    a, b = make_png(tmp_path / "a.png"), make_png(tmp_path / "b.png")
    (tmp_path / "a.jpg").write_bytes(b"lama")
    assert main([str(a), str(b), "jpg"]) == 1
    err = capsys.readouterr().err
    assert "--force" in err
    assert "1 berhasil, 1 gagal" in err
    assert (tmp_path / "a.jpg").read_bytes() == b"lama"
    assert (tmp_path / "b.jpg").is_file()


def test_force_overwrites(tmp_path):
    source = make_png(tmp_path / "a.png")
    (tmp_path / "a.jpg").write_bytes(b"lama")
    assert main([str(source), "jpg", "--force"]) == 0
    with Image.open(tmp_path / "a.jpg") as im:
        assert im.format == "JPEG"


def test_failure_in_the_middle_does_not_stop_batch(tmp_path, capsys):
    a = make_png(tmp_path / "a.png")
    broken = tmp_path / "rusak.png"
    broken.write_bytes(b"bukan gambar")
    c = make_png(tmp_path / "c.png")
    assert main([str(a), str(broken), str(c), "jpg"]) == 1
    err = capsys.readouterr().err
    assert "2 berhasil, 1 gagal" in err
    assert "✗ " + str(broken) in err
    assert (tmp_path / "a.jpg").is_file() and (tmp_path / "c.jpg").is_file()
    assert not (tmp_path / "rusak.jpg").exists()


def test_same_destination_name_not_overwritten(tmp_path, capsys):
    png = make_png(tmp_path / "a.png")
    webp = tmp_path / "a.webp"
    Image.new("RGB", (4, 4), "blue").save(webp, "WEBP")
    assert main([str(png), str(webp), "jpg"]) == 1
    with Image.open(tmp_path / "a.jpg") as im:
        assert im.size == (8, 8)  # still the PNG's result
    assert "1 berhasil, 1 gagal" in capsys.readouterr().err


def test_no_temp_files_left_behind(tmp_path):
    a = make_png(tmp_path / "a.png")
    broken = tmp_path / "b.png"
    broken.write_bytes(b"x")
    main([str(a), str(broken), "jpg", "-o", str(tmp_path / "out")])
    assert [p.name for p in (tmp_path / "out").iterdir()] == ["a.jpg"]
