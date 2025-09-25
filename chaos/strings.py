"""String utilities for the chaos package."""

from typing import Any
import re
import unicodedata
from .rules import get_rules


_DASH_CHARS = "\u2012\u2013\u2014\u2015\u2212\u2043\uFE58\uFE63\uFF0D"
_DASH_RE = re.compile(f"[{_DASH_CHARS}]")


def slugify(text: Any, *, strict: bool = False, max_len: int = 64) -> str:
    """Convert arbitrary text to a URL-safe slug.

    Rules:
    - Lowercase all letters
    - Convert spaces/underscores/punctuation to hyphens
    - Normalize unicode; strip accents to ASCII equivalents
    - Collapse multiple hyphens and trim from ends
    """
    if text is None:
        return ""

    # Coerce to string
    s = str(text)

    # Normalize various dash-like characters to ASCII hyphen for preservation
    s = _DASH_RE.sub("-", s)

    # Normalize unicode and strip accents by ASCII encoding
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")

    # Characters treated as joiners (removed) rather than separators
    for ch in get_rules().joiners:
        s = s.replace(ch, "")

    # Lowercase
    s = s.lower()

    # Replace any non-alphanumeric with hyphen
    s = re.sub(r"[^a-z0-9]+", "-", s)

    # Collapse multiple hyphens
    s = re.sub(r"-+", "-", s)

    # Trim hyphens
    s = s.strip("-")

    if strict:
        # Enforce maximum length and re-trim
        if max_len > 0 and len(s) > max_len:
            s = s[:max_len].strip("-")
        # Enforce non-empty fallback
        if not s:
            s = "n-a"

    return s
