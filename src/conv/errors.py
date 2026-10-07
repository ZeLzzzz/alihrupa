class ConvertError(Exception):
    """A file could not be converted; the message is shown to the user as-is."""


def warn(src, message: str) -> None:
    """A conversion succeeded, but the user should know about a limitation of the result."""
    import sys

    print(f"conv: {src}: peringatan: {message}", file=sys.stderr)
