import logging
import json
from pathlib import Path

from core.load_settings import load_settings

settings = load_settings()
logger = logging.getLogger("ingestion")

def chunk_projects():
    file_path = Path(settings["data"]["processed_dir"]) / "projects.json"

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            projects = json.load(file)
        logger.info(f"Loaded {len(projects)} projects from {file_path}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []

    if isinstance(projects, dict):
        projects = [projects]

    if not isinstance(projects, list):
        logger.error("Projects data is not a list")
        return []

    if not projects:
        logger.warning("No projects found in the file")
        return []

    chunks = []

    for idx, project in enumerate(projects):
        if not isinstance(project, dict):
            logger.warning(f"Skipping invalid project at index {idx}")
            continue

        project_id = project.get("id")
        project_title = project.get("title", "")
        if not isinstance(project_title, str) or not project_title:
            logger.warning(f"Invalid title at index {idx}")
            continue

        project_slug = project.get("slug", "")
        project_description = project.get("description", "")

        project_investor = project.get("investor", "")
        project_location = project.get("location", "")
        project_area = project.get("area", "")
        project_complete_date = project.get("complete_date", "")
        project_view_count = project.get("view_count", "")

        project_category = project.get("category", {})
        project_category_name = project_category.get("name", "") if isinstance(project_category, dict) else ""
        project_category_id = project_category.get("id") if isinstance(project_category, dict) else None
        project_category_slug = project_category.get("slug") if isinstance(project_category, dict) else ""

        project_interior_style = project.get("interiorStyle", {})
        project_interior_style_name = project_interior_style.get("name", "") if isinstance(project_interior_style, dict) else ""
        project_interior_style_id = project_interior_style.get("id") if isinstance(project_interior_style, dict) else None
        project_interior_style_slug = project_interior_style.get("slug") if isinstance(project_interior_style, dict) else ""

        project_architecture_type = project.get("architectureType", {})
        project_architecture_type_name = project_architecture_type.get("name", "") if isinstance(project_architecture_type, dict) else ""
        project_architecture_type_id = project_architecture_type.get("id") if isinstance(project_architecture_type, dict) else None
        project_architecture_type_slug = project_architecture_type.get("slug") if isinstance(project_architecture_type, dict) else ""

        text_parts = [
            f"Tên dự án: {project_title}",
            f"Mô tả: {project_description}",
            f"Dự án {project_title} thuộc loại {project_category_name}, "
            f"phong cách nội thất {project_interior_style_name}, "
            f"kiến trúc {project_architecture_type_name}.",
            f"Địa điểm: {project_location}",
            f"Nhà đầu tư: {project_investor}",
            f"Diện tích: {project_area}",
            f"Ngày hoàn thành: {project_complete_date}",
        ]

        text = "\n".join([t for t in text_parts if t and str(t).strip()])

        chunks.append({
            "text": text,
            "metadata": {
                "type": "project",
                "source": file_path.name,
                "project_id": project_id,
                "project_title": project_title,
                "project_slug": project_slug,
                "project_description": project_description,
                "project_location": project_location,
                "project_category": project_category_name,
                "project_category_slug": project_category_slug,
                "project_interior_style": project_interior_style_name,
                "project_architecture_type": project_architecture_type_name,
            }
        })

    if not chunks:
        logger.warning("No valid project chunks were created")

    return chunks
