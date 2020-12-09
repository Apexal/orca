def sanitize(str: str) -> str:
    """Sanitize a string by stripping whitespace on edges and in between."""
    return " ".join(str.strip().split())