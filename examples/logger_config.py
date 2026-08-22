"""
Экспериментальный логгер.

Выводит сообщения в консоль, используется в примерах.
"""

import logging
from logging import LogRecord


class CustomFormatter(logging.Formatter):
    # ANSI коды для цветов
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    RESET = '\033[0m'

    FORMAT = '%(levelname)s: %(message)s'

    FORMATS = {
        logging.INFO: f'{GREEN}%(levelname)s:{RESET} %(message)s',
        logging.WARNING: f'{YELLOW}%(levelname)s:{RESET} %(message)s',
        logging.ERROR: f'{RED}%(levelname)s:{RESET} %(message)s',
    }

    def format(self, record: LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self.FORMAT)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_logger(name: str = 'example') -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Чтобы хендлеры не дублировались при повторных вызовах.
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(CustomFormatter())
        logger.addHandler(handler)

    return logger
