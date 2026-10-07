"""Raster image conversion (PNG, JPG, WEBP) with Pillow."""

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from conv.errors import ConvertError

RASTER = ("png", "jpg", "webp")

PIL_FORMAT = {"png": "PNG", "jpg": "JPEG", "webp": "WEBP"}
SAVE_OPTIONS = {"png": {}, "jpg": {"quality": 90}, "webp": {"quality": 90}}
# Modes each format stores as-is; anything else is converted first.
NATIVE_MODES = {
    "png": {"1", "L", "LA", "I", "I;16", "P", "RGB", "RGBA"},
    "jpg": {"L", "RGB", "CMYK"},
    "webp": {"RGB", "RGBA"},
}


def prepare(im: Image.Image, fmt: str) -> Image.Image:
    """Convert to a mode the target format can store, keeping transparency where possible."""
    if fmt == "jpg" and im.has_transparency_data:
        # JPG has no alpha channel: flatten onto white instead of letting it turn black.
        rgba = im.convert("RGBA")
        flat = Image.new("RGB", im.size, "white")
        flat.paste(rgba, mask=rgba.getchannel("A"))
        return flat
    if im.mode in NATIVE_MODES[fmt]:
        return im
    return im.convert("RGBA" if im.has_transparency_data else "RGB")


def convert(src: Path, dst: Path, fmt: str) -> None:
    try:
        with Image.open(src) as opened:
            opened.load()  # surface truncated/corrupt data here rather than halfway through saving
            icc = opened.info.get("icc_profile")
            # Bake in the EXIF rotation, since the EXIF data itself is not carried over.
            im = ImageOps.exif_transpose(opened)
    except UnidentifiedImageError:
        raise ConvertError("bukan file gambar yang valid") from None
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as e:
        raise ConvertError(f"gambar rusak atau tidak bisa dibaca ({e})") from None

    options = dict(SAVE_OPTIONS[fmt])
    if icc:
        options["icc_profile"] = icc
    try:
        prepare(im, fmt).save(dst, PIL_FORMAT[fmt], **options)
    except OSError as e:
        raise ConvertError(f"gagal menulis hasil ({e})") from None
