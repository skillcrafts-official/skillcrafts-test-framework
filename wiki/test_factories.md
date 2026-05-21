# Фабрика тестов
Это раздел тестового фреймворка, в котором разрабатываются ассерты для будущих тестов.  

### Структура фабрики
Структура фабрики тестов повторяет структуру описания тестовых моделей:  
```
test_framework
|--test_factories
|  |--api
|  |  |--base_mixins.py 
|  |  |--auth_mixins.py
|  |  |--data_mixins.py
|  |  |--file_mixins.py
|  |  |--...
|  |-- DB
|  |-- UI
```

### Примеры миксинов с ассертами
Тут всё просто. Даём классу понятное название и описывам, как именно будет срабатывать `assert` в коде:  
```python
class ApiBaseAssertsMixin:
    """
    Класс-миксин для базовых проверок RESTAPI-запросов
    """
    def assert_status_code(self, expected_code: int):
        assert self.last_response is not None, "Нет выполненного запроса"
        actual = self.last_response.status_code
        assert actual == expected_code, f"Ожидался статус {expected_code}, получен {actual}"

    def assert_json_has_key(self, key: str):
        assert self.last_response is not None, "Нет выполненного запроса"
        json_data = self.last_response.json()
        assert key in json_data, f"Ключ '{key}' отсутствует в ответе: {json_data}"

    def assert_json_value(self, key: str, expected_value: Any):
        assert self.last_response is not None, "Нет выполненного запроса"
        json_data = self.last_response.json()
        actual = json_data.get(key)
        assert actual == expected_value, f"Ключ '{key}': ожидалось '{expected_value}', получено '{actual}'"
```

В случае срабатывания `assert` тесты не прерываются, а сообщение ассерта добавляется в результаты выполнения тестов. Поэтому при разборе падений будет сразу понятно, на каком уровне завалился тест.  

В данном случае рассматривается два уровня:  

- Высокий уровень, или уровень пользователя, или уровень бизнес-логики (например, нам пришли не те данные или не тот статус ответа).
- Низкий уровень, или уровень разработчика, или уровень ассерта (например, запрос был выполнен, но ответа никакого не пришло, или пришёл неожиданный тип данных).