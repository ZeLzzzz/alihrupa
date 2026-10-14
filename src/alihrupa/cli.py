"""Convert files between formats locally. Files never leave this machine."""

import argparse
import functools
import os
import sys
import tempfile
from pathlib import Path

from alihrupa import __version__
from alihrupa.converters import CONVERTERS, normalize, supported_table
from alihrupa.documents import PAPERS
from alihrupa.errors import ConvertError

EXISTS = "{dst} already exists, not overwritten (use --force to overwrite it)"


def publish(tmp: Path, dst: Path, force: bool) -> None:
    """Move the finished file into place, never overwriting an existing one unless forced."""
    if force:
        os.replace(tmp, dst)
        return
    try:
        os.link(tmp, dst)  # atomic, and fails if dst already exists
    except FileExistsError:
        raise ConvertError(EXISTS.format(dst=dst)) from None
    except OSError:
        # Filesystems without hard links (e.g. FAT USB drives): check, then rename.
        if dst.exists():
            raise ConvertError(EXISTS.format(dst=dst)) from None
        os.replace(tmp, dst)


def convert_file(src: Path, target: str, target_ext: str, out_dir: Path | None, force: bool, paper: str | None = None) -> Path:
    if not src.exists():
        raise ConvertError("file not found")
    if not src.is_file():
        raise ConvertError("not a file")
    source = normalize(src.suffix)
    if not source:
        raise ConvertError("unknown source format (the file has no extension)")
    if source == target:
        raise ConvertError(f"the file is already in {target} format, nothing changed")
    converter = CONVERTERS.get((source, target))
    if converter is None:
        raise ConvertError(f"converting {source} → {target} is not supported (see alihrupa --help)")
    if target == "pdf":
        converter = functools.partial(converter, paper=paper)

    dst = (out_dir or src.parent) / f"{src.stem}.{target_ext}"
    if dst.exists() and not force:
        raise ConvertError(EXISTS.format(dst=dst))
    # Write next to the destination first, so a failed conversion never leaves a half-written result.
    try:
        fd, name = tempfile.mkstemp(dir=dst.parent, prefix=f".{dst.stem}.", suffix=".alihrupa-tmp")
    except OSError as e:
        raise ConvertError(f"cannot write to {dst.parent} ({e})") from None
    os.close(fd)
    tmp = Path(name)
    try:
        converter(src, tmp, target)
        publish(tmp, dst, force)
    except OSError as e:
        raise ConvertError(f"could not save {dst} ({e})") from None
    finally:
        tmp.unlink(missing_ok=True)
    return dst


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="alihrupa",
        description="Convert files between formats locally. Files never leave this computer.",
        epilog=f"examples:\n  alihrupa photo.png jpg\n  alihrupa *.webp png -o results/\n  alihrupa report.docx pdf -p f4\n\nsupported conversions:\n{supported_table()}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", type=Path, help="files to convert")
    p.add_argument("format", help="target format, e.g. jpg, png, webp")
    p.add_argument("-o", "--output", type=Path, help="folder for the results (default: the folder of each source file)")
    p.add_argument("-f", "--force", action="store_true", help="overwrite results that already exist")
    p.add_argument(
        "-p", "--paper", metavar="SIZE", type=str.lower,
        help=f"paper size of PDF results: {', '.join(PAPERS)} (default: a4, or the DOCX page size; f4 = 215×330 mm)",
    )
    p.add_argument("-V", "--version", action="version", version=f"alihrupa {__version__}")
    args = p.parse_args(argv)

    target_ext = args.format.lower().lstrip(".")
    target = normalize(target_ext)
    if args.paper is not None:
        if args.paper not in PAPERS:
            p.error(f"unknown paper size: {args.paper} (choices: {', '.join(PAPERS)})")
        if target != "pdf":
            p.error("--paper only applies to PDF results")
    if args.output:
        try:
            args.output.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"alihrupa: cannot create folder {args.output} ({e})", file=sys.stderr)
            return 1

    failed: list[tuple[Path, str]] = []
    for src in args.files:
        try:
            dst = convert_file(src, target, target_ext, args.output, args.force, args.paper)
        except ConvertError as e:
            failed.append((src, str(e)))
            print(f"alihrupa: {src}: {e}", file=sys.stderr)
            continue
        print(f"{src} → {dst}")

    if len(args.files) > 1:
        ok = len(args.files) - len(failed)
        print(f"\nDone: {ok} converted, {len(failed)} failed", file=sys.stderr)
        for src, reason in failed:
            print(f"  ✗ {src}: {reason}", file=sys.stderr)
    return 1 if failed else 0


def run() -> None:
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    run()
