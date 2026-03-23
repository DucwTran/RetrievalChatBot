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
        logger.error(f"Invalid JSON format {e}")
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []

    if isinstance(projects, dict):
        projects = [projects]

    if not isinstance(projects, list):
        logger.error(f"Projects data is not a list")
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
      if not project_title or not isinstance(project_title, str):
          logger.warning(f"Skipping project with invalid title at index {idx}")
          continue

      project_slug = project.get("slug")
      project_description = project.get("description", "")
      if not project_description or not isinstance(project_description, str):
          logger.warning(f"Skipping project with invalid description at index {idx}")
          continue

      project_investor = project.get("investor", "")
      project_location = project.get("location", "")
      project_area = project.get("area", "")
      project_complete_date = project.get("complete_date", "")
      project_view_count = project.get("view_count", "")

      project_category = project.get("category", {})
      if not project_category or not isinstance(project_category, dict):
          logger.warning(f"Skipping project with invalid category at index {idx}")
          continue

      project_category_id = project_category.get("id")
      project_category_name = project_category.get("name", "")
      if not project_category_name or not isinstance(project_category_name, str):
          logger.warning(f"Skipping project with invalid category name at index {idx}")
          continue

      project_category_slug = project_category.get("slug")

      project_interior_style = project.get("interiorStyle", {})
      if not project_interior_style or not isinstance(project_interior_style, dict):
          logger.warning(f"Skipping project with invalid interior style at index {idx}")
          continue

      project_interior_style_id = project_interior_style.get("id")
      project_interior_style_name = project_interior_style.get("name", "")
      if not project_interior_style_name or not isinstance(project_interior_style_name, str):
          logger.warning(f"Skipping project with invalid interior style name at index {idx}")
          continue

      project_interior_style_slug = project_interior_style.get("slug")

      project_architecture_type = project.get("architectureType", {})
      if not project_architecture_type or not isinstance(project_architecture_type, dict):
          logger.warning(f"Skipping project with invalid architecture type at index {idx}")
          continue

      project_architecture_type_id = project_architecture_type.get("id")
      project_architecture_type_name = project_architecture_type.get("name", "")
      if not project_architecture_type_name or not isinstance(project_architecture_type_name, str):
          logger.warning(f"Skipping project with invalid architecture type name at index {idx}")
          continue

      project_architecture_type_slug = project_architecture_type.get("slug")

      text_parts = [
        f"Tên dự án: {project_title}",
        f"Slug dự án: {project_slug}",
        f"Mô tả dự án: {project_description}",
        f"Nhà đầu tư: {project_investor}",
        f"Địa điểm: {project_location}",
        f"Diện tích: {project_area}",
        f"Ngày hoàn thành: {project_complete_date}",
        f"Lượt xem: {project_view_count}",
        f"Loại dự án: {project_category_name}",
        f"Phong cách nội thất: {project_interior_style_name}",
        f"Loại kiến trúc: {project_architecture_type_name}",
      ]

      text = "\n".join(text_parts)

      chunks.append({
          "text": text,
          "metadata": {
              "type": "project",
              "source": "projects.json",
              "project_id": project_id,
              "project_title": project_title,
              "project_slug": project_slug,
              "project_description": project_description,
              "project_investor": project_investor,
              "project_location": project_location,
              "project_area": project_area,
              "project_complete_date": project_complete_date,
              "project_view_count": project_view_count,
              "project_category_id": project_category_id,
              "project_category_slug": project_category_slug,
              "project_category": project_category_name,
              "project_interior_style_id": project_interior_style_id,
              "project_interior_style_slug": project_interior_style_slug,
              "project_interior_style": project_interior_style_name,
              "project_architecture_type_id": project_architecture_type_id,
              "project_architecture_type_slug": project_architecture_type_slug,
              "project_architecture_type": project_architecture_type_name,
          }
      })

    if not chunks:
      logger.warning("No valid news category chunks were created")

    return chunks