"""
Поддерживающие функции для интерфейса перехвата и логирования исключений.
"""
import inspect
import logging
from logging import Logger
from typing import Union, Type, Any


def get_logger(logger_name: str = 'logger') -> logging.Logger:
    """
    Создаёт объект logger, если он не определён в модуле.
    """

    log_obj: Logger = globals().get(logger_name)

    if log_obj is None:
        log_obj: Logger = logging.getLogger(__name__)

    return log_obj


def get_simple_or_annotated(err: Union[Exception, Type[Exception], str],
                            func_name: str,
                            err_annotated: str = None) -> str:
    """
    Определяет какой шаблон наиболее подходящий с учётом переданных аттрибутов,
    и возвращает соответствующий строковый результат информации об ошибке.

    :param err: Сообщение об ошибке или алиас для обработанного исключения
                или само исключение.
    :param func_name: Название инициирующей исключение функцией.
    :param err_annotated: Аннотация для дополнительного описания ошибки.
    :return: Сформированная строка для публикации в log-файл.
    """

    if err_annotated is None:
        return simple_msg_err(err, func_name)

    return annotated_msg_err(err, func_name, err_annotated)


def get_err_str(err: Union[Exception, Type[Exception]]):
    """
    Формирует типовую строку на основе данных об исключении, предоставленном
    им самим.

    :param err: Объект класса исключений.
    :return: Строковый результат распаковки Exception или аттрибут *err*,
             обратно, если он является строкой или не является Exception.
    """

    if is_exc_instance(err):
        return f'{err.__class__.__name__}: {err}'

    return err


def simple_msg_err(err: Union[Exception, Type[Exception], str],
                   func_name: str
                   ) -> str:
    """
    Самая простая строка для отражения информации об ошибке.

    :param err: Сообщение об ошибке или алиас для обработанного исключения
                или само исключение.
    :param func_name: Название инициирующей исключение функцией.
    :return: Сформированная строка для публикации в log-файл.
    """

    return f'<{func_name}> {get_err_str(err)}'


def annotated_msg_err(err: Union[Exception, Type[Exception], str],
                      func_name: str,
                      err_annotated: str
                      ) -> str:
    """
    Текст логирования ошибки с аннотацией.

    :param err: Сообщение об ошибке или алиас для обработанного исключения
                или само исключение.
    :param func_name: Название инициирующей исключение функцией.
    :param err_annotated: Аннотация для дополнительного описания ошибки.
    :return: Сформированная строка для публикации в log-файл.
    """

    return f'<{func_name}> {err_annotated}: {get_err_str(err)}'


def custom_msg_err(err: Union[Exception, Type[Exception], str],
                   func_name: str,
                   template_msg_err: str,
                   **template_context
                   ) -> str:
    """
    Экспериментальный вариант формирования сообщения об ошибке. Может
    использоваться там, где нужно выдать более сложное и насыщенное сообщение,
    либо произвольно расположить данные.

    Например: 'Всем {err}! {func_name} вызывает {today} вечеринку {func_name}'.

    Благодаря template_context можно использовать любое количество
    дополнительных позиционных аргументов для шаблона, в дополнение к
    обязательным. **Важно** не забывать ключи или не делать лишние ключи,
    которых нет в шаблоне. Правила для метода *.format()*.

    Принцип работы следующий: template_msg_err.format(**template_context).

    :param err: Сообщение об ошибке или исключение. *Обязательное присутствие
                в шаблоне*.
    :param func_name: Название инициирующей исключение функцией. *Обязательное
                      присутствие в шаблоне*.
    :param template_msg_err: Шаблон для сообщения, который должен включать
                             ключи для обязательных элементов и предусмотренных
                             *template_context*.
    :param template_context: Любое количество позиционных аргументов, которые
                             должны быть отражены в шаблоне сообщения.
    :return: Сформированная строка для публикации в log-файл.
    """

    template_context.setdefault('err', err)
    template_context.setdefault('func_name', func_name)

    return template_msg_err.format(**template_context)


"""
Записи на полях для себя будущего, который всё это забудет.

Если коротко, на примере KeyError:
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
    Проверка, что объект в принципе является любым видом исключения.

    :param obj: Проверяемый тип класса исключений.
    :return: Логический тип.
    """
    return is_exc_instance(obj) or is_pure_exc_class(obj)


def is_pure_exc_class(obj: Any) -> bool:
    """
    Инспектируем объект на принадлежность к классу Exception, но при этом,
    что уже не является экземпляром Exception.

    :param obj: Проверяемый тип класса исключений.
    :return: Логический тип.
    """

    is_instance = is_exc_instance(obj)
    is_exc_class = inspect.isclass(obj) and issubclass(obj, Exception)

    return not is_instance and is_exc_class


def is_exc_instance(obj: Any) -> bool:
    """
    Проверяем, что это экземпляр Exception.

    :param obj: Проверяемый объект класса исключений.
    :return: Логический тип.
    """

    return isinstance(obj, Exception)
