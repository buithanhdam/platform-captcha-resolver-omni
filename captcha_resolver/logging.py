from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from datetime import datetime

__all__ = ["get_logger"]

_COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[41m",
}
_RESET = "\033[0m"
_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


class _ColorFormatter(logging.Formatter):
    def format(self, record) -> str:
        color = _COLORS.get(record.levelname, "")
        return f"{color}{super().format(record)}{_RESET}"


def _file_logger(name: str, log_dir: Path, file_level: int, console_level: int) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if logger.handlers:
        return logger

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(file_level)
    file_handler.setFormatter(logging.Formatter(_FMT, datefmt=_DATEFMT))
    logger.addHandler(file_handler)

    if not os.environ.get("OMNI_CAPTCHA_RESOLVER_QUIET", "").lower() in ("1", "true"):
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(_ColorFormatter(_FMT, datefmt=_DATEFMT))
        logger.addHandler(console_handler)

    return logger


def get_logger(
    name: str = "captcha_resolver",
    log_dir: str | Path | None = None,
    file_level: int = logging.DEBUG,
    console_level: int = logging.INFO,
) -> logging.Logger:
    if log_dir is None:
        log_dir = Path(os.environ.get("OMNI_CAPTCHA_RESOLVER_LOG_DIR", "logs"))
    return _file_logger(name, Path(log_dir), file_level, console_level)