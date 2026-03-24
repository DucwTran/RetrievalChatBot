import json
import logging
from pathlib import Path

from core.load_settings import load_settings

settings = load_settings()
logger = logging.getLogger("ingestion")

def chunk_architecture_types():
    file_path = Path(settings["data"]["processed_dir"]) / "architectureTypes.json"

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            architecture_types = json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

    if isinstance(architecture_types, dict):
        architecture_types = [architecture_types]

    if not isinstance(architecture_types, list):
        logger.error("Architecture types data is not a list")
        return []

    if not architecture_types:
        logger.warning("No architecture types found in the data")
        return []

    chunks = []

    for idx, architecture_type in enumerate(architecture_types):
        if not isinstance(architecture_type, dict):
            logger.warning(f"Skipping invalid architecture type at index {idx}")
            continue

        architecture_id = architecture_type.get("id")
        architecture_name = architecture_type.get("name", "")
        architecture_slug = architecture_type.get("slug", "")
        architecture_description = architecture_type.get("description", "")
        architecture_image = architecture_type.get("imageUrl", "")

        if not isinstance(architecture_name, str) or not architecture_name:
            logger.warning(f"Invalid architecture name at index {idx}")
            continue

        if not isinstance(architecture_image, str):
            architecture_image = ""

        if not isinstance(architecture_description, str):
            architecture_description = ""

        text_parts = [
            f"Loại kiến trúc: {architecture_name}",
            f"Mô tả: {architecture_description}",
            f"Hình ảnh minh họa: {architecture_image}",
        ]

        text = "\n".join([t for t in text_parts if t.strip()])

        chunks.append({
            "text": text,
            "metadata": {
                "type": "architecture_type",
                "source": "architectureTypes.json",
                "architecture_id": architecture_id,
                "architecture_name": architecture_name,
                "architecture_slug": architecture_slug,
                "architecture_description": architecture_description,
                "architecture_image": architecture_image,
            }
        })

    if not chunks:
        logger.warning("No valid architecture type chunks were created")

    return chunks
