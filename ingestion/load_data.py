import json
import logging
from pathlib import Path

from core.config import get_settings

logger = logging.getLogger("ingestion")


def export_tables() -> list[Path]:
    """Split the newest `database_export_*.json` in raw_dir into one JSON file per table."""
    settings = get_settings()
    raw_dir = Path(settings.data.raw_dir)
    out_dir = Path(settings.data.processed_dir)

    exports = sorted(raw_dir.glob("database_export_*.json"))
    if not exports:
        raise FileNotFoundError(f"No database_export_*.json found in {raw_dir}")
    source = exports[-1]

    with open(source, "r", encoding="utf-8") as f:
        tables = json.load(f).get("tables", {})

    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, rows in tables.items():
        if not rows:
            logger.warning(f"No data found in table: {name}")
            continue
        path = out_dir / f"{name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        written.append(path)
    logger.info(f"Exported {len(written)} tables from {source.name}")
    return written
