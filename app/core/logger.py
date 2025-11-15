"""Global Logging Configuration"""

import os
from typing import Union, Optional
import logging
from logging import FileHandler
from pathlib import Path
from colorlog import ColoredFormatter


def setuplog(
    name: str,
    level: Optional[int] = None,
    log_dir: Union[str, Path] = Path.cwd() / "logs",
    filename: str = "application.log",
) -> logging.Logger:
    """logging setup with color format and file logging into a 'logs' folder"""

    if level is None:
        env_level = os.getenv("LOG_LEVEL")

        if env_level:
            level = getattr(logging, env_level.upper(), logging.DEBUG)
        else:
            level = logging.DEBUG

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
        style="%",
    )

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    file_path = log_dir / filename

    file_formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    )

    # Handlers
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(console_formatter)

    file_handler = FileHandler(
        filename=str(file_path),
        encoding="utf-8",
    )

    logger = logging.getLogger(name)
    assert isinstance(level, int)
    logger.setLevel(level)
    logger.propagate = False

    has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    has_file = any(isinstance(h, FileHandler) for h in logger.handlers)

    if not has_stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(console_formatter)
        logger.addHandler(stream_handler)
    if not has_file:
        file_handler = FileHandler(str(file_path), encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
