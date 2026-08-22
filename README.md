![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)
![Version](https://img.shields.io/badge/version-0.6.0-green.svg?style=for-the-badge)

# ehandlers

Библиотека обработки исключений для Python-проектов, расширяющая стандартный модуль
`logging`. Предоставляет декораторы и утилиты для структурированного логирования ошибок
с полным контекстом.

Подробнее о `logging`
в [документации Python](https://docs.python.org/3/library/logging.html).

## Особенности

- **Универсальные декораторы** для синхронного и асинхронного кода, а также могут
  применяться для методов классов
- **Гибкое логирование** с добавлением контекста выполнения
- **Минимальные зависимости** — только стандартная библиотека Python
- **Типизированные аннотации** для улучшенной поддержки IDE

## Установка

### GitHub

```shell
pip install git+https://github.com/Shindler7/edhandlers.git 
```

### Для проектов с Poetry

```shell
poetry add git+https://github.com/Shindler7/ehandlers.git
```

## Быстрый старт

```python
import logging
from ehandlers import err_interceptor

logger = logging.getLogger(__name__)


@err_interceptor(log=logger, err_annotated='Обработка пользовательских данных')
def process_user_data(user_id: int) -> dict:
    # Код функции...
    if user_id < 0:
        raise ValueError('ID пользователя не может быть отрицательным')
    return {'id': user_id, 'status': 'active'}
```

## Декораторы

| Что нужно?                                                            | Какой декоратор?                           |
|-----------------------------------------------------------------------|--------------------------------------------|
| Ошибку логировать и возбудить заново исключение                       | [@err_interceptor](#err_interceptor)       |
| Логировать ошибку, а обёрнутый метод вернёт значение по умолчанию     | [@err_log_and_return](#err_log_and_return) |
| Возврат определённого значения должен вызвать исключение (валидаторы) | [@raise_if_return](#raise_if_return)       |

### @err_interceptor

Базовый декоратор для перехвата и логирования исключений с возможностью их повторного
возбуждения.

```python
import logging

from ehandlers import err_interceptor

logger = logging.getLogger(__name__)


@err_interceptor(
    log=logger,
    err_annotated='Деление чисел',
    args_to_annotate=True,
    level=logging.ERROR,
)
def divide(a: float, b: float) -> float:
    """Выполняет деление a на b."""
    return a / b
```

#### Параметры:

- `log` — экземпляр логгера (обязательный)
- `err_annotated` — дополнительное описание ошибки
- `args_to_annotate` — логировать аргументы функции (по умолчанию `False`)
- `exclude_self` — исключить из логирования аргументов `self` и `cls`, по умолчанию
  `True` (применяется, если  `args_to_annotate=True`)
- `exclude_args` — исключаются из логирования `args` (неименованные аргументы), по
  умолчанию `False` (применяется, если  `args_to_annotate=True`)
- `exclude_kwargs` — список именованных аргументов, которые не будут логированы
  (актуально, если  `args_to_annotate=True`)
- `level` — уровень логирования (по умолчанию `logging.ERROR`)
- `err_raise` — исключение для повторного возбуждения (опционально)
- `from_err` — сохранять оригинальный traceback (по умолчанию `True`)

> _Изменено в версии 0.6.0_:
>   - `log_obj` исключён, вместо него применяется `log`
>   - `log_level` переименован в `level`
>   - функционал аргумента `exclude_args` перенесён в `exclude_kwargs`
>   - обновлённый `exclude_args` теперь отвечает за логирование `args`

#### Безопасность логирования аргументов

> ⚠️При `args_to_annotate=True` в логи могут попасть чувствительные данные (`password`,
> `token`, `api_key` и т.д.). Рекомендуется явно исключать их через `exclude_kwargs`.
> Если секреты передаются позиционно, можно установить `exclude_args=True`, чтобы
> исключить их из выдачи.

### @err_log_and_return

Логирует исключение и возвращает заданное значение вместо его возбуждения.

```python
import logging

from typing import Any
from ehandlers import err_log_and_return

logger = logging.getLogger(__name__)

CONFIG: dict[str, Any] = {}


@err_log_and_return(
    log=logger,
    err_output={'status': 'error', 'message': 'Ошибка обработки'},
    args_to_annotate=True,
)
def get_config_value(key: str) -> Any:
    """Получает значение из конфигурации."""
    return CONFIG[key]  # Может вызвать KeyError
```

#### Параметры:

- `err_output` — значение, возвращаемое при ошибке (по умолчанию `None`)

Другие параметры аналогичны [@err_interceptor](#err_interceptor).

### @raise_if_return

Возбуждает исключение при возврате функцией определённых значений.

```python
import logging

from ehandlers import raise_if_return

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


@raise_if_return(
    exception=ValidationError,
    log=logger,
    err_msg_annotate='Валидация данных',
)
def validate_email(email: str) -> bool | str:
    """Валидирует email адрес."""
    if '@' not in email:
        return 'Некорректный email адрес'
    return True
```

#### Параметры:

- `log` — экземпляр логгера (обязательный)
- `level` — уровень логирования (по умолчанию `logging.ERROR`)
- `exception` — исключение для возбуждения (обязательный)
- `raise_by_type` — кортеж значений, вызывающих исключение (по умолчанию `(str,)`)
- `raise_by_none` — возбуждать исключение при возврате `None` (по умолчанию  `False`)
- `err_msg_annotate` — дополнительное описание в логе

## Функции-обработчики

Для использования внутри `try...except` блоков.

### intercept_err_and_log

Логирует исключение и возбуждает его повторно.

```python
import json
import logging

from ehandlers import intercept_err_and_log

logger = logging.getLogger(__name__)

invalid_json: str = '{"name": "Ivan", "age": 30, "is_employee": true'

try:
    data = json.loads(invalid_json)
except json.JSONDecodeError as err:
    intercept_err_and_log(err, log=logger, err_annotated='Парсинг JSON')
```

### raise_err_and_log

Создаёт и логирует новое исключение.

```python
import logging

from ehandlers import raise_err_and_log

logger = logging.getLogger(__name__)


class User:
    is_authenticated: bool = False


user = User()

if not user.is_authenticated:
    raise_err_and_log(
        PermissionError,
        err_message='Пользователь не аутентифицирован',
        log=logger,
        level=logging.WARNING,
    )
```

### log_err

Логирует исключение без его повторного возбуждения.

```python
import logging

from ehandlers import log_err

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    pass


class Database:
    def save(self) -> None:
        raise DatabaseError('Отсутствует доступ к базе данных.')


try:
    db = Database()
    db.save()
except DatabaseError as err:
    log_err(err, log=logger)
# Продолжаем выполнение...
```

## Асинхронная поддержка

Все декораторы поддерживают асинхронные функции и методы.

## Тесты

При поддержке `pytest` собраны тесты для проверки функциональности.

```shell
python -m pytest
```

## История версий

См. файл [CHANGELOG.md](CHANGELOG.md).

## Вклад в проект

Приветствуется проактивная поддержка и участие в развитии.

## Лицензия

Распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.
