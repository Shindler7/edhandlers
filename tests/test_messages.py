"""Тестирование корректности аннотирования информации."""

import ast
import re

from ehandlers.except_handlers.messages import err_annotated_msg


def wrapper_func() -> None:
    pass


def test_err_annotated_msg_valid_full() -> None:
    """Проверка корректности формирования аннотации с полным набором опций."""

    err_a: str = 'Test'
    args: tuple[int, ...] = (1, 2, 3)
    kwargs: dict[str, int] = {'a': 4, 'b': 5}

    result: str | None = err_annotated_msg(
        err_a,
        add_args=True,
        exclude_args=False,
        exclude_self=True,
        exclude_kwargs=None,
        func=wrapper_func,
        args=args,
        kwargs=kwargs,
    )

    assert result is not None, 'Результат не должен быть None'
    assert err_a in result, 'Базовое сообщение не найдено в результате'
    assert repr(args) in result, 'Аргументы отсутствуют в выдаче'
    assert repr(kwargs) in result, 'Именованные аргументы не найдены'


def test_err_annotated_msg_not_args() -> None:
    """Проверка, что срабатывает отключенный add_args."""

    err_a: str = 'Test'
    args: tuple[int, ...] = (1, 2, 3)
    kwargs: dict[str, int] = {}

    result: str | None = err_annotated_msg(
        err_a,
        add_args=False,
        exclude_args=False,
        exclude_self=True,
        exclude_kwargs=None,
        func=wrapper_func,
        args=args,
        kwargs=kwargs,
    )

    assert result is not None, 'Результат не должен быть None'
    assert result == err_a, 'Результат должен быть точной копией аннотации'


def test_err_annotated_msg_exclude_args() -> None:
    """Проверка, что исключенные именованные аргументы не попадают в выдачу."""

    err_a: str = 'Test'
    kwargs: dict[str, int] = {'a': 4, 'b': 5, 'c': 6, 'd': 7}
    exclude: list[str] = ['a', 'b']

    result: str | None = err_annotated_msg(
        err_a,
        add_args=True,
        exclude_args=False,
        exclude_self=True,
        exclude_kwargs=exclude,
        func=wrapper_func,
        args=(),
        kwargs=kwargs,
    )

    # "Test | args=(), kwargs={'c': 6, 'd': 7}"
    assert result is not None, 'Результат не должен быть None'

    # Извлекаем словарь.
    m = re.search(r'kwargs=(\{.*})$', result)
    assert m, 'Словарь не найден в финальной аннотации'
    kwargs_re = ast.literal_eval(m.group(1))

    for k in kwargs:
        if k in exclude:
            assert k not in kwargs_re
        else:
            assert k in kwargs_re
