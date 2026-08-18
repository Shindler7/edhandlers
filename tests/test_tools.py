"""Тестирование функциональности утилит."""

from ehandlers import tools


def test_exception() -> None:
    """Проверка корректности определения exception."""

    # Корректные типы.
    exc_obj: Exception = ValueError('message')
    exc_type: type[Exception] = AttributeError
    assert tools.is_exception(exc_obj)
    assert tools.is_exception(exc_type)

    # Некорректные типы.
    assert not tools.is_exception(str)
    assert not tools.is_exception(100500)


def test_is_exc_instance() -> None:
    """Проверка точности выявления экземпляра исключения."""

    exc_obj: Exception = ValueError('message')
    exc_type: type[Exception] = AttributeError

    assert tools.is_exc_instance(exc_obj)
    assert not tools.is_exc_instance(exc_type)

    # Другие типы.
    assert not tools.is_exc_instance('Im String')
    assert not tools.is_exc_instance(100500)


def test_exc_type() -> None:
    """Проверка корректности типа класса исключения."""

    exc_obj = ValueError('message')
    exc_type = AttributeError

    assert tools.is_exc_type(exc_type)
    assert not tools.is_exc_type(exc_obj)

    # Некорректные типы.
    for t in ['string', 100500, [112], None]:
        assert not tools.is_exc_type(t)
