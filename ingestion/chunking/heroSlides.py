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
        logger.error(f"Invalid JSON format: {e}")
        return []
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

        slide_title = slide.get("title", "")
        slide_subtitle = slide.get("subtitle", "")
        slide_description = slide.get("description", "")
        slide_image_url = slide.get("imageUrl", "")

        # chỉ bắt buộc title
        if not isinstance(slide_title, str) or not slide_title:
            logger.warning(f"Invalid title at index {idx}")
            continue

        if not isinstance(slide_subtitle, str):
            slide_subtitle = ""

        if not isinstance(slide_description, str):
            slide_description = ""

        if not isinstance(slide_image_url, str):
            slide_image_url = ""

        text_parts = [
            f"Tiêu đề: {slide_title}",
            f"Phụ đề: {slide_subtitle}",
            f"Mô tả: {slide_description}",
            f"Hình ảnh: {slide_image_url}",
        ]

        text = "\n".join([t for t in text_parts if t.strip()])

        chunks.append({
            "text": text,
            "metadata": {
                "type": "hero_slide",
                "source": "heroSlides.json",
                "slide_index": idx,
                "title": slide_title,
                "subtitle": slide_subtitle,
                "description": slide_description,
                "image_url": slide_image_url
            }
        })

    if not chunks:
        logger.warning("No valid hero slide chunks were created")

    return chunks
