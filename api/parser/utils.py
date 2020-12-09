from typing import Any, Optional


def sanitize(str: str) -> str:
    """Sanitize a string by stripping whitespace on edges and in between."""
    return " ".join(str.strip().split())

def extract_td_value(td: Any) -> Optional[str]:
    """
    Given a <td> element with potential children, extract the full, sanitized text.
    Returns None if no text or `'TBA'` in the text.
    """
    val = td.xpath("descendant-or-self::*/text()")

    if len(val):
        sanitized = sanitize("".join(val))
        if sanitized == "" or "TBA" in sanitized:
            return None
        return sanitized
    else:
        return None