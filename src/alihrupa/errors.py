class ConvertError(Exception):
    """A file could not be converted; the message is shown to the user as-is."""


def warn(src, message: str) -> None:
    """A conversion succeeded, but the user should know about a limitation of the result."""
    import sys

    print(f"alihrupa: {src}: warning: {message}", file=sys.stderr)


def plural(n: int, noun: str) -> str:
    """"1 image", "2 images"."""
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"
