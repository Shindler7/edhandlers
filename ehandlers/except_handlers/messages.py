"""
Подготовка сообщений для логирования исключений.
"""
from typing import Union, Type

from ehandlers.except_handlers.tools import is_exc_instance


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
