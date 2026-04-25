"""
Подготовка сообщений для логирования исключений.
"""
from collections.abc import Iterable, Mapping
from typing import Any

from ehandlers.except_handlers.tools import is_exc_instance, is_exc_type


def get_simple_or_annotated(err: Exception | type[Exception] | str,
                            func_name: str,
                            err_annotated: str | None = None) -> str:
    """Выбирает формат сообщения об ошибке: простой или аннотированный.

    :param err: Объект ошибки.
    :param func_name: Имя функции, в которой произошла ошибка.
    :param err_annotated: Опциональная аннотация ошибки.
    :return: Отформатированное сообщение об ошибке.
    """

    if err_annotated is None:
        return simple_msg_err(err, func_name)
    return annotated_msg_err(err, func_name, err_annotated)


def get_err_str(err: Exception | type[Exception] | str) -> str:
    """Преобразует объект ошибки в строковое представление.

    :param err: Объект ошибки.
    :return: Строка распаковки Exception или содержимое атрибута `err`, если
             это не объект `Exception`.
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

    raise TypeError(f'Неподдерживаемый тип ошибки: {err!r}')


def simple_msg_err(err: Exception | type[Exception] | str,
                   func_name: str) -> str:
    """Формирует базовое сообщение об ошибке для логирования.

    :param err: Источник информации об ошибке.
    :param func_name: Имя функции, в которой произошла ошибка.
    :return: Отформатированная строка для лога.
    """

    return f'[{func_name}] {get_err_str(err)}'


def annotated_msg_err(err: Exception | type[Exception] | str,
                      func_name: str,
                      err_annotated: str
                      ) -> str:
    """Формирует аннотированное сообщение об ошибке.

    :param err: Объект ошибки.
    :param func_name: Имя функции, в которой произошла ошибка.
    :param err_annotated: Контекст или описание ошибки.
    :return: Отформатированная строка с аннотацией.
    """

    return f'[{func_name}] {err_annotated}: {get_err_str(err)}'


def err_annotated_msg(
        err_a: str | None,
        add_args: bool,
        exclude_args: Iterable[str] | None,
        args: tuple[Any, ...],
        kwargs: Mapping[str, Any]) -> str | None:
    """Формирует аннотацию с опциональными аргументами функции.

    Используется в декораторах для добавления контекста выполнения.

    Примечания:

    - Аргументы логируются как есть, включая их представление через `repr()`.
    - ⚠️ Данные не маскируются — учитывайте это при работе с чувствительной
    информацией.

    :param err_a: Базовое сообщение аннотации. Может быть None.
    :param add_args: Флаг добавления аргументов функции к аннотации.
    :param exclude_args: Перечисленные именованные аргументы будут исключены
                         из выдачи, если используется `add_args`.
    :param args: Позиционные аргументы вызванной функции.
    :param kwargs: Именованные аргументы вызванной функции.
    :returns: None, если нет `err_a` и `add_args=False`, в ином случае
              оформленная строка.
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
