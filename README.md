![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

# ehandlers
**Коллекция обработчиков исключений**, позволяющих одновременно логировать 
события с помощью [logging](https://docs.python.org/3/library/logging.html).

Собственной механики логирования не имеет.

> **Важно:** Создано и обкатано в [Django](https://www.djangoproject.com/).

С версии *0.3.2b* декораторы поддерживают **асинхронные функции**. 

## Установка

```shell
pip install git+https://github.com/Shindler7/edhandlers.git 
```

## Декораторы

### @err_interceptor

**Базовый декоратор-перехватчик**. Обеспечивает исполнение функцией своих 
задач, а при возбуждении исключения перехватывает его и логирует. Исключение
возбуждается повторно, при необходимости с сохранением трассировки.

```python
import logging
from ehandlers.decorators import err_interceptor

logger = logging.getLogger(__name__)


@err_interceptor(log_obj=logger, err_annotated='Функция деления на ноль')
def boo():
    return 2/0
```

*Доступные атрибуты*:
* `err_raise` — позволяет установить исключение, которое будет возбуждено при
перехвате любых других исключений (необязательно). Можно передать как экземпляр
исключения (`ValueError('неверное значение')`), так и тип класса исключения
(`ValueError`), который будет преобразован декоратором в экземпляр;
* `err_annotated` — добавление любой текстовой информации при логировании 
исключения (необязательно);
* `args_to_annotate` — args и kwargs обёрнутой функции будут добавлены в лог 
(необязательно);
* `log_obj` — экземпляр `logging`;
* `log_level` — константа уровня логирования исключения (из стандартного набора
`logging`: `logging.WARNING`, `logging.ERROR` и др.);
* `from_err` — если `True` сохраняет трассировку исключения, что наиболее 
важно, если использован иной экземпляр исключения через атрибут `err_raise` 
(необязательно).

### @err_log_and_return

После перехвата исключения и логирования, обеспечивает **возврат** обёрнутой 
функцией **предустановленного значения**, а не исключения.

```python
import logging
from ehandlers.decorators import err_log_and_return

logger = logging.getLogger(__name__)


@err_log_and_return(log_obj=logger)
def foo(key: str):
    bar: dict[str, str] = {'a': 'A', 'b': 'B', 'c': 'C'}
    return bar[key]
```

*Доступные атрибуты*:
* `err_output` — результат, который будет возвращён обёрнутой функцией при
возбуждении исключения. По-умолчанию None;
* `err_annotated` — добавление любой текстовой информации при логировании 
исключения;
* `args_to_annotate` — args и kwargs обёрнутой функции будут добавлены в лог;
* `log_obj` — экземпляр `logging`;
* `log_level` — константа уровня логирования исключения.

### @raise_if_return

**Декоратор-инициатор исключений**, которые он возбуждает при получении 
возврата от обёрнутой функции. Например, в примере, каждый *return* 
вызовет `ValueError`. 

```python
import logging
from ehandlers.decorators import raise_if_return

logger = logging.getLogger(__name__)


@raise_if_return(exception=ValueError, log_obj=logger)
def validate(text: str):
    if not isinstance(text, str):
        return f'Текст ожидался str, а получено {type(text)}'
    
    if len(text) > 200:
        return 'Длина текста не должна превышать 200 символов'
```

*Доступные атрибуты*:
* ``exception`` — экземпляр исключения или тип класса исключения, которое будет
возбуждаться при перехвате возвратов. В приведённом примере это будет, например,
`ValueError('Длина текста не должна превышать 200 символов')'`;
* `err_msg_annotate` — дополнительная информация, которая будет добавлена при
логировании (необязательно);
* `log_obj` — экземпляр `logging`;
* `log_level` — константа уровня логирования исключения;
* `raise_by_type` — позволяет установить тип данных, перехват которых будет
возбуждать исключение. По-умолчанию `str`;
* `raise_by_none` — если `True`, при возврате обёрнутой функцией None будет
возбуждено исключение. По-умолчанию отключено.

## Функции

Кроме декораторов доступны отдельные методы, которые могут быть использованы
внутри дерева `try...except`. Учитывая, что именно на них опираются декораторы,
во многом дублируют их функционал.

* `intercept_err_and_log` — **транзитный перехватчик**: логирует с заданными 
параметрами переданное исключение и возбуждает его повторно;

```pycon
>>> import logging
>>> from ehandlers.except_handlers.handlers import intercept_err_and_log
>>> logger = logging.getLogger(__name__)
>>> try:
...     result = 2 / 0
... except ZeroDivisionError as err:
...     intercept_err_and_log(err, log_obj=logger)
...
<log_err> ZeroDivisionError: division by zero
Traceback (most recent call last):
(...)
ZeroDivisionError: division by zero
```
 
* `raise_err_and_log` — **инициатор исключения**, которое одновременно и 
логирует;

```pycon
>>> import logging
>>> from ehandlers.except_handlers.handlers import raise_err_and_log
>>> logger = logging.getLogger(__name__)
>>> 
>>> raise_err_and_log(RuntimeError, err_message='перевозбуждение', log_obj=logger)
<log_err> RuntimeError: перевозбуждение
Traceback (most recent call last):
(...)
RuntimeError: перевозбуждение
```

* `log_err` — **логирует** переданное исключение, **и останавливает** его.

```pycon
>>> import logging
>>> from ehandlers.except_handlers.handlers import log_err
>>> logger = logging.getLogger(__name__)
>>>
>>> try:
...     foo = {'a': 'A'}
...     foo['b']
... except KeyError as err:
...     log_err(err, log_obj=logger, log_level=logging.WARNING)
...
<log_err> KeyError: 'b'
```

## Версии

- 0.3.2 — добавлена поддержка асинхронных функций, расширена документация.
- 0.3.2b — обновление названия, структуры пакета, мелкие изменения. 
- 0.2b — технический коммит (изменение кодировки README.md).
- 0.1b — первичный пакет (без тестирования).
