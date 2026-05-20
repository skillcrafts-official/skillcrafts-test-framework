from typing import Any


class ApiBaseAssertsMixin:
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
