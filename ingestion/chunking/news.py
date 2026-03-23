import logging
import json
from pathlib import Path
from bs4 import BeautifulSoup

from core.load_settings import load_settings

settings = load_settings()
logger = logging.getLogger("ingestion")

def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def chunk_news():
    file_path = Path(settings["data"]["processed_dir"]) / "news.json"

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            news_data = json.load(file)
        logger.info(f"Successfully loaded {len(news_data)} records from {file_path}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format {e}")
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

    if isinstance(news_data, dict):
        news_data = [news_data]

    if not isinstance(news_data, list):
        logger.error("News data is not a list")
        return []

    if not news_data:
        logger.warning("No news found in the data")
        return []

    chunks = []

    for idx, news_item in enumerate(news_data):
        if not isinstance(news_item, dict):
            logger.warning(f"Skipping invalid news item at index {idx}")
            continue

        news_title = news_item.get("title", "")
        if not news_title or not isinstance(news_title, str):
            logger.warning(f"Skipping news item with invalid title at index {idx}")
            continue

        news_excerpt = news_item.get("excerpt", "")
        if not news_excerpt or not isinstance(news_excerpt, str):
            logger.warning(f"Skipping news item with invalid excerpt at index {idx}")
            continue

        news_content = news_item.get("content", "")
        if not news_content or not isinstance(news_content, str):
            logger.warning(f"Skipping news item with invalid content at index {idx}")
            continue

        new_content_text = html_to_text(news_content)
        news_image = news_item.get("thumbnailUrl")
        news_category = news_item.get("category")
        news_category_id = news_item.get("categoryId")
        news_category_name = news_item.get("categoryName")
        news_category_slug = news_item.get("categorySlug")

        text_parts = [
            f"Tiêu đề tin tức: {news_title}",
            f"Tóm tắt tin tức: {news_excerpt}",
            f"Nội dung chi tiết tin tức: {new_content_text}"
        ]

        text = "\n".join(text_parts)

        chunks.append({
            "text": text,
            "metadata": {
                "type": "news",
                "source": "news.json",
                "title": news_title,
                "excerpt": news_excerpt,
                "image": news_image,
                "category": news_category,              
                "category_id": news_category_id,
                "category_name": news_category_name,
                "category_slug": news_category_slug,
            }
        })

    if not chunks:
        logger.warning("No valid architecture type chunks were created")

    return chunks