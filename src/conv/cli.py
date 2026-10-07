"""Convert files between formats locally. Files never leave this machine."""

import argparse
import os
import sys
import tempfile
from pathlib import Path

from conv import __version__
from conv.converters import CONVERTERS, normalize, supported_table
from conv.errors import ConvertError


def publish(tmp: Path, dst: Path) -> None:
    """Move the finished file into place without ever overwriting an existing one."""
    try:
        os.link(tmp, dst)  # atomic, and fails if dst already exists
    except FileExistsError:
        raise ConvertError(f"{dst} sudah ada, tidak ditimpa") from None
    except OSError:
        # Filesystems without hard links (e.g. FAT USB drives): check, then rename.
        if dst.exists():
            raise ConvertError(f"{dst} sudah ada, tidak ditimpa") from None
        os.replace(tmp, dst)


def convert_file(src: Path, target: str, target_ext: str) -> Path:
    if not src.exists():
        raise ConvertError("file tidak ditemukan")
    if not src.is_file():
        raise ConvertError("bukan file")
    source = normalize(src.suffix)
    if not source:
        raise ConvertError("format sumber tidak dikenali (file tidak punya ekstensi)")
    if source == target:
        raise ConvertError(f"file sudah dalam format {target}, tidak ada yang diubah")
    converter = CONVERTERS.get((source, target))
    if converter is None:
        raise ConvertError(f"konversi {source} → {target} tidak didukung (lihat conv --help)")

    dst = src.with_suffix(f".{target_ext}")
    if dst.exists():
        raise ConvertError(f"{dst} sudah ada, tidak ditimpa")
    # Write next to the destination first, so a failed conversion never leaves a half-written result.
    fd, name = tempfile.mkstemp(dir=dst.parent, prefix=f".{dst.stem}.", suffix=".conv-tmp")
    os.close(fd)
    tmp = Path(name)
    try:
        converter(src, tmp, target)
        publish(tmp, dst)
    finally:
        tmp.unlink(missing_ok=True)
    return dst


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="conv",
        description="Konversi file antarformat secara lokal. File tidak pernah keluar dari komputer ini.",
        epilog=f"contoh:\n  conv foto.png jpg\n  conv *.webp png\n\nkonversi yang didukung:\n{supported_table()}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", type=Path, help="file yang akan dikonversi")
    p.add_argument("format", help="format tujuan, mis. jpg, png, webp")
    p.add_argument("-V", "--version", action="version", version=f"conv {__version__}")
    args = p.parse_args(argv)

    target_ext = args.format.lower().lstrip(".")
    target = normalize(target_ext)
    failed = 0
    for src in args.files:
        try:
            dst = convert_file(src, target, target_ext)
        except ConvertError as e:
            failed += 1
            print(f"conv: {src}: {e}", file=sys.stderr)
            continue
        print(f"{src} → {dst}")
    return 1 if failed else 0


def run() -> None:
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nDibatalkan.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    run()
