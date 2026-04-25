"""
Поддерживающие функции для интерфейса перехвата и логирования исключений.
"""
from typing import TypeAlias, TypeGuard

ExcInst: TypeAlias = Exception
ExcType: TypeAlias = type[Exception]
ExcLike: TypeAlias = ExcInst | ExcType


def is_exc_instance(obj: object) -> TypeGuard[ExcInst]:
    """Это экземпляр исключения? Пример: ValueError("message")"""
    return isinstance(obj, Exception)


def is_exc_type(obj: object) -> TypeGuard[ExcType]:
    """Это класс исключений? Пример: TypeError."""
    return isinstance(obj, type) and issubclass(obj, Exception)


def is_exception(obj: object) -> TypeGuard[ExcLike]:
    """Объект является любым видом исключения?"""
    return is_exc_instance(obj) or is_exc_type(obj)
