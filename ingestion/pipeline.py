import logging

from core.schema import Chunk
from ingestion.chunking.architectureTypes import chunk_architecture_types
from ingestion.chunking.companyInfo import chunk_company_info
from ingestion.chunking.interiorStyles import chunk_interior_styles
from ingestion.chunking.news import chunk_news
from ingestion.chunking.newsCategories import chunk_news_categories
from ingestion.chunking.projectCategories import chunk_project_categories
from ingestion.chunking.projects import chunk_projects
from ingestion.helpers.ids import chunk_id

logger = logging.getLogger("ingestion")

CHUNKERS = [
    chunk_architecture_types,
    chunk_company_info,
    chunk_interior_styles,
    chunk_news_categories,
    chunk_news,
    chunk_project_categories,
    chunk_projects,
]


def build_chunks() -> list[Chunk]:
    """Run every chunker and return deduplicated chunks with deterministic ids."""
    chunks: dict[str, Chunk] = {}
    for chunker in CHUNKERS:
        for raw in chunker():
            meta = raw["metadata"]
            cid = chunk_id(meta.get("source", ""), meta.get("chunk_type", ""), raw["text"])
            chunks[cid] = Chunk(id=cid, text=raw["text"], metadata={**meta, "chunk_id": cid})
    logger.info(f"Built {len(chunks)} chunks")
    return list(chunks.values())
