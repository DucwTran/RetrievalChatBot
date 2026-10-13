import json
import logging
from pathlib import Path
from datetime import datetime

from core.config import get_settings
from ingestion.helpers.make_metadata import make_metadata

settings = get_settings()
logger = logging.getLogger("ingestion")

def chunk_company_info():
    file_path = Path(settings.data.processed_dir) / "companyInfo.json"

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            company_info = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format {e}")
        return []
    except Exception as e:
        logger.error(f"Failed to load {e}")
        return []

    if isinstance(company_info, dict):
        company_info = [company_info]

    if not isinstance(company_info, list):
        logger.error("Company info data is not a list")
        return []

    if not company_info:
        logger.warning("No company info found in the data")
        return []

    chunks = []

    for idx, company in enumerate(company_info):
        if not isinstance(company, dict):
            logger.warning(f"Invalid company info at index {idx}: expected a dictionary")
            continue

        company_id = company.get("id")
        company_name = company.get("companyName", "")
        company_slogan = company.get("companySlogan")
        company_description = company.get("companyDescription", "")
        company_hotline = company.get("hotlines")
        company_email = company.get("emails")
        company_address = company.get("mainAddress")
        company_working_hours = company.get("workingHours")
        company_website = company.get("website")
        company_total_projects = company.get("totalProjects")
        company_social_links = company.get("socialLinks")
        company_social_text = ""
        if isinstance(company_social_links, dict):
            company_social_text = ", ".join([f"{key}: {value}" for key, value in company_social_links.items() if value])

        base_metadata = {
            "type": "company_info",
            "company_id": company_id,
            "company_name": company_name,
            "source": "companyInfo.json",
            "created_at": datetime.utcnow().isoformat(),
            "language": "vi"
        }

        CHUNK_PRIORITY = {
            "overview": 1,
            "description": 2,
            "contact_info": 3,
        }

        # Chunk overview
        if company_name and company_slogan:
            chunks.append({
                "text": f'Tên công ty: {company_name}\nKhẩu hiệu công ty: {company_slogan}',
                "metadata": make_metadata(base_metadata, chunk_type="overview", priority=CHUNK_PRIORITY["overview"])
            })

        # Chunk full description
        if company_description:
            if company_total_projects is not None:
                chunks.append({
                    "text": f"Mô tả công ty {company_name}: {company_description}. \nCông ty đã thực hiện tổng cộng {company_total_projects} dự án." ,
                    "metadata": make_metadata(base_metadata, chunk_type="description", priority=CHUNK_PRIORITY["description"])
                })
            else:
                chunks.append({
                    "text": f"Mô tả công ty {company_name}: {company_description}.",
                    "metadata": make_metadata(base_metadata, chunk_type="description", priority=CHUNK_PRIORITY["description"])
                })

        # Chunk contact info
        if company_hotline or company_email or company_address or company_website or company_social_text:
            text_parts = []
            if company_hotline:
                text_parts.append(f"Hotline: {company_hotline}")
            if company_email:
                text_parts.append(f"Email: {company_email}")
            if company_address:
                text_parts.append(f"Địa chỉ: {company_address}")
            if company_working_hours:
                text_parts.append(f"Giờ làm việc: {company_working_hours}")
            if company_website:
                text_parts.append(f"Website: {company_website}")
            if company_social_text:
                text_parts.append(f"Mạng xã hội: {company_social_text}")
            chunks.append({
                "text": "\n".join(text_parts),
                "metadata": make_metadata(base_metadata, chunk_type="contact_info", priority=CHUNK_PRIORITY["contact_info"])
            })

    return chunks
