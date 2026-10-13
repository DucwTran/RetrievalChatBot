"""Ingest the knowledge base into Qdrant.

Usage: python -m scripts.ingest [--recreate] [--skip-export]
"""
import argparse
import logging

from core.config import get_settings
from core.setup_logging import setup_logging
from embedding.embedder import Embedder
from ingestion.load_data import export_tables
from ingestion.pipeline import build_chunks
from vectorstore.qdrant import ensure_collection, make_client, upsert_chunks

logger = logging.getLogger("ingestion")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recreate", action="store_true", help="drop and rebuild the collection")
    parser.add_argument("--skip-export", action="store_true", help="reuse data/processed as is")
    args = parser.parse_args()

    setup_logging()
    settings = get_settings()

    if not args.skip_export:
        export_tables()
    chunks = build_chunks()
    if not chunks:
        raise SystemExit("No chunks produced; nothing to ingest.")

    embedder = Embedder(settings.embedding.model, settings.embedding.device, settings.embedding.batch_size)
    client = make_client(settings.qdrant)
    name = settings.qdrant.collection
    ensure_collection(client, name, embedder.dimension, recreate=args.recreate)

    step = settings.embedding.batch_size
    for i in range(0, len(chunks), step):
        batch = chunks[i : i + step]
        upsert_chunks(client, name, batch, embedder.embed_passages([c.text for c in batch]))
        logger.info(f"Upserted {i + len(batch)}/{len(chunks)}")

    logger.info(f"Done. Collection '{name}' has {client.count(name).count} points.")


if __name__ == "__main__":
    main()
