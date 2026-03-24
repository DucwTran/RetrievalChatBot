import json
import logging
from pathlib import Path

from core.load_settings import load_settings

settings = load_settings()
logger = logging.getLogger("ingestion")

def chunk_interior_styles():
    file_path = Path(settings["data"]["processed_dir"]) / "interiorStyles.json"

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            interior_styles = json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

    if isinstance(interior_styles, dict):
        interior_styles = [interior_styles]

    if not isinstance(interior_styles, list):
        logger.error("Interior styles data is not a list")
        return []

    if not interior_styles:
        logger.warning("No interior styles found in the data")
        return []

    chunks = []

    for idx, interior_style in enumerate(interior_styles):
        if not isinstance(interior_style, dict):
            logger.warning(f"Skipping invalid interior style at index {idx}")
            continue

        interior_style_id = interior_style.get("id")
        interior_style_name = interior_style.get("name", "")
        interior_style_slug = interior_style.get("slug", "")
        interior_style_description = interior_style.get("description", "")
        interior_style_image = interior_style.get("imageUrl", "")

        # chỉ bắt buộc name
        if not isinstance(interior_style_name, str) or not interior_style_name:
            logger.warning(f"Invalid interior style name at index {idx}")
            continue

        if not isinstance(interior_style_description, str):
            interior_style_description = ""

        if not isinstance(interior_style_image, str):
            interior_style_image = ""

        text_parts = [
            f"Loại nội thất: {interior_style_name}",
            f"Mô tả: {interior_style_description}",
            f"Hình ảnh minh họa: {interior_style_image}",
        ]

        text = "\n".join([t for t in text_parts if t.strip()])

        chunks.append({
            "text": text,
            "metadata": {
                "type": "interior_style",
                "source": "interiorStyles.json",
                "interior_style_id": interior_style_id,
                "interior_style_name": interior_style_name,
                "interior_style_slug": interior_style_slug,
                "interior_style_description": interior_style_description,
                "interior_style_image": interior_style_image,
            }
        })

    if not chunks:
        logger.warning("No valid interior style chunks were created")

    return chunks
