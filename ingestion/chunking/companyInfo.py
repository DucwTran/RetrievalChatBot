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
        logger.error(f"Invalid JSON format {e}")
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return []

    if isinstance(company_info, dict):
        company_info = [company_info]  # convert sang list

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

      company_name = info.get("companyName", "")
      if not company_name or not isinstance(company_name, str):
          logger.warning(f"Skipping company info with invalid name at index {idx}")
          continue

      company_slogan = info.get("companySlogan", "")
      if not company_slogan or not isinstance(company_slogan, str):
          logger.warning(f"Skipping company info with invalid slogan at index {idx}")
          continue

      company_description = info.get("companyDescription", "")
      if not company_description or not isinstance(company_description, str):
          logger.warning(f"Skipping company info with invalid description at index {idx}")
          continue

      company_hotlines = info.get("hotlines", [])
      if not isinstance(info, list):
          logger.warning(f"Skipping invalid company hotline at index {idx}")
          continue
      
      company_emails = info.get("emails", [])
      if not isinstance(info, list):
          logger.warning(f"Skipping invalid company emails at index {idx}")
          continue

      company_main_address = info.get("mainAddress", "")
      if not isinstance(company_main_address, str):
          logger.warning(f"Skipping company info with invalid main address at index {idx}")
          continue

      company_working_hours = info.get("workingHours", "")
      if not isinstance(company_working_hours, str):
          logger.warning(f"Skipping company info with invalid working hours at index {idx}")
          continue

      company_website = info.get("website", "")
      if not company_website or not isinstance(company_website, str):
          logger.warning(f"Skipping company info with invalid website at index {idx}")
          continue

      company_social_links = info.get("socialLinks", {})
      if isinstance(company_social_links, dict):
          company_social_text = ", ".join([f"{key}: {value}" for key, value in company_social_links.items() if value])


      company_total_employees = info.get("totalEmployees")
      if not isinstance(company_total_employees, int):
          logger.warning(f"Skipping company info with invalid total employees at index {idx}")
          continue

      company_total_projects = info.get("totalProjects")
      if not isinstance(company_total_projects, int):
          logger.warning(f"Skipping company info with invalid total projects at index {idx}")
          continue
      
      text_parts = [
        f"Tên công ty: {company_name}",
        f"Khẩu hiệu công ty {company_name}: {company_slogan}",
        f"Mô tả công ty {company_name}: {company_description}",
        f"Số điện thoại liên hệ công ty {company_name}: {', '.join(company_hotlines)}",
        f"Email liên hệ công ty {company_name}: {', '.join(company_emails)}",
        f"Địa chỉ chính công ty {company_name}: {company_main_address}",
        f"Giờ làm việc công ty {company_name}: {company_working_hours}",
        f"Website công ty {company_name}: {company_website}",
        f"Mạng xã hội công ty {company_name}: {company_social_text}",
        f"Tổng số nhân viên công ty {company_name}: {company_total_employees}",
        f"Tổng số dự án công ty {company_name}: {company_total_projects}"
    ]

    text = "\n".join(text_parts)

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
            "company_total_projects": company_total_projects
        }
    })

    if not chunks:
        logger.warning("No valid company info chunks were created")
        return []
    
    return chunks

