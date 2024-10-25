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
import logging
from logging import Logger
from typing import Callable, Union, Type

from .accessories import is_pure_exc_class, get_simple_or_annotated


def intercept_err_and_log(err: Exception,
                          *,
                          err_annotated: str = None,
                          err_raise: Exception = None,
                          log_obj: Logger,
                          log_level: int = logging.ERROR,
                          from_err: bool = True,
                          source_func: Union[Callable, str] = None,
                          **log_kwargs):
    """
    Функция-перехватчик исключений.

    Основная задача: получить экземпляр класса Exception, сделать запись в
    логи и вызвать исключение заново.

    Должна использоваться в блоке try/except для обработки возникших
    исключений. Плохая практика применять перехватчик, как самостоятельный
    инициатор исключений, хотя формально он эту работу выполнит.

    После обработки переданного экземпляра исключения вызывает исключение
    заново. Если передано err_raise, то err будет подменён на err_raise.

    :param err: Экземпляр Exception (например, самый подходящий вариант - это
                перехваченный в *except Exception as err*).
    :param err_annotated: Иногда мы можем пожелать добавить в log-файл
                          дополнительную аннотацию к ошибке. Например,
                          *"Ошибка чтения json: {err}"*.
    :param err_raise: Целевой экземпляр exception. Если будет передан тип
                      исключения, он будет обработан, но без инициализации
                      окажется неинформативным. Сравним: *raise KeyError*
                      и *raise KeyError('foo')*.
    :param log_obj: Объект Logger, инициализированный в вызывающем модуле.
    :param log_level: Уровень ошибки, при записи в логи через *logger*.
    :param from_err: Опция, которая позволяет сохранять цепочку исключений,
                     при трансформации.
    :param source_func: Вызывающая функция (рекомендуется) или её название.
    :param log_kwargs: Опционально, позиционные аргументы для *Logger*.
    """

    log_err(err,
            err_annotated=err_annotated,
            log_obj=log_obj,
            log_level=log_level,
            source_func=source_func,
            **log_kwargs)

    raise_except(err,
                 err_raise=err_raise,
                 from_err=from_err)


def raise_err_and_log(err: Union[Exception, Type[Exception]],
                      *,
                      err_message: str = None,
                      err_annotated: str = None,
                      log_obj: Logger,
                      log_level: int = logging.ERROR,
                      source_func: Union[Callable, str] = None):
    """
    Инициатор исключения, которое сам и логирует.

    Отличие от метода *intercept_err_and_log*: последний нацелен на перехват
    исключений, а этот метод сам порождает его.

    :param err: Экземпляр исключения или тип класса исключений.
    :param err_message: Если передан тип класса исключений, то он будет
                        инициализирован в экземпляр с err_message.
    :param err_annotated: Опционально, аннотация к исключению при записи в
                          логи.
    :param log_obj: Объект Logger, инициализированный в вызывающем модуле.
    :param log_level: Уровень ошибки, при записи в логи через *logger*.
                      Применяются уровни, предустановленные в logging.
    :param source_func: Вызывающая функция (рекомендуется) или её название.
    """

    exc_err = err
    if is_pure_exc_class(err):
        if err_message:
            exc_err = err(err_message)

    log_err(exc_err,
            err_annotated=err_annotated,
            log_obj=log_obj,
            log_level=log_level,
            source_func=source_func)

    raise_except(exc_err)


def log_err(err_to_log: Union[Exception, Type[Exception], str],
            *,
            err_annotated: str = None,
            log_obj: Logger = None,
            log_level: int = logging.ERROR,
            source_func: Union[Callable, str] = None,
            **log_kwargs):
    """
    Функция делает запись в log-файл, с помощью переданного объекта *Logger*.

    Если опции log_obj и func_name не переданы, они подменяются на дефолтные,
    которыми являются, соответственно, logger из модуля расположения log_err,
    и название функции 'log_err'.

    :param err_to_log: Данные об исключении, которые должны быть логированы.
                       Это может быть текстовая строка, экземпляр исключения
                       (предпочтительно) или чистый класс (тип) исключения
                       (не рекомендуется, так как может быть неинформативно).
                       *Заметка*: при обработке исключения через try/except
                       мы получаем в конструкции *as err* экземпляр исключения.
    :param err_annotated: Иногда мы желаем логировать дополнительную аннотацию
                          к ошибке. Например, *"Ошибка чтения json: {err}"*.
    :param log_obj: Объект Logger. Если не передан, применяется местный объект.
    :param log_level: Уровень ошибки, при записи в логи через *logger*.
    :param source_func: Указатель на вызывающую функцию (буквально, объект
                        функции). Через __name__ извлекается название функции,
                        и учитывается в логировании. Допускается передавать и
                        строковое название, но это плохая практика и ухудшает
                        гибкость под развитие (например, при изменении функции
                        можно пропустить, что в логи отдаётся строковое старое
                        название).
    :param log_kwargs: Опционально, позиционные аргументы для *Logger*.
    """

    def get_log_obj(log):
        if log is None:
            raise_type(AttributeError, msg='Отсутствует объект логирования')
        return log

    def get_func_name(fn):
        if fn is None or not isinstance(fn, (str, Callable)):
            fn = log_err
        if isinstance(fn, Callable):
            return fn.__name__
        return fn

    log_obj, func_name = get_log_obj(log_obj), get_func_name(source_func)

    err_msg: str = get_simple_or_annotated(err_to_log,
                                           func_name,
                                           err_annotated)

    log_obj.log(log_level, err_msg, **log_kwargs)


def raise_except(err: Union[Exception, Type[Exception]],
                 err_raise: Union[Exception, Type[Exception]] = None,
                 from_err: bool = True):
    """
    Функция вызывает переданное исключение.

    :param err: Экземпляр исключения или тип классов исключений. Рекомендуется
                всегда передавать экземпляр, для информативности.
    :param err_raise: Опция, если передано, то вызывается вместо err.
                      Рекомендуется всегда передавать экземпляр.
    :param from_err: Опция, которая позволяет сохранять цепочку исключений,
                     при трансформации (*raise err_raise from err*).
    """

    if err_raise:
        raise err_raise from err if from_err else err_raise

    raise err


def raise_type(err: Type[Exception], *, msg: str = None):
    """
    Функция создаёт исключение и вызывает его, добавляя текст сообщения.

    Красивая обёртка, внедрение которой мотивировано желанием сделать более
    элегантную выдачу исключений. Если погружать текст ошибки сразу в raise,
    то при трассировке стека текст повторяется дважды: при демонстрации части
    кода, где вызвано исключение и собственно само исключение.

    Если оборачивать это через переменную, то текст дважды не демонстрируется,
    однако такая конструкция в коде увеличивает и загромождает код, поэтому
    сделана такая вот обёртка для элегантности.

    :param err: Тип класса исключений.
    :param msg: Текст сообщения об ошибке.
    """

    if not is_pure_exc_class(err):
        # Здесь трассировка сохранена, чтобы упростить поиск ошибки, если
        # функция будет неправильно использована.
        raise TypeError(f'Аргумент {err} должен быть типом исключения, '
                        f'а не экземпляром исключения')

    err_instance: Exception = err(msg) if msg else err()

    raise err_instance
