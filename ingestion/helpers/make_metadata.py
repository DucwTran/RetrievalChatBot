def make_metadata(base: dict, **extra) -> dict:
    """Merge shared record metadata with chunk-specific fields."""
    return {**base, **extra}
