import logging

from core.setup_logging import setup_logging
from core.load_settings import load_settings
from ingestion.chunking.architectureTypes import chunk_architecture_types
from ingestion.chunking.companyInfo import chunk_company_info
from ingestion.chunking.interiorStyles import chunk_interior_styles
from ingestion.chunking.newsCategories import chunk_news_categories
from ingestion.chunking.news import chunk_news
from ingestion.chunking.projectCategories import chunk_project_categories
from ingestion.chunking.projects import chunk_projects
from vectorstore.upsert import upsert_chunks

setup_logging()
settings = load_settings()
logger = logging.getLogger("ingestion")

def upload_chunks():
    all_chunks = []

    all_chunks.extend(chunk_architecture_types())
    all_chunks.extend(chunk_company_info())
    all_chunks.extend(chunk_interior_styles())
    all_chunks.extend(chunk_news_categories())
    all_chunks.extend(chunk_news())
    all_chunks.extend(chunk_project_categories())
    all_chunks.extend(chunk_projects())
    logger.info(f"Total chunks created: {len(all_chunks)}")

    upsert_chunks(all_chunks)
    logger.info("All chunks have been uploaded to the vector store")

if __name__ =="__main__":
    upload_chunks()

