# conv

Convert images and documents from the terminal, on your own machine. Nothing is uploaded and nothing is downloaded while converting: every conversion runs offline.

```sh
conv laporan.pdf docx        # -> laporan.docx next to the PDF
conv *.png jpg               # many files at once
```

## Install

Requires [uv](https://docs.astral.sh/uv/) and Linux.

```sh
uv tool install git+https://github.com/ZeLzzzz/conv
```

This installs the `conv` command. No system packages are needed: no office suite, no pandoc, no ImageMagick. Pandoc, Typst, PyMuPDF and the SVG renderer come bundled in Python packages, so the installed tool takes about 570 MB.

If you do not have uv yet:

```sh
sudo pacman -S uv                                   # Arch
curl -LsSf https://astral.sh/uv/install.sh | sh     # Debian/Ubuntu and others
```

Update or remove:

```sh
uv tool upgrade conv
uv tool uninstall conv
```

## Usage

```sh
conv foto.png jpg                  # one file
conv *.webp png                    # several files; a summary is printed at the end
conv catatan.md pdf -o hasil/      # write results to another folder (created if missing)
conv foto.png jpg --force          # overwrite an existing result
conv --help                        # all options and supported conversions
```

The last argument is the target format. Results go next to the original file, named after it. Existing files are never overwritten unless you pass `--force`, and the original file is never changed.

| From | To |
|---|---|
| PNG, JPG, WEBP | each other |
| SVG | PNG |
| PDF | DOCX |
| DOCX | PDF |
| Markdown, TXT | DOCX, PDF |

The CLI messages are in Indonesian, because that is what the author uses.

### Exit codes and output

Each successful conversion prints `source → result` on stdout. Errors and warnings go to stderr. The exit code is `0` when every file was converted and `1` otherwise, including files skipped because the result already exists.

## Known limitations

- **PDF → DOCX** works well for text-based PDFs. Complex layouts (columns, intricate tables) are not reproduced exactly.
- **Scanned PDFs** have no text layer, so the DOCX contains images only. OCR is not supported; `conv` warns when this happens.
- **DOCX → PDF** rebuilds the document instead of rendering it like Word does. Text, headings, lists, tables and images are kept, but the result does not look identical. Headers, footers, text boxes and multi-column layouts are lost; `conv` warns about each of them.
- **Images referenced by URL** in Markdown or SVG are not downloaded. They are replaced by their description, with a warning.
- Markdown and TXT files must be UTF-8.
- Image conversion only changes the format: no resizing or quality settings. Transparent areas become white in JPG. EXIF metadata (including GPS location) is not copied; the photo's rotation is applied to the pixels instead.
- Linux only for now. Windows and macOS may work but are untested.

## Development

```sh
uv sync
uv run pytest
uv run conv --help
```

The spec lives in [`docs/`](docs/): brief, decisions, requirements and guardrails.

## License

[AGPL-3.0-or-later](LICENSE). PDF → DOCX uses [pdf2docx](https://github.com/ArtifexSoftware/pdf2docx), which depends on [PyMuPDF](https://github.com/pymupdf/PyMuPDF) under the AGPL.
