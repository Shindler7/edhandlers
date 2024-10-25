"""
Декораторы для перехвата и обработки ошибок, включая логирование.
"""
import asyncio
import functools
import logging
from logging import Logger
from typing import Union, Type, Tuple, Callable

from ehandler.except_handlers.accessories import is_pure_exc_class
from ehandler.except_handlers.interfaces import intercept_err_and_log, log_err


def err_interceptor(err_raise: Union[Exception, Type[Exception]] = None,
                    *,
                    err_annotated: str = None,
                    args_to_annotate: bool = False,
                    log_obj: Logger = None,
                    from_err: bool = True,
                    log_level: int = logging.ERROR):
    """
    Универсальный декоратор-перехватчик ошибок.

    В его задачи входит не остановить ошибку, а обработать. При необходимости
    трансформировать в нужный класс исключения, сделать запись в логи и т.д.

    :param err_raise: Экземпляр исключения или тип исключения, который должен
                      быть инициализирован после перехвата. Предпочтительным
                      является для информативности передавать экземпляр
                      исключения. Сравним: *raise KeyError*
                      и *raise KeyError['foo']*. Однако, альтернативным
                      решением является добавление __str__ в класс исключения,
                      тогда сообщение будет выводиться в любом случае.
    :param err_annotated: Иногда мы можем пожелать добавить в log-файл
                          дополнительную аннотацию к ошибке. Например,
                          *"Ошибка чтения json: {err}"*.
    :param args_to_annotate: Декоратор имеет доступ к args и kwargs функции, и
                             если опция активирована, то они будут добавлены к
                             err_annotated.
    :param log_obj: Объект *logger*, инициализированный в модуле вызова.
                    При наличии делается запись запрошенного уровня.
    :param from_err: Опция, которая применяется при трансформации исключения.
                     При включении использует параметр *from err*, что
                     позволяет отследить всю цепочку исключений. Если параметр
                     *raise_exc* не установлен, *from_err* игнорируется.
    :param log_level: Уровень ошибки (исключения) при записи в логи.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            try:

                return _async_or_sync(func, *args, **kwargs)

            except Exception as err:

                err_a: str = _err_annotated_msg(err_annotated,
                                                args_to_annotate,
                                                args, kwargs)
                intercept_err_and_log(err,
                                      err_raise=err_raise,
                                      err_annotated=err_a,
                                      log_obj=log_obj,
                                      log_level=log_level,
                                      from_err=from_err,
                                      source_func=func)

        return wrapper

    return decorator


def raise_if_return(*,
                    exception: Union[Exception, Type[Exception]],
                    err_msg_annotate: str = None,
                    log_obj: Logger,
                    log_level: int = logging.ERROR,
                    raise_by_type: Tuple = (str,),
                    raise_by_none: bool = False):
    """
    Инициатор исключений, при перехвате от обёрнутой функции любых сообщений,
    кроме None.

    Наиболее подходящий вариант использования - валидаторы.

    :param exception: Экземпляр исключения или тип класса исключений. В данном
                      случае *рекомендуется* передавать именно класс, что
                      позволит наиболее чисто инициировать информативные
                      исключения. Экземпляр исключения вызывается без
                      изменений.
    :param err_msg_annotate: Если предоставлено, этот текст подставляется как
                             вводная часть сообщения об ошибке, инициируемого
                             декоратором. Основным текстом ошибки считается
                             возврат (return) от обёрнутой функции. Примерный
                             образец: err_msg_annotate + str(result_from_func).
                             **Важно**: err_msg будет добавлено, если передан
                             тип класса исключений, а если экземпляр, то
                             err_msg_annotate будет отправлено для логирования.
    :param log_obj: Объект *Logger* вызывающего модуля.
    :param log_level: Уровень вывода ошибки в логи.
    :param raise_by_type: Исключение будет вызвано только в том случае, если
                          функция вернула значение указанного типа.
                          По-умолчанию это строка (для возврата текстовых
                          сообщений, которые считаются текстом ошибки).
                          Если перехвачен результат другого типа, он будет
                          возвращён обёрнутой функцией без исключения.
    :param raise_by_none: Опция, при активации которой возврат обёрнутой
                          функцией None расценивается как исключение.
    :raise exception
    """

    def decorator(func: Callable):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            def is_raise(res, r_type: Tuple, r_none: bool) -> bool:
                return isinstance(res, r_type) or (res is None and r_none)

            def get_err_msg(res, e_msg_annotate):
                if e_msg_annotate is None:
                    return str(res)
                return f'{e_msg_annotate}, {res}'

            result = _async_or_sync(func, *args, **kwargs)

            if not is_raise(result, raise_by_type, raise_by_none):
                return result

            err = exception
            if is_pure_exc_class(exception):
                err_msg = get_err_msg(result, err_msg_annotate)
                err = err(err_msg)

            intercept_err_and_log(err,
                                  log_obj=log_obj,
                                  log_level=log_level,
                                  source_func=func)

        return wrapper

    return decorator


def err_log_and_return(*,
                       err_output=None,
                       err_annotated: str = None,
                       args_to_annotate: bool = False,
                       log_obj: Logger = None,
                       log_level: int = logging.ERROR,
                       ):
    """
    Декоратор, который перехватывает исключение, заносит информацию о нём
    в log-файл, а затем не вызывает исключение, а обеспечивает возврат
    обёрнутой функцией объекта, указанного в *err_output*.

    :param err_output: Объект, данные, которые будут возвращены после обработки
                       ошибки, через return обёрнутой функции.
    :param err_annotated: Иногда мы можем пожелать добавить в log-файл
                          дополнительную аннотацию к ошибке. Например,
                          *"Ошибка чтения json: {err}"*.
    :param args_to_annotate: Декоратор имеет доступ к args и kwargs функции, и
                             если опция активирована, то они будут добавлены к
                             err_annotated.
    :param log_obj: Объект *logger*, инициализированный в модуле вызова.
                    При наличии делается запись запрошенного уровня.
    :param log_level: Уровень ошибки (исключения) при записи в логи.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            try:
                return _async_or_sync(func, *args, **kwargs)

            except Exception as err:

                log_err(err,
                        err_annotated=_err_annotated_msg(err_annotated,
                                                         args_to_annotate,
                                                         args, kwargs),
                        log_obj=log_obj,
                        log_level=log_level,
                        source_func=func)

                return err_output

        return wrapper

    return decorator


def _async_or_sync(func: Callable, *args, **kwargs):
    """
    Обёртка позволяющая исключить ситуации, когда декоратор обернул
    асинхронную функцию, а взаимодействует с ней, как с синхронной.

    :param func: Вызываемая декоратором функция.
    :param args: Аргументы для вызываемой функции.
    :param kwargs: Позиционные аргументы для вызываемой функции.
    """

    if asyncio.iscoroutinefunction(func):
        async def async_inner():
            return await func(*args, **kwargs)

        return async_inner()

    return func(*args, **kwargs)


def _err_annotated_msg(err_a: str, add_args: bool, args, kwargs) -> str:
    """
    Поддерживающая функция, которая формирует универсальную строку аннотации
    к сообщению об ошибке, с учётом опции сохранения args и kwargs из обёрнутой
    функции.

    :param err_a: Полученное декоратором сообщение для аннотации.
    :param add_args: Полученное декоратором указание добавлять или нет args
                     и kwargs к аннотации.
    :param args: Аргументы обёрнутой функции.
    :param kwargs: Позиционные аргументы обёрнутой функции.
    """

    if add_args:
        args_kwargs_a: str = f'args={args}, kwargs={kwargs}'
        err_a = f'{err_a} {args_kwargs_a}' if err_a else args_kwargs_a

    return err_a


__all__ = ['err_interceptor', 'err_log_and_return', 'raise_if_return']
