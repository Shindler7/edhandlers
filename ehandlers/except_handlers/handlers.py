"""
Инструменты для обработки и логирования исключений.

Настройка автоматического логирования создаваемых исключений.
При необходимости, здесь же можно создавать специальные переопределения
стандартных методов логирования Django.

Мотивация: в разных частях всего проекта требуется регулярно вызывать
исключения, и правильно их сразу логировать. Сейчас для этого нужно создавать
громоздкую конструкцию, например:

try:
    t = base['key']
except KeyError as e:
    err_msg = 'Неправильный ключ {e}'.format(e=e)
    logger.warning(f'<func_name> {err_msg}')
    raise MyError(err_msg) from e

При таком подходе нужно не забыть добавить логирование, раздать всем сообщение,
а это увеличивает и усложняет код. Главное же, что везде логирование
осуществляется индивидуально. Можно так:

import logging
logger = logging.getLogger(__name__)

try:
    t = base['key']
except KeyError as e:
    raise_err_and_log(MyError, logger, msg_err='Неправильный ключ')

Затем централизовано обрабатывать подобные исключения и логировать их единым
образом.
"""
import inspect
import logging
from logging import Logger
from typing import Callable, NoReturn

from .messages import get_simple_or_annotated
from .tools import is_exc_type


def intercept_err_and_log(err: Exception,
                          *,
                          err_annotated: str | None = None,
                          err_raise: Exception | None = None,
                          log_obj: Logger,
                          log_level: int = logging.ERROR,
                          from_err: bool = True,
                          source_func: Callable | str | None = None,
                          **log_kwargs) -> NoReturn:
    """Перехватывает, логирует и повторно возбуждает исключение.

    Основное назначение — обработка исключений в блоках `try/except` с
    добавлением контекста в логи и возможностью трансформации типа исключения.

    :param err: Перехваченное исключение. Должен быть экземпляром, не классом.
                Пример: `except ValueError as e:` → `e`.
    :param err_annotated: Дополнительный текст, уточняющий контекст ошибки.
                          Может содержать `{err}` для подстановки.
                          Пример: `"Не удалось десериализовать JSON: {err}"`
    :param err_raise: Исключение для возбуждения вместо `err`.
    :param log_obj: Экземпляр логгера для записи исключения (обязательный).
    :param log_level: Уровень логирования. По умолчанию: `logging.ERROR`.
    :param from_err: Если `True` и указан `err_raise`, сохраняет цепочку
                     исключений: `raise new_err from old_err`.
                     Полезно для отладки, чтобы видеть оригинальную причину.
    :param source_func: Функция, в которой произошла ошибка. Если не указано,
                        имя определяется автоматически через `inspect`.
    :param log_kwargs: Дополнительные аргументы для метода `log()`.
    """

    if source_func is None:
        fn_back = inspect.currentframe().f_back
        source_func = inspect.getframeinfo(fn_back).function

    log_err(err,
            err_annotated=err_annotated,
            log_obj=log_obj,
            log_level=log_level,
            source_func=source_func,
            **log_kwargs)

    raise_except(err, err_raise=err_raise, from_err=from_err)


def raise_err_and_log(err: Exception | type[Exception],
                      *,
                      err_message: str | None = None,
                      err_annotated: str | None = None,
                      log_obj: Logger,
                      log_level: int = logging.ERROR,
                      source_func: Callable | str | None = None) -> NoReturn:
    """Создаёт, логирует и возбуждает исключение.

    В отличие от `intercept_err_and_log`, который перехватывает существующие
    исключения, эта функция сама создаёт и возбуждает их.

    :param err: Исключение для возбуждения.
    :param err_message: Сообщение для исключения, если передан класс.
                        Игнорируется, если передан экземпляр.
    :param err_annotated: Дополнительный контекст для логирования.
                          Пример: `"Ошибка валидации пользователя"`.
    :param log_obj: Экземпляр логгера для записи исключения (обязательный).
    :param log_level: Уровень логирования. По умолчанию: `logging.ERROR`.
    :param source_func: Функция, в которой произошла ошибка. Если не указано,
                        имя определяется автоматически через `inspect`.
    """

    if source_func is None:
        fn_back = inspect.currentframe().f_back
        source_func = inspect.getframeinfo(fn_back).function

    if is_exc_type(err):
        exc_err = err(err_message) if err_message else err()
    else:
        exc_err = err

    log_err(exc_err,
            err_annotated=err_annotated,
            log_obj=log_obj,
            log_level=log_level,
            source_func=source_func)

    raise exc_err


def log_err(err_to_log: Exception | type[Exception] | str,
            *,
            err_annotated: str | None = None,
            log_obj: Logger,
            log_level: int = logging.ERROR,
            source_func: Callable | str | None = None,
            **log_kwargs) -> None:
    """Логирует исключение или сообщение об ошибке с контекстом.

    Универсальная функция для структурированного логирования ошибок с
    автоматическим определением контекста и поддержкой различных форматов
    ошибок.

    :param err_to_log: Информация об ошибке для логирования.
    :param err_annotated: Дополнительный текст, уточняющий контекст ошибки.
    :param log_obj: Экземпляр логгера. Если не удаётся определить —
                    возбуждается `AttributeError`.
    :param log_level: Уровень логирования из модуля `logging`. По умолчанию:
                      `logging.ERROR`.
    :param source_func: Функция, в которой произошла ошибка. Если не указано,
                        имя определяется автоматически через `inspect`.
    :param log_kwargs: Дополнительные аргументы для метода `log()` логгера.
    """

    def get_log_obj(log):
        if log is None or not isinstance(log, Logger):
            raise AttributeError(
                f'log_err: отсутствует объект логирования. '
                f'Функция: {func_name}, ошибка: {err_to_log}'
            )
        return log

    def get_func_name(fn):
        if not isinstance(fn, (str, Callable)):
            fn = log_err
        if isinstance(fn, Callable):
            return fn.__name__
        return fn

    # Определение имени вызывающей функции
    if source_func is None:
        try:
            current_frame = inspect.currentframe()
            fn_back = current_frame.f_back
            func_name = inspect.getframeinfo(fn_back).function
        finally:
            del current_frame
    else:
        func_name = get_func_name(source_func)

    # Получение объекта логирования.
    log_obj = get_log_obj(log_obj)

    err_msg: str = get_simple_or_annotated(
        err_to_log, func_name, err_annotated)

    log_obj.log(log_level, err_msg, **log_kwargs)


def raise_except(err: Exception | type[Exception],
                 err_raise: Exception | type[Exception] | None = None,
                 from_err: bool = True) -> NoReturn:
    """Возбуждает исключение, с возможностью замены типа и сохранения
    контекста.

    Универсальная утилита для работы с исключениями, позволяющая:
    1. Возбудить исключение как есть.
    2. Заменить одно исключение другим с сохранением исходного как причины.
    3. Заменить исключение без сохранения контекста.

    :param err: Исходное исключение. Может быть экземпляром или классом
                Exception.
    :param err_raise: Исключение для возбуждения вместо `err`. Если не указано,
                      возбуждается `err`. Формат аналогичен `err`.
    :param from_err: Если `True` и указан `err_raise`, используется синтаксис
                     `raise new_exc from old_exc`, сохраняющий цепочку
                     исключений. Если `False` — контекст теряется.
    """

    if is_exc_type(err):
        err = err()
    if err_raise and is_exc_type(err_raise):
        err_raise = err_raise()

    if err_raise:
        raise err_raise from err if from_err else err_raise

    raise err


def raise_type(err: type[Exception], *, msg: str = None) -> NoReturn:
    """Создаёт и возбуждает исключение указанного типа.

    Утилита для чистого возбуждения исключений без лишней трассировки в логах.
    В отличие от прямого `raise ValueError("message")`, этот метод создаёт
    более чистый traceback, исключая дублирование информации.

    :param err: Класс исключения для возбуждения (например, `ValueError`).
    :param msg: Текст сообщения исключения. Если не указан, используется
                пустая строка или значение по умолчанию для класса исключения.
    :raises TypeError: Если переданный `err` не является классом исключения.
    """

    if not is_exc_type(err):
        # Сохраняем трассировку для отладки неправильного использования.
        raise TypeError(f'{err} должен быть типом класса исключений')

    err_instance: Exception = err(msg) if msg else err()

    raise err_instance
