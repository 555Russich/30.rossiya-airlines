import logging
import sys
from pathlib import Path


def get_logger(filepath: Path) -> None:
    """
        Define logger to write logs in specific file.
        mode='a' is appending if file already exists
    """
    logging.basicConfig(
        level=logging.DEBUG,
        encoding='utf-8',
        format="[{asctime},{msecs:03.0f}]:[{levelname}]:{message}",
        datefmt='%d.%m.%Y %H:%M:%S',
        style='{',
        handlers=[
            logging.FileHandler(filepath, mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout),
        ]
    )

    logging.getLogger('asyncio').setLevel(logging.WARNING)


def log_and_print(msg: str) -> None:
    logging.info(msg)
    print(msg)
