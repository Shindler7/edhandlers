"""
Подготовка сообщений для логирования исключений.
"""

from collections.abc import Iterable, Mapping
from typing import Any

from ehandlers.except_handlers.tools import is_exc_instance, is_exc_type


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


def err_annotated_msg(
    err_a: str | None,
    add_args: bool,
    exclude_args: Iterable[str] | None,
    args: tuple[Any, ...],
    kwargs: Mapping[str, Any],
) -> str | None:
    """Формирует аннотацию с опциональными аргументами функции.

    Используется в декораторах для добавления контекста выполнения.

    Warnings:
        Данные не маскируются — учитывайте это при работе с чувствительной информацией.
        Аргументы вносятся в логи "как есть".

    Args:
        err_a: Базовое сообщение аннотации.
        add_args: Флаг добавления аргументов функции к аннотации.
        exclude_args: Перечисленные именованные аргументы, которые будут
            исключены из выдачи, если используется `add_args`.
        *args: Позиционные аргументы вызванной функции.
        **kwargs: Именованные аргументы вызванной функции.

    Returns:
        None, если нет `err_a` и `add_args=False`, в ином случае оформленная строка.
    """

    if not add_args:
        return err_a

    args_repr: str = repr(args) if args else '()'

    # Kwargs требует более детальной обработки.
    if kwargs:
        excluded: set[str] = set(exclude_args or ())
        valid_kwargs = {k: v for k, v in kwargs.items() if k not in excluded}
        kwargs_repr: str = repr(valid_kwargs)
    else:
        kwargs_repr: str = '{}'

    args_info = f'args={args_repr}, kwargs={kwargs_repr}'

    if err_a:
        return f'{err_a} | {args_info}'

    return args_info
