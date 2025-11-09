"""Global Logging Configuration"""

import logging
from logging import FileHandler
from pathlib import Path
from colorlog import ColoredFormatter
from typing import Optional, Union

def setuplog(
    name: str,
    level: int = logging.INFO,
    log_dir: Union[str, Path] = Path.cwd() / "logs",
    filename: str = "application.log",  # Fixed filename
) -> logging.Logger:
    """logging setup with color format and file logging into a 'logs' folder.

    All logs are written to a single file: ./logs/application.log.
    """

    # Colored console formatter
    console_formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(name)s:%(reset)s %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%"
    )

    # Ensure log directory exists
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    file_path = log_dir / filename  # Use the fixed filename

    # Plain formatter for file output
    file_formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")

    # Handlers
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(console_formatter)

    file_handler = FileHandler(
        filename=str(file_path),
        encoding="utf-8",
    )
    file_handler.setFormatter(file_formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # avoid double logging if root logger is configured

    # Avoid adding duplicate handlers when setuplog is called multiple times
    has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    has_file = any(isinstance(h, FileHandler) for h in logger.handlers)

    if not has_stream:
        logger.addHandler(stream_handler)
    if not has_file:
        logger.addHandler(file_handler)

    return logger
