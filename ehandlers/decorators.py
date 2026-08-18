"""
Декораторы для перехвата и обработки ошибок, включая логирование.
"""

import functools
import inspect
import logging
from collections.abc import Callable, Iterable
from logging import Logger
from typing import Any, NoReturn, TypeVar

from .except_handlers.handlers import MISSING, intercept_err_and_log, log_err
from .except_handlers.messages import err_annotated_msg
from .except_handlers.tools import is_exc_type

F = TypeVar('F', bound=Callable[..., Any])

__all__ = ['err_interceptor', 'err_log_and_return', 'raise_if_return']


def err_interceptor(
    err_raise: Exception | type[Exception] | None = None,
    *,
    err_annotated: str | None = None,
    args_to_annotate: bool = False,
    exclude_args: Iterable[str] | None = None,
    log: Logger = MISSING,
    log_obj: Logger = MISSING,
    from_err: bool = True,
    log_level: int = logging.ERROR,
) -> Callable[[F], F]:
    """Декоратор для перехвата, логирования и обработки исключений.

    Основная задача — не подавить исключение, а обогатить его обработку:
    трансформировать тип, добавить контекст в логи, сохранить трассировку.
    Исключение перехватывается, логируется и возбуждается повторно — либо
    оригинальное, либо заменённое.

    Декоратор универсален: корректно работает как с синхронными, так и с
    асинхронными функциями (`async def`).

    Warnings:
        Данные аргументов не маскируются при `args_to_annotate=True`.
        Учитывайте это при работе с конфиденциальной информацией.

    Args:
        log: Экземпляр логгера для записи исключения.
        err_raise: Исключение для повторного возбуждения после перехвата.
            Может быть классом (`ValueError`), готовым экземпляром
            (`ValueError("Текст")`) или `None` (выбросит оригинал).
        err_annotated: Дополнительный текст к логу.
        args_to_annotate: Если True, позиционные и именованные аргументы
            декорируемой функции будут добавлены в лог для отладки.
        exclude_args: Список имён аргументов, которые нужно скрыть из лога,
            если включен параметр `args_to_annotate`.
        from_err: Сохраняет цепочку исключений при замене (`raise new_err from err`).
            Если False, оригинальный traceback скрывается. Игнорируется, если
            `err_raise` равен `None`.
        log_level: Уровень логирования (константы из модуля `logging`).
        log_obj: Устаревший аргумент. Используйте вместо него `log`.

    Returns:
        Декоратор для функции.
    """

    def decorator(func: F) -> F:
        is_async: bool = inspect.iscoroutinefunction(inspect.unwrap(func))

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except Exception as err:
                    err_a: str | None = err_annotated_msg(
                        err_annotated, args_to_annotate, exclude_args, args, kwargs
                    )
                    intercept_err_and_log(
                        err,
                        err_raise=err_raise,
                        err_annotated=err_a,
                        log=log,
                        log_obj=log_obj,
                        log_level=log_level,
                        from_err=from_err,
                        source_func=func,
                    )

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as err:
                    err_a: str | None = err_annotated_msg(
                        err_annotated, args_to_annotate, exclude_args, args, kwargs
                    )
                    intercept_err_and_log(
                        err,
                        err_raise=err_raise,
                        err_annotated=err_a,
                        log=log,
                        log_obj=log_obj,
                        log_level=log_level,
                        from_err=from_err,
                        source_func=func,
                    )

            return sync_wrapper

    return decorator


def raise_if_return(
    *,
    exception: Exception | type[Exception],
    err_msg_annotate: str | None = None,
    log: Logger = MISSING,
    log_obj: Logger = MISSING,
    log_level: int = logging.ERROR,
    raise_by_type: tuple[type[Any], ...] = (str,),
    raise_by_none: bool = False,
) -> Callable[[F], F]:
    """Возбуждает исключение, если функция возвращает 'ошибочное' значение.

    Используется в валидаторах: если функция вернула строку (или другой
    указанный тип) — это трактуется как сообщение об ошибке и возбуждается
    исключение с этим текстом.

    Args:
        log: Экземпляр логгера для записи исключения.
        exception: Исключение для возбуждения. Может быть классом исключения
            (например, `ValueError`) или готовым экземпляром (`ValueError("Ошибка")`).
        err_msg_annotate: Дополнительный текст, добавляемый к сообщению.
            Если передан класс исключения, текст добавится к результату функции:
            `f'{err_msg_annotate}: {result}'`. Если передан экземпляр — текст
            используется только для логирования.
        log_level: Уровень логирования исключения.
        raise_by_type: Кортеж типов, при возврате которых возбуждается исключение.
            По умолчанию только строки (`str`) считаются ошибками.
        raise_by_none: Если True, возврат `None` также вызывает исключение.
        log_obj: Устаревший аргумент. Используйте вместо него `log`.

    Returns:
        Декоратор для функции.
    """

    def decorator(func: F) -> F:

        def is_raise(res: Any, r_type: tuple[type[Any], ...], r_none: bool) -> bool:
            """Проверка соответствия аргументам декоратора."""
            return isinstance(res, r_type) or (res is None and r_none)

        def raise_error(result_func: Any) -> NoReturn:
            """Выбросить исключение."""

            err_annotate: str | None = err_msg_annotate

            if is_exc_type(exception):
                if err_annotate is None:
                    err_msg: str = str(result_func)
                else:
                    err_msg: str = f'{err_annotate}, {result_func}'

                err: Exception = exception(err_msg)
                err_annotate = None

            elif isinstance(exception, Exception):
                err: Exception = exception

            else:
                raise TypeError('`exception` должен быть из класса исключений')

            intercept_err_and_log(
                err,
                err_annotated=err_annotate,
                log=log,
                log_obj=log_obj,
                log_level=log_level,
                source_func=func,
            )

        is_async: bool = inspect.iscoroutinefunction(inspect.unwrap(func))

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                result = await func(*args, **kwargs)
                if is_raise(result, raise_by_type, raise_by_none):
                    raise_error(result)
                return result

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                result = func(*args, **kwargs)
                if is_raise(result, raise_by_type, raise_by_none):
                    raise_error(result)
                return result

            return sync_wrapper

    return decorator


def err_log_and_return(
    *,
    err_output: Any | None = None,
    err_annotated: str | None = None,
    args_to_annotate: bool = False,
    exclude_args: Iterable[str] | None = None,
    log: Logger = MISSING,
    log_obj: Logger = MISSING,
    log_level: int = logging.ERROR,
) -> Callable[[F], F]:
    """Декоратор, который перехватывает исключения, логирует их и возвращает
    заданное значение.

    Основное отличие от `err_interceptor` — исключение не возбуждается
    повторно, а функция возвращает заранее определённое значение `err_output`.
    Это полезно в сценариях, где ошибка не должна прерывать выполнение.

    Warnings:
        Данные аргументов не маскируются при `args_to_annotate=True`.
        Учитывайте это при работе с чувствительной информацией.

    Args:
        log: Экземпляр логгера для записи исключения.
        err_output: Значение, возвращаемое функцией при возникновении исключения.
        err_annotated: Дополнительный текст к логу.
        args_to_annotate: Если True, имена аргументов функции добавляются в лог.
        exclude_args: Список аргументов, которые будут исключены из лога.
        log_level: Уровень логирования исключения.
        log_obj: Устаревший аргумент. Используйте вместо него `log`.

    Returns:
        Декоратор для функции.
    """

    def decorator(func: F) -> F:

        is_async: bool = inspect.iscoroutinefunction(inspect.unwrap(func))

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)

                except Exception as err:
                    log_err(
                        err,
                        err_annotated=err_annotated_msg(
                            err_annotated, args_to_annotate, exclude_args, args, kwargs
                        ),
                        log=log,
                        log_obj=log_obj,
                        log_level=log_level,
                        source_func=func,
                    )

                    return err_output

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)

                except Exception as err:
                    log_err(
                        err,
                        err_annotated=err_annotated_msg(
                            err_annotated, args_to_annotate, exclude_args, args, kwargs
                        ),
                        log=log,
                        log_obj=log_obj,
                        log_level=log_level,
                        source_func=func,
                    )

                    return err_output

            return sync_wrapper

    return decorator
