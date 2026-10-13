import logging
import shutil
from pathlib import Path

import pytest

from core.setup_logging import setup_logging


@pytest.fixture
def clean_root_logger():
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    for handler in root.handlers[:]:
        if handler not in handlers:
            handler.close()
    root.handlers[:], root.level = handlers, level


def test_setup_logging_works_on_a_fresh_clone_without_logs_dir(tmp_path, monkeypatch, clean_root_logger):
    (tmp_path / "config").mkdir()
    shutil.copy(Path("config/logging.yaml"), tmp_path / "config" / "logging.yaml")
    monkeypatch.chdir(tmp_path)
    assert not (tmp_path / "logs").exists()

    setup_logging()
    logging.getLogger("rag").info("hello")

    assert (tmp_path / "logs" / "application.log").exists()
