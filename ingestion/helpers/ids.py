import uuid


def chunk_id(source: str, chunk_type: str, text: str) -> str:
    """Deterministic id: re-ingesting the same content yields the same Qdrant point."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}|{chunk_type}|{text}"))
