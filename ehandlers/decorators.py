"""
Декораторы для перехвата и обработки ошибок, включая логирование.
"""
import functools
import inspect
import logging
from collections.abc import Iterable
from logging import Logger
from typing import Callable, Any, NoReturn

from .except_handlers.handlers import intercept_err_and_log, log_err
from .except_handlers.messages import err_annotated_msg
from .except_handlers.tools import is_exc_type, is_exc_instance


def err_interceptor(err_raise: Exception | type[Exception] | None = None,
                    *,
                    err_annotated: str | None = None,
                    args_to_annotate: bool = False,
                    exclude_args: Iterable[str] | None = None,
                    log_obj: Logger,
                    from_err: bool = True,
                    log_level: int = logging.ERROR):
    """Декоратор для перехвата, логирования и обработки исключений.

    Основная задача — не подавить исключение, а обогатить его обработку:
    трансформировать тип, добавить контекст в логи, сохранить трассировку.
    Исключение перехватывается, логируется и возбуждается повторно — либо
    оригинальное, либо заменённое.

    Примечания:

    - Декоратор работает как с синхронными, так и с асинхронными функциями.
    - При `args_to_annotate=True` в лог попадают позиционные и именованные
    аргументы.

    :param err_raise: Исключение для повторного возбуждения после перехвата.
                      Можно передать:
                      - экземпляр исключения: `ValueError("Неверное значение")`
                      - класс исключения: `ValueError` (будет создан экземпляр)
                      - `None`: будет возбуждено оригинальное исключение.

                      **Рекомендация**: для информативности передавать
                      экземпляр исключения с сообщением об ошибке.
    :param err_annotated: Текстовая аннотация, добавляемая к сообщению в логе.
                          Пример: `"Ошибка десериализации JSON: {err}"`.
    :param args_to_annotate: Если `True`, аргументы декорируемой функции будут
                             добавлены в лог (полезно для отладки). ⚠️ Данные
                             не маскируются — учитывайте это при работе с
                             чувствительной информацией.
    :param exclude_args: Перечисленные аргументы будут исключены из выдачи,
                         если используется `args_to_annotate=True`.
    :param log_obj: Экземпляр логгера (`Logger`). Исключение будет записано
                    с указанным уровнем логирования.
    :param from_err: Сохраняет цепочку исключений при использовании
                     `err_raise`. При `True` используется синтаксис
                     `raise new_err from err`, что сохраняет оригинальный
                     traceback. Игнорируется, если `err_raise` не указан.
    :param log_level: Уровень логирования (константы из модуля `logging`).
                      По умолчанию: `logging.ERROR`.
    """

    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as err:
                    err_a: str | None = err_annotated_msg(err_annotated,
                                                          args_to_annotate,
                                                          exclude_args,
                                                          args, kwargs)
                    intercept_err_and_log(err,
                                          err_raise=err_raise,
                                          err_annotated=err_a,
                                          log_obj=log_obj,
                                          log_level=log_level,
                                          from_err=from_err,
                                          source_func=func)

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as err:
                    err_a: str | None = err_annotated_msg(err_annotated,
                                                          args_to_annotate,
                                                          exclude_args,
                                                          args, kwargs)
                    intercept_err_and_log(err,
                                          err_raise=err_raise,
                                          err_annotated=err_a,
                                          log_obj=log_obj,
                                          log_level=log_level,
                                          from_err=from_err,
                                          source_func=func)

            return sync_wrapper

    return decorator


def raise_if_return(*,
                    exception: Exception | type[Exception],
                    err_msg_annotate: str = None,
                    log_obj: Logger,
                    log_level: int = logging.ERROR,
                    raise_by_type: tuple[Any, ...] = (str,),
                    raise_by_none: bool = False):
    """Возбуждает исключение, если функция возвращает 'ошибочное' значение.

    Используется в валидаторах: если функция вернула строку (или другой
    указанный тип) — это трактуется как сообщение об ошибке и возбуждается
    исключение с этим текстом.

    :param exception: Исключение для возбуждения. Может быть:
                      - классом исключения: `ValueError` (рекомендуется)
                      - экземпляром исключения: `ValueError("Сообщение")`
    :param err_msg_annotate: Дополнительный текст, добавляемый к сообщению
                             исключения. Если передан класс исключения — текст
                             добавляется к результату функции:
                             `f"{err_msg_annotate}: {result}"`. Если передан
                             экземпляр — текст используется только для
                             логирования.
    :param log_obj: Экземпляр логгера для записи возбуждаемых исключений.
    :param log_level: Уровень логирования исключения.
    :param raise_by_type: Кортеж типов, при возврате которых возбуждается
                          исключение. По умолчанию только строки считаются
                          ошибками. Пример: `(str, dict)` — строки и словари.
    :param raise_by_none: Если `True`, возврат `None` также вызывает
                          исключение. По умолчанию `False` — `None`
                          возвращается без ошибки.
    """

    def decorator(func: Callable):

        def is_raise(res, r_type: tuple, r_none: bool) -> bool:
            """Проверка соответствия аргументам декоратора."""
            return isinstance(res, r_type) or (res is None and r_none)

        def get_err_msg(res, e_msg_annotate) -> str:
            """Сформировать сообщение об ошибке."""
            if e_msg_annotate is None:
                return str(res)
            return f'{e_msg_annotate}, {res}'

        def raise_error(result_func: Any) -> NoReturn:
            """Выбросить исключение."""
            if is_exc_type(exception):
                err_msg = get_err_msg(result_func, err_msg_annotate)
                err: Exception = exception(err_msg)
            elif is_exc_instance(exception):
                err: Exception = exception  # noqa: заглушка для PyCharm.
            else:
                raise TypeError('exception должен быть в классе исключений')

            intercept_err_and_log(err,
                                  log_obj=log_obj,
                                  log_level=log_level,
                                  source_func=func)

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                if is_raise(result, raise_by_type, raise_by_none):
                    raise_error(result)
                else:
                    return result

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                if is_raise(result, raise_by_type, raise_by_none):
                    raise_error(result)
                else:
                    return result

            return sync_wrapper

    return decorator


def err_log_and_return(*,
                       err_output: Any | None = None,
                       err_annotated: str | None = None,
                       args_to_annotate: bool = False,
                       exclude_args: Iterable[str] | None = None,
                       log_obj: Logger,
                       log_level: int = logging.ERROR,
                       ):
    """Декоратор, который перехватывает исключения, логирует их и возвращает
    заданное значение.

    Основное отличие от `err_interceptor` — исключение не возбуждается
    повторно, а функция возвращает заранее определённое значение `err_output`.
    Это полезно в сценариях, где ошибка не должна прерывать выполнение
    программы, но требует фиксации в логах.

    :param err_output: Значение, возвращаемое функцией при возникновении
                       исключения. Может быть любого типа. По умолчанию `None`.
    :param err_annotated: Дополнительный текст, добавляемый к сообщению в логе.
                          Может содержать `{err}` для подстановки текста
                          исключения. Пример: `"Не удалось загрузить
                          конфигурацию: {err}"`.
    :param args_to_annotate: Если `True`, имена аргументов функции добавляются
                             в лог. ⚠️ Данные не маскируются — учитывайте это
                             при работе с чувствительной информацией.
    :param exclude_args: Перечисленные аргументы будут исключены из выдачи,
                         если используется `args_to_annotate=True`.
    :param log_obj: Экземпляр логгера для записи исключений.
    :param log_level: Уровень логирования исключения.
    """

    def decorator(func):

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)

                except Exception as err:
                    log_err(err,
                            err_annotated=err_annotated_msg(err_annotated,
                                                            args_to_annotate,
                                                            exclude_args,
                                                            args, kwargs),
                            log_obj=log_obj,
                            log_level=log_level,
                            source_func=func)

                    return err_output

            return async_wrapper

        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)

                except Exception as err:
                    log_err(err,
                            err_annotated=err_annotated_msg(err_annotated,
                                                            args_to_annotate,
                                                            exclude_args,
                                                            args, kwargs),
                            log_obj=log_obj,
                            log_level=log_level,
                            source_func=func)

                    return err_output

            return sync_wrapper

    return decorator


__all__ = ['err_interceptor', 'err_log_and_return', 'raise_if_return']
