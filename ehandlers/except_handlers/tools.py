"""
Поддерживающие функции для интерфейса перехвата и логирования исключений.
"""
import inspect
from typing import Any


def is_exception(obj: Any) -> bool:
    """Объект является любым видом исключения?"""
    return is_exc_instance(obj) or is_exc_type(obj)


def is_exc_type(obj: Any) -> bool:
    """Это объект типа класса исключений? Пример: TypeError."""

    is_instance = is_exc_instance(obj)
    is_exc_class = inspect.isclass(obj) and issubclass(obj, Exception)

    return not is_instance and is_exc_class


def is_exc_instance(obj: Any) -> bool:
    """Это экземпляр исключения? Пример: ValueError("message")"""
    return isinstance(obj, Exception)
