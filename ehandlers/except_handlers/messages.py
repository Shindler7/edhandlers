"""
Подготовка сообщений для логирования исключений.
"""

import inspect
from collections.abc import Callable, Iterable, Mapping
from functools import cache
from inspect import Signature
from typing import Any

from .tools import is_exc_instance, is_exc_type


def get_simple_or_annotated(
    err: Exception | type[Exception] | str,
    func_name: str,
    err_annotated: str | None = None,
) -> str:
    """Выбирает формат сообщения об ошибке: простой или аннотированный.

    Args:
        err: Объект исключения (ошибки).
        func_name: Имя функции, в которой произошло исключение.
        err_annotated: Опциональная текстовая аннотация для подстановки.
            Если передана, формирует расширенный контекст лога.

    Returns:
        Отформатированное сообщение об ошибке, готовое для записи в лог.
    """

    if err_annotated is None:
        return simple_msg_err(err, func_name)
    return annotated_msg_err(err, func_name, err_annotated)


def get_err_str(err: Exception | type[Exception] | str) -> str:
    """Преобразует объект ошибки в строковое представление.

    Args:
        err: Объект ошибки или любое другое значение, вызвавшее сбой.

    Returns:
        Строка распаковки Exception или содержимое атрибута `err`,
        если переданный объект не является наследником Exception.
    """

    if isinstance(err, str):
        return err

    if is_exc_type(err):
        return err.__name__

    if is_exc_instance(err):
        message: str = f'{err.__class__.__name__}'
        err_text = str(err)
        if err_text:
            message = f'{message}: {err_text}'
        return message

    raise TypeError(f'Неподдерживаемый тип ошибки: {err.__class__.__name__}')


def simple_msg_err(err: Exception | type[Exception] | str, func_name: str) -> str:
    """Формирует базовое сообщение об ошибке для логирования.

    Args:
        err: Источник информации об ошибке.
        func_name: Имя функции, в которой произошла ошибка.

    Returns:
        Отформатированная строка для лога.
    """

    return f'[{func_name}] {get_err_str(err)}'


def annotated_msg_err(
    err: Exception | type[Exception] | str, func_name: str, err_annotated: str
) -> str:
    """Формирует аннотированное сообщение об ошибке.

    Args:
        err: Объект ошибки.
        func_name: Имя функции, в которой произошла ошибка.
        err_annotated: Контекст или описание ошибки.

    Returns:
        Отформатированная строка с аннотацией.
    """

    return f'[{func_name}] {err_annotated}: {get_err_str(err)}'


@cache
def _safe_signature(func: Callable[..., Any]) -> inspect.Signature | None:
    """Безопасно извлекает и кэширует сигнатуру функции."""

    try:
        return inspect.signature(inspect.unwrap(func))
    except (TypeError, ValueError):
        return None


def err_annotated_msg(
    annotation: str | None,
    *,
    add_args: bool,
    exclude_args: bool,
    exclude_self: bool,
    exclude_kwargs: Iterable[str] | None,
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: Mapping[str, Any],
) -> str | None:
    """Формирует аннотацию с опциональными аргументами функции.

    Используется в декораторах для добавления контекста выполнения.

    Warnings:
        Данные не маскируются — учитывайте это при работе с чувствительной информацией.
        Аргументы вносятся в логи "как есть".

    Args:
        annotation: Базовое сообщение аннотации.
        add_args: Флаг добавления аргументов функции к аннотации.
        exclude_self: Если True, атрибуты `self` и `cls` не добавляются в логи, если
            включен параметр `args_to_annotate`.
        exclude_args: Если True, будут исключены все неименованные аргументы.
        exclude_kwargs: Перечисленные именованные аргументы, которые будут исключены
            из выдачи, если используется `add_args`.
        func: Указатель на декорированную функцию.
        args: Позиционные аргументы вызванной функции.
        kwargs: Именованные аргументы вызванной функции.

    Returns:
        None, если нет `err_a` и `add_args=False`, в ином случае оформленная строка.
    """

    if not add_args:
        return annotation

    cached_sig: Signature | None = _safe_signature(func)  # type: ignore[arg-type]
    excluded: set[str] = set(exclude_kwargs or ())
    args_info: str = 'args=() kwargs={}'

    if cached_sig is not None:
        try:
            bound = cached_sig.bind(*args, **kwargs)
            bound.apply_defaults()
            arguments = bound.arguments

            if exclude_args:
                arguments.pop('args', None)

            if exclude_self:
                arguments.pop('self', None)
                arguments.pop('cls', None)

            if exclude_kwargs:
                for key in set(exclude_kwargs or ()):
                    arguments.pop(key, None)

            args_info = ', '.join(f'{k}={v!r}' for k, v in arguments.items())
            args_info: str = f'context=({args_info})' if args_info else 'context=()'

        except (TypeError, ValueError):
            cached_sig = None

    if cached_sig is None:
        # Args.
        clean_args: tuple[Any, ...] = () if exclude_args else args
        # Kwargs.
        excluded: set[str] = set(exclude_kwargs or ())
        clean_kwargs = {k: v for k, v in kwargs.items() if k not in excluded}

        args_info: str = f'args={clean_args!r}, kwargs={clean_kwargs!r}'

    return f'{annotation} | {args_info}' if annotation else args_info
