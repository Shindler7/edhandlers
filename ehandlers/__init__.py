"""
ehandlers — структурированная обработка исключений с логированием.

Декораторы и утилиты для перехвата, логирования и обработки ошибок
с полным контекстом выполнения. Поддерживает синхронный и асинхронный код,
минимальные зависимости.

Быстрый старт:
    @err_interceptor(log_obj=logger, err_annotated="Обработка пользователя")
    def process_user(user_id: int) -> dict:
        ...

Декораторы:
    @err_interceptor       — логирует и пробрасывает исключение дальше
    @err_log_and_return    — логирует и возвращает значение по умолчанию
    @raise_if_return       — возбуждает исключение при определённых возвратах

Хендлеры для try/except:
    intercept_err_and_log  — логирует и пробрасывает
    log_err                — только логирует, выполнение продолжается
    raise_err_and_log      — создаёт, логирует и возбуждает новое исключение

Подробнее: https://github.com/Shindler7/ehandlers
"""

from .decorators import err_interceptor, err_log_and_return, raise_if_return
from .except_handlers import tools
from .except_handlers.handlers import intercept_err_and_log, log_err, raise_err_and_log

__all__ = (
    'err_interceptor',
    'err_log_and_return',
    'raise_if_return',
    'intercept_err_and_log',
    'log_err',
    'raise_err_and_log',
    'tools',
)

__version__ = '0.4.3'
__author__ = 'Vlad Barmichev'
__email__ = 'barmichev@gmail.com'
__status__ = 'Production'
