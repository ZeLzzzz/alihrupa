# alihrupa

Convert images and documents from the terminal, on your own machine. Nothing is uploaded and nothing is downloaded while converting: every conversion runs offline.

```sh
alihrupa laporan.pdf docx        # -> laporan.docx next to the PDF
alihrupa *.png jpg               # many files at once
```

## Install

Requires [uv](https://docs.astral.sh/uv/) and Linux.

```sh
uv tool install git+https://github.com/ZeLzzzz/alihrupa
```

This installs the `alihrupa` command. No system packages are needed: no office suite, no pandoc, no ImageMagick. Pandoc, Typst, PyMuPDF and the SVG renderer come bundled in Python packages, so the installed tool takes about 570 MB.

If you do not have uv yet:

```sh
sudo pacman -S uv                                   # Arch
curl -LsSf https://astral.sh/uv/install.sh | sh     # Debian/Ubuntu and others
```

Update or remove:

```sh
uv tool upgrade alihrupa
uv tool uninstall alihrupa
```

## Usage

```sh
alihrupa foto.png jpg                  # one file
alihrupa *.webp png                    # several files; a summary is printed at the end
alihrupa catatan.md pdf -o hasil/      # write results to another folder (created if missing)
alihrupa foto.png jpg --force          # overwrite an existing result
alihrupa --help                        # all options and supported conversions
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

Each successful conversion prints `source → result` on stdout. Errors and warnings go to stderr. The exit code is `0` when every file was converted and `1` otherwise, including files skipped because the result already exists or because the file is already in the target format.

## Known limitations

- **PDF → DOCX** works well for text-based PDFs. Complex layouts (columns, intricate tables) are not reproduced exactly.
- **Scanned PDFs** have no text layer, so the DOCX contains images only. OCR is not supported; `alihrupa` warns when this happens.
- **DOCX → PDF** rebuilds the document instead of rendering it like Word does. Text, headings, lists, tables and images are kept, but the result does not look identical. Headers, footers, text boxes and multi-column layouts are lost; `alihrupa` warns about each of them.
- **Images referenced by URL** in Markdown or SVG are not downloaded. In Markdown they are replaced by their description; in SVG they are left out. Either way `alihrupa` warns.
- Markdown and TXT files must be UTF-8.
- Image conversion only changes the format: no resizing or quality settings. Transparent areas become white in JPG. EXIF metadata (including GPS location) is not copied; the photo's rotation is applied to the pixels instead.
- Linux only for now. Windows and macOS may work but are untested.

## Development

```sh
uv sync
uv run pytest
uv run alihrupa --help
```

The spec lives in [`docs/`](docs/): brief, decisions, requirements and guardrails.

## License

[AGPL-3.0-or-later](LICENSE). PDF → DOCX uses [pdf2docx](https://github.com/ArtifexSoftware/pdf2docx), which depends on [PyMuPDF](https://github.com/pymupdf/PyMuPDF) under the AGPL.
