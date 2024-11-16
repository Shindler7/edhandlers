"""
Поддерживающие функции для интерфейса перехвата и логирования исключений.
"""
import inspect
import logging
from logging import Logger
from typing import Any


def get_logger(logger_name: str = 'logger') -> Logger:
    """
    Создаёт объект logger, если он не определён в модуле.
    """

    log_obj: Logger = globals().get(logger_name)

    if log_obj is None:
        log_obj: Logger = logging.getLogger(__name__)

    return log_obj


"""
Записи на полях.

.. code-block:: pycon

    >>> isinstance(KeyError, Exception)
    False
    >>> str(KeyError)
    <class 'KeyError'>
    >>>
    >>>
    >>> try:
    ...     j['boo']
    ... except KeyError as e:
    ...     type(e)
    ...     print(e)
    ...     isinstance(e, Exception)
    ...
    <class 'KeyError'>
    'boo'
    True
    >>>

"""


def is_exception(obj: Any) -> bool:
    """
    Объект является любым видом исключения?

    :param obj: Проверяемый объект.
    :return: True|False.
    """

    return is_exc_instance(obj) or is_exc_type(obj)


def is_exc_type(obj: Any) -> bool:
    """
    Это объект типа класса исключений?

    :param obj: Проверяемый объект.
    :return: True|False.
    """

    is_instance = is_exc_instance(obj)
    is_exc_class = inspect.isclass(obj) and issubclass(obj, Exception)

    return not is_instance and is_exc_class


def is_exc_instance(obj: Any) -> bool:
    """
    Это экземпляр исключения?

    :param obj: Проверяемый объект.
    :return: True|False.
    """

    return isinstance(obj, Exception)
