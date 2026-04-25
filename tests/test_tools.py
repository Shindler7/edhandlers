"""Тестирование функциональности утилит."""
from ehandlers.except_handlers import tools


def test_exception():
    """Проверка корректности определения exception."""

    # Корректные типы.
    exc_obj = ValueError("message")
    exc_type = AttributeError
    assert tools.is_exception(exc_obj) == True
    assert tools.is_exception(exc_type) == True

    # Некорректные типы.
    assert tools.is_exception(str) == False
    assert tools.is_exception(100500) == False


def test_is_exc_instance():
    """Проверка точности выявления экземпляра исключения."""

    exc_obj = ValueError("message")
    exc_type = AttributeError

    assert tools.is_exc_instance(exc_obj) == True
    assert tools.is_exc_instance(exc_type) == False

    # Другие типы.
    assert tools.is_exc_instance('Im String') == False
    assert tools.is_exc_instance(100500) == False


def test_exc_type():
    """Проверка корректности типа класса исключения."""

    exc_obj = ValueError("message")
    exc_type = AttributeError

    assert tools.is_exc_type(exc_type) == True
    assert tools.is_exc_type(exc_obj) == False

    # Некорректные типы.
    for t in ['string', 100500, [112], None]:
        assert tools.is_exc_type(t) == False
