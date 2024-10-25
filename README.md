![image](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)

# ehandler
Коллекция обработчиков исключений

## Обработчики исключений

Обработчики применяются для содействия перехвату, логированию исключений "на
лету". Присутствуют в двух вариациях: *функции* и *декораторы*.

Собственное логирование не осуществляют, опираются на переданные экземпляры
*Logger* или иные.

### Декораторы

```python3
from ehandler.decorators.except_handlers import err_interceptor
from ehandler.decorators.except_handlers import err_log_and_return
from ehandler.decorators.except_handlers import raise_if_return

@err_interceptor()
def a():
    ...
```

Форматы применения:
* **@err_interceptor** — ключевой обработчик. Исключение перехватывает, 
фиксирует в лог, и пропускает далее. Может подменить перехваченное исключение
на требуемое, но сохранив трассировку. 
* **@err_log_and_return** — подхватывает и логирует исключение, но далее гасит
его и возвращает заказанный результат вызвавшей функции. Например, пустой 
словарь или None. Иногда это удобно.
* **@raise_if_return** — подходит для создания валидаторов. Возбуждает 
исключение получая *return* от обёрнутой функции. Можно настроить типы, на
которые реагировать (например, только str).

В настоящее время внедрена поддержка **асинхронных функций** (*asyncio*).

### Функции

```python3
import logging
from typing import Dict

from ehandler.except_handlers.interfaces import intercept_err_and_log

logger = logging.Logger(__name__)


def a(data: Dict[str, str]):
    try:
        result: str = data['result']
    except KeyError as err:
        intercept_err_and_log(err, log_obj=logger, source_func=a)        
```

Функции, в сущности, это машинное отделение декораторов. Их задача предоставить
максимум функционала для логирования исключений и централизованного управления,
формирования единой выдачи в логи.
* **intercept_err_and_log** — перехватчик, который фиксирует исключение в логи,
и далее возбуждает его заново, либо подменяет на требуемое, при необходимости,
сохраняя трассировку (*from err*).
* **raise_err_and_log** — можно сказать, гибрид raise Exception и logger.
Фиксирует ошибку и возбуждает исключение. 
* **log_err** — обёртка для logger, опирается на его инфраструктуру, но
работает на централизацию обработки и контроль логирования, единство
представления информации.

### Версии

- 0.1b — создан первичный пакет (без тестирования).
