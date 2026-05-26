import os
import requests
from typing import Optional, Any

from skillcrafts_test_framework.settings import TEST_SERVICE

class BaseService:
    BASE_URL = TEST_SERVICE

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

    # ── Проверки ─────────────────────────────────────────────
    # def assert_status_code(self, expected_code: int):
    #     assert self.last_response is not None, "Нет выполненного запроса"
    #     actual = self.last_response.status_code
    #     assert actual == expected_code, f"Ожидался статус {expected_code}, получен {actual}"

    # def assert_json_has_key(self, key: str):
    #     assert self.last_response is not None, "Нет выполненного запроса"
    #     json_data = self.last_response.json()
    #     assert key in json_data, f"Ключ '{key}' отсутствует в ответе: {json_data}"

    # def assert_json_value(self, key: str, expected_value: Any):
    #     assert self.last_response is not None, "Нет выполненного запроса"
    #     json_data = self.last_response.json()
    #     actual = json_data.get(key)
    #     assert actual == expected_value, f"Ключ '{key}': ожидалось '{expected_value}', получено '{actual}'"