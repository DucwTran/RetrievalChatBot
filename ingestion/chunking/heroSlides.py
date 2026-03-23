import logging
import json
from pathlib import Path

from core.load_settings import load_settings

settings = load_settings()
logger = logging.getLogger("ingestion")

def chunk_hero_slides():
    file_path = Path(settings["data"]["processed_dir"]) / "heroSlides.json"

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            hero_slides = json.load(file)
            logger.info(f"Loaded {len(hero_slides)} hero slides from {file_path}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format {e}")
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []

    if isinstance(hero_slides, dict):
        hero_slides = [hero_slides]

    if not isinstance(hero_slides, list):
        logger.error("Hero slides data is not a list")
        return []

    if not hero_slides:
        logger.warning("No hero slides found in the file")
        return []

    chunks = []

    for idx, slide in enumerate(hero_slides):
        if not isinstance(slide, dict):
            logger.warning(f"Skipping invalid slide at index {idx}")
            continue

        company_title = slide.get("title", "")
        if not company_title or not isinstance(company_title, str):
            logger.warning(f"Skipping slide at index {idx} due to missing or invalid title")
            continue

        company_subtitle = slide.get("subtitle", "")
        if not company_subtitle or not isinstance(company_subtitle, str):
            logger.warning(f"Skipping slide at index {idx} due to missing or invalid subtitle")
            continue

        company_description = slide.get("description", "")
        if not company_description or not isinstance(company_description, str):
            logger.warning(f"Skipping slide at index {idx} due to missing or invalid description")
            continue

        company_image_url = slide.get("imageUrl")

        text_parts = [
            f"Lời mở đầu cho mục: {company_title} của công ty",
            f"Phụ đề mục {company_title}: {company_subtitle}",
            f"Mô tả chi tiết mục {company_title}: {company_description}"
        ]

        text = "\n".join(text_parts)

        chunks.append({
            "text": text,
            "metadata": {
                "type": "hero_slide",
                "source": "heroSlides.json",
                "slide_index": idx,
                "title": company_title,
                "subtitle": company_subtitle,
                "description": company_description,
                "image_url": company_image_url
            }
        })

    if not chunks:
        logger.warning("No valid hero slide chunks were created")

    return chunks