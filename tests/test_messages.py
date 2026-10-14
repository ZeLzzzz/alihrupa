"""REQ-013: terminal messages are in English, whatever the system language."""

import ast
import pathlib
import re

import pytest
from PIL import Image

from alihrupa import cli
from alihrupa.cli import main

SRC = pathlib.Path(__file__).parent.parent / "src" / "alihrupa"
INDONESIAN = re.compile(r"\b(tidak|gagal|sudah|bukan|peringatan|berhasil|selesai|dilewati|gambar|ukuran|kertas|hanya|"
                        r"ditimpa|lihat|bawaan|hasil|dibatalkan|pilihan|tata letak|mis)\b", re.I)
SPEC_ID = re.compile(r"\b[DG]-\d{3}\b")


def message_strings():
    """String literals in the source, docstrings left out (comments are not in the syntax tree at all)."""
    for path in SRC.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = {id(node.body[0].value) for node in ast.walk(tree)
                      if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)) and node.body
                      and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                yield path.name, node.value


# AC-4, AC-6: every message is English and explains itself instead of citing D-020 or G-001
def test_no_indonesian_or_spec_ids_in_messages():
    found = [(name, text) for name, text in message_strings() if INDONESIAN.search(text) or SPEC_ID.search(text)]
    assert found == []


# AC-1, AC-3: English whatever the system language says, also when conversions fail
@pytest.mark.parametrize("env", [{"LANG": "id_ID.UTF-8"}, {"LANGUAGE": "id", "LANG": "id_ID.UTF-8"}, {"LANG": "C"}, {}],
                         ids=["id_ID", "LANGUAGE-id", "C", "unset"])
def test_system_language_is_ignored(tmp_path, capsys, monkeypatch, env):
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.delenv(var, raising=False)
    for var, value in env.items():
        monkeypatch.setenv(var, value)
    assert main([str(tmp_path / "hilang.png"), str(tmp_path / "lain.png"), "jpg"]) == 1
    err = capsys.readouterr().err
    assert "hilang.png: file not found" in err and "Done: 0 converted, 2 failed" in err


def test_help_is_english(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--help"])
    assert e.value.code == 0
    out = capsys.readouterr().out
    assert "Convert files between formats locally" in out and "examples:" in out and "supported conversions:" in out
    assert not INDONESIAN.search(out)


# AC-2: invalid arguments, still exit 2
def test_invalid_arguments_in_english(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        main([str(tmp_path / "catatan.md"), "pdf", "-p", "b5"])
    assert e.value.code == 2
    assert "unknown paper size: b5 (choices: a4, a5, a3, letter, legal, f4)" in capsys.readouterr().err


def test_cancel_message(monkeypatch, capsys):
    def interrupted():
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "main", interrupted)
    with pytest.raises(SystemExit) as e:
        cli.run()
    assert e.value.code == 130
    assert "Cancelled." in capsys.readouterr().err


# AC-5: the result line scripts and agents read stays the same
def test_result_line_unchanged(tmp_path, capsys):
    source = tmp_path / "foto.png"
    Image.new("RGB", (4, 4), "red").save(source)
    assert main([str(source), "jpg"]) == 0
    assert capsys.readouterr().out == f"{source} → {tmp_path / 'foto.jpg'}\n"
