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
    raise_err_and_log(MyError, logger, msg_err = 'Неправильный ключ')

Затем централизовано обрабатывать подобные исключения и логировать их единым
образом.
"""

import logging
import os
import traceback
import warnings
from collections.abc import Callable
from logging import Logger
from traceback import StackSummary
from typing import Any, NoReturn

from .messages import get_simple_or_annotated
from .tools import is_exc_type

_LIB_DIR_NAME: str = 'ehandlers'
"""Название директории с кодом библиотеки."""

MISSING = object()


def intercept_err_and_log(
    err: Exception,
    *,
    err_annotated: str | None = None,
    err_raise: Exception | type[Exception] | None = None,
    log: Logger = MISSING,
    log_obj: Logger = MISSING,
    log_level: int = logging.ERROR,
    from_err: bool = True,
    source_func: Callable | str | None = None,
    **log_kwargs: Any,
) -> NoReturn:
    """Перехватывает, логирует и повторно возбуждает исключение.

    Основное назначение — обработка исключений в блоках `try/except` с
    добавлением контекста в логи и возможностью трансформации типа исключения.

    Args:
        err (Exception): Перехваченное исключение. Должен быть экземпляром,
            не классом. Пример: `except ValueError as err:` → `err`.
        err_annotated: Дополнительный текст, уточняющий текст ошибки.
        err_raise: Исключение для возбуждения вместо оригинального `err`. Может быть
            типом исключения, либо его экземпляром.
        log: Экземпляр логгера для записи исключения (обязательный). Рекомендуется
            передавать логгер текущего модуля.
        log: Экземпляр логгера для записи исключения
            (обязательный). Рекомендуется передавать логгер текущего модуля.
        log_obj: Устаревший аргумент. Используйте вместо
            него `log`. Будет удален в будущих версиях.
        log_level: Уровень логирования. По умолчанию: `logging.ERROR`.
        from_err: Если `True` и указан `err_raise`, сохраняет цепочку
            исключений: `raise new_err from old_err`. Полезно для отладки,
            чтобы видеть оригинальную причину.
        source_func: Функция, в которой произошла ошибка.
            Если не указано, имя определяется автоматически через `traceback`.
        log_kwargs: Дополнительные аргументы для логгера.

    Raises:
        Exception: Повторно возбуждает оригинальное исключение `err` или новое,
            переданное в `err_raise`.
    """

    log_err(
        err,
        err_annotated=err_annotated,
        log=log,
        log_obj=log_obj,
        log_level=log_level,
        source_func=source_func,
        **log_kwargs,
    )

    raise_except(err, err_raise=err_raise, from_err=from_err)


def raise_err_and_log(
    err: Exception | type[Exception],
    *,
    err_message: str | None = None,
    err_annotated: str | None = None,
    log: Logger = MISSING,
    log_obj: Logger = MISSING,
    log_level: int = logging.ERROR,
    source_func: Callable | str | None = None,
) -> NoReturn:
    """Создаёт, логирует и возбуждает исключение.

    В отличие от `intercept_err_and_log`, который перехватывает существующие
    исключения, эта функция сама создаёт и возбуждает их.

    Args:
        err: Исключение для возбуждения.
        err_message: Сообщение для исключения, если передан класс.
            Игнорируется, если передан экземпляр.
        err_annotated: Дополнительный контекст для логирования.
            Пример: `"Ошибка валидации пользователя"`.
        log: Экземпляр логгера для записи исключения (обязательный).
            Рекомендуется передавать логгер текущего модуля.
        log_obj: Устаревший аргумент. Используйте вместо
            него `log`. Будет удален в будущих версиях.
        log_level: Уровень логирования. По умолчанию: `logging.ERROR`.
        source_func: Функция, в которой произошла ошибка.
            Если не указано, имя определяется автоматически через `traceback`.

    Raises:
        Exception: Возбуждает переданное или созданное исключение `err`.
    """

    exc_err = (err(err_message) if err_message else err()) if is_exc_type(err) else err

    log_err(
        exc_err,
        err_annotated=err_annotated,
        log=log,
        log_obj=log_obj,
        log_level=log_level,
        source_func=source_func,
    )

    raise exc_err


def log_err(
    err_to_log: Exception | type[Exception] | str,
    *,
    err_annotated: str | None = None,
    log: Logger = MISSING,
    log_obj: Logger = MISSING,
    log_level: int = logging.ERROR,
    source_func: Callable | str | None = None,
    **log_kwargs: Any,
) -> None:
    """Логирует исключение или сообщение об ошибке с контекстом.

    Универсальная функция для структурированного логирования ошибок с
    автоматическим определением контекста и поддержкой различных форматов
    ошибок.

    Args:
        err_to_log: Информация об ошибке для логирования.
        err_annotated: Дополнительный текст, уточняющий контекст ошибки.
        log: Экземпляр логгера для записи исключения (обязательный).
            Рекомендуется передавать логгер текущего модуля.
        log_obj: Устаревший аргумент. Используйте вместо него `log`.
            Будет удален в будущих версиях.
        log_level: Уровень логирования из модуля `logging`. По умолчанию:
            `logging.ERROR`.
        source_func: Функция, в которой произошла ошибка. Если не указано,
            имя определяется автоматически через `traceback`.
        log_kwargs: Дополнительные аргументы для логгера.
    """

    if log_obj is not MISSING:
        warnings.warn(
            'Аргумент `log_obj` устарел и будет удалён в версии `0.6.0`. '
            'Используйте `log`.',
            DeprecationWarning,
            stacklevel=2,
        )

    # Логгер ожидается из атрибута `log`.
    log_obj: Any = log if isinstance(log, Logger) else log_obj

    # Выявляем вид информации об ошибке (исключении).
    if isinstance(err_to_log, (Exception, str)):
        err_info = err_to_log
    else:
        err_info = err_to_log.__name__

    # Определение имени вызывающей функции.
    if source_func is None:
        stack: StackSummary = traceback.extract_stack()

        func_name: str = '<function>'
        for frame_info in reversed(stack):
            if f'{os.path.sep}{_LIB_DIR_NAME}{os.path.sep}' not in frame_info.filename:
                func_name = frame_info.name
                break

    else:
        if isinstance(source_func, str):
            func_name = source_func
        elif callable(source_func):
            func_name = getattr(source_func, '__name__', str(source_func))
        else:
            func_name = '<неизвестно>'

    # Проверка объекта логирования.
    if not isinstance(log_obj, Logger):
        raise TypeError(
            'Отсутствует объект логирования (атрибут `log`). '
            f'Функция: {func_name}, исключение: {err_info}'
        )

    err_msg: str = get_simple_or_annotated(err_to_log, func_name, err_annotated)

    # Записываем в логи результат.
    log_obj.log(log_level, err_msg, **log_kwargs)


def raise_except(
    err: Exception | type[Exception],
    err_raise: Exception | type[Exception] | None = None,
    from_err: bool = True,
) -> NoReturn:
    """Возбуждает исключение, с возможностью замены типа и сохранения контекста.

    Универсальная утилита для работы с исключениями, позволяющая:
    1. Возбудить исключение как есть.
    2. Заменить одно исключение другим с сохранением исходного как причины.
    3. Заменить исключение без сохранения контекста.

    Args:
        err: Исходное исключение. Может быть экземпляром или классом Exception.
        err_raise: Исключение для возбуждения вместо `err`. Если не указано,
            возбуждается `err`. Формат аналогичен `err`.
        from_err: Если `True` и указан `err_raise`, используется синтаксис
            `raise new_exc from old_exc`, сохраняющий цепочку исключений.
            Если `False` — контекст теряется.

    Raises:
        Exception: Возбуждает переданное или сформированное исключение.
    """

    if is_exc_type(err):
        err = err()

    if err_raise is not None:
        if is_exc_type(err_raise):
            err_raise = err_raise()

        if from_err:
            raise err_raise from err
        raise err_raise from None

    raise err
