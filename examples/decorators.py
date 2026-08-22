"""Примеры использования декораторов.

Запуск:
    python -m examples.decorators
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from textwrap import dedent

from ehandlers import err_interceptor, err_log_and_return, raise_if_return

from .logger_config import get_logger

logger = get_logger()

BASE = {'one': 1, 'two': 2, 'three': 3}


@err_interceptor(log=logger, args_to_annotate=True)
def simple_find_key(key: str) -> int:
    """`err_interceptor`: логирует ошибку и пробрасывает её дальше."""
    return BASE[key]


@err_log_and_return(log=logger, err_output='нет данных')
def read_data() -> str:
    """`err_log_and_return`: возвращает запасное значение при ошибке."""
    # Файл с таким именем почти гарантированно не существует.
    filename = f'{uuid.uuid4()}.txt'
    with open(filename, encoding='utf-8') as file:
        return file.read().strip()


class ValidateUserError(Exception):
    """Ошибка валидации пользователя."""


@dataclass(slots=True, kw_only=True)
class User:
    name: str
    age: int
    is_active: bool


@raise_if_return(log=logger, exception=ValidateUserError)
def validate_user(user: User) -> str | None:
    """`raise_if_return`: поднимает исключение, если функция вернула строку."""
    if user.age < 18:
        return f'Пользователь {user.name} слишком молод.'
    if not user.is_active:
        return 'Пользователь не активен.'
    return None


def print_section(title: str, body: str) -> None:
    print(
        dedent(
            f"""
            *** Демонстрация декоратора `{title}` ***
            {body}
            """
        ).strip()
    )


def demo_err_interceptor() -> None:
    print_section(
        '@err_interceptor',
        'Он сохраняет ошибку в логи и повторно возбуждает исключение.',
    )

    try:
        simple_find_key('four')
    except KeyError as err:
        print(f'Останавливаем исключение `KeyError`: {err}')


def demo_err_log_and_return() -> None:
    print_section(
        '@err_log_and_return',
        'Пытаемся прочитать несуществующий файл.\n'
        'Через `err_output` задано значение, которое вернётся при ошибке.',
    )

    result = read_data()
    print(f'Результат функции `read_data`: "{result}"')


def demo_raise_if_return() -> None:
    print_section(
        '@raise_if_return',
        'Лучше всего подходит для валидаторов.\n'
        'Возбуждает исключение, если обёрнутая функция возвращает заданное значение.',
    )

    print("\n> 1. Вариант без ошибки: `User(name='Bob', age=42, is_active=True)`")
    user_bob = User(name='Bob', age=42, is_active=True)
    validate_user(user_bob)
    print('УСПЕШНО')

    print(
        '\n> 2. Вариант с ошибкой (пользователь не активен): '
        "`User(name='Boris', age=20, is_active=False)`"
    )
    user_boris = User(name='Boris', age=20, is_active=False)

    try:
        validate_user(user_boris)
    except ValidateUserError as err:
        print(f'ОШИБКА: {err}')


def main() -> None:
    demo_err_interceptor()
    print()
    demo_err_log_and_return()
    print()
    demo_raise_if_return()


if __name__ == '__main__':
    main()
