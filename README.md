![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)
![Version](https://img.shields.io/badge/version-0.5.0-green.svg?style=for-the-badge)

# ehandlers

Библиотека обработки исключений для Python-проектов, расширяющая стандартный модуль `logging`. Предоставляет декораторы
и утилиты для структурированного логирования ошибок с полным контекстом.

## Особенности

- **Универсальные декораторы** для синхронного и асинхронного кода
- **Гибкое логирование** с добавлением контекста выполнения
- **Минимальные зависимости** — только стандартная библиотека Python
- **Поддержка Django** и других веб-фреймворков
- **Типизированные аннотации** для улучшенной поддержки IDE

## Установка

### Github

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

# Декораторы обработки ошибок

| Что нужно?                                                             | Какой декоратор?      |
|------------------------------------------------------------------------|-----------------------|
| Ошибка должна быть залогирована, но программа должна упасть            | `@err_interceptor`    |
| Ошибка допустима, нужно вернуть значение по умолчанию и записать в лог | `@err_log_and_return` |
| Возврат определённого значения должен вызвать исключение (валидаторы)  | `@raise_if_return`    |

### @err_interceptor

Базовый декоратор для перехвата и логирования исключений с возможностью их повторного возбуждения.

```python
import logging

from ehandlers.decorators import err_interceptor

logger = logging.getLogger(__name__)


@err_interceptor(
    log=logger,
    err_annotated='Деление чисел',
    args_to_annotate=True,
    log_level=logging.ERROR,
)
def divide(a: float, b: float) -> float:
    """Выполняет деление a на b."""
    return a / b
```

#### Параметры:

- `log` — экземпляр логгера (обязательный)
- `err_annotated` — дополнительное описание ошибки
- `args_to_annotate` — логировать аргументы функции (по умолчанию `False`)
- `log_level` — уровень логирования (по умолчанию `logging.ERROR`)
- `err_raise` — исключение для повторного возбуждения (опционально)
- `from_err` — сохранять оригинальный traceback (по умолчанию `True`)

> _Изменено в версии 0.5.0_: на замену атрибута `log_obj` введён атрибут `log`. Будет
> полностью исключён с версии `0.6.0`.

### @err_log_and_return

Логирует исключение и возвращает заданное значение вместо его возбуждения.

```python
import logging

from ehandlers.decorators import err_log_and_return

logger = logging.getLogger(__name__)


# noinspection PyUnresolvedReferences
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
- Другие параметры аналогичны `@err_interceptor`

### @raise_if_return

Возбуждает исключение при возврате функцией определённых значений.

```python
import logging

from ehandlers.decorators import raise_if_return

logger = logging.getLogger(__name__)


# noinspection PyUnresolvedReferences
@raise_if_return(
    exception=ValidationError,
    log=logger,
    raise_by_type=(str,),
    err_msg_annotate='Валидация данных',
)
def validate_email(email: str) -> bool | str:
    """Валидирует email адрес."""
    if '@' not in email:
        return 'Некорректный email адрес'
    return True
```

#### Параметры:

- `exception` — исключение для возбуждения (обязательный)
- `raise_by_type` — кортеж значений, вызывающих исключение (по умолчанию `str`)
- raise_by_none — возбуждать исключение при возврате `None` (по умолчанию
  `False`)
- `err_msg_annotate` — дополнительное описание в логе

## Функции-обработчики

Для использования внутри `try...except` блоков.

### intercept_err_and_log

Логирует исключение и возбуждает его повторно.

```python
import logging

from ehandlers.except_handlers.handlers import intercept_err_and_log

logger = logging.getLogger(__name__)

try:
    data = json.loads(invalid_json)  # noqa
except json.JSONDecodeError as err:  # noqa
    intercept_err_and_log(err, log=logger, err_annotated='Парсинг JSON')
```

### raise_err_and_log

Создаёт и логирует новое исключение.

```python
import logging

from ehandlers.except_handlers.handlers import raise_err_and_log

logger = logging.getLogger(__name__)

if not user.is_authenticated:  # noqa
    raise_err_and_log(
        PermissionError,
        err_message='Пользователь не аутентифицирован',
        log=logger,
        log_level=logging.WARNING,
    )
```

### log_err

Логирует исключение без его повторного возбуждения.

```python
import logging

from ehandlers.except_handlers.handlers import log_err

logger = logging.getLogger(__name__)

try:
    db_record.save()  # noqa
except DatabaseError as err:  # noqa
    log_err(err, log=logger)
# Продолжаем выполнение...
```

## Асинхронная поддержка

Все декораторы полностью поддерживают асинхронные функции и методы.

```python
# noinspection PyUnresolvedReferences
@err_interceptor(log=logger)
async def fetch_data(url: str) -> dict:
    """Асинхронное получение данных."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

## 📖 Примеры использования

### Django

```python
# noinspection PyUnresolvedReferences
async def news_to_file(news: dict):
    """Сохранить новости в файл."""

    try:
        await files.write_json_async(configurate.NEWS_JSON_FULLPATH, news)
    except OSError as err:
        intercept_err_and_log(err, log=logger)  # noqa
```

### FastAPI/Starlette

```python
from fastapi import FastAPI, HTTPException  # noqa

from ehandlers.decorators import err_interceptor

app = FastAPI()


@app.get('/items/{item_id}')
@err_interceptor(
    log=logger,  # noqa
    err_raise=HTTPException(status_code=500, detail='Внутренняя ошибка'),
)
async def read_item(_item_id: int):
    print('Логика обработки...')
```

## Тесты

При поддержке `pytest` собраны тесты для проверки функциональности.

```pycon
python -m pytest
```

## История версий

### [0.5.0] — 18.08.2026

- В декораторах и методах добавлен атрибут `log` для будущей замены `log_obj`.
- Оптимизирован процесс вычисления имени функции, где выбросилось исключение.
- Удалён метод `raise_type` — плохая практика сложного раскрытия типов исключений.
- Повышена поддерживаемая версия `Python`: 3.12+.
- Улучшение кода на основе замечаний `ruff`, без изменения функциональности.

### [0.4.2] — 24.07.2026

- Исправлена опечатка в `setup.py` в ссылке на репозиторий проекта.

### [0.4.1] — 25.04.2026

- Добавлен аргумент `exclude_args` для аргумента `args_to_annotate`, что позволяет исключить отдельные аргументы функций
  из выдачи в логи.
- Улучшена обработка типов данных.

### [0.4.0] — 25.01.2026

- Исправлены ошибки при обработке асинхронных методов.
- Улучшена поддержка типизации для IDE.
- Оптимизирована производительность декораторов.

### [0.3.3]

- Добавлена поддержка асинхронных функций.
- Расширена документация с примерами использования.
- Улучшена обработка контекста исключений.

### [0.3.2b]

- Обновлена структура пакета.
- Добавлены тесты для основных сценариев.
- Улучшена совместимость с Python 3.11+.

### [0.1b]

- Первый публичный релиз.
- Базовые декораторы и обработчики.
- Поддержка синхронного кода.

## Вклад в проект

Приветствуется проактивная поддержка и участие в развитии.

## Лицензия

Распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.
