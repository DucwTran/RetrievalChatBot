import logging
import json
from pathlib import Path

from core.load_settings import load_settings

settings = load_settings()
logger = logging.getLogger("ingestion")


def chunk_company_info():
    file_path = Path(settings["data"]["processed_dir"]) / "companyInfo.json"

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            company_info = json.load(file)
            logger.info(f"Successfully loaded {len(company_info)} records from {file_path}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

    # normalize về list
    if isinstance(company_info, dict):
        company_info = [company_info]

    if not isinstance(company_info, list):
        logger.error("Company info data is not a list")
        return []

    if not company_info:
        logger.warning("No company info found in the data")
        return []

    chunks = []

    for idx, info in enumerate(company_info):
        if not isinstance(info, dict):
            logger.warning(f"Skipping invalid company info at index {idx}")
            continue

        # ====== lấy dữ liệu ======
        company_name = info.get("companyName")
        company_slogan = info.get("companySlogan")
        company_description = info.get("companyDescription")
        company_hotlines = info.get("hotlines", [])
        company_emails = info.get("emails", [])
        company_main_address = info.get("mainAddress")
        company_working_hours = info.get("workingHours")
        company_website = info.get("website")
        company_social_links = info.get("socialLinks", {})
        company_total_employees = info.get("totalEmployees")
        company_total_projects = info.get("totalProjects")

        # ====== validate ======
        if not isinstance(company_name, str) or not company_name:
            logger.warning(f"Invalid company name at index {idx}")
            continue

        if not isinstance(company_slogan, str):
            company_slogan = ""

        if not isinstance(company_description, str):
            company_description = ""

        if not isinstance(company_hotlines, list):
            logger.warning(f"Invalid hotlines at index {idx}")
            company_hotlines = []

        if not isinstance(company_emails, list):
            logger.warning(f"Invalid emails at index {idx}")
            company_emails = []

        if not isinstance(company_main_address, str):
            company_main_address = ""

        if not isinstance(company_working_hours, str):
            company_working_hours = ""

        if not isinstance(company_website, str):
            company_website = ""

        if not isinstance(company_social_links, dict):
            company_social_links = {}

        if not isinstance(company_total_employees, int):
            company_total_employees = 0

        if not isinstance(company_total_projects, int):
            company_total_projects = 0

        # ====== xử lý social links ======
        company_social_text = ", ".join(
            [f"{key}: {value}" for key, value in company_social_links.items() if value]
        )

        # ====== build text ======
        text_parts = [
            f"Tên công ty: {company_name}",
            f"Khẩu hiệu: {company_slogan}",
            f"Mô tả: {company_description}",
            f"Số điện thoại: {', '.join(company_hotlines)}",
            f"Email: {', '.join(company_emails)}",
            f"Địa chỉ: {company_main_address}",
            f"Giờ làm việc: {company_working_hours}",
            f"Website: {company_website}",
            f"Mạng xã hội: {company_social_text}",
            f"Tổng nhân viên: {company_total_employees}",
            f"Tổng dự án: {company_total_projects}",
        ]

        text = "\n".join([t for t in text_parts if t.strip()])

        # ====== append chunk ======
        chunks.append({
            "text": text,
            "metadata": {
                "type": "company_info",
                "source": "companyInfo.json",
                "company_name": company_name,
                "company_slogan": company_slogan,
                "company_description": company_description,
                "company_hotlines": company_hotlines,
                "company_emails": company_emails,
                "company_main_address": company_main_address,
                "company_working_hours": company_working_hours,
                "company_website": company_website,
                "company_social_links": company_social_links,
                "company_total_employees": company_total_employees,
                "company_total_projects": company_total_projects,
            }
        })

    if not chunks:
        logger.warning("No valid company info chunks were created")
        return []

    return chunks
