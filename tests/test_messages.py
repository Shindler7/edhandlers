"""Тестирование корректности аннотирования информации."""

import ast
import re

from ehandlers.except_handlers.messages import err_annotated_msg


def test_err_annotated_msg_valid_full():
    """Проверка корректности формирования аннотации с полным набором опций."""

    err_a = 'Test'
    args = (1, 2, 3)
    kwargs = {'a': 4, 'b': 5}

    result: str | None = err_annotated_msg(
        err_a, True, None, args, kwargs)

    assert result is not None, 'Результат не должен быть None'
    assert err_a in result, 'Базовое сообщение не найдено в результате'
    assert repr(args) in result, 'Аргументы отсутствуют в выдаче'
    assert repr(kwargs) in result, 'Именованные аргументы не найдены'


def test_err_annotated_msg_not_args():
    """Проверка, что срабатывает отключенный add_args."""

    err_a = 'Test'
    args = (1, 2, 3)

    result = err_annotated_msg(err_a, False, None, args, {})

    assert result is not None, 'Результат не должен быть None'
    assert result == err_a, 'Результат должен быть точной копией аннотации'


def test_err_annotated_msg_exclude_args():
    """Проверка, что исключенные именованные аргументы не попадают в выдачу."""

    err_a = 'Test'
    kwargs = {'a': 4, 'b': 5, 'c': 6, 'd': 7}
    exclude = ['a', 'b']

    result = err_annotated_msg(err_a, True, exclude, (), kwargs)

    # "Test | args=(), kwargs={'c': 6, 'd': 7}"
    assert result is not None, 'Результат не должен быть None'

    # Извлекаем словарь.
    m = re.search(r"kwargs=(\{.*})$", result)
    assert m, 'Словарь не найден в финальной аннотации'
    kwargs_re = ast.literal_eval(m.group(1))

    for k in kwargs.keys():
        if k in exclude:
            assert k not in kwargs_re
        else:
            assert k in kwargs_re
