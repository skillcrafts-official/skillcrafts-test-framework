# Описание тестовых моделей
## Структура описания
В основе тестовых моделей лежит следующая структура каталогов  
```
test_framework
|--test_models
|  |--api
|  |  |--base.py 
|  |  |--api_model_1.py
|  |  |--api_model_2.py
|  |  |--...
|  |-- DB
|  |-- UI
```

### Назначение файла base.py
В данном файле описаны правила взаимодействия с тестируемым сервисом.  
Пример,  
```python
class BaseService:
    BASE_URL = "https://api.skillcrafts.ru"

    def __init__(self):
        self.last_response: Optional[requests.Response] = None

    def _get_headers(self) -> dict:
        """Базовые заголовки, наследники могут добавлять авторизацию."""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.BASE_URL}/{path.lstrip('/')}"
        headers = self._get_headers()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        self.last_response = requests.request(method, url, headers=headers, **kwargs)
        return self.last_response

    def get(self, path: str, **kwargs) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, data: Optional[dict] = None, **kwargs) -> requests.Response:
        return self._request("POST", path, json=data, **kwargs)

    def put(self, path: str, data: Optional[dict] = None, **kwargs) -> requests.Response:
        return self._request("PUT", path, json=data, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self._request("DELETE", path, **kwargs)
```

### Назначение файла api_model_1.py  

Данный файл предназначен для описания правил работы с ендпоинтами REST API в виде классов по принципу: одна схема (schema) - один класс.  
В каждом классе определяются методы запросов. Один метод - один ендпоинт.  

Например, у меня есть ендпоинт, запрашивающий JWT-токены.  
Тогда я пишу класс, который будет хранить токены и мета-данные, соответствующие модели данных для этого эндпоинта.  
```python
class Auth(BaseService, ApiBaseAssertsMixin):
    """
    Модель данных описывается аналогично фреймворкам django и FastAPI
    """
    access_token: Optional[str] = None   # токен
    refresh_token: Optional[str] = None  # токен
    user_id = str | None                 # мета-информация
```
А также метод, который будет делать запрос этих данных.
```python
    """Начало класса в листинге выше"""

    def token(self, email: str, password: str) -> dict:
        """Получает access + refresh токены + мета данные"""
        self.post("/auth/token/", data={"email": email, "password": password})
        tokens = self.last_response.json()
        Auth.access_token = tokens.get("access")
        Auth.refresh_token = tokens.get("refresh")
        Auth.user_id = tokens.get("user_id")
        return tokens
```
Далее нужно подмешать в класс миксины с методами-ассертами, которые нужны будут для тест-дизайна. Подробнее о тест-дизайне в резделе [wiki/test_design/](https://wiki.skillcrafts.ru/wiki/test_design/).

В приведённым выше классе подмешивается миксин с общими для любого ендпоинта ассертами, такими как проверка статус-кода, проверка наличия токена для заголовка `Authorization` и т.д.

Миксины с ассертами разрабатываются в отдельном блоке фреймворка "Фабрика тестов": [test_factories](https://wiki.skillcrafts.ru/wiki/test_factories/).