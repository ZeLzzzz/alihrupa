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

EXISTS = "{dst} sudah ada, tidak ditimpa (pakai --force untuk menimpa)"


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


def convert_file(src: Path, target: str, target_ext: str, out_dir: Path | None, force: bool, paper: str = "a4") -> Path:
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
        raise ConvertError(f"konversi {source} → {target} tidak didukung (lihat alihrupa --help)")
    if target == "pdf":
        converter = functools.partial(converter, paper=paper)

    dst = (out_dir or src.parent) / f"{src.stem}.{target_ext}"
    if dst.exists() and not force:
        raise ConvertError(EXISTS.format(dst=dst))
    # Write next to the destination first, so a failed conversion never leaves a half-written result.
    try:
        fd, name = tempfile.mkstemp(dir=dst.parent, prefix=f".{dst.stem}.", suffix=".alihrupa-tmp")
    except OSError as e:
        raise ConvertError(f"tidak bisa menulis ke {dst.parent} ({e})") from None
    os.close(fd)
    tmp = Path(name)
    try:
        converter(src, tmp, target)
        publish(tmp, dst, force)
    except OSError as e:
        raise ConvertError(f"gagal menyimpan {dst} ({e})") from None
    finally:
        tmp.unlink(missing_ok=True)
    return dst


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="alihrupa",
        description="Konversi file antarformat secara lokal. File tidak pernah keluar dari komputer ini.",
        epilog=f"contoh:\n  alihrupa foto.png jpg\n  alihrupa *.webp png -o hasil/\n  alihrupa laporan.docx pdf -p f4\n\nkonversi yang didukung:\n{supported_table()}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("files", nargs="+", type=Path, help="file yang akan dikonversi")
    p.add_argument("format", help="format tujuan, mis. jpg, png, webp")
    p.add_argument("-o", "--output", type=Path, help="folder hasil (bawaan: folder yang sama dengan file asli)")
    p.add_argument("-f", "--force", action="store_true", help="timpa file hasil yang sudah ada")
    p.add_argument(
        "-p", "--paper", metavar="UKURAN", type=str.lower,
        help=f"ukuran kertas hasil PDF: {', '.join(PAPERS)} (bawaan: a4; f4 = 215×330 mm)",
    )
    p.add_argument("-V", "--version", action="version", version=f"alihrupa {__version__}")
    args = p.parse_args(argv)

    target_ext = args.format.lower().lstrip(".")
    target = normalize(target_ext)
    if args.paper is not None:
        if args.paper not in PAPERS:
            p.error(f"ukuran kertas tidak dikenal: {args.paper} (pilihan: {', '.join(PAPERS)})")
        if target != "pdf":
            p.error("--paper hanya untuk hasil PDF")
    if args.output:
        try:
            args.output.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"alihrupa: tidak bisa membuat folder {args.output} ({e})", file=sys.stderr)
            return 1

    failed: list[tuple[Path, str]] = []
    for src in args.files:
        try:
            dst = convert_file(src, target, target_ext, args.output, args.force, args.paper or "a4")
        except ConvertError as e:
            failed.append((src, str(e)))
            print(f"alihrupa: {src}: {e}", file=sys.stderr)
            continue
        print(f"{src} → {dst}")

    if len(args.files) > 1:
        ok = len(args.files) - len(failed)
        print(f"\nSelesai: {ok} berhasil, {len(failed)} gagal", file=sys.stderr)
        for src, reason in failed:
            print(f"  ✗ {src}: {reason}", file=sys.stderr)
    return 1 if failed else 0


def run() -> None:
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nDibatalkan.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    run()
