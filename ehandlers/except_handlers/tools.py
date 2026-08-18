"""
Поддерживающие функции для интерфейса перехвата и логирования исключений.
"""

from typing import TypeGuard


def is_exc_instance(obj: object) -> TypeGuard[Exception]:
    """Это экземпляр исключения? Пример: ValueError("message")."""
    return isinstance(obj, Exception)


def is_exc_type(obj: object) -> TypeGuard[type[Exception]]:
    """Это тип исключения? Пример: TypeError."""
    return isinstance(obj, type) and issubclass(obj, Exception)


def is_exception(obj: object) -> TypeGuard[Exception | type[Exception]]:
    """Это любой вид исключения?"""
    return is_exc_instance(obj) or is_exc_type(obj)
